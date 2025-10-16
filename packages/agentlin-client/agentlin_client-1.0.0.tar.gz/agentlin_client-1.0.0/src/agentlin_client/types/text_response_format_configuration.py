# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias

from pydantic import Field as FieldInfo

from .._utils import PropertyInfo
from .._models import BaseModel

__all__ = ["TextResponseFormatConfiguration", "Text", "JsonSchema", "JsonObject"]


class Text(BaseModel):
    type: Literal["text"]
    """The type of response format being defined. Always `text`."""


class JsonSchema(BaseModel):
    name: str
    """The name of the response format.

    Must be a-z, A-Z, 0-9, or contain underscores and dashes, with a maximum length
    of 64.
    """

    schema_: Dict[str, object] = FieldInfo(alias="schema")
    """
    The schema for the response format, described as a JSON Schema object. Learn how
    to build JSON schemas [here](https://json-schema.org/).
    """

    type: Literal["json_schema"]
    """The type of response format being defined. Always `json_schema`."""

    description: Optional[str] = None
    """
    A description of what the response format is for, used by the model to determine
    how to respond in the format.
    """

    strict: Optional[bool] = None
    """
    Whether to enable strict schema adherence when generating the output. If set to
    true, the model will always follow the exact schema defined in the `schema`
    field. Only a subset of JSON Schema is supported when `strict` is `true`. To
    learn more, read the
    [Structured Outputs guide](https://platform.openai.com/docs/guides/structured-outputs).
    """


class JsonObject(BaseModel):
    type: Literal["json_object"]
    """The type of response format being defined. Always `json_object`."""


TextResponseFormatConfiguration: TypeAlias = Annotated[
    Union[Text, JsonSchema, JsonObject], PropertyInfo(discriminator="type")
]
