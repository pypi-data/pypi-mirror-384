"""
MCP Client Library for Promptware agents.

Enables agents to call MCP verbs on other agents.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

import requests


@dataclass
class MCPResponse:
    """Response from an MCP verb call."""
    ok: bool
    version: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, str]] = None

    def is_success(self) -> bool:
        """Check if the call was successful."""
        return self.ok and self.error is None

    def get_data(self) -> Dict[str, Any]:
        """Get response data, raising if call failed."""
        if not self.is_success():
            error_msg = self.error.get("message", "Unknown error") if self.error else "Call failed"
            error_code = self.error.get("code", "E_UNKNOWN") if self.error else "E_UNKNOWN"
            raise MCPError(error_code, error_msg)
        return self.data or {}


class MCPError(Exception):
    """Exception raised when MCP call fails."""
    def __init__(self, code: str, message: str):
        super().__init__(f"[{code}] {message}")
        self.code = code
        self.message = message


class MCPClient:
    """
    Client for calling MCP verbs on agents.

    Example:
        client = MCPClient("http://localhost:23456")
        response = client.call("review.submit@v1", {"pr_url": "https://..."})
        review_id = response.get_data()["review_id"]
    """

    def __init__(
        self,
        base_url: str,
        timeout: int = 30,
        retries: int = 3
    ):
        """
        Initialize MCP client.

        Args:
            base_url: Base URL of the agent (e.g., "http://localhost:23456")
            timeout: Request timeout in seconds
            retries: Number of retries on failure
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.retries = retries
        self.session = requests.Session()

    def call(
        self,
        method: str,
        params: Optional[Dict[str, Any]] = None
    ) -> MCPResponse:
        """
        Call an MCP verb on the agent.

        Args:
            method: MCP verb name (e.g., "task.execute@v1")
            params: Parameters to pass to the verb

        Returns:
            MCPResponse with success/error information

        Raises:
            MCPError: If call fails after retries
            requests.RequestException: If network error occurs
        """
        url = f"{self.base_url}/mcp"
        payload = {
            "method": method,
            "params": params or {}
        }

        last_error = None
        for attempt in range(self.retries):
            try:
                response = self.session.post(
                    url,
                    json=payload,
                    timeout=self.timeout,
                    headers={"Content-Type": "application/json"}
                )

                # Parse response
                if response.status_code == 200:
                    data = response.json()
                    return MCPResponse(
                        ok=data.get("ok", False),
                        version=data.get("version", "v1"),
                        data=data.get("data"),
                        error=data.get("error")
                    )
                else:
                    # Non-200 response
                    try:
                        error_data = response.json()
                        return MCPResponse(
                            ok=False,
                            version="v1",
                            error=error_data.get("error", {
                                "code": "E_HTTP",
                                "message": f"HTTP {response.status_code}"
                            })
                        )
                    except:
                        return MCPResponse(
                            ok=False,
                            version="v1",
                            error={
                                "code": "E_HTTP",
                                "message": f"HTTP {response.status_code}: {response.text}"
                            }
                        )

            except requests.Timeout:
                last_error = MCPError("E_TIMEOUT", f"Request timed out after {self.timeout}s")
            except requests.ConnectionError as e:
                last_error = MCPError("E_CONNECTION", f"Connection failed: {str(e)}")
            except requests.RequestException as e:
                last_error = MCPError("E_NETWORK", f"Network error: {str(e)}")

            # Don't retry on success or if last attempt
            if attempt < self.retries - 1:
                continue

        # All retries failed
        if last_error:
            raise last_error
        else:
            raise MCPError("E_UNKNOWN", "Call failed for unknown reason")

    def health_check(self) -> Dict[str, Any]:
        """
        Check if the agent is healthy.

        Returns:
            Health status dictionary
        """
        url = f"{self.base_url}/health"
        response = self.session.get(url, timeout=5)
        response.raise_for_status()
        return response.json()

    def list_verbs(self) -> Dict[str, Any]:
        """
        List all verbs exposed by the agent.

        Returns:
            Dictionary with agent name and list of verbs
        """
        url = f"{self.base_url}/verbs"
        response = self.session.get(url, timeout=5)
        response.raise_for_status()
        return response.json()

    def close(self):
        """Close the client session."""
        self.session.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


class AgentRegistry:
    """
    Simple registry for discovering agents.

    For now, this is just a hardcoded mapping.
    In Wave 4, this will be a real service discovery system.
    """

    def __init__(self):
        self._agents: Dict[str, str] = {}

    def register(self, agent_name: str, base_url: str):
        """Register an agent."""
        self._agents[agent_name] = base_url

    def discover(self, agent_name: str) -> Optional[str]:
        """Find an agent's base URL."""
        return self._agents.get(agent_name)

    def get_client(self, agent_name: str) -> MCPClient:
        """Get MCP client for an agent."""
        url = self.discover(agent_name)
        if not url:
            raise MCPError("E_DISCOVERY", f"Agent not found: {agent_name}")
        return MCPClient(url)

    def list_agents(self) -> list[str]:
        """List all registered agents."""
        return list(self._agents.keys())


# Global registry instance (for simple usage)
_global_registry = AgentRegistry()


def register_agent(agent_name: str, base_url: str):
    """Register an agent globally."""
    _global_registry.register(agent_name, base_url)


def get_agent_client(agent_name: str) -> MCPClient:
    """Get client for a registered agent."""
    return _global_registry.get_client(agent_name)


def call_agent(agent_name: str, method: str, params: Optional[Dict[str, Any]] = None) -> MCPResponse:
    """
    Convenience function to call an agent verb.

    Example:
        register_agent("code-reviewer", "http://localhost:23456")
        response = call_agent("code-reviewer", "review.submit@v1", {"pr_url": "..."})
    """
    client = get_agent_client(agent_name)
    return client.call(method, params)