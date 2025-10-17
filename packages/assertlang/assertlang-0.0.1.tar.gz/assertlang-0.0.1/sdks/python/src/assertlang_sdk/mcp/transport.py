"""HTTP/WebSocket transport for MCP verbs."""

import json
from typing import Any

try:
    import requests
except ImportError:
    requests = None  # type: ignore

from ..errors import E_JSON, E_RUNTIME, CompatibilityError, PromptwareError
from ..types import MCPEnvelope
from ..version import __daemon_min_version__, __version__


class Transport:
    """HTTP transport for MCP verb calls."""

    def __init__(self, daemon_url: str):
        """Initialize transport.

        Args:
            daemon_url: Base URL of Promptware daemon
        """
        if requests is None:
            raise ImportError(
                "requests library required for HTTP transport. "
                "Install with: pip install requests"
            )

        self.daemon_url = daemon_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update(
            {"Content-Type": "application/json", "User-Agent": f"promptware-sdk/{__version__}"}
        )

        # Verify daemon compatibility on first connection
        self._check_compatibility()

    def call_verb(self, verb: str, payload: dict[str, Any]) -> MCPEnvelope:
        """Call MCP verb via HTTP POST.

        Args:
            verb: Verb name (e.g., 'plan.create@v1')
            payload: Request payload

        Returns:
            MCP response envelope

        Raises:
            PromptwareError: If HTTP request fails or response invalid
        """
        url = f"{self.daemon_url}/mcp/{verb}"

        try:
            response = self.session.post(url, json=payload, timeout=60)
            response.raise_for_status()
        except requests.RequestException as e:
            raise PromptwareError(E_RUNTIME, f"HTTP request failed: {e}") from e

        try:
            envelope: MCPEnvelope = response.json()
        except json.JSONDecodeError as e:
            raise PromptwareError(E_JSON, f"Invalid JSON response: {e}") from e

        # Validate envelope structure
        if not isinstance(envelope, dict):
            raise PromptwareError(E_JSON, "Response envelope must be dict")
        if "ok" not in envelope or "version" not in envelope:
            raise PromptwareError(E_JSON, "Response envelope missing 'ok' or 'version' field")

        return envelope

    def _check_compatibility(self) -> None:
        """Check daemon version compatibility.

        Raises:
            CompatibilityError: If daemon version too old
        """
        try:
            # Call health check or version endpoint
            response = self.session.get(f"{self.daemon_url}/health", timeout=5)
            response.raise_for_status()
            data = response.json()
            daemon_version = data.get("version", "0.0.0")

            # Simple version comparison (assumes semver)
            if self._compare_versions(daemon_version, __daemon_min_version__) < 0:
                raise CompatibilityError(__version__, daemon_version, __daemon_min_version__)

        except requests.RequestException:
            # Daemon not reachable, will fail on first verb call
            pass

    @staticmethod
    def _compare_versions(v1: str, v2: str) -> int:
        """Compare semantic versions.

        Args:
            v1: First version string
            v2: Second version string

        Returns:
            -1 if v1 < v2, 0 if equal, 1 if v1 > v2
        """
        parts1 = [int(p) for p in v1.split(".")]
        parts2 = [int(p) for p in v2.split(".")]

        for p1, p2 in zip(parts1, parts2):
            if p1 < p2:
                return -1
            if p1 > p2:
                return 1

        return 0