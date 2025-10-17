# .NET Adapter Smoke-Test Notes

The .NET harness mirrors the Node/Go/Rust suites by compiling adapters in disposable projects and executing their `Handle` method.

## Harness Overview
- Test entry point: `tests/tools/test_dotnet_adapters.py`.
- Fixtures: JSON request/response pairs under `tests/fixtures/dotnet_adapters/` (e.g., `loop.json`).
- Each test run creates a temporary SDK-style project, copies the adapter as `Adapter.cs`, writes a small `Program.cs` runner, and invokes `dotnet run --configuration Release -- payload.json`.
- Payloads are written to disk so we don’t fight CLI argument parsing; the runner reads the file, converts to dictionaries/lists, calls `Adapter.Handle`, and prints the serialized response.
- The harness honours `DOTNET_BIN` for alternate SDK installs (default `dotnet`).

## Requirements
- .NET SDK 8.0+ installed locally. If the stock `dotnet` on the PATH fails, point `DOTNET_BIN` at an alternative install (e.g., one created via `dotnet-install.sh`).
- Standard BCL only—adapters must avoid external NuGet dependencies. Extensions would require project templating.

## Open Questions
- Should we share common C# utilities (JSON conversion helpers) across runners instead of regenerating them per workspace?
- How to tag adapters that need additional assets (e.g., extra C# files) so the harness includes them.
- Whether we want to add a `dotnet build` step separate from `dotnet run` for faster iteration once more fixtures exist.

Progress is tracked in `docs/execution-plan.md` and `TODO.md` (Tooling & Tests backlog).
