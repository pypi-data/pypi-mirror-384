# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal, Required, TypedDict

__all__ = ["TextContentPartParam"]


class TextContentPartParam(TypedDict, total=False):
    text: Required[str]
    """The text content."""

    type: Required[Literal["text"]]
    """The type of the content part."""
