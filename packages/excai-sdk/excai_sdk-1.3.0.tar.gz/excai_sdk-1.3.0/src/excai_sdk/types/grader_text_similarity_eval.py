# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from .fine_tuning.alpha.grader_text_similarity_ft import GraderTextSimilarityFt

__all__ = ["GraderTextSimilarityEval"]


class GraderTextSimilarityEval(GraderTextSimilarityFt):
    pass_threshold: float
    """The threshold for the score."""
