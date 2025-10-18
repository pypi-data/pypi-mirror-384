# Rust Adapter Smoke-Test Blueprint

This document describes the smoke harness that exercises generated Rust adapters.

## Goals
- Execute each adapter’s `handle(&serde_json::Value) -> serde_json::Value` implementation with deterministic fixture payloads.
- Avoid global `cargo build` on the entire repository; instead spin up disposable workspaces so tests stay hermetic.
- Mirror the Node/Go harness conventions for fixtures, subset assertions, and environment overrides.

## Harness Overview
1. **Discovery**: `tests/tools/test_rust_adapters.py` enumerates `tools/*/adapters/adapter_rust.rs` and cross-references fixtures under `tests/fixtures/rust_adapters/`.
2. **Workspace Setup**: For each case, the harness materialises a temporary Cargo project that copies the adapter source to `src/adapter.rs`, writes a lightweight runner in `src/main.rs`, and injects a minimal `Cargo.toml` with `serde`/`serde_json` dependencies.
3. **Execution**: The runner invokes the adapter’s `handle` function with the JSON payload via `cargo run --quiet -- '<payload>'`, returning the serialized response on stdout.
4. **Assertions**: Harness decodes stdout to JSON and compares it against fixture-defined subsets, mirroring the helper logic used by Node/Go harnesses.

## Fixtures
- Store request/response cases in `tests/fixtures/rust_adapters/<tool>.json`.
- Each entry contains `payload`, `expected`, and optional `network`/`skip` flags for adapters that require additional setup.

## Integration
- Harness ships as `tests/tools/test_rust_adapters.py` and runs with the standard `pytest tests/tools` batch (invoked by `scripts/run_test_batches.sh`).
- The `CARGO_BIN` environment variable can override the cargo binary if alternate toolchains are desired.
- Temporary workspaces are cleaned up automatically after each case.

## Open Questions
- How to share a common Cargo template (e.g., under `tests/_support`) so workspace generation stays consistent.
- Whether to enable async adapters (requiring `tokio`) or keep the harness synchronous for now.
- Strategy for handling adapters that depend on additional Rust sources beyond `adapter_rust.rs` (e.g., helper modules).

Progress is tracked in `docs/execution-plan.md` and the Tooling & Tests backlog.
