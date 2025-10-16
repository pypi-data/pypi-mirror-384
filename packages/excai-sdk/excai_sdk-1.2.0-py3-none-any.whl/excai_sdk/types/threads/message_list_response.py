# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List

from .message import Message
from ..._models import BaseModel

__all__ = ["MessageListResponse"]


class MessageListResponse(BaseModel):
    data: List[Message]

    first_id: str

    has_more: bool

    last_id: str

    object: str
