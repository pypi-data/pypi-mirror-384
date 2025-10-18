# AssertLang CLI Guide

Complete guide to using the `promptware` command-line interface.

## Installation

### From Source

```bash
# Clone repository
git clone https://github.com/promptware/promptware.git
cd promptware

# Install in development mode
pip install -e .
```

### From PyPI (when published)

```bash
pip install promptware
```

### Verify Installation

```bash
promptware --version
# Output: AssertLang 0.1.0
```

## Quick Start

### 1. Create New Agent

```bash
# Create from basic template
promptware init my-agent

# Create API agent
promptware init api-service --template api --port 8080

# Create AI agent
promptware init chatbot --template ai
```

### 2. Validate Agent

```bash
# Basic validation
promptware validate my-agent.al

# Detailed validation with verbose output
promptware validate my-agent.al --verbose
```

### 3. Generate Server

```bash
# Generate Python server
promptware generate my-agent.al --lang python

# Generate Go server
promptware generate my-agent.al --lang go

# Generate Node.js server with custom output
promptware generate my-agent.al --lang typescript --output ./servers/nodejs
```

### 4. Build & Run

**Python:**
```bash
cd generated/my-agent
pip install -r requirements.txt
python my-agent_server.py
```

**Node.js:**
```bash
cd generated/my-agent
npm install
node my-agent_server.js
```

**Go:**
```bash
python3 scripts/build_server.py my-agent.al go
./examples/demo/go/my-agent
```

**C#:**
```bash
python3 scripts/build_server.py my-agent.al dotnet
cd examples/demo/dotnet && dotnet run
```

**Rust:**
```bash
python3 scripts/build_server.py my-agent.al rust
./examples/demo/rust/target/release/my-agent
```

### 5. Test Your Agent

Once your agent is running, test it with auto-generated tests:

```bash
# Health check and verb discovery
asl test http://localhost:3000

# Run full integration test suite
asl test http://localhost:3000 --auto

# Load test critical verbs
asl test http://localhost:3000 --load --verb user.create@v1 --requests 500

# Generate coverage report
asl test http://localhost:3000 --auto --coverage
```

## Commands Reference

### `asl test`

Test a running MCP agent with auto-generated integration tests and load testing.

**Usage:**
```bash
asl test <agent-url> [OPTIONS]
```

**Options:**
- `--auto` - Auto-generate and run integration tests from verb schemas
- `--load` - Run load tests (requires `--verb`)
- `--verb VERB` - Specific verb to load test
- `--requests NUM` - Number of load test requests (default: 100)
- `--concurrency NUM` - Concurrent requests for load testing (default: 10)
- `--coverage` - Export coverage report to coverage.json
- `--timeout SEC` - Request timeout in seconds (default: 30)

**Examples:**
```bash
# Basic health check and verb discovery
asl test http://localhost:3000

# Run auto-generated integration tests
asl test http://localhost:3000 --auto

# Load test a specific verb
asl test http://localhost:3000 --load --verb user.create@v1 --requests 1000 --concurrency 50

# Full test suite with coverage report
asl test http://localhost:3000 --auto --coverage
```

**What it does:**

1. **Health Check** - Verifies agent is running and responding
2. **Verb Discovery** - Lists all available verbs and their schemas
3. **Integration Tests** (with `--auto`):
   - Auto-generates test cases from verb schemas
   - Happy path tests with valid parameters
   - Error tests with missing/invalid parameters
   - Validates expected response fields
4. **Load Tests** (with `--load`):
   - Concurrent requests with configurable parallelism
   - Latency statistics (avg, min, max, P95, P99)
   - Throughput measurement (requests per second)
   - Error tracking and reporting
5. **Coverage Report** (with `--coverage`):
   - Exports JSON report with tested verbs
   - Percentage of verbs tested
   - Timestamp and agent URL

**Output:**
```
🧪 Testing agent at http://localhost:3000

✓ Health check passed: {'status': 'alive', 'uptime_seconds': 3600}

✓ Discovered 5 verbs

🧪 Running 10 integration tests...

[1/10] test_user_create_v1_happy_path... ✓ PASS (45ms)
[2/10] test_user_create_v1_missing_param... ✓ PASS (12ms)
...

============================================================
📊 Test Summary
============================================================
Total:    10
Passed:   10 ✓
Failed:   0 ✗
Coverage: 100.0%
============================================================

✨ Testing complete!
```

### `promptware generate`

Generate MCP server from .al file.

**Usage:**
```bash
promptware generate <file.al> [OPTIONS]
```

**Options:**
- `--lang LANGUAGE` - Target language (python, typescript, go, csharp, rust). Default: python
- `--output DIR` - Output directory. Default: `./generated/<agent-name>`
- `--build` - Build server after generation (for compiled languages)
- `--yes, -y` - Skip confirmation prompts (for CI/scripts)
- `--dry-run` - Show what would be generated without writing files
- `--quiet, -q` - Minimal output (for CI/scripts)

**Examples:**
```bash
# Python server (default)
promptware generate agent.al

# Preview without writing files
promptware generate agent.al --dry-run

# Go server with build (skip confirmation)
promptware generate agent.al --lang go --build --yes

# Quiet mode for CI/CD
promptware generate agent.al --quiet --yes

# Rust server with custom output
promptware generate agent.al --lang rust --output ./production/rust-server
```

**Safety Features:**

- **Confirmation Prompt** - By default, shows what will be created and asks for confirmation
- **Dry-Run Mode** - Use `--dry-run` to preview without writing any files
- **Skip Confirmation** - Use `--yes/-y` to bypass prompts (ideal for CI/CD)
- **Quiet Mode** - Use `--quiet/-q` for minimal output (only errors)
- **NO_COLOR Support** - Respects `NO_COLOR` environment variable for plain text output

### `promptware validate`

Validate .al file syntax and structure.

**Usage:**
```bash
promptware validate <file.al> [OPTIONS]
```

**Options:**
- `--verbose` - Show detailed validation output including agent details

**Examples:**
```bash
# Basic validation
promptware validate agent.al

# Detailed output
promptware validate agent.al --verbose
```

**Output (verbose):**
```
🔍 Validating agent.pw...
✓ Syntax valid

📋 Agent Details:
  Name: user-service
  Port: 3000
  Verbs: 2
    - user.create@v1 (2 params, 1 returns)
    - user.get@v1 (1 params, 1 returns)
  Tools: http, auth, logger
```

### `promptware list-tools`

List all available tools that can be used in .al agents.

**Usage:**
```bash
promptware list-tools [OPTIONS]
```

**Options:**
- `--lang LANGUAGE` - Show tools for specific language (python, typescript, go, csharp, rust, all). Default: all
- `--category CATEGORY` - Filter by category

**Categories:**
- HTTP & APIs
- Authentication
- Storage & Data
- Flow Control
- Logging & Monitoring
- Scheduling
- Media
- System

**Examples:**
```bash
# List all tools
promptware list-tools

# List Python tools only
promptware list-tools --lang python

# List HTTP & API tools
promptware list-tools --category "HTTP & APIs"
```

**Output:**
```
🛠️  Available AssertLang Tools

📦 HTTP & APIs
  • http                     [python, nodejs, go, csharp, rust]
  • rest                     [python, nodejs, go, csharp, rust]
  • api-auth                 [python, nodejs, go, csharp, rust]

📦 Authentication
  • auth                     [python, nodejs, go, csharp, rust]
  • encryption               [python, nodejs, go, csharp, rust]

Total: 38 tools
```

### `promptware init`

Create new .al agent from template.

**Usage:**
```bash
promptware init <name> [OPTIONS]
```

**Options:**
- `--template TYPE` - Agent template (basic, api, workflow, ai). Default: basic
- `--port PORT` - Server port. Default: 3000

**Templates:**

1. **basic** - Simple agent with single verb
2. **api** - API agent with HTTP tools
3. **workflow** - Workflow agent with scheduler
4. **ai** - AI-powered agent with LLM

**Examples:**
```bash
# Basic agent
promptware init my-agent

# API service on port 8080
promptware init api-service --template api --port 8080

# AI chatbot
promptware init chatbot --template ai
```

### `promptware config`

Manage global and per-project configuration.

**Usage:**
```bash
promptware config <subcommand> [OPTIONS]
```

**Subcommands:**

#### `config set`

Set configuration value.

```bash
promptware config set <key> <value> [--project]
```

**Examples:**
```bash
# Set default language globally
promptware config set defaults.language rust

# Set default language for current project only
promptware config set defaults.language nodejs --project

# Set auto-confirm for generate command
promptware config set generate.auto_confirm true

# Set default port
promptware config set init.port 8080
```

#### `config get`

Get configuration value.

```bash
promptware config get <key>
```

**Examples:**
```bash
# Get default language
promptware config get defaults.language

# Get init port
promptware config get init.port
```

#### `config unset`

Remove configuration value.

```bash
promptware config unset <key> [--project]
```

**Examples:**
```bash
# Remove global language default
promptware config unset defaults.language

# Remove project-level setting
promptware config unset defaults.language --project
```

#### `config list`

List all configuration values.

```bash
promptware config list
```

**Output:**
```json
{
  "defaults": {
    "language": "rust",
    "template": "basic",
    "output_dir": null
  },
  "generate": {
    "auto_confirm": false
  },
  "init": {
    "port": 3000
  }
}
```

#### `config path`

Show path to config file.

```bash
promptware config path [--project]
```

**Examples:**
```bash
# Show global config file path
promptware config path

# Show project config file path
promptware config path --project
```

#### `config edit`

Open config file in editor.

```bash
promptware config edit [--project]
```

**Configuration Files:**

- **Global**: `~/.config/promptware/config.toml` (XDG-compliant)
- **Project**: `.promptware/config.toml` (in current directory)

**Precedence:**

CLI arguments > Project config > Global config > Defaults

**Available Keys:**

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `defaults.language` | string | `python` | Default target language |
| `defaults.template` | string | `basic` | Default init template |
| `defaults.output_dir` | string | `null` | Default output directory |
| `generate.auto_confirm` | boolean | `false` | Skip confirmations by default |
| `init.port` | integer | `3000` | Default server port |

**Format:**

Supports both TOML and JSON formats. TOML is preferred:

```toml
[defaults]
language = "rust"
template = "api"

[generate]
auto_confirm = false

[init]
port = 8080
```

### `promptware help`

Show help for commands.

**Usage:**
```bash
promptware help [COMMAND]
```

**Examples:**
```bash
# General help
promptware help

# Command-specific help
promptware help generate
promptware help validate
promptware help config
```

### `promptware version`

Show version information.

**Usage:**
```bash
promptware --version
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PROMPTWARE_HOME` | AssertLang installation directory | Auto-detected |
| `XDG_CONFIG_HOME` | Base directory for config files | `~/.config` |
| `NO_COLOR` | Disable colored output | Not set |
| `ANTHROPIC_API_KEY` | API key for AI-powered agents | None |
| `ALLOWED_ORIGINS` | CORS allowed origins | `*` |
| `DEBUG` | Enable debug mode | `false` |
| `RATE_LIMIT` | Requests per minute per IP | `100` |

## Common Workflows

### Development Workflow

```bash
# 1. Set up preferences (optional)
promptware config set defaults.language python

# 2. Create agent
promptware init my-service --template api

# 3. Edit my-service.al (customize verbs, tools)

# 4. Validate
promptware validate my-service.al --verbose

# 5. Preview generation (dry-run)
promptware generate my-service.al --dry-run

# 6. Generate development server
promptware generate my-service.al

# 7. Run and test
cd generated/my-service
pip install -r requirements.txt
python my-service_server.py
```

### Production Workflow

```bash
# 1. Validate agent
promptware validate my-service.al

# 2. Generate production server (skip confirmation for CI)
promptware generate my-service.al --lang go --output ./production --yes --quiet

# 3. Build
python3 scripts/build_server.py my-service.al go

# 4. Deploy binary
./examples/demo/go/my-service
```

### CI/CD Workflow

```bash
# Use --yes and --quiet for automated pipelines
promptware generate agent.al --yes --quiet

# Or set config for entire project
promptware config set generate.auto_confirm true --project

# Disable colored output
export NO_COLOR=1
promptware generate agent.al --yes
```

### Multi-Language Workflow

```bash
# Generate servers in all languages
promptware generate agent.al --lang python --output ./servers/python
promptware generate agent.al --lang typescript --output ./servers/nodejs
promptware generate agent.al --lang go --output ./servers/go
promptware generate agent.al --lang csharp --output ./servers/csharp
promptware generate agent.al --lang rust --output ./servers/rust
```

## Troubleshooting

### Command Not Found

If `promptware` command is not found after installation:

```bash
# Ensure pip bin directory is in PATH
export PATH="$HOME/.local/bin:$PATH"

# Or use python -m
python3 -m promptware.cli --help
```

### Import Errors

If you get import errors:

```bash
# Reinstall in development mode
pip install -e .

# Or add to PYTHONPATH
export PYTHONPATH="/path/to/promptware:$PYTHONPATH"
```

### Build Failures (Compiled Languages)

For Go/C#/Rust build issues:

```bash
# Verify runtime installed
go version
dotnet --version
cargo --version

# Use build script directly
python3 scripts/build_server.py agent.al go
```

## Shell Completion

### Bash

```bash
# Add to ~/.bashrc
eval "$(_PROMPTWARE_COMPLETE=bash_source promptware)"
```

### Zsh

```bash
# Add to ~/.zshrc
eval "$(_PROMPTWARE_COMPLETE=zsh_source promptware)"
```

### Fish

```bash
# Add to ~/.config/fish/completions/promptware.fish
_PROMPTWARE_COMPLETE=fish_source promptware | source
```

## Next Steps

- [Writing .al Agents](./promptware-dsl-spec.md)
- [Production Deployment](./production-hardening.md)
- [Tool Development](./tool-development.md)
- [API Reference](./api-reference.md)
