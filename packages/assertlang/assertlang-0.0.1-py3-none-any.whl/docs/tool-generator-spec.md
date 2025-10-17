# Tool Generator Specification

## Purpose
Design a single "tool generator" node that can author new AssertLang tools from a declarative spec. The generator should become the canonical way to produce and evolve the 36 core tools (and marketplace extensions) while keeping MCP envelopes, schemas, adapters, and tests in sync.

## Inputs (Generator Specification)
A generator run consumes a `toolgen.yaml` (or JSON) manifest with these sections:

- `tool`: id (`logger`), display name, summary, category (2/3/4/5/6 families), and MCP version (`v1`).
- `envelope`: switches for `health`, `capabilities`, streaming, and whether the tool is long-running.
- `schema`:
  - `$ref`s to shared fragments (e.g. `schema/fragments/lang.v1.json`).
  - Request/response definitions (merged into `/schemas/tools/<tool>.v1.json`).
  - Shared fields toggles (`lang`, `adapter`, `runtime`, `limits`, `deps`, `egress`).
- `operations`: list of sub-commands (e.g. `connect`, `send`, `close` for websocket) with descriptions and examples.
- `adapters`: per language runtime instructions:
  - `language`: `python|node|go|rust|java|dotnet|cpp`.
  - `template`: which adapter template to render (`rest-client`, `fs`, etc.).
  - `deps`: language-specific dependencies (pip packages, npm packages, go modules, nuget packages, cargo crates, maven artifacts).
  - `entry`: optional override for command to execute at runtime.
- `policy`: declare required capabilities (network, fs, secrets), egress defaults, allowlists, timeouts, retry strategies.
- `telemetry`: log events to emit, tracers to call, metrics buckets.
- `testing`: generated test cases, fixtures, or harness expectations.
- `docs`: quickstart text, usage examples, related tools.
- `marketplace`: metadata for publishing (tags, version, compatibility matrix).

### Template Library (Python)

- `stdout_logger` — emit structured log envelope (`logger`, `custom-tool-template`, etc.).
- `rest_client` — compose base/path URLs and issue HTTP requests (`rest`).
- `http_client` — generic HTTP fetcher (`http`).
- `auth_header` — generate API key / JWT headers (`auth`, `api-auth`).
- `json_validator` — validate JSON payloads with `jsonschema` (`validate-data`).
- `conditional_eval` — evaluate equality/regex conditions (`conditional`).
- `loop_counter` — count items (`loop`).
- `branch_select` — choose case/default branches (`branch`).
- `timing_sleep` — measure sleep durations (`timing`).
- `input_file` / `output_writer` — read/write files or stdout (`input`, `output`).
- `hash_utility` — compute SHA-256 hashes (`encryption`).
- `rest_client` / `http_client` — network clients for REST/HTTP tools.
- `tracer_simple`, `thread_simulator`, `async_simulator`, `scheduler_simulator` — control-flow simulators.
- `error_status`, `error_log_scanner`, `plugin_manager`, `marketplace_uploader`, `custom_template_helper`, `noop_ok` — misc helpers for admin tools.

> Additional language templates follow the same naming; use `_package_name` (tool id → package-safe) when referencing adapters. See `docs/toolgen-template-catalog.md` for the up-to-date inventory of specs and rendered templates.
>
> Runtime-specific conventions now live in dedicated guides:
> - Node (`docs/toolgen-node-adapter-template.md`)
> - Go (`docs/toolgen-go-adapter-template.md`)
> - Rust (`docs/toolgen-rust-adapter-template.md`)
> - .NET (`docs/toolgen-dotnet-adapter-template.md`)

## Outputs (Generator Artifacts)
For each tool spec the generator produces:

1. **Schema**: `schemas/tools/<tool>.v1.json` (or updates existing) including common envelope fields and custom request/response.
1. **Adapters**: code stubs under `tools/<tool>/adapters/` for each language listed. Templates reside in `templates/adapters/<language>/<kind>.tmpl`.
1. **Runner Glue**: optional shared Python harness in `tools/<tool>/__init__.py` that uses adapters or direct logic (similar to `tools/base.py`).
1. **Registry Entry**: append/update the tool record in `data/tools_registry.json` (id, summary, envelope, policy, adapter deps) for CLI/daemon discovery.
1. **Tests**:
   - Contract tests under `tests/tools/test_<tool>.py` verifying schema validation and sample executions.
   - Runner integration tests that exercise the generated adapters via `run_tool` when applicable.
1. **Docs**: Markdown summary in `docs/tools/<tool>.md` referencing schema, envelope, and examples. Update aggregate docs (`docs/tool-specifications.md`).
1. **CI Hooks**: append tests to coverage manifests (e.g. `pyproject.toml` extra dependencies) and ensure lint/test commands include new files.

## Generator Workflow
1. Parse spec → validate against `toolgen.spec.schema.json`.
2. Merge default fragments (shared request fields, error codes) into tool schema.
3. Render adapter templates, injecting metadata (method enums, flags, env scaffolds, dependency instructions).
4. Emit tests using defined operations/examples; stub out HTTP mocks when `network: deny` policies are set.
5. Update docs/registry in a transactional write (support `--dry-run`).
6. Run formatters (Black, Prettier, gofmt, dotnet format, rustfmt) when adapters are created.

## Hooks for MCP Runtime
- Generator annotates dependency data so `run_start_v1` can prepare environments (e.g. Python requirements → `deps.python.requirements`).
- Policy section determines runtime enforcement (exposed to the daemon for allowlist checks).
- Telemetry config defines which events the daemon should expect (log channel names, trace spans).
- Capabilities/health toggles ensure each tool advertises MCP-level readiness before first use.
- `data/tools_registry.json` is consumed by the daemon to merge default env/dependency settings whenever plans omit them. The CLI and MCP runtime load generated adapters dynamically based on the sanitized package name returned by `_package_name(tool_id)`.

## Extensibility Considerations
- Support composition: generator should embed sub-tool calls by referencing other tool specs.
- Allow partial regeneration (e.g. `toolgen update --schema` to only refresh JSON schema).
- Maintain newline/format stability to keep diffs clean.
- Provide migration strategy when schemas bump versions (`v2` etc.).

## Next Steps
1. Author `toolgen.spec.schema.json` describing the manifest structure.
2. Build `promptware toolgen` CLI that validates the manifest and renders the artifacts above.
3. Pilot with the Logger tool spec, then expand to the rest of the catalog.
