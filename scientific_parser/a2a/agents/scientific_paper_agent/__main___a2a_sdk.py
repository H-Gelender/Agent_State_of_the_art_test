"""Scientific paper parser agent using A2A SDK pattern.

This agent searches for scientific papers using an MCP server, extracts key information,
and saves them to a configured directory using the A2A protocol with AgentExecutor.

Run the MCP server first:
    python arxiv_server.py

Then run this agent:
    python __main__.py
"""

import os 
import logging
import sys
from pathlib import Path

import click
import httpx
from dotenv import load_dotenv

from .agent_executor import ScientificPaperAgentExecutor

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

# Configuration
OUTPUT_DIR = Path(os.environ.get('PAPER_OUTPUT_DIR', './parsed_papers'))
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def build_agent_card(host: str, port: int) -> AgentCard:
    """Build the agent card for the scientific paper agent."""
    return AgentCard(
        name="Scientific Paper Agent",
        description="An AI agent that searches for scientific papers using ArXiv, extracts key information like topics and overviews, and saves structured results to disk.",
        url=f"http://{host}:{port}/",
        version="1.0.0",
        capabilities=AgentCapabilities(streaming=True, push_notifications=True),
        default_input_modes=["text", "text/plain"],
        default_output_modes=["text", "text/plain", "application/json"],
        skills=[
            AgentSkill(
                id="paper_search",
                name="Scientific Paper Search",
                description="Search for scientific papers on ArXiv and extract detailed information including topics, abstracts, and relevance analysis",
                tags=["research", "papers", "arxiv", "scientific", "literature", "academic"],
                examples=[
                    "Find papers about machine learning in healthcare", 
                    "Search for recent research on quantum computing",
                    "Look for papers on climate change modeling",
                    "Find AI papers related to computer vision",
                    "Search for papers about deep learning applications"
                ],
            ),
            AgentSkill(
                id="paper_analysis", 
                name="Paper Analysis and Extraction",
                description="Analyze scientific papers to extract key topics, assess relevance, and provide structured overviews",
                tags=["analysis", "topics", "keywords", "relevance", "summary"],
                examples=[
                    "Analyze the relevance of papers to a specific research topic",
                    "Extract key topics and keywords from research papers", 
                    "Provide structured summaries of academic literature",
                    "Assess paper usefulness for research purposes"
                ],
            )
        ],
    )

@click.command()
@click.option('--host', 'host', default='0.0.0.0', help='Host to run the server on')
@click.option('--port', 'port', default=7000, help='Port to run the server on')
def main(host: str, port: int):
    """Main function to start the scientific paper A2A agent."""
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Check for required environment variables
    if not os.getenv("GOOGLE_API_KEY"):
        logger.error("GOOGLE_API_KEY environment variable not set")
        sys.exit(1)
    
    print(f"Starting Scientific Paper A2A Agent on http://{host}:{port}")
    print(f"Papers will be saved to: {OUTPUT_DIR.absolute()}")
    print("Use Ctrl+C to stop the server")
    
    # Create the agent executor
    try:
        agent_executor = ScientificPaperAgentExecutor()
    except ValueError as e:
        logger.error(f"Failed to initialize agent: {e}")
        sys.exit(1)
    
    # Set up A2A server components
    client = httpx.AsyncClient()
    push_config_store = InMemoryPushNotificationConfigStore()
    push_sender = BasePushNotificationSender(
        httpx_client=client,
        config_store=push_config_store
    )
    
    handler = DefaultRequestHandler(
        agent_executor=agent_executor,
        task_store=InMemoryTaskStore(),
        push_config_store=push_config_store,
        push_sender=push_sender
    )
    
    server = A2AStarletteApplication(
        agent_card=build_agent_card(host, port),
        http_handler=handler,
    )

    logger.info(f"Starting Scientific Paper Agent on {host}:{port}")
    uvicorn.run(server.build(), host=host, port=port)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nShutting down Scientific Paper A2A Agent...")
    except Exception as e:
        logging.error(f"Error starting agent: {e}")
        sys.exit(1)