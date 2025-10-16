#!/usr/bin/env python
"""
__main__.py (Version Simplifiée)
- Utilise la nouvelle fonction 'create_and_initialize_agent' de agent.py.
- La logique de connexion a été déplacée.
"""

import asyncio
from dotenv import load_dotenv

# Importe la nouvelle fonction usine et les classes nécessaires
from .agent import create_and_initialize_agent, AgentWrapper

# Charger les variables d'environnement
load_dotenv()


async def run_agent(agent: AgentWrapper, query: str) -> str:
    """Exécute une seule requête (inchangé)."""
    if not query:
        return "Query cannot be empty."
    
    print(f"\n🤖 Agent received query: {query}")
    response = await agent.ainvoke(query)
    print(f"\n📄 Agent response: {response}")
    return response


async def run_interactive_loop(agent: AgentWrapper) -> None:
    """Exécute une boucle de chat interactive (inchangé)."""
    print("\n🚀 MCP Client Ready! Type 'quit' to exit.")
    
    while True:
        query = input("\nQuery: ").strip()
        if query.lower() == "quit":
            break
        
        if not query:
            continue
        
        response = await run_agent(agent, query)
        print(f"\nResponse:\n{response}")


async def main() -> None:
    """
    Fonction principale (MAINTENANT SIMPLIFIÉE).
    """
    # Utilise l'AsyncExitStack retourné par la fonction usine pour garantir
    # la fermeture propre des connexions à la fin du bloc 'with'.
    agent, exit_stack = await create_and_initialize_agent()
    async with exit_stack:
        # L'agent est déjà prêt, on lance la boucle
        await run_interactive_loop(agent)
    
    print("\n👋 Goodbye!")


if __name__ == "__main__":
    asyncio.run(main())