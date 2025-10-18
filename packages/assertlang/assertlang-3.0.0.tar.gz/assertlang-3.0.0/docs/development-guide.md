# Development Guide

## Core
- Implement MCP verbs: `plan.create@v1`, `fs.apply@v1`, `run.start@v1`, `validate.check@v1`, `report.finish@v1`
- Default port: 23456 (fallback to leased high ports when binding is denied)
- All verbs exposed via JSON-RPC 2.0 / JSON envelopes

## Language Bindings
- Python, Rust, Go, TypeScript
- Each tool has language adapters with flags (`--python`, `--go`, etc.)

## Runner Protocol Essentials
- Runners communicate via stdin/stdout JSON envelopes (`{"ok": bool, "version": "v1", ...}`).
- Methods to support: `apply`, `start`, `stop`, `health`; emit exactly one JSON payload per call.
- Populate `error.code` with `E_BUILD`, `E_RUNTIME`, etc., so the daemon can distinguish failure modes.

## Testing Notes
- `pytest tests/test_toolgen_templates.py -q` checks that every language template stays syntactically valid.
- Dotnet compilation smoke tests are opt-in: export `PROMPTWARE_RUN_DOTNET_SMOKE=1` before running pytest to compile generated C# adapters with the local `dotnet` CLI.

## Containers
- Use Docker/ContainerD for sandbox isolation
- Ephemeral containers spun up per `run`
- Auto-cleanup on `report.finish`

## Sub-Agents
- Parallel execution allowed (multi-runner race model)
- Coordinator merges results, chooses best outcome

## Security
- Limited permissions
- Ephemeral volumes only
- No host network by default
