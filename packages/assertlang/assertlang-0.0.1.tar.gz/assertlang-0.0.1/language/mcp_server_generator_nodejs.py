"""
MCP Server Generator for Node.js/Express.

Generates Express-based MCP servers from .al agent definitions.
"""

from __future__ import annotations

from language.agent_parser import AgentDefinition, ExposeBlock
from language.mcp_error_handling import get_nodejs_error_middleware, get_validation_helpers
from language.mcp_health_checks import get_health_endpoints_pattern, get_nodejs_health_check
from language.mcp_security import get_nodejs_security_middleware


def generate_nodejs_mcp_server(agent: AgentDefinition) -> str:
    """
    Generate a complete Node.js/Express MCP server from agent definition.

    Returns JavaScript code that:
    - Runs on the specified port
    - Exposes MCP verbs as HTTP endpoints
    - Handles JSON-RPC requests
    - Returns MCP-formatted responses
    """

    code_parts = []

    # Imports and setup
    code_parts.append(_generate_imports(agent))

    # Tool executor setup
    code_parts.append(_generate_tool_setup(agent))

    # Handler functions for each exposed verb
    for expose in agent.exposes:
        code_parts.append(_generate_verb_handler(expose, agent))

    # Main MCP endpoint
    code_parts.append(_generate_mcp_endpoint(agent))

    # Health and verbs endpoints
    code_parts.append(_generate_utility_endpoints(agent))

    # Server startup
    code_parts.append(_generate_server_startup(agent))

    return "\n\n".join(code_parts)


def _generate_imports(agent: AgentDefinition) -> str:
    """Generate import statements."""
    imports = f"""import express from 'express';
import {{ fileURLToPath }} from 'url';
import {{ dirname, join }} from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const app = express();
app.use(express.json());

{get_nodejs_error_middleware()}

{get_nodejs_health_check()}

{get_validation_helpers("nodejs")}

{get_nodejs_security_middleware()}"""

    # Add tool registry imports if agent uses tools
    if agent.tools:
        imports += """

// Tool registry imports
import { getRegistry } from './promptware-js/registry.js';
const toolRegistry = getRegistry();"""

    return imports


def _generate_tool_setup(agent: AgentDefinition) -> str:
    """Generate tool executor setup."""
    if not agent.tools:
        return """// No tools configured
const toolExecutor = null;"""

    tools_array = ', '.join([f"'{tool}'" for tool in agent.tools])

    return f"""// Tool executor setup
const configuredTools = [{tools_array}];

const toolExecutor = {{
  hasTools: () => configuredTools.length > 0,
  executeTools: async (params) => {{
    const results = {{}};

    for (const toolName of configuredTools) {{
      try {{
        // Map parameters to tool
        const toolParams = {{ ...params }};
        const result = await toolRegistry.executeTool(toolName, toolParams);
        results[toolName] = result;
      }} catch (error) {{
        results[toolName] = {{
          ok: false,
          error: {{ code: 'E_TOOL_EXEC', message: error.message }}
        }};
      }}
    }}

    return results;
  }}
}};"""


def _generate_verb_handler(expose: ExposeBlock, agent: AgentDefinition) -> str:
    """Generate handler function for an exposed MCP verb."""

    # Parse verb name (e.g., "task.execute@v1" -> "taskExecuteV1")
    handler_name = expose.verb.replace(".", "_").replace("@", "_").replace("-", "_")
    camel_name = ''.join(word.capitalize() for word in handler_name.split('_'))

    # Build parameter validation
    param_checks = []
    for param in expose.params:
        param_checks.append(f"""  if (!params.{param["name"]}) {{
    return {{
      error: {{ code: 'E_ARGS', message: 'Missing required parameter: {param["name"]}' }}
    }};
  }}""")

    param_validation = "\n".join(param_checks) if param_checks else "  // No required parameters"

    # Build return fields (mock data)
    return_fields = {}
    for ret in expose.returns:
        if ret["type"] == "string":
            return_fields[ret["name"]] = f'"{ret["name"]}_value"'
        elif ret["type"] == "int":
            return_fields[ret["name"]] = "0"
        elif ret["type"] == "bool":
            return_fields[ret["name"]] = "true"
        elif ret["type"] == "array":
            return_fields[ret["name"]] = "[]"
        elif ret["type"] == "object":
            return_fields[ret["name"]] = "{}"
        else:
            return_fields[ret["name"]] = "null"

    return_obj = ",\n    ".join([f"{k}: {v}" for k, v in return_fields.items()])

    return f"""/**
 * Handler for {expose.verb}
 *
 * @param {{Object}} params - Verb parameters
 * @returns {{Object}} Result object
 */
async function handle{camel_name}(params) {{
{param_validation}

  // TODO: Implement actual handler logic
  // For now, return mock data
  return {{
    {return_obj}
  }};
}}"""


def _generate_mcp_endpoint(agent: AgentDefinition) -> str:
    """Generate main MCP JSON-RPC endpoint."""

    # Build tool schemas for tools/list
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

    # Build verb routing
    verb_routes = []
    for i, expose in enumerate(agent.exposes):
        handler_name = expose.verb.replace(".", "_").replace("@", "_").replace("-", "_")
        camel_name = ''.join(word.capitalize() for word in handler_name.split('_'))

        condition = "if" if i == 0 else "else if"
        verb_routes.append(f"""      {condition} (verbName === '{expose.verb}') {{
        verbResult = await handle{camel_name}(verbParams);
      }}""")

    verb_routing = "\n".join(verb_routes)

    return f"""// Main MCP endpoint
app.post('/mcp', async (req, res) => {{
  try {{
    const {{ jsonrpc, id, method, params }} = req.body;

    if (!method) {{
      return res.status(400).json({{
        jsonrpc: '2.0',
        id: id || 1,
        error: {{ code: -32600, message: 'Invalid Request: missing method' }}
      }});
    }}

    // Handle MCP protocol methods
    if (method === 'initialize') {{
      return res.json({{
        jsonrpc: '2.0',
        id,
        result: {{
          protocolVersion: '0.1.0',
          capabilities: {{ tools: {{}}, prompts: {{}} }},
          serverInfo: {{ name: '{agent.name}', version: 'v1' }}
        }}
      }});
    }}

    if (method === 'tools/list') {{
      return res.json({{
        jsonrpc: '2.0',
        id,
        result: {{ tools: {tool_schemas_json} }}
      }});
    }}

    if (method === 'tools/call') {{
      const verbName = params?.name;
      const verbParams = params?.arguments || {{}};

      if (!verbName) {{
        return res.status(400).json({{
          jsonrpc: '2.0',
          id,
          error: {{ code: -32602, message: 'Invalid params: missing tool name' }}
        }});
      }}

      // Execute tools first (if configured)
      let toolResults = {{}};
      let toolsExecuted = [];

      if (toolExecutor && toolExecutor.hasTools()) {{
        toolResults = await toolExecutor.executeTools(verbParams);
        toolsExecuted = Object.keys(toolResults);
      }}

      // Route to appropriate verb handler
      let verbResult = null;

{verb_routing}
      else {{
        return res.status(404).json({{
          jsonrpc: '2.0',
          id,
          error: {{ code: -32601, message: `Method not found: ${{verbName}}` }}
        }});
      }}

      // Check for errors
      if (verbResult && verbResult.error) {{
        return res.status(400).json({{
          jsonrpc: '2.0',
          id,
          error: {{ code: -32000, message: verbResult.error.message }}
        }});
      }}

      // Determine mode
      const hasApiKey = !!process.env.ANTHROPIC_API_KEY;
      const mode = (hasApiKey && {bool(agent.llm)}) ? 'standalone_ai' : 'ide_integrated';

      // Build MCP-compliant response
      const responseData = {{
        input_params: verbParams,
        tool_results: toolResults,
        metadata: {{
          mode,
          agent_name: '{agent.name}',
          timestamp: new Date().toISOString(),
          tools_executed: toolsExecuted
        }},
        ...verbResult
      }};

      return res.json({{
        jsonrpc: '2.0',
        id,
        result: responseData
      }});
    }}

    // Unknown method
    return res.status(404).json({{
      jsonrpc: '2.0',
      id,
      error: {{ code: -32601, message: `Method not found: ${{method}}` }}
    }});

  }} catch (error) {{
    console.error('MCP endpoint error:', error);
    return res.status(500).json({{
      jsonrpc: '2.0',
      id: req.body?.id || 1,
      error: {{ code: -32603, message: `Internal error: ${{error.message}}` }}
    }});
  }}
}});"""


def _generate_utility_endpoints(agent: AgentDefinition) -> str:
    """Generate health and verbs endpoints."""

    verbs_list = ', '.join([f"'{e.verb}'" for e in agent.exposes])

    health_endpoints = get_health_endpoints_pattern("nodejs", agent.name)

    return f"""{health_endpoints["health"]}

{health_endpoints["ready"]}

// List all exposed verbs
app.get('/verbs', (req, res) => {{
  res.json({{
    agent: '{agent.name}',
    verbs: [{verbs_list}]
  }});
}});"""


def _generate_server_startup(agent: AgentDefinition) -> str:
    """Generate server startup code."""

    return f"""// Start server
const PORT = {agent.port};

app.listen(PORT, () => {{
  console.log(`MCP server for agent: {agent.name}`);
  console.log(`Port: ${{PORT}}`);
  console.log(`Exposed verbs: [{', '.join([e.verb for e in agent.exposes])}]`);
  console.log(`Health check: http://127.0.0.1:${{PORT}}/health`);
  console.log(`MCP endpoint: http://127.0.0.1:${{PORT}}/mcp`);
}});"""


def generate_nodejs_server_from_pw(pw_code: str) -> str:
    """
    Convenience function: parse .al code and generate Node.js MCP server.

    Args:
        pw_code: .al file content

    Returns:
        JavaScript code for MCP server
    """
    from language.agent_parser import parse_agent_pw

    agent = parse_agent_pw(pw_code)
    return generate_nodejs_mcp_server(agent)
