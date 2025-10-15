# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import TypedDict

from .order_enum import OrderEnum

__all__ = ["VideoListParams"]


class VideoListParams(TypedDict, total=False):
    after: str
    """Identifier for the last item from the previous pagination request"""

    limit: int
    """Number of items to retrieve"""

    order: OrderEnum
    """Sort order of results by timestamp.

    Use `asc` for ascending order or `desc` for descending order.
    """
