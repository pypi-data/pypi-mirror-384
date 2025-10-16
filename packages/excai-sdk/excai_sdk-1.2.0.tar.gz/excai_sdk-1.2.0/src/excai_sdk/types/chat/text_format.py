# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing_extensions import Literal

from ..._models import BaseModel

__all__ = ["TextFormat"]


class TextFormat(BaseModel):
    type: Literal["text"]
    """The type of response format being defined. Always `text`."""
