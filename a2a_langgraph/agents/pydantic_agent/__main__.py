import os 
import logging
import sys

import click
import httpx
from dotenv import load_dotenv

from .agent_executor import GreetingAgentExecutor

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
        name="Greeting Agent",
        description="A friendly agent that can greet people and have conversations.",
        url=f"http://{host}:{port}/",
        version="1.0.0",
        capabilities=AgentCapabilities(streaming=True, pushNotifications=True),
        defaultInputModes=["text", "text/plain"],
        defaultOutputModes=["text", "text/plain"],
        skills=[
            AgentSkill(
                id="greet",
                name="Greet People",
                description="Provides friendly greetings and casual conversation.",
                tags=["greeting", "conversation", "social"],
                examples=["Hello!", "Hi there!", "How are you?", "Good morning!"],
            )
        ],
    )

@click.command()
@click.option('--host', 'host', default='localhost', help='Host to run the server on')
@click.option('--port', 'port', default=5000, help='Port to run the server on')
def main(host: str, port: int):
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    logger = logging.getLogger(__name__)

    agent_executor = GreetingAgentExecutor()

    if not os.getenv("GOOGLE_API_KEY"):
        logger.error("GOOGLE_API_KEY environment variable not set")
        sys.exit(1)

    client = httpx.AsyncClient()
    push_config_store = InMemoryPushNotificationConfigStore()
    push_sender = BasePushNotificationSender(httpx_client=client,
                    config_store=push_config_store)
    
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

    logger.info(f"Starting Greeting Agent on {host}:{port}")
    uvicorn.run(server.build(), host=host, port=port)

if __name__ == "__main__":
    main()