from dotenv import load_dotenv
import asyncio
import os
import json
import logging
from pathlib import Path
from typing import Any
from datetime import datetime

from pydantic_ai import Agent, RunContext
from pydantic_ai.mcp import MCPServerStreamableHTTP

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.types import (
    TaskArtifactUpdateEvent,
    TaskStatusUpdateEvent,
    TaskStatus,
    TaskState,
)
from a2a.utils import (
    new_agent_text_message,
    new_task,
    new_text_artifact
)

from .agent import PaperSearchResult, load_mcp_servers

logger = logging.getLogger(__name__)
load_dotenv()

# Configuration
OUTPUT_DIR = Path(os.environ.get('PAPER_OUTPUT_DIR', './parsed_papers'))
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

class ScientificPaperAgentExecutor(AgentExecutor):
    """Agent executor for the scientific paper search and analysis agent using A2A SDK pattern."""

    def __init__(self):
        # Check for Gemini API key
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is required for Gemini API")
        
        # Load MCP servers
        self.mcp_servers = load_mcp_servers()
        
        # Initialize the Pydantic AI agent
        self.agent = Agent(
            model="google-gla:gemini-2.5-flash-lite",
            output_type=PaperSearchResult,
            toolsets=self.mcp_servers,
            system_prompt="""You are a scientific paper analysis assistant. Your job is to:
            1. ALWAYS use the arxiv_retriever tool to search for scientific papers
            2. Extract key information including topics, keywords, and overviews
            3. Evaluate the usefulness of each paper for the given query
            4. Provide structured output that can be saved for later reference
            
            IMPORTANT: You MUST use the arxiv_retriever tool to search for papers. Never return empty results without using this tool.
            
            For topics, always use CAPITAL LETTERS for keywords.
            Be thorough and accurate in your extraction of information.
            Mark papers as useful=True if they are relevant to the query, False otherwise.
            """
        )

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        task = None
        try:
            query = context.get_user_input()
            task = context.current_task

            if not query:
                raise ValueError("No user input provided to the agent.")
            
            if not task:
                if context.message:
                    task = new_task(context.message)
                    await event_queue.enqueue_event(task)
                else:
                    raise ValueError("No message or task provided")
            
            logger.info(f"Processing scientific paper search query: {query}")
            
            # Send working status
            await event_queue.enqueue_event(
                TaskStatusUpdateEvent(
                    task_id=task.id,
                    context_id=task.context_id,
                    status=TaskStatus(
                        state=TaskState.working,
                        message=new_agent_text_message(
                            f"Searching for scientific papers about: {query}",
                            task.context_id,
                            task.id
                        ),
                    ),
                    final=False,
                )
            )
            
            # Parse max_results from query if specified
            max_results = 5
            if "max_results:" in query.lower():
                try:
                    parts = query.split("max_results:")
                    max_results = int(parts[1].strip().split()[0])
                    query = parts[0].strip()
                except:
                    pass
            
            # Use asyncio.to_thread to run the agent search in a separate thread
            result = await asyncio.to_thread(
                self._run_paper_search_sync,
                query,
                max_results
            )
                
            paper_results = result
            
            logger.info(f"Found {paper_results.total_found} papers for query: {query}")
            
            # Save results to file
            filename = query.lower().replace(' ', '_')
            filename = ''.join(c for c in filename if c.isalnum() or c == '_')
            filename = filename[:100]  # Limit length
            filename = f"{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            output_path = OUTPUT_DIR / f"{filename}.json"
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(paper_results.model_dump_json(indent=2))
            
            # Create response text
            response_lines = [
                f"Found {paper_results.total_found} papers for query: '{paper_results.query}'",
                f"Results saved to: {output_path}",
                "",
                "Papers found:"
            ]
            
            for i, paper in enumerate(paper_results.papers, 1):
                response_lines.extend([
                    f"{i}. {paper.title}",
                    f"   Authors: {', '.join(paper.authors)}",
                    f"   Topics: {', '.join(paper.topics)}",
                    f"   Useful: {paper.useful}",
                    f"   Overview: {paper.overview}",
                    ""
                ])
            
            response_text = "\n".join(response_lines)
            
            # Send artifact with the response
            await event_queue.enqueue_event(
                TaskArtifactUpdateEvent(
                    task_id=task.id,
                    context_id=task.context_id,
                    artifact=new_text_artifact(
                        name='paper_search_results',
                        description=f'Scientific paper search results for: {query}',
                        text=response_text,
                    ),
                    append=False,
                    last_chunk=True,
                )
            )
            
            # Also send the JSON data as an artifact
            await event_queue.enqueue_event(
                TaskArtifactUpdateEvent(
                    task_id=task.id,
                    context_id=task.context_id,
                    artifact=new_text_artifact(
                        name='paper_search_data',
                        description=f'Raw JSON data for papers about: {query}',
                        text=paper_results.model_dump_json(indent=2),
                    ),
                    append=False,
                    last_chunk=True,
                )
            )
            
            # Mark task as completed
            await event_queue.enqueue_event(
                TaskStatusUpdateEvent(
                    task_id=task.id,
                    context_id=task.context_id,
                    status=TaskStatus(state=TaskState.completed),
                    final=True,
                )
            )
            
        except Exception as e:
            logger.error(f"Error in scientific paper agent execution: {e}")
            
            # Send error status
            await event_queue.enqueue_event(
                TaskStatusUpdateEvent(
                    task_id=task.id if task else "unknown",
                    context_id=task.context_id if task else "unknown",
                    status=TaskStatus(
                        state=TaskState.failed,
                        message=new_agent_text_message(
                            f"Error searching for papers: {str(e)}",
                            task.context_id if task else "unknown",
                            task.id if task else "unknown"
                        ),
                    ),
                    final=True,
                )
            )

    def _run_paper_search_sync(self, query: str, max_results: int) -> PaperSearchResult:
        """Run paper search synchronously with proper MCP connection management."""
        import asyncio
        
        # Create a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            return loop.run_until_complete(self._async_paper_search(query, max_results))
        finally:
            loop.close()
    
    async def _async_paper_search(self, query: str, max_results: int) -> PaperSearchResult:
        """Async paper search with proper MCP connection management."""
        async with self.agent:
            result = await self.agent.run(
                f"Search for papers about: {query}. Find up to {max_results} papers and extract detailed information from each one."
            )
            return result.output

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise Exception('Cancel not supported')