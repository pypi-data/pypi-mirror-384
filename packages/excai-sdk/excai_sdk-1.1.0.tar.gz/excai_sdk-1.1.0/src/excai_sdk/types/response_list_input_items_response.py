# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Union
from typing_extensions import Literal, Annotated, TypeAlias

from .._utils import PropertyInfo
from .._models import BaseModel
from .conversations.input_message import InputMessage
from .conversations.mcp_tool_call import McpToolCall
from .conversations.mcp_list_tools import McpListTools
from .conversations.output_message import OutputMessage
from .conversations.computer_tool_call import ComputerToolCall
from .conversations.image_gen_tool_call import ImageGenToolCall
from .conversations.mcp_approval_request import McpApprovalRequest
from .conversations.web_search_tool_call import WebSearchToolCall
from .conversations.file_search_tool_call import FileSearchToolCall
from .conversations.local_shell_tool_call import LocalShellToolCall
from .conversations.code_interpreter_tool_call import CodeInterpreterToolCall
from .conversations.function_tool_call_resource import FunctionToolCallResource
from .conversations.local_shell_tool_call_output import LocalShellToolCallOutput
from .conversations.mcp_approval_response_resource import McpApprovalResponseResource
from .conversations.computer_tool_call_output_resource import ComputerToolCallOutputResource
from .conversations.function_tool_call_output_resource import FunctionToolCallOutputResource

__all__ = ["ResponseListInputItemsResponse", "Data", "DataMessage"]


class DataMessage(InputMessage):
    id: str
    """The unique ID of the message input."""


Data: TypeAlias = Annotated[
    Union[
        DataMessage,
        OutputMessage,
        FileSearchToolCall,
        ComputerToolCall,
        ComputerToolCallOutputResource,
        WebSearchToolCall,
        FunctionToolCallResource,
        FunctionToolCallOutputResource,
        ImageGenToolCall,
        CodeInterpreterToolCall,
        LocalShellToolCall,
        LocalShellToolCallOutput,
        McpListTools,
        McpApprovalRequest,
        McpApprovalResponseResource,
        McpToolCall,
    ],
    PropertyInfo(discriminator="type"),
]


class ResponseListInputItemsResponse(BaseModel):
    data: List[Data]
    """A list of items used to generate this response."""

    first_id: str
    """The ID of the first item in the list."""

    has_more: bool
    """Whether there are more items available."""

    last_id: str
    """The ID of the last item in the list."""

    object: Literal["list"]
    """The type of object returned, must be `list`."""
