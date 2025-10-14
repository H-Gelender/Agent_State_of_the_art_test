import json
import logging
from pathlib import Path
from typing import Dict, Optional
from a2a.client import A2AClient, A2ACardResolver

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

    async def discover_agents(self, httpx_client) -> int:
        """Discover agent capabilities and build detailed registry."""
        discovered = 0
        for name, url in self.agents.items():
            try:
                resolver = A2ACardResolver(httpx_client=httpx_client, base_url=url)
                agent_card = await resolver.get_agent_card()
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
                    ],
                    'tags': getattr(agent_card, 'tags', [])
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
