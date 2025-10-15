# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Union
from typing_extensions import Literal, TypeAlias

from ...._models import BaseModel
from .grader_python_script import GraderPythonScript
from .grader_text_similarity_ft import GraderTextSimilarityFt
from .grader_score_assignment_model import GraderScoreAssignmentModel
from .grader_string_check_comparison import GraderStringCheckComparison

__all__ = ["GraderMulti", "Graders"]

Graders: TypeAlias = Union[
    GraderStringCheckComparison, GraderTextSimilarityFt, GraderPythonScript, GraderScoreAssignmentModel
]


class GraderMulti(BaseModel):
    calculate_output: str
    """A formula to calculate the output based on grader results."""

    graders: Graders
    """
    A StringCheckGrader object that performs a string comparison between input and
    reference using a specified operation.
    """

    name: str
    """The name of the grader."""

    type: Literal["multi"]
    """The object type, which is always `multi`."""
