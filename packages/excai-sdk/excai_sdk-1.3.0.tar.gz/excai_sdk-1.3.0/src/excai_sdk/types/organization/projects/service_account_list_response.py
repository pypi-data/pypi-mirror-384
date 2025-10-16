# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List
from typing_extensions import Literal

from ...._models import BaseModel
from .project_service_account import ProjectServiceAccount

__all__ = ["ServiceAccountListResponse"]


class ServiceAccountListResponse(BaseModel):
    data: List[ProjectServiceAccount]

    first_id: str

    has_more: bool

    last_id: str

    object: Literal["list"]
