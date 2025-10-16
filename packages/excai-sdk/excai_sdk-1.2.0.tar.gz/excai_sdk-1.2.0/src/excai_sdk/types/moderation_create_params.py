# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union, Iterable
from typing_extensions import Literal, Required, TypeAlias, TypedDict

from .._types import SequenceNotStr

__all__ = [
    "ModerationCreateParams",
    "InputModerationMultiModalArray",
    "InputModerationMultiModalArrayImageURL",
    "InputModerationMultiModalArrayImageURLImageURL",
    "InputModerationMultiModalArrayText",
]


class ModerationCreateParams(TypedDict, total=False):
    input: Required[Union[str, SequenceNotStr[str], Iterable[InputModerationMultiModalArray]]]
    """Input (or inputs) to classify.

    Can be a single string, an array of strings, or an array of multi-modal input
    objects similar to other models.
    """

    model: Union[
        str,
        Literal[
            "omni-moderation-latest", "omni-moderation-2024-09-26", "text-moderation-latest", "text-moderation-stable"
        ],
    ]
    """The content moderation model you would like to use.

    Learn more in
    [the moderation guide](https://main.excai.ai/docs/guides/moderation), and learn
    about available models [here](https://main.excai.ai/docs/models#moderation).
    """


class InputModerationMultiModalArrayImageURLImageURL(TypedDict, total=False):
    url: Required[str]
    """Either a URL of the image or the base64 encoded image data."""


class InputModerationMultiModalArrayImageURL(TypedDict, total=False):
    image_url: Required[InputModerationMultiModalArrayImageURLImageURL]
    """Contains either an image URL or a data URL for a base64 encoded image."""

    type: Required[Literal["image_url"]]
    """Always `image_url`."""


class InputModerationMultiModalArrayText(TypedDict, total=False):
    text: Required[str]
    """A string of text to classify."""

    type: Required[Literal["text"]]
    """Always `text`."""


InputModerationMultiModalArray: TypeAlias = Union[
    InputModerationMultiModalArrayImageURL, InputModerationMultiModalArrayText
]
