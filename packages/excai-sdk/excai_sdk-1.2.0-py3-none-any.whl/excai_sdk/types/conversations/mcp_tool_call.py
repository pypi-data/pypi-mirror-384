# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from typing_extensions import Literal

from ..._models import BaseModel

__all__ = ["McpToolCall"]


class McpToolCall(BaseModel):
    id: str
    """The unique ID of the tool call."""

    arguments: str
    """A JSON string of the arguments passed to the tool."""

    name: str
    """The name of the tool that was run."""

    server_label: str
    """The label of the MCP server running the tool."""

    type: Literal["mcp_call"]
    """The type of the item. Always `mcp_call`."""

    approval_request_id: Optional[str] = None
    """
    Unique identifier for the MCP tool call approval request. Include this value in
    a subsequent `mcp_approval_response` input to approve or reject the
    corresponding tool call.
    """

    error: Optional[str] = None
    """The error from the tool call, if any."""

    output: Optional[str] = None
    """The output from the tool call."""

    status: Optional[Literal["in_progress", "completed", "incomplete", "calling", "failed"]] = None
    """The status of the tool call.

    One of `in_progress`, `completed`, `incomplete`, `calling`, or `failed`.
    """
