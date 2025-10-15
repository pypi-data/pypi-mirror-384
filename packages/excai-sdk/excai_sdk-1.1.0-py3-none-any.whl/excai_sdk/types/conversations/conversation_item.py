# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias

from ..._utils import PropertyInfo
from ..._models import BaseModel
from .mcp_tool_call import McpToolCall
from .mcp_list_tools import McpListTools
from .reasoning_item import ReasoningItem
from .refusal_content import RefusalContent
from .custom_tool_call import CustomToolCall
from .computer_tool_call import ComputerToolCall
from .input_file_content import InputFileContent
from .input_text_content import InputTextContent
from .image_gen_tool_call import ImageGenToolCall
from .input_image_content import InputImageContent
from .output_text_content import OutputTextContent
from .mcp_approval_request import McpApprovalRequest
from .web_search_tool_call import WebSearchToolCall
from .file_search_tool_call import FileSearchToolCall
from .local_shell_tool_call import LocalShellToolCall
from .reasoning_text_content import ReasoningTextContent
from .custom_tool_call_output import CustomToolCallOutput
from .code_interpreter_tool_call import CodeInterpreterToolCall
from .function_tool_call_resource import FunctionToolCallResource
from .local_shell_tool_call_output import LocalShellToolCallOutput
from .mcp_approval_response_resource import McpApprovalResponseResource
from .computer_tool_call_output_resource import ComputerToolCallOutputResource
from .function_tool_call_output_resource import FunctionToolCallOutputResource

__all__ = [
    "ConversationItem",
    "Message",
    "MessageContent",
    "MessageContentText",
    "MessageContentSummaryText",
    "MessageContentComputerScreenshot",
]


class MessageContentText(BaseModel):
    text: str

    type: Literal["text"]


class MessageContentSummaryText(BaseModel):
    text: str
    """A summary of the reasoning output from the model so far."""

    type: Literal["summary_text"]
    """The type of the object. Always `summary_text`."""


class MessageContentComputerScreenshot(BaseModel):
    file_id: Optional[str] = None
    """The identifier of an uploaded file that contains the screenshot."""

    image_url: Optional[str] = None
    """The URL of the screenshot image."""

    type: Literal["computer_screenshot"]
    """Specifies the event type.

    For a computer screenshot, this property is always set to `computer_screenshot`.
    """


MessageContent: TypeAlias = Annotated[
    Union[
        InputTextContent,
        OutputTextContent,
        MessageContentText,
        MessageContentSummaryText,
        ReasoningTextContent,
        RefusalContent,
        InputImageContent,
        MessageContentComputerScreenshot,
        InputFileContent,
    ],
    PropertyInfo(discriminator="type"),
]


class Message(BaseModel):
    id: str
    """The unique ID of the message."""

    content: List[MessageContent]
    """The content of the message"""

    role: Literal["unknown", "user", "assistant", "system", "critic", "discriminator", "developer", "tool"]
    """The role of the message.

    One of `unknown`, `user`, `assistant`, `system`, `critic`, `discriminator`,
    `developer`, or `tool`.
    """

    status: Literal["in_progress", "completed", "incomplete"]
    """The status of item.

    One of `in_progress`, `completed`, or `incomplete`. Populated when items are
    returned via API.
    """

    type: Literal["message"]
    """The type of the message. Always set to `message`."""


ConversationItem: TypeAlias = Annotated[
    Union[
        Message,
        FunctionToolCallResource,
        FunctionToolCallOutputResource,
        FileSearchToolCall,
        WebSearchToolCall,
        ImageGenToolCall,
        ComputerToolCall,
        ComputerToolCallOutputResource,
        ReasoningItem,
        CodeInterpreterToolCall,
        LocalShellToolCall,
        LocalShellToolCallOutput,
        McpListTools,
        McpApprovalRequest,
        McpApprovalResponseResource,
        McpToolCall,
        CustomToolCall,
        CustomToolCallOutput,
    ],
    PropertyInfo(discriminator="type"),
]
