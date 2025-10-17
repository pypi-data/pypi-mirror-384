"""
MCP Server Generator for .NET/C#.

Generates C# ASP.NET Core servers from .al agent definitions.
C# uses compile-time tool imports (no dynamic loading like Python/Node.js).
"""

from __future__ import annotations

from language.agent_parser import AgentDefinition
from language.mcp_error_handling import get_csharp_error_middleware, get_validation_helpers
from language.mcp_health_checks import get_csharp_health_check, get_health_endpoints_pattern
from language.mcp_security import get_csharp_security_middleware


def generate_dotnet_mcp_server(agent: AgentDefinition) -> str:
    """
    Generate a complete C# ASP.NET Core MCP server from agent definition.

    Returns C# code that:
    - Runs on the specified port
    - Exposes MCP verbs as HTTP endpoints
    - Handles JSON-RPC requests
    - Returns MCP-formatted responses
    - Imports tools at compile time
    """

    code_parts = []

    # Usings and namespace
    code_parts.append(_generate_usings(agent))

    # Tool registry with compile-time imports
    code_parts.append(_generate_tool_registry(agent))

    # Verb handlers class
    code_parts.append(_generate_verb_handlers_class(agent))

    # Main MCP endpoint
    code_parts.append(_generate_mcp_endpoint(agent))

    # Program.cs main
    code_parts.append(_generate_program_main(agent))

    return "\n\n".join(code_parts)


def _generate_usings(agent: AgentDefinition) -> str:
    """Generate using statements and namespace."""
    # All using statements consolidated here - no imports elsewhere!
    usings = """using System.Text.Json;
using System.Text.Json.Nodes;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http;
using Microsoft.Extensions.Hosting;
using Microsoft.AspNetCore.RateLimiting;
using System.Threading.RateLimiting;
using Microsoft.Extensions.Logging;

namespace UserServiceMcp;"""

    # Note: Tool imports commented out for now
    # In production, these would import actual tool adapters:
    # - Tool adapters need to be created first
    # - Build system would copy adapters into ./tools/
    # - Then these imports would work
    #
    # if agent.tools:
    #     tool_usings = []
    #     for tool in agent.tools:
    #         tool_namespace = tool.replace("-", "_").title()
    #         tool_usings.append(f"using {tool_namespace}Adapter;")
    #     usings += "\n" + "\n".join(tool_usings)

    return usings


def _generate_tool_registry(agent: AgentDefinition) -> str:
    """Generate tool registry with inline stub implementations."""

    # Helper functions first
    helpers = []

    # Strip imports from helper functions
    def strip_imports(code: str) -> str:
        """Remove import/using statements from code."""
        lines = code.split('\n')
        result = []
        in_using_block = False

        for line in lines:
            stripped = line.strip()
            if stripped.startswith('using ') and ';' in stripped:
                continue
            elif stripped.startswith('using ') and not ';' in stripped:
                in_using_block = True
                continue
            elif in_using_block and ';' in line:
                in_using_block = False
                continue
            elif in_using_block:
                continue
            else:
                result.append(line)

        return '\n'.join(result).strip()

    helpers.append("// Error handling helpers")
    helpers.append(strip_imports(get_csharp_error_middleware()))
    helpers.append("")
    helpers.append("// Health check helpers")

    # Health check code needs special handling - wrap static var in class
    health_check_code = strip_imports(get_csharp_health_check())
    # Replace the static variable with a static class
    health_check_code = health_check_code.replace(
        "static HealthCheck healthChecker = new HealthCheck();",
        """public static class HealthCheckManager
{
    public static readonly HealthCheck Instance = new HealthCheck();
}"""
    )
    helpers.append(health_check_code)

    helpers_code = "\n".join(helpers)

    if not agent.tools:
        # No tools configured - provide stub function
        return f"""{helpers_code}

// No tools configured
public static class ToolRegistry
{{
    public static Dictionary<string, Dictionary<string, object>> ExecuteTools(Dictionary<string, object> parameters)
    {{
        return new Dictionary<string, Dictionary<string, object>>();
    }}
}}"""

    # Generate stub tool handlers (actual tool imports commented out above)
    tool_stubs = []
    for tool in agent.tools:
        tool_var = tool.replace("-", "_")
        tool_class = "".join(word.capitalize() for word in tool_var.split("_"))

        # Create stub handler that returns placeholder
        tool_stubs.append(f"""// Stub handler for {tool} tool
public static class {tool_class}Handler
{{
    public static Dictionary<string, object> Handle(Dictionary<string, object> parameters)
    {{
        return new Dictionary<string, object>
        {{
            ["ok"] = true,
            ["version"] = "v1",
            ["message"] = "Tool stub: {tool} (actual implementation requires tool adapter)",
            ["params"] = parameters
        }};
    }}
}}""")

    tool_map_entries = []
    for tool in agent.tools:
        tool_var = tool.replace("-", "_")
        tool_class = "".join(word.capitalize() for word in tool_var.split("_"))
        tool_map_entries.append(f'        {{ "{tool}", {tool_class}Handler.Handle }}')

    tools_list = ', '.join([f'"{t}"' for t in agent.tools])

    # Tool registry code (helpers are now in separate section)
    registry_code = f"""{helpers_code}

// Tool stubs (replace with actual imports in production)
{chr(10).join(tool_stubs)}

// Tool registry
public static class ToolRegistry
{{
    private static readonly Dictionary<string, Func<Dictionary<string, object>, Dictionary<string, object>>> Handlers = new()
    {{
{chr(10).join(tool_map_entries)}
    }};

    public static Dictionary<string, object> ExecuteTool(string toolName, Dictionary<string, object> parameters)
    {{
        if (!Handlers.TryGetValue(toolName, out var handler))
        {{
            return new Dictionary<string, object>
            {{
                ["ok"] = false,
                ["version"] = "v1",
                ["error"] = new Dictionary<string, object>
                {{
                    ["code"] = "E_TOOL_NOT_FOUND",
                    ["message"] = $"Tool not found: {{toolName}}"
                }}
            }};
        }}
        return handler(parameters);
    }}

    public static Dictionary<string, Dictionary<string, object>> ExecuteTools(Dictionary<string, object> parameters)
    {{
        var configuredTools = new[] {{ {tools_list} }};
        var results = new Dictionary<string, Dictionary<string, object>>();

        foreach (var toolName in configuredTools)
        {{
            results[toolName] = ExecuteTool(toolName, parameters);
        }}

        return results;
    }}
}}"""

    return registry_code


def _generate_verb_handlers_class(agent: AgentDefinition) -> str:
    """Generate VerbHandlers class containing all verb handler methods."""

    handlers = []
    for expose in agent.exposes:
        # Convert verb name to C# method name (PascalCase)
        handler_name = expose.verb.replace(".", "_").replace("@", "_").replace("-", "_")
        parts = handler_name.split("_")
        method_name = "".join(word.capitalize() for word in parts)

        # Build parameter validation
        param_checks = []
        for param in expose.params:
            param_checks.append(f"""        if (!parameters.ContainsKey("{param["name"]}"))
        {{
            return new Dictionary<string, object>
            {{
                ["error"] = new Dictionary<string, object>
                {{
                    ["code"] = "E_ARGS",
                    ["message"] = "Missing required parameter: {param["name"]}"
                }}
            }};
        }}""")

        param_validation = "\n".join(param_checks) if param_checks else "        // No required parameters"

        # Build return fields (mock data)
        return_fields = []
        for ret in expose.returns:
            if ret["type"] == "string":
                return_fields.append(f'        ["{ret["name"]}"] = "{ret["name"]}_value"')
            elif ret["type"] == "int":
                return_fields.append(f'        ["{ret["name"]}"] = 0')
            elif ret["type"] == "bool":
                return_fields.append(f'        ["{ret["name"]}"] = true')
            elif ret["type"] == "array":
                return_fields.append(f'        ["{ret["name"]}"] = new List<object>()')
            elif ret["type"] == "object":
                return_fields.append(f'        ["{ret["name"]}"] = new Dictionary<string, object>()')

        return_obj = ",\n".join(return_fields)

        handlers.append(f"""    // Handler for {expose.verb}
    public static Dictionary<string, object> Handle{method_name}(Dictionary<string, object> parameters)
    {{
{param_validation}

        // TODO: Implement actual handler logic
        return new Dictionary<string, object>
        {{
{return_obj}
        }};
    }}""")

    handlers_code = "\n\n".join(handlers)

    return f"""// Verb handlers
public static class VerbHandlers
{{
{handlers_code}
}}"""


def _generate_mcp_endpoint(agent: AgentDefinition) -> str:
    """Generate main MCP JSON-RPC endpoint handler."""

    # Build verb routing
    verb_routes = []
    for expose in agent.exposes:
        handler_name = expose.verb.replace(".", "_").replace("@", "_").replace("-", "_")
        parts = handler_name.split("_")
        method_name = "".join(word.capitalize() for word in parts)

        verb_routes.append(f"""            "{expose.verb}" => VerbHandlers.Handle{method_name}(verbParams)""")

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

    tools_init = "ToolRegistry.ExecuteTools(verbParams)" if agent.tools else "new Dictionary<string, Dictionary<string, object>>()"

    return f"""// MCP endpoint handler
public static class McpHandler
{{
    public static async Task HandleRequest(HttpContext context)
    {{
        if (context.Request.Method != "POST")
        {{
            context.Response.StatusCode = 405;
            await context.Response.WriteAsync("Method not allowed");
            return;
        }}

        var req = await JsonSerializer.DeserializeAsync<Dictionary<string, JsonElement>>(context.Request.Body);
        if (req == null)
        {{
            context.Response.StatusCode = 400;
            await context.Response.WriteAsync("Invalid JSON");
            return;
        }}

        var method = req.TryGetValue("method", out var m) ? m.GetString() : null;
        var id = req.TryGetValue("id", out var i) ? i.GetInt32() : 0;

        object response = method switch
        {{
            "initialize" => new
            {{
                jsonrpc = "2.0",
                id = id,
                result = new
                {{
                    protocolVersion = "0.1.0",
                    capabilities = new {{ tools = new {{}}, prompts = new {{}} }},
                    serverInfo = new {{ name = "{agent.name}", version = "v1" }}
                }}
            }},

            "tools/list" => new
            {{
                jsonrpc = "2.0",
                id = id,
                result = new
                {{
                    tools = JsonSerializer.Deserialize<object[]>(@"{tool_schemas_json.replace('"', '""')}")
                }}
            }},

            "tools/call" => HandleToolsCall(req, id),

            _ => new
            {{
                jsonrpc = "2.0",
                id = id,
                error = new {{ code = -32601, message = $"Method not found: {{method}}" }}
            }}
        }};

        await context.Response.WriteAsJsonAsync(response);
    }}

    private static object HandleToolsCall(Dictionary<string, JsonElement> req, int id)
    {{
        var paramsElem = req.TryGetValue("params", out var p) ? p : default;
        var verbName = paramsElem.TryGetProperty("name", out var n) ? n.GetString() : null;
        var verbParamsElem = paramsElem.TryGetProperty("arguments", out var a) ? a : default;

        if (string.IsNullOrEmpty(verbName))
        {{
            return new
            {{
                jsonrpc = "2.0",
                id = id,
                error = new {{ code = -32602, message = "Invalid params: missing tool name" }}
            }};
        }}

        var verbParams = JsonSerializer.Deserialize<Dictionary<string, object>>(verbParamsElem.GetRawText())
            ?? new Dictionary<string, object>();

        // Execute tools first (if configured)
        var toolResults = {tools_init};
        var toolsExecuted = toolResults.Keys.ToList();

        // Route to appropriate verb handler
        var verbResult = verbName switch
        {{
{verb_routing},
            _ => new Dictionary<string, object>
            {{
                ["error"] = new Dictionary<string, object>
                {{
                    ["code"] = "E_VERB_NOT_FOUND",
                    ["message"] = $"Verb not found: {{verbName}}"
                }}
            }}
        }};

        // Check for errors
        if (verbResult.ContainsKey("error"))
        {{
            return new
            {{
                jsonrpc = "2.0",
                id = id,
                error = new {{ code = -32000, message = verbResult["error"] }}
            }};
        }}

        // Build MCP-compliant response
        var responseData = new Dictionary<string, object>
        {{
            ["input_params"] = verbParams,
            ["tool_results"] = toolResults,
            ["metadata"] = new Dictionary<string, object>
            {{
                ["mode"] = "ide_integrated",
                ["agent_name"] = "{agent.name}",
                ["timestamp"] = DateTime.UtcNow.ToString("o"),
                ["tools_executed"] = toolsExecuted
            }}
        }};

        // Merge verb result
        foreach (var kvp in verbResult)
        {{
            responseData[kvp.Key] = kvp.Value;
        }}

        return new
        {{
            jsonrpc = "2.0",
            id = id,
            result = responseData
        }};
    }}
}}"""


def _generate_program_main(agent: AgentDefinition) -> str:
    """Generate Program.cs main method."""

    verbs_list = ', '.join([e.verb for e in agent.exposes])

    health_endpoints = get_health_endpoints_pattern("csharp", agent.name)

    # Replace healthChecker with HealthCheckManager.Instance
    health_endpoints["health"] = health_endpoints["health"].replace("healthChecker", "HealthCheckManager.Instance")
    health_endpoints["ready"] = health_endpoints["ready"].replace("healthChecker", "HealthCheckManager.Instance")

    # Strip imports from security middleware
    def strip_imports(code: str) -> str:
        """Remove import/using statements from code."""
        lines = code.split('\n')
        result = []
        in_using_block = False

        for line in lines:
            stripped = line.strip()
            if stripped.startswith('using ') and ';' in stripped:
                continue
            elif stripped.startswith('using ') and not ';' in stripped:
                in_using_block = True
                continue
            elif in_using_block and ';' in line:
                in_using_block = False
                continue
            elif in_using_block:
                continue
            else:
                result.append(line)

        return '\n'.join(result).strip()

    security_middleware = strip_imports(get_csharp_security_middleware())

    # Indent security middleware properly (it defines builder and app)
    # We need to extract just the initialization parts
    verbs_array = ', '.join([f'"{e.verb}"' for e in agent.exposes])

    return f"""// Program.cs main entry point
public class Program
{{
    public static void Main(string[] args)
    {{
        var builder = WebApplication.CreateBuilder(args);

        // Rate limiting
        builder.Services.AddRateLimiter(options =>
        {{
            options.GlobalLimiter = PartitionedRateLimiter.Create<HttpContext, string>(context =>
                RateLimitPartition.GetFixedWindowLimiter(
                    partitionKey: context.Connection.RemoteIpAddress?.ToString() ?? "unknown",
                    factory: _ => new FixedWindowRateLimiterOptions
                    {{
                        PermitLimit = 100,
                        Window = TimeSpan.FromMinutes(1),
                        QueueProcessingOrder = QueueProcessingOrder.OldestFirst,
                        QueueLimit = 0
                    }}));

            options.OnRejected = async (context, cancellationToken) =>
            {{
                context.HttpContext.Response.StatusCode = 429;
                await context.HttpContext.Response.WriteAsJsonAsync(new
                {{
                    jsonrpc = "2.0",
                    error = new
                    {{
                        code = -32006,
                        message = "Too many requests"
                    }}
                }}, cancellationToken);
            }};
        }});

        // CORS
        var allowedOrigins = Environment.GetEnvironmentVariable("ALLOWED_ORIGINS")?.Split(',')
            ?? new[] {{ "*" }};

        builder.Services.AddCors(options =>
        {{
            options.AddDefaultPolicy(policy =>
            {{
                policy.WithOrigins(allowedOrigins)
                      .AllowAnyMethod()
                      .AllowAnyHeader()
                      .SetPreflightMaxAge(TimeSpan.FromHours(1));
            }});
        }});

        var app = builder.Build();

        // Use CORS
        app.UseCors();

        // Use rate limiting
        app.UseRateLimiter();

        // Security headers middleware
        app.Use(async (context, next) =>
        {{
            context.Response.Headers["X-Content-Type-Options"] = "nosniff";
            context.Response.Headers["X-Frame-Options"] = "DENY";
            context.Response.Headers["X-XSS-Protection"] = "1; mode=block";
            context.Response.Headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains";
            await next();
        }});

        // MCP endpoint
        app.MapPost("/mcp", McpHandler.HandleRequest);

        // Health endpoints
        {health_endpoints["health"]}

        {health_endpoints["ready"]}

        // Verbs endpoint
        app.MapGet("/verbs", () => new
        {{
            agent = "{agent.name}",
            verbs = new[] {{ {verbs_array} }}
        }});

        var port = "{agent.port}";
        Console.WriteLine($"MCP server for agent: {agent.name}");
        Console.WriteLine($"Port: {{port}}");
        Console.WriteLine($"Exposed verbs: [{verbs_list}]");
        Console.WriteLine($"Health check: http://127.0.0.1:{{port}}/health");
        Console.WriteLine($"Readiness check: http://127.0.0.1:{{port}}/ready");
        Console.WriteLine($"MCP endpoint: http://127.0.0.1:{{port}}/mcp");

        app.Run($"http://127.0.0.1:{{port}}");
    }}
}}"""


def generate_dotnet_server_from_pw(pw_code: str) -> str:
    """
    Convenience function: parse .al code and generate C# MCP server.

    Args:
        pw_code: .al file content

    Returns:
        C# code for MCP server
    """
    from language.agent_parser import parse_agent_pw

    agent = parse_agent_pw(pw_code)
    return generate_dotnet_mcp_server(agent)
