# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union
from typing_extensions import Literal, Required, TypeAlias, TypedDict

from .alpha.grader_multi_param import GraderMultiParam
from .alpha.grader_python_script_param import GraderPythonScriptParam
from .alpha.grader_text_similarity_ft_param import GraderTextSimilarityFtParam
from .alpha.grader_score_assignment_model_param import GraderScoreAssignmentModelParam
from .alpha.grader_string_check_comparison_param import GraderStringCheckComparisonParam

__all__ = [
    "FineTuneMethodParam",
    "Dpo",
    "DpoHyperparameters",
    "Reinforcement",
    "ReinforcementGrader",
    "ReinforcementHyperparameters",
    "Supervised",
    "SupervisedHyperparameters",
]


class DpoHyperparameters(TypedDict, total=False):
    batch_size: Union[Literal["auto"], int]
    """Number of examples in each batch.

    A larger batch size means that model parameters are updated less frequently, but
    with lower variance.
    """

    beta: Union[Literal["auto"], float]
    """The beta value for the DPO method.

    A higher beta value will increase the weight of the penalty between the policy
    and reference model.
    """

    learning_rate_multiplier: Union[Literal["auto"], float]
    """Scaling factor for the learning rate.

    A smaller learning rate may be useful to avoid overfitting.
    """

    n_epochs: Union[Literal["auto"], int]
    """The number of epochs to train the model for.

    An epoch refers to one full cycle through the training dataset.
    """


class Dpo(TypedDict, total=False):
    hyperparameters: DpoHyperparameters
    """The hyperparameters used for the DPO fine-tuning job."""


ReinforcementGrader: TypeAlias = Union[
    GraderStringCheckComparisonParam,
    GraderTextSimilarityFtParam,
    GraderPythonScriptParam,
    GraderScoreAssignmentModelParam,
    GraderMultiParam,
]


class ReinforcementHyperparameters(TypedDict, total=False):
    batch_size: Union[Literal["auto"], int]
    """Number of examples in each batch.

    A larger batch size means that model parameters are updated less frequently, but
    with lower variance.
    """

    compute_multiplier: Union[Literal["auto"], float]
    """
    Multiplier on amount of compute used for exploring search space during training.
    """

    eval_interval: Union[Literal["auto"], int]
    """The number of training steps between evaluation runs."""

    eval_samples: Union[Literal["auto"], int]
    """Number of evaluation samples to generate per training step."""

    learning_rate_multiplier: Union[Literal["auto"], float]
    """Scaling factor for the learning rate.

    A smaller learning rate may be useful to avoid overfitting.
    """

    n_epochs: Union[Literal["auto"], int]
    """The number of epochs to train the model for.

    An epoch refers to one full cycle through the training dataset.
    """

    reasoning_effort: Literal["default", "low", "medium", "high"]
    """Level of reasoning effort."""


class Reinforcement(TypedDict, total=False):
    grader: Required[ReinforcementGrader]
    """The grader used for the fine-tuning job."""

    hyperparameters: ReinforcementHyperparameters
    """The hyperparameters used for the reinforcement fine-tuning job."""


class SupervisedHyperparameters(TypedDict, total=False):
    batch_size: Union[Literal["auto"], int]
    """Number of examples in each batch.

    A larger batch size means that model parameters are updated less frequently, but
    with lower variance.
    """

    learning_rate_multiplier: Union[Literal["auto"], float]
    """Scaling factor for the learning rate.

    A smaller learning rate may be useful to avoid overfitting.
    """

    n_epochs: Union[Literal["auto"], int]
    """The number of epochs to train the model for.

    An epoch refers to one full cycle through the training dataset.
    """


class Supervised(TypedDict, total=False):
    hyperparameters: SupervisedHyperparameters
    """The hyperparameters used for the fine-tuning job."""


class FineTuneMethodParam(TypedDict, total=False):
    type: Required[Literal["supervised", "dpo", "reinforcement"]]
    """The type of method. Is either `supervised`, `dpo`, or `reinforcement`."""

    dpo: Dpo
    """Configuration for the DPO fine-tuning method."""

    reinforcement: Reinforcement
    """Configuration for the reinforcement fine-tuning method."""

    supervised: Supervised
    """Configuration for the supervised fine-tuning method."""
