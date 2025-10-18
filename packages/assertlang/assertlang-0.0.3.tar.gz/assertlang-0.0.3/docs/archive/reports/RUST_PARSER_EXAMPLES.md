# Rust Parser Examples

## Example 1: Basic Rust Server

### Input Rust Code

```rust
use warp::Filter;
use serde_json::{json, Value};

fn handle_echo_message_v1(params: &Value) -> Value {
    if !params.get("message").is_some() {
        return json!({
            "error": {
                "code": "E_ARGS",
                "message": "Missing required parameter: message"
            }
        });
    }

    json!({
        "echo": "echo_value",
        "timestamp": "timestamp_value"
    })
}

#[tokio::main]
async fn main() {
    let port: u16 = 9090;

    println!("MCP server for agent: minimal-rust-agent");

    warp::serve(routes)
        .run(([127, 0, 0, 1], port))
        .await;
}
```

### Extracted PW DSL

```
lang rust
agent minimal-rust-agent
port 9090

expose echo.message@v1:
  params:
    message string
  returns:
    echo string
    timestamp string
```

### Extraction Details

- **Agent Name**: Extracted from `println!` statement
- **Port**: Extracted from `let port: u16 = 9090`
- **Framework**: Detected as `warp` from `use warp::Filter`
- **Verb**: Converted `handle_echo_message_v1` → `echo.message@v1`
- **Params**: Extracted from `params.get("message")` check
- **Returns**: Extracted from `json!()` macro fields

---

## Example 2: Rust Server with Tools

### Input Rust Code

```rust
use warp::Filter;
use serde_json::{json, Value};
use std::collections::HashMap;

// Tool stubs
fn http_handle(params: &Value) -> Value {
    json!({
        "ok": true,
        "version": "v1",
        "message": "Tool stub: http"
    })
}

fn execute_tools(params: &Value) -> HashMap<String, Value> {
    let configured_tools = vec!["http"];
    let mut results = HashMap::new();

    for tool_name in configured_tools {
        let result = execute_tool(tool_name, params);
        results.insert(tool_name.to_string(), result);
    }

    results
}

/// Handler for fetch data
///
/// # Params
/// - url (String): URL to fetch
///
/// # Returns
/// - status (i32): HTTP status code
/// - data (String): Response data
/// - cached (bool): Whether data was cached
fn handle_fetch_data_v1(params: &Value) -> Value {
    if !params.get("url").is_some() {
        return json!({
            "error": {
                "code": "E_ARGS",
                "message": "Missing required parameter: url"
            }
        });
    }

    json!({
        "status": 200,
        "data": "response_data",
        "cached": false
    })
}

#[tokio::main]
async fn main() {
    let port: u16 = 9091;

    println!("MCP server for agent: tool-rust-agent");
    println!("Port: {}", port);
    println!("Exposed verbs: [fetch.data@v1]");

    warp::serve(routes)
        .run(([127, 0, 0, 1], port))
        .await;
}
```

### Extracted PW DSL

```
lang rust
agent tool-rust-agent
port 9091

tools:
  - http

expose fetch.data@v1:
  params:
    url string
  returns:
    status int
    data string
    cached bool
```

### Extraction Details

- **Agent Name**: Extracted from `println!` statement
- **Port**: Extracted from `let port: u16 = 9091`
- **Framework**: Detected as `warp` from imports
- **Tools**: Extracted from `vec!["http"]` in `execute_tools`
- **Verb**: Converted `handle_fetch_data_v1` → `fetch.data@v1`
- **Params**: Extracted from doc comments `# Params` section
- **Returns**: Extracted from doc comments `# Returns` section
- **Type Mapping**:
  - `String` → `string`
  - `i32` → `int`
  - `bool` → `bool`

---

## Example 3: Using Doc Comments

### Input Rust Code with Full Documentation

```rust
/// Handle create order request
///
/// This function creates a new order in the system.
///
/// # Params
/// - customer_id (String): Customer ID
/// - amount (i32): Order amount in cents
/// - currency (String): Currency code (USD, EUR, etc.)
///
/// # Returns
/// - order_id (String): Newly created order ID
/// - status (String): Order status (pending, confirmed, etc.)
/// - total (f64): Total amount with taxes
/// - created_at (String): ISO 8601 timestamp
fn handle_create_order_v1(params: &Value) -> Value {
    // Validate required params
    if !params.get("customer_id").is_some() {
        return json!({
            "error": {
                "code": "E_ARGS",
                "message": "Missing required parameter: customer_id"
            }
        });
    }

    if !params.get("amount").is_some() {
        return json!({
            "error": {
                "code": "E_ARGS",
                "message": "Missing required parameter: amount"
            }
        });
    }

    // Create order
    json!({
        "order_id": "ORDER-123",
        "status": "pending",
        "total": 99.99,
        "created_at": "2025-01-01T00:00:00Z"
    })
}
```

### Extracted PW DSL

```
lang rust
agent order-service
port 8080

expose create.order@v1:
  params:
    customer_id string
    amount int
    currency string
  returns:
    order_id string
    status string
    total float
    created_at string
```

### Extraction Details

- **Params**: Extracted from doc comment `# Params` section
- **Returns**: Extracted from doc comment `# Returns` section
- **Type Mapping**:
  - `String` → `string`
  - `i32` → `int`
  - `f64` → `float`
- **Confidence**: 100% (doc comments provide complete information)

---

## Example 4: Multiple Verbs

### Input Rust Code

```rust
fn handle_get_user_v1(params: &Value) -> Value {
    json!({
        "id": "user123",
        "name": "John Doe",
        "email": "john@example.com"
    })
}

fn handle_update_user_v1(params: &Value) -> Value {
    json!({
        "id": "user123",
        "updated": true
    })
}

fn handle_delete_user_v1(params: &Value) -> Value {
    json!({
        "deleted": true,
        "id": "user123"
    })
}

async fn verbs_handler() -> Result<impl Reply, warp::Rejection> {
    Ok(reply::json(&json!({
        "agent": "user-service",
        "verbs": ["get.user@v1", "update.user@v1", "delete.user@v1"]
    })))
}

#[tokio::main]
async fn main() {
    let port: u16 = 8080;
    warp::serve(routes).run(([0,0,0,0], port)).await;
}
```

### Extracted PW DSL

```
lang rust
agent user-service
port 8080

expose get.user@v1:
  returns:
    id string
    name string
    email string

expose update.user@v1:
  returns:
    id string
    updated bool

expose delete.user@v1:
  returns:
    deleted bool
    id string
```

### Extraction Details

- **Multiple Verbs**: All three handlers extracted
- **Verb Names**: Extracted from both handler names and verbs endpoint
- **Returns**: Extracted from `json!()` macro in each handler
- **Cross-Validation**: Verbs in handler names match verbs in routing

---

## CLI Usage Examples

### Basic Parsing

```bash
$ python3 reverse_parsers/cli.py main.rs
lang rust
agent minimal-rust-agent
port 9090

expose echo.message@v1:
  params:
    message string
  returns:
    echo string
    timestamp string
```

### With Metadata

```bash
$ python3 reverse_parsers/cli.py main.rs --metadata
# Extracted from rust code
# Framework: warp
# Confidence: 100%

lang rust
agent minimal-rust-agent
port 9090

expose echo.message@v1:
  params:
    message string
  returns:
    echo string
    timestamp string
```

### Verbose Output

```bash
$ python3 reverse_parsers/cli.py main.rs --verbose
Parsing main.rs (rust)...

============================================================
EXTRACTION STATISTICS
============================================================
Agent name:  minimal-rust-agent
Port:        9090
Framework:   warp
Confidence:  100%
Verbs found: 1
Tools found: 0

============================================================

lang rust
agent minimal-rust-agent
port 9090
...
```

### Save to File

```bash
$ python3 reverse_parsers/cli.py main.rs --output agent.pw
Parsing main.rs (rust)...
✅ Wrote PW DSL to: agent.pw
```

---

## Type Mapping Reference

| Rust Type | PW Type | Example |
|-----------|---------|---------|
| `String`, `str`, `&str` | `string` | `"hello"` |
| `i32`, `i64`, `u32`, `u64` | `int` | `42` |
| `f32`, `f64` | `float` | `3.14` |
| `bool` | `bool` | `true` |
| `Vec<T>` | `array<T>` | `vec![1, 2, 3]` |
| `HashMap<K, V>` | `object` | `HashMap::new()` |
| `serde_json::Value` | `object` | `json!({})` |
| `Option<T>` | `T` | Unwrapped |

---

## Confidence Scores

| Scenario | Confidence | Notes |
|----------|-----------|-------|
| Doc comments + framework detected | 100% | Best case |
| Function bodies + framework detected | 90-100% | Very good |
| Doc comments only | 80-90% | Good |
| Function bodies only | 70-80% | Acceptable |
| No framework detected | -20% | Penalty applied |

---

## Supported Patterns

### Framework Detection
- ✅ `use warp::Filter`
- ✅ `use actix_web::`
- ✅ `warp::serve()`
- ✅ `HttpServer::new()`

### Handler Functions
- ✅ `fn handle_verb_name_v1(...)`
- ✅ `fn handle_multi_word_verb_v2(...)`
- ✅ Snake case to dot notation conversion

### Port Extraction
- ✅ `let port: u16 = 8080`
- ✅ `const PORT: u16 = 8080`
- ✅ `.run(([127, 0, 0, 1], 9090))`
- ✅ `.bind("127.0.0.1:8080")`

### Tools Configuration
- ✅ `vec!["tool1", "tool2"]`
- ✅ `static CONFIGURED_TOOLS: &[&str] = &["tool"]`
- ✅ `const CONFIGURED_TOOLS: &[&str] = &["tool"]`

### Documentation
- ✅ Rust doc comments (`///`)
- ✅ `# Params` sections
- ✅ `# Returns` sections
- ✅ Type annotations in docs
