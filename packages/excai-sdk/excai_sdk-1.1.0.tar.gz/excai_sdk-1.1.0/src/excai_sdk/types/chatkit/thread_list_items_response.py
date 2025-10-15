# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias

from ..._utils import PropertyInfo
from ..._models import BaseModel
from .task_type import TaskType

__all__ = [
    "ThreadListItemsResponse",
    "Data",
    "DataChatkitUserMessage",
    "DataChatkitUserMessageAttachment",
    "DataChatkitUserMessageContent",
    "DataChatkitUserMessageContentInputText",
    "DataChatkitUserMessageContentQuotedText",
    "DataChatkitUserMessageInferenceOptions",
    "DataChatkitUserMessageInferenceOptionsToolChoice",
    "DataChatkitAssistantMessage",
    "DataChatkitAssistantMessageContent",
    "DataChatkitAssistantMessageContentAnnotation",
    "DataChatkitAssistantMessageContentAnnotationFile",
    "DataChatkitAssistantMessageContentAnnotationFileSource",
    "DataChatkitAssistantMessageContentAnnotationURL",
    "DataChatkitAssistantMessageContentAnnotationURLSource",
    "DataChatkitWidget",
    "DataChatkitClientToolCall",
    "DataChatkitTask",
    "DataChatkitTaskGroup",
    "DataChatkitTaskGroupTask",
]


class DataChatkitUserMessageAttachment(BaseModel):
    id: str
    """Identifier for the attachment."""

    mime_type: str
    """MIME type of the attachment."""

    name: str
    """Original display name for the attachment."""

    preview_url: Optional[str] = None
    """Preview URL for rendering the attachment inline."""

    type: Literal["image", "file"]
    """Attachment discriminator."""


class DataChatkitUserMessageContentInputText(BaseModel):
    text: str
    """Plain-text content supplied by the user."""

    type: Literal["input_text"]
    """Type discriminator that is always `input_text`."""


class DataChatkitUserMessageContentQuotedText(BaseModel):
    text: str
    """Quoted text content."""

    type: Literal["quoted_text"]
    """Type discriminator that is always `quoted_text`."""


DataChatkitUserMessageContent: TypeAlias = Annotated[
    Union[DataChatkitUserMessageContentInputText, DataChatkitUserMessageContentQuotedText],
    PropertyInfo(discriminator="type"),
]


class DataChatkitUserMessageInferenceOptionsToolChoice(BaseModel):
    id: str
    """Identifier of the requested tool."""


class DataChatkitUserMessageInferenceOptions(BaseModel):
    model: Optional[str] = None
    """Model name that generated the response.

    Defaults to null when using the session default.
    """

    tool_choice: Optional[DataChatkitUserMessageInferenceOptionsToolChoice] = None
    """Preferred tool to invoke. Defaults to null when ChatKit should auto-select."""


class DataChatkitUserMessage(BaseModel):
    id: str
    """Identifier of the thread item."""

    attachments: List[DataChatkitUserMessageAttachment]
    """Attachments associated with the user message. Defaults to an empty list."""

    content: List[DataChatkitUserMessageContent]
    """Ordered content elements supplied by the user."""

    created_at: int
    """Unix timestamp (in seconds) for when the item was created."""

    inference_options: Optional[DataChatkitUserMessageInferenceOptions] = None
    """Inference overrides applied to the message. Defaults to null when unset."""

    object: Literal["chatkit.thread_item"]
    """Type discriminator that is always `chatkit.thread_item`."""

    thread_id: str
    """Identifier of the parent thread."""

    type: Literal["chatkit.user_message"]


class DataChatkitAssistantMessageContentAnnotationFileSource(BaseModel):
    filename: str
    """Filename referenced by the annotation."""

    type: Literal["file"]
    """Type discriminator that is always `file`."""


class DataChatkitAssistantMessageContentAnnotationFile(BaseModel):
    source: DataChatkitAssistantMessageContentAnnotationFileSource
    """File attachment referenced by the annotation."""

    type: Literal["file"]
    """Type discriminator that is always `file` for this annotation."""


class DataChatkitAssistantMessageContentAnnotationURLSource(BaseModel):
    type: Literal["url"]
    """Type discriminator that is always `url`."""

    url: str
    """URL referenced by the annotation."""


class DataChatkitAssistantMessageContentAnnotationURL(BaseModel):
    source: DataChatkitAssistantMessageContentAnnotationURLSource
    """URL referenced by the annotation."""

    type: Literal["url"]
    """Type discriminator that is always `url` for this annotation."""


DataChatkitAssistantMessageContentAnnotation: TypeAlias = Annotated[
    Union[DataChatkitAssistantMessageContentAnnotationFile, DataChatkitAssistantMessageContentAnnotationURL],
    PropertyInfo(discriminator="type"),
]


class DataChatkitAssistantMessageContent(BaseModel):
    annotations: List[DataChatkitAssistantMessageContentAnnotation]
    """Ordered list of annotations attached to the response text."""

    text: str
    """Assistant generated text."""

    type: Literal["output_text"]
    """Type discriminator that is always `output_text`."""


class DataChatkitAssistantMessage(BaseModel):
    id: str
    """Identifier of the thread item."""

    content: List[DataChatkitAssistantMessageContent]
    """Ordered assistant response segments."""

    created_at: int
    """Unix timestamp (in seconds) for when the item was created."""

    object: Literal["chatkit.thread_item"]
    """Type discriminator that is always `chatkit.thread_item`."""

    thread_id: str
    """Identifier of the parent thread."""

    type: Literal["chatkit.assistant_message"]
    """Type discriminator that is always `chatkit.assistant_message`."""


class DataChatkitWidget(BaseModel):
    id: str
    """Identifier of the thread item."""

    created_at: int
    """Unix timestamp (in seconds) for when the item was created."""

    object: Literal["chatkit.thread_item"]
    """Type discriminator that is always `chatkit.thread_item`."""

    thread_id: str
    """Identifier of the parent thread."""

    type: Literal["chatkit.widget"]
    """Type discriminator that is always `chatkit.widget`."""

    widget: str
    """Serialized widget payload rendered in the UI."""


class DataChatkitClientToolCall(BaseModel):
    id: str
    """Identifier of the thread item."""

    arguments: str
    """JSON-encoded arguments that were sent to the tool."""

    call_id: str
    """Identifier for the client tool call."""

    created_at: int
    """Unix timestamp (in seconds) for when the item was created."""

    name: str
    """Tool name that was invoked."""

    object: Literal["chatkit.thread_item"]
    """Type discriminator that is always `chatkit.thread_item`."""

    output: Optional[str] = None
    """JSON-encoded output captured from the tool.

    Defaults to null while execution is in progress.
    """

    status: Literal["in_progress", "completed"]
    """Execution status for the tool call."""

    thread_id: str
    """Identifier of the parent thread."""

    type: Literal["chatkit.client_tool_call"]
    """Type discriminator that is always `chatkit.client_tool_call`."""


class DataChatkitTask(BaseModel):
    id: str
    """Identifier of the thread item."""

    created_at: int
    """Unix timestamp (in seconds) for when the item was created."""

    heading: Optional[str] = None
    """Optional heading for the task. Defaults to null when not provided."""

    object: Literal["chatkit.thread_item"]
    """Type discriminator that is always `chatkit.thread_item`."""

    summary: Optional[str] = None
    """Optional summary that describes the task. Defaults to null when omitted."""

    task_type: TaskType
    """Subtype for the task."""

    thread_id: str
    """Identifier of the parent thread."""

    type: Literal["chatkit.task"]
    """Type discriminator that is always `chatkit.task`."""


class DataChatkitTaskGroupTask(BaseModel):
    heading: Optional[str] = None
    """Optional heading for the grouped task. Defaults to null when not provided."""

    summary: Optional[str] = None
    """Optional summary that describes the grouped task.

    Defaults to null when omitted.
    """

    type: TaskType
    """Subtype for the grouped task."""


class DataChatkitTaskGroup(BaseModel):
    id: str
    """Identifier of the thread item."""

    created_at: int
    """Unix timestamp (in seconds) for when the item was created."""

    object: Literal["chatkit.thread_item"]
    """Type discriminator that is always `chatkit.thread_item`."""

    tasks: List[DataChatkitTaskGroupTask]
    """Tasks included in the group."""

    thread_id: str
    """Identifier of the parent thread."""

    type: Literal["chatkit.task_group"]
    """Type discriminator that is always `chatkit.task_group`."""


Data: TypeAlias = Annotated[
    Union[
        DataChatkitUserMessage,
        DataChatkitAssistantMessage,
        DataChatkitWidget,
        DataChatkitClientToolCall,
        DataChatkitTask,
        DataChatkitTaskGroup,
    ],
    PropertyInfo(discriminator="type"),
]


class ThreadListItemsResponse(BaseModel):
    data: List[Data]
    """A list of items"""

    first_id: Optional[str] = None
    """The ID of the first item in the list."""

    has_more: bool
    """Whether there are more items available."""

    last_id: Optional[str] = None
    """The ID of the last item in the list."""

    object: Literal["list"]
    """The type of object returned, must be `list`."""
