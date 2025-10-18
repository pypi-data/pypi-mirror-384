# AssertLang Testing Guide

Comprehensive testing framework for MCP agents.

## Overview

The AssertLang testing framework provides:

- **Auto-generated test fixtures** - Tests generated from verb schemas
- **Integration testing** - Validate all verbs work correctly
- **Load testing** - Performance testing with concurrency
- **Coverage tracking** - Track which verbs have been tested
- **Beautiful CLI** - User-friendly command-line interface

## Quick Start

### CLI Testing

Test a running agent:

```bash
# Health check and verb discovery
asl test http://localhost:3000

# Auto-generated integration tests
asl test http://localhost:3000 --auto

# Load test a specific verb
asl test http://localhost:3000 --load --verb user.create@v1 --requests 1000

# Full test suite with coverage
asl test http://localhost:3000 --auto --coverage
```

### Python API

Use the testing framework programmatically:

```python
from promptware.testing import AgentTester

# Create tester
tester = AgentTester("http://localhost:3000")

# Health check
if tester.health_check():
    print("Agent is healthy")

# Discover verbs
verbs = tester.discover_verbs()
print(f"Found {len(verbs)} verbs")

# Auto-generate and run tests
test_cases = tester.generate_test_fixtures()
summary = tester.run_integration_tests(test_cases)

# Load test
result = tester.run_load_test(
    "user.create@v1",
    {"email": "test@example.com", "name": "Test"},
    num_requests=100,
    concurrency=10
)

# Export coverage
tester.export_coverage_report()
```

## Features

### Auto-Generated Test Fixtures

The framework analyzes verb schemas and generates test cases automatically:

**Happy path tests:**
- Valid parameters for all required fields
- Tests successful execution
- Validates expected response fields

**Error tests:**
- Missing required parameters
- Invalid parameter types
- Expects appropriate error codes

```python
# Generate tests from schemas
tester = AgentTester("http://localhost:3000")
test_cases = tester.generate_test_fixtures()

# Inspect generated tests
for test in test_cases:
    print(f"{test.name}: {test.verb}")
    print(f"  Params: {test.params}")
    print(f"  Expects error: {test.expect_error}")
```

### Integration Testing

Run comprehensive integration tests:

```python
# Run all tests
summary = tester.run_integration_tests(verbose=True)

# Check results
print(f"Passed: {summary['passed']}/{summary['total']}")
print(f"Coverage: {summary['coverage_pct']:.1f}%")

# Access individual results
for result in summary['results']:
    if not result.passed:
        print(f"Failed: {result.test_name}")
        print(f"Error: {result.error}")
```

**Output:**
```
🧪 Running 10 integration tests...

[1/10] test_user_create_v1_happy_path... ✓ PASS (45ms)
[2/10] test_user_create_v1_missing_param... ✓ PASS (12ms)
[3/10] test_user_get_v1_happy_path... ✓ PASS (23ms)
...

============================================================
📊 Test Summary
============================================================
Total:    10
Passed:   10 ✓
Failed:   0 ✗
Coverage: 100.0%
============================================================
```

### Load Testing

Stress test your agent with concurrent requests:

```python
# Load test with 1000 requests, 50 concurrent
result = tester.run_load_test(
    verb_name="user.create@v1",
    params={
        "email": "loadtest@example.com",
        "name": "Load Test"
    },
    num_requests=1000,
    concurrency=50,
    verbose=True
)

# Analyze results
print(f"Success rate: {result.successful / result.total_requests * 100:.1f}%")
print(f"RPS: {result.requests_per_second:.1f}")
print(f"Avg latency: {result.avg_latency_ms:.1f}ms")
print(f"P95 latency: {result.p95_latency_ms:.1f}ms")
print(f"P99 latency: {result.p99_latency_ms:.1f}ms")
```

**Output:**
```
⚡ Load Testing: user.create@v1
   Requests: 1000
   Concurrency: 50

  Progress: 100/1000 (98 ok, 2 failed)
  Progress: 200/1000 (196 ok, 4 failed)
  ...

============================================================
📈 Load Test Results
============================================================
Total Requests:  1000
Successful:      985 (98.5%)
Failed:          15 (1.5%)
Duration:        12.34s
RPS:             81.0

Latency:
  Average:       580.3ms
  Min:           45.2ms
  Max:           2341.5ms
  P95:           1234.6ms
  P99:           1876.3ms
============================================================
```

### Coverage Tracking

Track which verbs have been tested:

```python
# Run tests
tester.run_integration_tests()

# Check coverage
coverage_pct = (sum(tester.coverage.values()) / len(tester.coverage)) * 100
print(f"Coverage: {coverage_pct:.1f}%")

# See which verbs were tested
for verb, tested in tester.coverage.items():
    status = "✓" if tested else "✗"
    print(f"{status} {verb}")

# Export to JSON
tester.export_coverage_report("coverage.json")
```

**coverage.json:**
```json
{
  "timestamp": "2025-09-30T12:34:56.789Z",
  "agent_url": "http://localhost:3000",
  "total_verbs": 5,
  "tested_verbs": 5,
  "coverage_pct": 100.0,
  "verbs": {
    "user.create@v1": true,
    "user.get@v1": true,
    "user.update@v1": true,
    "user.delete@v1": true,
    "user.list@v1": true
  }
}
```

## Custom Test Cases

Define custom test cases for specific scenarios:

```python
from promptware.testing import TestCase

# Define custom tests
custom_tests = [
    # Test valid user creation
    TestCase(
        name="test_create_admin_user",
        verb="user.create@v1",
        params={
            "email": "admin@example.com",
            "name": "Admin User",
            "role": "admin"
        },
        expected_fields=["user_id", "email", "name", "role"]
    ),

    # Test missing required field
    TestCase(
        name="test_create_user_missing_email",
        verb="user.create@v1",
        params={"name": "No Email User"},
        expected_fields=[],
        expect_error=True,
        error_code=-32602  # Invalid params
    ),

    # Test invalid parameter type
    TestCase(
        name="test_create_user_invalid_type",
        verb="user.create@v1",
        params={
            "email": "test@example.com",
            "name": 12345  # Should be string
        },
        expected_fields=[],
        expect_error=True
    ),
]

# Run custom tests
summary = tester.run_integration_tests(custom_tests)
```

## Production Workflow

Recommended testing workflow for production:

```python
def production_test_workflow(agent_url: str):
    """Production testing workflow."""
    tester = AgentTester(agent_url, timeout=60)

    # 1. Health check
    if not tester.health_check(verbose=False):
        raise RuntimeError("Agent not healthy")

    # 2. Discover verbs
    verbs = tester.discover_verbs()

    # 3. Run integration tests
    test_cases = tester.generate_test_fixtures()
    summary = tester.run_integration_tests(test_cases, verbose=False)

    if summary['failed'] > 0:
        raise RuntimeError(f"{summary['failed']} tests failed")

    # 4. Load test critical verbs
    critical_verbs = [v for v in verbs if 'create' in v['name'] or 'update' in v['name']]

    for verb in critical_verbs:
        # Generate test params
        input_schema = verb.get('inputSchema', {})
        properties = input_schema.get('properties', {})
        test_params = tester._generate_test_data(properties, input_schema.get('required', []))

        # Load test
        result = tester.run_load_test(
            verb['name'],
            test_params,
            num_requests=100,
            concurrency=10,
            verbose=False
        )

        success_rate = (result.successful / result.total_requests) * 100
        if success_rate < 95.0:
            raise RuntimeError(f"{verb['name']} load test: {success_rate:.1f}% success rate")

    # 5. Export coverage
    tester.export_coverage_report()

    return True
```

## CI/CD Integration

### GitHub Actions

```yaml
name: Test Agent

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          pip install -e .
          pip install -r requirements.txt

      - name: Start agent
        run: |
          python generated/my-agent/my-agent_server.py &
          sleep 5

      - name: Run tests
        run: |
          asl test http://localhost:3000 --auto --coverage

      - name: Upload coverage
        uses: actions/upload-artifact@v3
        with:
          name: coverage-report
          path: coverage.json
```

### Docker

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install AssertLang
COPY . .
RUN pip install -e .

# Run agent
CMD ["python", "generated/my-agent/my-agent_server.py"]

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:3000/health')"
```

Test the Docker container:

```bash
# Build and run
docker build -t my-agent .
docker run -d -p 3000:3000 my-agent

# Test
asl test http://localhost:3000 --auto
```

## CLI Reference

### Basic Commands

```bash
# Health check and verb discovery
asl test http://localhost:3000

# Integration tests
asl test http://localhost:3000 --auto

# Load tests
asl test http://localhost:3000 --load --verb user.create@v1

# Full suite
asl test http://localhost:3000 --auto --coverage
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--auto` | Auto-generate and run integration tests | - |
| `--load` | Run load tests | - |
| `--verb VERB` | Verb to load test (required with `--load`) | - |
| `--requests NUM` | Number of load test requests | 100 |
| `--concurrency NUM` | Concurrent requests | 10 |
| `--coverage` | Export coverage report | - |
| `--timeout SEC` | Request timeout | 30 |

## API Reference

### AgentTester Class

```python
class AgentTester:
    def __init__(self, agent_url: str, timeout: int = 30):
        """Initialize tester."""

    def health_check(self, verbose: bool = True) -> bool:
        """Check agent health."""

    def discover_verbs(self) -> List[Dict[str, Any]]:
        """Discover all verbs."""

    def generate_test_fixtures(self) -> List[TestCase]:
        """Auto-generate test fixtures from schemas."""

    def run_integration_tests(
        self,
        test_cases: Optional[List[TestCase]] = None,
        verbose: bool = True
    ) -> Dict[str, Any]:
        """Run integration tests."""

    def run_load_test(
        self,
        verb_name: str,
        params: Dict[str, Any],
        num_requests: int = 100,
        concurrency: int = 10,
        verbose: bool = True
    ) -> LoadTestResult:
        """Run load test."""

    def export_coverage_report(self, output_file: str = "coverage.json"):
        """Export coverage report."""
```

### TestCase Dataclass

```python
@dataclass
class TestCase:
    name: str                           # Test name
    verb: str                           # Verb to test
    params: Dict[str, Any]              # Parameters to send
    expected_fields: List[str]          # Expected response fields
    expect_error: bool = False          # Whether error is expected
    error_code: Optional[int] = None    # Expected error code
```

### LoadTestResult Dataclass

```python
@dataclass
class LoadTestResult:
    total_requests: int         # Total requests made
    successful: int             # Successful requests
    failed: int                 # Failed requests
    total_duration_s: float     # Total duration in seconds
    avg_latency_ms: float       # Average latency
    min_latency_ms: float       # Minimum latency
    max_latency_ms: float       # Maximum latency
    p95_latency_ms: float       # 95th percentile latency
    p99_latency_ms: float       # 99th percentile latency
    requests_per_second: float  # Throughput
    errors: List[str]           # List of unique errors
```

## Best Practices

### 1. Test in Development

Always test agents during development:

```bash
# Generate agent
promptware generate my-agent.al

# Start agent
cd generated/my-agent
python my-agent_server.py &

# Test immediately
asl test http://localhost:3000 --auto
```

### 2. Load Test Before Production

Run load tests to find performance bottlenecks:

```bash
# Start with low concurrency
asl test http://localhost:3000 --load --verb user.create@v1 --requests 100 --concurrency 5

# Gradually increase
asl test http://localhost:3000 --load --verb user.create@v1 --requests 500 --concurrency 25

# Production-level test
asl test http://localhost:3000 --load --verb user.create@v1 --requests 1000 --concurrency 50
```

### 3. Track Coverage

Maintain high test coverage:

```bash
# Run tests with coverage
asl test http://localhost:3000 --auto --coverage

# Check coverage.json
cat coverage.json | jq '.coverage_pct'
```

### 4. Automate in CI

Add testing to your CI/CD pipeline (see CI/CD Integration above).

### 5. Test All Languages

If you support multiple languages, test each:

```bash
# Test Python agent
asl test http://localhost:3000 --auto

# Test Node.js agent
asl test http://localhost:3001 --auto

# Test Go agent
asl test http://localhost:3002 --auto
```

## Examples

See `examples/test_agent.py` for comprehensive examples:

```bash
python examples/test_agent.py
```

## Next Steps

- [CLI Guide](./cli-guide.md) - Complete CLI reference
- [SDK Guide](./sdk-guide.md) - Client library documentation
- [Production Hardening](./production-hardening.md) - Production features
