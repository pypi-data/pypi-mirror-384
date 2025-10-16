# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Union, Optional
from typing_extensions import Required, TypeAlias, TypedDict

from ..conversations.input_file_content_param import InputFileContentParam
from ..conversations.input_text_content_param import InputTextContentParam
from ..conversations.input_image_content_param import InputImageContentParam

__all__ = ["PromptParam", "Variables"]

Variables: TypeAlias = Union[str, InputTextContentParam, InputImageContentParam, InputFileContentParam]


class PromptParam(TypedDict, total=False):
    id: Required[str]
    """The unique identifier of the prompt template to use."""

    variables: Optional[Dict[str, Variables]]
    """Optional map of values to substitute in for variables in your prompt.

    The substitution values can either be strings, or other Response input types
    like images or files.
    """

    version: Optional[str]
    """Optional version of the prompt template."""
