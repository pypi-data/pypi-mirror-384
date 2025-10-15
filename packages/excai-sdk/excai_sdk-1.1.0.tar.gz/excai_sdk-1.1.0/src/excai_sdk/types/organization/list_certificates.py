# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from typing_extensions import Literal

from ..._models import BaseModel
from .certificate import Certificate

__all__ = ["ListCertificates"]


class ListCertificates(BaseModel):
    data: List[Certificate]

    has_more: bool

    object: Literal["list"]

    first_id: Optional[str] = None

    last_id: Optional[str] = None
