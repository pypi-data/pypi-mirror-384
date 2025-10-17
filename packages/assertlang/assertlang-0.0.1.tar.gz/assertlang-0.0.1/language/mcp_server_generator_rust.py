"""
MCP Server Generator for Rust.

Generates Rust HTTP servers from .al agent definitions.
Rust uses compile-time tool imports (no dynamic loading).
"""

from __future__ import annotations

from language.agent_parser import AgentDefinition, ExposeBlock
from language.mcp_error_handling import get_rust_error_middleware
from language.mcp_health_checks import get_health_endpoints_pattern, get_rust_health_check
from language.mcp_security import get_rust_security_middleware


def generate_rust_mcp_server(agent: AgentDefinition) -> str:
    """
    Generate a complete Rust HTTP MCP server from agent definition.

    Returns Rust code that:
    - Runs on the specified port
    - Exposes MCP verbs as HTTP endpoints
    - Handles JSON-RPC requests
    - Returns MCP-formatted responses
    - Imports tools at compile time
    """

    code_parts = []

    # Dependencies and imports (ALL imports must be here)
    code_parts.append(_generate_imports(agent))

    # Helper functions (error handling, health checks, security middleware)
    code_parts.append(_generate_helper_functions(agent))

    # Tool registry with compile-time imports
    code_parts.append(_generate_tool_registry(agent))

    # Handler functions for each exposed verb
    for expose in agent.exposes:
        code_parts.append(_generate_verb_handler(expose, agent))

    # Main MCP endpoint handler
    code_parts.append(_generate_mcp_endpoint(agent))

    # Utility endpoints
    code_parts.append(_generate_utility_endpoints(agent))

    # Main function
    code_parts.append(_generate_main(agent))

    return "\n\n".join(code_parts)


def _generate_imports(agent: AgentDefinition) -> str:
    """Generate use statements and module declarations."""
    # All imports consolidated here - no imports elsewhere!
    imports = """use serde::Deserialize;
use serde_json::{json, Value};
use std::collections::HashMap;
use std::env;
use std::fmt;
use std::sync::{Arc, Mutex, Once};
use std::time::{Duration, Instant, SystemTime};
use warp::http::header::{HeaderMap, HeaderValue};
use warp::{Filter, reply, Reply};"""

    # Note: Tool imports commented out for now
    # In production, these would import actual tool modules:
    # - Tool modules need to be created first
    # - Build system would place them in ./tools/
    # - Then these imports would work
    #
    # if agent.tools:
    #     tool_mods = []
    #     for tool in agent.tools:
    #         mod_name = tool.replace("-", "_")
    #         tool_mods.append(f"mod {mod_name};")
    #     imports += "\n\n// Tool modules\n" + "\n".join(tool_mods)

    return imports


def _generate_helper_functions(agent: AgentDefinition) -> str:
    """Generate helper functions (error handling, health check, security middleware)."""
    helpers = []

    # Get helper code and fix issues
    error_middleware = get_rust_error_middleware()
    health_check = get_rust_health_check()
    security_middleware = get_rust_security_middleware()

    # Remove import blocks and lazy_static from helper functions (imports are already at top)
    def strip_imports_and_fix(code: str) -> str:
        """Remove import blocks and fix lazy_static usage."""
        lines = code.split('\n')
        result = []
        skip_until_close = False

        for line in lines:
            # Skip use statements
            if line.strip().startswith('use '):
                continue
            # Skip lazy_static blocks - we'll create static without it
            elif 'lazy_static::lazy_static!' in line or 'lazy_static!' in line:
                skip_until_close = True
                continue
            elif skip_until_close:
                if line.strip() == '}':
                    skip_until_close = False
                continue
            else:
                result.append(line)

        return '\n'.join(result).strip()

    # Add Display trait implementation for McpError
    error_with_display = strip_imports_and_fix(error_middleware)

    # Insert Display trait implementation after McpError enum
    error_with_display = error_with_display.replace(
        """impl McpError {""",
        """impl fmt::Display for McpError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            McpError::Validation(msg) => write!(f, "Validation error: {}", msg),
            McpError::Timeout(msg) => write!(f, "Timeout: {}", msg),
            McpError::NotFound(msg) => write!(f, "Not found: {}", msg),
            McpError::Internal(msg) => write!(f, "Internal error: {}", msg),
        }
    }
}

impl McpError {"""
    )

    helpers.append("// Error handling helpers")
    helpers.append(error_with_display)
    helpers.append("")
    helpers.append("// Health check helpers")

    # Fix health check - replace lazy_static with static initialization
    health_fixed = strip_imports_and_fix(health_check)
    # Replace chrono usage with standard library
    health_fixed = health_fixed.replace(
        'chrono::Utc::now().to_rfc3339()',
        'SystemTime::now().duration_since(SystemTime::UNIX_EPOCH).unwrap().as_secs()'
    )
    # Replace the static ref line with a simple function that creates new instances
    health_fixed = health_fixed.replace(
        """static ref HEALTH_CHECKER: HealthCheck = HealthCheck::new();""",
        ""
    )
    # Add a static instance using Once pattern (simpler than lazy_static)
    health_fixed += """

// Static health checker instance
static mut HEALTH_CHECKER_INSTANCE: Option<HealthCheck> = None;
static HEALTH_CHECKER_INIT: Once = Once::new();

fn get_health_checker() -> &'static HealthCheck {
    unsafe {
        HEALTH_CHECKER_INIT.call_once(|| {
            HEALTH_CHECKER_INSTANCE = Some(HealthCheck::new());
        });
        HEALTH_CHECKER_INSTANCE.as_ref().unwrap()
    }
}

// For backwards compatibility
struct HealthCheckerWrapper;
impl HealthCheckerWrapper {
    fn check_liveness(&self) -> Value {
        get_health_checker().check_liveness()
    }
    fn check_readiness(&self) -> Value {
        get_health_checker().check_readiness()
    }
}

static HEALTH_CHECKER: HealthCheckerWrapper = HealthCheckerWrapper;"""

    helpers.append(health_fixed)
    helpers.append("")
    helpers.append("// Security middleware helpers")

    # Fix security - replace lazy_static with simple static
    security_fixed = strip_imports_and_fix(security_middleware)
    security_fixed = security_fixed.replace(
        """static ref RATE_LIMITER: RateLimiter = RateLimiter::new(100, Duration::from_secs(60));""",
        ""
    )

    # Add simple static initializer
    security_fixed += """

// Static rate limiter instance
static mut RATE_LIMITER_INSTANCE: Option<RateLimiter> = None;
static RATE_LIMITER_INIT: Once = Once::new();

fn get_rate_limiter() -> &'static RateLimiter {
    unsafe {
        RATE_LIMITER_INIT.call_once(|| {
            RATE_LIMITER_INSTANCE = Some(RateLimiter::new(100, Duration::from_secs(60)));
        });
        RATE_LIMITER_INSTANCE.as_ref().unwrap()
    }
}"""

    helpers.append(security_fixed)

    return "\n".join(helpers)


def _generate_tool_registry(agent: AgentDefinition) -> str:
    """Generate tool registry with compile-time tool imports."""
    if not agent.tools:
        # No tools configured - provide stub function
        return """// No tools configured
fn execute_tools(_params: &Value) -> HashMap<String, Value> {
    HashMap::new()
}"""

    # Generate stub tool handlers (actual tool imports commented out above)
    tool_stubs = []
    for tool in agent.tools:
        tool_var = tool.replace("-", "_")
        # Create stub handler that returns placeholder
        tool_stubs.append(f"""// Stub handler for {tool} tool
fn {tool_var}_handle(params: &Value) -> Value {{
    json!({{
        "ok": true,
        "version": "v1",
        "message": "Tool stub: {tool} (actual implementation requires tool module)",
        "params": params
    }})
}}""")

    tool_cases = []
    for tool in agent.tools:
        tool_var = tool.replace("-", "_")
        tool_cases.append(f'        "{tool}" => {tool_var}_handle(params)')

    tools_list = ', '.join([f'"{t}"' for t in agent.tools])

    # Tool registry code
    registry_code = f"""// Tool stubs (replace with actual imports in production)
{chr(10).join(tool_stubs)}

// Tool registry
fn execute_tool(tool_name: &str, params: &Value) -> Value {{
    match tool_name {{
{chr(10).join(tool_cases)},
        _ => json!({{
            "ok": false,
            "version": "v1",
            "error": {{
                "code": "E_TOOL_NOT_FOUND",
                "message": format!("Tool not found: {{}}", tool_name)
            }}
        }})
    }}
}}

fn execute_tools(params: &Value) -> HashMap<String, Value> {{
    let configured_tools = vec![{tools_list}];
    let mut results = HashMap::new();

    for tool_name in configured_tools {{
        let result = execute_tool(tool_name, params);
        results.insert(tool_name.to_string(), result);
    }}

    results
}}"""

    return registry_code


def _generate_verb_handler(expose: ExposeBlock, agent: AgentDefinition) -> str:
    """Generate handler function for an exposed MCP verb."""

    # Convert verb name to Rust function name (snake_case)
    handler_name = expose.verb.replace(".", "_").replace("@", "_").replace("-", "_").lower()
    func_name = f"handle_{handler_name}"

    # Build parameter validation
    param_checks = []
    for param in expose.params:
        param_checks.append(f"""    if !params.get("{param["name"]}").is_some() {{
        return json!({{
            "error": {{
                "code": "E_ARGS",
                "message": "Missing required parameter: {param["name"]}"
            }}
        }});
    }}""")

    param_validation = "\n".join(param_checks) if param_checks else "    // No required parameters"

    # Build return fields (mock data)
    return_fields = []
    for ret in expose.returns:
        if ret["type"] == "string":
            return_fields.append(f'        "{ret["name"]}": "{ret["name"]}_value"')
        elif ret["type"] == "int":
            return_fields.append(f'        "{ret["name"]}": 0')
        elif ret["type"] == "bool":
            return_fields.append(f'        "{ret["name"]}": true')
        elif ret["type"] == "array":
            return_fields.append(f'        "{ret["name"]}": []')
        elif ret["type"] == "object":
            return_fields.append(f'        "{ret["name"]}": {{}}')

    return_obj = ",\n".join(return_fields)

    return f"""// Handler for {expose.verb}
fn {func_name}(params: &Value) -> Value {{
{param_validation}

    // TODO: Implement actual handler logic
    json!({{
{return_obj}
    }})
}}"""


def _generate_mcp_endpoint(agent: AgentDefinition) -> str:
    """Generate main MCP JSON-RPC endpoint handler."""

    # Build verb routing
    verb_routes = []
    for expose in agent.exposes:
        handler_name = expose.verb.replace(".", "_").replace("@", "_").replace("-", "_").lower()
        func_name = f"handle_{handler_name}"
        verb_routes.append(f'        "{expose.verb}" => {func_name}(&verb_params)')

    verb_routing = ",\n".join(verb_routes)

    # Build tool schemas
    tool_schemas = []
    for expose in agent.exposes:
        properties = {}
        required = []

        for param in expose.params:
            param_type = param["type"]
            if param_type == "int":
                param_type = "integer"
            elif param_type == "bool":
                param_type = "boolean"

            properties[param["name"]] = {
                "type": param_type,
                "description": f"Parameter: {param['name']}"
            }
            required.append(param["name"])

        tool_schemas.append({
            "name": expose.verb,
            "description": expose.prompt_template or f"Execute {expose.verb}",
            "inputSchema": {
                "type": "object",
                "properties": properties,
                "required": required
            }
        })

    import json
    tool_schemas_json = json.dumps(tool_schemas, indent=2)

    has_tools = agent.tools is not None and len(agent.tools) > 0

    tools_execution = """
        // Execute tools first (if configured)
        let tool_results = execute_tools(&verb_params);
        let tools_executed: Vec<String> = tool_results.keys().cloned().collect();""" if has_tools else """
        // No tools configured
        let tool_results: HashMap<String, Value> = HashMap::new();
        let tools_executed: Vec<String> = Vec::new();"""

    return f"""// MCP endpoint handler
#[derive(Deserialize)]
struct JsonRpcRequest {{
    jsonrpc: String,
    id: Option<i64>,
    method: String,
    params: Option<Value>,
}}

async fn mcp_handler(req: JsonRpcRequest) -> Result<impl Reply, warp::Rejection> {{
    let id = req.id.unwrap_or(0);

    let response = match req.method.as_str() {{
        "initialize" => json!({{
            "jsonrpc": "2.0",
            "id": id,
            "result": {{
                "protocolVersion": "0.1.0",
                "capabilities": {{ "tools": {{}}, "prompts": {{}} }},
                "serverInfo": {{ "name": "{agent.name}", "version": "v1" }}
            }}
        }}),

        "tools/list" => {{
            let tools: Value = serde_json::from_str(r#"{tool_schemas_json}"#).unwrap();
            json!({{
                "jsonrpc": "2.0",
                "id": id,
                "result": {{ "tools": tools }}
            }})
        }},

        "tools/call" => {{
            let empty_params = json!({{}});
            let params = req.params.as_ref().unwrap_or(&empty_params);
            let verb_name = params.get("name")
                .and_then(Value::as_str)
                .unwrap_or("");
            let verb_params = params.get("arguments")
                .unwrap_or(&json!({{}}))
                .clone();

            if verb_name.is_empty() {{
                return Ok(reply::json(&json!({{
                    "jsonrpc": "2.0",
                    "id": id,
                    "error": {{ "code": -32602, "message": "Invalid params: missing tool name" }}
                }})));
            }}
{tools_execution}

            // Route to appropriate verb handler
            let verb_result = match verb_name {{
{verb_routing},
                _ => json!({{
                    "error": {{
                        "code": "E_VERB_NOT_FOUND",
                        "message": format!("Verb not found: {{}}", verb_name)
                    }}
                }})
            }};

            // Check for errors
            if verb_result.get("error").is_some() {{
                return Ok(reply::json(&json!({{
                    "jsonrpc": "2.0",
                    "id": id,
                    "error": {{ "code": -32000, "message": verb_result["error"] }}
                }})));
            }}

            // Build MCP-compliant response
            let timestamp = SystemTime::now()
                .duration_since(SystemTime::UNIX_EPOCH)
                .unwrap()
                .as_secs();
            let mut response_data = json!({{
                "input_params": verb_params,
                "tool_results": tool_results,
                "metadata": {{
                    "mode": "ide_integrated",
                    "agent_name": "{agent.name}",
                    "timestamp": timestamp,
                    "tools_executed": tools_executed
                }}
            }});

            // Merge verb result
            if let (Some(response_obj), Some(verb_obj)) =
                (response_data.as_object_mut(), verb_result.as_object()) {{
                for (k, v) in verb_obj {{
                    response_obj.insert(k.clone(), v.clone());
                }}
            }}

            json!({{
                "jsonrpc": "2.0",
                "id": id,
                "result": response_data
            }})
        }},

        _ => json!({{
            "jsonrpc": "2.0",
            "id": id,
            "error": {{ "code": -32601, "message": format!("Method not found: {{}}", req.method) }}
        }})
    }};

    Ok(reply::json(&response))
}}"""


def _generate_utility_endpoints(agent: AgentDefinition) -> str:
    """Generate health and verbs endpoints."""

    verbs_list = ', '.join([f'"{e.verb}"' for e in agent.exposes])

    health_endpoints = get_health_endpoints_pattern("rust", agent.name)

    return f"""{health_endpoints["health"]}

{health_endpoints["ready"]}

// List all exposed verbs
async fn verbs_handler() -> Result<impl Reply, warp::Rejection> {{
    Ok(reply::json(&json!({{
        "agent": "{agent.name}",
        "verbs": [{verbs_list}]
    }})))
}}"""


def _generate_main(agent: AgentDefinition) -> str:
    """Generate main function."""

    verbs_list = ', '.join([e.verb for e in agent.exposes])

    return f"""#[tokio::main]
async fn main() {{
    let mcp_route = warp::post()
        .and(warp::path("mcp"))
        .and(warp::body::json())
        .and_then(mcp_handler);

    let health_route = warp::get()
        .and(warp::path("health"))
        .and_then(health_handler);

    let ready_route = warp::get()
        .and(warp::path("ready"))
        .and_then(ready_handler);

    let verbs_route = warp::get()
        .and(warp::path("verbs"))
        .and_then(verbs_handler);

    let routes = mcp_route
        .or(health_route)
        .or(ready_route)
        .or(verbs_route)
        .with(with_cors());

    let port: u16 = {agent.port};

    println!("MCP server for agent: {agent.name}");
    println!("Port: {{}}", port);
    println!("Exposed verbs: [{verbs_list}]");
    println!("Health check: http://127.0.0.1:{{}}/health", port);
    println!("Readiness check: http://127.0.0.1:{{}}/ready", port);
    println!("MCP endpoint: http://127.0.0.1:{{}}/mcp", port);

    warp::serve(routes)
        .run(([127, 0, 0, 1], port))
        .await;
}}"""


def generate_rust_server_from_pw(pw_code: str) -> str:
    """
    Convenience function: parse .al code and generate Rust MCP server.

    Args:
        pw_code: .al file content

    Returns:
        Rust code for MCP server
    """
    from language.agent_parser import parse_agent_pw

    agent = parse_agent_pw(pw_code)
    return generate_rust_mcp_server(agent)
