# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import List, Union, Iterable, Optional
from typing_extensions import Literal, Required, TypeAlias, TypedDict

from .truncation_param import TruncationParam
from ..reasoning_effort import ReasoningEffort
from ..file_search_ranker import FileSearchRanker
from ..chat.function_param import FunctionParam
from ..chat.metadata_param import MetadataParam
from .create_message_param import CreateMessageParam
from .assistant_tools_code_param import AssistantToolsCodeParam
from ..assistant_supported_models import AssistantSupportedModels
from .api_tool_choice_option_param import APIToolChoiceOptionParam
from .api_response_format_option_param import APIResponseFormatOptionParam

__all__ = [
    "RunCreateParams",
    "Tool",
    "ToolFileSearch",
    "ToolFileSearchFileSearch",
    "ToolFileSearchFileSearchRankingOptions",
    "ToolFunction",
]


class RunCreateParams(TypedDict, total=False):
    assistant_id: Required[str]
    """
    The ID of the [assistant](https://main.excai.ai/docs/api-reference/assistants)
    to use to execute this run.
    """

    include: List[Literal["step_details.tool_calls[*].file_search.results[*].content"]]
    """A list of additional fields to include in the response.

    Currently the only supported value is
    `step_details.tool_calls[*].file_search.results[*].content` to fetch the file
    search result content.

    See the
    [file search tool documentation](https://main.excai.ai/docs/assistants/tools/file-search#customizing-file-search-settings)
    for more information.
    """

    additional_instructions: Optional[str]
    """Appends additional instructions at the end of the instructions for the run.

    This is useful for modifying the behavior on a per-run basis without overriding
    other instructions.
    """

    additional_messages: Optional[Iterable[CreateMessageParam]]
    """Adds additional messages to the thread before creating the run."""

    instructions: Optional[str]
    """
    Overrides the
    [instructions](https://main.excai.ai/docs/api-reference/assistants/createAssistant)
    of the assistant. This is useful for modifying the behavior on a per-run basis.
    """

    max_completion_tokens: Optional[int]
    """
    The maximum number of completion tokens that may be used over the course of the
    run. The run will make a best effort to use only the number of completion tokens
    specified, across multiple turns of the run. If the run exceeds the number of
    completion tokens specified, the run will end with status `incomplete`. See
    `incomplete_details` for more info.
    """

    max_prompt_tokens: Optional[int]
    """The maximum number of prompt tokens that may be used over the course of the run.

    The run will make a best effort to use only the number of prompt tokens
    specified, across multiple turns of the run. If the run exceeds the number of
    prompt tokens specified, the run will end with status `incomplete`. See
    `incomplete_details` for more info.
    """

    metadata: Optional[MetadataParam]
    """Set of 16 key-value pairs that can be attached to an object.

    This can be useful for storing additional information about the object in a
    structured format, and querying for objects via API or the dashboard.

    Keys are strings with a maximum length of 64 characters. Values are strings with
    a maximum length of 512 characters.
    """

    model: Union[str, AssistantSupportedModels, None]
    """
    The ID of the [Model](https://main.excai.ai/docs/api-reference/models) to be
    used to execute this run. If a value is provided here, it will override the
    model associated with the assistant. If not, the model associated with the
    assistant will be used.
    """

    parallel_tool_calls: bool
    """
    Whether to enable
    [parallel function calling](https://main.excai.ai/docs/guides/function-calling#configuring-parallel-function-calling)
    during tool use.
    """

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

    stream: Optional[bool]
    """
    If `true`, returns a stream of events that happen during the Run as server-sent
    events, terminating when the Run enters a terminal state with a `data: [DONE]`
    message.
    """

    temperature: Optional[float]
    """What sampling temperature to use, between 0 and 2.

    Higher values like 0.8 will make the output more random, while lower values like
    0.2 will make it more focused and deterministic.
    """

    tool_choice: Optional[APIToolChoiceOptionParam]
    """
    Controls which (if any) tool is called by the model. `none` means the model will
    not call any tools and instead generates a message. `auto` is the default value
    and means the model can pick between generating a message or calling one or more
    tools. `required` means the model must call one or more tools before responding
    to the user. Specifying a particular tool like `{"type": "file_search"}` or
    `{"type": "function", "function": {"name": "my_function"}}` forces the model to
    call that tool.
    """

    tools: Optional[Iterable[Tool]]
    """Override the tools the assistant can use for this run.

    This is useful for modifying the behavior on a per-run basis.
    """

    top_p: Optional[float]
    """
    An alternative to sampling with temperature, called nucleus sampling, where the
    model considers the results of the tokens with top_p probability mass. So 0.1
    means only the tokens comprising the top 10% probability mass are considered.

    We generally recommend altering this or temperature but not both.
    """

    truncation_strategy: Optional[TruncationParam]
    """Controls for how a thread will be truncated prior to the run.

    Use this to control the initial context window of the run.
    """


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
