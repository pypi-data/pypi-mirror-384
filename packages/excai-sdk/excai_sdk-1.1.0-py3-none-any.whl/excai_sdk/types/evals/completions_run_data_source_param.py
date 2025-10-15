# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union, Iterable, Optional
from typing_extensions import Literal, Required, TypeAlias, TypedDict

from ..reasoning_effort import ReasoningEffort
from ..chat.metadata_param import MetadataParam
from ..chat.text_format_param import TextFormatParam
from .jsonl_file_id_source_param import JSONLFileIDSourceParam
from ..chat.json_object_format_param import JsonObjectFormatParam
from ..chat.json_schema_format_param import JsonSchemaFormatParam
from .jsonl_file_content_source_param import JSONLFileContentSourceParam
from ..chat.chat_completion_tool_param import ChatCompletionToolParam
from ..fine_tuning.alpha.eval_item_param import EvalItemParam
from ..conversations.easy_input_message_param import EasyInputMessageParam

__all__ = [
    "CompletionsRunDataSourceParam",
    "Source",
    "SourceStoredCompletions",
    "InputMessages",
    "InputMessagesTemplate",
    "InputMessagesTemplateTemplate",
    "InputMessagesItemReference",
    "SamplingParams",
    "SamplingParamsResponseFormat",
]


class SourceStoredCompletions(TypedDict, total=False):
    type: Required[Literal["stored_completions"]]
    """The type of source. Always `stored_completions`."""

    created_after: Optional[int]
    """An optional Unix timestamp to filter items created after this time."""

    created_before: Optional[int]
    """An optional Unix timestamp to filter items created before this time."""

    limit: Optional[int]
    """An optional maximum number of items to return."""

    metadata: Optional[MetadataParam]
    """Set of 16 key-value pairs that can be attached to an object.

    This can be useful for storing additional information about the object in a
    structured format, and querying for objects via API or the dashboard.

    Keys are strings with a maximum length of 64 characters. Values are strings with
    a maximum length of 512 characters.
    """

    model: Optional[str]
    """An optional model to filter by (e.g., 'gpt-4o')."""


Source: TypeAlias = Union[JSONLFileContentSourceParam, JSONLFileIDSourceParam, SourceStoredCompletions]

InputMessagesTemplateTemplate: TypeAlias = Union[EasyInputMessageParam, EvalItemParam]


class InputMessagesTemplate(TypedDict, total=False):
    template: Required[Iterable[InputMessagesTemplateTemplate]]
    """A list of chat messages forming the prompt or context.

    May include variable references to the `item` namespace, ie {{item.name}}.
    """

    type: Required[Literal["template"]]
    """The type of input messages. Always `template`."""


class InputMessagesItemReference(TypedDict, total=False):
    item_reference: Required[str]
    """A reference to a variable in the `item` namespace. Ie, "item.input_trajectory" """

    type: Required[Literal["item_reference"]]
    """The type of input messages. Always `item_reference`."""


InputMessages: TypeAlias = Union[InputMessagesTemplate, InputMessagesItemReference]

SamplingParamsResponseFormat: TypeAlias = Union[TextFormatParam, JsonSchemaFormatParam, JsonObjectFormatParam]


class SamplingParams(TypedDict, total=False):
    max_completion_tokens: int
    """The maximum number of tokens in the generated output."""

    reasoning_effort: Optional[ReasoningEffort]
    """
    Constrains effort on reasoning for
    [reasoning models](https://main.excai.ai/docs/guides/reasoning). Currently
    supported values are `minimal`, `low`, `medium`, and `high`. Reducing reasoning
    effort can result in faster responses and fewer tokens used on reasoning in a
    response.

    Note: The `gpt-5-pro` model defaults to (and only supports) `high` reasoning
    effort.
    """

    response_format: SamplingParamsResponseFormat
    """An object specifying the format that the model must output.

    Setting to `{ "type": "json_schema", "json_schema": {...} }` enables Structured
    Outputs which ensures the model will match your supplied JSON schema. Learn more
    in the
    [Structured Outputs guide](https://main.excai.ai/docs/guides/structured-outputs).

    Setting to `{ "type": "json_object" }` enables the older JSON mode, which
    ensures the message the model generates is valid JSON. Using `json_schema` is
    preferred for models that support it.
    """

    seed: int
    """A seed value to initialize the randomness, during sampling."""

    temperature: float
    """A higher temperature increases randomness in the outputs."""

    tools: Iterable[ChatCompletionToolParam]
    """A list of tools the model may call.

    Currently, only functions are supported as a tool. Use this to provide a list of
    functions the model may generate JSON inputs for. A max of 128 functions are
    supported.
    """

    top_p: float
    """An alternative to temperature for nucleus sampling; 1.0 includes all tokens."""


class CompletionsRunDataSourceParam(TypedDict, total=False):
    source: Required[Source]
    """Determines what populates the `item` namespace in this run's data source."""

    type: Required[Literal["completions"]]
    """The type of run data source. Always `completions`."""

    input_messages: InputMessages
    """Used when sampling from a model.

    Dictates the structure of the messages passed into the model. Can either be a
    reference to a prebuilt trajectory (ie, `item.input_trajectory`), or a template
    with variable references to the `item` namespace.
    """

    model: str
    """The name of the model to use for generating completions (e.g. "o3-mini")."""

    sampling_params: SamplingParams
