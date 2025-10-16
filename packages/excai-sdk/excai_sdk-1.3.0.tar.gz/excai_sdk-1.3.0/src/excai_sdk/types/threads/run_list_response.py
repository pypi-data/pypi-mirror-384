# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List

from .run import Run
from ..._models import BaseModel

__all__ = ["RunListResponse"]


class RunListResponse(BaseModel):
    data: List[Run]

    first_id: str

    has_more: bool

    last_id: str

    object: str
