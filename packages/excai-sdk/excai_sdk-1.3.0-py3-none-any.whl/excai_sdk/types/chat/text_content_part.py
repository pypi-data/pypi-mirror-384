# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing_extensions import Literal

from ..._models import BaseModel

__all__ = ["TextContentPart"]


class TextContentPart(BaseModel):
    text: str
    """The text content."""

    type: Literal["text"]
    """The type of the content part."""
