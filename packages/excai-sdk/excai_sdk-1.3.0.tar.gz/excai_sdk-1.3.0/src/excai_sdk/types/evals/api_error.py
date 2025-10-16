# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from ..._models import BaseModel

__all__ = ["APIError"]


class APIError(BaseModel):
    code: str
    """The error code."""

    message: str
    """The error message."""
