# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from .fine_tuning.alpha.grader_score_assignment_model_param import GraderScoreAssignmentModelParam

__all__ = ["GraderScoreEvalModelParam"]


class GraderScoreEvalModelParam(GraderScoreAssignmentModelParam, total=False):
    pass_threshold: float
    """The threshold for the score."""
