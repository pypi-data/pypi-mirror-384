# Rust Adapter Template Spec

Defines the structure and expectations for toolgen-generated Rust adapters so multi-runtime tooling remains consistent.

## Goals
- Emit a single Rust source file at `tools/<package>/adapters/adapter_rust.rs`.
- Provide `pub const VERSION: &str = "v1";` and `pub fn handle(request: &serde_json::Value) -> serde_json::Value`.
- Keep adapters dependency-light (prefer `serde_json`, `reqwest`, `chrono` only when required).
- Support both pure data transforms and network calls without leaking implementation details to callers.

## File Layout
```
tools/
  <package>/
    adapters/
      adapter_rust.rs
```
- `<package>` derives from `_package_name(tool_id)` (e.g., `api-auth` → `api_auth`).
- Additional language-neutral assets live alongside but are not referenced directly by Rust code.

## Module Surface
- Expose helpers like `ok` / `error` as private functions within the file; avoid cross-file modules.
- Incoming payload arrives as `&Value`; guard against non-object input with `E_SCHEMA`.
- Prefer explicit extraction helpers (e.g., `request.get("field").and_then(Value::as_str)`).
- Propagate errors using taxonomy: `E_ARGS`, `E_UNSUPPORTED`, `E_RUNTIME`, `E_NETWORK`.
- Successful responses return `serde_json::json!({ "ok": true, "version": VERSION, "data": ... })`.

## Environment & Packaging
- No committed `Cargo.toml`. The daemon generates an ephemeral workspace that lists adapters as binaries and pins approved crates.
- Allowed base crates: `serde`, `serde_json`, `reqwest`, `chrono`. New crates must be added to the dependency allowlist before use.
- Target toolchain: Rust 1.75+ with `cargo` available (pre-provisioned during dependency bootstrap).
- Avoid `async` for now; use blocking clients to simplify smoke-test harnesses.

## Smoke Test Guidance
- During Wave 2, introduce generated `_test.rs` files (or template-driven tests) that:
  1. Construct representative `Value` payloads.
  2. Call `handle` and assert success/error cases.
  3. Run under `cargo test --package promptware_adapters --bin <tool>_adapter` (harness will fill in package/bin names).
- Until tests land, quick manual validation:
```
cargo run --bin adapter -- tools/api_auth/adapters/adapter_rust.rs <<'JSON'
{"type":"apiKey","token":"t"}
JSON
```
  (A future harness will streamline this invocation.)

Automated smoke coverage is now provided by `pytest tests/tools/test_rust_adapters.py`, which materialises a disposable Cargo project per adapter, executes it via `cargo run`, and validates responses using fixtures in `tests/fixtures/rust_adapters/`.

## Open Questions
- Do we want to expose a shared crate of helper utilities (`promptware_adapter_support`) to reduce duplication?
- Should we enable `async` + `tokio` once the daemon supports async runtimes?
- How will we stub network calls for deterministic smoke tests?

Track decisions and follow-up actions in `docs/execution-plan.md` under Adapter Packaging Notes.
