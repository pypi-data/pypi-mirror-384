# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List
from typing_extensions import Literal

from .eval_run import EvalRun
from ..._models import BaseModel

__all__ = ["RunListResponse"]


class RunListResponse(BaseModel):
    data: List[EvalRun]
    """An array of eval run objects."""

    first_id: str
    """The identifier of the first eval run in the data array."""

    has_more: bool
    """Indicates whether there are more evals available."""

    last_id: str
    """The identifier of the last eval run in the data array."""

    object: Literal["list"]
    """The type of this object. It is always set to "list"."""
