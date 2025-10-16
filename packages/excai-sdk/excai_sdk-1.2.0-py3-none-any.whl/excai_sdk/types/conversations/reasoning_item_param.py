# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Iterable, Optional
from typing_extensions import Literal, Required, TypedDict

from .reasoning_text_content_param import ReasoningTextContentParam

__all__ = ["ReasoningItemParam", "Summary"]


class Summary(TypedDict, total=False):
    text: Required[str]
    """A summary of the reasoning output from the model so far."""

    type: Required[Literal["summary_text"]]
    """The type of the object. Always `summary_text`."""


class ReasoningItemParam(TypedDict, total=False):
    id: Required[str]
    """The unique identifier of the reasoning content."""

    summary: Required[Iterable[Summary]]
    """Reasoning summary content."""

    type: Required[Literal["reasoning"]]
    """The type of the object. Always `reasoning`."""

    content: Iterable[ReasoningTextContentParam]
    """Reasoning text content."""

    encrypted_content: Optional[str]
    """
    The encrypted content of the reasoning item - populated when a response is
    generated with `reasoning.encrypted_content` in the `include` parameter.
    """

    status: Literal["in_progress", "completed", "incomplete"]
    """The status of the item.

    One of `in_progress`, `completed`, or `incomplete`. Populated when items are
    returned via API.
    """
