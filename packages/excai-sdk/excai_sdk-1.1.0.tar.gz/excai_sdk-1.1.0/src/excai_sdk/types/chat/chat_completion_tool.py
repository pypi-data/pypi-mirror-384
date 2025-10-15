# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing_extensions import Literal

from ..._models import BaseModel
from .function_object import FunctionObject

__all__ = ["ChatCompletionTool"]


class ChatCompletionTool(BaseModel):
    function: FunctionObject

    type: Literal["function"]
    """The type of the tool. Currently, only `function` is supported."""
