"""Timeline event reader for streaming execution events."""

import time
from typing import Iterator, Literal

try:
    import requests
except ImportError:
    requests = None  # type: ignore

from ..errors import E_RUNTIME, E_TIMEOUT, PromptwareError
from ..types import TimelineEvent


class TimelineReader:
    """Stream timeline events from a running execution."""

    def __init__(self, run_id: str, daemon_url: str = "http://localhost:8765"):
        """Initialize timeline reader.

        Args:
            run_id: Execution run ID (from mcp.run_start_v1)
            daemon_url: URL of Promptware daemon
        """
        if requests is None:
            raise ImportError(
                "requests library required for timeline reading. "
                "Install with: pip install requests"
            )

        self.run_id = run_id
        self.daemon_url = daemon_url.rstrip("/")
        self.session = requests.Session()

    def events(self, poll_interval: float = 0.5) -> Iterator[TimelineEvent]:
        """Stream timeline events for this run.

        Args:
            poll_interval: Seconds between polls (default: 0.5)

        Yields:
            Timeline events as they become available

        Raises:
            PromptwareError: If event streaming fails
        """
        url = f"{self.daemon_url}/timeline/{self.run_id}"
        last_event_id = 0

        while True:
            try:
                response = self.session.get(
                    url, params={"since": last_event_id}, timeout=10
                )
                response.raise_for_status()
                data = response.json()

                events = data.get("events", [])
                for event in events:
                    yield event
                    last_event_id = event.get("id", last_event_id + 1)

                # Check if run complete
                if data.get("complete", False):
                    break

                time.sleep(poll_interval)

            except requests.RequestException as e:
                raise PromptwareError(E_RUNTIME, f"Failed to fetch timeline events: {e}") from e

    def wait_for_completion(self, timeout: int = 60) -> Literal["success", "failure", "timeout"]:
        """Block until run completes.

        Args:
            timeout: Maximum wait time in seconds (default: 60)

        Returns:
            Final run status

        Raises:
            PromptwareError: If wait times out or status fetch fails
        """
        url = f"{self.daemon_url}/run/{self.run_id}/status"
        start_time = time.time()

        while True:
            if time.time() - start_time > timeout:
                raise PromptwareError(E_TIMEOUT, f"Run {self.run_id} did not complete within {timeout}s")

            try:
                response = self.session.get(url, timeout=5)
                response.raise_for_status()
                data = response.json()

                status = data.get("status")
                if status in ("success", "failure", "timeout"):
                    return status  # type: ignore

                time.sleep(1.0)

            except requests.RequestException as e:
                raise PromptwareError(E_RUNTIME, f"Failed to fetch run status: {e}") from e

    def filter_by_phase(
        self, phase: Literal["call", "let", "if", "parallel", "fanout", "merge", "state"]
    ) -> list[TimelineEvent]:
        """Get all events matching a specific phase.

        Args:
            phase: Phase to filter by

        Returns:
            List of matching events

        Raises:
            PromptwareError: If event fetch fails
        """
        url = f"{self.daemon_url}/timeline/{self.run_id}"

        try:
            response = self.session.get(url, params={"phase": phase}, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data.get("events", [])

        except requests.RequestException as e:
            raise PromptwareError(E_RUNTIME, f"Failed to filter timeline events: {e}") from e