from dotenv import load_dotenv
import os 
import logging
from datetime import datetime

from typing import Literal, Any, AsyncIterable
from pydantic import BaseModel

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool
from langchain_core.messages import AIMessage, ToolMessage, HumanMessage
from langchain_core.runnables.config import RunnableConfig

from .config import MODEL

logger = logging.getLogger(__name__)
load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY environment variable not set")
logger.info("GOOGLE_API_KEY found in environment variables.")

memory = MemorySaver()

@tool
def get_time_now() -> dict[str, str]:
    """Returns the current system time in HH:MM:SS format."""
    current_time = datetime.now().strftime("%H:%M:%S")
    return {"current_time": current_time}

class ResponseFormat(BaseModel):
    status: Literal["completed", "input_required", "error"]
    message: str

class TellTimeAgent:
    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]
    
    SYSTEM_INSTRUCTION = (
        "You are a specialized assistant for time-related queries. "
        "Use the 'get_time_now' tool when users ask for the current time to get the time in HH:MM:SS format. "
        "Convert this time to the requested format by the user on your own. You are allowed to do that. "
        "Always respond with a helpful message about the time."
    )

    def __init__(self):
        self.model = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp")
        self.tools = [get_time_now]
        
        # Create the agent with the correct parameter name
        self.graph = create_react_agent(
            self.model,
            self.tools,
            checkpointer=memory,
            prompt=self.SYSTEM_INSTRUCTION,
        )

    async def stream(self, query: str, session_id: str) -> AsyncIterable[dict[str, Any]]:
        """Stream responses from the agent."""
        
        config: RunnableConfig = {
            "configurable": {
                "thread_id": session_id
            }
        }

        inputs = {"messages": [HumanMessage(content=query)]}
        
        try:
            # Track if we've seen any tool calls
            has_tool_calls = False
            final_response = ""
            
            async for chunk in self.graph.astream(inputs, config, stream_mode="values"):
                if "messages" in chunk and chunk["messages"]:
                    latest_message = chunk["messages"][-1]
                    
                    if isinstance(latest_message, AIMessage):
                        if latest_message.tool_calls:
                            has_tool_calls = True
                            yield {
                                "is_task_complete": False,
                                "require_user_input": False,
                                "content": "Looking up the current time...",
                            }
                        elif latest_message.content and not has_tool_calls:
                            # Direct response without tools
                            final_response = latest_message.content
                        elif latest_message.content and has_tool_calls:
                            # Final response after using tools
                            final_response = latest_message.content
                    
                    elif isinstance(latest_message, ToolMessage):
                        yield {
                            "is_task_complete": False,
                            "require_user_input": False,
                            "content": "Processing the time result...",
                        }
            
            # Yield final response
            if final_response:
                yield {
                    "is_task_complete": True,
                    "require_user_input": False,
                    "content": final_response,
                }
            else:
                yield {
                    "is_task_complete": False,
                    "require_user_input": True,
                    "content": "I need more information to help you with your request.",
                }
                
        except Exception as e:
            logger.error(f"Error in agent stream: {e}")
            yield {
                "is_task_complete": False,
                "require_user_input": True,
                "content": f"An error occurred: {str(e)}. Please try again.",
            }

