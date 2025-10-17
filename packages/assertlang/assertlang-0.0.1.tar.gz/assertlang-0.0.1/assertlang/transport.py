"""
HTTP transport layer for MCP client.

Handles low-level HTTP communication with retry logic and timeouts.
"""
import time
from typing import Any, Dict, Optional

import requests

from .exceptions import (
    ConnectionError,
    ProtocolError,
    ServiceUnavailableError,
    TimeoutError,
)


class HTTPTransport:
    """HTTP transport for MCP JSON-RPC protocol."""

    def __init__(
        self,
        base_url: str,
        timeout: float = 30.0,
        retries: int = 3,
        backoff_factor: float = 2.0,
        initial_delay: float = 1.0,
    ):
        """
        Initialize HTTP transport.

        Args:
            base_url: Base URL of MCP service (e.g., "http://localhost:23450")
            timeout: Request timeout in seconds
            retries: Number of retry attempts for transient failures
            backoff_factor: Multiplier for exponential backoff (delay *= factor)
            initial_delay: Initial delay in seconds before first retry
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.retries = retries
        self.backoff_factor = backoff_factor
        self.initial_delay = initial_delay
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        })

    def request(
        self,
        method: str,
        params: Optional[Dict[str, Any]] = None,
        request_id: int = 1,
    ) -> Dict[str, Any]:
        """
        Send JSON-RPC request with retry logic.

        Args:
            method: JSON-RPC method name
            params: Method parameters
            request_id: JSON-RPC request ID

        Returns:
            Response data (result field from JSON-RPC response)

        Raises:
            ConnectionError: Failed to connect after retries
            TimeoutError: Request timed out
            ServiceUnavailableError: Server returned 5xx error
            ProtocolError: Invalid JSON-RPC response
        """
        payload = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params or {}
        }

        last_exception = None
        delay = self.initial_delay

        for attempt in range(self.retries):
            try:
                response = self.session.post(
                    f"{self.base_url}/mcp",
                    json=payload,
                    timeout=self.timeout,
                )

                # Check HTTP status
                if response.status_code >= 500:
                    # 5xx errors are retriable
                    last_exception = ServiceUnavailableError(
                        f"Service returned {response.status_code}: {response.text}"
                    )
                    if attempt < self.retries - 1:
                        time.sleep(delay)
                        delay *= self.backoff_factor
                        continue
                    raise last_exception

                # Parse JSON-RPC response
                try:
                    data = response.json()
                except ValueError as e:
                    raise ProtocolError(f"Invalid JSON response: {e}")

                # Validate JSON-RPC structure
                if "jsonrpc" not in data or data["jsonrpc"] != "2.0":
                    raise ProtocolError("Invalid JSON-RPC response: missing jsonrpc field")

                if "id" not in data or data["id"] != request_id:
                    raise ProtocolError("Invalid JSON-RPC response: ID mismatch")

                # Check for JSON-RPC error
                if "error" in data:
                    error = data["error"]
                    code = error.get("code", -32000)
                    message = error.get("message", "Unknown error")

                    # These are not retriable (client errors)
                    from .exceptions import InvalidParamsError, InvalidVerbError, MCPError

                    if code == -32601:
                        raise InvalidVerbError(params.get("name", "unknown"), message)
                    elif code == -32602:
                        raise InvalidParamsError(message)
                    else:
                        raise MCPError(message, code=code)

                # Return result
                if "result" not in data:
                    raise ProtocolError("Invalid JSON-RPC response: missing result field")

                return data["result"]

            except requests.exceptions.Timeout:
                last_exception = TimeoutError(f"Request timed out after {self.timeout}s")
                if attempt < self.retries - 1:
                    time.sleep(delay)
                    delay *= self.backoff_factor
                    continue
                raise last_exception

            except requests.exceptions.ConnectionError as e:
                last_exception = ConnectionError(f"Failed to connect to {self.base_url}: {e}")
                if attempt < self.retries - 1:
                    time.sleep(delay)
                    delay *= self.backoff_factor
                    continue
                raise last_exception

            except (ConnectionError, TimeoutError, ServiceUnavailableError):
                # Re-raise our own exceptions (already wrapped)
                if attempt < self.retries - 1:
                    time.sleep(delay)
                    delay *= self.backoff_factor
                    continue
                raise

        # Should never reach here, but just in case
        if last_exception:
            raise last_exception
        raise ConnectionError("All retry attempts failed")

    def close(self):
        """Close the HTTP session."""
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
