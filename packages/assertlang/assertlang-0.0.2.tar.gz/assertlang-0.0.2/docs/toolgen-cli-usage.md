# Toolgen CLI Usage

The `toolgen` CLI generates AssertLang tool artifacts (schemas, adapters, tests, docs) from YAML tool specifications.

---

## Basic Usage

```bash
python3 cli/toolgen.py <spec_file> [OPTIONS]
```

### Required Arguments

- `spec_file` — Path to a YAML tool specification file (e.g., `toolgen/specs/http.tool.yaml`)

### Options

- `--output <path>` — Output directory for generated artifacts (default: `.mcpd/toolgen`)
- `--dry-run` — Show planned artifacts without writing files

---

## Multi-Language Adapter Generation

Toolgen automatically generates adapters for **all languages** declared in the `adapters` section of your tool spec. There are no language-specific CLI flags.

### Supported Languages

- `python` — Python 3.9+ adapters
- `node` — Node.js 18+ adapters (CommonJS)
- `go` — Go 1.19+ adapters
- `rust` — Rust 1.70+ adapters
- `dotnet` — .NET 7+ adapters (C#)

### Template Selection

Each adapter entry in the spec declares:
1. **Language** — The target runtime (`python`, `node`, `go`, `rust`, `dotnet`)
2. **Template** — The template name to render (e.g., `http_client`, `json_validator`)
3. **Dependencies** — Language-specific package requirements

### Example Spec: Multi-Language HTTP Tool

```yaml
tool:
  id: http
  name: HTTP Tool
  summary: Perform HTTP requests with configurable headers, body, and timeout.
  category: specialized
  version: v1

adapters:
  - language: python
    template: http_client
    deps:
      python:
        requirements: [requests>=2.31]

  - language: node
    template: http_client
    deps:
      node:
        packages: []

  - language: go
    template: http_client
    deps:
      go:
        modules: []

  - language: rust
    template: http_client
    deps:
      rust:
        crates: [reqwest, serde_json]

  - language: dotnet
    template: http_client
    deps:
      dotnet:
        packages: []
```

Running `python3 cli/toolgen.py toolgen/specs/http.tool.yaml` generates:
- `schemas/tools/http.v1.json` — JSON Schema definition
- `tools/http/adapters/adapter_python.py` — Python adapter
- `tools/http/adapters/adapter_node.js` — Node.js adapter
- `tools/http/adapters/adapter_go.go` — Go adapter
- `tools/http/adapters/adapter_rust.rs` — Rust adapter
- `tools/http/adapters/Adapter.cs` — .NET adapter
- `tests/tools/test_http.py` — Test harness
- `docs/tools/http.md` — Tool documentation
- `data/tools_registry.json` — Updated tool registry

---

## Generating Single-Language Tools

To generate adapters for only one language, include only that language in the `adapters` section:

```yaml
adapters:
  - language: python
    template: custom_logic
    deps:
      python:
        requirements: []
```

This produces only the Python adapter; no Node/Go/Rust/.NET files are created.

---

## Generated Artifact Locations

| Artifact Type | Path Pattern | Example |
| --- | --- | --- |
| Schema | `schemas/tools/<tool-id>.v1.json` | `schemas/tools/http.v1.json` |
| Python adapter | `tools/<pkg>/adapters/adapter_python.py` | `tools/http/adapters/adapter_python.py` |
| Node adapter | `tools/<pkg>/adapters/adapter_node.js` | `tools/http/adapters/adapter_node.js` |
| Go adapter | `tools/<pkg>/adapters/adapter_go.go` | `tools/http/adapters/adapter_go.go` |
| Rust adapter | `tools/<pkg>/adapters/adapter_rust.rs` | `tools/http/adapters/adapter_rust.rs` |
| .NET adapter | `tools/<pkg>/adapters/Adapter.cs` | `tools/http/adapters/Adapter.cs` |
| Tests | `tests/tools/test_<pkg>.py` | `tests/tools/test_http.py` |
| Docs | `docs/tools/<tool-id>.md` | `docs/tools/http.md` |
| Registry | `data/tools_registry.json` | (single file, updated incrementally) |

**Note**: `<pkg>` is the package name derived from `<tool-id>` by replacing hyphens with underscores (e.g., `api-auth` → `api_auth`). Reserved keywords like `async` get a `_tool` suffix.

---

## Template Reference

Each language has a set of pre-built templates. Templates are referenced by name in the `adapters[].template` field.

### Common Templates

| Template Name | Purpose | Languages |
| --- | --- | --- |
| `http_client` | HTTP request execution | python, node, go, rust, dotnet |
| `json_validator` | JSON Schema validation | python, node, go, rust, dotnet |
| `file_reader` | Read file contents | python, node, go, rust, dotnet |
| `storage_fs` | Filesystem storage operations (put/get/list/delete) | python, node, go, rust, dotnet |
| `rest_client` | REST API client with base URL | python, node, go, rust, dotnet |
| `transform_convert` | JSON ↔ YAML conversion | python, node, go, rust, dotnet |
| `auth_header` | Generate auth headers (API key, bearer) | python, node, go, rust, dotnet |
| `stdout_logger` | Structured logging to stdout | python, node, go |
| `error_log_collector` | Collect and summarize error logs | python, node, go, rust, dotnet |
| `loop_counter` | Iterate items and count iterations | python, node, go, rust, dotnet |
| `branch_select` | Conditional branching by value | python, node, go, rust, dotnet |
| `conditional_eval` | Simple condition evaluation (==, !=, regex) | python, node, go, rust, dotnet |
| `output_writer` | Write to stdout or files | python, node, go, rust, dotnet |
| `error_toggle` | Report error state toggles | python, node, go, rust, dotnet |
| `async_simulator` | Simulate async execution | python, node, go, rust, dotnet |
| `schema_stub` | Minimal schema-only stub | python |

See `docs/toolgen-template-catalog.md` for the full list of templates and their language coverage.

---

## Workflow Examples

### 1. Generate All Adapters for an Existing Tool

```bash
python3 cli/toolgen.py toolgen/specs/http.tool.yaml
```

**Output**:
```json
{
  "ok": true,
  "version": "v1",
  "data": {
    "written": [
      "schemas/tools/http.v1.json",
      "tools/http/adapters/adapter_python.py",
      "tools/http/adapters/adapter_node.js",
      "tools/http/adapters/adapter_go.go",
      "tools/http/adapters/adapter_rust.rs",
      "tools/http/adapters/Adapter.cs",
      "docs/tools/http.md",
      "tests/tools/test_http.py",
      "data/tools_registry.json"
    ]
  }
}
```

### 2. Preview Artifacts Without Writing Files

```bash
python3 cli/toolgen.py toolgen/specs/storage.tool.yaml --dry-run
```

**Output**:
```json
{
  "ok": true,
  "version": "v1",
  "data": {
    "planned": {
      "schema": "schemas/tools/storage.v1.json",
      "adapters": [
        "tools/storage/adapters/adapter_python.py",
        "tools/storage/adapters/adapter_node.js",
        "tools/storage/adapters/adapter_go.go",
        "tools/storage/adapters/adapter_rust.rs",
        "tools/storage/adapters/Adapter.cs"
      ],
      "tests": ["tests/tools/test_storage.py"],
      "docs": ["docs/tools/storage.md"],
      "registry": "data/tools_registry.json"
    }
  }
}
```

### 3. Generate Python-Only Adapter for a New Tool

Create a spec file `toolgen/specs/my-tool.tool.yaml`:
```yaml
tool:
  id: my-tool
  name: My Custom Tool
  summary: Does something useful.
  category: specialized
  version: v1

envelope:
  capabilities: false
  health: false
  streaming: false
  long_running: false

schema:
  shared_fields:
    - lang
    - runtime
  request:
    type: object
    properties:
      input:
        type: string
    required: [input]
  response:
    type: object
    properties:
      output:
        type: string
    required: [output]

operations:
  - id: process
    summary: Process the input.
    example:
      request:
        input: "hello"
      response:
        output: "HELLO"

adapters:
  - language: python
    template: schema_stub
    deps:
      python:
        requirements: []

policy:
  network: deny
  filesystem: deny
  secrets: deny
  timeout_sec: 30
```

Generate:
```bash
python3 cli/toolgen.py toolgen/specs/my-tool.tool.yaml
```

Only Python artifacts are created (no Node/Go/Rust/.NET files).

### 4. Add Node Adapter to Existing Tool

Edit the tool spec to add a Node adapter entry:
```yaml
adapters:
  - language: python
    template: existing_template
    deps:
      python:
        requirements: []

  - language: node  # Add this block
    template: existing_template
    deps:
      node:
        packages: []
```

Re-run toolgen:
```bash
python3 cli/toolgen.py toolgen/specs/my-tool.tool.yaml
```

The Node adapter is generated; existing Python adapter is overwritten (regenerated).

---

## Tool Specification Structure

### Minimal Spec

```yaml
tool:
  id: example
  name: Example Tool
  summary: Short description.
  category: specialized
  version: v1

envelope:
  capabilities: false
  health: false
  streaming: false
  long_running: false

schema:
  request:
    type: object
    properties: {}
  response:
    type: object
    properties: {}

operations:
  - id: do_something
    summary: Perform an action.

adapters:
  - language: python
    template: schema_stub
    deps:
      python:
        requirements: []

policy:
  network: deny
  filesystem: deny
  secrets: deny
  timeout_sec: 30
```

### Full Spec Fields

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `tool.id` | string | Yes | Unique tool identifier (lowercase, hyphen-separated) |
| `tool.name` | string | Yes | Human-readable tool name |
| `tool.summary` | string | Yes | One-sentence tool description |
| `tool.category` | string | Yes | Category: `core`, `specialized`, `marketplace` |
| `tool.version` | string | Yes | Version string (e.g., `v1`) |
| `envelope.capabilities` | boolean | Yes | Tool supports capability negotiation |
| `envelope.health` | boolean | Yes | Tool supports health checks |
| `envelope.streaming` | boolean | Yes | Tool supports streaming responses |
| `envelope.long_running` | boolean | Yes | Tool operations are long-running |
| `schema.request` | object | Yes | JSON Schema for request payload |
| `schema.response` | object | Yes | JSON Schema for response payload |
| `schema.shared_fields` | array | No | List of shared field names to include (e.g., `lang`, `runtime`, `limits`) |
| `operations` | array | Yes | List of operation definitions |
| `operations[].id` | string | Yes | Operation identifier |
| `operations[].summary` | string | Yes | Operation description |
| `operations[].example` | object | No | Example request/response pair |
| `adapters` | array | Yes | List of adapter definitions (at least one required) |
| `adapters[].language` | string | Yes | Target language: `python`, `node`, `go`, `rust`, `dotnet` |
| `adapters[].template` | string | Yes | Template name to render |
| `adapters[].deps` | object | No | Language-specific dependencies |
| `policy.network` | string | Yes | Network policy: `allow`, `deny` |
| `policy.filesystem` | string | Yes | Filesystem policy: `allow`, `deny` |
| `policy.secrets` | string | Yes | Secrets policy: `allow`, `deny` |
| `policy.timeout_sec` | integer | Yes | Execution timeout in seconds |
| `telemetry.emit` | array | No | Telemetry event definitions |
| `testing.cases` | array | No | Test case definitions |
| `marketplace.tags` | array | No | Marketplace tags |
| `marketplace.maturity` | string | No | Maturity level: `alpha`, `beta`, `stable` |

---

## Dependency Declaration

Dependencies are declared per-language in the `adapters[].deps` field.

### Python Dependencies

```yaml
adapters:
  - language: python
    template: http_client
    deps:
      python:
        requirements:
          - requests>=2.31
          - pyyaml>=6.0
```

Generated requirements are consumed by the daemon's Python runner during environment setup.

### Node Dependencies

```yaml
adapters:
  - language: node
    template: http_client
    deps:
      node:
        packages:
          - axios@1.6.0
          - lodash
```

Daemon installs packages via `npm install` before adapter invocation.

### Go Dependencies

```yaml
adapters:
  - language: go
    template: http_client
    deps:
      go:
        modules:
          - github.com/gorilla/mux@v1.8.0
```

Daemon creates ephemeral `go.mod` with declared modules.

### Rust Dependencies

```yaml
adapters:
  - language: rust
    template: http_client
    deps:
      rust:
        crates:
          - reqwest
          - serde_json
```

Daemon generates `Cargo.toml` with specified crates.

### .NET Dependencies

```yaml
adapters:
  - language: dotnet
    template: http_client
    deps:
      dotnet:
        packages:
          - Newtonsoft.Json
```

Daemon creates SDK-style `.csproj` with package references.

---

## Testing Generated Adapters

After generating adapters, validate them with the smoke test suite:

```bash
# Test all languages
python3 -m pytest tests/tools/ -v

# Test specific language
python3 -m pytest tests/tools/test_node_adapters.py -v
python3 -m pytest tests/tools/test_go_adapters.py -v
python3 -m pytest tests/tools/test_rust_adapters.py -v
python3 -m pytest tests/tools/test_dotnet_adapters.py -v

# Test specific tool
python3 -m pytest tests/tools/test_http.py -v
```

**Note**: Language-specific tests require the corresponding runtime (`node`, `go`, `cargo`, `dotnet`) in `$PATH`.

---

## Troubleshooting

| Issue | Cause | Fix |
| --- | --- | --- |
| `KeyError: 'adapters'` | Spec missing `adapters` section | Add at least one adapter entry |
| `jsonschema.ValidationError` | Spec doesn't match schema | Check `schemas/toolgen.spec.schema.json` for required fields |
| `FileNotFoundError: template not found` | Template name doesn't exist | Check `docs/toolgen-template-catalog.md` for valid template names |
| `ModuleNotFoundError: jsonschema` | Missing Python dependency | `pip install jsonschema` |
| Generated adapter fails smoke tests | Template bug or spec mismatch | Review template implementation and spec `operations[].example` |

---

## Advanced: Custom Templates

Custom templates are not yet supported in Wave 2. Template definitions are embedded in `cli/toolgen.py` under the `TEMPLATES` dictionary. To add a new template:

1. Define template code in `cli/toolgen.py` (search for `TEMPLATES = {`).
2. Register template name in the appropriate language section.
3. Update `docs/toolgen-template-catalog.md` with the new template.
4. Add smoke test fixtures under `tests/fixtures/<language>_adapters/`.

Full custom template SDK is planned for Wave 4.

---

## Integration with AssertLang Daemon

Generated adapters are consumed by the AssertLang daemon during plan execution:

1. User submits a `.pw` plan referencing a tool (e.g., `call http.request`).
2. Daemon reads `data/tools_registry.json` to locate the tool's schema and adapters.
3. Daemon selects the adapter matching the requested runtime (from `.pw` file or environment config).
4. Daemon invokes the adapter's `handle` entry point with the request payload.
5. Adapter returns a response envelope: `{"ok": bool, "version": "v1", "data": {...}}`.
6. Daemon logs timeline events and continues plan execution.

See `docs/development-guide.md` for runner protocol details.

---

## CI/CD Integration

Regenerate all tool adapters in CI to catch template regressions:

```bash
# Regenerate all tools
for spec in toolgen/specs/*.tool.yaml; do
  python3 cli/toolgen.py "$spec"
done

# Run adapter smoke tests
python3 -m pytest tests/tools/ -v

# Check for uncommitted changes (adapter drift detection)
git diff --exit-code tools/ schemas/ docs/tools/ tests/tools/
```

---

## Reference Documentation

- **Tool specs**: `toolgen/specs/*.tool.yaml`
- **Template catalog**: `docs/toolgen-template-catalog.md`
- **Adapter templates**: `docs/toolgen-*-adapter-template.md`
- **Smoke tests**: `tests/tools/test_*_adapters.py`
- **Runner protocol**: `docs/development-guide.md`
- **Wave 2 roadmap**: `docs/execution-plan.md`

---

Keep this doc in sync with `cli/toolgen.py` and `docs/toolgen-template-catalog.md` as template support evolves.