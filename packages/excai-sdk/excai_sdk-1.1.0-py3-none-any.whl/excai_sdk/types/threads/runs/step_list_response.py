# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List

from .run_step import RunStep
from ...._models import BaseModel

__all__ = ["StepListResponse"]


class StepListResponse(BaseModel):
    data: List[RunStep]

    first_id: str

    has_more: bool

    last_id: str

    object: str
