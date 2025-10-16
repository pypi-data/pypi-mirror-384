# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import Literal, Required, TypedDict

__all__ = ["ImageGenToolCallParam"]


class ImageGenToolCallParam(TypedDict, total=False):
    id: Required[str]
    """The unique ID of the image generation call."""

    result: Required[Optional[str]]
    """The generated image encoded in base64."""

    status: Required[Literal["in_progress", "completed", "generating", "failed"]]
    """The status of the image generation call."""

    type: Required[Literal["image_generation_call"]]
    """The type of the image generation call. Always `image_generation_call`."""
