# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Union, Optional
from typing_extensions import Literal, Required, TypeAlias, TypedDict

from .chat.text_format_param import TextFormatParam
from .chat.json_object_format_param import JsonObjectFormatParam

__all__ = ["TextResponseFormatConfigurationParam", "JsonSchema"]


class JsonSchema(TypedDict, total=False):
    name: Required[str]
    """The name of the response format.

    Must be a-z, A-Z, 0-9, or contain underscores and dashes, with a maximum length
    of 64.
    """

    schema: Required[Dict[str, object]]
    """
    The schema for the response format, described as a JSON Schema object. Learn how
    to build JSON schemas [here](https://json-schema.org/).
    """

    type: Required[Literal["json_schema"]]
    """The type of response format being defined. Always `json_schema`."""

    description: str
    """
    A description of what the response format is for, used by the model to determine
    how to respond in the format.
    """

    strict: Optional[bool]
    """
    Whether to enable strict schema adherence when generating the output. If set to
    true, the model will always follow the exact schema defined in the `schema`
    field. Only a subset of JSON Schema is supported when `strict` is `true`. To
    learn more, read the
    [Structured Outputs guide](https://main.excai.ai/docs/guides/structured-outputs).
    """


TextResponseFormatConfigurationParam: TypeAlias = Union[TextFormatParam, JsonSchema, JsonObjectFormatParam]
