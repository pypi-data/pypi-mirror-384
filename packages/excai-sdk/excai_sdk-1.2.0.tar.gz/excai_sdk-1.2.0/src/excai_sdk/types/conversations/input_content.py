# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Union
from typing_extensions import Annotated, TypeAlias

from ..._utils import PropertyInfo
from .input_audio import InputAudio
from .input_file_content import InputFileContent
from .input_text_content import InputTextContent
from .input_image_content import InputImageContent

__all__ = ["InputContent"]

InputContent: TypeAlias = Annotated[
    Union[InputTextContent, InputImageContent, InputFileContent, InputAudio], PropertyInfo(discriminator="type")
]
