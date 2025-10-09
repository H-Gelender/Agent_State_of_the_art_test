import asyncio
import httpx
import json
import logging
import os
from pathlib import Path
from uuid import uuid4
from typing import Dict, Optional

from a2a.client import A2AClient, A2ACardResolver
from a2a.types import MessageSendParams, SendMessageRequest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IntelligentAgentRegistry:
    """Intelligent agent registry with LLM-based routing."""
    
    def __init__(self, registry_path: str = "client/agent_registry.json"):
        self.registry_path = Path(registry_path)
        self.agents: Dict[str, str] = {}
        self.clients: Dict[str, A2AClient] = {}
        self.agent_cards: Dict[str, dict] = {}
    
    def load_registry(self) -> bool:
        """Load agents from registry file."""
        try:
            with open(self.registry_path, 'r') as f:
                self.agents = json.load(f)
            logger.info(f"📂 Loaded {len(self.agents)} agents from registry")
            return True
        except Exception as e:
            logger.error(f"Failed to load registry: {e}")
            return False
    
    async def discover_agents(self, httpx_client: httpx.AsyncClient) -> int:
        """Discover agent capabilities and build detailed registry."""
        discovered = 0
        for name, url in self.agents.items():
            try:
                resolver = A2ACardResolver(httpx_client=httpx_client, base_url=url)
                agent_card = await resolver.get_agent_card()
                
                # Store detailed agent information
                self.agent_cards[name] = {
                    'url': url,
                    'description': agent_card.description,
                    'name': agent_card.name,
                    'skills': [
                        {
                            'name': skill.name,
                            'description': skill.description,
                            'examples': skill.examples
                        } for skill in (agent_card.skills or [])
                    ]
                }
                
                self.clients[name] = A2AClient(httpx_client=httpx_client, agent_card=agent_card)
                logger.info(f"✅ Connected to {name}: {agent_card.description}")
                discovered += 1
            except Exception as e:
                logger.warning(f"❌ Failed to connect to {name}: {e}")
        return discovered
    
    def get_client(self, agent_name: str) -> Optional[A2AClient]:
        """Get client for an agent."""
        return self.clients.get(agent_name)
    
    def get_agents_info(self) -> str:
        """Get formatted agent information for LLM context."""
        if not self.agent_cards:
            return "No agents available."
        
        agents_info = "Available agents:\n"
        for name, info in self.agent_cards.items():
            agents_info += f"\n- **{name}**: {info['description']}\n"
            if info['skills']:
                agents_info += "  Skills:\n"
                for skill in info['skills']:
                    agents_info += f"    • {skill['name']}: {skill['description']}\n"
                    if skill['examples']:
                        agents_info += f"      Examples: {', '.join(skill['examples'][:3])}\n"
        return agents_info

async def call_gemini_api(prompt: str) -> str:
    """Call Gemini API directly to avoid Pydantic AI issues."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        # If no API key, use simple keyword matching as fallback
        return None
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent?key={api_key}"
    
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 100
        }
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()
        
        data = response.json()
        if "candidates" in data and data["candidates"]:
            candidate = data["candidates"][0]
            if "content" in candidate and "parts" in candidate["content"]:
                return candidate["content"]["parts"][0]["text"]
        
        raise Exception("No valid response from Gemini")

async def smart_fallback_routing(registry: IntelligentAgentRegistry, query: str) -> str:
    """Smart keyword-based routing when LLM is not available."""
    query_lower = query.lower().strip()
    
    # Analyze agent capabilities and match with query
    for agent_name, info in registry.agent_cards.items():
        # Check if query matches agent description or skills
        description = info['description'].lower()
        skills_text = ' '.join([
            f"{skill['name']} {skill['description']} {' '.join(skill.get('examples', []))}"
            for skill in info['skills']
        ]).lower()
        
        # Time-related queries
        if any(keyword in query_lower for keyword in ['time', 'clock', 'hour', 'when', 'minute']):
            if any(keyword in description + ' ' + skills_text for keyword in ['time', 'clock', 'current']):
                logger.info(f"🎯 Smart routing: {query} → {agent_name} (time-related)")
                return agent_name
        
        # Greeting queries
        if any(keyword in query_lower for keyword in ['hello', 'hi', 'greet', 'how are you', 'good morning']):
            if any(keyword in description + ' ' + skills_text for keyword in ['greet', 'friendly', 'conversation', 'hello']):
                logger.info(f"🎯 Smart routing: {query} → {agent_name} (greeting)")
                return agent_name
    
    # Fallback to first agent
    first_agent = next(iter(registry.agent_cards.keys()))
    logger.info(f"🎯 Smart routing: {query} → {agent_name} (fallback)")
    return first_agent

async def intelligent_route_query(registry: IntelligentAgentRegistry, query: str) -> str:
    """Use LLM to intelligently route query to the most appropriate agent."""
    
    # Handle list agents command
    if query.lower().strip() in ['list', 'agents', 'list agents', 'show agents']:
        return registry.get_agents_info()
    
    if not registry.agent_cards:
        return "❌ No agents available"
    
    # Try LLM routing first, then smart fallback
    try:
        # Get agent information for LLM context
        agents_context = registry.get_agents_info()
        
        # Create prompt for agent selection
        prompt = f"""You are an intelligent agent orchestrator. Analyze the user query and select the MOST APPROPRIATE agent to handle it.

{agents_context}

User Query: "{query}"

Rules:
1. Choose the agent whose skills BEST match the user's request
2. Respond with ONLY the agent name (e.g., "telltime_agent" or "greeting_agent")
3. If no agent is perfect, choose the closest match
4. Be concise - respond with just the agent name

Agent to use:"""

        # Try Gemini API first
        gemini_response = await call_gemini_api(prompt)
        
        if gemini_response:
            selected_agent = gemini_response.strip().lower()
            
            # Validate the selected agent exists
            if selected_agent in registry.agent_cards:
                logger.info(f"🎯 LLM selected agent: {selected_agent}")
                return await send_to_agent(registry, query, selected_agent)
            else:
                # Try partial match
                for agent_name in registry.agent_cards.keys():
                    if agent_name in selected_agent or selected_agent in agent_name:
                        logger.info(f"🎯 LLM selected agent (partial match): {agent_name}")
                        return await send_to_agent(registry, query, agent_name)
        
        # Fallback to smart routing if LLM fails or no API key
        logger.info("🧠 Using smart fallback routing")
        selected_agent = await smart_fallback_routing(registry, query)
        return await send_to_agent(registry, query, selected_agent)
            
    except Exception as e:
        logger.warning(f"⚠️ LLM routing failed: {e}")
        # Use smart fallback routing
        logger.info("🧠 Using smart fallback routing")
        selected_agent = await smart_fallback_routing(registry, query)
        return await send_to_agent(registry, query, selected_agent)

async def send_to_agent(registry: IntelligentAgentRegistry, query: str, agent_name: str) -> str:
    """Send query to specific agent."""
    client = registry.get_client(agent_name)
    if not client:
        return f"❌ Agent {agent_name} not available"
    
    try:
        # Send message
        payload = {
            'message': {
                'role': 'user',
                'parts': [{'kind': 'text', 'text': query}],
                'message_id': uuid4().hex,
            },
        }
        request = SendMessageRequest(id=str(uuid4()), params=MessageSendParams(**payload))
        response = await client.send_message(request)
        
        # Extract response (same pattern as working client)
        if hasattr(response, 'root') and hasattr(response.root, 'result'):
            task = response.root.result
            if task.artifacts and task.artifacts[0].parts:
                return task.artifacts[0].parts[0].root.text
            return str(task)
        return str(response)
        
    except Exception as e:
        return f"❌ Error: {e}"

async def main():
    """Main orchestrator with intelligent LLM-based routing."""
    registry = IntelligentAgentRegistry()
    
    if not registry.load_registry():
        print("❌ Failed to load agent registry")
        return
    
    async with httpx.AsyncClient() as client:
        discovered = await registry.discover_agents(client)
        
        if discovered == 0:
            print("❌ No agents connected")
            return
        
        print(f"✅ Connected to {discovered} agents")
        print("🧠 Using intelligent LLM-based routing")
        print("💬 Ready! Type 'exit' to quit.\n")
        
        while True:
            try:
                query = input("You: ").strip()
                if not query or query.lower() in ["exit", "quit"]:
                    break
                
                response = await intelligent_route_query(registry, query)
                print(f"Assistant: {response}\n")
                
            except KeyboardInterrupt:
                break
        
        print("👋 Goodbye!")

if __name__ == "__main__":
    asyncio.run(main())