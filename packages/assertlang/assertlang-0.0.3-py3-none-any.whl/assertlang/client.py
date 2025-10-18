"""
MCP Client for calling Promptware services over HTTP.

Provides both a reusable client class and a simple function-based API.
"""
from typing import Any, Dict, List, Optional

from .transport import HTTPTransport


class MCPClient:
    """
    MCP client for calling Promptware services.

    Example:
        >>> client = MCPClient("http://localhost:23450")
        >>> result = client.call("user.get@v1", {"user_id": "123"})
        >>> print(result)

    Or use as context manager:
        >>> with MCPClient("http://localhost:23450") as client:
        ...     result = client.call("user.get@v1", {"user_id": "123"})
    """

    def __init__(
        self,
        address: str,
        timeout: float = 30.0,
        retries: int = 3,
        backoff_factor: float = 2.0,
    ):
        """
        Initialize MCP client.

        Args:
            address: Base URL of MCP service (e.g., "http://localhost:23450")
            timeout: Request timeout in seconds
            retries: Number of retry attempts for transient failures
            backoff_factor: Multiplier for exponential backoff
        """
        self.address = address
        self.transport = HTTPTransport(
            base_url=address,
            timeout=timeout,
            retries=retries,
            backoff_factor=backoff_factor,
        )
        self._initialized = False
        self._server_info = None
        self._available_tools = None

    def initialize(self) -> Dict[str, Any]:
        """
        Initialize connection to MCP server.

        Returns server capabilities and information.

        Returns:
            Server info dict with keys: protocolVersion, capabilities, serverInfo

        Raises:
            ConnectionError: Failed to connect
            ProtocolError: Invalid response
        """
        result = self.transport.request("initialize", params={})
        self._initialized = True
        self._server_info = result.get("serverInfo", {})
        return result

    def list_tools(self) -> List[Dict[str, Any]]:
        """
        List all available tools/verbs from the server.

        Returns:
            List of tool definitions with schemas

        Raises:
            ConnectionError: Failed to connect
            ProtocolError: Invalid response
        """
        result = self.transport.request("tools/list", params={})
        tools = result.get("tools", [])
        self._available_tools = {tool["name"]: tool for tool in tools}
        return tools

    def call(
        self,
        verb: str,
        arguments: Dict[str, Any],
        request_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Call an MCP verb/tool.

        Args:
            verb: Verb name (e.g., "user.get@v1")
            arguments: Verb arguments/parameters
            request_id: Optional JSON-RPC request ID

        Returns:
            Result dict containing:
                - input_params: Echo of input parameters
                - tool_results: Results from any tools executed
                - metadata: Execution metadata (mode, timestamp, etc.)
                - ...verb-specific return values...

        Raises:
            InvalidVerbError: Verb doesn't exist
            InvalidParamsError: Invalid parameters
            ConnectionError: Connection failed
            TimeoutError: Request timed out
            MCPError: Other MCP errors
        """
        params = {
            "name": verb,
            "arguments": arguments,
        }

        result = self.transport.request(
            "tools/call",
            params=params,
            request_id=request_id or 1,
        )

        return result

    def get_server_info(self) -> Optional[Dict[str, Any]]:
        """
        Get cached server info (from initialize call).

        Returns None if initialize() hasn't been called yet.
        """
        return self._server_info

    def get_tool_schema(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        Get schema for a specific tool.

        Returns None if tool doesn't exist or list_tools() hasn't been called.
        """
        if not self._available_tools:
            return None
        return self._available_tools.get(tool_name)

    def close(self):
        """Close the client connection."""
        self.transport.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


def call_verb(
    service: str,
    verb: str,
    params: Dict[str, Any],
    address: Optional[str] = None,
    timeout: float = 30.0,
    retries: int = 3,
) -> Dict[str, Any]:
    """
    Simple function to call an MCP verb.

    Convenience wrapper that creates a client, calls the verb, and cleans up.

    Args:
        service: Service name (for documentation, not used in URL)
        verb: Verb name (e.g., "user.get@v1")
        params: Verb parameters
        address: Service address (e.g., "http://localhost:23450")
                 If None, defaults to http://localhost:23450
        timeout: Request timeout in seconds
        retries: Number of retry attempts

    Returns:
        Result dict from verb execution

    Example:
        >>> result = call_verb(
        ...     service="user-service",
        ...     verb="user.get@v1",
        ...     params={"user_id": "123"},
        ...     address="http://localhost:23450"
        ... )
        >>> print(result['metadata']['mode'])
        'ide_integrated'

    Raises:
        InvalidVerbError: Verb doesn't exist
        InvalidParamsError: Invalid parameters
        ConnectionError: Connection failed
        TimeoutError: Request timed out
        MCPError: Other MCP errors
    """
    # Default address if not provided
    if address is None:
        address = "http://localhost:23450"

    with MCPClient(address, timeout=timeout, retries=retries) as client:
        return client.call(verb, params)
