# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal, Required, TypedDict

from .file_expiration_after_param import FileExpirationAfterParam

__all__ = ["UploadCreateParams"]


class UploadCreateParams(TypedDict, total=False):
    bytes: Required[int]
    """The number of bytes in the file you are uploading."""

    filename: Required[str]
    """The name of the file to upload."""

    mime_type: Required[str]
    """The MIME type of the file.

    This must fall within the supported MIME types for your file purpose. See the
    supported MIME types for assistants and vision.
    """

    purpose: Required[Literal["assistants", "batch", "fine-tune", "vision"]]
    """The intended purpose of the uploaded file.

    See the
    [documentation on File purposes](https://main.excai.ai/docs/api-reference/files/create#files-create-purpose).
    """

    expires_after: FileExpirationAfterParam
    """The expiration policy for a file.

    By default, files with `purpose=batch` expire after 30 days and all other files
    are persisted until they are manually deleted.
    """
