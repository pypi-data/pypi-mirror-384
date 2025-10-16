# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union
from typing_extensions import Literal, TypeAlias

from ..chat.text_format_param import TextFormatParam
from ..chat.json_object_format_param import JsonObjectFormatParam
from ..chat.json_schema_format_param import JsonSchemaFormatParam

__all__ = ["APIResponseFormatOptionParam"]

APIResponseFormatOptionParam: TypeAlias = Union[
    Literal["auto"], TextFormatParam, JsonObjectFormatParam, JsonSchemaFormatParam
]
