# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Union
from typing_extensions import Literal, TypeAlias

from ..._models import BaseModel

__all__ = ["RealtimeTruncation", "RetentionRatioTruncation"]


class RetentionRatioTruncation(BaseModel):
    retention_ratio: float
    """
    Fraction of post-instruction conversation tokens to retain (0.0 - 1.0) when the
    conversation exceeds the input token limit.
    """

    type: Literal["retention_ratio"]
    """Use retention ratio truncation."""


RealtimeTruncation: TypeAlias = Union[Literal["auto", "disabled"], RetentionRatioTruncation]
