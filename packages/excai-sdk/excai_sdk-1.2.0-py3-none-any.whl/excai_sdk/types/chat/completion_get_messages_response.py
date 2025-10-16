# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Union, Optional
from typing_extensions import Literal, TypeAlias

from ..._models import BaseModel
from .response_message import ResponseMessage
from .text_content_part import TextContentPart
from .image_content_part import ImageContentPart

__all__ = ["CompletionGetMessagesResponse", "Data", "DataContentPart"]

DataContentPart: TypeAlias = Union[TextContentPart, ImageContentPart]


class Data(ResponseMessage):
    id: str
    """The identifier of the chat message."""

    content_parts: Optional[List[DataContentPart]] = None
    """
    If a content parts array was provided, this is an array of `text` and
    `image_url` parts. Otherwise, null.
    """


class CompletionGetMessagesResponse(BaseModel):
    data: List[Data]
    """An array of chat completion message objects."""

    first_id: str
    """The identifier of the first chat message in the data array."""

    has_more: bool
    """Indicates whether there are more chat messages available."""

    last_id: str
    """The identifier of the last chat message in the data array."""

    object: Literal["list"]
    """The type of this object. It is always set to "list"."""
