# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union
from typing_extensions import Required, TypeAlias, TypedDict

from .grader_multi_param import GraderMultiParam
from .grader_python_script_param import GraderPythonScriptParam
from .grader_text_similarity_ft_param import GraderTextSimilarityFtParam
from .grader_score_assignment_model_param import GraderScoreAssignmentModelParam
from .grader_string_check_comparison_param import GraderStringCheckComparisonParam

__all__ = ["GraderValidateParams", "Grader"]


class GraderValidateParams(TypedDict, total=False):
    grader: Required[Grader]
    """The grader used for the fine-tuning job."""


Grader: TypeAlias = Union[
    GraderStringCheckComparisonParam,
    GraderTextSimilarityFtParam,
    GraderPythonScriptParam,
    GraderScoreAssignmentModelParam,
    GraderMultiParam,
]
