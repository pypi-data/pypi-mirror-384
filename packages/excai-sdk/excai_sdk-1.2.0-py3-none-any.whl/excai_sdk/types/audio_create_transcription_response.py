# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias

from .._utils import PropertyInfo
from .._models import BaseModel
from .transcription_segment import TranscriptionSegment
from .transcript_text_usage_duration import TranscriptTextUsageDuration

__all__ = [
    "AudioCreateTranscriptionResponse",
    "CreateTranscriptionResponseJson",
    "CreateTranscriptionResponseJsonLogprob",
    "CreateTranscriptionResponseJsonUsage",
    "CreateTranscriptionResponseJsonUsageTokens",
    "CreateTranscriptionResponseJsonUsageTokensInputTokenDetails",
    "CreateTranscriptionResponseVerboseJson",
    "CreateTranscriptionResponseVerboseJsonWord",
]


class CreateTranscriptionResponseJsonLogprob(BaseModel):
    token: Optional[str] = None
    """The token in the transcription."""

    bytes: Optional[List[float]] = None
    """The bytes of the token."""

    logprob: Optional[float] = None
    """The log probability of the token."""


class CreateTranscriptionResponseJsonUsageTokensInputTokenDetails(BaseModel):
    audio_tokens: Optional[int] = None
    """Number of audio tokens billed for this request."""

    text_tokens: Optional[int] = None
    """Number of text tokens billed for this request."""


class CreateTranscriptionResponseJsonUsageTokens(BaseModel):
    input_tokens: int
    """Number of input tokens billed for this request."""

    output_tokens: int
    """Number of output tokens generated."""

    total_tokens: int
    """Total number of tokens used (input + output)."""

    type: Literal["tokens"]
    """The type of the usage object. Always `tokens` for this variant."""

    input_token_details: Optional[CreateTranscriptionResponseJsonUsageTokensInputTokenDetails] = None
    """Details about the input tokens billed for this request."""


CreateTranscriptionResponseJsonUsage: TypeAlias = Annotated[
    Union[CreateTranscriptionResponseJsonUsageTokens, TranscriptTextUsageDuration], PropertyInfo(discriminator="type")
]


class CreateTranscriptionResponseJson(BaseModel):
    text: str
    """The transcribed text."""

    logprobs: Optional[List[CreateTranscriptionResponseJsonLogprob]] = None
    """The log probabilities of the tokens in the transcription.

    Only returned with the models `gpt-4o-transcribe` and `gpt-4o-mini-transcribe`
    if `logprobs` is added to the `include` array.
    """

    usage: Optional[CreateTranscriptionResponseJsonUsage] = None
    """Token usage statistics for the request."""


class CreateTranscriptionResponseVerboseJsonWord(BaseModel):
    end: float
    """End time of the word in seconds."""

    start: float
    """Start time of the word in seconds."""

    word: str
    """The text content of the word."""


class CreateTranscriptionResponseVerboseJson(BaseModel):
    duration: float
    """The duration of the input audio."""

    language: str
    """The language of the input audio."""

    text: str
    """The transcribed text."""

    segments: Optional[List[TranscriptionSegment]] = None
    """Segments of the transcribed text and their corresponding details."""

    usage: Optional[TranscriptTextUsageDuration] = None
    """Usage statistics for models billed by audio input duration."""

    words: Optional[List[CreateTranscriptionResponseVerboseJsonWord]] = None
    """Extracted words and their corresponding timestamps."""


AudioCreateTranscriptionResponse: TypeAlias = Union[
    CreateTranscriptionResponseJson, CreateTranscriptionResponseVerboseJson
]
