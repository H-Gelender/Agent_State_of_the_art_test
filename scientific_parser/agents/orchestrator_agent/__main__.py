import uvicorn
import asyncclick as click
from rich import print
from .agent import OrchestratorAgent

# --- Server Configuration ---
HOST = "0.0.0.0"
PORT = 10000
AGENT_NAME = "OrchestratorAgent"
AGENT_DESCRIPTION = "The main chat agent that delegates tasks to other agents."


@click.group()
def cli():
    """CLI for the Orchestrator Agent."""
    pass

@cli.command()
def start_server():
    """Starts the OrchestratorAgent as an A2A server."""
    orchestrator = OrchestratorAgent()
    app = orchestrator.to_a2a(
        name=AGENT_NAME,
        description=AGENT_DESCRIPTION,
        url=f"http://{HOST}:{PORT}"
    )
    print(f"🚀 Starting {AGENT_NAME} on http://{HOST}:{PORT}")
    uvicorn.run(app, host=HOST, port=PORT)

@cli.command()
@click.argument("prompt")
async def chat(prompt: str):
    """Starts a chat session with the orchestrator."""
    print(f"[bold blue]You:[/bold blue] {prompt}")
    orchestrator = OrchestratorAgent()
    response = await orchestrator.chat(prompt)
    print(f"[bold green]ArXiv Chatbot:[/bold green] {response}")


if __name__ == "__main__":
    cli()