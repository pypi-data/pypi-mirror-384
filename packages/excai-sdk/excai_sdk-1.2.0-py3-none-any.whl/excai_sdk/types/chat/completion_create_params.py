# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, List, Union, Iterable, Optional
from typing_extensions import Literal, Required, TypeAlias, TypedDict

from .verbosity import Verbosity
from ..reasoning_effort import ReasoningEffort
from .text_format_param import TextFormatParam
from .shared_model_ids_param import SharedModelIDsParam
from ..voice_ids_shared_param import VoiceIDsSharedParam
from .text_content_part_param import TextContentPartParam
from .image_content_part_param import ImageContentPartParam
from .json_object_format_param import JsonObjectFormatParam
from .json_schema_format_param import JsonSchemaFormatParam
from ..stop_configuration_param import StopConfigurationParam
from .chat_completion_tool_param import ChatCompletionToolParam
from ..conversations.input_audio_param import InputAudioParam
from ..chat_completion_stream_options_param import ChatCompletionStreamOptionsParam
from .model_response_properties_create_param import ModelResponsePropertiesCreateParam
from .chat_completion_message_tool_call_union_param import ChatCompletionMessageToolCallUnionParam

__all__ = [
    "CompletionCreateParams",
    "Body",
    "BodyMessage",
    "BodyMessageDeveloper",
    "BodyMessageSystem",
    "BodyMessageUser",
    "BodyMessageUserContentArrayOfContentPart",
    "BodyMessageUserContentArrayOfContentPartFile",
    "BodyMessageUserContentArrayOfContentPartFileFile",
    "BodyMessageAssistant",
    "BodyMessageAssistantAudio",
    "BodyMessageAssistantContentArrayOfContentPart",
    "BodyMessageAssistantContentArrayOfContentPartRefusal",
    "BodyMessageAssistantFunctionCall",
    "BodyMessageTool",
    "BodyMessageFunction",
    "BodyAudio",
    "BodyFunctionCall",
    "BodyFunctionCallFunctionCallOption",
    "BodyFunction",
    "BodyPrediction",
    "BodyResponseFormat",
    "BodyToolChoice",
    "BodyToolChoiceChatCompletionAllowedToolsChoice",
    "BodyToolChoiceChatCompletionAllowedToolsChoiceAllowedTools",
    "BodyToolChoiceChatCompletionNamedToolChoice",
    "BodyToolChoiceChatCompletionNamedToolChoiceFunction",
    "BodyToolChoiceChatCompletionNamedToolChoiceCustom",
    "BodyToolChoiceChatCompletionNamedToolChoiceCustomCustom",
    "BodyTool",
    "BodyToolCustom",
    "BodyToolCustomCustom",
    "BodyToolCustomCustomFormat",
    "BodyToolCustomCustomFormatText",
    "BodyToolCustomCustomFormatGrammar",
    "BodyToolCustomCustomFormatGrammarGrammar",
    "BodyWebSearchOptions",
    "BodyWebSearchOptionsUserLocation",
    "BodyWebSearchOptionsUserLocationApproximate",
]


class CompletionCreateParams(TypedDict, total=False):
    body: Required[Body]


class BodyMessageDeveloper(TypedDict, total=False):
    content: Required[Union[str, Iterable[TextContentPartParam]]]
    """The contents of the developer message."""

    role: Required[Literal["developer"]]
    """The role of the messages author, in this case `developer`."""

    name: str
    """An optional name for the participant.

    Provides the model information to differentiate between participants of the same
    role.
    """


class BodyMessageSystem(TypedDict, total=False):
    content: Required[Union[str, Iterable[TextContentPartParam]]]
    """The contents of the system message."""

    role: Required[Literal["system"]]
    """The role of the messages author, in this case `system`."""

    name: str
    """An optional name for the participant.

    Provides the model information to differentiate between participants of the same
    role.
    """


class BodyMessageUserContentArrayOfContentPartFileFile(TypedDict, total=False):
    file_data: str
    """
    The base64 encoded file data, used when passing the file to the model as a
    string.
    """

    file_id: str
    """The ID of an uploaded file to use as input."""

    filename: str
    """The name of the file, used when passing the file to the model as a string."""


class BodyMessageUserContentArrayOfContentPartFile(TypedDict, total=False):
    file: Required[BodyMessageUserContentArrayOfContentPartFileFile]

    type: Required[Literal["file"]]
    """The type of the content part. Always `file`."""


BodyMessageUserContentArrayOfContentPart: TypeAlias = Union[
    TextContentPartParam, ImageContentPartParam, InputAudioParam, BodyMessageUserContentArrayOfContentPartFile
]


class BodyMessageUser(TypedDict, total=False):
    content: Required[Union[str, Iterable[BodyMessageUserContentArrayOfContentPart]]]
    """The contents of the user message."""

    role: Required[Literal["user"]]
    """The role of the messages author, in this case `user`."""

    name: str
    """An optional name for the participant.

    Provides the model information to differentiate between participants of the same
    role.
    """


class BodyMessageAssistantAudio(TypedDict, total=False):
    id: Required[str]
    """Unique identifier for a previous audio response from the model."""


class BodyMessageAssistantContentArrayOfContentPartRefusal(TypedDict, total=False):
    refusal: Required[str]
    """The refusal message generated by the model."""

    type: Required[Literal["refusal"]]
    """The type of the content part."""


BodyMessageAssistantContentArrayOfContentPart: TypeAlias = Union[
    TextContentPartParam, BodyMessageAssistantContentArrayOfContentPartRefusal
]


class BodyMessageAssistantFunctionCall(TypedDict, total=False):
    arguments: Required[str]
    """
    The arguments to call the function with, as generated by the model in JSON
    format. Note that the model does not always generate valid JSON, and may
    hallucinate parameters not defined by your function schema. Validate the
    arguments in your code before calling your function.
    """

    name: Required[str]
    """The name of the function to call."""


class BodyMessageAssistant(TypedDict, total=False):
    role: Required[Literal["assistant"]]
    """The role of the messages author, in this case `assistant`."""

    audio: Optional[BodyMessageAssistantAudio]
    """
    Data about a previous audio response from the model.
    [Learn more](https://main.excai.ai/docs/guides/audio).
    """

    content: Union[str, Iterable[BodyMessageAssistantContentArrayOfContentPart], None]
    """The contents of the assistant message.

    Required unless `tool_calls` or `function_call` is specified.
    """

    function_call: Optional[BodyMessageAssistantFunctionCall]
    """Deprecated and replaced by `tool_calls`.

    The name and arguments of a function that should be called, as generated by the
    model.
    """

    name: str
    """An optional name for the participant.

    Provides the model information to differentiate between participants of the same
    role.
    """

    refusal: Optional[str]
    """The refusal message by the assistant."""

    tool_calls: Iterable[ChatCompletionMessageToolCallUnionParam]
    """The tool calls generated by the model, such as function calls."""


class BodyMessageTool(TypedDict, total=False):
    content: Required[Union[str, Iterable[TextContentPartParam]]]
    """The contents of the tool message."""

    role: Required[Literal["tool"]]
    """The role of the messages author, in this case `tool`."""

    tool_call_id: Required[str]
    """Tool call that this message is responding to."""


class BodyMessageFunction(TypedDict, total=False):
    content: Required[Optional[str]]
    """The contents of the function message."""

    name: Required[str]
    """The name of the function to call."""

    role: Required[Literal["function"]]
    """The role of the messages author, in this case `function`."""


BodyMessage: TypeAlias = Union[
    BodyMessageDeveloper, BodyMessageSystem, BodyMessageUser, BodyMessageAssistant, BodyMessageTool, BodyMessageFunction
]


class BodyAudio(TypedDict, total=False):
    format: Required[Literal["wav", "aac", "mp3", "flac", "opus", "pcm16"]]
    """Specifies the output audio format.

    Must be one of `wav`, `mp3`, `flac`, `opus`, or `pcm16`.
    """

    voice: Required[VoiceIDsSharedParam]
    """The voice the model uses to respond.

    Supported voices are `alloy`, `ash`, `ballad`, `coral`, `echo`, `fable`, `nova`,
    `onyx`, `sage`, and `shimmer`.
    """


class BodyFunctionCallFunctionCallOption(TypedDict, total=False):
    name: Required[str]
    """The name of the function to call."""


BodyFunctionCall: TypeAlias = Union[Literal["none", "auto"], BodyFunctionCallFunctionCallOption]


class BodyFunction(TypedDict, total=False):
    name: Required[str]
    """The name of the function to be called.

    Must be a-z, A-Z, 0-9, or contain underscores and dashes, with a maximum length
    of 64.
    """

    description: str
    """
    A description of what the function does, used by the model to choose when and
    how to call the function.
    """

    parameters: Dict[str, object]
    """The parameters the functions accepts, described as a JSON Schema object.

    See the [guide](https://main.excai.ai/docs/guides/function-calling) for
    examples, and the
    [JSON Schema reference](https://json-schema.org/understanding-json-schema/) for
    documentation about the format.

    Omitting `parameters` defines a function with an empty parameter list.
    """


class BodyPrediction(TypedDict, total=False):
    content: Required[Union[str, Iterable[TextContentPartParam]]]
    """
    The content that should be matched when generating a model response. If
    generated tokens would match this content, the entire model response can be
    returned much more quickly.
    """

    type: Required[Literal["content"]]
    """The type of the predicted content you want to provide.

    This type is currently always `content`.
    """


BodyResponseFormat: TypeAlias = Union[TextFormatParam, JsonSchemaFormatParam, JsonObjectFormatParam]


class BodyToolChoiceChatCompletionAllowedToolsChoiceAllowedTools(TypedDict, total=False):
    mode: Required[Literal["auto", "required"]]
    """Constrains the tools available to the model to a pre-defined set.

    `auto` allows the model to pick from among the allowed tools and generate a
    message.

    `required` requires the model to call one or more of the allowed tools.
    """

    tools: Required[Iterable[Dict[str, object]]]
    """A list of tool definitions that the model should be allowed to call.

    For the Chat Completions API, the list of tool definitions might look like:

    ```json
    [
      { "type": "function", "function": { "name": "get_weather" } },
      { "type": "function", "function": { "name": "get_time" } }
    ]
    ```
    """


class BodyToolChoiceChatCompletionAllowedToolsChoice(TypedDict, total=False):
    allowed_tools: Required[BodyToolChoiceChatCompletionAllowedToolsChoiceAllowedTools]
    """Constrains the tools available to the model to a pre-defined set."""

    type: Required[Literal["allowed_tools"]]
    """Allowed tool configuration type. Always `allowed_tools`."""


class BodyToolChoiceChatCompletionNamedToolChoiceFunction(TypedDict, total=False):
    name: Required[str]
    """The name of the function to call."""


class BodyToolChoiceChatCompletionNamedToolChoice(TypedDict, total=False):
    function: Required[BodyToolChoiceChatCompletionNamedToolChoiceFunction]

    type: Required[Literal["function"]]
    """For function calling, the type is always `function`."""


class BodyToolChoiceChatCompletionNamedToolChoiceCustomCustom(TypedDict, total=False):
    name: Required[str]
    """The name of the custom tool to call."""


class BodyToolChoiceChatCompletionNamedToolChoiceCustom(TypedDict, total=False):
    custom: Required[BodyToolChoiceChatCompletionNamedToolChoiceCustomCustom]

    type: Required[Literal["custom"]]
    """For custom tool calling, the type is always `custom`."""


BodyToolChoice: TypeAlias = Union[
    Literal["none", "auto", "required"],
    BodyToolChoiceChatCompletionAllowedToolsChoice,
    BodyToolChoiceChatCompletionNamedToolChoice,
    BodyToolChoiceChatCompletionNamedToolChoiceCustom,
]


class BodyToolCustomCustomFormatText(TypedDict, total=False):
    type: Required[Literal["text"]]
    """Unconstrained text format. Always `text`."""


class BodyToolCustomCustomFormatGrammarGrammar(TypedDict, total=False):
    definition: Required[str]
    """The grammar definition."""

    syntax: Required[Literal["lark", "regex"]]
    """The syntax of the grammar definition. One of `lark` or `regex`."""


class BodyToolCustomCustomFormatGrammar(TypedDict, total=False):
    grammar: Required[BodyToolCustomCustomFormatGrammarGrammar]
    """Your chosen grammar."""

    type: Required[Literal["grammar"]]
    """Grammar format. Always `grammar`."""


BodyToolCustomCustomFormat: TypeAlias = Union[BodyToolCustomCustomFormatText, BodyToolCustomCustomFormatGrammar]


class BodyToolCustomCustom(TypedDict, total=False):
    name: Required[str]
    """The name of the custom tool, used to identify it in tool calls."""

    description: str
    """Optional description of the custom tool, used to provide more context."""

    format: BodyToolCustomCustomFormat
    """The input format for the custom tool. Default is unconstrained text."""


class BodyToolCustom(TypedDict, total=False):
    custom: Required[BodyToolCustomCustom]
    """Properties of the custom tool."""

    type: Required[Literal["custom"]]
    """The type of the custom tool. Always `custom`."""


BodyTool: TypeAlias = Union[ChatCompletionToolParam, BodyToolCustom]


class BodyWebSearchOptionsUserLocationApproximate(TypedDict, total=False):
    city: str
    """Free text input for the city of the user, e.g. `San Francisco`."""

    country: str
    """
    The two-letter [ISO country code](https://en.wikipedia.org/wiki/ISO_3166-1) of
    the user, e.g. `US`.
    """

    region: str
    """Free text input for the region of the user, e.g. `California`."""

    timezone: str
    """
    The [IANA timezone](https://timeapi.io/documentation/iana-timezones) of the
    user, e.g. `America/Los_Angeles`.
    """


class BodyWebSearchOptionsUserLocation(TypedDict, total=False):
    approximate: Required[BodyWebSearchOptionsUserLocationApproximate]
    """Approximate location parameters for the search."""

    type: Required[Literal["approximate"]]
    """The type of location approximation. Always `approximate`."""


class BodyWebSearchOptions(TypedDict, total=False):
    search_context_size: Literal["low", "medium", "high"]
    """
    High level guidance for the amount of context window space to use for the
    search. One of `low`, `medium`, or `high`. `medium` is the default.
    """

    user_location: Optional[BodyWebSearchOptionsUserLocation]
    """Approximate location parameters for the search."""


class Body(ModelResponsePropertiesCreateParam, total=False):
    messages: Required[Iterable[BodyMessage]]
    """A list of messages comprising the conversation so far.

    Depending on the [model](https://main.excai.ai/docs/models) you use, different
    message types (modalities) are supported, like
    [text](https://main.excai.ai/docs/guides/text-generation),
    [images](https://main.excai.ai/docs/guides/vision), and
    [audio](https://main.excai.ai/docs/guides/audio).
    """

    model: Required[SharedModelIDsParam]
    """Model ID used to generate the response, like `gpt-4o` or `o3`.

    EXCai offers a wide range of models with different capabilities, performance
    characteristics, and price points. Refer to the
    [model guide](https://main.excai.ai/docs/models) to browse and compare available
    models.
    """

    audio: Optional[BodyAudio]
    """Parameters for audio output.

    Required when audio output is requested with `modalities: ["audio"]`.
    [Learn more](https://main.excai.ai/docs/guides/audio).
    """

    frequency_penalty: Optional[float]
    """Number between -2.0 and 2.0.

    Positive values penalize new tokens based on their existing frequency in the
    text so far, decreasing the model's likelihood to repeat the same line verbatim.
    """

    function_call: BodyFunctionCall
    """Deprecated in favor of `tool_choice`.

    Controls which (if any) function is called by the model.

    `none` means the model will not call a function and instead generates a message.

    `auto` means the model can pick between generating a message or calling a
    function.

    Specifying a particular function via `{"name": "my_function"}` forces the model
    to call that function.

    `none` is the default when no functions are present. `auto` is the default if
    functions are present.
    """

    functions: Iterable[BodyFunction]
    """Deprecated in favor of `tools`.

    A list of functions the model may generate JSON inputs for.
    """

    logit_bias: Optional[Dict[str, int]]
    """Modify the likelihood of specified tokens appearing in the completion.

    Accepts a JSON object that maps tokens (specified by their token ID in the
    tokenizer) to an associated bias value from -100 to 100. Mathematically, the
    bias is added to the logits generated by the model prior to sampling. The exact
    effect will vary per model, but values between -1 and 1 should decrease or
    increase likelihood of selection; values like -100 or 100 should result in a ban
    or exclusive selection of the relevant token.
    """

    logprobs: Optional[bool]
    """Whether to return log probabilities of the output tokens or not.

    If true, returns the log probabilities of each output token returned in the
    `content` of `message`.
    """

    max_completion_tokens: Optional[int]
    """
    An upper bound for the number of tokens that can be generated for a completion,
    including visible output tokens and
    [reasoning tokens](https://main.excai.ai/docs/guides/reasoning).
    """

    max_tokens: Optional[int]
    """
    The maximum number of [tokens](/tokenizer) that can be generated in the chat
    completion. This value can be used to control
    [costs](https://excai.com/api/pricing/) for text generated via API.

    This value is now deprecated in favor of `max_completion_tokens`, and is not
    compatible with [o-series models](https://main.excai.ai/docs/guides/reasoning).
    """

    modalities: Optional[List[Literal["text", "audio"]]]
    """
    Output types that you would like the model to generate. Most models are capable
    of generating text, which is the default:

    `["text"]`

    The `gpt-4o-audio-preview` model can also be used to
    [generate audio](https://main.excai.ai/docs/guides/audio). To request that this
    model generate both text and audio responses, you can use:

    `["text", "audio"]`
    """

    n: Optional[int]
    """How many chat completion choices to generate for each input message.

    Note that you will be charged based on the number of generated tokens across all
    of the choices. Keep `n` as `1` to minimize costs.
    """

    parallel_tool_calls: bool
    """
    Whether to enable
    [parallel function calling](https://main.excai.ai/docs/guides/function-calling#configuring-parallel-function-calling)
    during tool use.
    """

    prediction: Optional[BodyPrediction]
    """
    Static predicted output content, such as the content of a text file that is
    being regenerated.
    """

    presence_penalty: Optional[float]
    """Number between -2.0 and 2.0.

    Positive values penalize new tokens based on whether they appear in the text so
    far, increasing the model's likelihood to talk about new topics.
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

    response_format: BodyResponseFormat
    """An object specifying the format that the model must output.

    Setting to `{ "type": "json_schema", "json_schema": {...} }` enables Structured
    Outputs which ensures the model will match your supplied JSON schema. Learn more
    in the
    [Structured Outputs guide](https://main.excai.ai/docs/guides/structured-outputs).

    Setting to `{ "type": "json_object" }` enables the older JSON mode, which
    ensures the message the model generates is valid JSON. Using `json_schema` is
    preferred for models that support it.
    """

    seed: Optional[int]
    """
    This feature is in Beta. If specified, our system will make a best effort to
    sample deterministically, such that repeated requests with the same `seed` and
    parameters should return the same result. Determinism is not guaranteed, and you
    should refer to the `system_fingerprint` response parameter to monitor changes
    in the backend.
    """

    stop: Optional[StopConfigurationParam]
    """Not supported with latest reasoning models `o3` and `o4-mini`.

    Up to 4 sequences where the API will stop generating further tokens. The
    returned text will not contain the stop sequence.
    """

    store: Optional[bool]
    """
    Whether or not to store the output of this chat completion request for use in
    our [model distillation](https://main.excai.ai/docs/guides/distillation) or
    [evals](https://main.excai.ai/docs/guides/evals) products.

    Supports text and image inputs. Note: image inputs over 8MB will be dropped.
    """

    stream: Optional[bool]
    """
    If set to true, the model response data will be streamed to the client as it is
    generated using
    [server-sent events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events#Event_stream_format).
    See the
    [Streaming section below](https://main.excai.ai/docs/api-reference/chat/streaming)
    for more information, along with the
    [streaming responses](https://main.excai.ai/docs/guides/streaming-responses)
    guide for more information on how to handle the streaming events.
    """

    stream_options: Optional[ChatCompletionStreamOptionsParam]
    """Options for streaming response. Only set this when you set `stream: true`."""

    tool_choice: BodyToolChoice
    """
    Controls which (if any) tool is called by the model. `none` means the model will
    not call any tool and instead generates a message. `auto` means the model can
    pick between generating a message or calling one or more tools. `required` means
    the model must call one or more tools. Specifying a particular tool via
    `{"type": "function", "function": {"name": "my_function"}}` forces the model to
    call that tool.

    `none` is the default when no tools are present. `auto` is the default if tools
    are present.
    """

    tools: Iterable[BodyTool]
    """A list of tools the model may call.

    You can provide either
    [custom tools](https://main.excai.ai/docs/guides/function-calling#custom-tools)
    or [function tools](https://main.excai.ai/docs/guides/function-calling).
    """

    top_logprobs: Optional[int]  # type: ignore
    """
    An integer between 0 and 20 specifying the number of most likely tokens to
    return at each token position, each with an associated log probability.
    `logprobs` must be set to `true` if this parameter is used.
    """

    verbosity: Optional[Verbosity]
    """Constrains the verbosity of the model's response.

    Lower values will result in more concise responses, while higher values will
    result in more verbose responses. Currently supported values are `low`,
    `medium`, and `high`.
    """

    web_search_options: BodyWebSearchOptions
    """
    This tool searches the web for relevant results to use in a response. Learn more
    about the
    [web search tool](https://main.excai.ai/docs/guides/tools-web-search?api-mode=chat).
    """
