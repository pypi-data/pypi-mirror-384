# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union
from typing_extensions import Literal, Required, TypeAlias, TypedDict

from .grader_python_script_param import GraderPythonScriptParam
from .grader_text_similarity_ft_param import GraderTextSimilarityFtParam
from .grader_score_assignment_model_param import GraderScoreAssignmentModelParam
from .grader_string_check_comparison_param import GraderStringCheckComparisonParam

__all__ = ["GraderMultiParam", "Graders"]

Graders: TypeAlias = Union[
    GraderStringCheckComparisonParam,
    GraderTextSimilarityFtParam,
    GraderPythonScriptParam,
    GraderScoreAssignmentModelParam,
]


class GraderMultiParam(TypedDict, total=False):
    calculate_output: Required[str]
    """A formula to calculate the output based on grader results."""

    graders: Required[Graders]
    """
    A StringCheckGrader object that performs a string comparison between input and
    reference using a specified operation.
    """

    name: Required[str]
    """The name of the grader."""

    type: Required[Literal["multi"]]
    """The object type, which is always `multi`."""
