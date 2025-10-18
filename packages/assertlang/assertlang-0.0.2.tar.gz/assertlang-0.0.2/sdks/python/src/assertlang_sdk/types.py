"""Promptware SDK type definitions."""

from typing import Any, Literal, TypedDict


class ToolRequest(TypedDict, total=False):
    """Tool invocation request."""

    tool_id: str
    params: dict[str, Any]


class ToolResponse(TypedDict):
    """Tool invocation response."""

    ok: bool
    version: Literal["v1"]
    data: dict[str, Any] | None
    error: dict[str, str] | None


class TimelineEvent(TypedDict, total=False):
    """Timeline event from interpreter execution."""

    phase: Literal["call", "let", "if", "parallel", "fanout", "merge", "state"]
    action: str
    status: Literal["ok", "error"]
    duration_ms: float
    # Phase-specific fields
    alias: str  # call
    result_alias: str  # call
    attempt: int  # call
    target: str  # let, merge
    condition: str  # if
    branch: Literal["then", "else"]  # if
    branches: list[str]  # parallel, fanout
    cases: list[dict[str, str]]  # fanout
    mode: Literal["dict", "append", "collect"] | None  # merge
    append_key: str  # merge
    sources: list[dict[str, str]]  # merge
    name: str  # state
    error: str  # error status
    code: str  # error status


class MCPEnvelope(TypedDict):
    """MCP request/response envelope."""

    ok: bool
    version: Literal["v1"]
    data: dict[str, Any] | None
    error: dict[str, str] | None