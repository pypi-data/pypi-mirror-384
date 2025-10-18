# AssertLang MCP Client Library

Python client library for calling AssertLang services over HTTP using the MCP protocol.

## Installation

```bash
# From project root
pip install -e .
```

## Quick Start

### Simple Function Call

```python
from promptware import call_verb

result = call_verb(
    service="user-service",
    verb="user.get@v1",
    params={"user_id": "123"},
    address="http://localhost:23450"
)

print(result)
```

### Reusable Client

```python
from promptware import MCPClient

client = MCPClient("http://localhost:23450")

# Initialize connection (optional but recommended)
server_info = client.initialize()
print(f"Connected to: {server_info['serverInfo']['name']}")

# List available tools
tools = client.list_tools()
for tool in tools:
    print(f"- {tool['name']}: {tool['description']}")

# Call verbs
result = client.call("user.get@v1", {"user_id": "123"})
print(result)

# Cleanup
client.close()
```

### Context Manager (Recommended)

```python
from promptware import MCPClient

with MCPClient("http://localhost:23450") as client:
    result = client.call("user.get@v1", {"user_id": "123"})
    print(result)
# Automatic cleanup
```

## API Reference

### `call_verb()`

Simple function for one-off verb calls.

```python
call_verb(
    service: str,           # Service name (documentation only)
    verb: str,              # Verb name (e.g., "user.get@v1")
    params: Dict[str, Any], # Verb parameters
    address: str = None,    # Service URL (default: http://localhost:23450)
    timeout: float = 30.0,  # Request timeout in seconds
    retries: int = 3        # Number of retry attempts
) -> Dict[str, Any]
```

**Returns:** Result dict with keys:
- `input_params`: Echo of input parameters
- `tool_results`: Results from tool execution
- `metadata`: Execution metadata (mode, timestamp, tools_executed)
- ...verb-specific return values...

**Raises:**
- `InvalidVerbError`: Verb doesn't exist
- `InvalidParamsError`: Invalid parameters
- `ConnectionError`: Connection failed
- `TimeoutError`: Request timed out
- `MCPError`: Other MCP errors

### `MCPClient`

Reusable client for multiple calls.

#### Constructor

```python
MCPClient(
    address: str,              # Base URL (e.g., "http://localhost:23450")
    timeout: float = 30.0,     # Request timeout in seconds
    retries: int = 3,          # Retry attempts for transient failures
    backoff_factor: float = 2.0 # Exponential backoff multiplier
)
```

#### Methods

##### `initialize()`

Initialize connection and get server capabilities.

```python
result = client.initialize()
# Returns:
# {
#     "protocolVersion": "0.1.0",
#     "capabilities": {"tools": {}, "prompts": {}},
#     "serverInfo": {"name": "service-name", "version": "v1"}
# }
```

##### `list_tools()`

List all available tools/verbs.

```python
tools = client.list_tools()
# Returns: List[Dict] with tool definitions
# Each tool has: name, description, inputSchema
```

##### `call()`

Call an MCP verb.

```python
result = client.call(
    verb: str,                    # Verb name
    arguments: Dict[str, Any],    # Verb arguments
    request_id: int = None        # Optional JSON-RPC ID
)
```

##### `get_server_info()`

Get cached server info from `initialize()`.

```python
info = client.get_server_info()
# Returns None if initialize() not called yet
```

##### `get_tool_schema()`

Get schema for a specific tool.

```python
schema = client.get_tool_schema("user.get@v1")
# Returns None if tool doesn't exist or list_tools() not called
```

##### `close()`

Close the client connection.

```python
client.close()
```

## Error Handling

### Exception Hierarchy

```
MCPError (base)
├── ConnectionError        # Failed to connect
├── TimeoutError          # Request timed out
├── ServiceUnavailableError # 5xx server error
├── InvalidVerbError      # Verb not found
├── InvalidParamsError    # Invalid parameters
└── ProtocolError         # MCP protocol violation
```

### Example

```python
from promptware import call_verb
from promptware.exceptions import (
    InvalidVerbError,
    InvalidParamsError,
    TimeoutError,
    ConnectionError,
)

try:
    result = call_verb(
        service="user-service",
        verb="user.get@v1",
        params={"user_id": "123"},
        address="http://localhost:23450",
        timeout=5.0,
        retries=3
    )
except InvalidVerbError as e:
    print(f"Verb not found: {e.verb}")
except InvalidParamsError as e:
    print(f"Invalid params: {e.validation_errors}")
except TimeoutError:
    print("Request timed out")
except ConnectionError as e:
    print(f"Connection failed: {e}")
```

## Retry Logic

The client automatically retries transient failures:

- **Retry on:**
  - Connection errors
  - 5xx server errors
  - Timeout errors

- **Don't retry on:**
  - 4xx client errors (bad params, verb not found)
  - Successful responses

**Exponential backoff:**
```
Attempt 1: immediate
Attempt 2: 1s delay
Attempt 3: 2s delay
Attempt 4: 4s delay (if retries=3)
```

**Configure retries:**
```python
client = MCPClient(
    "http://localhost:23450",
    timeout=10.0,
    retries=5,           # 5 retry attempts
    backoff_factor=1.5   # 1s, 1.5s, 2.25s, ...
)
```

## Response Format

All verb calls return a dict with this structure:

```python
{
    "input_params": {
        # Echo of your input parameters
        "user_id": "123"
    },
    "tool_results": {
        # Results from tool execution
        "http": {
            "ok": True,
            "data": {"status": 200, ...}
        }
    },
    "metadata": {
        "mode": "ide_integrated",  # or "standalone_ai"
        "agent_name": "user-service",
        "timestamp": "2025-09-30T...",
        "tools_executed": ["http"]
    },
    # Verb-specific return values
    "user_id": "123",
    "name": "John Doe",
    "email": "john@example.com"
}
```

## Service-to-Service Communication

Example: Order service calling user service

```python
from promptware import MCPClient

def create_order(user_id: str, items: list, total: float):
    # Validate user first
    with MCPClient("http://user-service:23450") as user_client:
        user = user_client.call("user.get@v1", {"user_id": user_id})

        if user.get('status') != 'active':
            raise ValueError("User is not active")

    # Create order
    with MCPClient("http://order-service:23451") as order_client:
        order = order_client.call("order.create@v1", {
            "user_id": user_id,
            "items": items,
            "total": total
        })

        return order
```

## Advanced Usage

### Inspect Tool Schemas

```python
with MCPClient("http://localhost:23450") as client:
    tools = client.list_tools()

    for tool in tools:
        print(f"Tool: {tool['name']}")
        print(f"Description: {tool['description']}")

        schema = tool['inputSchema']
        required = schema.get('required', [])

        for param, info in schema['properties'].items():
            req = "*" if param in required else " "
            print(f"  {req} {param}: {info['type']}")
```

### Access Tool Results

```python
result = client.call("fetch.url@v1", {
    "url": "https://api.github.com/zen",
    "method": "GET"
})

# Check which tools ran
print(result['metadata']['tools_executed'])  # ['http']

# Access tool results
http_result = result['tool_results']['http']
if http_result['ok']:
    print(http_result['data']['body'])
```

### Custom Timeouts Per Call

```python
# Short-lived client for fast operations
fast_client = MCPClient("http://localhost:23450", timeout=2.0, retries=1)

# Long-lived client for slow operations
slow_client = MCPClient("http://localhost:23451", timeout=60.0, retries=5)
```

## Testing

See `tests/test_client.py` for unit tests and `tests/test_client_integration.py` for integration tests.

```bash
# Run unit tests
python3 tests/test_client.py

# Run integration tests (requires running server)
python3 tests/test_client_integration.py
```

## Examples

See `examples/client_examples.py` for complete working examples:
- Simple calls
- Reusable clients
- Context managers
- Error handling
- Service-to-service communication
- Tool inspection
- Custom timeouts

## Next Steps

- See `docs/http-transport-integration.md` for full integration plan
- Check `examples/` for two-service demo
- Read MCP protocol spec for advanced features
