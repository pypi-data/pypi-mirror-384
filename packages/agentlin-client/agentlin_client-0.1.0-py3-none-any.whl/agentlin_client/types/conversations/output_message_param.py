# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union, Iterable
from typing_extensions import Literal, Required, TypeAlias, TypedDict

from .refusal_content_param import RefusalContentParam
from .output_text_content_param import OutputTextContentParam

__all__ = ["OutputMessageParam", "Content"]

Content: TypeAlias = Union[OutputTextContentParam, RefusalContentParam]


class OutputMessageParam(TypedDict, total=False):
    id: Required[str]
    """The unique ID of the output message."""

    content: Required[Iterable[Content]]
    """The content of the output message."""

    role: Required[Literal["assistant"]]
    """The role of the output message. Always `assistant`."""

    status: Required[Literal["in_progress", "completed", "incomplete"]]
    """The status of the message input.

    One of `in_progress`, `completed`, or `incomplete`. Populated when input items
    are returned via API.
    """

    type: Required[Literal["message"]]
    """The type of the output message. Always `message`."""
