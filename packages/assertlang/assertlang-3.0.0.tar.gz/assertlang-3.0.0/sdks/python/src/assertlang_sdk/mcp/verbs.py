"""MCP verb implementations."""

from typing import Any, Literal

from ..errors import E_JSON, E_RUNTIME, PromptwareError
from ..types import MCPEnvelope
from .transport import Transport


class MCP:
    """MCP verb wrapper for Promptware daemon integration."""

    def __init__(self, daemon_url: str = "http://localhost:8765"):
        """Initialize MCP client.

        Args:
            daemon_url: URL of Promptware daemon (default: http://localhost:8765)
        """
        self.transport = Transport(daemon_url)

    def plan_create_v1(
        self, source: str, format: Literal["dsl", "natural"] = "dsl"
    ) -> dict[str, Any]:
        """Create execution plan from DSL or natural language.

        Args:
            source: Plan source (DSL code or natural language prompt)
            format: Source format ('dsl' or 'natural')

        Returns:
            Parsed plan AST

        Raises:
            PromptwareError: If plan creation fails
        """
        payload = {"source": source, "format": format}
        response = self.transport.call_verb("plan.create@v1", payload)
        return self._unwrap(response)

    def run_start_v1(self, plan: dict[str, Any], state: dict[str, Any] | None = None) -> str:
        """Start plan execution.

        Args:
            plan: Parsed plan AST (from plan_create_v1)
            state: Initial state variables (optional)

        Returns:
            run_id for tracking execution

        Raises:
            PromptwareError: If execution fails to start
        """
        payload = {"plan": plan, "state": state or {}}
        response = self.transport.call_verb("run.start@v1", payload)
        data = self._unwrap(response)
        return data["run_id"]

    def httpcheck_assert_v1(
        self, url: str, status_code: int = 200, timeout_sec: int = 10
    ) -> dict[str, Any]:
        """Assert HTTP endpoint health.

        Args:
            url: URL to check
            status_code: Expected HTTP status code (default: 200)
            timeout_sec: Request timeout in seconds (default: 10)

        Returns:
            Check result with actual_status_code and success flag

        Raises:
            PromptwareError: If HTTP check fails or times out
        """
        payload = {"url": url, "status_code": status_code, "timeout_sec": timeout_sec}
        response = self.transport.call_verb("httpcheck.assert@v1", payload)
        return self._unwrap(response)

    def report_finish_v1(
        self, run_id: str, status: Literal["success", "failure", "timeout"]
    ) -> dict[str, Any]:
        """Mark run as complete.

        Args:
            run_id: Execution run ID (from run_start_v1)
            status: Final execution status

        Returns:
            Completion metadata

        Raises:
            PromptwareError: If report fails
        """
        payload = {"run_id": run_id, "status": status}
        response = self.transport.call_verb("report.finish@v1", payload)
        return self._unwrap(response)

    def _unwrap(self, envelope: MCPEnvelope) -> dict[str, Any]:
        """Unwrap MCP envelope, raising exception on error.

        Args:
            envelope: MCP response envelope

        Returns:
            Response data payload

        Raises:
            PromptwareError: If envelope contains error
        """
        if not envelope["ok"]:
            error = envelope.get("error", {})
            code = error.get("code", E_RUNTIME)
            message = error.get("message", "Unknown error")
            raise PromptwareError(code, message)

        data = envelope.get("data")
        if data is None:
            raise PromptwareError(E_JSON, "Response envelope missing 'data' field")

        return data