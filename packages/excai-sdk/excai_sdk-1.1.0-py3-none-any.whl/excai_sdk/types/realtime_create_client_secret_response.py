# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias

from .._utils import PropertyInfo
from .._models import BaseModel
from .realtime.prompt import Prompt
from .voice_ids_shared import VoiceIDsShared
from .realtime.mcp_tool import McpTool
from .audio_transcription import AudioTranscription
from .noise_reduction_type import NoiseReductionType
from .realtime_function_tool import RealtimeFunctionTool
from .realtime.tool_choice_mcp import ToolChoiceMcp
from .realtime.realtime_truncation import RealtimeTruncation
from .realtime.tool_choice_options import ToolChoiceOptions
from .realtime.tool_choice_function import ToolChoiceFunction
from .realtime.realtime_audio_formats import RealtimeAudioFormats
from .realtime.realtime_turn_detection import RealtimeTurnDetection

__all__ = [
    "RealtimeCreateClientSecretResponse",
    "Session",
    "SessionRealtime",
    "SessionRealtimeClientSecret",
    "SessionRealtimeAudio",
    "SessionRealtimeAudioInput",
    "SessionRealtimeAudioInputNoiseReduction",
    "SessionRealtimeAudioOutput",
    "SessionRealtimeToolChoice",
    "SessionRealtimeTool",
    "SessionRealtimeTracing",
    "SessionRealtimeTracingTracingConfiguration",
    "SessionTranscription",
    "SessionTranscriptionAudio",
    "SessionTranscriptionAudioInput",
    "SessionTranscriptionAudioInputNoiseReduction",
    "SessionTranscriptionAudioInputTurnDetection",
]


class SessionRealtimeClientSecret(BaseModel):
    expires_at: int
    """Timestamp for when the token expires.

    Currently, all tokens expire after one minute.
    """

    value: str
    """
    Ephemeral key usable in client environments to authenticate connections to the
    Realtime API. Use this in client-side environments rather than a standard API
    token, which should only be used server-side.
    """


class SessionRealtimeAudioInputNoiseReduction(BaseModel):
    type: Optional[NoiseReductionType] = None
    """Type of noise reduction.

    `near_field` is for close-talking microphones such as headphones, `far_field` is
    for far-field microphones such as laptop or conference room microphones.
    """


class SessionRealtimeAudioInput(BaseModel):
    format: Optional[RealtimeAudioFormats] = None
    """The format of the input audio."""

    noise_reduction: Optional[SessionRealtimeAudioInputNoiseReduction] = None
    """Configuration for input audio noise reduction.

    This can be set to `null` to turn off. Noise reduction filters audio added to
    the input audio buffer before it is sent to VAD and the model. Filtering the
    audio can improve VAD and turn detection accuracy (reducing false positives) and
    model performance by improving perception of the input audio.
    """

    transcription: Optional[AudioTranscription] = None
    """
    Configuration for input audio transcription, defaults to off and can be set to
    `null` to turn off once on. Input audio transcription is not native to the
    model, since the model consumes audio directly. Transcription runs
    asynchronously through
    [the /audio/transcriptions endpoint](https://main.excai.ai/docs/api-reference/audio/createTranscription)
    and should be treated as guidance of input audio content rather than precisely
    what the model heard. The client can optionally set the language and prompt for
    transcription, these offer additional guidance to the transcription service.
    """

    turn_detection: Optional[RealtimeTurnDetection] = None
    """Configuration for turn detection, ether Server VAD or Semantic VAD.

    This can be set to `null` to turn off, in which case the client must manually
    trigger model response.

    Server VAD means that the model will detect the start and end of speech based on
    audio volume and respond at the end of user speech.

    Semantic VAD is more advanced and uses a turn detection model (in conjunction
    with VAD) to semantically estimate whether the user has finished speaking, then
    dynamically sets a timeout based on this probability. For example, if user audio
    trails off with "uhhm", the model will score a low probability of turn end and
    wait longer for the user to continue speaking. This can be useful for more
    natural conversations, but may have a higher latency.
    """


class SessionRealtimeAudioOutput(BaseModel):
    format: Optional[RealtimeAudioFormats] = None
    """The format of the output audio."""

    speed: Optional[float] = None
    """
    The speed of the model's spoken response as a multiple of the original speed.
    1.0 is the default speed. 0.25 is the minimum speed. 1.5 is the maximum speed.
    This value can only be changed in between model turns, not while a response is
    in progress.

    This parameter is a post-processing adjustment to the audio after it is
    generated, it's also possible to prompt the model to speak faster or slower.
    """

    voice: Optional[VoiceIDsShared] = None
    """The voice the model uses to respond.

    Voice cannot be changed during the session once the model has responded with
    audio at least once. Current voice options are `alloy`, `ash`, `ballad`,
    `coral`, `echo`, `sage`, `shimmer`, `verse`, `marin`, and `cedar`. We recommend
    `marin` and `cedar` for best quality.
    """


class SessionRealtimeAudio(BaseModel):
    input: Optional[SessionRealtimeAudioInput] = None

    output: Optional[SessionRealtimeAudioOutput] = None


SessionRealtimeToolChoice: TypeAlias = Union[ToolChoiceOptions, ToolChoiceFunction, ToolChoiceMcp]

SessionRealtimeTool: TypeAlias = Union[RealtimeFunctionTool, McpTool]


class SessionRealtimeTracingTracingConfiguration(BaseModel):
    group_id: Optional[str] = None
    """
    The group id to attach to this trace to enable filtering and grouping in the
    Traces Dashboard.
    """

    metadata: Optional[object] = None
    """
    The arbitrary metadata to attach to this trace to enable filtering in the Traces
    Dashboard.
    """

    workflow_name: Optional[str] = None
    """The name of the workflow to attach to this trace.

    This is used to name the trace in the Traces Dashboard.
    """


SessionRealtimeTracing: TypeAlias = Union[Literal["auto"], SessionRealtimeTracingTracingConfiguration, None]


class SessionRealtime(BaseModel):
    client_secret: SessionRealtimeClientSecret
    """Ephemeral key returned by the API."""

    type: Literal["realtime"]
    """The type of session to create. Always `realtime` for the Realtime API."""

    audio: Optional[SessionRealtimeAudio] = None
    """Configuration for input and output audio."""

    include: Optional[List[Literal["item.input_audio_transcription.logprobs"]]] = None
    """Additional fields to include in server outputs.

    `item.input_audio_transcription.logprobs`: Include logprobs for input audio
    transcription.
    """

    instructions: Optional[str] = None
    """The default system instructions (i.e.

    system message) prepended to model calls. This field allows the client to guide
    the model on desired responses. The model can be instructed on response content
    and format, (e.g. "be extremely succinct", "act friendly", "here are examples of
    good responses") and on audio behavior (e.g. "talk quickly", "inject emotion
    into your voice", "laugh frequently"). The instructions are not guaranteed to be
    followed by the model, but they provide guidance to the model on the desired
    behavior.

    Note that the server sets default instructions which will be used if this field
    is not set and are visible in the `session.created` event at the start of the
    session.
    """

    max_output_tokens: Union[int, Literal["inf"], None] = None
    """
    Maximum number of output tokens for a single assistant response, inclusive of
    tool calls. Provide an integer between 1 and 4096 to limit output tokens, or
    `inf` for the maximum available tokens for a given model. Defaults to `inf`.
    """

    model: Union[
        str,
        Literal[
            "gpt-realtime",
            "gpt-realtime-2025-08-28",
            "gpt-4o-realtime-preview",
            "gpt-4o-realtime-preview-2024-10-01",
            "gpt-4o-realtime-preview-2024-12-17",
            "gpt-4o-realtime-preview-2025-06-03",
            "gpt-4o-mini-realtime-preview",
            "gpt-4o-mini-realtime-preview-2024-12-17",
            "gpt-realtime-mini",
            "gpt-realtime-mini-2025-10-06",
            "gpt-audio-mini",
            "gpt-audio-mini-2025-10-06",
        ],
        None,
    ] = None
    """The Realtime model used for this session."""

    output_modalities: Optional[List[Literal["text", "audio"]]] = None
    """The set of modalities the model can respond with.

    It defaults to `["audio"]`, indicating that the model will respond with audio
    plus a transcript. `["text"]` can be used to make the model respond with text
    only. It is not possible to request both `text` and `audio` at the same time.
    """

    prompt: Optional[Prompt] = None
    """
    Reference to a prompt template and its variables.
    [Learn more](https://main.excai.ai/docs/guides/text?api-mode=responses#reusable-prompts).
    """

    tool_choice: Optional[SessionRealtimeToolChoice] = None
    """How the model chooses tools.

    Provide one of the string modes or force a specific function/MCP tool.
    """

    tools: Optional[List[SessionRealtimeTool]] = None
    """Tools available to the model."""

    tracing: Optional[SessionRealtimeTracing] = None
    """
    Realtime API can write session traces to the
    [Traces Dashboard](/logs?api=traces). Set to null to disable tracing. Once
    tracing is enabled for a session, the configuration cannot be modified.

    `auto` will create a trace for the session with default values for the workflow
    name, group id, and metadata.
    """

    truncation: Optional[RealtimeTruncation] = None
    """
    Controls how the realtime conversation is truncated prior to model inference.
    The default is `auto`.
    """


class SessionTranscriptionAudioInputNoiseReduction(BaseModel):
    type: Optional[NoiseReductionType] = None
    """Type of noise reduction.

    `near_field` is for close-talking microphones such as headphones, `far_field` is
    for far-field microphones such as laptop or conference room microphones.
    """


class SessionTranscriptionAudioInputTurnDetection(BaseModel):
    prefix_padding_ms: Optional[int] = None
    """Amount of audio to include before the VAD detected speech (in milliseconds).

    Defaults to 300ms.
    """

    silence_duration_ms: Optional[int] = None
    """Duration of silence to detect speech stop (in milliseconds).

    Defaults to 500ms. With shorter values the model will respond more quickly, but
    may jump in on short pauses from the user.
    """

    threshold: Optional[float] = None
    """Activation threshold for VAD (0.0 to 1.0), this defaults to 0.5.

    A higher threshold will require louder audio to activate the model, and thus
    might perform better in noisy environments.
    """

    type: Optional[str] = None
    """Type of turn detection, only `server_vad` is currently supported."""


class SessionTranscriptionAudioInput(BaseModel):
    format: Optional[RealtimeAudioFormats] = None
    """The PCM audio format. Only a 24kHz sample rate is supported."""

    noise_reduction: Optional[SessionTranscriptionAudioInputNoiseReduction] = None
    """Configuration for input audio noise reduction."""

    transcription: Optional[AudioTranscription] = None
    """Configuration of the transcription model."""

    turn_detection: Optional[SessionTranscriptionAudioInputTurnDetection] = None
    """Configuration for turn detection.

    Can be set to `null` to turn off. Server VAD means that the model will detect
    the start and end of speech based on audio volume and respond at the end of user
    speech.
    """


class SessionTranscriptionAudio(BaseModel):
    input: Optional[SessionTranscriptionAudioInput] = None


class SessionTranscription(BaseModel):
    id: str
    """Unique identifier for the session that looks like `sess_1234567890abcdef`."""

    object: str
    """The object type. Always `realtime.transcription_session`."""

    type: Literal["transcription"]
    """The type of session. Always `transcription` for transcription sessions."""

    audio: Optional[SessionTranscriptionAudio] = None
    """Configuration for input audio for the session."""

    expires_at: Optional[int] = None
    """Expiration timestamp for the session, in seconds since epoch."""

    include: Optional[List[Literal["item.input_audio_transcription.logprobs"]]] = None
    """Additional fields to include in server outputs.

    - `item.input_audio_transcription.logprobs`: Include logprobs for input audio
      transcription.
    """


Session: TypeAlias = Annotated[Union[SessionRealtime, SessionTranscription], PropertyInfo(discriminator="type")]


class RealtimeCreateClientSecretResponse(BaseModel):
    expires_at: int
    """Expiration timestamp for the client secret, in seconds since epoch."""

    session: Session
    """The session configuration for either a realtime or transcription session."""

    value: str
    """The generated client secret value."""
