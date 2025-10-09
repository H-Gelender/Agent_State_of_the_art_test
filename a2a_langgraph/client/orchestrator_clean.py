import asyncio
import httpx
import json
import logging
from pathlib import Path
from uuid import uuid4
from typing import Dict, Optional

from a2a.client import A2AClient, A2ACardResolver
from a2a.types import MessageSendParams, SendMessageRequest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleAgentRegistry:
    """Simple agent registry that loads from JSON file."""
    
    def __init__(self, registry_path: str = "client/agent_registry.json"):
        self.registry_path = Path(registry_path)
        self.agents: Dict[str, str] = {}
        self.clients: Dict[str, A2AClient] = {}
    
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
        """Discover agent capabilities."""
        discovered = 0
        for name, url in self.agents.items():
            try:
                resolver = A2ACardResolver(httpx_client=httpx_client, base_url=url)
                agent_card = await resolver.get_agent_card()
                self.clients[name] = A2AClient(httpx_client=httpx_client, agent_card=agent_card)
                logger.info(f"✅ Connected to {name}")
                discovered += 1
            except Exception as e:
                logger.warning(f"❌ Failed to connect to {name}: {e}")
        return discovered
    
    def get_client(self, agent_name: str) -> Optional[A2AClient]:
        """Get client for an agent."""
        return self.clients.get(agent_name)

async def route_query(registry: SimpleAgentRegistry, query: str) -> str:
    """Route query to appropriate agent."""
    query_lower = query.lower().strip()
    
    # Route based on keywords
    if any(keyword in query_lower for keyword in ['time', 'clock', 'hour', 'when']):
        return await send_to_agent(registry, query, 'telltime_agent')
    
    if any(keyword in query_lower for keyword in ['hello', 'hi', 'greet', 'how are you']):
        return await send_to_agent(registry, query, 'greeting_agent')
    
    if query_lower in ['list', 'agents', 'list agents']:
        return f"Available agents: {', '.join(registry.agents.keys())}"
    
    # Fallback to first available agent
    if registry.clients:
        first_agent = next(iter(registry.clients.keys()))
        return await send_to_agent(registry, query, first_agent)
    
    return "❌ No agents available"

async def send_to_agent(registry: SimpleAgentRegistry, query: str, agent_name: str) -> str:
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
    """Main orchestrator."""
    registry = SimpleAgentRegistry()
    
    if not registry.load_registry():
        print("❌ Failed to load agent registry")
        return
    
    async with httpx.AsyncClient() as client:
        discovered = await registry.discover_agents(client)
        
        if discovered == 0:
            print("❌ No agents connected")
            return
        
        print(f"✅ Connected to {discovered} agents")
        print("💬 Ready! Type 'exit' to quit.\n")
        
        while True:
            try:
                query = input("You: ").strip()
                if not query or query.lower() in ["exit", "quit"]:
                    break
                
                response = await route_query(registry, query)
                print(f"Assistant: {response}\n")
                
            except KeyboardInterrupt:
                break
        
        print("👋 Goodbye!")

if __name__ == "__main__":
    asyncio.run(main())