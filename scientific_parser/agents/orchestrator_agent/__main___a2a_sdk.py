import os 
import logging
import sys

import click
import httpx
from dotenv import load_dotenv

# Add the current directory to the path to find the agent_executor module
sys.path.insert(0, os.path.dirname(__file__))

from agent_executor import ScientificPaperAgentExecutor

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler  
from a2a.server.tasks import (
    BasePushNotificationSender,
    InMemoryPushNotificationConfigStore,
    InMemoryTaskStore,
)
from a2a.types import AgentCard, AgentSkill, AgentCapabilities

import uvicorn

load_dotenv()

def build_agent_card(host: str, port: int) -> AgentCard:
    return AgentCard(
        name="Scientific Paper Agent",
        description="An intelligent agent that searches ArXiv for scientific papers, downloads PDFs, and extracts metadata using MCP tools.",
        url=f"http://{host}:{port}/",
        version="1.0.0",
        capabilities=AgentCapabilities(streaming=True, push_notifications=True),
        default_input_modes=["text", "text/plain"],
        default_output_modes=["text", "text/plain"],
        skills=[
            AgentSkill(
                id="arxiv_search",
                name="ArXiv Paper Search",
                description="Search ArXiv for scientific papers on any topic and download PDFs with metadata extraction.",
                tags=["arxiv", "research", "papers", "academic", "science", "download"],
                examples=[
                    "Find papers about machine learning",
                    "Search for quantum computing research",
                    "Look for papers on climate change",
                    "Find recent AI safety papers"
                ],
            ),
            AgentSkill(
                id="scientific_research",
                name="Scientific Research Assistant",
                description="Comprehensive scientific literature search and analysis with automatic PDF download and metadata extraction.",
                tags=["research", "analysis", "academic", "literature", "papers"],
                examples=[
                    "Research papers on neural networks from 2024",
                    "Find interdisciplinary research on biotechnology",
                    "Search for papers by specific authors",
                    "Look for papers with specific keywords"
                ],
            )
        ],
    )

@click.command()
@click.option('--host', 'host', default='localhost', help='Host to run the server on')
@click.option('--port', 'port', default=7000, help='Port to run the server on')
def main(host: str, port: int):
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Validate required environment variables
    if not os.getenv('GOOGLE_API_KEY'):
        logger.error("GOOGLE_API_KEY environment variable is required")
        sys.exit(1)
    
    logger.info("Starting Scientific Paper A2A Agent Server (A2A SDK version)...")
    logger.info(f"Server will run on http://{host}:{port}")
    
    # Create agent executor
    agent_executor = ScientificPaperAgentExecutor()
    
    # Create push notification components
    push_config_store = InMemoryPushNotificationConfigStore()
    push_sender = BasePushNotificationSender(
        httpx_client=httpx.AsyncClient(),
        config_store=push_config_store
    )
    
    # Create request handler
    request_handler = DefaultRequestHandler(
        agent_executor=agent_executor,
        task_store=InMemoryTaskStore(),
        push_config_store=push_config_store,
        push_sender=push_sender
    )
    
    # Create the A2A application
    server = A2AStarletteApplication(
        agent_card=build_agent_card(host, port),
        http_handler=request_handler,
    )
    
    # Run the server
    uvicorn.run(server.build(), host=host, port=port)

if __name__ == "__main__":
    main()