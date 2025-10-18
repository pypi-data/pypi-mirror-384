"""
Exception classes for Promptware MCP client.
"""


class MCPError(Exception):
    """Base exception for all MCP client errors."""

    def __init__(self, message: str, code: int = None):
        super().__init__(message)
        self.message = message
        self.code = code


class ConnectionError(MCPError):
    """Failed to connect to MCP service."""
    pass


class TimeoutError(MCPError):
    """Request timed out."""
    pass


class ServiceUnavailableError(MCPError):
    """Service is unavailable or not responding."""
    pass


class InvalidVerbError(MCPError):
    """Requested verb does not exist."""

    def __init__(self, verb: str, message: str = None):
        self.verb = verb
        super().__init__(message or f"Verb not found: {verb}", code=-32601)


class InvalidParamsError(MCPError):
    """Invalid parameters provided."""

    def __init__(self, message: str, validation_errors: dict = None):
        super().__init__(message, code=-32602)
        self.validation_errors = validation_errors or {}


class ProtocolError(MCPError):
    """MCP protocol violation or unexpected response format."""
    pass
