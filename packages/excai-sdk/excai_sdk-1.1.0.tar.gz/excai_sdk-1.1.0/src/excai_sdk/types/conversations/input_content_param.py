# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union
from typing_extensions import TypeAlias

from .input_audio_param import InputAudioParam
from .input_file_content_param import InputFileContentParam
from .input_text_content_param import InputTextContentParam
from .input_image_content_param import InputImageContentParam

__all__ = ["InputContentParam"]

InputContentParam: TypeAlias = Union[
    InputTextContentParam, InputImageContentParam, InputFileContentParam, InputAudioParam
]
