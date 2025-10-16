# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Union, Optional
from typing_extensions import Literal, TypeAlias

from ..._models import BaseModel
from .alpha.grader_multi import GraderMulti
from .alpha.grader_python_script import GraderPythonScript
from .alpha.grader_text_similarity_ft import GraderTextSimilarityFt
from .alpha.grader_score_assignment_model import GraderScoreAssignmentModel
from .alpha.grader_string_check_comparison import GraderStringCheckComparison

__all__ = [
    "FineTuneMethod",
    "Dpo",
    "DpoHyperparameters",
    "Reinforcement",
    "ReinforcementGrader",
    "ReinforcementHyperparameters",
    "Supervised",
    "SupervisedHyperparameters",
]


class DpoHyperparameters(BaseModel):
    batch_size: Union[Literal["auto"], int, None] = None
    """Number of examples in each batch.

    A larger batch size means that model parameters are updated less frequently, but
    with lower variance.
    """

    beta: Union[Literal["auto"], float, None] = None
    """The beta value for the DPO method.

    A higher beta value will increase the weight of the penalty between the policy
    and reference model.
    """

    learning_rate_multiplier: Union[Literal["auto"], float, None] = None
    """Scaling factor for the learning rate.

    A smaller learning rate may be useful to avoid overfitting.
    """

    n_epochs: Union[Literal["auto"], int, None] = None
    """The number of epochs to train the model for.

    An epoch refers to one full cycle through the training dataset.
    """


class Dpo(BaseModel):
    hyperparameters: Optional[DpoHyperparameters] = None
    """The hyperparameters used for the DPO fine-tuning job."""


ReinforcementGrader: TypeAlias = Union[
    GraderStringCheckComparison, GraderTextSimilarityFt, GraderPythonScript, GraderScoreAssignmentModel, GraderMulti
]


class ReinforcementHyperparameters(BaseModel):
    batch_size: Union[Literal["auto"], int, None] = None
    """Number of examples in each batch.

    A larger batch size means that model parameters are updated less frequently, but
    with lower variance.
    """

    compute_multiplier: Union[Literal["auto"], float, None] = None
    """
    Multiplier on amount of compute used for exploring search space during training.
    """

    eval_interval: Union[Literal["auto"], int, None] = None
    """The number of training steps between evaluation runs."""

    eval_samples: Union[Literal["auto"], int, None] = None
    """Number of evaluation samples to generate per training step."""

    learning_rate_multiplier: Union[Literal["auto"], float, None] = None
    """Scaling factor for the learning rate.

    A smaller learning rate may be useful to avoid overfitting.
    """

    n_epochs: Union[Literal["auto"], int, None] = None
    """The number of epochs to train the model for.

    An epoch refers to one full cycle through the training dataset.
    """

    reasoning_effort: Optional[Literal["default", "low", "medium", "high"]] = None
    """Level of reasoning effort."""


class Reinforcement(BaseModel):
    grader: ReinforcementGrader
    """The grader used for the fine-tuning job."""

    hyperparameters: Optional[ReinforcementHyperparameters] = None
    """The hyperparameters used for the reinforcement fine-tuning job."""


class SupervisedHyperparameters(BaseModel):
    batch_size: Union[Literal["auto"], int, None] = None
    """Number of examples in each batch.

    A larger batch size means that model parameters are updated less frequently, but
    with lower variance.
    """

    learning_rate_multiplier: Union[Literal["auto"], float, None] = None
    """Scaling factor for the learning rate.

    A smaller learning rate may be useful to avoid overfitting.
    """

    n_epochs: Union[Literal["auto"], int, None] = None
    """The number of epochs to train the model for.

    An epoch refers to one full cycle through the training dataset.
    """


class Supervised(BaseModel):
    hyperparameters: Optional[SupervisedHyperparameters] = None
    """The hyperparameters used for the fine-tuning job."""


class FineTuneMethod(BaseModel):
    type: Literal["supervised", "dpo", "reinforcement"]
    """The type of method. Is either `supervised`, `dpo`, or `reinforcement`."""

    dpo: Optional[Dpo] = None
    """Configuration for the DPO fine-tuning method."""

    reinforcement: Optional[Reinforcement] = None
    """Configuration for the reinforcement fine-tuning method."""

    supervised: Optional[Supervised] = None
    """Configuration for the supervised fine-tuning method."""
