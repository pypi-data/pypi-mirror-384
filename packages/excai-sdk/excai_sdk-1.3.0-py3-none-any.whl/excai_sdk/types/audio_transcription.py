# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from typing_extensions import Literal

from .._models import BaseModel

__all__ = ["AudioTranscription"]


class AudioTranscription(BaseModel):
    language: Optional[str] = None
    """The language of the input audio.

    Supplying the input language in
    [ISO-639-1](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes) (e.g. `en`)
    format will improve accuracy and latency.
    """

    model: Optional[Literal["whisper-1", "openai/gpt-oss-120b-transcribe-latest", "openai/gpt-oss-120b-transcribe"]] = (
        None
    )
    """The model to use for transcription.

    Current options are `whisper-1`, `openai/gpt-oss-120b-transcribe-latest`,
    `openai/gpt-oss-120b-transcribe`, and `openai/gpt-oss-120b-transcribe`.
    """

    prompt: Optional[str] = None
    """
    An optional text to guide the model's style or continue a previous audio
    segment. For `whisper-1`, the
    [prompt is a list of keywords](https://main.excai.ai/docs/guides/speech-to-text#prompting).
    For `openai/gpt-oss-120b-transcribe` models, the prompt is a free text string,
    for example "expect words related to technology".
    """
