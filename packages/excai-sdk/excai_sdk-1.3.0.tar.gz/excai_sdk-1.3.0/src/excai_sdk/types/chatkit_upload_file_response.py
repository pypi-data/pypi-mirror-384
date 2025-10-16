# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias

from .._utils import PropertyInfo
from .._models import BaseModel

__all__ = ["ChatkitUploadFileResponse", "File", "Image"]


class File(BaseModel):
    id: str
    """Unique identifier for the uploaded file."""

    mime_type: Optional[str] = None
    """MIME type reported for the uploaded file. Defaults to null when unknown."""

    name: Optional[str] = None
    """Original filename supplied by the uploader. Defaults to null when unnamed."""

    type: Literal["file"]
    """Type discriminator that is always `file`."""

    upload_url: Optional[str] = None
    """Signed URL for downloading the uploaded file.

    Defaults to null when no download link is available.
    """


class Image(BaseModel):
    id: str
    """Unique identifier for the uploaded image."""

    mime_type: str
    """MIME type of the uploaded image."""

    name: Optional[str] = None
    """Original filename for the uploaded image. Defaults to null when unnamed."""

    preview_url: str
    """Preview URL that can be rendered inline for the image."""

    type: Literal["image"]
    """Type discriminator that is always `image`."""

    upload_url: Optional[str] = None
    """Signed URL for downloading the uploaded image.

    Defaults to null when no download link is available.
    """


ChatkitUploadFileResponse: TypeAlias = Annotated[Union[File, Image], PropertyInfo(discriminator="type")]
