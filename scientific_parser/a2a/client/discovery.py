import json
from pathlib import Path
from typing import Dict, Optional
import os

def load_agent_registry(file_path: str) -> Dict[str, str]:
    """Load the agent registry from a JSON file."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Agent registry file not found: {file_path}")
    
    with open(path, 'r') as file:
        registry = json.load(file)
    
    return registry

class AgentDiscovery:
    def __init__(self):
        self.registry_file = os.path.join(
            os.path.dirname(__file__),
            "agent_registry.json"
        )
        self.registry = load_agent_registry(self.registry_file)
        self.names = list(self.registry.keys())
        self.urls = list(self.registry.values())
    def get_agent_url(self, agent_name: str) -> Optional[str]:
        """Get the URL of an agent by its name."""
        return self.registry.get(agent_name)

    def list_agents(self) -> Dict[str, str]:
        """List all registered agents."""
        return self.registry