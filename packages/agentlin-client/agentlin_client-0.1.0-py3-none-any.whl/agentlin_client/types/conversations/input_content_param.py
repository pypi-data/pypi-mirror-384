# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union
from typing_extensions import Literal, Required, TypeAlias, TypedDict

from .input_file_content_param import InputFileContentParam
from .input_text_content_param import InputTextContentParam
from .input_image_content_param import InputImageContentParam

__all__ = ["InputContentParam", "InputAudio", "InputAudioInputAudio"]


class InputAudioInputAudio(TypedDict, total=False):
    data: Required[str]
    """Base64-encoded audio data."""

    format: Required[Literal["mp3", "wav"]]
    """The format of the audio data. Currently supported formats are `mp3` and `wav`."""


class InputAudio(TypedDict, total=False):
    input_audio: Required[InputAudioInputAudio]

    type: Required[Literal["input_audio"]]
    """The type of the input item. Always `input_audio`."""


InputContentParam: TypeAlias = Union[InputTextContentParam, InputImageContentParam, InputFileContentParam, InputAudio]
