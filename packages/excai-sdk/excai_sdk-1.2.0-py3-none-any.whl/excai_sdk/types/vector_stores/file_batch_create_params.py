# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import Required, TypedDict

from ..._types import SequenceNotStr
from ..chunking_strategy_request_param import ChunkingStrategyRequestParam
from .vector_store_file_attributes_param import VectorStoreFileAttributesParam

__all__ = ["FileBatchCreateParams"]


class FileBatchCreateParams(TypedDict, total=False):
    file_ids: Required[SequenceNotStr[str]]
    """
    A list of [File](https://main.excai.ai/docs/api-reference/files) IDs that the
    vector store should use. Useful for tools like `file_search` that can access
    files.
    """

    attributes: Optional[VectorStoreFileAttributesParam]
    """Set of 16 key-value pairs that can be attached to an object.

    This can be useful for storing additional information about the object in a
    structured format, and querying for objects via API or the dashboard. Keys are
    strings with a maximum length of 64 characters. Values are strings with a
    maximum length of 512 characters, booleans, or numbers.
    """

    chunking_strategy: ChunkingStrategyRequestParam
    """The chunking strategy used to chunk the file(s).

    If not set, will use the `auto` strategy. Only applicable if `file_ids` is
    non-empty.
    """
