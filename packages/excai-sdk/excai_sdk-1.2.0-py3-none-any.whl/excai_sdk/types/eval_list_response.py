# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List
from typing_extensions import Literal

from .eval import Eval
from .._models import BaseModel

__all__ = ["EvalListResponse"]


class EvalListResponse(BaseModel):
    data: List[Eval]
    """An array of eval objects."""

    first_id: str
    """The identifier of the first eval in the data array."""

    has_more: bool
    """Indicates whether there are more evals available."""

    last_id: str
    """The identifier of the last eval in the data array."""

    object: Literal["list"]
    """The type of this object. It is always set to "list"."""
