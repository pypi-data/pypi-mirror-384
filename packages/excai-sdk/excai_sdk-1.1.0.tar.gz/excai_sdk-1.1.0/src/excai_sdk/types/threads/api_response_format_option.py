# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Union
from typing_extensions import Literal, TypeAlias

from ..chat.text_format import TextFormat
from ..chat.json_object_format import JsonObjectFormat
from ..chat.json_schema_format import JsonSchemaFormat

__all__ = ["APIResponseFormatOption"]

APIResponseFormatOption: TypeAlias = Union[Literal["auto"], TextFormat, JsonObjectFormat, JsonSchemaFormat]
