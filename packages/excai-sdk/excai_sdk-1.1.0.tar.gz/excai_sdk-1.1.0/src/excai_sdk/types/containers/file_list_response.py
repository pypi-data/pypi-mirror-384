# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List
from typing_extensions import Literal

from ..._models import BaseModel
from .container_file import ContainerFile

__all__ = ["FileListResponse"]


class FileListResponse(BaseModel):
    data: List[ContainerFile]
    """A list of container files."""

    first_id: str
    """The ID of the first file in the list."""

    has_more: bool
    """Whether there are more files available."""

    last_id: str
    """The ID of the last file in the list."""

    object: Literal["list"]
    """The type of object returned, must be 'list'."""
