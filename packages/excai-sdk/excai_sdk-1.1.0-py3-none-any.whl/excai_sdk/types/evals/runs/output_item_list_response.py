# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List
from typing_extensions import Literal

from ...._models import BaseModel
from .eval_run_output_item import EvalRunOutputItem

__all__ = ["OutputItemListResponse"]


class OutputItemListResponse(BaseModel):
    data: List[EvalRunOutputItem]
    """An array of eval run output item objects."""

    first_id: str
    """The identifier of the first eval run output item in the data array."""

    has_more: bool
    """Indicates whether there are more eval run output items available."""

    last_id: str
    """The identifier of the last eval run output item in the data array."""

    object: Literal["list"]
    """The type of this object. It is always set to "list"."""
