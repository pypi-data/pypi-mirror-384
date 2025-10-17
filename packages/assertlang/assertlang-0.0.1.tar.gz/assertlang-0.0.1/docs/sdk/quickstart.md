# AssertLang SDK Quick Start

This guide demonstrates how to integrate AssertLang into your applications using the Python SDK.

---

## Installation

### Python SDK

```bash
pip install promptware-sdk
```

**Requirements**:
- Python 3.10 or higher
- AssertLang daemon running locally (default: `http://localhost:8765`)

---

## Basic Usage

### 1. Create and Execute a Plan

```python
from promptware_sdk import mcp

# Define a plan in AssertLang DSL
plan_source = """
call http_client as api {
    url: "https://api.github.com/repos/promptware/promptware"
    method: "GET"
}

let repo_name = api.data.name
let stars = api.data.stargazers_count
"""

# Create execution plan
plan = mcp.plan_create_v1(plan_source, format="dsl")

# Start execution
run_id = mcp.run_start_v1(plan, state={"debug": True})

print(f"Started run: {run_id}")
```

---

### 2. Stream Timeline Events

```python
from promptware_sdk import TimelineReader

# Create timeline reader
reader = TimelineReader(run_id)

# Stream events in real-time
for event in reader.events():
    phase = event['phase']
    status = event['status']
    alias = event.get('alias', '')

    if phase == 'call':
        print(f"Tool call: {alias} - {status}")
    elif phase == 'let':
        target = event.get('target', '')
        print(f"Variable assignment: {target}")
```

---

### 3. Wait for Completion

```python
# Block until run completes (with timeout)
status = reader.wait_for_completion(timeout=60)

if status == "success":
    print("Execution completed successfully")
elif status == "failure":
    print("Execution failed")
elif status == "timeout":
    print("Execution timed out")

# Report finish to daemon
mcp.report_finish_v1(run_id, status)
```

---

## Example: HTTP Health Check

```python
from promptware_sdk import mcp, AssertLangError

try:
    # Assert endpoint is healthy
    result = mcp.httpcheck_assert_v1(
        url="https://api.example.com/health",
        status_code=200,
        timeout_sec=5
    )

    if result['success']:
        print(f"Health check passed: {result['actual_status_code']}")
    else:
        print(f"Health check failed: expected 200, got {result['actual_status_code']}")

except AssertLangError as e:
    print(f"Error: {e.code} - {e.message}")
```

---

## Example: Natural Language Plans

```python
from promptware_sdk import mcp

# Create plan from natural language
plan = mcp.plan_create_v1(
    "Fetch weather data for San Francisco and save to file",
    format="natural"
)

# Execute
run_id = mcp.run_start_v1(plan)
```

**Note**: Natural language compilation requires Wave 4 compiler. Use `format="dsl"` for Wave 2/3.

---

## Error Handling

```python
from promptware_sdk import AssertLangError, E_RUNTIME, E_TIMEOUT, E_POLICY

try:
    plan = mcp.plan_create_v1(plan_source)
    run_id = mcp.run_start_v1(plan)

except AssertLangError as e:
    if e.code == E_RUNTIME:
        print(f"Runtime error: {e.message}")
    elif e.code == E_TIMEOUT:
        print(f"Operation timed out: {e.message}")
    elif e.code == E_POLICY:
        print(f"Policy violation: {e.message}")
    else:
        print(f"Unknown error ({e.code}): {e.message}")
```

---

## Filtering Timeline Events

```python
from promptware_sdk import TimelineReader

reader = TimelineReader(run_id)

# Get only 'call' events (tool invocations)
call_events = reader.filter_by_phase("call")

for event in call_events:
    alias = event['alias']
    duration = event['duration_ms']
    print(f"{alias} took {duration:.2f}ms")

# Get only 'if' events (conditionals)
if_events = reader.filter_by_phase("if")

for event in if_events:
    condition = event['condition']
    branch = event['branch']
    print(f"Condition '{condition}' evaluated to '{branch}'")
```

---

## Configuration

### Custom Daemon URL

```python
from promptware_sdk import MCP, TimelineReader

# Connect to remote daemon
mcp_client = MCP(daemon_url="http://production.example.com:8765")
plan = mcp_client.plan_create_v1(plan_source)

# Timeline reader with custom URL
reader = TimelineReader(
    run_id=run_id,
    daemon_url="http://production.example.com:8765"
)
```

---

### Environment Variables

```bash
# Set daemon URL via environment
export PROMPTWARE_DAEMON_URL=http://localhost:8765

# Set log level
export PROMPTWARE_LOG_LEVEL=debug
```

**Note**: Environment variable support planned for SDK 0.2.0.

---

## Testing Your Integration

### Mock Daemon Responses

```python
from unittest.mock import Mock, patch
from promptware_sdk import mcp

def test_plan_creation():
    with patch.object(mcp.transport, 'call_verb') as mock_call:
        # Mock successful response
        mock_call.return_value = {
            "ok": True,
            "version": "v1",
            "data": {"plan": {"steps": []}}
        }

        result = mcp.plan_create_v1("call http_client as api")

        assert "plan" in result
        mock_call.assert_called_once()
```

---

### Integration Tests

```python
import pytest
from promptware_sdk import mcp, TimelineReader

@pytest.mark.integration
def test_full_execution():
    """Test full plan execution (requires running daemon)."""

    plan = mcp.plan_create_v1("""
        call http_client as api {
            url: "https://httpbin.org/get"
            method: "GET"
        }
    """)

    run_id = mcp.run_start_v1(plan)
    reader = TimelineReader(run_id)

    status = reader.wait_for_completion(timeout=30)
    assert status == "success"

    mcp.report_finish_v1(run_id, status)
```

---

## Best Practices

### 1. Always Handle Errors

```python
from promptware_sdk import AssertLangError

try:
    plan = mcp.plan_create_v1(plan_source)
    run_id = mcp.run_start_v1(plan)
    status = TimelineReader(run_id).wait_for_completion()

except AssertLangError as e:
    # Log error and handle gracefully
    logger.error(f"Execution failed: {e.code} - {e.message}")
    # Implement retry logic or fallback
```

---

### 2. Use Timeouts

```python
# Always specify timeouts to prevent hanging
reader = TimelineReader(run_id)

try:
    status = reader.wait_for_completion(timeout=60)
except AssertLangError as e:
    if e.code == E_TIMEOUT:
        # Handle timeout explicitly
        print("Execution exceeded 60s timeout")
```

---

### 3. Report Finish

```python
# Always report finish, even on failure
try:
    run_id = mcp.run_start_v1(plan)
    status = TimelineReader(run_id).wait_for_completion()

finally:
    # Ensure daemon knows run is complete
    mcp.report_finish_v1(run_id, status or "failure")
```

---

### 4. Stream Events for Long-Running Plans

```python
# For long plans, stream events instead of blocking
reader = TimelineReader(run_id)

for event in reader.events():
    # Process events as they arrive
    if event['phase'] == 'call' and event['status'] == 'error':
        # React to errors immediately
        print(f"Tool {event['alias']} failed: {event.get('error')}")
        break
```

---

## Next Steps

- **[API Reference](./api-reference.md)**: Full SDK API documentation
- **[Integration Examples](./examples/)**: Real-world integration patterns
- **[Policy Hooks](../policy-hooks.md)**: Understanding tool policies
- **[Timeline Events](../runner-timeline-parity.md)**: Event schema reference

---

## Troubleshooting

### "Connection refused" error

**Problem**: SDK cannot connect to daemon.

**Solution**:
```bash
# Verify daemon is running
curl http://localhost:8765/health

# Start daemon if not running
promptware daemon start
```

---

### "Compatibility error" on SDK import

**Problem**: SDK version incompatible with daemon.

**Solution**:
```bash
# Check versions
python -c "from promptware_sdk import __version__; print(__version__)"
promptware --version

# Upgrade SDK to match daemon
pip install --upgrade promptware-sdk
```

---

### Timeline events not streaming

**Problem**: `reader.events()` returns immediately without events.

**Solution**:
- Ensure run is actually executing (check `reader.wait_for_completion()`)
- Verify daemon timeline endpoint is accessible
- Check for network issues if daemon is remote

---

## Support

- **Issues**: https://github.com/promptware/promptware/issues
- **Discussions**: https://github.com/promptware/promptware/discussions
- **Documentation**: https://docs.assertlang.dev

---

**Last updated**: 2025-09-29 (SDK v0.1.0)