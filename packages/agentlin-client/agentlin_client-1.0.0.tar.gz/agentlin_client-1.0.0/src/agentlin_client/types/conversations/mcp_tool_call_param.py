# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import Literal, Required, TypedDict

__all__ = ["McpToolCallParam"]


class McpToolCallParam(TypedDict, total=False):
    id: Required[str]
    """The unique ID of the tool call."""

    arguments: Required[str]
    """A JSON string of the arguments passed to the tool."""

    name: Required[str]
    """The name of the tool that was run."""

    server_label: Required[str]
    """The label of the MCP server running the tool."""

    type: Required[Literal["mcp_call"]]
    """The type of the item. Always `mcp_call`."""

    approval_request_id: Optional[str]
    """
    Unique identifier for the MCP tool call approval request. Include this value in
    a subsequent `mcp_approval_response` input to approve or reject the
    corresponding tool call.
    """

    error: Optional[str]
    """The error from the tool call, if any."""

    output: Optional[str]
    """The output from the tool call."""

    status: Literal["in_progress", "completed", "incomplete", "calling", "failed"]
    """The status of the tool call.

    One of `in_progress`, `completed`, `incomplete`, `calling`, or `failed`.
    """
