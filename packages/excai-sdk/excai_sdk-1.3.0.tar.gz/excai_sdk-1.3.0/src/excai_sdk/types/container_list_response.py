# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List
from typing_extensions import Literal

from .._models import BaseModel
from .container import Container

__all__ = ["ContainerListResponse"]


class ContainerListResponse(BaseModel):
    data: List[Container]
    """A list of containers."""

    first_id: str
    """The ID of the first container in the list."""

    has_more: bool
    """Whether there are more containers available."""

    last_id: str
    """The ID of the last container in the list."""

    object: Literal["list"]
    """The type of object returned, must be 'list'."""
