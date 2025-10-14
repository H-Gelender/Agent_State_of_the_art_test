from dotenv import load_dotenv
import asyncio
import os
import logging
import json

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

# Import from the a2a scientific agent
import sys
parent_parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
a2a_scientific_agent_path = os.path.join(parent_parent_dir, 'a2a', 'agents', 'scientific_paper_agent')
sys.path.insert(0, a2a_scientific_agent_path)

from agent import search_and_parse_papers

logger = logging.getLogger(__name__)
load_dotenv()


class ScientificPaperAgentExecutor(AgentExecutor):
    """Agent executor for the scientific paper search agent using A2A SDK pattern."""

    def __init__(self):
        """Initialize the scientific paper agent executor."""
        # Validate required environment variables
        if not os.getenv('GOOGLE_API_KEY'):
            raise ValueError("GOOGLE_API_KEY environment variable is required")
        
        self.output_dir = os.getenv('PAPER_OUTPUT_DIR', 'data')

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Execute the scientific paper search request."""
        try:
            query = context.get_user_input()
            task = context.current_task

            if not query:
                raise ValueError("No search query provided to the agent.")
            
            if not task:
                task = new_task(context.message)
                await event_queue.enqueue_event(task)

            logger.info(f"Starting scientific paper search for query: {query}")
            
            # Update task status to running
            await event_queue.enqueue_event(
                TaskStatusUpdateEvent(
                    task_id=task.id,
                    context_id=task.context_id,
                    status=TaskStatus(
                        state=TaskState.working,
                        message=new_agent_text_message(
                            "Starting paper search...",
                            task.context_id,
                            task.id
                        ),
                    ),
                    final=False,
                )
            )

            # Create task for async execution in separate thread
            result = await asyncio.to_thread(self._run_paper_search_sync, query)

            # Handle both PaperSearchResult object and dict formats
            papers = []
            if result:
                try:
                    if hasattr(result, 'papers'):
                        papers = result.papers  # type: ignore
                    elif isinstance(result, dict) and 'papers' in result:
                        papers = result['papers']
                except Exception as e:
                    logger.warning(f"Error accessing papers from result: {e}")
                    papers = []
                    
            if papers:
                logger.info(f"Found {len(papers)} papers")
                
                # Create summary artifact
                summary_text = f"Found {len(papers)} papers:\n\n"
                for i, paper in enumerate(papers[:5], 1):  # Show first 5 papers
                    if hasattr(paper, 'title'):  # Pydantic object
                        title = paper.title
                        authors = paper.authors if hasattr(paper, 'authors') else []
                        overview = getattr(paper, 'overview', 'No overview available')
                    else:  # Dict object
                        title = paper.get('title', 'No title')
                        authors = paper.get('authors', [])
                        overview = paper.get('overview', paper.get('summary', 'No overview available'))
                    
                    summary_text += f"{i}. {title}\n"
                    summary_text += f"   Authors: {', '.join(authors)}\n"
                    summary_text += f"   Overview: {overview[:200]}...\n\n"
                
                if len(papers) > 5:
                    summary_text += f"... and {len(papers) - 5} more papers.\n"

                await event_queue.enqueue_event(
                    TaskArtifactUpdateEvent(
                        task_id=task.id,
                        context_id=task.context_id,
                        artifact=new_text_artifact(
                            name="Paper Search Results",
                            description="Summary of found papers",
                            text=summary_text
                        ),
                        append=False,
                        last_chunk=False,
                    )
                )

                # Create detailed results artifact as JSON
                try:
                    if hasattr(result, 'model_dump'):
                        result_json = result.model_dump()  # type: ignore
                    elif hasattr(result, 'dict'):
                        result_json = result.dict()  # type: ignore
                    else:
                        result_json = dict(result) if result else {}
                except:
                    result_json = {"papers": [dict(p) if hasattr(p, 'dict') else p for p in papers]}
                    
                await event_queue.enqueue_event(
                    TaskArtifactUpdateEvent(
                        task_id=task.id,
                        context_id=task.context_id,
                        artifact=new_text_artifact(
                            name="Detailed Results (JSON)",
                            description="Full paper data in JSON format",
                            text=json.dumps(result_json, indent=2, ensure_ascii=False, default=str)
                        ),
                        append=False,
                        last_chunk=True,
                    )
                )

                # Update task status to completed
                await event_queue.enqueue_event(
                    TaskStatusUpdateEvent(
                        task_id=task.id,
                        context_id=task.context_id,
                        status=TaskStatus(state=TaskState.completed),
                        final=True,
                    )
                )
            else:
                # No papers found - create artifact with message
                await event_queue.enqueue_event(
                    TaskArtifactUpdateEvent(
                        task_id=task.id,
                        context_id=task.context_id,
                        artifact=new_text_artifact(
                            name="Search Results",
                            description="Paper search results",
                            text="No papers found for the given query."
                        ),
                        append=False,
                        last_chunk=True,
                    )
                )

                await event_queue.enqueue_event(
                    TaskStatusUpdateEvent(
                        task_id=task.id,
                        context_id=task.context_id,
                        status=TaskStatus(state=TaskState.completed),
                        final=True,
                    )
                )

        except Exception as e:
            logger.error(f"Error in scientific paper search: {e}", exc_info=True)
            
            # Update task status to failed
            task = context.current_task
            if task:
                await event_queue.enqueue_event(
                    TaskStatusUpdateEvent(
                        task_id=task.id,
                        context_id=task.context_id,
                        status=TaskStatus(
                            state=TaskState.input_required,
                            message=new_agent_text_message(
                                f"Error during paper search: {str(e)}",
                                task.context_id,
                                task.id
                            ),
                        ),
                        final=True,
                    )
                )

    def _run_paper_search_sync(self, query: str) -> dict:
        """Run paper search in sync context (called from asyncio.to_thread)."""
        try:
            # Create a new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Run the paper search
                result = loop.run_until_complete(search_and_parse_papers(
                    query=query,
                    max_results=10
                ))
                return result
            finally:
                # Clean up the event loop
                loop.close()
                
        except Exception as e:
            logger.error(f"Error in sync paper search: {e}", exc_info=True)
            raise e
    
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise Exception('Cancel not supported')