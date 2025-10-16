import sys
import os
import asyncio

import uvicorn
from dotenv import load_dotenv

# Imports depuis la nouvelle version de la librairie a2a
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCard, AgentSkill, AgentCapabilities

# --- Intégration de votre logique existante ---
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
try:
    from agents.scientific_agent.client.agent import create_and_initialize_agent
    from agents.scientific_agent.a2a_wrapper.agent_executor import SearchAgentExecutor
    from agents.scientific_agent.a2a_wrapper.config import HOST, PORT, PUBLIC_HOST, MODEL

except ImportError as e:
    print(f"❌ ImportError (absolute import): {e}")
    try:
        from client.agent import create_and_initialize_agent
        from agent_executor import SearchAgentExecutor
    except ImportError as e2:
        print(f"❌ ImportError (relative import): {e2}")
        raise
# ---------------------------------------------
load_dotenv()

def debug(msg: str):
    """Fonction utilitaire pour le débogage."""
    print(f"[DEBUG] {msg}")

async def main_a2a():
    """
    Fonction principale pour le wrapper A2A, mise à jour pour la nouvelle API.
    """

    initialized_agent, exit_stack = await create_and_initialize_agent()

    search_skill = AgentSkill(
        id='search',  # Un identifiant unique pour le skill
        name='Web Search Skill',
        description='Performs a web search for a given query.',
        tags=["research", "web", "information", "up to date information"],
        examples=['What is the A2A protocol?']
    )

    # Configuration depuis config.py
    host = HOST
    port = PORT
    public_host = PUBLIC_HOST
    
    capabilities = AgentCapabilities(streaming=False, push_notifications=False)

    agent_card = AgentCard(
        name='Search Agent (A2A)',
        description='An agent that can perform web searches and provide answers.',
        url=f'http://{public_host}:{port}/',
        version='1.0.0',
        skills=[search_skill],
        capabilities=capabilities,
        default_input_modes=['text/plain'],
        default_output_modes=['text/plain'],
    )
    # 4. Créer l'AgentExecutor avec l'agent initialisé
    agent_executor = SearchAgentExecutor(agent=initialized_agent)

    # 5. Configurer le gestionnaire de requêtes (Request Handler)
    # C'est le cœur du serveur A2A. Il utilise l'executor pour faire le travail.
    request_handler = DefaultRequestHandler(
        agent_executor=agent_executor,
        task_store=InMemoryTaskStore(), # Stockage en mémoire pour les tâches
    )

    # 6. Construire l'application serveur A2A
    server_app = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler,
    )

    print("🚀 Starting A2A Agent Wrapper (New API)...")
    print(f"   Listening on {host}:{port}")
    print(f"   Agent Card will be available at http://{public_host}:{port}/.well-known/agent.json")

    # 7. Lancer le serveur avec Uvicorn
    config = uvicorn.Config(server_app.build(), host=host, port=port)
    server = uvicorn.Server(config)
    
    # server.serve() est une coroutine, elle s'intègre donc parfaitement
    # dans notre boucle d'événements existante.
    await server.serve()


if __name__ == "__main__":
    try:
        asyncio.run(main_a2a())
    except KeyboardInterrupt:
        print("\n👋 Server stopped gracefully.")