# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import List, Union, Iterable, Optional
from typing_extensions import Literal, Required, TypeAlias, TypedDict

from .prompt_param import PromptParam
from .mcp_tool_param import McpToolParam
from .tool_choice_options import ToolChoiceOptions
from ..noise_reduction_type import NoiseReductionType
from .tool_choice_mcp_param import ToolChoiceMcpParam
from ..voice_ids_shared_param import VoiceIDsSharedParam
from .realtime_truncation_param import RealtimeTruncationParam
from ..audio_transcription_param import AudioTranscriptionParam
from .tool_choice_function_param import ToolChoiceFunctionParam
from .realtime_audio_formats_param import RealtimeAudioFormatsParam
from ..realtime_function_tool_param import RealtimeFunctionToolParam
from .realtime_turn_detection_param import RealtimeTurnDetectionParam

__all__ = [
    "CallAcceptParams",
    "Audio",
    "AudioInput",
    "AudioInputNoiseReduction",
    "AudioOutput",
    "ToolChoice",
    "Tool",
    "Tracing",
    "TracingTracingConfiguration",
]


class CallAcceptParams(TypedDict, total=False):
    type: Required[Literal["realtime"]]
    """The type of session to create. Always `realtime` for the Realtime API."""

    audio: Audio
    """Configuration for input and output audio."""

    include: List[Literal["item.input_audio_transcription.logprobs"]]
    """Additional fields to include in server outputs.

    `item.input_audio_transcription.logprobs`: Include logprobs for input audio
    transcription.
    """

    instructions: str
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

    max_output_tokens: Union[int, Literal["inf"]]
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
    ]
    """The Realtime model used for this session."""

    output_modalities: List[Literal["text", "audio"]]
    """The set of modalities the model can respond with.

    It defaults to `["audio"]`, indicating that the model will respond with audio
    plus a transcript. `["text"]` can be used to make the model respond with text
    only. It is not possible to request both `text` and `audio` at the same time.
    """

    prompt: Optional[PromptParam]
    """
    Reference to a prompt template and its variables.
    [Learn more](https://main.excai.ai/docs/guides/text?api-mode=responses#reusable-prompts).
    """

    tool_choice: ToolChoice
    """How the model chooses tools.

    Provide one of the string modes or force a specific function/MCP tool.
    """

    tools: Iterable[Tool]
    """Tools available to the model."""

    tracing: Optional[Tracing]
    """
    Realtime API can write session traces to the
    [Traces Dashboard](/logs?api=traces). Set to null to disable tracing. Once
    tracing is enabled for a session, the configuration cannot be modified.

    `auto` will create a trace for the session with default values for the workflow
    name, group id, and metadata.
    """

    truncation: RealtimeTruncationParam
    """
    Controls how the realtime conversation is truncated prior to model inference.
    The default is `auto`.
    """


class AudioInputNoiseReduction(TypedDict, total=False):
    type: NoiseReductionType
    """Type of noise reduction.

    `near_field` is for close-talking microphones such as headphones, `far_field` is
    for far-field microphones such as laptop or conference room microphones.
    """


class AudioInput(TypedDict, total=False):
    format: RealtimeAudioFormatsParam
    """The format of the input audio."""

    noise_reduction: AudioInputNoiseReduction
    """Configuration for input audio noise reduction.

    This can be set to `null` to turn off. Noise reduction filters audio added to
    the input audio buffer before it is sent to VAD and the model. Filtering the
    audio can improve VAD and turn detection accuracy (reducing false positives) and
    model performance by improving perception of the input audio.
    """

    transcription: AudioTranscriptionParam
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

    turn_detection: Optional[RealtimeTurnDetectionParam]
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


class AudioOutput(TypedDict, total=False):
    format: RealtimeAudioFormatsParam
    """The format of the output audio."""

    speed: float
    """
    The speed of the model's spoken response as a multiple of the original speed.
    1.0 is the default speed. 0.25 is the minimum speed. 1.5 is the maximum speed.
    This value can only be changed in between model turns, not while a response is
    in progress.

    This parameter is a post-processing adjustment to the audio after it is
    generated, it's also possible to prompt the model to speak faster or slower.
    """

    voice: VoiceIDsSharedParam
    """The voice the model uses to respond.

    Voice cannot be changed during the session once the model has responded with
    audio at least once. Current voice options are `alloy`, `ash`, `ballad`,
    `coral`, `echo`, `sage`, `shimmer`, `verse`, `marin`, and `cedar`. We recommend
    `marin` and `cedar` for best quality.
    """


class Audio(TypedDict, total=False):
    input: AudioInput

    output: AudioOutput


ToolChoice: TypeAlias = Union[ToolChoiceOptions, ToolChoiceFunctionParam, ToolChoiceMcpParam]

Tool: TypeAlias = Union[RealtimeFunctionToolParam, McpToolParam]


class TracingTracingConfiguration(TypedDict, total=False):
    group_id: str
    """
    The group id to attach to this trace to enable filtering and grouping in the
    Traces Dashboard.
    """

    metadata: object
    """
    The arbitrary metadata to attach to this trace to enable filtering in the Traces
    Dashboard.
    """

    workflow_name: str
    """The name of the workflow to attach to this trace.

    This is used to name the trace in the Traces Dashboard.
    """


Tracing: TypeAlias = Union[Literal["auto"], TracingTracingConfiguration]
