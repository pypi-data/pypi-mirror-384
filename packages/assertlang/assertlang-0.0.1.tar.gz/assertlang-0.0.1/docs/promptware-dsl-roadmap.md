# AssertLang DSL Roadmap

This living outline captures the steps required to turn AssertLang into a full programming language that orchestrates the 36 tools across heterogeneous runtimes.

## Phase A — Grammar & Authoring Experience
- Define a minimal DSL grammar: program metadata, sequential tool invocations, dataflow wiring (`alias`, `input.from`, fan-in/out), error/retry clauses.
- Build a parser that emits the existing plan JSON (`files`, `deps`, `start`) so `.pw` files round-trip through the current daemon.
- Provide a formatter/linter for fast author feedback before invoking the daemon.
- Autogenerate runnable Python scaffolds when authors describe tool calls (e.g., `tool http as fetch` + `call fetch method=GET ...`) to keep getting-started paths tight.

## Phase B — Cross-Language Adapters
- Extend toolgen specs with Node, Go, Rust, and .NET templates for the high-usage tools (http, storage, logger, transform, validate).
- Ensure `run_start_v1` selects the appropriate adapter based on plan language and merges allowlisted deps automatically.
- Publish SDK shims (Python/Node first) that wrap MCP verbs so external code can participate bidirectionally.

## Phase C — Execution Orchestrator
- Implement a coordinator loop that executes multi-step plans, maintains state, supports branching/retries, and marshals outputs back into `report.finish_v1`.
- Reuse existing tools as primitives; add state helpers (e.g., KV store tool) if required.
- Integrate health/telemetry so long-running programs stay within policy (timeouts, network, cache control).

Keep this file updated as phases complete or new requirements emerge.
