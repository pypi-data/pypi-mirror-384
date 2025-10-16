# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal, Required, TypedDict

__all__ = ["ReasoningTextContentParam"]


class ReasoningTextContentParam(TypedDict, total=False):
    text: Required[str]
    """The reasoning text from the model."""

    type: Required[Literal["reasoning_text"]]
    """The type of the reasoning text. Always `reasoning_text`."""
