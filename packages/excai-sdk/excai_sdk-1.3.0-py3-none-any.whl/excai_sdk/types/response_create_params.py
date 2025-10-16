# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import List, Union, Iterable, Optional
from typing_extensions import Required, TypeAlias, TypedDict

from .conversations.includable import Includable
from .response_properties_param import ResponsePropertiesParam
from .conversations.input_item_param import InputItemParam
from .chat.model_response_properties_create_param import ModelResponsePropertiesCreateParam

__all__ = ["ResponseCreateParams", "Body", "BodyConversation", "BodyConversationConversationParam", "BodyStreamOptions"]


class ResponseCreateParams(TypedDict, total=False):
    body: Required[Body]


class BodyConversationConversationParam(TypedDict, total=False):
    id: Required[str]
    """The unique ID of the conversation."""


BodyConversation: TypeAlias = Union[str, BodyConversationConversationParam]


class BodyStreamOptions(TypedDict, total=False):
    include_obfuscation: bool
    """When true, stream obfuscation will be enabled.

    Stream obfuscation adds random characters to an `obfuscation` field on streaming
    delta events to normalize payload sizes as a mitigation to certain side-channel
    attacks. These obfuscation fields are included by default, but add a small
    amount of overhead to the data stream. You can set `include_obfuscation` to
    false to optimize for bandwidth if you trust the network links between your
    application and the EXCai API.
    """


class Body(ModelResponsePropertiesCreateParam, ResponsePropertiesParam, total=False):
    conversation: Optional[BodyConversation]
    """The conversation that this response belongs to.

    Items from this conversation are prepended to `input_items` for this response
    request. Input items and output items from this response are automatically added
    to this conversation after this response completes.
    """

    include: Optional[List[Includable]]
    """Specify additional output data to include in the model response.

    Currently supported values are:

    - `web_search_call.action.sources`: Include the sources of the web search tool
      call.
    - `code_interpreter_call.outputs`: Includes the outputs of python code execution
      in code interpreter tool call items.
    - `computer_call_output.output.image_url`: Include image urls from the computer
      call output.
    - `file_search_call.results`: Include the search results of the file search tool
      call.
    - `message.input_image.image_url`: Include image urls from the input message.
    - `message.output_text.logprobs`: Include logprobs with assistant messages.
    - `reasoning.encrypted_content`: Includes an encrypted version of reasoning
      tokens in reasoning item outputs. This enables reasoning items to be used in
      multi-turn conversations when using the Responses API statelessly (like when
      the `store` parameter is set to `false`, or when an organization is enrolled
      in the zero data retention program).
    """

    input: Union[str, Iterable[InputItemParam]]
    """Text, image, or file inputs to the model, used to generate a response.

    Learn more:

    - [Text inputs and outputs](https://main.excai.ai/docs/guides/text)
    - [Image inputs](https://main.excai.ai/docs/guides/images)
    - [File inputs](https://main.excai.ai/docs/guides/pdf-files)
    - [Conversation state](https://main.excai.ai/docs/guides/conversation-state)
    - [Function calling](https://main.excai.ai/docs/guides/function-calling)
    """

    instructions: Optional[str]
    """A system (or developer) message inserted into the model's context.

    When using along with `previous_response_id`, the instructions from a previous
    response will not be carried over to the next response. This makes it simple to
    swap out system (or developer) messages in new responses.
    """

    parallel_tool_calls: Optional[bool]
    """Whether to allow the model to run tool calls in parallel."""

    store: Optional[bool]
    """Whether to store the generated model response for later retrieval via API."""

    stream: Optional[bool]
    """
    If set to true, the model response data will be streamed to the client as it is
    generated using
    [server-sent events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events#Event_stream_format).
    See the
    [Streaming section below](https://main.excai.ai/docs/api-reference/responses-streaming)
    for more information.
    """

    stream_options: Optional[BodyStreamOptions]
    """Options for streaming responses. Only set this when you set `stream: true`."""
