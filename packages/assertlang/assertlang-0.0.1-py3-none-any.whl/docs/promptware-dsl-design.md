# AssertLang DSL Design (Draft)

## 1. Goals
- Provide a concise, agent-friendly orchestration language across the AssertLang verbs (`plan`, `apply`, `run`, `validate`, `report`).
- Keep dataflow explicit so agents can reason about intermediate state, retries, and fan-in/out without bespoke glue code.
- Ship tooling parity: parser, formatter, linter, interpreter, and timeline telemetry must behave consistently across macOS/Linux hosts.
- Support incremental evolution toward a natural-language compiler while remaining production-worthy today.

## 2. Current Surface
Wave 1 delivers the following constructs (see `docs/promptware-dsl-spec.md` for the formal grammar):

- **Metadata directives**: `lang`, `start`, `prompt`, `assume`, `dep`, and `tool` configure the execution environment.
- **Files**: `file <path>:` blocks capture source artefacts; indentation inside the block is preserved verbatim.
- **Calls**: `call <alias> key=value …` with `expect.*` assertions, retry hints, and optional `as <result>` aliases.
- **Assignments**: `let <target> = <value>` store literals or references (`${alias.path}`) for later steps.
- **Conditionals**: `if/else` branches evaluate Python expressions with `${…}` substitutions.
- **Parallelism**: `parallel:` with named `branch` blocks executes sibling scopes that inherit parent state.
- **State scopes**: `state <name>:` runs a nested plan and exposes its responses under `responses["<name>"]`.
- **Fan-out**: `fanout <alias>:` with `case <expr?>:` blocks slugifies case labels and records branch metadata.
- **Fan-in**: `merge` directives support `append`, `collect`, and `dict` modes, each emitting `sources`, `mode`, and optional `append_key` metadata.
- **Dataflow helpers**: `input.from=alias.output` and dotted/indexed payload keys compile into nested JSON structures; inline `{key: value}` and `[item, …]` literals round-trip through the formatter.

Formatter and linter parity:
- Canonical two-space indentation, blank-line separation between logical sections, and stable ordering of metadata and tool directives.
- Lint warnings for empty control blocks, missing `start` commands when files exist, absent expectations on tool calls, and suspicious fan-in (e.g., `merge append` without a list-like source).

## 3. Execution Semantics
1. **Parsing** (`language/parser.py`) emits `{ prompt?, plan? }`, normalising payloads, retries, and references. `PWParseError` exposes `code` (`E_SYNTAX` or `E_PLAN_REF`) so tooling can surface contextual diagnostics.
2. **Formatting/Linting** (`language/dsl_utils.py`) round-trips `.pw` files and surfaces structural issues before a plan reaches the daemon.
3. **Interpretation** (`language/interpreter.py`) builds an internal step graph (`CallStep`, `FanoutStep`, `MergeStep`, etc.) and executes actions in-process. `PWExecutionError` now carries `code` values:
   - `E_PLAN`: invalid plan structure (missing targets, duplicate merge aliases, incorrect container types for assignments).
   - `E_PLAN_REF`: unresolved tool aliases or response references.
   - `E_RUNTIME`: downstream tool failures, expectation mismatches, merge type errors.
   Errors bubble into timeline events with the same `code`, aligning interpreter telemetry with daemon traces.
4. **Timelines**: every action records `{ phase/action, status, duration_ms?, attempt?, branches?, cases?, mode?, append_key? }`. Fan-out events list executed case labels with original conditions; merge events annotate the mode and append bucket.

## 4. Diagnostics & Error Codes
| Code | Producer | Typical Trigger |
| --- | --- | --- |
| `E_SYNTAX` | Parser | Mixed indentation, malformed directives, missing arguments. |
| `E_PLAN` | Interpreter validation | `let` without target, merge bucket collisions, list/dict assignment misuse. |
| `E_PLAN_REF` | Parser / interpreter | `call` referencing undefined tools, `${unknown.alias}` lookups. |
| `E_RUNTIME` | Interpreter execution | Tool error responses, failed `expect.*` assertions, merge type mismatches. |

Timeline payloads include the same `code` when `status == "error"`, giving downstream consumers a stable taxonomy regardless of whether the failure originated in the daemon or interpreter.

## 5. Wave 1 Wrap-Up & Next Steps
- ✅ Grammar coverage now includes state scopes, fan-out, merge modes, inline collections, and dataflow helpers. Golden fixtures in `tests/dsl_fixtures/` cover each construct.
- ✅ Interpreter orchestrates plans via the step graph, logging retry attempts and merge metadata.
- ✅ Documentation refreshed (`docs/promptware-dsl-spec.md`, this file) to describe the shipped behaviour and lint rules.
- 🔜 Wave 2+ priorities: cross-language adapter templates, host SDKs, richer policy enforcement, and the natural-language prompt compiler.

Keep this design note synced with parser/interpreter changes so new contributors understand the contract between syntax, runtime semantics, and telemetry.
