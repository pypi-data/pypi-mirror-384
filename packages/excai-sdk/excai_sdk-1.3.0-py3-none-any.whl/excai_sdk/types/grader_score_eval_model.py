# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from .fine_tuning.alpha.grader_score_assignment_model import GraderScoreAssignmentModel

__all__ = ["GraderScoreEvalModel"]


class GraderScoreEvalModel(GraderScoreAssignmentModel):
    pass_threshold: Optional[float] = None
    """The threshold for the score."""
