#!/usr/bin/env python
"""
__main__.py

Point d'entrée du client MCP. Ce fichier:
  - Orchestre l'initialisation de tous les composants
  - Utilise mcp_utils pour la configuration et la connexion
  - Utilise agents.py pour créer l'agent
  - Fournit la boucle interactive

⚠️  NE PAS MODIFIER CE FICHIER pour changer l'agent ou le modèle.
    Modifiez agents.py à la place.

Usage:
    python -m <package_name>
"""

import asyncio
from contextlib import AsyncExitStack

from dotenv import load_dotenv

from .mcp_utils import (
    read_config_json,
    get_mcp_servers_config,
    connect_to_all_mcp_servers,
)
from .agent import get_agent

# Charger les variables d'environnement
load_dotenv()


async def run_interactive_loop(agent) -> None:
    """
    Exécute une boucle de chat interactive avec l'agent.
    
    Args:
        agent: AgentWrapper qui gère n'importe quel type d'agent
    """
    print("\n🚀 MCP Client Ready! Type 'quit' to exit.")
    
    while True:
        query = input("\nQuery: ").strip()
        if query.lower() == "quit":
            break
        
        if not query:
            continue
        
        # L'AgentWrapper gère automatiquement le format correct
        response = await agent.ainvoke(query)
        print(f"\nResponse:\n{response}")


async def main() -> None:
    """
    Fonction principale qui orchestre l'exécution du client MCP.
    """
    # Lire la configuration
    config = read_config_json()
    mcp_servers = get_mcp_servers_config(config)
    
    if not mcp_servers:
        print("❌ No MCP servers configured. Exiting.")
        return
    
    # Gérer les connexions MCP avec AsyncExitStack
    async with AsyncExitStack() as exit_stack:
        # Se connecter à tous les serveurs MCP et charger les outils
        tools = await connect_to_all_mcp_servers(
            mcp_servers,
            exit_stack,
            verbose=True
        )
        
        # Créer l'agent - TOUTE la configuration est dans agents.py
        agent = get_agent(tools)
        
        # Exécuter la boucle interactive
        await run_interactive_loop(agent)
    
    print("\n👋 Goodbye!")


if __name__ == "__main__":
    asyncio.run(main())