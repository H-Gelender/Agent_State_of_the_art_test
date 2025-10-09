import asyncio
import httpx
import logging
import json
from pathlib import Path
from uuid import uuid4
from typing import Dict, Optional, Set, List
from dotenv import load_dotenv

from pydantic_ai import Agent, RunContext
from pydantic_ai.tools import Tool

from a2a.client import A2AClient, A2ACardResolver
from a2a.types import MessageSendParams, SendMessageRequest

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AutoAgentRegistry:
    """Fully automatic agent registry that discovers agents without user intervention."""
    
    def __init__(self, registry_path: str = "client/agent_registry.json"):
        self.registry_path = Path(registry_path)
        self.agents: Dict[str, str] = {}  # name -> url
        self.agent_cards: Dict[str, dict] = {}  # name -> card info
        self.clients: Dict[str, A2AClient] = {}  # name -> client
        self.discovered_urls: Set[str] = set()  # track discovered URLs
        self.scan_ports = [3000, 5000, 8000, 8080, 9000, 9001, 9002]  # Common agent ports
    
    async def auto_discover_all_agents(self, httpx_client: httpx.AsyncClient) -> Dict[str, str]:
        """Automatically discover all available agents from registry and common ports."""
        all_discovered = {}
        
        # First, try to load from registry file
        registry_agents = self._load_registry_file()
        if registry_agents:
            logger.info(f"📂 Found {len(registry_agents)} agents in registry file")
            registry_results = await self._discover_from_urls(httpx_client, list(registry_agents.values()))
            all_discovered.update(registry_results)
        
        # Then, scan common ports for additional agents
        logger.info(f"🔍 Scanning common ports: {self.scan_ports}")
        scan_urls = [f"http://localhost:{port}" for port in self.scan_ports]
        scan_results = await self._discover_from_urls(httpx_client, scan_urls)
        all_discovered.update(scan_results)
        
        # Update registry file with all discovered agents
        if all_discovered:
            self._save_registry_file()
        
        return all_discovered
    
    def _load_registry_file(self) -> Dict[str, str]:
        """Load existing registry file if it exists."""
        try:
            if self.registry_path.exists():
                with open(self.registry_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load registry file: {e}")
        return {}
    
    def _save_registry_file(self):
        """Save current agents to registry file."""
        try:
            registry_data = {name: info['url'] for name, info in self.agent_cards.items()}
            with open(self.registry_path, 'w') as f:
                json.dump(registry_data, f, indent=2)
            logger.info(f"💾 Saved {len(registry_data)} agents to registry file")
        except Exception as e:
            logger.warning(f"Could not save registry file: {e}")
    
    async def _discover_from_urls(self, httpx_client: httpx.AsyncClient, urls: List[str]) -> Dict[str, str]:
        """Discover agents from a list of URLs."""
        results = {}
        for url in urls:
            if url in self.discovered_urls:
                continue
            
            agent_name = await self._discover_single_agent(httpx_client, url)
            if agent_name:
                results[url] = agent_name
        return results
    
    async def _discover_single_agent(self, httpx_client: httpx.AsyncClient, agent_url: str) -> Optional[str]:
        """Discover and register a single agent by URL."""
        try:
            logger.info(f"🔍 Trying {agent_url}")
            
            # Set a shorter timeout for discovery
            resolver = A2ACardResolver(httpx_client=httpx_client, base_url=agent_url)
            agent_card = await resolver.get_agent_card()
            
            # Generate unique agent name
            base_name = agent_card.name.lower().replace(" ", "_").replace("-", "_")
            agent_name = base_name
            counter = 1
            while agent_name in self.agents:
                agent_name = f"{base_name}_{counter}"
                counter += 1
            
            # Register the agent
            self.agents[agent_name] = agent_url
            self.agent_cards[agent_name] = {
                'url': agent_url,
                'card': agent_card,
                'capabilities': agent_card.capabilities.model_dump() if agent_card.capabilities else {},
                'skills': [skill.model_dump() for skill in agent_card.skills] if agent_card.skills else []
            }
            self.clients[agent_name] = A2AClient(httpx_client=httpx_client, agent_card=agent_card)
            self.discovered_urls.add(agent_url)
            
            logger.info(f"✅ Registered '{agent_name}': {agent_card.description}")
            return agent_name
            
        except Exception as e:
            logger.debug(f"❌ No agent at {agent_url}: {e}")
            return None
    
    def get_client(self, agent_name: str) -> Optional[A2AClient]:
        return self.clients.get(agent_name)
    
    def find_agent_by_capability(self, keywords: List[str]) -> Optional[str]:
        """Find the best agent based on keywords in their skills/description."""
        best_agent = None
        max_score = 0
        
        for agent_name, info in self.agent_cards.items():
            score = 0
            
            # Check agent name
            agent_name_lower = agent_name.lower()
            for keyword in keywords:
                if keyword.lower() in agent_name_lower:
                    score += 2
            
            # Check description
            description = info['card'].description.lower()
            for keyword in keywords:
                if keyword.lower() in description:
                    score += 1
            
            # Check skills
            for skill in info.get('skills', []):
                skill_text = f"{skill.get('name', '')} {skill.get('description', '')}".lower()
                for keyword in keywords:
                    if keyword.lower() in skill_text:
                        score += 2
                
                # Check examples
                examples_text = ' '.join(skill.get('examples', [])).lower()
                for keyword in keywords:
                    if keyword.lower() in examples_text:
                        score += 1
            
            if score > max_score:
                max_score = score
                best_agent = agent_name
        
        return best_agent if max_score > 0 else None

class AutoOrchestratorContext:
    """Context for the automatic orchestrator."""
    def __init__(self, registry: AutoAgentRegistry, httpx_client: httpx.AsyncClient):
        self.registry = registry
        self.httpx_client = httpx_client

# Tool functions for the orchestrator
async def smart_query_handler(ctx: RunContext[AutoOrchestratorContext], user_query: str) -> str:
    """
    Intelligently handle user queries by automatically selecting the best agent.
    
    Args:
        user_query: The user's question or request
    
    Returns:
        Response from the appropriate agent or direct response
    """
    registry = ctx.deps.registry
    query_lower = user_query.lower()
    
    # If no agents available, try to discover some
    if not registry.agents:
        logger.info("No agents available, attempting auto-discovery...")
        await registry.auto_discover_all_agents(ctx.deps.httpx_client)
        
        if not registry.agents:
            return "❌ No agents are currently available. Please make sure some agents are running on common ports (3000, 5000, 8000, 8080, 9000)."
    
    # Smart agent selection based on query content
    selected_agent = None
    
    # Time-related queries
    time_keywords = ['time', 'clock', 'hour', 'minute', 'second', 'when', 'what time', 'current time', 'now']
    if any(keyword in query_lower for keyword in time_keywords):
        selected_agent = registry.find_agent_by_capability(time_keywords)
    
    # Greeting queries
    elif any(keyword in query_lower for keyword in ['hello', 'hi', 'greet', 'how are you', 'good morning', 'good afternoon', 'good evening']):
        selected_agent = registry.find_agent_by_capability(['greeting', 'hello', 'conversation'])
    
    # Math/calculation queries
    elif any(keyword in query_lower for keyword in ['calculate', 'math', 'sum', 'multiply', 'divide', 'equation']):
        selected_agent = registry.find_agent_by_capability(['math', 'calculation', 'compute'])
    
    # Weather queries
    elif any(keyword in query_lower for keyword in ['weather', 'temperature', 'forecast', 'rain', 'sunny']):
        selected_agent = registry.find_agent_by_capability(['weather', 'temperature', 'forecast'])
    
    # If no specific match found, try to find the most relevant agent
    if not selected_agent:
        # Extract key words from query
        words = [word.strip('.,!?') for word in query_lower.split() if len(word) > 3]
        selected_agent = registry.find_agent_by_capability(words)
    
    # Fallback to first available agent
    if not selected_agent and registry.agents:
        selected_agent = next(iter(registry.agents.keys()))
    
    if not selected_agent:
        return "❌ No suitable agent found for your query. Please try running some agents first."
    
    # Send query to the selected agent
    return await _send_to_agent(ctx, user_query, selected_agent)

async def list_available_agents(ctx: RunContext[AutoOrchestratorContext]) -> str:
    """List all currently available agents and their capabilities."""
    registry = ctx.deps.registry
    
    if not registry.agent_cards:
        return "❌ No agents are currently available. I'll try to discover some automatically..."
    
    result = f"🤖 Available agents ({len(registry.agent_cards)}):\n\n"
    for agent_name, info in registry.agent_cards.items():
        result += f"• **{agent_name}** ({info['url']})\n"
        result += f"  📝 {info['card'].description}\n"
        
        skills = info.get('skills', [])
        if skills:
            result += "  🛠️ Skills:\n"
            for skill in skills[:2]:  # Show first 2 skills
                result += f"    - {skill.get('name', 'Unknown')}: {skill.get('description', 'No description')}\n"
            if len(skills) > 2:
                result += f"    ... and {len(skills) - 2} more skills\n"
        result += "\n"
    
    return result

async def refresh_agents(ctx: RunContext[AutoOrchestratorContext]) -> str:
    """Refresh the agent registry by re-discovering all agents."""
    registry = ctx.deps.registry
    
    # Clear current registry
    registry.agents.clear()
    registry.agent_cards.clear()
    registry.clients.clear()
    registry.discovered_urls.clear()
    
    # Re-discover all agents
    discovered = await registry.auto_discover_all_agents(ctx.deps.httpx_client)
    
    if discovered:
        return f"✅ Refreshed agent registry! Found {len(discovered)} agents:\n" + \
               "\n".join([f"  - {name} at {url}" for url, name in discovered.items()])
    else:
        return "❌ No agents found during refresh. Make sure agents are running on common ports."

async def _send_to_agent(ctx: RunContext[AutoOrchestratorContext], query: str, agent_name: str) -> str:
    """Send a query to a specific agent."""
    registry = ctx.deps.registry
    client = registry.get_client(agent_name)
    
    if not client:
        return f"❌ Agent '{agent_name}' is not available."
    
    logger.info(f"🎯 Sending query to {agent_name}: '{query}'")
    
    try:
        send_message_payload = {
            'message': {
                'role': 'user',
                'parts': [{'kind': 'text', 'text': query}],
                'message_id': uuid4().hex,
            },
        }
        request = SendMessageRequest(id=str(uuid4()), params=MessageSendParams(**send_message_payload))
        
        response = await client.send_message(request)
        
        if hasattr(response, 'root') and hasattr(response.root, 'result'):
            task = response.root.result
            if task.artifacts and task.artifacts[0].parts:
                response_text = task.artifacts[0].parts[0].root.text
                return f"🤖 **{agent_name}**: {response_text}"
            else:
                return f"🤖 **{agent_name}**: {str(task.status)}"
        else:
            return f"🤖 **{agent_name}**: {str(response)}"
            
    except Exception as e:
        return f"❌ Error communicating with {agent_name}: {e}"

async def simple_route_query(registry: AutoAgentRegistry, query: str) -> str:
    """Simple query routing without Pydantic AI agent to avoid Gemini issues."""
    query_lower = query.lower().strip()
    
    # Handle special commands
    if query_lower in ['list agents', 'show agents', 'agents']:
        if not registry.agent_cards:
            return "❌ No agents are currently available."
        
        result = f"🤖 Available agents ({len(registry.agent_cards)}):\n\n"
        for agent_name, info in registry.agent_cards.items():
            result += f"• **{agent_name}** ({info['url']})\n"
            result += f"  📝 {info['card'].description}\n"
        return result
    
    # Time-related queries
    if any(keyword in query_lower for keyword in ['time', 'clock', 'hour', 'minute', 'when']):
        if 'telltime_agent' in registry.agent_cards:
            return await _send_to_agent_simple(registry, query, 'telltime_agent')
    
    # Greeting queries
    if any(keyword in query_lower for keyword in ['hello', 'hi', 'greet', 'how are you', 'good morning', 'good afternoon', 'good evening']):
        if 'greeting_agent' in registry.agent_cards:
            return await _send_to_agent_simple(registry, query, 'greeting_agent')
    
    # Fallback to first available agent
    if registry.agent_cards:
        first_agent = next(iter(registry.agent_cards.keys()))
        return await _send_to_agent_simple(registry, query, first_agent)
    
    return "❌ No agents available to handle your request."

async def _send_to_agent_simple(registry: AutoAgentRegistry, query: str, agent_name: str) -> str:
    """Send query to agent without complex context handling."""
    client = registry.get_client(agent_name)
    if not client:
        return f"❌ Agent '{agent_name}' is not available."
    
    logger.info(f"🎯 Sending query to {agent_name}: '{query}'")
    
    try:
        send_message_payload = {
            'message': {
                'role': 'user',
                'parts': [{'kind': 'text', 'text': query}],
                'message_id': uuid4().hex,
            },
        }
        request = SendMessageRequest(id=str(uuid4()), params=MessageSendParams(**send_message_payload))
        
        response = await client.send_message(request)
        
        # Use exact same response handling as working client.py
        if hasattr(response, 'root') and hasattr(response.root, 'result'):
            task = response.root.result
            if task.artifacts and task.artifacts[0].parts:
                response_text = task.artifacts[0].parts[0].root.text
                logger.info(f"✅ Response from {agent_name}: {response_text}")
                return response_text
            else:
                logger.info(f"✅ Response from {agent_name}: {task}")
                return str(task)
        else:
            logger.info(f"📄 Full response: {response.model_dump_json(indent=2, exclude_none=True)}")
            return str(response)
            
    except Exception as e:
        error_msg = f"❌ Error communicating with {agent_name}: {e}"
        logger.error(error_msg)
        return error_msg

async def main():
    """Main entry point for the automatic orchestrator."""
    registry = AutoAgentRegistry()
    
    # Configure httpx for faster timeouts during discovery
    timeout = httpx.Timeout(connect=2.0, read=5.0, write=5.0, pool=5.0)
    
    async with httpx.AsyncClient(timeout=timeout) as httpx_client:
        context = AutoOrchestratorContext(registry, httpx_client)
        
        print("\n🤖 Automatic A2A Orchestrator Starting...")
        print("🔍 Auto-discovering available agents...")
        
        # Automatically discover agents at startup
        discovered = await registry.auto_discover_all_agents(httpx_client)
        
        if discovered:
            print(f"\n✅ Discovered {len(discovered)} agents:")
            for url, agent_name in discovered.items():
                agent_info = registry.agent_cards[agent_name]
                print(f"  🤖 {agent_name}: {agent_info['card'].description}")
        else:
            print("\n⚠️ No agents found. Make sure agents are running on ports: 3000, 5000, 8000, 8080, 9000")
            print("   You can start agents and I'll discover them automatically!")
        
        print("\n💬 I'm ready! Just ask me anything and I'll route it to the right agent automatically.")
        print("   Examples: 'What time is it?', 'Hello', 'Calculate 2+2'")
        print("   Type 'list agents' to see available agents, 'refresh' to rediscover, or 'exit' to quit.\n")
        
        while True:
            try:
                query = input("You: ").strip()
                if not query or query.lower() in {"exit", "quit"}:
                    print("👋 Goodbye!")
                    break
                
                # Handle refresh command
                if query.lower() in ['refresh', 'refresh agents']:
                    print("🔄 Refreshing agents...")
                    discovered = await registry.auto_discover_all_agents(httpx_client)
                    if discovered:
                        print(f"✅ Refreshed! Found {len(discovered)} agents.")
                    else:
                        print("❌ No agents found during refresh.")
                    continue
                
                # Process the query using simple routing (no Pydantic AI agent)
                response_text = await simple_route_query(registry, query)
                print(f"Assistant: {response_text}\n")
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}\n")

if __name__ == "__main__":
    asyncio.run(main())
