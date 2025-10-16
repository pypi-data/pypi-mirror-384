# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Union, Optional
from typing_extensions import TypeAlias

from ...._models import BaseModel
from .grader_multi import GraderMulti
from .grader_python_script import GraderPythonScript
from .grader_text_similarity_ft import GraderTextSimilarityFt
from .grader_score_assignment_model import GraderScoreAssignmentModel
from .grader_string_check_comparison import GraderStringCheckComparison

__all__ = ["GraderValidateResponse", "Grader"]

Grader: TypeAlias = Union[
    GraderStringCheckComparison, GraderTextSimilarityFt, GraderPythonScript, GraderScoreAssignmentModel, GraderMulti
]


class GraderValidateResponse(BaseModel):
    grader: Optional[Grader] = None
    """The grader used for the fine-tuning job."""
