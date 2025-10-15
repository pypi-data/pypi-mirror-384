# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from typing_extensions import Literal

from .._models import BaseModel
from .audio_transcription import AudioTranscription

__all__ = ["RealtimeCreateTranscriptionSessionResponse", "ClientSecret", "TurnDetection"]


class ClientSecret(BaseModel):
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


class TurnDetection(BaseModel):
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


class RealtimeCreateTranscriptionSessionResponse(BaseModel):
    client_secret: ClientSecret
    """Ephemeral key returned by the API.

    Only present when the session is created on the server via REST API.
    """

    input_audio_format: Optional[str] = None
    """The format of input audio. Options are `pcm16`, `g711_ulaw`, or `g711_alaw`."""

    input_audio_transcription: Optional[AudioTranscription] = None
    """Configuration of the transcription model."""

    modalities: Optional[List[Literal["text", "audio"]]] = None
    """The set of modalities the model can respond with.

    To disable audio, set this to ["text"].
    """

    turn_detection: Optional[TurnDetection] = None
    """Configuration for turn detection.

    Can be set to `null` to turn off. Server VAD means that the model will detect
    the start and end of speech based on audio volume and respond at the end of user
    speech.
    """
