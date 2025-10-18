# CLI Commands Reference

**Complete reference for AssertLang command-line tools.**

---

## Overview

AssertLang provides a comprehensive CLI for working with contracts:
- **Build** - Compile PW → Python/Go/Rust/JavaScript
- **Validate** - Check contract syntax and correctness
- **Generate** - Create MCP servers from agents
- **Test** - Integration and load testing
- **Init** - Project scaffolding

**Installation**:
```bash
pip install promptware
```

**Verify**:
```bash
promptware --version
# Output: AssertLang 2.2.0
```

---

## Quick Reference

| Command | Purpose | Example |
|---------|---------|---------|
| `build` | Compile PW to target language | `asl build file.al -o file.py` |
| `compile` | Compile PW to MCP JSON | `asl compile file.pw` |
| `run` | Execute PW file | `promptware run file.pw` |
| `validate` | Check contract syntax | `promptware validate file.pw` |
| `generate` | Generate MCP server | `promptware generate agent.pw` |
| `test` | Test MCP agent | `asl test http://localhost:3000 --auto` |
| `list-tools` | Show available tools | `promptware list-tools` |
| `init` | Create new project | `promptware init my-agent` |
| `config` | Manage configuration | `promptware config set defaults.language go` |
| `ai-guide` | Show AI agent guide | `promptware ai-guide` |

---

## build

**Compile AssertLang contracts to target languages.**

### Syntax
```bash
asl build <file.al> [OPTIONS]
```

### Options

| Option | Short | Values | Default | Description |
|--------|-------|--------|---------|-------------|
| `--lang` | `-l` | python, go, rust, typescript, javascript, csharp | python | Target language |
| `--format` | `-f` | standard, pydantic, typeddict | standard | Python output format |
| `--output` | `-o` | path | stdout | Output file path |
| `--verbose` | `-v` | - | - | Show detailed output |

### Examples

**Basic compilation:**
```bash
asl build calculator.al -o calculator.py
```
Output:
```
✓ Compiled calculator.al → calculator.py
```

**Multiple languages:**
```bash
# Python
asl build user.al --lang python -o user.py

# Go
asl build user.al --lang go -o user.go

# Rust
asl build user.al --lang rust -o user.rs

# TypeScript
asl build user.al --lang typescript -o user.ts

# JavaScript
asl build user.al --lang javascript -o user.js
```

**Python output formats:**
```bash
# Standard code (functions/classes)
asl build model.al --format standard -o model.py

# Pydantic models (validation)
asl build model.al --format pydantic -o model.py

# TypedDict schemas (state types)
asl build model.al --format typeddict -o model.py
```

**Verbose mode:**
```bash
asl build contract.al -o contract.py --verbose
```
Output:
```
ℹ Reading: contract.al
ℹ Parsing PW code...
✓ Parsed: 5 functions, 2 classes
ℹ Converting to MCP...
ℹ Generating python code...
ℹ Written: contract.py (1547 chars)
✓ Compiled contract.al → contract.py
```

**To stdout:**
```bash
asl build add.al
```
Output (Python code printed):
```python
def add(x: int, y: int) -> int:
    check_precondition(x > 0, "positive_x")
    check_precondition(y > 0, "positive_y")

    result = x + y

    check_postcondition(result > 0, "positive_result")
    return result
```

### Generated Output

**Python (standard)**:
```python
from promptware.runtime.contracts import check_precondition, check_postcondition

def add(x: int, y: int) -> int:
    check_precondition(x > 0, "positive_x", f"Expected x > 0, got x = {x}")
    check_precondition(y > 0, "positive_y", f"Expected y > 0, got y = {y}")

    __result = x + y

    check_postcondition(__result > 0, "positive_result",
        f"Expected result > 0, got result = {__result}")

    return __result
```

**Python (pydantic)**:
```python
from pydantic import BaseModel, field_validator

class User(BaseModel):
    name: str
    age: int

    @field_validator('name')
    def validate_name(cls, v):
        if not (len(v) > 0):
            raise ValueError("Contract 'non_empty' failed: Expected len(name) > 0")
        return v

    @field_validator('age')
    def validate_age(cls, v):
        if not (v >= 0 and v <= 120):
            raise ValueError("Contract 'valid_age' failed: Expected 0 <= age <= 120")
        return v
```

---

## compile

**Compile PW to MCP JSON intermediate representation.**

### Syntax
```bash
asl compile <file.al> [OPTIONS]
```

### Options

| Option | Short | Values | Default | Description |
|--------|-------|--------|---------|-------------|
| `--output` | `-o` | path | `<input>.pw.json` | Output JSON file |
| `--verbose` | `-v` | - | - | Verbose output |

### Examples

**Basic compilation:**
```bash
asl compile user.al
```
Output:
```
✓ Compiled user.al → user.pw.json
```

**Custom output:**
```bash
asl compile contract.al -o ir.json
```

**Verbose:**
```bash
asl compile contract.al --verbose
```
Output:
```
ℹ Reading: contract.al
ℹ Parsing PW code...
ℹ Converting to MCP JSON...
ℹ Written: contract.pw.json (3241 chars)
✓ Compiled contract.al → contract.pw.json
```

### JSON Output Format

```json
{
  "module": {
    "functions": [
      {
        "name": "add",
        "params": [
          {"name": "x", "type": "int"},
          {"name": "y", "type": "int"}
        ],
        "return_type": "int",
        "requires": [
          {"name": "positive_x", "expr": "x > 0"}
        ],
        "ensures": [
          {"name": "positive_result", "expr": "result > 0"}
        ],
        "body": [...]
      }
    ],
    "classes": []
  }
}
```

---

## run

**Execute PW file directly (compile + run).**

### Syntax
```bash
promptware run <file.al> [OPTIONS]
```

### Options

| Option | Short | Description |
|--------|-------|-------------|
| `--verbose` | `-v` | Show compilation steps |

### Examples

**Basic execution:**
```bash
promptware run calculator.al
```

**With verbose:**
```bash
promptware run program.al --verbose
```
Output:
```
ℹ Reading: program.al
ℹ Parsing PW code...
ℹ Generating Python code...
ℹ Executing...
────────────────────────────────────────────────────────────
Hello from AssertLang!
Result: 42
```

### Use Cases

1. **Quick testing** - Test contracts without saving generated code
2. **Script execution** - Run PW scripts directly
3. **Development** - Rapid iteration during development

---

## validate

**Validate contract syntax and correctness.**

### Syntax
```bash
promptware validate <file.al> [OPTIONS]
```

### Options

| Option | Description |
|--------|-------------|
| `--verbose` | Show detailed validation output |

### Examples

**Basic validation:**
```bash
promptware validate order.al
```
Output:
```
🔍 Validating order.pw...
✓ Syntax valid
```

**Verbose validation:**
```bash
promptware validate order.al --verbose
```
Output:
```
🔍 Validating order.pw...
✓ Syntax valid

📋 Contract Details:
  Functions: 3
    - calculate_total (2 preconditions, 2 postconditions)
    - apply_discount (3 preconditions, 1 postcondition)
    - validate_order (4 preconditions, 1 postcondition)

  Classes: 1
    - Order (2 invariants, 5 methods)

📊 Coverage:
  Preconditions: 9
  Postconditions: 5
  Invariants: 2
```

**Validation errors:**
```bash
promptware validate broken.al
```
Output:
```
🔍 Validating broken.pw...
✗ Validation failed: Unexpected token at line 5, column 10

  Line 5:     @requires positive x > 0
                                 ^
  Expected ':' after contract clause name

Suggestion: Add colon after clause name: @requires positive: x > 0
```

---

## generate

**Generate MCP server from agent definition.**

### Syntax
```bash
promptware generate <agent.al> [OPTIONS]
```

### Options

| Option | Short | Values | Default | Description |
|--------|-------|--------|---------|-------------|
| `--lang` | - | python, nodejs, go, csharp, rust | python | Target language |
| `--output` | - | path | `./generated/<agent>` | Output directory |
| `--build` | - | - | - | Build after generation |
| `--yes` | `-y` | - | - | Skip confirmation |
| `--dry-run` | - | - | - | Show what would be generated |
| `--quiet` | `-q` | - | - | Minimal output |

### Examples

**Python server:**
```bash
promptware generate user-service.al --lang python
```
Output:
```
📖 Reading user-service.pw...
✓ Parsed agent: user-service
  Port: 3000
  Verbs: 4
  Tools: 2

ℹ Will create:
  Output directory: /path/to/generated/user-service
  • user-service_server.py (247 lines)
  • requirements.txt (6 lines)

Proceed? [Y/n] y

🔨 Generating python server...
✓ Created: user-service_server.py
✓ Created: requirements.txt

📦 Next steps:
  cd generated/user-service
  pip install -r requirements.txt
  python user-service_server.py

✨ Server generated successfully!
📂 Output: /path/to/generated/user-service
```

**Go server:**
```bash
promptware generate api.al --lang go --output ./build
```

**Dry-run mode:**
```bash
promptware generate agent.al --dry-run
```
Output:
```
📖 Reading agent.pw...
✓ Parsed agent: my-agent

ℹ Dry-run mode - no files will be written

Would create in: /path/to/generated/my-agent
  ✓ my-agent_server.py (180 bytes, 45 lines)
  ✓ requirements.txt (85 bytes, 4 lines)
```

**Auto-confirm:**
```bash
promptware generate agent.al --yes
```

---

## test

**Test running MCP agent.**

### Syntax
```bash
asl test <agent-url> [OPTIONS]
```

### Options

| Option | Description |
|--------|-------------|
| `--auto` | Auto-generate integration tests |
| `--load` | Run load tests (requires --verb) |
| `--verb VERB` | Specific verb to test |
| `--requests NUM` | Number of requests (default: 100) |
| `--concurrency NUM` | Concurrent requests (default: 10) |
| `--coverage` | Export coverage report |
| `--timeout SEC` | Request timeout (default: 30s) |

### Examples

**Health check:**
```bash
asl test http://localhost:3000
```
Output:
```
🧪 Testing agent at http://localhost:3000

✓ Health check passed
✓ Agent responding

✓ Discovered 4 verbs
```

**Integration tests:**
```bash
asl test http://localhost:3000 --auto
```
Output:
```
🧪 Testing agent at http://localhost:3000

✓ Health check passed

✓ Discovered 4 verbs

Running integration tests...

  ✓ user.create@v1        (142ms)
  ✓ user.get@v1           (89ms)
  ✓ user.update@v1        (156ms)
  ✓ user.delete@v1        (103ms)

Passed: 4/4
Failed: 0/4
Total time: 490ms

✨ Testing complete!
```

**Load test:**
```bash
asl test http://localhost:3000 --load --verb user.create@v1 --requests 1000 --concurrency 50
```
Output:
```
🧪 Testing agent at http://localhost:3000

✓ Health check passed
✓ Discovered 4 verbs

============================================================
Load Testing: user.create@v1
============================================================

Running 1000 requests with concurrency 50...

Progress: [████████████████████████████████] 1000/1000

Results:
  Requests:     1000
  Successful:   997
  Failed:       3
  Duration:     8.4s
  RPS:          119.0

  Latency:
    Min:        12ms
    Max:        456ms
    Mean:       87ms
    P50:        82ms
    P95:        145ms
    P99:        234ms

✨ Testing complete!
```

**Coverage report:**
```bash
asl test http://localhost:3000 --auto --coverage
```
Output:
```
✓ Exported coverage report: coverage.json
```

---

## list-tools

**List available AssertLang tools.**

### Syntax
```bash
promptware list-tools [OPTIONS]
```

### Options

| Option | Values | Default | Description |
|--------|--------|---------|-------------|
| `--lang` | python, nodejs, go, csharp, rust, all | all | Filter by language |
| `--category` | category name | all | Filter by category |

### Examples

**List all tools:**
```bash
promptware list-tools
```
Output:
```
🛠️  Available AssertLang Tools

📦 HTTP & APIs
  • http                      [python, nodejs, go, csharp, rust]
  • rest                      [python, nodejs, go]
  • api-auth                  [python, nodejs]

📦 Authentication
  • auth                      [python, nodejs, go, csharp]
  • encryption                [python, nodejs, go]

📦 Storage & Data
  • storage                   [python, nodejs, go, rust]
  • validate-data             [python, nodejs, go, csharp, rust]
  • transform                 [python, nodejs]

📦 Flow Control
  • conditional               [python, nodejs, go, csharp, rust]
  • branch                    [python, nodejs, go, csharp]
  • loop                      [python, nodejs, go]
  • async                     [python, nodejs, rust]
  • thread                    [python, go, rust]

Total: 27 tools
```

**Filter by language:**
```bash
promptware list-tools --lang rust
```
Output:
```
📦 HTTP & APIs
  • http                      [rust]

📦 Storage & Data
  • storage                   [rust]
  • validate-data             [rust]

Total: 3 tools
(Filtered by language: rust)
```

---

## init

**Create new AssertLang project from template.**

### Syntax
```bash
promptware init <name> [OPTIONS]
```

### Options

| Option | Values | Default | Description |
|--------|--------|---------|-------------|
| `--template` | basic, api, workflow, ai | basic | Project template |
| `--port` | port number | 3000 | Server port |

### Examples

**Basic agent:**
```bash
promptware init my-agent
```
Output:
```
✓ Created: my-agent.al

📝 Next steps:
  1. Edit my-agent.al to customize your agent
  2. Validate: promptware validate my-agent.al
  3. Generate: promptware generate my-agent.al --lang python
```

Generated `my-agent.pw`:
```pw
agent my-agent

port 3000

expose task.execute@v1 (
    task: string
) -> (
    result: string
)
```

**API agent:**
```bash
promptware init api-service --template api --port 8080
```
Generated `api-service.pw`:
```pw
agent api-service

port 8080

tools: http, auth, logger

expose api.call@v1 (
    endpoint: string,
    method: string
) -> (
    response: object,
    status: int
)
```

**AI agent:**
```bash
promptware init assistant --template ai
```
Generated `assistant.pw`:
```pw
agent assistant

port 3000

llm: anthropic claude-3-5-sonnet-20241022

prompt: "You are a helpful AI assistant."

expose chat.message@v1 (
    message: string
) -> (
    response: string
)
```

**Workflow agent:**
```bash
promptware init workflow --template workflow
```

---

## config

**Manage AssertLang configuration.**

### Syntax
```bash
promptware config <action> [OPTIONS]
```

### Actions

| Action | Description |
|--------|-------------|
| `set <key> <value>` | Set configuration value |
| `get <key>` | Get configuration value |
| `unset <key>` | Remove configuration value |
| `list` | List all configuration |
| `edit` | Open config file in editor |
| `path` | Show config file path |

### Options

| Option | Description |
|--------|-------------|
| `--project` | Use project config (not global) |

### Examples

**Set default language:**
```bash
promptware config set defaults.language go
```
Output:
```
✓ Set defaults.language = go (global)
```

**Get configuration:**
```bash
promptware config get defaults.language
```
Output:
```
go
```

**List all config:**
```bash
promptware config list
```
Output:
```json
{
  "defaults": {
    "language": "go",
    "port": 3000
  },
  "generate": {
    "auto_confirm": false
  }
}
```

**Edit config:**
```bash
promptware config edit
```
Opens config file in `$EDITOR` (nano, vim, etc.)

**Show config path:**
```bash
promptware config path
```
Output:
```
/Users/username/.config/promptware/config.toml
```

**Project-level config:**
```bash
promptware config set defaults.language python --project
```
Output:
```
✓ Set defaults.language = python (project)
```

**Unset config:**
```bash
promptware config unset defaults.language
```
Output:
```
✓ Unset defaults.language (global)
```

### Configuration Keys

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `defaults.language` | string | python | Default target language |
| `defaults.port` | int | 3000 | Default server port |
| `generate.auto_confirm` | bool | false | Skip confirmation prompts |
| `generate.install_deps` | bool | true | Auto-install dependencies |

---

## ai-guide

**Show AI agent onboarding guide.**

### Syntax
```bash
promptware ai-guide
```

### Example

```bash
promptware ai-guide
```
Output:
```markdown
# AssertLang AI Agent Guide

This guide helps AI coding agents understand AssertLang...

[Full guide content printed to stdout]

ℹ Copy this entire output and paste it to any AI coding agent.
ℹ They will understand how to help you build services with AssertLang.
```

---

## help

**Show help for commands.**

### Syntax
```bash
promptware help [COMMAND]
```

### Examples

**General help:**
```bash
promptware help
```

**Command-specific help:**
```bash
promptware help build
promptware help generate
promptware help test
```

---

## Common Workflows

### Development Workflow

```bash
# 1. Write contract
vim user.al

# 2. Validate syntax
promptware validate user.al

# 3. Test with different targets
asl build user.al                          # Python (default)
asl build user.al --lang go                # Go
asl build user.al --lang rust              # Rust

# 4. Generate final output
asl build user.al -o user.py

# 5. Run it
python user.py
```

### Agent Development Workflow

```bash
# 1. Create agent from template
promptware init my-service --template api

# 2. Edit agent definition
vim my-service.al

# 3. Validate
promptware validate my-service.al

# 4. Generate server
promptware generate my-service.al --lang python

# 5. Run server
cd generated/my-service
pip install -r requirements.txt
python my-service_server.py

# 6. Test (in another terminal)
asl test http://localhost:3000 --auto
```

### Testing Workflow

```bash
# 1. Health check
asl test http://localhost:3000

# 2. Integration tests
asl test http://localhost:3000 --auto

# 3. Load test specific verb
asl test http://localhost:3000 \
    --load \
    --verb user.create@v1 \
    --requests 10000 \
    --concurrency 100

# 4. Export coverage
asl test http://localhost:3000 --auto --coverage
```

---

## Environment Variables

| Variable | Values | Effect |
|----------|--------|--------|
| `NO_COLOR` | 1, true | Disable colored output |
| `EDITOR` | editor path | Default editor for `config edit` |
| `PROMPTWARE_DISABLE_CONTRACTS` | 1, true | Disable runtime contract checking |

### Examples

```bash
# Disable colors (for CI/scripts)
NO_COLOR=1 asl build contract.al

# Use specific editor
EDITOR=vim promptware config edit

# Disable runtime contracts
PROMPTWARE_DISABLE_CONTRACTS=1 python generated_code.py
```

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error (parse error, validation failed, etc.) |
| 2 | Invalid arguments |

---

## See Also

- **[Contract Syntax](contract-syntax.md)** - PW language reference
- **[Runtime API](runtime-api.md)** - Python/JavaScript runtime
- **[MCP Operations](mcp-operations.md)** - MCP server API
- **[Quickstart](../../QUICKSTART.md)** - Get started in 5 minutes

---

**[← MCP Operations](mcp-operations.md)** | **[Error Codes →](error-codes.md)**
