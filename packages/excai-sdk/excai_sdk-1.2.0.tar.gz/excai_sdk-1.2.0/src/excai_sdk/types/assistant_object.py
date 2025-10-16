# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias

from .._utils import PropertyInfo
from .._models import BaseModel
from .chat.function import Function
from .chat.metadata import Metadata
from .file_search_ranker import FileSearchRanker
from .threads.assistant_tools_code import AssistantToolsCode
from .threads.api_response_format_option import APIResponseFormatOption

__all__ = [
    "AssistantObject",
    "Tool",
    "ToolFileSearch",
    "ToolFileSearchFileSearch",
    "ToolFileSearchFileSearchRankingOptions",
    "ToolFunction",
    "ToolResources",
    "ToolResourcesCodeInterpreter",
    "ToolResourcesFileSearch",
]


class ToolFileSearchFileSearchRankingOptions(BaseModel):
    score_threshold: float
    """The score threshold for the file search.

    All values must be a floating point number between 0 and 1.
    """

    ranker: Optional[FileSearchRanker] = None
    """The ranker to use for the file search.

    If not specified will use the `auto` ranker.
    """


class ToolFileSearchFileSearch(BaseModel):
    max_num_results: Optional[int] = None
    """The maximum number of results the file search tool should output.

    The default is 20 for `gpt-4*` models and 5 for `gpt-3.5-turbo`. This number
    should be between 1 and 50 inclusive.

    Note that the file search tool may output fewer than `max_num_results` results.
    See the
    [file search tool documentation](https://main.excai.ai/docs/assistants/tools/file-search#customizing-file-search-settings)
    for more information.
    """

    ranking_options: Optional[ToolFileSearchFileSearchRankingOptions] = None
    """The ranking options for the file search.

    If not specified, the file search tool will use the `auto` ranker and a
    score_threshold of 0.

    See the
    [file search tool documentation](https://main.excai.ai/docs/assistants/tools/file-search#customizing-file-search-settings)
    for more information.
    """


class ToolFileSearch(BaseModel):
    type: Literal["file_search"]
    """The type of tool being defined: `file_search`"""

    file_search: Optional[ToolFileSearchFileSearch] = None
    """Overrides for the file search tool."""


class ToolFunction(BaseModel):
    function: Function

    type: Literal["function"]
    """The type of tool being defined: `function`"""


Tool: TypeAlias = Annotated[Union[AssistantToolsCode, ToolFileSearch, ToolFunction], PropertyInfo(discriminator="type")]


class ToolResourcesCodeInterpreter(BaseModel):
    file_ids: Optional[List[str]] = None
    """
    A list of [file](https://main.excai.ai/docs/api-reference/files) IDs made
    available to the `code_interpreter`` tool. There can be a maximum of 20 files
    associated with the tool.
    """


class ToolResourcesFileSearch(BaseModel):
    vector_store_ids: Optional[List[str]] = None
    """
    The ID of the
    [vector store](https://main.excai.ai/docs/api-reference/vector-stores/object)
    attached to this assistant. There can be a maximum of 1 vector store attached to
    the assistant.
    """


class ToolResources(BaseModel):
    code_interpreter: Optional[ToolResourcesCodeInterpreter] = None

    file_search: Optional[ToolResourcesFileSearch] = None


class AssistantObject(BaseModel):
    id: str
    """The identifier, which can be referenced in API endpoints."""

    created_at: int
    """The Unix timestamp (in seconds) for when the assistant was created."""

    description: Optional[str] = None
    """The description of the assistant. The maximum length is 512 characters."""

    instructions: Optional[str] = None
    """The system instructions that the assistant uses.

    The maximum length is 256,000 characters.
    """

    metadata: Optional[Metadata] = None
    """Set of 16 key-value pairs that can be attached to an object.

    This can be useful for storing additional information about the object in a
    structured format, and querying for objects via API or the dashboard.

    Keys are strings with a maximum length of 64 characters. Values are strings with
    a maximum length of 512 characters.
    """

    model: str
    """ID of the model to use.

    You can use the
    [List models](https://main.excai.ai/docs/api-reference/models/list) API to see
    all of your available models, or see our
    [Model overview](https://main.excai.ai/docs/models) for descriptions of them.
    """

    name: Optional[str] = None
    """The name of the assistant. The maximum length is 256 characters."""

    object: Literal["assistant"]
    """The object type, which is always `assistant`."""

    tools: List[Tool]
    """A list of tool enabled on the assistant.

    There can be a maximum of 128 tools per assistant. Tools can be of types
    `code_interpreter`, `file_search`, or `function`.
    """

    response_format: Optional[APIResponseFormatOption] = None
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

    temperature: Optional[float] = None
    """What sampling temperature to use, between 0 and 2.

    Higher values like 0.8 will make the output more random, while lower values like
    0.2 will make it more focused and deterministic.
    """

    tool_resources: Optional[ToolResources] = None
    """A set of resources that are used by the assistant's tools.

    The resources are specific to the type of tool. For example, the
    `code_interpreter` tool requires a list of file IDs, while the `file_search`
    tool requires a list of vector store IDs.
    """

    top_p: Optional[float] = None
    """
    An alternative to sampling with temperature, called nucleus sampling, where the
    model considers the results of the tokens with top_p probability mass. So 0.1
    means only the tokens comprising the top 10% probability mass are considered.

    We generally recommend altering this or temperature but not both.
    """
