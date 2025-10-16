# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Union
from typing_extensions import Literal, Annotated, TypeAlias

from ..._utils import PropertyInfo
from ..._models import BaseModel
from .input_file_content import InputFileContent
from .input_text_content import InputTextContent
from .input_image_content import InputImageContent

__all__ = ["InputContent", "InputAudio", "InputAudioInputAudio"]


class InputAudioInputAudio(BaseModel):
    data: str
    """Base64-encoded audio data."""

    format: Literal["mp3", "wav"]
    """The format of the audio data. Currently supported formats are `mp3` and `wav`."""


class InputAudio(BaseModel):
    input_audio: InputAudioInputAudio

    type: Literal["input_audio"]
    """The type of the input item. Always `input_audio`."""


InputContent: TypeAlias = Annotated[
    Union[InputTextContent, InputImageContent, InputFileContent, InputAudio], PropertyInfo(discriminator="type")
]
