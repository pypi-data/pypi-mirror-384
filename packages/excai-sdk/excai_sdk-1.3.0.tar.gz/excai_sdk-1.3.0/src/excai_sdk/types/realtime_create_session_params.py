# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import List, Union, Iterable, Optional
from typing_extensions import Literal, Required, TypeAlias, TypedDict

from .realtime.prompt_param import PromptParam
from .voice_ids_shared_param import VoiceIDsSharedParam
from .realtime.realtime_truncation_param import RealtimeTruncationParam

__all__ = [
    "RealtimeCreateSessionParams",
    "ClientSecret",
    "InputAudioTranscription",
    "Tool",
    "Tracing",
    "TracingTracingConfiguration",
    "TurnDetection",
]


class RealtimeCreateSessionParams(TypedDict, total=False):
    client_secret: Required[ClientSecret]
    """Ephemeral key returned by the API."""

    input_audio_format: str
    """The format of input audio. Options are `pcm16`, `g711_ulaw`, or `g711_alaw`."""

    input_audio_transcription: InputAudioTranscription
    """
    Configuration for input audio transcription, defaults to off and can be set to
    `null` to turn off once on. Input audio transcription is not native to the
    model, since the model consumes audio directly. Transcription runs
    asynchronously and should be treated as rough guidance rather than the
    representation understood by the model.
    """

    instructions: str
    """The default system instructions (i.e.

    system message) prepended to model calls. This field allows the client to guide
    the model on desired responses. The model can be instructed on response content
    and format, (e.g. "be extremely succinct", "act friendly", "here are examples of
    good responses") and on audio behavior (e.g. "talk quickly", "inject emotion
    into your voice", "laugh frequently"). The instructions are not guaranteed to be
    followed by the model, but they provide guidance to the model on the desired
    behavior. Note that the server sets default instructions which will be used if
    this field is not set and are visible in the `session.created` event at the
    start of the session.
    """

    max_response_output_tokens: Union[int, Literal["inf"]]
    """
    Maximum number of output tokens for a single assistant response, inclusive of
    tool calls. Provide an integer between 1 and 4096 to limit output tokens, or
    `inf` for the maximum available tokens for a given model. Defaults to `inf`.
    """

    modalities: List[Literal["text", "audio"]]
    """The set of modalities the model can respond with.

    To disable audio, set this to ["text"].
    """

    output_audio_format: str
    """The format of output audio. Options are `pcm16`, `g711_ulaw`, or `g711_alaw`."""

    prompt: Optional[PromptParam]
    """
    Reference to a prompt template and its variables.
    [Learn more](https://main.excai.ai/docs/guides/text?api-mode=responses#reusable-prompts).
    """

    speed: float
    """The speed of the model's spoken response.

    1.0 is the default speed. 0.25 is the minimum speed. 1.5 is the maximum speed.
    This value can only be changed in between model turns, not while a response is
    in progress.
    """

    temperature: float
    """Sampling temperature for the model, limited to [0.6, 1.2]. Defaults to 0.8."""

    tool_choice: str
    """How the model chooses tools.

    Options are `auto`, `none`, `required`, or specify a function.
    """

    tools: Iterable[Tool]
    """Tools (functions) available to the model."""

    tracing: Tracing
    """Configuration options for tracing.

    Set to null to disable tracing. Once tracing is enabled for a session, the
    configuration cannot be modified.

    `auto` will create a trace for the session with default values for the workflow
    name, group id, and metadata.
    """

    truncation: RealtimeTruncationParam
    """
    Controls how the realtime conversation is truncated prior to model inference.
    The default is `auto`.
    """

    turn_detection: TurnDetection
    """Configuration for turn detection.

    Can be set to `null` to turn off. Server VAD means that the model will detect
    the start and end of speech based on audio volume and respond at the end of user
    speech.
    """

    voice: VoiceIDsSharedParam
    """The voice the model uses to respond.

    Voice cannot be changed during the session once the model has responded with
    audio at least once. Current voice options are `alloy`, `ash`, `ballad`,
    `coral`, `echo`, `sage`, `shimmer`, and `verse`.
    """


class ClientSecret(TypedDict, total=False):
    expires_at: Required[int]
    """Timestamp for when the token expires.

    Currently, all tokens expire after one minute.
    """

    value: Required[str]
    """
    Ephemeral key usable in client environments to authenticate connections to the
    Realtime API. Use this in client-side environments rather than a standard API
    token, which should only be used server-side.
    """


class InputAudioTranscription(TypedDict, total=False):
    model: str
    """The model to use for transcription."""


class Tool(TypedDict, total=False):
    description: str
    """
    The description of the function, including guidance on when and how to call it,
    and guidance about what to tell the user when calling (if anything).
    """

    name: str
    """The name of the function."""

    parameters: object
    """Parameters of the function in JSON Schema."""

    type: Literal["function"]
    """The type of the tool, i.e. `function`."""


class TracingTracingConfiguration(TypedDict, total=False):
    group_id: str
    """
    The group id to attach to this trace to enable filtering and grouping in the
    traces dashboard.
    """

    metadata: object
    """
    The arbitrary metadata to attach to this trace to enable filtering in the traces
    dashboard.
    """

    workflow_name: str
    """The name of the workflow to attach to this trace.

    This is used to name the trace in the traces dashboard.
    """


Tracing: TypeAlias = Union[Literal["auto"], TracingTracingConfiguration]


class TurnDetection(TypedDict, total=False):
    prefix_padding_ms: int
    """Amount of audio to include before the VAD detected speech (in milliseconds).

    Defaults to 300ms.
    """

    silence_duration_ms: int
    """Duration of silence to detect speech stop (in milliseconds).

    Defaults to 500ms. With shorter values the model will respond more quickly, but
    may jump in on short pauses from the user.
    """

    threshold: float
    """Activation threshold for VAD (0.0 to 1.0), this defaults to 0.5.

    A higher threshold will require louder audio to activate the model, and thus
    might perform better in noisy environments.
    """

    type: str
    """Type of turn detection, only `server_vad` is currently supported."""
