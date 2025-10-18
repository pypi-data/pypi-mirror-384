# Test Batch System Documentation

This document explains the test batching system for AssertLang, including how to run batches, interpret outputs, and troubleshoot failures.

---

## Overview

The test batch system runs AssertLang's test suite sequentially in logical groups, avoiding environment timeouts that can occur when running all tests simultaneously.

**Benefits**:
- **Isolation**: Each test batch runs in a separate pytest invocation, preventing cross-contamination
- **Debugging**: Batch failures are easier to isolate and debug
- **Performance**: Comparable runtime to full pytest (~2.6s batched vs ~2.0s full)
- **Clarity**: Clear separation between MVP, runner, verb, and tool tests

---

## Running Test Batches

### Via Make (Recommended)

```bash
make test-batches
```

This activates the virtual environment and runs the batch script.

### Via Script Directly

```bash
bash scripts/run_test_batches.sh
```

Requires manual virtual environment activation:
```bash
source .venv/bin/activate
bash scripts/run_test_batches.sh
```

---

## Batch Structure

The batch script runs 4 sequential test groups:

### Batch 1: MVP End-to-End
```bash
pytest tests/test_mvp_e2e.py
```
- **Purpose**: Validate core DSL execution flow
- **Tests**: 1 test validating hello-world plan execution
- **Expected**: 1 passed
- **Runtime**: ~1.8s

### Batch 2: Runner I/O Protocol
```bash
pytest tests/test_runners_io.py
```
- **Purpose**: Validate runner envelope compliance (apply/start/stop/health)
- **Tests**: 10 tests (7 run, 3 skipped if runtimes unavailable)
- **Expected**: 7 passed, 3 skipped
- **Runtime**: ~0.4s

### Batch 3: Verb Contracts
```bash
pytest tests/test_verbs_contracts.py -vv
```
- **Purpose**: Validate MCP verb schemas and timeline events
- **Tests**: Currently has import error (missing `schema_utils` module)
- **Expected**: Collection error (known issue)
- **Runtime**: ~0.1s

### Batch 4: Tool Adapters
```bash
pytest tests/tools -q
```
- **Purpose**: Smoke test multi-language tool adapters (Node/Go/Rust/.NET)
- **Tests**: Varies by available runtimes (node/go/cargo/dotnet in PATH)
- **Expected**: Varies (adapters skip if runtime unavailable)
- **Runtime**: Varies by runtime count

---

## Interpreting Output

### Successful Batch Run

```
============================= test session starts ==============================
platform darwin -- Python 3.13.4, pytest-8.4.2, pluggy-1.6.0
rootdir: /Users/hustlermain/HUSTLER_CONTENT/HSTLR/DEV/AssertLang
configfile: pyproject.toml
collected 1 item

tests/test_mvp_e2e.py .                                                  [100%]

============================== 1 passed in 1.78s ===============================
```

**Indicators**:
- `collected N items` — All tests discovered
- `.` — Test passed
- `N passed in X.XXs` — All tests succeeded

### Skipped Tests

```
tests/test_runners_io.py .......sss                                      [100%]

========================= 7 passed, 3 skipped in 0.37s =========================
```

**Indicators**:
- `s` — Test skipped (usually due to missing runtime like `go` or `dotnet`)
- `N passed, M skipped` — Some tests skipped but not failures

**Reason**: Tests skip when required runtimes not in PATH (see "Troubleshooting" below).

### Failed Batch (Collection Error)

```
==================================== ERRORS ====================================
________________ ERROR collecting tests/test_verbs_contracts.py ________________
ImportError while importing test module '/path/to/tests/test_verbs_contracts.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
...
E   ModuleNotFoundError: No module named 'schema_utils'
=========================== short test summary info ============================
ERROR tests/test_verbs_contracts.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
=============================== 1 error in 0.11s ===============================
```

**Indicators**:
- `ERROR collecting` — Test file couldn't be imported
- `ModuleNotFoundError` — Missing dependency
- `Interrupted: 1 error during collection` — Pytest stopped before running tests

**Current known issue**: `test_verbs_contracts.py` missing `schema_utils` module (unrelated to toolgen fix).

### Failed Test (Assertion Error)

```
tests/test_example.py F                                                  [100%]

=================================== FAILURES ===================================
_________________________________ test_example _________________________________
...
AssertionError: expected True, got False
```

**Indicators**:
- `F` — Test failed
- `FAILURES` section shows stack trace and assertion details
- Exit code non-zero (script stops due to `set -e`)

---

## Performance Metrics

| Approach | Runtime | Tests Run | Notes |
| --- | --- | --- | --- |
| **Batch script** | ~2.6s | 18 (8 passed, 3 skipped, 1 error) | Sequential batches |
| **Full pytest** | ~2.0s | Variable | Single invocation, may timeout on large suites |

**Conclusion**: Batch overhead minimal (~0.6s), acceptable for isolation benefits.

---

## Rerun Strategies

### Rerun All Batches

```bash
make test-batches
```

Re-runs all 4 batches sequentially.

### Rerun Single Batch

```bash
# MVP tests only
pytest tests/test_mvp_e2e.py

# Runner tests only
pytest tests/test_runners_io.py

# Verb tests only
pytest tests/test_verbs_contracts.py -vv

# Tool adapter tests only
pytest tests/tools -q
```

Use this when debugging a specific failing batch.

### Rerun Specific Test

```bash
# By test name
pytest tests/test_mvp_e2e.py::test_hello_world -v

# By test file and function
pytest tests/test_runners_io.py::test_apply_writes_files -v
```

Use this when debugging a specific failing test case.

### Skip Failing Batches

Edit `scripts/run_test_batches.sh` and comment out failing batch:

```bash
pytest tests/test_mvp_e2e.py
pytest tests/test_runners_io.py
# pytest tests/test_verbs_contracts.py -vv  # Skip until schema_utils fixed
pytest tests/tools -q
```

---

## Troubleshooting

### Issue: "No module named 'schema_utils'"

**Batch affected**: `test_verbs_contracts.py`

**Cause**: Missing internal module (not in `setup.py` or `pyproject.toml`)

**Workaround**: Skip batch by commenting out line in `scripts/run_test_batches.sh`:
```bash
# pytest tests/test_verbs_contracts.py -vv
```

**Fix**: Add `schema_utils` to project or refactor `test_verbs_contracts.py`.

---

### Issue: Tests Skipped (Go/Rust/.NET)

**Batch affected**: `test_tools`

**Symptom**: `N passed, M skipped in X.XXs`

**Cause**: Required runtime not in PATH:
- Go tests require `go` command
- Rust tests require `cargo` command
- .NET tests require `dotnet` command

**Verify runtimes**:
```bash
go version        # Check Go available
cargo --version   # Check Rust available
dotnet --version  # Check .NET available
```

**Fix**: Install missing runtimes or skip those tests.

---

### Issue: Batch Script Exits Early

**Symptom**: Script stops after first failing batch

**Cause**: `set -e` flag in script causes exit on first error

**Workaround**: Remove `set -e` from `scripts/run_test_batches.sh`:
```bash
#!/usr/bin/env bash
set -uo pipefail  # Remove -e flag

pytest tests/test_mvp_e2e.py || true
pytest tests/test_runners_io.py || true
pytest tests/test_verbs_contracts.py -vv || true
pytest tests/tools -q || true
```

**Trade-off**: All batches run, but failures not immediately visible in exit code.

---

### Issue: Slow Tool Adapter Tests

**Batch affected**: `test_tools`

**Symptom**: `pytest tests/tools` takes >10 seconds

**Cause**: Multi-language compilation overhead (Go modules, Rust crates, .NET SDK)

**Optimize**:
1. Cache compiled artifacts:
   ```bash
   # Cache Go modules
   export GOCACHE=/tmp/go-build-cache

   # Cache Cargo builds
   export CARGO_TARGET_DIR=/tmp/cargo-target
   ```

2. Skip slow runtimes:
   ```bash
   pytest tests/tools -k 'not rust and not dotnet'
   ```

---

## CI Integration

### GitHub Actions Example

```yaml
name: Test Batches

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.13'
      - name: Install dependencies
        run: |
          python -m venv .venv
          . .venv/bin/activate
          pip install -e .
      - name: Run test batches
        run: make test-batches
```

---

## Extending Batch System

### Adding New Batch

Edit `scripts/run_test_batches.sh`:

```bash
pytest tests/test_mvp_e2e.py
pytest tests/test_runners_io.py
pytest tests/test_verbs_contracts.py -vv
pytest tests/tools -q
pytest tests/integration -v  # New batch
```

### Parallel Batches (Advanced)

Replace sequential execution with parallel:

```bash
#!/usr/bin/env bash
set -euo pipefail

pytest tests/test_mvp_e2e.py &
pytest tests/test_runners_io.py &
pytest tests/test_verbs_contracts.py -vv &
pytest tests/tools -q &

wait  # Wait for all background jobs
```

**Trade-offs**:
- Faster runtime (concurrent execution)
- Harder to debug (interleaved output)
- May cause resource contention

---

## Batch vs Full Pytest

| Aspect | Batch Script | Full Pytest |
| --- | --- | --- |
| **Runtime** | ~2.6s | ~2.0s |
| **Isolation** | High (separate invocations) | Low (single process) |
| **Debugging** | Easy (clear batch boundaries) | Hard (mixed output) |
| **Exit codes** | First failure stops script | All tests run unless `-x` flag |
| **Output** | Verbose (per-batch summaries) | Compact (single summary) |
| **CI suitability** | High (good for large suites) | Medium (may timeout) |

**Recommendation**: Use batch script for development and CI; use full pytest for quick validation.

---

## Known Issues

1. **test_verbs_contracts.py import error**
   - Status: Open
   - Impact: Batch 3 always fails
   - Workaround: Comment out in batch script

2. **Runtime detection incomplete**
   - Status: Open
   - Impact: Tool adapter tests skip silently if `go`/`cargo`/`dotnet` unavailable
   - Workaround: Check `which go && which cargo && which dotnet` before running

---

## References

- **Batch script**: `scripts/run_test_batches.sh`
- **Makefile target**: `Makefile:23` (`test-batches` target)
- **Execution plan**: `docs/execution-plan.md` (Wave 2 CI batching tasks)
- **Test harnesses**: `tests/tools/test_*_adapters.py`

---

**Last updated**: 2025-09-29