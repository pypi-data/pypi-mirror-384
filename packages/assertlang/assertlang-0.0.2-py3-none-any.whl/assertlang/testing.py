"""
Promptware Testing Framework

Provides comprehensive testing capabilities for MCP agents:
- Auto-generated test fixtures from verb schemas
- Integration tests for all verbs
- Load testing support
- Mock tool execution
- Coverage reports
"""

import json
import statistics
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests


@dataclass
class TestCase:
    """Individual test case."""
    name: str
    verb: str
    params: Dict[str, Any]
    expected_fields: List[str]
    expect_error: bool = False
    error_code: Optional[int] = None


@dataclass
class TestResult:
    """Result from a test execution."""
    test_name: str
    verb: str
    passed: bool
    duration_ms: float
    error: Optional[str] = None
    response: Optional[Dict[str, Any]] = None


@dataclass
class LoadTestResult:
    """Results from load testing."""
    total_requests: int
    successful: int
    failed: int
    total_duration_s: float
    avg_latency_ms: float
    min_latency_ms: float
    max_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    requests_per_second: float
    errors: List[str] = field(default_factory=list)


class AgentTester:
    """
    Comprehensive testing framework for MCP agents.

    Features:
    - Auto-generate tests from verb schemas
    - Integration testing
    - Load testing
    - Coverage tracking
    - Mock tool execution
    """

    def __init__(self, agent_url: str, timeout: int = 30):
        """
        Initialize tester.

        Args:
            agent_url: Agent base URL (e.g., "http://localhost:3000")
            timeout: Request timeout in seconds
        """
        self.agent_url = agent_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        self.verbs: List[Dict[str, Any]] = []
        self.coverage: Dict[str, bool] = {}

    def discover_verbs(self) -> List[Dict[str, Any]]:
        """Discover all verbs from the agent."""
        response = self._make_request("tools/list", {})
        self.verbs = response.get("result", {}).get("tools", [])

        # Initialize coverage tracking
        for verb in self.verbs:
            self.coverage[verb["name"]] = False

        return self.verbs

    def generate_test_fixtures(self) -> List[TestCase]:
        """
        Auto-generate test fixtures from verb schemas.

        Returns:
            List of test cases with realistic test data
        """
        if not self.verbs:
            self.discover_verbs()

        test_cases = []

        for verb in self.verbs:
            verb_name = verb["name"]
            input_schema = verb.get("inputSchema", {})
            properties = input_schema.get("properties", {})
            required = input_schema.get("required", [])

            # Generate test data based on schema
            test_params = self._generate_test_data(properties, required)

            # Happy path test
            test_cases.append(TestCase(
                name=f"test_{verb_name.replace('.', '_').replace('@', '_')}_happy_path",
                verb=verb_name,
                params=test_params,
                expected_fields=self._get_expected_fields(verb),
            ))

            # Missing required parameter test
            if required:
                missing_param = required[0]
                invalid_params = {
                    k: v for k, v in test_params.items() if k != missing_param}
                test_cases.append(TestCase(
                    name=f"test_{verb_name.replace('.', '_').replace('@', '_')}_missing_param",
                    verb=verb_name,
                    params=invalid_params,
                    expected_fields=[],
                    expect_error=True,
                    error_code=-32602,  # Invalid params
                ))

        return test_cases

    def run_integration_tests(
        self,
        test_cases: Optional[List[TestCase]] = None,
        verbose: bool = True
    ) -> Dict[str, Any]:
        """
        Run integration tests.

        Args:
            test_cases: Test cases to run (auto-generated if None)
            verbose: Print progress output

        Returns:
            Test results summary
        """
        if test_cases is None:
            if verbose:
                print("🔍 Auto-generating test fixtures...")
            test_cases = self.generate_test_fixtures()

        if verbose:
            print(f"\n🧪 Running {len(test_cases)} integration tests...\n")

        results: List[TestResult] = []
        passed = 0
        failed = 0

        for i, test_case in enumerate(test_cases, 1):
            if verbose:
                print(f"[{i}/{len(test_cases)}] {test_case.name}...", end=" ")

            result = self._run_test_case(test_case)
            results.append(result)

            if result.passed:
                passed += 1
                if verbose:
                    print(f"✓ PASS ({result.duration_ms:.0f}ms)")
            else:
                failed += 1
                if verbose:
                    print(f"✗ FAIL ({result.duration_ms:.0f}ms)")
                    if result.error:
                        print(f"    Error: {result.error}")

            # Update coverage
            self.coverage[test_case.verb] = True

        # Calculate coverage
        coverage_pct = (sum(self.coverage.values()) /
                        len(self.coverage) * 100) if self.coverage else 0

        summary = {
            "total": len(test_cases),
            "passed": passed,
            "failed": failed,
            "coverage_pct": coverage_pct,
            "results": results,
        }

        if verbose:
            print(f"\n{'='*60}")
            print("📊 Test Summary")
            print(f"{'='*60}")
            print(f"Total:    {summary['total']}")
            print(f"Passed:   {summary['passed']} ✓")
            print(f"Failed:   {summary['failed']} ✗")
            print(f"Coverage: {coverage_pct:.1f}%")
            print(f"{'='*60}\n")

        return summary

    def run_load_test(
        self,
        verb_name: str,
        params: Dict[str, Any],
        num_requests: int = 100,
        concurrency: int = 10,
        verbose: bool = True
    ) -> LoadTestResult:
        """
        Run load test against a verb.

        Args:
            verb_name: Verb to test
            params: Parameters to send
            num_requests: Total number of requests
            concurrency: Concurrent requests
            verbose: Print progress

        Returns:
            Load test results
        """
        if verbose:
            print(f"\n⚡ Load Testing: {verb_name}")
            print(f"   Requests: {num_requests}")
            print(f"   Concurrency: {concurrency}")
            print()

        latencies: List[float] = []
        errors: List[str] = []
        successful = 0
        failed = 0

        start_time = time.time()

        def make_request(_):
            """Execute single request."""
            request_start = time.time()
            try:
                response = self._call_verb(verb_name, params)
                latency = (time.time() - request_start) * 1000

                if "error" in response:
                    return False, latency, response["error"].get("message", "Unknown error")
                else:
                    return True, latency, None
            except Exception as e:
                latency = (time.time() - request_start) * 1000
                return False, latency, str(e)

        # Execute load test with thread pool
        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            futures = [executor.submit(make_request, i)
                       for i in range(num_requests)]

            for i, future in enumerate(as_completed(futures), 1):
                success, latency, error = future.result()
                latencies.append(latency)

                if success:
                    successful += 1
                else:
                    failed += 1
                    if error:
                        errors.append(error)

                if verbose and i % 10 == 0:
                    print(
                        f"  Progress: {i}/{num_requests} ({successful} ok, {failed} failed)")

        total_duration = time.time() - start_time

        # Calculate statistics
        latencies.sort()

        result = LoadTestResult(
            total_requests=num_requests,
            successful=successful,
            failed=failed,
            total_duration_s=total_duration,
            avg_latency_ms=statistics.mean(latencies),
            min_latency_ms=min(latencies),
            max_latency_ms=max(latencies),
            p95_latency_ms=latencies[int(
                len(latencies) * 0.95)] if latencies else 0,
            p99_latency_ms=latencies[int(
                len(latencies) * 0.99)] if latencies else 0,
            requests_per_second=num_requests / total_duration,
            errors=list(set(errors))[:10]  # First 10 unique errors
        )

        if verbose:
            print(f"\n{'='*60}")
            print("📈 Load Test Results")
            print(f"{'='*60}")
            print(f"Total Requests:  {result.total_requests}")
            print(
                f"Successful:      {result.successful} ({result.successful/result.total_requests*100:.1f}%)")
            print(
                f"Failed:          {result.failed} ({result.failed/result.total_requests*100:.1f}%)")
            print(f"Duration:        {result.total_duration_s:.2f}s")
            print(f"RPS:             {result.requests_per_second:.1f}")
            print("\nLatency:")
            print(f"  Average:       {result.avg_latency_ms:.1f}ms")
            print(f"  Min:           {result.min_latency_ms:.1f}ms")
            print(f"  Max:           {result.max_latency_ms:.1f}ms")
            print(f"  P95:           {result.p95_latency_ms:.1f}ms")
            print(f"  P99:           {result.p99_latency_ms:.1f}ms")
            if result.errors:
                print("\nErrors:")
                for error in result.errors[:5]:
                    print(f"  - {error}")
            print(f"{'='*60}\n")

        return result

    def health_check(self, verbose: bool = True) -> bool:
        """
        Check agent health.

        Returns:
            True if healthy, False otherwise
        """
        try:
            response = self.session.get(
                f"{self.agent_url}/health",
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()

            if verbose:
                print(f"✓ Health check passed: {data}")

            return data.get("status") in ["healthy", "alive"]
        except Exception as e:
            if verbose:
                print(f"✗ Health check failed: {e}")
            return False

    def _run_test_case(self, test_case: TestCase) -> TestResult:
        """Execute a single test case."""
        start_time = time.time()

        try:
            response = self._call_verb(test_case.verb, test_case.params)
            duration_ms = (time.time() - start_time) * 1000

            # Check if error was expected
            if test_case.expect_error:
                if "error" in response:
                    error_code = response["error"].get("code")
                    if test_case.error_code and error_code != test_case.error_code:
                        return TestResult(
                            test_name=test_case.name,
                            verb=test_case.verb,
                            passed=False,
                            duration_ms=duration_ms,
                            error=f"Expected error code {test_case.error_code}, got {error_code}",
                            response=response
                        )
                    return TestResult(
                        test_name=test_case.name,
                        verb=test_case.verb,
                        passed=True,
                        duration_ms=duration_ms,
                        response=response
                    )
                else:
                    return TestResult(
                        test_name=test_case.name,
                        verb=test_case.verb,
                        passed=False,
                        duration_ms=duration_ms,
                        error="Expected error but got success",
                        response=response
                    )

            # Check for unexpected errors
            if "error" in response:
                return TestResult(
                    test_name=test_case.name,
                    verb=test_case.verb,
                    passed=False,
                    duration_ms=duration_ms,
                    error=response["error"].get("message", "Unknown error"),
                    response=response
                )

            # Validate expected fields
            result_data = response.get("result", {})
            missing_fields = [
                f for f in test_case.expected_fields if f not in result_data]

            if missing_fields:
                return TestResult(
                    test_name=test_case.name,
                    verb=test_case.verb,
                    passed=False,
                    duration_ms=duration_ms,
                    error=f"Missing expected fields: {missing_fields}",
                    response=response
                )

            return TestResult(
                test_name=test_case.name,
                verb=test_case.verb,
                passed=True,
                duration_ms=duration_ms,
                response=response
            )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return TestResult(
                test_name=test_case.name,
                verb=test_case.verb,
                passed=False,
                duration_ms=duration_ms,
                error=str(e)
            )

    def _call_verb(self, verb_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Call a verb and return response."""
        return self._make_request(
            "tools/call",
            {"name": verb_name, "arguments": params}
        )

    def _make_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make JSON-RPC request."""
        payload = {
            "jsonrpc": "2.0",
            "id": int(time.time() * 1000),
            "method": method,
            "params": params,
        }

        response = self.session.post(
            f"{self.agent_url}/mcp",
            json=payload,
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()

    def _generate_test_data(
        self,
        properties: Dict[str, Any],
        required: List[str]
    ) -> Dict[str, Any]:
        """Generate realistic test data based on schema."""
        test_data = {}

        for prop_name, prop_schema in properties.items():
            prop_type = prop_schema.get("type", "string")

            if prop_type == "string":
                test_data[prop_name] = f"test_{prop_name}"
            elif prop_type == "integer" or prop_type == "int":
                test_data[prop_name] = 123
            elif prop_type == "boolean" or prop_type == "bool":
                test_data[prop_name] = True
            elif prop_type == "array":
                test_data[prop_name] = []
            elif prop_type == "object":
                test_data[prop_name] = {}
            else:
                test_data[prop_name] = None

        return test_data

    def _get_expected_fields(self, verb: Dict[str, Any]) -> List[str]:
        """Extract expected return fields from verb schema."""
        # Standard MCP response fields
        expected = ["input_params", "tool_results", "metadata"]

        # Add any custom fields from description
        # (In practice, you'd parse the verb's return schema)

        return expected

    def export_coverage_report(self, output_file: str = "coverage.json"):
        """Export coverage report to JSON."""
        report = {
            "timestamp": datetime.now().isoformat(),
            "agent_url": self.agent_url,
            "total_verbs": len(self.coverage),
            "tested_verbs": sum(self.coverage.values()),
            "coverage_pct": (sum(self.coverage.values()) / len(self.coverage) * 100) if self.coverage else 0,
            "verbs": self.coverage,
        }

        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"✓ Coverage report exported to {output_file}")
