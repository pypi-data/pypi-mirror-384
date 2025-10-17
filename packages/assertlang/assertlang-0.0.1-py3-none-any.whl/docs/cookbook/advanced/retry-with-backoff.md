# Retry with Exponential Backoff

**Implement resilient retry logic with exponential backoff for handling transient failures.**

---

## Problem

Network calls, API requests, and external services fail temporarily:
- Network timeouts
- Rate limiting (429 errors)
- Temporary service unavailability
- Database deadlocks
- Intermittent errors

**Bad approach:**
```python
# Python: No retry
response = requests.get(url)
# Fails immediately on transient error
```

**Worse approach:**
```python
# Python: Naive retry (hammers the service)
for i in range(10):
    try:
        response = requests.get(url)
        break
    except:
        pass  # Retry immediately
# Makes problem worse during outages
```

---

## Solution

Exponential backoff with jitter:

```promptware
function retry_with_backoff<T>(
    operation: function() -> Result<T, String>,
    max_attempts: Int,
    base_delay_ms: Int
) -> Result<T, String>
  requires:
    max_attempts > 0
    base_delay_ms > 0
  do
    let attempts = 0

    while attempts < max_attempts:
      let result = operation()

      if result is Ok(value):
        return Ok(value)
      end

      attempts = attempts + 1

      if attempts < max_attempts:
        # Exponential backoff: delay = base * 2^attempt
        let delay = base_delay_ms * (2 ** attempts)
        sleep(delay)
      end
    end

    return Err("Max retry attempts exceeded")
  end
end
```

---

## Basic Retry Pattern

### Simple Retry

```promptware
function retry_simple<T>(
    operation: function() -> Result<T, String>,
    max_attempts: Int
) -> Result<T, String>
  requires:
    max_attempts > 0
    max_attempts <= 10
  do
    let attempts = 0
    let last_error = "No error"

    while attempts < max_attempts:
      let result = operation()

      if result is Ok(value):
        return Ok(value)
      else if result is Err(msg):
        last_error = msg
        attempts = attempts + 1
      end
    end

    return Err("Failed after " + String(attempts) + " attempts: " + last_error)
  end
end
```

---

## Exponential Backoff

### With Maximum Delay Cap

```promptware
function retry_exponential<T>(
    operation: function() -> Result<T, String>,
    max_attempts: Int,
    base_delay_ms: Int,
    max_delay_ms: Int
) -> Result<T, String>
  requires:
    max_attempts > 0
    base_delay_ms > 0
    max_delay_ms >= base_delay_ms
  do
    let attempts = 0

    while attempts < max_attempts:
      let result = operation()

      if result is Ok(value):
        return Ok(value)
      end

      attempts = attempts + 1

      if attempts < max_attempts:
        # Calculate exponential delay
        let delay = base_delay_ms * (2 ** attempts)

        # Cap at maximum
        if delay > max_delay_ms:
          delay = max_delay_ms
        end

        sleep(delay)
      end
    end

    return Err("Exhausted all retry attempts")
  end
end
```

---

## Jittered Backoff

### Prevent Thundering Herd

```promptware
function retry_with_jitter<T>(
    operation: function() -> Result<T, String>,
    max_attempts: Int,
    base_delay_ms: Int,
    max_delay_ms: Int
) -> Result<T, String>
  requires:
    max_attempts > 0
    base_delay_ms > 0
    max_delay_ms >= base_delay_ms
  do
    let attempts = 0

    while attempts < max_attempts:
      let result = operation()

      if result is Ok(value):
        return Ok(value)
      end

      attempts = attempts + 1

      if attempts < max_attempts:
        # Exponential delay
        let exp_delay = base_delay_ms * (2 ** attempts)

        # Cap delay
        if exp_delay > max_delay_ms:
          exp_delay = max_delay_ms
        end

        # Add jitter (random 0-100%)
        let jitter = random_int(0, exp_delay)
        let delay = exp_delay + jitter

        sleep(delay)
      end
    end

    return Err("All retries failed")
  end
end
```

---

## Conditional Retry

### Only Retry Transient Errors

```promptware
function is_retryable_error(error: String) -> Bool
  do
    # Retry on specific error patterns
    if "timeout" in error:
      return true
    end

    if "429" in error:  # Rate limited
      return true
    end

    if "503" in error:  # Service unavailable
      return true
    end

    if "connection refused" in error:
      return true
    end

    # Don't retry client errors (400, 401, 403, 404)
    if "400" in error or "401" in error or "403" in error or "404" in error:
      return false
    end

    return false
  end
end

function retry_smart<T>(
    operation: function() -> Result<T, String>,
    max_attempts: Int,
    base_delay_ms: Int
) -> Result<T, String>
  requires:
    max_attempts > 0
    base_delay_ms > 0
  do
    let attempts = 0

    while attempts < max_attempts:
      let result = operation()

      if result is Ok(value):
        return Ok(value)
      else if result is Err(error):
        # Only retry if error is retryable
        if not is_retryable_error(error):
          return Err("Non-retryable error: " + error)
        end

        attempts = attempts + 1

        if attempts < max_attempts:
          let delay = base_delay_ms * (2 ** attempts)
          sleep(delay)
        end
      end
    end

    return Err("Exhausted retries on retryable error")
  end
end
```

---

## Circuit Breaker Pattern

### Fail Fast After Multiple Failures

```promptware
type CircuitState:
  is_open: Bool
  failure_count: Int
  last_failure_time: Int
  success_count: Int
end

function is_circuit_open(
    state: CircuitState,
    threshold: Int,
    timeout_ms: Int,
    current_time: Int
) -> Bool
  requires:
    threshold > 0
    timeout_ms > 0
  do
    if not state.is_open:
      return false
    end

    # Check if timeout expired (circuit can close)
    let time_since_failure = current_time - state.last_failure_time

    if time_since_failure > timeout_ms:
      return false  # Circuit can close
    end

    return true  # Circuit still open
  end
end

function retry_with_circuit_breaker<T>(
    operation: function() -> Result<T, String>,
    state: CircuitState,
    threshold: Int,
    current_time: Int
) -> Result<T, CircuitState>
  requires:
    threshold > 0
  do
    # Check if circuit is open
    if is_circuit_open(state, threshold, 30000, current_time):
      return Err("Circuit breaker open - service unavailable")
    end

    # Try operation
    let result = operation()

    if result is Ok(value):
      # Success - reset failure count
      let new_state = CircuitState(
        is_open=false,
        failure_count=0,
        last_failure_time=state.last_failure_time,
        success_count=state.success_count + 1
      )
      return Ok(new_state)

    else:
      # Failure - increment count
      let new_failure_count = state.failure_count + 1

      # Open circuit if threshold exceeded
      let should_open = new_failure_count >= threshold

      let new_state = CircuitState(
        is_open=should_open,
        failure_count=new_failure_count,
        last_failure_time=current_time,
        success_count=state.success_count
      )

      return Err(new_state)
    end
  end
end
```

---

## Real-World Examples

### API Request with Retry

```python
# Python
import requests
import time
from retry_backoff import retry_with_jitter, Ok, Err

def fetch_user_data(user_id: str):
    """Fetch user from API with retry."""

    def operation():
        try:
            response = requests.get(
                f"https://api.example.com/users/{user_id}",
                timeout=5
            )

            if response.status_code == 200:
                return Ok(response.json())
            elif response.status_code == 429:
                return Err("Rate limited (429)")
            elif response.status_code >= 500:
                return Err(f"Server error ({response.status_code})")
            else:
                return Err(f"Client error ({response.status_code})")

        except requests.Timeout:
            return Err("Request timeout")
        except requests.ConnectionError:
            return Err("Connection error")

    # Retry with exponential backoff
    result = retry_with_jitter(
        operation=operation,
        max_attempts=5,
        base_delay_ms=100,
        max_delay_ms=10000
    )

    return result
```

### Database Query with Retry

```python
# Python (PostgreSQL)
import psycopg2
from retry_backoff import retry_smart

def execute_transaction(query: str, params: tuple):
    """Execute database transaction with retry on deadlock."""

    def operation():
        try:
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()

            cursor.execute(query, params)
            conn.commit()

            return Ok(cursor.rowcount)

        except psycopg2.extensions.TransactionRollbackError:
            # Deadlock - retry
            return Err("Deadlock detected")

        except psycopg2.OperationalError as e:
            # Connection error - retry
            return Err(f"Connection error: {e}")

        except psycopg2.Error as e:
            # Other errors - don't retry
            return Err(f"Database error (non-retryable): {e}")

    result = retry_smart(
        operation=operation,
        max_attempts=3,
        base_delay_ms=50
    )

    return result
```

---

## Integration Examples

### Async/Await (Python)

```python
# Python (asyncio)
import asyncio
from typing import Callable, TypeVar
from retry_backoff import Ok, Err

T = TypeVar('T')

async def retry_async(
    operation: Callable[[], Awaitable[Result[T, str]]],
    max_attempts: int,
    base_delay_ms: int
) -> Result[T, str]:
    """Async retry with exponential backoff."""

    attempts = 0

    while attempts < max_attempts:
        result = await operation()

        if isinstance(result, Ok):
            return result

        attempts += 1

        if attempts < max_attempts:
            delay_seconds = (base_delay_ms * (2 ** attempts)) / 1000
            await asyncio.sleep(delay_seconds)

    return Err("Max retries exceeded")

# Usage
async def fetch_data_async():
    async def operation():
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return Ok(data)
                    return Err(f"HTTP {response.status}")
        except asyncio.TimeoutError:
            return Err("Timeout")

    return await retry_async(operation, max_attempts=5, base_delay_ms=100)
```

---

## Testing Retry Logic

```python
# Python (pytest)
import pytest
from unittest.mock import Mock
from retry_backoff import retry_simple, Ok, Err

def test_retry_success_first_attempt():
    operation = Mock(return_value=Ok(42))

    result = retry_simple(operation, max_attempts=3)

    assert isinstance(result, Ok)
    assert result.value == 42
    assert operation.call_count == 1

def test_retry_success_after_failures():
    operation = Mock(side_effect=[
        Err("error 1"),
        Err("error 2"),
        Ok(42)
    ])

    result = retry_simple(operation, max_attempts=3)

    assert isinstance(result, Ok)
    assert result.value == 42
    assert operation.call_count == 3

def test_retry_all_attempts_fail():
    operation = Mock(return_value=Err("persistent error"))

    result = retry_simple(operation, max_attempts=3)

    assert isinstance(result, Err)
    assert "persistent error" in result.error
    assert operation.call_count == 3

def test_exponential_backoff_timing(monkeypatch):
    """Test that delays grow exponentially."""
    sleep_calls = []

    def mock_sleep(ms):
        sleep_calls.append(ms)

    monkeypatch.setattr("time.sleep", mock_sleep)

    operation = Mock(return_value=Err("error"))

    retry_exponential(operation, max_attempts=4, base_delay_ms=100, max_delay_ms=10000)

    # Delays should be: 200ms, 400ms, 800ms
    assert sleep_calls == [200, 400, 800]
```

---

## Best Practices

1. **Cap Maximum Delay**: Prevent waiting too long
2. **Use Jitter**: Prevent thundering herd
3. **Retry Selectively**: Not all errors are retryable
4. **Log Attempts**: Track retry patterns
5. **Monitor Metrics**: Alert on high retry rates
6. **Circuit Breaker**: Fail fast when service is down

---

## See Also

- [Error Recovery Strategies](error-recovery.md) - More error handling patterns
- [Monitor Contract Violations](../../how-to/deployment/monitoring.md) - Monitor retries
- [API Rate Limiting](../real-world/04_api_rate_limiting/README.md) - Rate limiting example

---

**Difficulty:** Advanced
**Time:** 30 minutes
**Category:** Advanced Patterns
**Last Updated:** 2025-10-15
