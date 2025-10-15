# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from ..model_response_properties_standard_param import ModelResponsePropertiesStandardParam

__all__ = ["ModelResponsePropertiesCreateParam"]


class ModelResponsePropertiesCreateParam(ModelResponsePropertiesStandardParam, total=False):
    top_logprobs: int  # type: ignore
    """
    An integer between 0 and 20 specifying the number of most likely tokens to
    return at each token position, each with an associated log probability.
    """
