import asyncio
import httpx
import json
import logging
from pathlib import Path
from uuid import uuid4
from typing import Dict, Optional

from a2a.client import A2AClient, A2ACardResolver
from a2a.types import (
    MessageSendParams,
    SendMessageRequest,
    SendStreamingMessageRequest,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgentRegistry:
    """Manages discovery and access to multiple A2A agents."""
    
    def __init__(self, registry_path: str = "client/agent_registry.json"):
        self.registry_path = Path(registry_path)
        self.agents: Dict[str, str] = {}
        self.agent_cards: Dict[str, dict] = {}
        self.clients: Dict[str, A2AClient] = {}
        
    def load_registry(self) -> Dict[str, str]:
        """Load agent registry from JSON file."""
        try:
            with open(self.registry_path, 'r') as f:
                self.agents = json.load(f)
            logger.info(f"Loaded {len(self.agents)} agents from registry:")
            for name, url in self.agents.items():
                logger.info(f"  - {name}: {url}")
            return self.agents
        except FileNotFoundError:
            logger.error(f"Registry file not found: {self.registry_path}")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in registry file: {e}")
            return {}
    
    async def discover_agents(self, httpx_client: httpx.AsyncClient) -> Dict[str, dict]:
        """Discover agent capabilities by fetching their agent cards."""
        discovered = {}
        
        for agent_name, agent_url in self.agents.items():
            try:
                logger.info(f"Discovering capabilities for {agent_name} at {agent_url}")
                resolver = A2ACardResolver(httpx_client=httpx_client, base_url=agent_url)
                agent_card = await resolver.get_agent_card()
                
                discovered[agent_name] = {
                    'url': agent_url,
                    'card': agent_card,
                    'capabilities': agent_card.capabilities.model_dump() if agent_card.capabilities else {},
                    'skills': [skill.model_dump() for skill in agent_card.skills] if agent_card.skills else []
                }
                
                # Create A2A client for this agent
                self.clients[agent_name] = A2AClient(httpx_client=httpx_client, agent_card=agent_card)
                
                logger.info(f"✅ {agent_name}: {agent_card.description}")
                
            except Exception as e:
                logger.error(f"❌ Failed to discover {agent_name} at {agent_url}: {e}")
        
        self.agent_cards = discovered
        return discovered
    
    def get_client(self, agent_name: str) -> Optional[A2AClient]:
        """Get A2A client for a specific agent."""
        return self.clients.get(agent_name)
    
    def list_agents(self) -> None:
        """Display available agents and their capabilities."""
        if not self.agent_cards:
            print("No agents discovered yet.")
            return
            
        print("\n=== Available Agents ===")
        for i, (name, info) in enumerate(self.agent_cards.items(), 1):
            card = info['card']
            print(f"\n{i}. {name.upper()}")
            print(f"   📍 URL: {info['url']}")
            print(f"   📋 Description: {card.description}")
            
            if info['skills']:
                print("   🛠️  Skills:")
                for skill in info['skills']:
                    print(f"      - {skill['name']}: {skill['description']}")
                    if skill.get('examples'):
                        print(f"        Examples: {', '.join(skill['examples'][:2])}")
            
            capabilities = info['capabilities']
            caps_list = []
            if capabilities.get('streaming'):
                caps_list.append("Streaming")
            if capabilities.get('pushNotifications'):
                caps_list.append("Push Notifications")
            
            if caps_list:
                print(f"   ⚡ Capabilities: {', '.join(caps_list)}")

async def run_non_streaming_test(client: A2AClient, query: str, agent_name: str):
    """Sends a non-streaming message to the agent."""
    logger.info(f"\n--- Sending Non-Streaming Request to {agent_name} ---")
    
    send_message_payload = {
        'message': {
            'role': 'user',
            'parts': [{'kind': 'text', 'text': query}],
            'message_id': uuid4().hex,
        },
    }
    request = SendMessageRequest(
        id=str(uuid4()), params=MessageSendParams(**send_message_payload)
    )

    response = await client.send_message(request)
    
    # Extract and display the response in a user-friendly way
    if hasattr(response, 'root') and hasattr(response.root, 'result'):
        task = response.root.result
        if task.artifacts and task.artifacts[0].parts:
            response_text = task.artifacts[0].parts[0].root.text
            print(f"\n🤖 {agent_name} Response: {response_text}")
        else:
            print(f"\n🤖 {agent_name} Response: {task}")
    else:
        print(f"\n🤖 {agent_name} Full Response:")
        print(response.model_dump_json(indent=2, exclude_none=True))
    
    return response

async def run_streaming_test(client: A2AClient, query: str, agent_name: str):
    """Sends a streaming message to the agent."""
    logger.info(f"\n--- Sending Streaming Request to {agent_name} ---")

    send_message_payload = {
        'message': {
            'role': 'user',
            'parts': [{'kind': 'text', 'text': query}],
            'message_id': uuid4().hex,
        },
    }
    streaming_request = SendStreamingMessageRequest(
        id=str(uuid4()), params=MessageSendParams(**send_message_payload)
    )

    stream_response = client.send_message_streaming(streaming_request)
    
    print(f"\n🔄 Streaming response from {agent_name}:")
    async for chunk in stream_response:
        print(f"📦 Chunk: {chunk.model_dump_json(indent=2, exclude_none=True)}")

def select_agent(registry: AgentRegistry) -> Optional[str]:
    """Allow user to select an agent from the registry."""
    registry.list_agents()
    
    if not registry.agent_cards:
        return None
    
    agent_names = list(registry.agent_cards.keys())
    
    while True:
        try:
            print(f"\nSelect an agent (1-{len(agent_names)}) or 0 to quit:")
            choice = input("Enter your choice: ").strip()
            
            if choice == '0':
                return None
            
            choice_idx = int(choice) - 1
            if 0 <= choice_idx < len(agent_names):
                selected_agent = agent_names[choice_idx]
                print(f"✅ Selected: {selected_agent}")
                return selected_agent
            else:
                print("❌ Invalid choice. Please try again.")
                
        except (ValueError, KeyboardInterrupt):
            print("❌ Invalid input. Please enter a number.")
            return None

async def main():
    """Main function to run the multi-agent client."""
    registry = AgentRegistry()
    
    # Load the agent registry
    if not registry.load_registry():
        print("❌ Failed to load agent registry. Please check the registry file.")
        return
    
    async with httpx.AsyncClient() as httpx_client:
        # Discover all agents
        print("\n🔍 Discovering agents...")
        await registry.discover_agents(httpx_client)
        
        if not registry.agent_cards:
            print("❌ No agents were successfully discovered.")
            return
        
        print(f"\n✅ Successfully discovered {len(registry.agent_cards)} agents!")
        
        while True:
            # Select an agent
            selected_agent = select_agent(registry)
            if not selected_agent:
                print("👋 Goodbye!")
                break
            
            client = registry.get_client(selected_agent)
            if not client:
                print(f"❌ No client available for {selected_agent}")
                continue
            
            # Interact with the selected agent
            while True:
                query = input(f"\n💬 Enter a message for {selected_agent} (or press Enter to change agent): ")
                if not query:
                    break
                
                mode = input("Send as (s)treaming or (n)on-streaming? [s/n]: ").lower()

                try:
                    if mode == 'n':
                        await run_non_streaming_test(client, query, selected_agent)
                    elif mode == 's':
                        await run_streaming_test(client, query, selected_agent)
                    else:
                        print("❌ Invalid mode. Please enter 's' or 'n'.")
                        
                except Exception as e:
                    logger.error(f"❌ Error communicating with {selected_agent}: {e}")

if __name__ == "__main__":
    asyncio.run(main())