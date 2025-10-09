from dotenv import load_dotenv
import asyncio
import os
import logging
from typing import Any, AsyncIterable

from pydantic_ai import Agent

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

logger = logging.getLogger(__name__)
load_dotenv()

class GreetingAgentExecutor(AgentExecutor):
    """Agent executor for the Pydantic AI greeting agent."""

    def __init__(self):
        # Initialize the Pydantic AI agent
        self.agent = Agent(
            model="google-gla:gemini-2.5-flash-lite",
            output_type=str,
            system_prompt=(
                "You are a friendly greeting agent. Your role is to provide warm, "
                "welcoming greetings and engage in pleasant conversation. Be cheerful, "
                "helpful, and personable in your responses. You can greet people, "
                "ask how they're doing, and have light conversations."
            )
        )

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        try:
            query = context.get_user_input()
            task = context.current_task

            if not query:
                raise ValueError("No user input provided to the agent.")
            
            if not task:
                task = new_task(context.message)
                await event_queue.enqueue_event(task)
            
            logger.info(f"Processing greeting query: {query}")
            
            # Send working status
            await event_queue.enqueue_event(
                TaskStatusUpdateEvent(
                    taskId=task.id,
                    contextId=task.context_id,
                    status=TaskStatus(
                        state=TaskState.working,
                        message=new_agent_text_message(
                            "Preparing a friendly response...",
                            task.context_id,
                            task.id
                        ),
                    ),
                    final=False,
                )
            )
            
            # Get response from Pydantic AI agent  
            # Use asyncio.to_thread to run the sync method in a separate thread
            result = await asyncio.to_thread(self.agent.run_sync, query)
            response_text = result.output  # Extract the actual output text
            
            logger.info(f"Greeting agent response: {response_text}")
            
            # Send artifact with the response
            await event_queue.enqueue_event(
                TaskArtifactUpdateEvent(
                    taskId=task.id,
                    contextId=task.context_id,
                    artifact=new_text_artifact(
                        name='greeting_response',
                        description='Friendly greeting response from agent.',
                        text=response_text,
                    ),
                    append=False,
                    lastChunk=True,
                )
            )
            
            # Mark task as completed
            await event_queue.enqueue_event(
                TaskStatusUpdateEvent(
                    taskId=task.id,
                    contextId=task.context_id,
                    status=TaskStatus(state=TaskState.completed),
                    final=True,
                )
            )
                    
        except Exception as e:
            logger.error(f"Error in greeting agent execute: {e}")
            # Send error status
            if 'task' in locals() and task:
                await event_queue.enqueue_event(
                    TaskStatusUpdateEvent(
                        taskId=task.id,
                        contextId=task.context_id,
                        status=TaskStatus(
                            state=TaskState.input_required,
                            message=new_agent_text_message(
                                f"An error occurred: {str(e)}",
                                task.context_id,
                                task.id
                            ),
                        ),
                        final=True,
                    )
                )

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise Exception('Cancel not supported')