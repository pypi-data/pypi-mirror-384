# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union
from typing_extensions import Required, TypeAlias, TypedDict

from .grader_multi_param import GraderMultiParam
from .grader_python_script_param import GraderPythonScriptParam
from .grader_text_similarity_ft_param import GraderTextSimilarityFtParam
from .grader_score_assignment_model_param import GraderScoreAssignmentModelParam
from .grader_string_check_comparison_param import GraderStringCheckComparisonParam

__all__ = ["GraderRunParams", "Grader"]


class GraderRunParams(TypedDict, total=False):
    grader: Required[Grader]
    """The grader used for the fine-tuning job."""

    model_sample: Required[str]
    """The model sample to be evaluated.

    This value will be used to populate the `sample` namespace. See
    [the guide](https://main.excai.ai/docs/guides/graders) for more details. The
    `output_json` variable will be populated if the model sample is a valid JSON
    string.
    """

    item: object
    """The dataset item provided to the grader.

    This will be used to populate the `item` namespace. See
    [the guide](https://main.excai.ai/docs/guides/graders) for more details.
    """


Grader: TypeAlias = Union[
    GraderStringCheckComparisonParam,
    GraderTextSimilarityFtParam,
    GraderPythonScriptParam,
    GraderScoreAssignmentModelParam,
    GraderMultiParam,
]
