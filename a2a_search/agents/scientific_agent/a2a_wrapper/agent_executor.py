"""
agent_executor.py (Version Corrigée)

Implémente l'interface AgentExecutor pour le Search Agent, en respectant
le contrat défini par la librairie a2a.
"""

# Importe les classes nécessaires de la librairie a2a
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils import new_agent_text_message
from a2a.types import TextPart

# Importe la logique de notre agent
try:
    from agents.scientific_agent.client.agent import AgentWrapper
    from agents.scientific_agent.client.__main__ import run_agent
except ImportError as e:
    print(f"❌ ImportError (absolute import): {e}")
    try:
        from client.agent import AgentWrapper
        from client.__main__ import run_agent
    except ImportError as e2:
        print(f"❌ ImportError (relative import): {e2}")
        raise
        
class SearchAgentExecutor(AgentExecutor):
    """
    Exécute les tâches pour le Search Agent en respectant le contrat A2A.
    """
    def __init__(self, agent: AgentWrapper):
        """
        Initialise l'executor avec l'instance de l'agent LangGraph.
        """
        self._agent = agent
        print("✅ SearchAgentExecutor (v2) initialized with a ready-to-use agent.")

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """
        Méthode appelée par le DefaultRequestHandler. C'est le point d'entrée.
        """
        print(f"▶️  Executor received task.")

        # 1. Extraire la question de l'utilisateur depuis le contexte.
        # Le message est dans context.request.params.message.parts
        query = ""
        try:
            # On cherche la partie textuelle du message de l'utilisateur
            for part in context.message.parts:
                if isinstance(part.root, TextPart):
                    query = part.root.text
                    break
            
            if not query:
                raise ValueError("No text found in user message.")

            print(f"    Query extracted: '{query}'")

        except (AttributeError, ValueError) as e:
            error_message = f"Could not extract query from request: {e}"
            print(f"❌ {error_message}")
            await event_queue.enqueue_event(new_agent_text_message(f"Error: {error_message}"))
            return

        # 2. Exécuter la logique de l'agent (le code qui fonctionnait déjà)
        print("    🚀 Calling the agent's core logic (run_agent)...")
        result_text = await run_agent(self._agent, query)
        print(f"    ✅ Agent returned result: '{result_text[:100]}...'")

        # 3. Publier le résultat dans la file d'événements.
        # Le serveur A2A s'occupera de l'envoyer au client.
        await event_queue.enqueue_event(new_agent_text_message(result_text))
        print("    📤 Result enqueued for the client.")

    async def cancel(
        self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        """
        Logique d'annulation (non supportée pour l'instant).
        """
        print(f"⚠️  Cancel request received for task {context.task_id}, but not supported.")
        # On pourrait ici publier un événement pour dire que l'annulation n'est pas possible.
        raise NotImplementedError("Cancellation is not supported by this agent.")
