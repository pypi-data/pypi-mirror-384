# Agent Communication Guide

**AssertLang Agent-to-Agent Communication**

This guide explains how to build autonomous agents that coordinate via MCP verbs using AssertLang's `.pw` language.

---

## Overview

AssertLang enables agents written in different languages to communicate via a shared protocol based on MCP (Model Context Protocol). Agents:

1. **Expose MCP verbs** - define capabilities other agents can call
2. **Call other agents' verbs** - coordinate with peers
3. **Run on standard port** - 23456 for discovery
4. **Speak .al protocol** - language-agnostic coordination

---

## Quick Start

### 1. Define an Agent (`.pw` file)

```al
lang python
agent code-reviewer
port 23456

expose review.submit@v1:
  params:
    pr_url string
  returns:
    review_id string
    status string

expose review.status@v1:
  params:
    review_id string
  returns:
    status string
    comments array
```

### 2. Generate MCP Server

```python
from language.mcp_server_generator import generate_mcp_server_from_pw

with open('agent.pw', 'r') as f:
    server_code = generate_mcp_server_from_pw(f.read())

with open('agent_server.py', 'w') as f:
    f.write(server_code)
```

### 3. Run the Server

```bash
pip3 install fastapi uvicorn requests
python3 agent_server.py
```

Server runs on port 23456 and exposes:
- `POST /mcp` - MCP verb endpoint
- `GET /health` - Health check
- `GET /verbs` - List exposed verbs

### 4. Call from Another Agent

```python
from language.mcp_client import call_agent, register_agent

# Register the agent
register_agent("code-reviewer", "http://127.0.0.1:23456")

# Call a verb
response = call_agent(
    "code-reviewer",
    "review.submit@v1",
    {"pr_url": "https://github.com/test/pr/1"}
)

if response.is_success():
    data = response.get_data()
    print(f"Review ID: {data['review_id']}")
```

---

## Agent Definition Syntax

### Basic Structure

```al
lang <language>        # python, node, go, rust, etc.
agent <name>           # agent identifier
port <number>          # MCP server port (default: 23456)

expose <verb>:         # MCP verb definition
  params:              # input parameters
    <name> <type>
  returns:             # output fields
    <name> <type>
```

### Supported Types

- `string` - Text data
- `int` - Integer numbers
- `bool` - True/false values
- `object` - JSON objects
- `array` - JSON arrays

### Example: Multi-Verb Agent

```al
lang python
agent task-executor
port 23456

expose task.create@v1:
  params:
    name string
    priority int
  returns:
    task_id string
    status string

expose task.execute@v1:
  params:
    task_id string
  returns:
    result object
    status string

expose task.status@v1:
  params:
    task_id string
  returns:
    status string
    progress int
```

---

## MCP Server

### Generated Server Structure

The generator creates a FastAPI application with:

**Handler Functions**: One per exposed verb
```python
def handle_review_submit_v1(params: Dict[str, Any]) -> Dict[str, Any]:
    # Parameter validation
    if "pr_url" not in params:
        return {"error": {"code": "E_ARGS", "message": "Missing pr_url"}}

    # Business logic (implement here)
    # ...

    return {
        "review_id": "...",
        "status": "pending"
    }
```

**MCP Endpoint**: JSON-RPC over HTTP
```python
@app.post("/mcp")
async def mcp_endpoint(request: Request):
    body = await request.json()
    method = body.get("method")
    params = body.get("params", {})

    # Route to handler
    if method == "review.submit@v1":
        result = handle_review_submit_v1(params)
        # ...

    return JSONResponse({
        "ok": True,
        "version": "v1",
        "data": result
    })
```

**Utility Endpoints**:
- `GET /health` - Returns agent health status
- `GET /verbs` - Lists all exposed MCP verbs

### Request Format

```json
{
  "method": "verb.name@v1",
  "params": {
    "param1": "value1",
    "param2": 123
  }
}
```

### Response Format

**Success**:
```json
{
  "ok": true,
  "version": "v1",
  "data": {
    "field1": "value1",
    "field2": 123
  }
}
```

**Error**:
```json
{
  "ok": false,
  "version": "v1",
  "error": {
    "code": "E_ARGS",
    "message": "Missing required parameter: pr_url"
  }
}
```

### Error Codes

- `E_ARGS` - Missing or invalid parameters
- `E_METHOD` - Unknown MCP verb
- `E_RUNTIME` - Runtime execution error
- `E_TIMEOUT` - Request timeout
- `E_NETWORK` - Network communication failure

---

## MCP Client

### Basic Usage

```python
from language.mcp_client import MCPClient

client = MCPClient("http://localhost:23456")
response = client.call("review.submit@v1", {"pr_url": "https://..."})

if response.is_success():
    data = response.get_data()
    print(data["review_id"])
else:
    print(f"Error: {response.error}")
```

### With Retries and Timeout

```python
client = MCPClient(
    "http://localhost:23456",
    timeout=60,    # seconds
    retries=5      # retry attempts
)
```

### Context Manager

```python
with MCPClient("http://localhost:23456") as client:
    response = client.call("verb@v1", {})
    # Client auto-closes
```

### Error Handling

```python
from language.mcp_client import MCPError

try:
    response = client.call("verb@v1", {})
    data = response.get_data()  # Raises MCPError if failed
except MCPError as e:
    print(f"Code: {e.code}")
    print(f"Message: {e.message}")
```

---

## Agent Registry

### Simple Registry (Current)

```python
from language.mcp_client import register_agent, call_agent

# Register agents
register_agent("code-reviewer", "http://localhost:23456")
register_agent("test-runner", "http://localhost:23457")

# Call agents by name
response = call_agent("code-reviewer", "review.submit@v1", {...})
```

### Custom Registry

```python
from language.mcp_client import AgentRegistry

registry = AgentRegistry()
registry.register("agent-a", "http://localhost:23456")
registry.register("agent-b", "http://localhost:23457")

# Get client
client = registry.get_client("agent-a")
response = client.call("verb@v1", {})

# List all agents
agents = registry.list_agents()
```

### Future: Service Discovery (Wave 4)

In Wave 4, agents will automatically discover each other:

```python
# Agent auto-registers on startup
# No manual registration needed

# Discover by capability
agents = registry.discover_by_capability("code-review")

# Call any available agent
response = call_any("code-review", "review.submit@v1", {...})
```

---

## Two-Agent Coordination Example

### Agent A: Orchestrator

```al
lang python
agent orchestrator
port 23457

expose workflow.execute@v1:
  params:
    pr_url string
  returns:
    workflow_id string
    status string
```

### Agent B: Code Reviewer

```al
lang python
agent code-reviewer
port 23456

expose review.submit@v1:
  params:
    pr_url string
  returns:
    review_id string
    status string
```

### Coordination Code

```python
from language.mcp_client import register_agent, call_agent

# Setup
register_agent("code-reviewer", "http://localhost:23456")
register_agent("orchestrator", "http://localhost:23457")

# Orchestrator calls code-reviewer
response = call_agent(
    "code-reviewer",
    "review.submit@v1",
    {"pr_url": "https://github.com/test/pr/1"}
)

if response.is_success():
    data = response.get_data()
    review_id = data["review_id"]

    # Poll for status
    status_response = call_agent(
        "code-reviewer",
        "review.status@v1",
        {"review_id": review_id}
    )

    print(status_response.get_data())
```

---

## Running the Demo

### Step 1: Install Dependencies

```bash
pip3 install fastapi uvicorn requests
```

### Step 2: Generate and Start Agent

```bash
# Generate server
python3 << 'EOF'
from language.mcp_server_generator import generate_mcp_server_from_pw

with open('examples/demo_agent.pw', 'r') as f:
    code = generate_mcp_server_from_pw(f.read())

with open('examples/demo_agent_server.py', 'w') as f:
    f.write(code)
EOF

# Run server
python3 examples/demo_agent_server.py
```

### Step 3: Run Coordination Demo

In another terminal:

```bash
python3 examples/two_agent_demo.py
```

This demonstrates:
- Health checks
- Verb discovery
- Agent-to-agent calls
- Error handling
- Bidirectional communication

---

## Best Practices

### 1. Use Descriptive Verb Names

✅ Good:
- `review.submit@v1`
- `task.execute@v1`
- `data.query@v1`

❌ Bad:
- `do@v1`
- `run@v1`
- `execute@v1`

### 2. Version Your Verbs

Always include `@v1`, `@v2`, etc. for compatibility:

```al
expose review.submit@v1:  # Initial version
expose review.submit@v2:  # New version with more params
```

### 3. Validate Parameters

Handler functions should validate all inputs:

```python
def handle_verb(params):
    if "required_field" not in params:
        return {"error": {"code": "E_ARGS", "message": "Missing required_field"}}

    # Process...
```

### 4. Use Standard Port (23456)

All AssertLang agents should use port 23456 unless there's a conflict.

### 5. Handle Errors Gracefully

```python
try:
    response = client.call("verb@v1", params)
    if response.is_success():
        data = response.get_data()
    else:
        # Log error, retry, or fail gracefully
        log.error(f"Call failed: {response.error}")
except MCPError as e:
    # Handle specific MCP errors
    if e.code == "E_TIMEOUT":
        # Retry logic
        pass
```

---

## Troubleshooting

### Agent Not Responding

```bash
# Check if agent is running
curl http://localhost:23456/health

# Check verbs
curl http://localhost:23456/verbs
```

### Connection Refused

- Ensure agent server is running
- Check port is correct (23456)
- Verify no firewall blocking

### Timeout Errors

Increase client timeout:

```python
client = MCPClient("http://localhost:23456", timeout=120)
```

### Missing Parameters

Check request payload matches verb definition:

```python
# Verb expects: {"pr_url": "..."}
# Must provide exactly that parameter name
response = client.call("review.submit@v1", {"pr_url": "https://..."})
```

---

## Next Steps

- **Week 2**: Build more complex coordination patterns
- **Week 3**: Cross-language agents (Python ↔ Node ↔ Go)
- **Wave 4**: Service discovery and registry
- **Wave 5**: Production deployment (Kubernetes, monitoring)

---

## API Reference

### MCPClient

```python
MCPClient(base_url, timeout=30, retries=3)
client.call(method, params) -> MCPResponse
client.health_check() -> dict
client.list_verbs() -> dict
```

### MCPResponse

```python
response.ok -> bool
response.version -> str
response.data -> dict | None
response.error -> dict | None
response.is_success() -> bool
response.get_data() -> dict  # Raises MCPError if failed
```

### AgentRegistry

```python
registry.register(agent_name, base_url)
registry.discover(agent_name) -> str | None
registry.get_client(agent_name) -> MCPClient
registry.list_agents() -> list[str]
```

---

For more examples, see `examples/two_agent_demo.py`.