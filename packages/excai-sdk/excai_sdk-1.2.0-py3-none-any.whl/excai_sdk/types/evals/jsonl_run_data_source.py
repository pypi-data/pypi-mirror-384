# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Union
from typing_extensions import Literal, Annotated, TypeAlias

from ..._utils import PropertyInfo
from ..._models import BaseModel
from .jsonl_file_id_source import JSONLFileIDSource
from .jsonl_file_content_source import JSONLFileContentSource

__all__ = ["JSONLRunDataSource", "Source"]

Source: TypeAlias = Annotated[Union[JSONLFileContentSource, JSONLFileIDSource], PropertyInfo(discriminator="type")]


class JSONLRunDataSource(BaseModel):
    source: Source
    """Determines what populates the `item` namespace in the data source."""

    type: Literal["jsonl"]
    """The type of data source. Always `jsonl`."""
