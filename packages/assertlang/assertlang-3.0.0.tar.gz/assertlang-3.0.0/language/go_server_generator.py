"""
DEPRECATED: Use language.mcp_server_generator_go instead.

This module is deprecated and will be removed in a future version.
Use the new unified generator system in language.mcp_server_generator_go.

Go MCP Server Generator for Promptware agents.

Generates Go HTTP server-based MCP servers from .al agent definitions.
"""

from __future__ import annotations

from language.agent_parser import AgentDefinition, ExposeBlock


def generate_go_mcp_server(agent: AgentDefinition) -> str:
    """
    Generate a complete Go MCP server from agent definition.

    Returns Go HTTP server code that:
    - Runs on the specified port
    - Exposes MCP verbs as HTTP endpoints
    - Handles JSON-RPC requests
    - Returns MCP-formatted responses
    """

    code_parts = []

    # Package and imports
    code_parts.append(_generate_imports(agent))

    # Type definitions
    code_parts.append(_generate_types(agent))

    # Handler functions
    for expose in agent.exposes:
        code_parts.append(_generate_verb_handler(expose, agent))

    # Main MCP endpoint
    code_parts.append(_generate_mcp_endpoint(agent))

    # Main function
    code_parts.append(_generate_main(agent))

    return "\n\n".join(code_parts)


def _generate_imports(agent: AgentDefinition) -> str:
    """Generate package declaration and imports."""
    return """package main

import (
\t"encoding/json"
\t"fmt"
\t"log"
\t"net/http"
\t"sync/atomic"
\t"time"
)"""


def _generate_types(agent: AgentDefinition) -> str:
    """Generate Go type definitions."""
    return """// AgentState holds the agent's runtime state
type AgentState struct {
\tAgentName       string
\tStartedAt       time.Time
\tRequestsHandled int64
}

// MCPRequest represents an incoming MCP request
type MCPRequest struct {
\tMethod string                 `json:"method"`
\tParams map[string]interface{} `json:"params"`
}

// MCPResponse represents an MCP response
type MCPResponse struct {
\tOK      bool                   `json:"ok"`
\tVersion string                 `json:"version"`
\tData    map[string]interface{} `json:"data,omitempty"`
\tError   *MCPError              `json:"error,omitempty"`
}

// MCPError represents an error in MCP format
type MCPError struct {
\tCode    string `json:"code"`
\tMessage string `json:"message"`
}

var agentState = &AgentState{
\tAgentName: "agent_name",
\tStartedAt: time.Now(),
}"""


def _generate_verb_handler(expose: ExposeBlock, agent: AgentDefinition) -> str:
    """Generate handler function for an exposed MCP verb."""
    handler_name = expose.verb.replace(".", "_").replace("@", "_")

    # Build parameter validation
    param_checks = []
    for param in expose.params:
        param_checks.append(
            f'\tif _, ok := params["{param["name"]}"]; !ok {{\n'
            f'\t\treturn nil, &MCPError{{Code: "E_ARGS", Message: "Missing required parameter: {param["name"]}"}}\n'
            f'\t}}'
        )

    param_validation = "\n".join(param_checks) if param_checks else "\t// No required parameters"

    # Generate return structure
    return_fields = []
    for ret in expose.returns:
        if ret["type"] == "string":
            return_fields.append(f'\t\t"{ret["name"]}": "{ret["name"]}_value"')
        elif ret["type"] == "int":
            return_fields.append(f'\t\t"{ret["name"]}": 0')
        elif ret["type"] == "bool":
            return_fields.append(f'\t\t"{ret["name"]}": true')
        else:
            return_fields.append(f'\t\t"{ret["name"]}": nil')

    return_obj = ",\n".join(return_fields)

    handler_title = handler_name.title()
    return f'''// handle{handler_title} handles the {expose.verb} verb
func handle{handler_title}(params map[string]interface{{}}) (map[string]interface{{}}, *MCPError) {{{{
{param_validation}

\tatomic.AddInt64(&agentState.RequestsHandled, 1)

\t// TODO: Implement actual handler logic
\treturn map[string]interface{{}}{{{{
{return_obj},
\t}}}}, nil
}}}}'''


def _generate_mcp_endpoint(agent: AgentDefinition) -> str:
    """Generate main MCP JSON-RPC endpoint handler."""

    # Build verb routing
    verb_routes = []
    for expose in agent.exposes:
        handler_name = expose.verb.replace(".", "_").replace("@", "_")
        handler_title = handler_name.title()
        verb_routes.append(
            f'\tcase "{expose.verb}":\n'
            f'\t\treturn handle{handler_title}(req.Params)'
        )

    verb_routing = "\n".join(verb_routes)

    return f'''// mcpHandler handles MCP JSON-RPC requests
func mcpHandler(w http.ResponseWriter, r *http.Request) {{
\tw.Header().Set("Content-Type", "application/json")

\tif r.Method != http.MethodPost {{
\t\thttp.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
\t\treturn
\t}}

\tvar req MCPRequest
\tif err := json.NewDecoder(r.Body).Decode(&req); err != nil {{
\t\tjson.NewEncoder(w).Encode(MCPResponse{{
\t\t\tOK:      false,
\t\t\tVersion: "v1",
\t\t\tError:   &MCPError{{Code: "E_PARSE", Message: err.Error()}},
\t\t}})
\t\treturn
\t}}

\tif req.Method == "" {{
\t\tjson.NewEncoder(w).Encode(MCPResponse{{
\t\t\tOK:      false,
\t\t\tVersion: "v1",
\t\t\tError:   &MCPError{{Code: "E_ARGS", Message: "Missing 'method' in request"}},
\t\t}})
\t\treturn
\t}}

\t// Route to appropriate handler
\tvar result map[string]interface{{}}
\tvar mcpErr *MCPError

\tswitch req.Method {{
{verb_routing}
\tdefault:
\t\tmcpErr = &MCPError{{Code: "E_METHOD", Message: fmt.Sprintf("Unknown method: %s", req.Method)}}
\t}}

\tif mcpErr != nil {{
\t\tw.WriteHeader(http.StatusBadRequest)
\t\tjson.NewEncoder(w).Encode(MCPResponse{{
\t\t\tOK:      false,
\t\t\tVersion: "v1",
\t\t\tError:   mcpErr,
\t\t}})
\t\treturn
\t}}

\tjson.NewEncoder(w).Encode(MCPResponse{{
\t\tOK:      true,
\t\tVersion: "v1",
\t\tData:    result,
\t}})
}}

// healthHandler handles health check requests
func healthHandler(w http.ResponseWriter, r *http.Request) {{{{
\tw.Header().Set("Content-Type", "application/json")
\tjson.NewEncoder(w).Encode(map[string]interface{{}}{{{{
\t\t"status": "healthy",
\t\t"agent":  agentState.AgentName,
\t\t"uptime": atomic.LoadInt64(&agentState.RequestsHandled),
\t}}}})
}}}}

// verbsHandler lists all exposed verbs
func verbsHandler(w http.ResponseWriter, r *http.Request) {{{{
\tw.Header().Set("Content-Type", "application/json")
\tjson.NewEncoder(w).Encode(map[string]interface{{}}{{{{
\t\t"agent": agentState.AgentName,
\t\t"verbs": {[f'"{e.verb}"' for e in agent.exposes]},
\t}}}})
}}}}'''


def _generate_main(agent: AgentDefinition) -> str:
    """Generate main function."""
    return f'''func main() {{{{
\tagentState.AgentName = "{agent.name}"

\thttp.HandleFunc("/mcp", mcpHandler)
\thttp.HandleFunc("/health", healthHandler)
\thttp.HandleFunc("/verbs", verbsHandler)

\tport := {agent.port}
\tfmt.Printf("Starting MCP server for agent: {agent.name}\\n")
\tfmt.Printf("Port: %d\\n", port)
\tfmt.Printf("Exposed verbs: {[e.verb for e in agent.exposes]}\\n")
\tfmt.Printf("Health check: http://127.0.0.1:%d/health\\n", port)
\tfmt.Printf("MCP endpoint: http://127.0.0.1:%d/mcp\\n", port)

\tlog.Fatal(http.ListenAndServe(fmt.Sprintf(":%d", port), nil))
}}}}'''


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