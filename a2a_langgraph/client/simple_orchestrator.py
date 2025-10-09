import asyncio
import httpx
import logging
import json
from pathlib import Path
from uuid import uuid4
from typing import Dict, Optional
from dotenv import load_dotenv

from pydantic_ai import Agent, RunContext

from a2a.client import A2AClient, A2ACardResolver
from a2a.types import MessageSendParams, SendMessageRequest

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleAgentRegistry:
    """Simple registry that loads agents from registry file only."""
    
    def __init__(self, registry_path: str = "client/agent_registry.json"):
        self.registry_path = Path(registry_path)
        self.agents: Dict[str, str] = {}  # name -> url
        self.agent_cards: Dict[str, dict] = {}  # name -> card info
        self.clients: Dict[str, A2AClient] = {}  # name -> client
    
    def load_registry(self) -> Dict[str, str]:
        """Load agents from the registry file."""
        try:
            if self.registry_path.exists():
                with open(self.registry_path, 'r') as f:
                    self.agents = json.load(f)
                logger.info(f"📂 Loaded {len(self.agents)} agents from registry")
                return self.agents
            else:
                logger.warning(f"Registry file not found: {self.registry_path}")
                return {}
        except Exception as e:
            logger.error(f"Failed to load registry: {e}")
            return {}
    
    async def discover_agents(self, httpx_client: httpx.AsyncClient) -> Dict[str, dict]:
        """Discover agents from the registry file."""
        discovered = {}
        
        for agent_name, agent_url in self.agents.items():
            try:
                logger.info(f"🔍 Discovering {agent_name} at {agent_url}")
                resolver = A2ACardResolver(httpx_client=httpx_client, base_url=agent_url)
                agent_card = await resolver.get_agent_card()
                
                discovered[agent_name] = {
                    'url': agent_url,
                    'card': agent_card,
                    'capabilities': agent_card.capabilities.model_dump() if agent_card.capabilities else {},
                    'skills': [skill.model_dump() for skill in agent_card.skills] if agent_card.skills else []
                }
                self.clients[agent_name] = A2AClient(httpx_client=httpx_client, agent_card=agent_card)
                logger.info(f"✅ Successfully registered {agent_name}")
                
            except Exception as e:
                logger.error(f"❌ Failed to discover {agent_name} at {agent_url}: {e}")
        
        self.agent_cards = discovered
        return discovered
    
    def get_client(self, agent_name: str) -> Optional[A2AClient]:
        return self.clients.get(agent_name)

class OrchestratorContext:
    """Context for the orchestrator."""
    def __init__(self, registry: SimpleAgentRegistry, httpx_client: httpx.AsyncClient):
        self.registry = registry
        self.httpx_client = httpx_client

async def delegate_to_agent(ctx: RunContext[OrchestratorContext], query: str, agent_name: str) -> str:
    """
    Delegate a query to a specific agent by name.
    
    Args:
        query: The user's query to send to the agent
        agent_name: The name of the agent to delegate to
    
    Returns:
        The response from the delegated agent
    """
    registry = ctx.deps.registry
    client = registry.get_client(agent_name)
    
    if not client:
        available_agents = list(registry.agents.keys())
        error_msg = f"❌ Agent '{agent_name}' is not available. Available agents: {', '.join(available_agents)}"
        logger.warning(error_msg)
        return error_msg
    
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
        
        # Extract response using EXACT same pattern as working client.py
        if hasattr(response, 'root') and hasattr(response.root, 'result'):
            task = response.root.result
            if task.artifacts and task.artifacts[0].parts:
                response_text = task.artifacts[0].parts[0].root.text
                logger.info(f"✅ Response from {agent_name}: {response_text}")
                return f"🤖 **{agent_name}**: {response_text}"
            else:
                logger.info(f"✅ Response from {agent_name}: {task}")
                return f"🤖 **{agent_name}**: {str(task)}"
        else:
            logger.info(f"📄 Full response: {response.model_dump_json(indent=2, exclude_none=True)}")
            return f"🤖 **{agent_name}**: {str(response)}"
        
    except Exception as e:
        error_msg = f"❌ Error communicating with {agent_name}: {e}"
        logger.error(error_msg)
        return error_msg

async def list_available_agents(ctx: RunContext[OrchestratorContext]) -> str:
    """List all currently available agents and their capabilities."""
    registry = ctx.deps.registry
    
    if not registry.agent_cards:
        return "❌ No agents are currently available."
    
    result = f"🤖 Available agents ({len(registry.agent_cards)}):\n\n"
    for agent_name, info in registry.agent_cards.items():
        result += f"• **{agent_name}** ({info['url']})\n"
        result += f"  📝 {info['card'].description}\n"
        
        skills = info.get('skills', [])
        if skills:
            result += "  🛠️ Skills:\n"
            for skill in skills:
                result += f"    - {skill.get('name', 'Unknown')}: {skill.get('description', 'No description')}\n"
        result += "\n"
    
    return result

# Create the orchestrator agent
orchestrator_agent = Agent(
    model="google-gla:gemini-2.5-flash-lite",
    output_type=str,
    system_prompt="""You are an intelligent orchestrator that manages multiple A2A agents.

Your behavior:
1. **Smart Delegation**: Analyze user queries and delegate to the appropriate agent
2. **Agent Management**: Show available agents when requested
3. **Natural Responses**: Provide conversational responses

AVAILABLE TOOLS:
- delegate_to_agent(query, agent_name): Send queries to specific agents
- list_available_agents(): Show all available agents

AGENT SELECTION RULES:
- Time queries (what time, current time, clock) → use "telltime_agent"
- Greetings (hello, hi, how are you) → use "greeting_agent"  
- If unsure, try the most relevant agent based on keywords

EXAMPLES:
- User: "What time is it?" → delegate_to_agent("What time is it?", "telltime_agent")
- User: "Hello" → delegate_to_agent("Hello", "greeting_agent")
- User: "List agents" → list_available_agents()

Always be helpful and provide clear responses.""",
    tools=[delegate_to_agent, list_available_agents],
)

async def main():
    """Main entry point for the orchestrator."""
    registry = SimpleAgentRegistry()
    
    # Load agents from registry file
    if not registry.load_registry():
        print("❌ No agents found in registry file. Please check client/agent_registry.json")
        return
    
    async with httpx.AsyncClient() as httpx_client:
        context = OrchestratorContext(registry, httpx_client)
        
        print(f"\n🤖 A2A Orchestrator Starting...")
        print(f"📂 Found {len(registry.agents)} agents in registry")
        
        # Discover the agents
        discovered = await registry.discover_agents(httpx_client)
        
        if discovered:
            print(f"\n✅ Successfully connected to {len(discovered)} agents:")
            for agent_name, info in discovered.items():
                print(f"  🤖 {agent_name}: {info['card'].description}")
        else:
            print("\n⚠️ Could not connect to any agents. Make sure they are running.")
            return
        
        print("\n💬 Ready! Ask me anything and I'll route it to the right agent.")
        print("   Examples: 'What time is it?', 'Hello', 'List agents'")
        print("   Type 'exit' to quit.\n")
        
        while True:
            try:
                query = input("You: ").strip()
                if not query or query.lower() in {"exit", "quit"}:
                    print("👋 Goodbye!")
                    break
                
                # Process the query through the orchestrator
                result = await orchestrator_agent.run(query, deps=context)
                response_text = result.output
                
                print(f"Assistant: {response_text}\n")
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}\n")

if __name__ == "__main__":
    asyncio.run(main())