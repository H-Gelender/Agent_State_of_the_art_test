import logging
from typing import Any
from pydantic_ai import Agent, A2AClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Address of our Scientist Agent ---
SCIENTIST_AGENT_URL = "http://localhost:10001"


class OrchestratorAgent:
    """
    An AI agent that orchestrates tasks by delegating to specialized agents.
    It acts as the main entry point for user interaction.
    """

    def __init__(self, model: Any = "google:gemini-1.5-flash-latest"):
        """
        Initializes the OrchestratorAgent.
        """
        # This is the "brain" of the orchestrator.
        # Its instructions tell it HOW to use its tools.
        self.agent = Agent(
            model=model,
            instructions=(
                "You are an orchestrator. Your job is to understand the user's request "
                "and delegate it to the correct specialized agent. "
                "Use the 'delegate_to_scientist' tool to ask the ScientistAgent to perform research on arXiv."
            )
        )

        # Create a client to communicate with the ScientistAgent
        self.scientist_client = A2AClient(base_url=SCIENTIST_AGENT_URL)

        # Register the delegation tool
        self.agent.tool(self.delegate_to_scientist)

    async def delegate_to_scientist(self, research_query: str, num_articles: int = 3) -> str:
        """
        Delegates a research task to the ScientistAgent.

        Args:
            research_query (str): The topic or query to research on arXiv.
            num_articles (int): The number of articles to retrieve.

        Returns:
            str: The result from the ScientistAgent.
        """
        logger.info(f"Delegating task to ScientistAgent: query='{research_query}', num_articles={num_articles}")
        try:
            # This is the agent-to-agent call.
            # 'research_arxiv_and_save' is the name of the method on the ScientistAgent.
            # Pydantic-ai handles the network request and parameter mapping.
            response = await self.scientist_client.call(
                "research_arxiv_and_save",
                query=research_query,
                max_results=num_articles,
            )
            logger.info(f"Received response from ScientistAgent: {response}")
            return str(response)
        except Exception as e:
            logger.error(f"Failed to delegate task to ScientistAgent: {e}")
            return f"Error communicating with the ScientistAgent: {e}"

    async def chat(self, user_prompt: str) -> str:
        """
        The main chat method that the user interacts with.
        It runs the agent with the user's prompt.
        """
        logger.info(f"Orchestrator received user prompt: '{user_prompt}'")
        result = await self.agent.run(user_prompt)
        return result.output

    def to_a2a(self, **kwargs):
        """Exposes the underlying agent's to_a2a method."""
        return self.agent.to_a2a(**kwargs)