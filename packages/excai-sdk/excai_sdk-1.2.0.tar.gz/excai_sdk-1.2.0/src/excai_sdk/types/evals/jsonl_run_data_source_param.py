# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union
from typing_extensions import Literal, Required, TypeAlias, TypedDict

from .jsonl_file_id_source_param import JSONLFileIDSourceParam
from .jsonl_file_content_source_param import JSONLFileContentSourceParam

__all__ = ["JSONLRunDataSourceParam", "Source"]

Source: TypeAlias = Union[JSONLFileContentSourceParam, JSONLFileIDSourceParam]


class JSONLRunDataSourceParam(TypedDict, total=False):
    source: Required[Source]
    """Determines what populates the `item` namespace in the data source."""

    type: Required[Literal["jsonl"]]
    """The type of data source. Always `jsonl`."""
