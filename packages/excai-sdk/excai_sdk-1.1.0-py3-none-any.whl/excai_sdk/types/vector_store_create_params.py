# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import TypedDict

from .._types import SequenceNotStr
from .chat.metadata_param import MetadataParam
from .chunking_strategy_request_param import ChunkingStrategyRequestParam
from .vector_store_expiration_after_param import VectorStoreExpirationAfterParam

__all__ = ["VectorStoreCreateParams"]


class VectorStoreCreateParams(TypedDict, total=False):
    chunking_strategy: ChunkingStrategyRequestParam
    """The chunking strategy used to chunk the file(s).

    If not set, will use the `auto` strategy. Only applicable if `file_ids` is
    non-empty.
    """

    expires_after: VectorStoreExpirationAfterParam
    """The expiration policy for a vector store."""

    file_ids: SequenceNotStr[str]
    """
    A list of [File](https://main.excai.ai/docs/api-reference/files) IDs that the
    vector store should use. Useful for tools like `file_search` that can access
    files.
    """

    metadata: Optional[MetadataParam]
    """Set of 16 key-value pairs that can be attached to an object.

    This can be useful for storing additional information about the object in a
    structured format, and querying for objects via API or the dashboard.

    Keys are strings with a maximum length of 64 characters. Values are strings with
    a maximum length of 512 characters.
    """

    name: str
    """The name of the vector store."""
