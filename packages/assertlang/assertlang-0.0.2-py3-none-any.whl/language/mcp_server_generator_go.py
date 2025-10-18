"""
MCP Server Generator for Go/net/http.

Generates Go HTTP servers from .al agent definitions.
Go uses compile-time tool imports (no dynamic loading like Python/Node.js).
"""

from __future__ import annotations

from language.agent_parser import AgentDefinition, ExposeBlock
from language.mcp_error_handling import get_go_error_middleware
from language.mcp_health_checks import get_go_health_check, get_health_endpoints_pattern
from language.mcp_security import get_go_security_middleware


def generate_go_mcp_server(agent: AgentDefinition) -> str:
    """
    Generate a complete Go HTTP MCP server from agent definition.

    Returns Go code that:
    - Runs on the specified port
    - Exposes MCP verbs as HTTP endpoints
    - Handles JSON-RPC requests
    - Returns MCP-formatted responses
    - Imports tools at compile time
    """

    code_parts = []

    # Package and imports (ALL imports must be here)
    code_parts.append(_generate_imports(agent))

    # Helper functions (error handling, health checks, security middleware)
    code_parts.append(_generate_helper_functions(agent))

    # Tool registry with compile-time imports
    code_parts.append(_generate_tool_registry(agent))

    # Handler functions for each exposed verb
    for expose in agent.exposes:
        code_parts.append(_generate_verb_handler(expose, agent))

    # Main MCP endpoint
    code_parts.append(_generate_mcp_endpoint(agent))

    # Health and utility endpoints
    code_parts.append(_generate_utility_endpoints(agent))

    # Main function
    code_parts.append(_generate_main(agent))

    return "\n\n".join(code_parts)


def _generate_imports(agent: AgentDefinition) -> str:
    """Generate package and ALL import statements (must be first after package)."""
    # All imports consolidated here - no imports elsewhere!
    imports = """package main

import (
\t"encoding/json"
\t"fmt"
\t"log"
\t"net/http"
\t"os"
\t"strings"
\t"sync"
\t"time"
)"""

    # Note: Tool imports commented out for now
    # In production, these would import actual tool adapters:
    # - Tool adapters need to be created first
    # - Build system would copy adapters into ./tools/
    # - Then these imports would work
    #
    # if agent.tools:
    #     tool_imports = []
    #     for tool in agent.tools:
    #         tool_path = tool.replace("-", "_")
    #         tool_imports.append(f'\t{tool_path} "user-service-mcp/tools/{tool_path}/adapters"')
    #     imports += "\n\nimport (\n" + "\n".join(tool_imports) + "\n)"

    return imports


def _generate_helper_functions(agent: AgentDefinition) -> str:
    """Generate helper functions (error handling, health check, security middleware)."""
    helpers = []

    # Get helper code and strip out embedded import statements
    error_middleware = get_go_error_middleware()
    health_check = get_go_health_check()
    security_middleware = get_go_security_middleware()

    # Remove import blocks from helper functions (imports are already at top)
    def strip_imports(code: str) -> str:
        """Remove import blocks from code."""
        lines = code.split('\n')
        result = []
        in_import_block = False

        for line in lines:
            if line.strip().startswith('import ('):
                in_import_block = True
                continue
            elif in_import_block and line.strip() == ')':
                in_import_block = False
                continue
            elif in_import_block:
                continue
            else:
                result.append(line)

        return '\n'.join(result).strip()

    helpers.append("// Error handling helpers")
    helpers.append(strip_imports(error_middleware))
    helpers.append("")
    helpers.append("// Health check helpers")
    helpers.append(strip_imports(health_check))
    helpers.append("")
    helpers.append("// Security middleware helpers")
    helpers.append(strip_imports(security_middleware))

    return "\n".join(helpers)


def _generate_tool_registry(agent: AgentDefinition) -> str:
    """Generate tool registry with compile-time tool imports."""
    if not agent.tools:
        # No tools configured - provide stub function
        return """// No tools configured
func executeTools(params map[string]interface{}) map[string]interface{} {
\treturn map[string]interface{}{}
}"""

    # Generate stub tool handlers (actual tool imports commented out above)
    tool_stubs = []
    for tool in agent.tools:
        tool_var = tool.replace("-", "_")
        # Create stub handler that returns placeholder
        tool_stubs.append(f"""// Stub handler for {tool} tool
func {tool_var}_Handle(params map[string]interface{{}}) map[string]interface{{}} {{
\treturn map[string]interface{{}}{{
\t\t"ok":      true,
\t\t"version": "v1",
\t\t"message": "Tool stub: {tool} (actual implementation requires tool adapter)",
\t\t"params":  params,
\t}}
}}""")

    tool_map_entries = []
    for tool in agent.tools:
        tool_var = tool.replace("-", "_")
        tool_map_entries.append(f'\t\t"{tool}": {tool_var}_Handle,')

    tools_list = ', '.join([f'"{t}"' for t in agent.tools])

    # Tool registry code (helpers are now in separate section)
    registry_code = """// Tool stubs (replace with actual imports in production)
%s

// Tool registry
var toolHandlers = map[string]func(map[string]interface{}) map[string]interface{}{
%s
}

func executeTool(toolName string, params map[string]interface{}) map[string]interface{} {
\thandler, ok := toolHandlers[toolName]
\tif !ok {
\t\treturn map[string]interface{}{
\t\t\t"ok":      false,
\t\t\t"version": "v1",
\t\t\t"error": map[string]interface{}{
\t\t\t\t"code":    "E_TOOL_NOT_FOUND",
\t\t\t\t"message": fmt.Sprintf("Tool not found: %%s", toolName),
\t\t\t},
\t\t}
\t}
\treturn handler(params)
}

func executeTools(params map[string]interface{}) map[string]interface{} {
\tconfiguredTools := []string{%s}
\tresults := make(map[string]interface{})

\tfor _, toolName := range configuredTools {
\t\tresult := executeTool(toolName, params)
\t\tresults[toolName] = result
\t}

\treturn results
}""" % ("\n\n".join(tool_stubs), chr(10).join(tool_map_entries), tools_list)

    return registry_code


def _generate_verb_handler(expose: ExposeBlock, agent: AgentDefinition) -> str:
    """Generate handler function for an exposed MCP verb."""

    # Convert verb name to Go function name (PascalCase)
    handler_name = expose.verb.replace(".", "_").replace("@", "_").replace("-", "_")
    parts = handler_name.split("_")
    func_name = "".join(word.capitalize() for word in parts)

    # Build parameter validation
    param_checks = []
    for param in expose.params:
        param_type = "string"
        if param["type"] == "int":
            param_type = "float64"
        elif param["type"] == "bool":
            param_type = "bool"

        param_checks.append(f'''\tif _, ok := params["{param["name"]}"].({param_type}); !ok {{
\t\treturn map[string]interface{{}}{{
\t\t\t"error": map[string]interface{{}}{{
\t\t\t\t"code":    "E_ARGS",
\t\t\t\t"message": "Missing required parameter: {param["name"]}",
\t\t\t}},
\t\t}}
\t}}''')

    param_validation = "\n".join(param_checks) if param_checks else "\t// No required parameters"

    # Build return fields (mock data)
    return_fields = []
    for ret in expose.returns:
        if ret["type"] == "string":
            return_fields.append(f'\t\t"{ret["name"]}": "{ret["name"]}_value",')
        elif ret["type"] == "int":
            return_fields.append(f'\t\t"{ret["name"]}": 0,')
        elif ret["type"] == "bool":
            return_fields.append(f'\t\t"{ret["name"]}": true,')
        elif ret["type"] == "array":
            return_fields.append(f'\t\t"{ret["name"]}": []interface{{}}{{}},')
        elif ret["type"] == "object":
            return_fields.append(f'\t\t"{ret["name"]}": map[string]interface{{}}{{}},')

    return_obj = "\n".join(return_fields)

    return f"""// Handler for {expose.verb}
func handle{func_name}(params map[string]interface{{}}) map[string]interface{{}} {{
{param_validation}

\t// TODO: Implement actual handler logic
\t// For now, return mock data
\treturn map[string]interface{{}}{{
{return_obj}
\t}}
}}"""


def _generate_mcp_endpoint(agent: AgentDefinition) -> str:
    """Generate main MCP JSON-RPC endpoint."""

    # Build verb routing
    verb_routes = []
    for expose in agent.exposes:
        handler_name = expose.verb.replace(".", "_").replace("@", "_").replace("-", "_")
        parts = handler_name.split("_")
        func_name = "".join(word.capitalize() for word in parts)

        verb_routes.append(f'''\tcase "{expose.verb}":
\t\tverbResult = handle{func_name}(verbParams)''')

    verb_routing = "\n".join(verb_routes)

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
    # Escape quotes for Go string literal
    tool_schemas_json_escaped = tool_schemas_json.replace('\\', '\\\\').replace('"', '\\"').replace('\n', ' ')

    has_tools = "true" if agent.tools else "false"

    return f'''// MCP endpoint handler
func mcpHandler(w http.ResponseWriter, r *http.Request) {{
\tif r.Method != "POST" {{
\t\thttp.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
\t\treturn
\t}}

\tvar req map[string]interface{{}}
\tif err := json.NewDecoder(r.Body).Decode(&req); err != nil {{
\t\thttp.Error(w, "Invalid JSON", http.StatusBadRequest)
\t\treturn
\t}}

\tmethod, _ := req["method"].(string)
\tid, _ := req["id"].(float64)

\tswitch method {{
\tcase "initialize":
\t\tresponse := map[string]interface{{}}{{
\t\t\t"jsonrpc": "2.0",
\t\t\t"id":      id,
\t\t\t"result": map[string]interface{{}}{{
\t\t\t\t"protocolVersion": "0.1.0",
\t\t\t\t"capabilities":    map[string]interface{{}}{{"tools": map[string]interface{{}}{{}}, "prompts": map[string]interface{{}}{{}}}},
\t\t\t\t"serverInfo":      map[string]interface{{}}{{"name": "{agent.name}", "version": "v1"}},
\t\t\t}},
\t\t}}
\t\tjson.NewEncoder(w).Encode(response)

\tcase "tools/list":
\t\t// Parse tool schemas from JSON
\t\tvar tools []interface{{}}
\t\ttoolsJSON := "{tool_schemas_json_escaped}"
\t\tif err := json.Unmarshal([]byte(toolsJSON), &tools); err != nil {{
\t\t\thttp.Error(w, "Internal error", http.StatusInternalServerError)
\t\t\treturn
\t\t}}
\t\tresponse := map[string]interface{{}}{{
\t\t\t"jsonrpc": "2.0",
\t\t\t"id":      id,
\t\t\t"result":  map[string]interface{{}}{{"tools": tools}},
\t\t}}
\t\tjson.NewEncoder(w).Encode(response)

\tcase "tools/call":
\t\tparams, _ := req["params"].(map[string]interface{{}})
\t\tverbName, _ := params["name"].(string)
\t\tverbParams, _ := params["arguments"].(map[string]interface{{}})

\t\tif verbName == "" {{
\t\t\tresponse := map[string]interface{{}}{{
\t\t\t\t"jsonrpc": "2.0",
\t\t\t\t"id":      id,
\t\t\t\t"error":   map[string]interface{{}}{{"code": -32602, "message": "Invalid params: missing tool name"}},
\t\t\t}}
\t\t\tjson.NewEncoder(w).Encode(response)
\t\t\treturn
\t\t}}

\t\t// Execute tools first (if configured)
\t\ttoolResults := make(map[string]interface{{}})
\t\ttoolsExecuted := []string{{}}

\t\tif {has_tools} {{
\t\t\ttoolResults = executeTools(verbParams)
\t\t\tfor k := range toolResults {{
\t\t\t\ttoolsExecuted = append(toolsExecuted, k)
\t\t\t}}
\t\t}}

\t\t// Route to appropriate verb handler
\t\tvar verbResult map[string]interface{{}}

\t\tswitch verbName {{
{verb_routing}
\t\tdefault:
\t\t\tresponse := map[string]interface{{}}{{
\t\t\t\t"jsonrpc": "2.0",
\t\t\t\t"id":      id,
\t\t\t\t"error":   map[string]interface{{}}{{"code": -32601, "message": fmt.Sprintf("Method not found: %s", verbName)}},
\t\t\t}}
\t\t\tjson.NewEncoder(w).Encode(response)
\t\t\treturn
\t\t}}

\t\t// Check for errors
\t\tif err, ok := verbResult["error"]; ok {{
\t\t\tresponse := map[string]interface{{}}{{
\t\t\t\t"jsonrpc": "2.0",
\t\t\t\t"id":      id,
\t\t\t\t"error":   map[string]interface{{}}{{"code": -32000, "message": err}},
\t\t\t}}
\t\t\tjson.NewEncoder(w).Encode(response)
\t\t\treturn
\t\t}}

\t\t// Build MCP-compliant response
\t\tresponseData := map[string]interface{{}}{{
\t\t\t"input_params":  verbParams,
\t\t\t"tool_results":  toolResults,
\t\t\t"metadata": map[string]interface{{}}{{
\t\t\t\t"mode":           "ide_integrated",
\t\t\t\t"agent_name":     "{agent.name}",
\t\t\t\t"timestamp":      time.Now().Format(time.RFC3339),
\t\t\t\t"tools_executed": toolsExecuted,
\t\t\t}},
\t\t}}

\t\t// Merge verb result
\t\tfor k, v := range verbResult {{
\t\t\tresponseData[k] = v
\t\t}}

\t\tresponse := map[string]interface{{}}{{
\t\t\t"jsonrpc": "2.0",
\t\t\t"id":      id,
\t\t\t"result":  responseData,
\t\t}}
\t\tjson.NewEncoder(w).Encode(response)

\tdefault:
\t\tresponse := map[string]interface{{}}{{
\t\t\t"jsonrpc": "2.0",
\t\t\t"id":      id,
\t\t\t"error":   map[string]interface{{}}{{"code": -32601, "message": fmt.Sprintf("Method not found: %s", method)}},
\t\t}}
\t\tjson.NewEncoder(w).Encode(response)
\t}}
}}'''


def _generate_utility_endpoints(agent: AgentDefinition) -> str:
    """Generate health and verbs endpoints."""

    verbs_list = ', '.join([f'"{e.verb}"' for e in agent.exposes])

    health_endpoints = get_health_endpoints_pattern("go", agent.name)

    return f"""{health_endpoints["health"]}

{health_endpoints["ready"]}

// List all exposed verbs
func verbsHandler(w http.ResponseWriter, r *http.Request) {{
\tresponse := map[string]interface{{}}{{
\t\t"agent": "{agent.name}",
\t\t"verbs": []string{{{verbs_list}}},
\t}}
\tjson.NewEncoder(w).Encode(response)
}}"""


def _generate_main(agent: AgentDefinition) -> str:
    """Generate main function."""

    verbs_list = ', '.join([e.verb for e in agent.exposes])

    return f"""func main() {{
\t// Apply security middleware chain
\tmcpWithMiddleware := rateLimitMiddleware(
\t\tsecurityHeadersMiddleware(
\t\t\tcorsMiddleware(mcpHandler),
\t\t),
\t)

\thttp.HandleFunc("/mcp", mcpWithMiddleware)
\thttp.HandleFunc("/health", healthHandler)
\thttp.HandleFunc("/ready", readyHandler)
\thttp.HandleFunc("/verbs", verbsHandler)

\tport := "{agent.port}"
\tlog.Printf("MCP server for agent: {agent.name}")
\tlog.Printf("Port: %s", port)
\tlog.Printf("Exposed verbs: [{verbs_list}]")
\tlog.Printf("Health check: http://127.0.0.1:%s/health", port)
\tlog.Printf("Readiness check: http://127.0.0.1:%s/ready", port)
\tlog.Printf("MCP endpoint: http://127.0.0.1:%s/mcp", port)

\tif err := http.ListenAndServe(":"+port, nil); err != nil {{
\t\tlog.Fatal(err)
\t}}
}}"""


def generate_go_server_from_pw(pw_code: str) -> str:
    """
    Convenience function: parse .al code and generate Go MCP server.

    Args:
        pw_code: .al file content

    Returns:
        Go code for MCP server
    """
    from language.agent_parser import parse_agent_pw

    agent = parse_agent_pw(pw_code)
    return generate_go_mcp_server(agent)
