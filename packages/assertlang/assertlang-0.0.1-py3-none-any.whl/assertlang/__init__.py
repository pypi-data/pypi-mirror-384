"""
AssertLang Python Client Library

Provides MCP client for calling AssertLang services over HTTP.
"""

from .client import MCPClient, call_verb
from .exceptions import (
    ConnectionError,
    InvalidParamsError,
    InvalidVerbError,
    MCPError,
    ProtocolError,
    ServiceUnavailableError,
    TimeoutError,
)

__version__ = "0.0.1"

__all__ = [
    "MCPClient",
    "call_verb",
    "MCPError",
    "ConnectionError",
    "TimeoutError",
    "ServiceUnavailableError",
    "InvalidVerbError",
    "InvalidParamsError",
    "ProtocolError",
]
