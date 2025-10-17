# Editor Integration Guide

AssertLang agents can be used directly in editors like Cursor, Windsurf, and Cline through their built-in MCP support. **No API keys needed** - use your editor's AI features!

## Quick Start

Generate MCP configuration for your project:

```bash
# For Cursor (default)
promptware mcp-config --directory examples/devops_suite

# For Windsurf
promptware mcp-config --directory examples/devops_suite --editor windsurf

# For Cline (VSCode extension)
promptware mcp-config --directory examples/devops_suite --editor cline

# For current directory (auto-scans for .al files)
promptware mcp-config
```

## Supported Editors

### Cursor

**Auto-Config:**
```bash
cd your-project
promptware mcp-config --editor cursor
```

This creates `.cursor/mcp.json` in your project directory. Cursor automatically loads it.

**Manual Setup:**
1. Run `promptware mcp-config`
2. Copy the generated config from `.cursor/mcp.json`
3. Open Cursor Settings (Cmd+, or Ctrl+,)
4. Search for "MCP"
5. Click "Edit in settings.json"
6. Paste the config

**Using Agents:**
- Open Cursor chat
- Your AssertLang agents appear in the MCP menu
- Use them like: "@code-reviewer analyze this function"

### Windsurf

**Auto-Config:**
```bash
cd your-project
promptware mcp-config --editor windsurf
```

This creates `.windsurf/mcp.json` which Windsurf loads automatically.

**Using Agents:**
- Open Windsurf
- Access Settings → Extensions → MCP
- Your agents appear in the MCP server list
- Use them in chat: "@test-runner run unit tests"

### Cline (VSCode Extension)

**Auto-Config:**
```bash
cd your-project
promptware mcp-config --editor cline
```

This creates `.vscode/mcp.json` for the Cline extension.

**Manual Setup:**
1. Install Cline extension in VSCode
2. Run `promptware mcp-config --editor cline`
3. Open VSCode Settings
4. Search for "Cline MCP"
5. Configuration loaded from `.vscode/mcp.json`

## How It Works

The `mcp-config` command:

1. **Scans** your project for `.pw` agent files
2. **Generates** MCP server configs pointing to `promptware run <agent.al>`
3. **Creates** editor-specific config files (`.cursor/mcp.json`, etc.)
4. **No API keys** needed - uses your editor's AI features

## Example: DevOps Suite in Cursor

```bash
# Generate config for DevOps agents
promptware mcp-config --directory examples/devops_suite --editor cursor

# Output: .cursor/mcp.json with 3 agents:
# - code-reviewer (AI-powered security analysis)
# - test-runner (test execution with metrics)
# - deployment-orchestrator (CI/CD workflow)
```

In Cursor, you can now:
```
@code-reviewer analyze this authentication function for vulnerabilities
@test-runner execute the unit test suite
@deployment-orchestrator deploy version 2.1.0b3 to staging
```

## Config Format

Generated config looks like:

```json
{
  "mcpServers": {
    "code-reviewer": {
      "command": "promptware",
      "args": ["run", "/path/to/code_reviewer_agent.al"]
    },
    "test-runner": {
      "command": "promptware",
      "args": ["run", "/path/to/test_runner_agent.al"]
    }
  }
}
```

Each agent is:
- **Started on-demand** by the editor
- **Uses editor's AI** (no separate API key)
- **Exposes verbs** via MCP protocol
- **Automatic cleanup** when editor closes

## Advanced Usage

### Custom Output Location

```bash
promptware mcp-config --directory examples --output ~/.config/cursor
```

### Single Agent

```bash
promptware mcp-config --agent-file my_agent.al --editor cursor
```

### Project-Wide Setup

```bash
# Setup for entire project (scans all subdirectories)
cd my-promptware-project
promptware mcp-config
```

This creates configs for all `.pw` files found in the project tree.

## Benefits

**No API Keys Required:**
- Use your editor's AI features directly
- No separate Anthropic/OpenAI API keys needed
- Editor handles authentication and billing

**Seamless Integration:**
- Agents appear as native MCP tools in your editor
- Same chat interface you're already using
- No separate terminals or processes to manage

**Auto-Discovery:**
- Automatically finds all `.pw` files
- Generates configs for all agents
- Updates when you add new agents

**Multi-Agent Workflows:**
- Use multiple agents in one chat session
- Agents can call each other via MCP
- Full DevOps pipeline in your editor

## Troubleshooting

**Agents not appearing in editor:**
1. Check config was created: `ls .cursor/mcp.json`
2. Restart your editor
3. Check editor MCP settings
4. Verify `promptware` is in PATH: `which promptware`

**"Command not found: promptware":**
```bash
pip install -e .
# Or add to PATH manually
```

**Agent fails to start:**
- Check `.pw` file syntax: `asl test your_agent.pw`
- Check dependencies installed: `pip install -r requirements.txt`
- Check port not in use: `lsof -i :23450`

**Want to use custom AI model:**
Edit the generated config to add env vars:
```json
{
  "mcpServers": {
    "code-reviewer": {
      "command": "promptware",
      "args": ["run", "/path/to/agent.al"],
      "env": {
        "ANTHROPIC_API_KEY": "sk-..."
      }
    }
  }
}
```

## Next Steps

- [Write your first agent](quickstart.md)
- [Agent DSL reference](dsl-reference.md)
- [DevOps examples](../examples/devops_suite/README.md)
- [Cross-language agents](../examples/cross_language/README.md)