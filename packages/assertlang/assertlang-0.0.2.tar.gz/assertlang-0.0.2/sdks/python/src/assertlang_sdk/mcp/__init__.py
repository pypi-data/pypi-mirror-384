"""MCP verb wrappers for Promptware SDK."""

from .verbs import MCP

# Singleton instance
mcp = MCP()

__all__ = ["mcp", "MCP"]