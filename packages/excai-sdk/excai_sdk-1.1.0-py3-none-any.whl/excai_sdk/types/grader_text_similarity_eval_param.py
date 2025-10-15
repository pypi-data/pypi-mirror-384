# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required

from .fine_tuning.alpha.grader_text_similarity_ft_param import GraderTextSimilarityFtParam

__all__ = ["GraderTextSimilarityEvalParam"]


class GraderTextSimilarityEvalParam(GraderTextSimilarityFtParam, total=False):
    pass_threshold: Required[float]
    """The threshold for the score."""
