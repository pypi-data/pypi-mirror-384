"""Promptware SDK - Host integration for Promptware daemon."""

from .errors import (
    E_BUILD,
    E_COMPAT,
    E_FS,
    E_JSON,
    E_METHOD,
    E_POLICY,
    E_RUNTIME,
    E_TIMEOUT,
    CompatibilityError,
    PromptwareError,
)
from .mcp import MCP, mcp
from .timeline import TimelineReader
from .types import MCPEnvelope, TimelineEvent, ToolRequest, ToolResponse
from .version import __version__

__all__ = [
    # MCP verbs
    "mcp",
    "MCP",
    # Timeline
    "TimelineReader",
    # Errors
    "PromptwareError",
    "CompatibilityError",
    "E_RUNTIME",
    "E_POLICY",
    "E_TIMEOUT",
    "E_BUILD",
    "E_JSON",
    "E_FS",
    "E_METHOD",
    "E_COMPAT",
    # Types
    "ToolRequest",
    "ToolResponse",
    "TimelineEvent",
    "MCPEnvelope",
    # Version
    "__version__",
]