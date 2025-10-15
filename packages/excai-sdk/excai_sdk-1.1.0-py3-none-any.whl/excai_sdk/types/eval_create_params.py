# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Union, Iterable, Optional
from typing_extensions import Literal, Required, TypeAlias, TypedDict

from .._types import SequenceNotStr
from .chat.metadata_param import MetadataParam
from .grader_python_eval_param import GraderPythonEvalParam
from .grader_score_eval_model_param import GraderScoreEvalModelParam
from .grader_string_check_eval_param import GraderStringCheckEvalParam
from .fine_tuning.alpha.eval_item_param import EvalItemParam
from .grader_text_similarity_eval_param import GraderTextSimilarityEvalParam

__all__ = [
    "EvalCreateParams",
    "DataSourceConfig",
    "DataSourceConfigCustom",
    "DataSourceConfigLogs",
    "DataSourceConfigStoredCompletions",
    "TestingCriterion",
    "TestingCriterionLabelModel",
    "TestingCriterionLabelModelInput",
    "TestingCriterionLabelModelInputSimpleInputMessage",
]


class EvalCreateParams(TypedDict, total=False):
    data_source_config: Required[DataSourceConfig]
    """The configuration for the data source used for the evaluation runs.

    Dictates the schema of the data used in the evaluation.
    """

    testing_criteria: Required[Iterable[TestingCriterion]]
    """A list of graders for all eval runs in this group.

    Graders can reference variables in the data source using double curly braces
    notation, like `{{item.variable_name}}`. To reference the model's output, use
    the `sample` namespace (ie, `{{sample.output_text}}`).
    """

    metadata: Optional[MetadataParam]
    """Set of 16 key-value pairs that can be attached to an object.

    This can be useful for storing additional information about the object in a
    structured format, and querying for objects via API or the dashboard.

    Keys are strings with a maximum length of 64 characters. Values are strings with
    a maximum length of 512 characters.
    """

    name: str
    """The name of the evaluation."""


class DataSourceConfigCustom(TypedDict, total=False):
    item_schema: Required[Dict[str, object]]
    """The json schema for each row in the data source."""

    type: Required[Literal["custom"]]
    """The type of data source. Always `custom`."""

    include_sample_schema: bool
    """
    Whether the eval should expect you to populate the sample namespace (ie, by
    generating responses off of your data source)
    """


class DataSourceConfigLogs(TypedDict, total=False):
    type: Required[Literal["logs"]]
    """The type of data source. Always `logs`."""

    metadata: Dict[str, object]
    """Metadata filters for the logs data source."""


class DataSourceConfigStoredCompletions(TypedDict, total=False):
    type: Required[Literal["stored_completions"]]
    """The type of data source. Always `stored_completions`."""

    metadata: Dict[str, object]
    """Metadata filters for the stored completions data source."""


DataSourceConfig: TypeAlias = Union[DataSourceConfigCustom, DataSourceConfigLogs, DataSourceConfigStoredCompletions]


class TestingCriterionLabelModelInputSimpleInputMessage(TypedDict, total=False):
    content: Required[str]
    """The content of the message."""

    role: Required[str]
    """The role of the message (e.g. "system", "assistant", "user")."""


TestingCriterionLabelModelInput: TypeAlias = Union[TestingCriterionLabelModelInputSimpleInputMessage, EvalItemParam]


class TestingCriterionLabelModel(TypedDict, total=False):
    input: Required[Iterable[TestingCriterionLabelModelInput]]
    """A list of chat messages forming the prompt or context.

    May include variable references to the `item` namespace, ie {{item.name}}.
    """

    labels: Required[SequenceNotStr[str]]
    """The labels to classify to each item in the evaluation."""

    model: Required[str]
    """The model to use for the evaluation. Must support structured outputs."""

    name: Required[str]
    """The name of the grader."""

    passing_labels: Required[SequenceNotStr[str]]
    """The labels that indicate a passing result. Must be a subset of labels."""

    type: Required[Literal["label_model"]]
    """The object type, which is always `label_model`."""


TestingCriterion: TypeAlias = Union[
    TestingCriterionLabelModel,
    GraderStringCheckEvalParam,
    GraderTextSimilarityEvalParam,
    GraderPythonEvalParam,
    GraderScoreEvalModelParam,
]
