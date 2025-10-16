# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from typing_extensions import Literal

from ..._models import BaseModel

__all__ = ["FileSearchToolCall", "Result"]


class Result(BaseModel):
    file_id: Optional[str] = None
    """The unique ID of the file."""

    filename: Optional[str] = None
    """The name of the file."""

    score: Optional[float] = None
    """The relevance score of the file - a value between 0 and 1."""

    text: Optional[str] = None
    """The text that was retrieved from the file."""


class FileSearchToolCall(BaseModel):
    id: str
    """The unique ID of the file search tool call."""

    queries: List[str]
    """The queries used to search for files."""

    status: Literal["in_progress", "searching", "completed", "incomplete", "failed"]
    """The status of the file search tool call.

    One of `in_progress`, `searching`, `incomplete` or `failed`,
    """

    type: Literal["file_search_call"]
    """The type of the file search tool call. Always `file_search_call`."""

    results: Optional[List[Result]] = None
    """The results of the file search tool call."""
