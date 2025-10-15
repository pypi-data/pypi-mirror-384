# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Union, Iterable, Optional
from typing_extensions import Literal, Required, TypeAlias, TypedDict

from .chat.verbosity import Verbosity
from .reasoning_effort import ReasoningEffort
from .response_tool_param import ResponseToolParam
from .realtime.prompt_param import PromptParam
from .realtime.tool_choice_mcp_param import ToolChoiceMcpParam
from .realtime.tool_choice_function_param import ToolChoiceFunctionParam
from .text_response_format_configuration_param import TextResponseFormatConfigurationParam

__all__ = [
    "ResponsePropertiesParam",
    "Reasoning",
    "Text",
    "ToolChoice",
    "ToolChoiceAllowedTools",
    "ToolChoiceToolChoiceTypes",
    "ToolChoiceCustom",
]


class Reasoning(TypedDict, total=False):
    effort: Optional[ReasoningEffort]
    """
    Constrains effort on reasoning for
    [reasoning models](https://main.excai.ai/docs/guides/reasoning). Currently
    supported values are `minimal`, `low`, `medium`, and `high`. Reducing reasoning
    effort can result in faster responses and fewer tokens used on reasoning in a
    response.

    Note: The `gpt-5-pro` model defaults to (and only supports) `high` reasoning
    effort.
    """

    generate_summary: Optional[Literal["auto", "concise", "detailed"]]
    """**Deprecated:** use `summary` instead.

    A summary of the reasoning performed by the model. This can be useful for
    debugging and understanding the model's reasoning process. One of `auto`,
    `concise`, or `detailed`.
    """

    summary: Optional[Literal["auto", "concise", "detailed"]]
    """A summary of the reasoning performed by the model.

    This can be useful for debugging and understanding the model's reasoning
    process. One of `auto`, `concise`, or `detailed`.
    """


class Text(TypedDict, total=False):
    format: TextResponseFormatConfigurationParam
    """An object specifying the format that the model must output.

    Configuring `{ "type": "json_schema" }` enables Structured Outputs, which
    ensures the model will match your supplied JSON schema. Learn more in the
    [Structured Outputs guide](https://main.excai.ai/docs/guides/structured-outputs).

    The default format is `{ "type": "text" }` with no additional options.

    **Not recommended for gpt-4o and newer models:**

    Setting to `{ "type": "json_object" }` enables the older JSON mode, which
    ensures the message the model generates is valid JSON. Using `json_schema` is
    preferred for models that support it.
    """

    verbosity: Optional[Verbosity]
    """Constrains the verbosity of the model's response.

    Lower values will result in more concise responses, while higher values will
    result in more verbose responses. Currently supported values are `low`,
    `medium`, and `high`.
    """


class ToolChoiceAllowedTools(TypedDict, total=False):
    mode: Required[Literal["auto", "required"]]
    """Constrains the tools available to the model to a pre-defined set.

    `auto` allows the model to pick from among the allowed tools and generate a
    message.

    `required` requires the model to call one or more of the allowed tools.
    """

    tools: Required[Iterable[Dict[str, object]]]
    """A list of tool definitions that the model should be allowed to call.

    For the Responses API, the list of tool definitions might look like:

    ```json
    [
      { "type": "function", "name": "get_weather" },
      { "type": "mcp", "server_label": "deepwiki" },
      { "type": "image_generation" }
    ]
    ```
    """

    type: Required[Literal["allowed_tools"]]
    """Allowed tool configuration type. Always `allowed_tools`."""


class ToolChoiceToolChoiceTypes(TypedDict, total=False):
    type: Required[
        Literal[
            "file_search",
            "web_search_preview",
            "computer_use_preview",
            "web_search_preview_2025_03_11",
            "image_generation",
            "code_interpreter",
        ]
    ]
    """The type of hosted tool the model should to use.

    Learn more about [built-in tools](https://main.excai.ai/docs/guides/tools).

    Allowed values are:

    - `file_search`
    - `web_search_preview`
    - `computer_use_preview`
    - `code_interpreter`
    - `image_generation`
    """


class ToolChoiceCustom(TypedDict, total=False):
    name: Required[str]
    """The name of the custom tool to call."""

    type: Required[Literal["custom"]]
    """For custom tool calling, the type is always `custom`."""


ToolChoice: TypeAlias = Union[
    ToolChoiceAllowedTools, ToolChoiceToolChoiceTypes, ToolChoiceFunctionParam, ToolChoiceMcpParam, ToolChoiceCustom
]


class ResponsePropertiesParam(TypedDict, total=False):
    background: Optional[bool]
    """
    Whether to run the model response in the background.
    [Learn more](https://main.excai.ai/docs/guides/background).
    """

    max_output_tokens: Optional[int]
    """
    An upper bound for the number of tokens that can be generated for a response,
    including visible output tokens and
    [reasoning tokens](https://main.excai.ai/docs/guides/reasoning).
    """

    max_tool_calls: Optional[int]
    """
    The maximum number of total calls to built-in tools that can be processed in a
    response. This maximum number applies across all built-in tool calls, not per
    individual tool. Any further attempts to call a tool by the model will be
    ignored.
    """

    model: Union[
        Literal[
            "gpt-5",
            "gpt-5-mini",
            "gpt-5-nano",
            "gpt-5-2025-08-07",
            "gpt-5-mini-2025-08-07",
            "gpt-5-nano-2025-08-07",
            "gpt-5-chat-latest",
            "gpt-4.1",
            "gpt-4.1-mini",
            "gpt-4.1-nano",
            "gpt-4.1-2025-04-14",
            "gpt-4.1-mini-2025-04-14",
            "gpt-4.1-nano-2025-04-14",
            "o4-mini",
            "o4-mini-2025-04-16",
            "o3",
            "o3-2025-04-16",
            "o3-mini",
            "o3-mini-2025-01-31",
            "o1",
            "o1-2024-12-17",
            "o1-preview",
            "o1-preview-2024-09-12",
            "o1-mini",
            "o1-mini-2024-09-12",
            "gpt-4o",
            "gpt-4o-2024-11-20",
            "gpt-4o-2024-08-06",
            "gpt-4o-2024-05-13",
            "gpt-4o-audio-preview",
            "gpt-4o-audio-preview-2024-10-01",
            "gpt-4o-audio-preview-2024-12-17",
            "gpt-4o-audio-preview-2025-06-03",
            "gpt-4o-mini-audio-preview",
            "gpt-4o-mini-audio-preview-2024-12-17",
            "gpt-4o-search-preview",
            "gpt-4o-mini-search-preview",
            "gpt-4o-search-preview-2025-03-11",
            "gpt-4o-mini-search-preview-2025-03-11",
            "chatgpt-4o-latest",
            "codex-mini-latest",
            "gpt-4o-mini",
            "gpt-4o-mini-2024-07-18",
            "gpt-4-turbo",
            "gpt-4-turbo-2024-04-09",
            "gpt-4-0125-preview",
            "gpt-4-turbo-preview",
            "gpt-4-1106-preview",
            "gpt-4-vision-preview",
            "gpt-4",
            "gpt-4-0314",
            "gpt-4-0613",
            "gpt-4-32k",
            "gpt-4-32k-0314",
            "gpt-4-32k-0613",
            "gpt-3.5-turbo",
            "gpt-3.5-turbo-16k",
            "gpt-3.5-turbo-0301",
            "gpt-3.5-turbo-0613",
            "gpt-3.5-turbo-1106",
            "gpt-3.5-turbo-0125",
            "gpt-3.5-turbo-16k-0613",
            "o1-pro",
            "o1-pro-2025-03-19",
            "o3-pro",
            "o3-pro-2025-06-10",
            "o3-deep-research",
            "o3-deep-research-2025-06-26",
            "o4-mini-deep-research",
            "o4-mini-deep-research-2025-06-26",
            "computer-use-preview",
            "computer-use-preview-2025-03-11",
            "gpt-5-codex",
            "gpt-5-pro",
            "gpt-5-pro-2025-10-06",
        ],
        str,
    ]
    """Model ID used to generate the response, like `gpt-4o` or `o3`.

    EXCai offers a wide range of models with different capabilities, performance
    characteristics, and price points. Refer to the
    [model guide](https://main.excai.ai/docs/models) to browse and compare available
    models.
    """

    previous_response_id: Optional[str]
    """The unique ID of the previous response to the model.

    Use this to create multi-turn conversations. Learn more about
    [conversation state](https://main.excai.ai/docs/guides/conversation-state).
    Cannot be used in conjunction with `conversation`.
    """

    prompt: Optional[PromptParam]
    """
    Reference to a prompt template and its variables.
    [Learn more](https://main.excai.ai/docs/guides/text?api-mode=responses#reusable-prompts).
    """

    reasoning: Optional[Reasoning]
    """**gpt-5 and o-series models only**

    Configuration options for
    [reasoning models](https://main.excai.ai/docs/guides/reasoning).
    """

    text: Text
    """Configuration options for a text response from the model.

    Can be plain text or structured JSON data. Learn more:

    - [Text inputs and outputs](https://main.excai.ai/docs/guides/text)
    - [Structured Outputs](https://main.excai.ai/docs/guides/structured-outputs)
    """

    tool_choice: ToolChoice
    """
    How the model should select which tool (or tools) to use when generating a
    response. See the `tools` parameter to see how to specify which tools the model
    can call.
    """

    tools: Iterable[ResponseToolParam]
    """An array of tools the model may call while generating a response.

    You can specify which tool to use by setting the `tool_choice` parameter.

    We support the following categories of tools:

    - **Built-in tools**: Tools that are provided by EXCai that extend the model's
      capabilities, like
      [web search](https://main.excai.ai/docs/guides/tools-web-search) or
      [file search](https://main.excai.ai/docs/guides/tools-file-search). Learn more
      about [built-in tools](https://main.excai.ai/docs/guides/tools).
    - **MCP Tools**: Integrations with third-party systems via custom MCP servers or
      predefined connectors such as Google Drive and SharePoint. Learn more about
      [MCP Tools](https://main.excai.ai/docs/guides/tools-connectors-mcp).
    - **Function calls (custom tools)**: Functions that are defined by you, enabling
      the model to call your own code with strongly typed arguments and outputs.
      Learn more about
      [function calling](https://main.excai.ai/docs/guides/function-calling). You
      can also use custom tools to call your own code.
    """

    truncation: Optional[Literal["auto", "disabled"]]
    """The truncation strategy to use for the model response.

    - `auto`: If the input to this Response exceeds the model's context window size,
      the model will truncate the response to fit the context window by dropping
      items from the beginning of the conversation.
    - `disabled` (default): If the input size will exceed the context window size
      for a model, the request will fail with a 400 error.
    """
