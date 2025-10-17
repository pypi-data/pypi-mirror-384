# Go Adapter Smoke-Test Blueprint

This note captures the test harness that validates generated Go adapters.

## Objectives
- Exercise each adapter’s exported `Handle(map[string]interface{}) map[string]interface{}` function without requiring network access unless explicitly mocked.
- Run tests via standard tooling (`GO111MODULE=on go test`) so they integrate with `scripts/run_test_batches.sh`.
- Keep fixtures lightweight and deterministic, mirroring the Node harness structure.

## Harness Overview
1. **Discovery**: `tests/tools/test_go_adapters.py` enumerates `tools/*/adapters/adapter_go.go` and cross-references JSON fixtures.
2. **Execution**: For each case, the harness copies the adapter into a temporary workspace alongside a generated runner (`runner_main.go`) and invokes `go run adapter_go.go runner_main.go '<payload>'`.
3. **Assertions**: Adapter output is decoded from stdout and compared against fixture-defined subsets, matching the taxonomy used by Node tests.

## Fixtures
- Request/response pairs live under `tests/fixtures/go_adapters/<tool>.json` (e.g., `loop.json`).
- Each entry declares `payload` and `expected` objects; optional metadata fields may be introduced later for skips/networking.

## Integration
- Harness integrates with the existing `pytest tests/tools` batch (invoked by `scripts/run_test_batches.sh`).
- `GO_BIN` environment variable overrides the default `go` binary if needed.
- Helper functions mirror the Node subset comparison logic for consistency.

## Open Questions
- How to tag network-dependent adapters so fixtures can skip them or inject httptest servers.
- Whether to upstream shared helper functions (e.g., response builders) into a common Go support library.
- How to extend the harness when adapters require additional files (multiple Go sources) beyond `adapter_go.go`.

Track progress in `docs/execution-plan.md` under Adapter Packaging Notes and the Tooling & Tests backlog.
