# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import List, Union, Optional
from typing_extensions import Literal, Required, TypeAlias, TypedDict

from .noise_reduction_type import NoiseReductionType
from .audio_transcription_param import AudioTranscriptionParam
from .realtime.realtime_audio_formats_param import RealtimeAudioFormatsParam
from .realtime.realtime_session_create_param import RealtimeSessionCreateParam
from .realtime.realtime_turn_detection_param import RealtimeTurnDetectionParam

__all__ = [
    "RealtimeCreateClientSecretParams",
    "ExpiresAfter",
    "Session",
    "SessionTranscription",
    "SessionTranscriptionAudio",
    "SessionTranscriptionAudioInput",
    "SessionTranscriptionAudioInputNoiseReduction",
]


class RealtimeCreateClientSecretParams(TypedDict, total=False):
    expires_after: ExpiresAfter
    """Configuration for the client secret expiration.

    Expiration refers to the time after which a client secret will no longer be
    valid for creating sessions. The session itself may continue after that time
    once started. A secret can be used to create multiple sessions until it expires.
    """

    session: Session
    """Session configuration to use for the client secret.

    Choose either a realtime session or a transcription session.
    """


class ExpiresAfter(TypedDict, total=False):
    anchor: Literal["created_at"]
    """
    The anchor point for the client secret expiration, meaning that `seconds` will
    be added to the `created_at` time of the client secret to produce an expiration
    timestamp. Only `created_at` is currently supported.
    """

    seconds: int
    """The number of seconds from the anchor point to the expiration.

    Select a value between `10` and `7200` (2 hours). This default to 600 seconds
    (10 minutes) if not specified.
    """


class SessionTranscriptionAudioInputNoiseReduction(TypedDict, total=False):
    type: NoiseReductionType
    """Type of noise reduction.

    `near_field` is for close-talking microphones such as headphones, `far_field` is
    for far-field microphones such as laptop or conference room microphones.
    """


class SessionTranscriptionAudioInput(TypedDict, total=False):
    format: RealtimeAudioFormatsParam
    """The PCM audio format. Only a 24kHz sample rate is supported."""

    noise_reduction: SessionTranscriptionAudioInputNoiseReduction
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


class SessionTranscriptionAudio(TypedDict, total=False):
    input: SessionTranscriptionAudioInput


class SessionTranscription(TypedDict, total=False):
    type: Required[Literal["transcription"]]
    """The type of session to create.

    Always `transcription` for transcription sessions.
    """

    audio: SessionTranscriptionAudio
    """Configuration for input and output audio."""

    include: List[Literal["item.input_audio_transcription.logprobs"]]
    """Additional fields to include in server outputs.

    `item.input_audio_transcription.logprobs`: Include logprobs for input audio
    transcription.
    """


Session: TypeAlias = Union[RealtimeSessionCreateParam, SessionTranscription]
