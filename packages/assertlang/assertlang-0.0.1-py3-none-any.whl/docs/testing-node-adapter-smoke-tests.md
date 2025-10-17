# Node Adapter Smoke-Test Blueprint

Wave 2 introduces runtime-level checks for generated Node adapters. This blueprint captures the harness design before wiring new tests into CI.

## Objectives
- Execute each adapter’s `handle` function in-process via Node to validate success and error paths.
- Keep tests hermetic (no outbound network) by stubbing fetch/file operations where needed.
- Integrate with `scripts/run_test_batches.sh` under the `tools` batch.

## Implementation
- Harness lives in `tests/tools/test_node_adapters.py` and runs once per test suite, iterating through JSON-defined cases.
- Fixtures reside under `tests/fixtures/node_adapters/` (e.g., `api_auth.json`) and declare success/error expectations.
- Runtime lookup honours the `NODE_BIN` environment variable (defaults to `node`).

## Harness Design
1. **Discovery**: Python test scans `tools/*/adapters/adapter_node.js` and skips adapters that require network I/O.
2. **Invocation**: For each adapter, emit a temporary JS runner:
   ```js
   const { handle } = require(process.argv[2]);
   const payload = JSON.parse(process.argv[3]);
   Promise.resolve(handle(payload))
     .then(result => { console.log(JSON.stringify(result)); })
     .catch(err => { console.error(err); process.exit(1); });
   ```
3. **Execution**: Invoke via `node runner.js <adapter_path> '<payload>'` using `subprocess.run`.
4. **Assertions**: Parse stdout JSON in pytest and assert:
   - `ok` flag aligns with expectation.
   - `version === 'v1'`.
   - Error codes match taxonomy (`E_SCHEMA`, `E_ARGS`, etc.).

## Fixtures
- Provide representative payloads per tool under `tests/fixtures/node_adapters/<tool>.json`.
- Include negative cases (missing required fields) to ensure error handling stays intact.

## Integration Points
- `test_node_adapters.py` sits in `tests/tools/`; it runs as part of the existing `pytest tests/tools` batch (invoked by `scripts/run_test_batches.sh`).
- Harness respects the `NODE_BIN` environment variable for alternate Node installations.
- `docs/toolgen-node-adapter-template.md` references `pytest tests/tools/test_node_adapters.py` for manual execution guidance.

## Outstanding Work
- Define strategy for adapters that perform outbound network requests (mock fetch? local test server?).
- Decide whether to cache the temporary runner script or generate per test invocation.
- Measure execution time to ensure batch stays within macOS sandbox limits.

Track implementation progress in `docs/execution-plan.md` (CI batching + Toolgen templates sections).
