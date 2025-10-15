# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Union
from typing_extensions import Literal, TypeAlias

from .assistants_named_tool_choice import AssistantsNamedToolChoice

__all__ = ["APIToolChoiceOption"]

APIToolChoiceOption: TypeAlias = Union[Literal["none", "auto", "required"], AssistantsNamedToolChoice]
