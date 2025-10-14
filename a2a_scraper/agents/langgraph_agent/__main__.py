import os 
import logging
import sys

import click
import httpx
from dotenv import load_dotenv

from .agent import TellTimeAgent
from .agent_executor import TellTimeAgentExecutor

# --- These are the CORRECT imports from a2a-sdk ---
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler  
from a2a.server.tasks import (
    BasePushNotificationSender,
    InMemoryPushNotificationConfigStore,
    InMemoryTaskStore,
)
from a2a.types import AgentCard, AgentSkill, AgentCapabilities
# ----------------------------------------------------

import uvicorn

load_dotenv()

def build_agent_card(host: str, port: int) -> AgentCard:
    return AgentCard(
        name="TellTime Agent",
        description="Tells the current system time.",
        url=f"http://{host}:{port}/",
        version="1.0.0",
        capabilities=AgentCapabilities(streaming=True, pushNotifications=True),
        defaultInputModes=TellTimeAgent.SUPPORTED_CONTENT_TYPES,
        defaultOutputModes=TellTimeAgent.SUPPORTED_CONTENT_TYPES,
        skills=[
            AgentSkill(
                id="tell_time",
                name="Get Current Time",
                description="Tells the current system time in HH:MM:SS format.",
                tags=["time", "clock"],
                examples=["What time is it?", "Tell me the current time."],
            )
        ],
    )

@click.command()
@click.option('--host', 'host', default='localhost', help='Host to run the server on')
@click.option('--port', 'port', default=8000, help='Port to run the server on')
def main(host: str, port: int):
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    logger = logging.getLogger(__name__)

    agent_executor = TellTimeAgentExecutor()

    if not os.getenv("GOOGLE_API_KEY"):
        logger.error("GOOGLE_API_KEY environment variable not set")
        sys.exit(1)

    client = httpx.AsyncClient()
    push_config_store = InMemoryPushNotificationConfigStore()
    push_sender = BasePushNotificationSender(httpx_client=client,
                    config_store=push_config_store)
    
    # This handler knows how to call `execute` with an `event_queue`.
    handler = DefaultRequestHandler(
        agent_executor = agent_executor,
        task_store = InMemoryTaskStore(),
        push_config_store=push_config_store,
        push_sender=push_sender
    )
    
    # This application uses the DefaultRequestHandler correctly.
    server = A2AStarletteApplication(
        agent_card = build_agent_card(host, port),
        http_handler=handler,
    )

    uvicorn.run(server.build(), host=host, port=port)

if __name__ == "__main__":
    main()