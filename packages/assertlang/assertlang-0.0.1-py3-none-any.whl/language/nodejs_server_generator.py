"""
DEPRECATED: Use language.mcp_server_generator_nodejs instead.

This module is deprecated and will be removed in a future version.
Use the new unified generator system in language.mcp_server_generator_nodejs.

Node.js MCP Server Generator for Promptware agents.

Generates Express-based MCP servers from .al agent definitions.
"""

from __future__ import annotations

from language.agent_parser import AgentDefinition, ExposeBlock


def generate_nodejs_mcp_server(agent: AgentDefinition) -> str:
    """
    Generate a complete Node.js MCP server from agent definition.

    Returns Express application code that:
    - Runs on the specified port
    - Exposes MCP verbs as HTTP endpoints
    - Handles JSON-RPC requests
    - Returns MCP-formatted responses
    """

    code_parts = []

    # Imports and setup
    code_parts.append(_generate_imports(agent))

    # Handler functions for each exposed verb
    for expose in agent.exposes:
        code_parts.append(_generate_verb_handler(expose, agent))

    # Main MCP endpoint
    code_parts.append(_generate_mcp_endpoint(agent))

    # Server startup
    code_parts.append(_generate_server_startup(agent))

    return "\n\n".join(code_parts)


def _generate_imports(agent: AgentDefinition) -> str:
    """Generate import statements and server setup."""
    imports = """const express = require('express');
const app = express();

// Agent state (in-memory for demo)
const agentState = {
  agentName: '${agent_name}',
  startedAt: new Date().toISOString(),
  requestsHandled: 0
};

// Middleware
app.use(express.json());"""

    return imports.replace('${agent_name}', agent.name)


def _generate_verb_handler(expose: ExposeBlock, agent: AgentDefinition) -> str:
    """Generate handler function for an exposed MCP verb."""
    handler_name = expose.verb.replace(".", "_").replace("@", "_")

    # Build parameter validation
    param_checks = []
    for param in expose.params:
        param_checks.append(
            f'  if (!params.{param["name"]}) {{\n'
            f'    return {{ error: {{ code: "E_ARGS", message: "Missing required parameter: {param["name"]}" }} }};\n'
            f'  }}'
        )

    param_validation = "\n".join(param_checks) if param_checks else "  // No required parameters"

    # Generate return structure
    return_fields = {}
    for ret in expose.returns:
        if ret["type"] == "string":
            return_fields[ret["name"]] = f'"{ret["name"]}_value"'
        elif ret["type"] == "int":
            return_fields[ret["name"]] = "0"
        elif ret["type"] == "bool":
            return_fields[ret["name"]] = "true"
        elif ret["type"] == "object":
            return_fields[ret["name"]] = "{}"
        elif ret["type"] == "array":
            return_fields[ret["name"]] = "[]"
        else:
            return_fields[ret["name"]] = "null"

    return_obj = ", ".join([f'{k}: {v}' for k, v in return_fields.items()])

    return f'''/**
 * Handler for {expose.verb}
 *
 * Parameters: {", ".join([p["name"] for p in expose.params])}
 * Returns: {", ".join([r["name"] for r in expose.returns])}
 */
function handle_{handler_name}(params) {{
{param_validation}

  agentState.requestsHandled++;

  // TODO: Implement actual handler logic
  return {{ {return_obj} }};
}}'''


def _generate_mcp_endpoint(agent: AgentDefinition) -> str:
    """Generate main MCP JSON-RPC endpoint."""

    # Build verb routing
    verb_routes = []
    for expose in agent.exposes:
        handler_name = expose.verb.replace(".", "_").replace("@", "_")
        verb_routes.append(
            f'    case "{expose.verb}":\n'
            f'      result = handle_{handler_name}(params);\n'
            f'      break;'
        )

    verb_routing = "\n".join(verb_routes)

    return f'''// Main MCP endpoint - handles JSON-RPC requests
app.post('/mcp', (req, res) => {{
  try {{
    const {{ method, params = {{}} }} = req.body;

    if (!method) {{
      return res.status(400).json({{
        ok: false,
        version: 'v1',
        error: {{
          code: 'E_ARGS',
          message: "Missing 'method' in request"
        }}
      }});
    }}

    let result;
    switch (method) {{
{verb_routing}
      default:
        return res.status(404).json({{
          ok: false,
          version: 'v1',
          error: {{
            code: 'E_METHOD',
            message: `Unknown method: ${{method}}`
          }}
        }});
    }}

    // Check for errors in result
    if (result.error) {{
      return res.status(400).json({{
        ok: false,
        version: 'v1',
        error: result.error
      }});
    }}

    // Success response
    res.json({{
      ok: true,
      version: 'v1',
      data: result
    }});
  }} catch (error) {{
    res.status(500).json({{
      ok: false,
      version: 'v1',
      error: {{
        code: 'E_RUNTIME',
        message: error.message
      }}
    }});
  }}
}});

// Health check endpoint
app.get('/health', (req, res) => {{
  res.json({{
    status: 'healthy',
    agent: '{agent.name}',
    uptime: agentState.requestsHandled
  }});
}});

// List all exposed verbs
app.get('/verbs', (req, res) => {{
  res.json({{
    agent: '{agent.name}',
    verbs: {[f'"{e.verb}"' for e in agent.exposes]}
  }});
}});'''


def _generate_server_startup(agent: AgentDefinition) -> str:
    """Generate server startup code."""
    return f'''// Start server
const PORT = {agent.port};
app.listen(PORT, () => {{
  console.log(`Starting MCP server for agent: {agent.name}`);
  console.log(`Port: ${{PORT}}`);
  console.log(`Exposed verbs: {[e.verb for e in agent.exposes]}`);
  console.log(`Health check: http://127.0.0.1:${{PORT}}/health`);
  console.log(`MCP endpoint: http://127.0.0.1:${{PORT}}/mcp`);
}});'''


def generate_nodejs_server_from_pw(pw_code: str) -> str:
    """
    Convenience function: parse .al code and generate Node.js MCP server.

    Args:
        pw_code: .al file content

    Returns:
        Node.js code for MCP server
    """
    from language.agent_parser import parse_agent_pw

    agent = parse_agent_pw(pw_code)
    return generate_nodejs_mcp_server(agent)