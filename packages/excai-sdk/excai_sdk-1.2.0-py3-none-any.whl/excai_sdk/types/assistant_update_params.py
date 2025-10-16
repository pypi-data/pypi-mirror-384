# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union, Iterable, Optional
from typing_extensions import Literal, Required, TypeAlias, TypedDict

from .._types import SequenceNotStr
from .reasoning_effort import ReasoningEffort
from .file_search_ranker import FileSearchRanker
from .chat.function_param import FunctionParam
from .chat.metadata_param import MetadataParam
from .assistant_supported_models import AssistantSupportedModels
from .threads.assistant_tools_code_param import AssistantToolsCodeParam
from .threads.api_response_format_option_param import APIResponseFormatOptionParam

__all__ = [
    "AssistantUpdateParams",
    "ToolResources",
    "ToolResourcesCodeInterpreter",
    "ToolResourcesFileSearch",
    "Tool",
    "ToolFileSearch",
    "ToolFileSearchFileSearch",
    "ToolFileSearchFileSearchRankingOptions",
    "ToolFunction",
]


class AssistantUpdateParams(TypedDict, total=False):
    description: Optional[str]
    """The description of the assistant. The maximum length is 512 characters."""

    instructions: Optional[str]
    """The system instructions that the assistant uses.

    The maximum length is 256,000 characters.
    """

    metadata: Optional[MetadataParam]
    """Set of 16 key-value pairs that can be attached to an object.

    This can be useful for storing additional information about the object in a
    structured format, and querying for objects via API or the dashboard.

    Keys are strings with a maximum length of 64 characters. Values are strings with
    a maximum length of 512 characters.
    """

    model: Union[str, AssistantSupportedModels]
    """ID of the model to use.

    You can use the
    [List models](https://main.excai.ai/docs/api-reference/models/list) API to see
    all of your available models, or see our
    [Model overview](https://main.excai.ai/docs/models) for descriptions of them.
    """

    name: Optional[str]
    """The name of the assistant. The maximum length is 256 characters."""

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

    response_format: Optional[APIResponseFormatOptionParam]
    """Specifies the format that the model must output.

    Compatible with [GPT-4o](https://main.excai.ai/docs/models#gpt-4o),
    [GPT-4 Turbo](https://main.excai.ai/docs/models#gpt-4-turbo-and-gpt-4), and all
    GPT-3.5 Turbo models since `gpt-3.5-turbo-1106`.

    Setting to `{ "type": "json_schema", "json_schema": {...} }` enables Structured
    Outputs which ensures the model will match your supplied JSON schema. Learn more
    in the
    [Structured Outputs guide](https://main.excai.ai/docs/guides/structured-outputs).

    Setting to `{ "type": "json_object" }` enables JSON mode, which ensures the
    message the model generates is valid JSON.

    **Important:** when using JSON mode, you **must** also instruct the model to
    produce JSON yourself via a system or user message. Without this, the model may
    generate an unending stream of whitespace until the generation reaches the token
    limit, resulting in a long-running and seemingly "stuck" request. Also note that
    the message content may be partially cut off if `finish_reason="length"`, which
    indicates the generation exceeded `max_tokens` or the conversation exceeded the
    max context length.
    """

    temperature: Optional[float]
    """What sampling temperature to use, between 0 and 2.

    Higher values like 0.8 will make the output more random, while lower values like
    0.2 will make it more focused and deterministic.
    """

    tool_resources: Optional[ToolResources]
    """A set of resources that are used by the assistant's tools.

    The resources are specific to the type of tool. For example, the
    `code_interpreter` tool requires a list of file IDs, while the `file_search`
    tool requires a list of vector store IDs.
    """

    tools: Iterable[Tool]
    """A list of tool enabled on the assistant.

    There can be a maximum of 128 tools per assistant. Tools can be of types
    `code_interpreter`, `file_search`, or `function`.
    """

    top_p: Optional[float]
    """
    An alternative to sampling with temperature, called nucleus sampling, where the
    model considers the results of the tokens with top_p probability mass. So 0.1
    means only the tokens comprising the top 10% probability mass are considered.

    We generally recommend altering this or temperature but not both.
    """


class ToolResourcesCodeInterpreter(TypedDict, total=False):
    file_ids: SequenceNotStr[str]
    """
    Overrides the list of [file](https://main.excai.ai/docs/api-reference/files) IDs
    made available to the `code_interpreter` tool. There can be a maximum of 20
    files associated with the tool.
    """


class ToolResourcesFileSearch(TypedDict, total=False):
    vector_store_ids: SequenceNotStr[str]
    """
    Overrides the
    [vector store](https://main.excai.ai/docs/api-reference/vector-stores/object)
    attached to this assistant. There can be a maximum of 1 vector store attached to
    the assistant.
    """


class ToolResources(TypedDict, total=False):
    code_interpreter: ToolResourcesCodeInterpreter

    file_search: ToolResourcesFileSearch


class ToolFileSearchFileSearchRankingOptions(TypedDict, total=False):
    score_threshold: Required[float]
    """The score threshold for the file search.

    All values must be a floating point number between 0 and 1.
    """

    ranker: FileSearchRanker
    """The ranker to use for the file search.

    If not specified will use the `auto` ranker.
    """


class ToolFileSearchFileSearch(TypedDict, total=False):
    max_num_results: int
    """The maximum number of results the file search tool should output.

    The default is 20 for `gpt-4*` models and 5 for `gpt-3.5-turbo`. This number
    should be between 1 and 50 inclusive.

    Note that the file search tool may output fewer than `max_num_results` results.
    See the
    [file search tool documentation](https://main.excai.ai/docs/assistants/tools/file-search#customizing-file-search-settings)
    for more information.
    """

    ranking_options: ToolFileSearchFileSearchRankingOptions
    """The ranking options for the file search.

    If not specified, the file search tool will use the `auto` ranker and a
    score_threshold of 0.

    See the
    [file search tool documentation](https://main.excai.ai/docs/assistants/tools/file-search#customizing-file-search-settings)
    for more information.
    """


class ToolFileSearch(TypedDict, total=False):
    type: Required[Literal["file_search"]]
    """The type of tool being defined: `file_search`"""

    file_search: ToolFileSearchFileSearch
    """Overrides for the file search tool."""


class ToolFunction(TypedDict, total=False):
    function: Required[FunctionParam]

    type: Required[Literal["function"]]
    """The type of tool being defined: `function`"""


Tool: TypeAlias = Union[AssistantToolsCodeParam, ToolFileSearch, ToolFunction]
