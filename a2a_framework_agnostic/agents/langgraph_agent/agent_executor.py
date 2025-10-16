from .agent import TellTimeAgent

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
import logging

logger = logging.getLogger(__name__)

class TellTimeAgentExecutor(AgentExecutor):

    def __init__(self):
        self.agent = TellTimeAgent()

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        try:
            query = context.get_user_input()
            task = context.current_task

            if not query:
                raise ValueError("No user input provided to the agent.")
            
            if not task:
                task = new_task(context.message)
                await event_queue.enqueue_event(task)
            
            logger.info(f"Processing query: {query}")
            
            # Stream responses from the agent
            async for event in self.agent.stream(query, task.context_id):
                logger.info(f"Received event: {event}")
                
                if event.get('is_task_complete', False):
                    # Task is complete
                    await event_queue.enqueue_event(
                        TaskArtifactUpdateEvent(
                            taskId=task.id,
                            contextId=task.context_id,
                            artifact=new_text_artifact(
                                name='current_result',
                                description='Result of request to agent.',
                                text=event['content'],
                            ),
                            append=False,
                            lastChunk=True,
                        )
                    )
                    await event_queue.enqueue_event(
                        TaskStatusUpdateEvent(
                            taskId=task.id,
                            contextId=task.context_id,
                            status=TaskStatus(state=TaskState.completed),
                            final=True,
                        )
                    )
                    break

                elif event.get('require_user_input', False):
                    # Need user input
                    await event_queue.enqueue_event(
                        TaskStatusUpdateEvent(
                            taskId=task.id,
                            contextId=task.context_id,
                            status=TaskStatus(
                                state=TaskState.input_required,
                                message=new_agent_text_message(
                                    event['content'],
                                    task.context_id,
                                    task.id
                                ),
                            ),
                            final=True,
                        )
                    )
                    break

                else:
                    # Working status
                    await event_queue.enqueue_event(
                        TaskStatusUpdateEvent(
                            taskId=task.id,
                            contextId=task.context_id,
                            status=TaskStatus(
                                state=TaskState.working,
                                message=new_agent_text_message(
                                    event['content'],
                                    task.context_id,
                                    task.id
                                ),
                            ),
                            final=False,
                        )
                    )
                    
        except Exception as e:
            logger.error(f"Error in execute: {e}")
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
    