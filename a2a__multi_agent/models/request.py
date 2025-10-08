from typing import Annotated, Union, Literal       # For type annotations and discriminator logic
from pydantic import Field                         # Field configurations for Pydantic models
from pydantic.type_adapter import TypeAdapter      # For runtime discriminated union parsing

# Base models for JSON-RPC requests and responses
from models.json_rpc import JSONRPCRequest, JSONRPCResponse

# Task-related parameter and return models
from models.task import Task, TaskSendParams
from models.task import TaskQueryParams


# -----------------------------------------------------------------------------
# SendTaskRequest: Used to send a new task to an agent
# -----------------------------------------------------------------------------

class SendTaskRequest(JSONRPCRequest):
    method: Literal["tasks/send"] = "tasks/send"    # Exact method string required
    params: TaskSendParams                          # Task creation parameters


# -----------------------------------------------------------------------------
# GetTaskRequest: Used to retrieve a task's status or history
# -----------------------------------------------------------------------------

class GetTaskRequest(JSONRPCRequest):
    method: Literal["tasks/get"] = "tasks/get"      # Exact method string required
    params: TaskQueryParams                         # Task ID and optional history limit


# -----------------------------------------------------------------------------
# A2ARequest: Discriminated union of supported request types
# -----------------------------------------------------------------------------
# This allows automatic parsing of request types based on the `method` field.

A2ARequest = TypeAdapter(
    Annotated[
        Union[
            SendTaskRequest,
            GetTaskRequest,
            # CancelTaskRequest can be added here in future if implemented
        ],
        Field(discriminator="method")
    ]
)


# -----------------------------------------------------------------------------
# SendTaskResponse: Response model for a successful "tasks/send" request
# -----------------------------------------------------------------------------

class SendTaskResponse(JSONRPCResponse):
    result: Task | None = None                      # The task returned by the agent


# -----------------------------------------------------------------------------
# GetTaskResponse: Response model for a "tasks/get" request
# -----------------------------------------------------------------------------

class GetTaskResponse(JSONRPCResponse):
    result: Task | None = None                      # The requested task, or None if not found