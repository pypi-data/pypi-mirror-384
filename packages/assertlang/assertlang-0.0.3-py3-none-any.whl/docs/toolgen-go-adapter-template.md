# Go Adapter Template Spec

Defines the canonical structure for toolgen-generated Go adapters so every tool exposes a consistent Go surface area.

## Goals
- Emit a single Go source file at `tools/<package>/adapters/adapter_go.go`.
- Provide a simple entrypoint (`Handle`) returning `map[string]interface{}` compatible with the daemon bridge.
- Avoid external dependencies beyond the Go standard library.
- Keep the code Go 1.20+-compatible and runnable with `GO111MODULE=on`.

## File Layout
```
tools/
  <package>/
    adapters/
      adapter_go.go
```
- `<package>` derives from `_package_name(tool_id)` (e.g., `api-auth` → `api_auth`).
- Additional assets remain language-agnostic; Go code lives solely in the adapters folder.

## Module Surface
- Declare `package main` to align with the existing dynamic loader which builds via `go build` on the fly.
- Export `const Version = "v1"` (string) and `func Handle(map[string]interface{}) map[string]interface{}`.
- Validate request types defensively:
  - Return `{ "ok": false, "version": Version, "error": { "code": "E_SCHEMA", ... } }` for non-object payloads.
  - Use `E_ARGS` for invalid argument shapes, `E_UNSUPPORTED` for unsupported enums, `E_NETWORK`/`E_RUNTIME` for runtime failures.
- Successful responses must return `{ "ok": true, "version": Version, "data": ... }` mirroring other runtimes.

## Coding Conventions
- Prefer explicit type assertions (`value, ok := req["field"].(string)`).
- Use dedicated helpers when shaping responses if repeated more than twice.
- Ensure `defer` cleanups for network/IO resources (e.g., `resp.Body.Close()`).

## Environment Assumptions
- Go 1.20 or newer with modules enabled.
- No third-party imports; if a tool requires them, surface through plan dependency declarations so the daemon handles vendoring.
- Compilation happens in a temporary workspace managed by the daemon; adapters should not rely on GOPATH.

## Packaging & Build
- Do **not** generate per-tool `go.mod`; the daemon constructs ephemeral modules when invoking `go build`/`go test`.
- Generated code must compile with `go build ./tools/<package>/adapters` when executed inside the repo root with the ephemeral module.
- Keep exported names stable to allow future shared harnesses (`Handle`, `Version`).

## Smoke Test Guidance
- Generate companion `_test.go` files during Wave 2 that:
  1. Build a sample request map and call `Handle` directly.
  2. Assert both success and error paths.
  3. Run via `GO111MODULE=on go test ./tools/<package>/adapters` within the test harness.
- Until automated tests exist, quick manual validation:
```
GO111MODULE=on go test ./tools/api_auth/adapters -run TestHandleSmoke
```
  (Harness-supplied `_test.go` files will surface `TestHandleSmoke` and similar checks.)

Automated smoke coverage now runs through `pytest tests/tools/test_go_adapters.py`, which copies adapters into a temporary workspace and executes them via `go run` using fixtures in `tests/fixtures/go_adapters/`.

## Open Questions
- Should we convert adapters to `package adapter` and expose an additional `Main()` for CLI usage?
- Do we need shared helper libraries (e.g., response builders) to reduce duplication once generics land?
- How will we flag network-dependent adapters so smoke tests can provide httptest servers or skip them gracefully?

Track these decisions in `docs/execution-plan.md` under Adapter Packaging Notes.
