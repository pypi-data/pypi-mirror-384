# Node Adapter Template Spec

This guide establishes the canonical structure for toolgen-generated Node adapters so every tool ships with a consistent, production-ready runtime stub.

## Goals
- Single-file CommonJS module located at `tools/<package>/adapters/adapter_node.js` (package name derived from `_package_name(tool_id)`).
- Zero external dependencies; rely on the daemon bootstrap to provision Node ≥18 with global `fetch`.
- Stable response contract: `{ ok: boolean, version: 'v1', data?, error? }`.
- Deterministic smoke tests runnable via plain `node` without bundlers.

## File Layout
```
tools/
  <package>/
    adapters/
      adapter_node.js
```
- `<package>` is `tool_id` with hyphens replaced by underscores (e.g., `api-auth` → `api_auth`).
- Additional assets (schemas, docs) remain tool-specific and are not duplicated per language.

## Module Surface
- Export `VERSION = 'v1'` and a single `handle(request)` function via `module.exports`.
- `handle` may be async (e.g., HTTP client) or sync; prefer async when performing I/O.
- Requests must be validated defensively:
  - Reject non-object requests with `{ ok: false, error: { code: 'E_SCHEMA', ... } }`.
  - Use `E_ARGS` for missing/invalid parameters, `E_UNSUPPORTED` for unknown enum values, `E_NETWORK` for transport failures.
- Successful calls return `{ ok: true, version: VERSION, data: <payload> }`.
- Keep runtime logging out of adapters; the daemon emits timeline events already.

## Error Helpers (Optional)
Simple helper functions (`ok`, `error`) are allowed if they remain file-local and do not introduce external dependencies.

## Environment Assumptions
- Node 18+ (global `fetch`, `AbortController`).
- No dynamic `import`. Stick with CommonJS so the daemon can `require` modules without transpilation.
- Avoid filesystem writes except when the tool explicitly models file output.

## Packaging Decision
- Do **not** generate per-tool `package.json`; adapters stay dependency-free and loadable via `require`.
- When a tool needs third-party packages, surface them through plan `dep node <group>` entries so the daemon bootstrap installs them once.
- Central daemon logic remains responsible for Node version pinning and cache reuse; adapters should not attempt self-managed installs.

## Smoke Test Expectations
Create `tests/tools/test_<tool>_node.py` style checks that:
1. Load the adapter via `import importlib.util` + `node` subprocess or reuse existing `ToolRunner` harness if available.
2. Execute `handle` with representative payloads and assert response shape.
3. Verify error paths (missing args, invalid enums).

For ad-hoc validation, run:
```
node -e "const a = require('./tools/api_auth/adapters/adapter_node'); console.log(a.handle({ type: 'apiKey', token: 't' }));"
```

Automated coverage is provided by `pytest tests/tools/test_node_adapters.py`, which discovers fixtures in `tests/fixtures/node_adapters/`.

## Open Questions
- Should adapters expose TypeScript typings for host SDK consumption?
- What pattern should we adopt for streaming/large payloads without buffering in memory?
- Can we share common validation helpers across adapters without introducing cross-file imports?

Track resolutions in `docs/execution-plan.md` under “Adapter Packaging Notes”.
