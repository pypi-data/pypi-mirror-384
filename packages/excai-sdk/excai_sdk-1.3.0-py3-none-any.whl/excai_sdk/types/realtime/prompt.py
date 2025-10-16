# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, Union, Optional
from typing_extensions import TypeAlias

from ..._models import BaseModel
from ..conversations.input_file_content import InputFileContent
from ..conversations.input_text_content import InputTextContent
from ..conversations.input_image_content import InputImageContent

__all__ = ["Prompt", "Variables"]

Variables: TypeAlias = Union[str, InputTextContent, InputImageContent, InputFileContent]


class Prompt(BaseModel):
    id: str
    """The unique identifier of the prompt template to use."""

    variables: Optional[Dict[str, Variables]] = None
    """Optional map of values to substitute in for variables in your prompt.

    The substitution values can either be strings, or other Response input types
    like images or files.
    """

    version: Optional[str] = None
    """Optional version of the prompt template."""
