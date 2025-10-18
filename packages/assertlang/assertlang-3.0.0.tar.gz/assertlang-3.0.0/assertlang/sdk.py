"""
Promptware SDK - Production-ready client library for MCP agents.

Features:
- Dynamic verb discovery with autocomplete
- Automatic retries with exponential backoff
- Connection pooling
- Circuit breaker pattern
- Timeout handling
- Type hints
- Request/response logging
"""

import logging
import time
from dataclasses import dataclass
from enum import Enum
from threading import Lock
from typing import Any, Callable, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class AgentConfig:
    """Configuration for agent client."""
    base_url: str
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    retry_backoff: float = 2.0
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: int = 60
    connection_pool_size: int = 10
    enable_logging: bool = False


class CircuitBreaker:
    """Circuit breaker for fault tolerance."""

    def __init__(self, threshold: int = 5, timeout: int = 60):
        self.threshold = threshold
        self.timeout = timeout
        self.failures = 0
        self.last_failure_time = 0
        self.state = CircuitState.CLOSED
        self._lock = Lock()

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection."""
        with self._lock:
            if self.state == CircuitState.OPEN:
                if time.time() - self.last_failure_time >= self.timeout:
                    self.state = CircuitState.HALF_OPEN
                    logger.info("Circuit breaker entering HALF_OPEN state")
                else:
                    raise CircuitBreakerError("Circuit breaker is OPEN")

        try:
            result = func(*args, **kwargs)

            with self._lock:
                if self.state == CircuitState.HALF_OPEN:
                    self.state = CircuitState.CLOSED
                    self.failures = 0
                    logger.info("Circuit breaker CLOSED - service recovered")

            return result

        except Exception:
            with self._lock:
                self.failures += 1
                self.last_failure_time = time.time()

                if self.failures >= self.threshold:
                    self.state = CircuitState.OPEN
                    logger.error(
                        f"Circuit breaker OPEN after {self.failures} failures")

            raise


class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open."""
    pass


class AgentError(Exception):
    """Base exception for agent errors."""
    pass


class ConnectionError(AgentError):
    """Connection to agent failed."""
    pass


class TimeoutError(AgentError):
    """Request timed out."""
    pass


class VerbNotFoundError(AgentError):
    """Verb does not exist."""
    pass


class InvalidParamsError(AgentError):
    """Invalid parameters provided."""
    pass


class VerbProxy:
    """Dynamic proxy for verb calls with dot notation."""

    def __init__(self, client: 'Agent', verb_path: str = ""):
        self._client = client
        self._verb_path = verb_path

    def __getattr__(self, name: str) -> 'VerbProxy':
        """Build verb path dynamically."""
        new_path = f"{self._verb_path}.{name}" if self._verb_path else name
        return VerbProxy(self._client, new_path)

    def __call__(self, **kwargs) -> Any:
        """Execute verb call."""
        # Assume v1 by default
        verb_name = f"{self._verb_path}@v1"
        return self._client.call_verb(verb_name, kwargs)


class Agent:
    """
    Production-ready MCP agent client.

    Features:
    - Dynamic verb discovery
    - Automatic retries with exponential backoff
    - Circuit breaker pattern
    - Connection pooling
    - Timeout handling

    Example:
        >>> agent = Agent("http://localhost:3000")
        >>> result = agent.user.create(email="test@example.com", name="Test User")
        >>> user = agent.user.get(user_id="123")
    """

    def __init__(
        self,
        base_url: str,
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        enable_logging: bool = False,
    ):
        """
        Initialize agent client.

        Args:
            base_url: Agent base URL (e.g., "http://localhost:3000")
            timeout: Request timeout in seconds (default: 30)
            max_retries: Maximum retry attempts (default: 3)
            retry_delay: Initial retry delay in seconds (default: 1.0)
            enable_logging: Enable request/response logging (default: False)
        """
        self.config = AgentConfig(
            base_url=base_url.rstrip('/'),
            timeout=timeout,
            max_retries=max_retries,
            retry_delay=retry_delay,
        )

        if enable_logging:
            logging.basicConfig(level=logging.INFO)

        # HTTP session with connection pooling
        self.session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=self.config.connection_pool_size,
            pool_maxsize=self.config.connection_pool_size,
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)

        # Circuit breaker
        self.circuit_breaker = CircuitBreaker(
            threshold=self.config.circuit_breaker_threshold,
            timeout=self.config.circuit_breaker_timeout,
        )

        # Cache for discovered verbs
        self._verbs_cache: Optional[List[Dict[str, Any]]] = None
        self._server_info: Optional[Dict[str, Any]] = None

    def __getattr__(self, name: str) -> VerbProxy:
        """Enable dynamic verb calls via dot notation."""
        if name.startswith('_'):
            raise AttributeError(
                f"'{type(self).__name__}' object has no attribute '{name}'")
        return VerbProxy(self, name)

    def health(self) -> Dict[str, Any]:
        """Check agent health status."""
        try:
            response = self.session.get(
                f"{self.config.base_url}/health",
                timeout=self.config.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise ConnectionError(f"Health check failed: {e}")

    def ready(self) -> Dict[str, Any]:
        """Check agent readiness status."""
        try:
            response = self.session.get(
                f"{self.config.base_url}/ready",
                timeout=self.config.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise ConnectionError(f"Readiness check failed: {e}")

    def discover(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Discover available verbs from agent.

        Args:
            force_refresh: Force refresh from server (default: False)

        Returns:
            List of verb definitions with parameters and return types
        """
        if self._verbs_cache and not force_refresh:
            return self._verbs_cache

        try:
            response = self._make_request("tools/list", {})
            tools = response.get("result", {}).get("tools", [])
            self._verbs_cache = tools
            return tools
        except Exception as e:
            logger.error(f"Verb discovery failed: {e}")
            return []

    def list_verbs(self) -> List[str]:
        """Get list of all verb names."""
        verbs = self.discover()
        return [v["name"] for v in verbs]

    def get_verb_schema(self, verb_name: str) -> Optional[Dict[str, Any]]:
        """Get schema for a specific verb."""
        verbs = self.discover()
        for verb in verbs:
            if verb["name"] == verb_name:
                return verb
        return None

    def call_verb(
        self,
        verb_name: str,
        params: Dict[str, Any],
        timeout: Optional[int] = None,
    ) -> Any:
        """
        Call a verb with parameters.

        Args:
            verb_name: Verb name (e.g., "user.create@v1")
            params: Verb parameters
            timeout: Override default timeout

        Returns:
            Verb result

        Raises:
            VerbNotFoundError: Verb does not exist
            InvalidParamsError: Invalid parameters
            TimeoutError: Request timed out
            ConnectionError: Connection failed
        """
        return self._call_with_retry(
            verb_name=verb_name,
            params=params,
            timeout=timeout or self.config.timeout,
        )

    def _call_with_retry(
        self,
        verb_name: str,
        params: Dict[str, Any],
        timeout: int,
    ) -> Any:
        """Execute verb call with retry logic."""
        delay = self.config.retry_delay

        for attempt in range(self.config.max_retries + 1):
            try:
                return self.circuit_breaker.call(
                    self._execute_call,
                    verb_name,
                    params,
                    timeout,
                )
            except CircuitBreakerError:
                raise ConnectionError(
                    "Circuit breaker is open - service unavailable")
            except (requests.Timeout, requests.ConnectionError) as e:
                if attempt == self.config.max_retries:
                    raise ConnectionError(
                        f"Failed after {attempt + 1} attempts: {e}")

                logger.warning(
                    f"Attempt {attempt + 1} failed, retrying in {delay}s: {e}")
                time.sleep(delay)
                delay *= self.config.retry_backoff

            except requests.RequestException as e:
                # Don't retry on HTTP errors (4xx, 5xx)
                raise self._handle_http_error(e)

    def _execute_call(
        self,
        verb_name: str,
        params: Dict[str, Any],
        timeout: int,
    ) -> Any:
        """Execute the actual verb call."""
        response = self._make_request(
            method="tools/call",
            params={
                "name": verb_name,
                "arguments": params,
            },
            timeout=timeout,
        )

        if "error" in response:
            error = response["error"]
            code = error.get("code", -32603)
            message = error.get("message", "Unknown error")

            if code == -32601:
                raise VerbNotFoundError(f"Verb not found: {verb_name}")
            elif code == -32602:
                raise InvalidParamsError(message)
            else:
                raise AgentError(f"Agent error ({code}): {message}")

        return response.get("result", {})

    def _make_request(
        self,
        method: str,
        params: Dict[str, Any],
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Make JSON-RPC request to agent."""
        payload = {
            "jsonrpc": "2.0",
            "id": int(time.time() * 1000),
            "method": method,
            "params": params,
        }

        if self.config.enable_logging:
            logger.info(f"Request: {method} with params: {params}")

        response = self.session.post(
            f"{self.config.base_url}/mcp",
            json=payload,
            timeout=timeout or self.config.timeout,
        )
        response.raise_for_status()

        result = response.json()

        if self.config.enable_logging:
            logger.info(f"Response: {result}")

        return result

    def _handle_http_error(self, error: requests.RequestException) -> Exception:
        """Convert HTTP errors to appropriate exceptions."""
        if isinstance(error, requests.Timeout):
            return TimeoutError(f"Request timed out: {error}")
        elif isinstance(error, requests.ConnectionError):
            return ConnectionError(f"Connection failed: {error}")
        else:
            return AgentError(f"HTTP error: {error}")

    def close(self):
        """Close HTTP session and release resources."""
        self.session.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# Convenience function for quick calls
def call_verb(
    base_url: str,
    verb_name: str,
    params: Dict[str, Any],
    **kwargs
) -> Any:
    """
    Convenience function for one-off verb calls.

    Example:
        >>> result = call_verb(
        ...     "http://localhost:3000",
        ...     "user.create@v1",
        ...     {"email": "test@example.com", "name": "Test"}
        ... )
    """
    with Agent(base_url, **kwargs) as agent:
        return agent.call_verb(verb_name, params)
