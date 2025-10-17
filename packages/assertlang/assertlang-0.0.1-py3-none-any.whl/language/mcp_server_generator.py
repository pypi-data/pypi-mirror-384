"""
MCP Server Generator for Promptware agents.

Generates FastAPI-based MCP servers from .al agent definitions.
"""

from __future__ import annotations

from typing import Dict, List

from language.agent_parser import (
    AgentDefinition,
    ExposeBlock,
    WorkflowDefinition,
    WorkflowStep,
)
from language.mcp_error_handling import get_python_error_middleware, get_validation_helpers
from language.mcp_health_checks import get_health_endpoints_pattern, get_python_health_check
from language.mcp_security import get_python_security_middleware


def _strip_imports(code: str) -> str:
    """Remove import statements from code block."""
    lines = code.split('\n')
    result = []
    skip_next = False

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Skip import lines
        if stripped.startswith('from ') and ' import ' in stripped:
            continue
        elif stripped.startswith('import '):
            continue
        # Skip the line after import if it's empty
        elif skip_next and not stripped:
            skip_next = False
            continue
        else:
            result.append(line)
            skip_next = False

    return '\n'.join(result).strip()


def _get_python_security_middleware_no_imports() -> str:
    """Get Python security middleware with imports stripped."""
    original = get_python_security_middleware()
    stripped = _strip_imports(original)

    # Replace slowapi references with conditional try/except
    # Since slowapi might not be installed in test environment
    if 'slowapi' in stripped or 'limiter' in stripped.lower():
        return '''
# Security middleware (with optional rate limiting)
# Note: Advanced rate limiting requires slowapi package

# Basic CORS middleware (always available)
try:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=os.environ.get("ALLOWED_ORIGINS", "*").split(","),
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
        max_age=3600,
    )
except Exception:
    pass  # CORS optional in testing

# Trusted host middleware (optional)
try:
    if os.environ.get("ALLOWED_HOSTS"):
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=os.environ.get("ALLOWED_HOSTS").split(",")
        )
except Exception:
    pass

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response
'''

    return stripped


def generate_python_mcp_server(agent: AgentDefinition) -> str:
    """
    Generate a complete Python MCP server from agent definition.

    Returns FastAPI application code that:
    - Runs on the specified port
    - Exposes MCP verbs as HTTP endpoints
    - Handles JSON-RPC requests
    - Returns MCP-formatted responses
    """

    code_parts = []

    # Imports
    code_parts.append(_generate_imports(agent))

    # Temporal workflows and activities (if enabled)
    if agent.temporal and agent.workflows:
        code_parts.append(_generate_temporal_workflows(agent))

    # FastAPI app initialization
    code_parts.append(_generate_app_init(agent))

    # Handler functions for each exposed verb
    for expose in agent.exposes:
        code_parts.append(_generate_verb_handler(expose, agent))

    # Main MCP endpoint
    code_parts.append(_generate_mcp_endpoint(agent))

    # Server startup
    code_parts.append(_generate_server_startup(agent))

    return "\n\n".join(code_parts)


def _generate_imports(agent: AgentDefinition) -> str:
    """Generate import statements."""
    base_imports = """from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn
from typing import Any, Dict, Optional
from datetime import datetime
import time
import sys
import os
from pathlib import Path

# Note: Tool imports commented out until tool adapters exist
# In production, these would import actual tool registry:
# - Tool adapters need to be created first
# - Then tools.registry and language.tool_executor would be available
#
# from tools.registry import get_registry
# from language.tool_executor import ToolExecutor

# Security middleware imports (optional - comment out if not installed)
try:
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.middleware.trustedhost import TrustedHostMiddleware
    # Note: slowapi is optional - only for advanced rate limiting
    # from slowapi import Limiter, _rate_limit_exceeded_handler
    # from slowapi.util import get_remote_address
    # from slowapi.errors import RateLimitExceeded
except ImportError:
    pass  # Security features optional in testing"""

    # Add LangChain imports if agent uses LLM
    if agent.llm:
        langchain_imports = """
import os
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser"""
        base_imports += langchain_imports

    # Add OpenTelemetry imports if observability enabled
    if agent.observability and (agent.observability.traces or agent.observability.metrics):
        otel_imports = """
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader, ConsoleMetricExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource"""
        base_imports += otel_imports

    # Add Temporal imports if workflows enabled
    if agent.temporal and agent.workflows:
        temporal_imports = """
import asyncio
from datetime import timedelta
from temporalio import workflow, activity
from temporalio.client import Client
from temporalio.worker import Worker"""
        base_imports += temporal_imports

    return base_imports


def _generate_app_init(agent: AgentDefinition) -> str:
    """Generate FastAPI app initialization."""

    # OpenTelemetry setup if observability enabled
    otel_setup = ""
    if agent.observability and (agent.observability.traces or agent.observability.metrics):
        otel_setup = f'''
# OpenTelemetry setup
resource = Resource.create({{"service.name": "{agent.name}"}})
'''

        if agent.observability.traces:
            otel_setup += '''
# Trace provider
trace_provider = TracerProvider(resource=resource)
trace_processor = BatchSpanProcessor(ConsoleSpanExporter())
trace_provider.add_span_processor(trace_processor)
trace.set_tracer_provider(trace_provider)
tracer = trace.get_tracer(__name__)
'''

        if agent.observability.metrics:
            otel_setup += '''
# Metrics provider
metric_reader = PeriodicExportingMetricReader(ConsoleMetricExporter())
meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
metrics.set_meter_provider(meter_provider)
meter = metrics.get_meter(__name__)

# Metrics instruments
request_counter = meter.create_counter(
    "mcp_requests_total",
    description="Total number of MCP requests"
)
request_duration = meter.create_histogram(
    "mcp_request_duration_seconds",
    description="MCP request duration in seconds"
)
error_counter = meter.create_counter(
    "mcp_errors_total",
    description="Total number of MCP errors"
)
'''

    init_code = otel_setup + f'''
# MCP Server for agent: {agent.name}
app = FastAPI(
    title="{agent.name}",
    description="Promptware MCP Agent",
    version="v1"
)

{get_python_error_middleware()}

{get_python_health_check()}

{get_validation_helpers("python")}

{_get_python_security_middleware_no_imports()}'''

    # Auto-instrument FastAPI if observability enabled
    if agent.observability and agent.observability.traces:
        init_code += '''

# Auto-instrument FastAPI
FastAPIInstrumentor.instrument_app(app)'''

    init_code += f'''

# Agent state (in-memory for demo)
agent_state: Dict[str, Any] = {{
    "agent_name": "{agent.name}",
    "started_at": datetime.now().isoformat(),
    "requests_handled": 0
}}

# Tool registry (stub implementation until tool adapters exist)
configured_tools = {agent.tools}

def execute_tool(tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a single tool (stub implementation)."""
    if tool_name not in configured_tools:
        return {{
            "ok": False,
            "version": "v1",
            "error": {{
                "code": "E_TOOL_NOT_FOUND",
                "message": f"Tool not found: {{tool_name}}"
            }}
        }}

    # Stub response - actual implementation requires tool adapters
    return {{
        "ok": True,
        "version": "v1",
        "message": f"Tool stub: {{tool_name}} (actual implementation requires tool adapter)",
        "params": params
    }}

def execute_tools(params: Dict[str, Any]) -> Dict[str, Any]:
    """Execute all configured tools."""
    results = {{}}
    for tool_name in configured_tools:
        results[tool_name] = execute_tool(tool_name, params)
    return results

def has_tools() -> bool:
    """Check if agent has tools configured."""
    return len(configured_tools) > 0'''

    # Add Temporal client initialization if workflows enabled
    if agent.temporal and agent.workflows:
        init_code += '''

# Temporal client (global)
temporal_client: Optional[Client] = None

async def get_temporal_client() -> Client:
    """Get or create Temporal client."""
    global temporal_client
    if temporal_client is None:
        temporal_client = await Client.connect("localhost:7233")
    return temporal_client'''

    # Add LLM initialization if agent uses LLM
    if agent.llm:
        # Parse LLM spec (e.g., "anthropic claude-3-5-sonnet-20241022")
        llm_parts = agent.llm.split()
        llm_parts[0] if llm_parts else "anthropic"
        model_name = " ".join(llm_parts[1:]) if len(llm_parts) > 1 else "claude-3-5-sonnet-20241022"

        llm_init = f'''

# LLM initialization ({agent.llm})
llm = ChatAnthropic(
    model="{model_name}",
    api_key=os.environ.get("ANTHROPIC_API_KEY"),
    temperature=0,
)'''

        # Add global prompt if specified
        if agent.prompt_template:
            llm_init += f'''

# Global agent prompt
AGENT_SYSTEM_PROMPT = """{agent.prompt_template}"""'''

        init_code += llm_init

    return init_code


def _generate_verb_handler(expose: ExposeBlock, agent: AgentDefinition) -> str:
    """Generate handler function for an exposed MCP verb."""

    # Parse verb name (e.g., "task.execute@v1" -> "task_execute_v1")
    handler_name = expose.verb.replace(".", "_").replace("@", "_")

    # Build parameter validation
    param_names = [p["name"] for p in expose.params]
    param_checks = []
    for param in expose.params:
        param_checks.append(f'''    if "{param["name"]}" not in params:
        return {{"error": {{"code": "E_ARGS", "message": "Missing required parameter: {param["name"]}"}}}}''')

    param_validation = "\n".join(param_checks) if param_checks else "    # No required parameters"

    # Add tracing and metrics if observability enabled
    observability_setup = ""
    observability_record = ""
    has_tracing = agent.observability and agent.observability.traces

    if agent.observability:
        if agent.observability.metrics:
            observability_setup = '''    start_time = time.time()
'''
            observability_record = f'''
    # Record metrics
    duration = time.time() - start_time
    request_counter.add(1, {{"verb": "{expose.verb}", "agent": "{agent.name}"}})
    request_duration.record(duration, {{"verb": "{expose.verb}"}})'''

    # Generate handler body based on type
    if agent.temporal and expose.verb == "workflow.execute@v1":
        # Special handler for workflow execution
        handler_body = _generate_workflow_execution_handler(agent)
    elif agent.llm and expose.prompt_template:
        # AI-powered handler using LangChain
        handler_body = _generate_ai_handler_body(expose, agent, param_names)
    elif agent.llm:
        # LLM available but no specific prompt - generic implementation
        handler_body = _generate_generic_ai_handler_body(expose, agent, param_names)
    else:
        # Non-AI handler - mock implementation
        handler_body = _generate_mock_handler_body(expose)

    # Wrap handler body with tracing span if enabled
    if has_tracing:
        # Indent handler body for span context
        lines = handler_body.split("\n")
        indented_lines = []
        for line in lines:
            if line.strip():
                indented_lines.append("    " + line)
            else:
                indented_lines.append(line)
        indented_body = "\n".join(indented_lines)

        handler_body = f'''    with tracer.start_as_current_span("{expose.verb}") as span:
        span.set_attribute("verb", "{expose.verb}")
        span.set_attribute("agent", "{agent.name}")
{indented_body}'''

    return f'''def handle_{handler_name}(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handler for {expose.verb}

    Parameters:
{_format_params_doc(expose.params)}

    Returns:
{_format_returns_doc(expose.returns)}
    """
{param_validation}

    agent_state["requests_handled"] += 1
{observability_setup}{handler_body}{observability_record}'''


def _generate_workflow_execution_handler(agent: AgentDefinition) -> str:
    """Generate handler for workflow.execute@v1 verb."""
    if not agent.workflows:
        return _generate_mock_handler_body(ExposeBlock(verb="workflow.execute@v1"))

    workflow_def = agent.workflows[0]
    workflow_class_name = workflow_def.name.replace("@", "_").replace(".", "_").title() + "Workflow"

    return f'''    # Execute Temporal workflow
    try:
        workflow_id = params.get("workflow_id")
        workflow_params = params.get("params", {{}})

        # Get Temporal client
        client = asyncio.run(get_temporal_client())

        # Start workflow execution
        handle = asyncio.run(
            client.start_workflow(
                {workflow_class_name}.run,
                **workflow_params,
                id=workflow_id,
                task_queue="{agent.name}-task-queue",
            )
        )

        return {{
            "execution_id": handle.id,
            "status": "running"
        }}
    except Exception as e:
        return {{
            "error": {{
                "code": "E_RUNTIME",
                "message": f"Workflow execution failed: {{str(e)}}"
            }}
        }}'''


def _generate_mock_handler_body(expose: ExposeBlock) -> str:
    """Generate mock implementation for non-AI handlers."""
    return_fields = {}
    for ret in expose.returns:
        if ret["type"] == "string":
            return_fields[ret["name"]] = f'"{ret["name"]}_value"'
        elif ret["type"] == "int":
            return_fields[ret["name"]] = "0"
        elif ret["type"] == "bool":
            return_fields[ret["name"]] = "True"
        elif ret["type"] == "object":
            return_fields[ret["name"]] = "{}"
        elif ret["type"] == "array":
            return_fields[ret["name"]] = "[]"
        else:
            return_fields[ret["name"]] = "None"

    return_dict = ",\n        ".join([f'"{k}": {v}' for k, v in return_fields.items()])

    return f'''    # TODO: Implement actual handler logic
    # For now, return mock data
    return {{
        {return_dict}
    }}'''


def _generate_ai_handler_body(expose: ExposeBlock, agent: AgentDefinition, param_names: List[str]) -> str:
    """Generate AI-powered handler using LangChain with specific prompt."""
    # Build prompt with parameters
    ", ".join([f"{{params['{p}']}}" for p in param_names])

    # Format parameters for prompt
    param_placeholders = "\n    ".join([f'{p}: {{params["{p}"]}}' for p in param_names])

    return f'''    # AI-powered handler using LangChain
    try:
        # Build prompt with parameters
        user_prompt = f"""
{expose.prompt_template}

Input parameters:
    {param_placeholders}
"""

        # Call LLM
        messages = []
        if hasattr(globals().get('AGENT_SYSTEM_PROMPT'), '__len__'):
            messages.append(SystemMessage(content=AGENT_SYSTEM_PROMPT))
        messages.append(HumanMessage(content=user_prompt))

        response = llm.invoke(messages)
        result_text = response.content

        # Parse response and structure return values
        # TODO: Improve response parsing based on return types
        return {{
            "{expose.returns[0]["name"] if expose.returns else "result"}": result_text
        }}

    except Exception as e:
        return {{
            "error": {{
                "code": "E_RUNTIME",
                "message": f"LLM call failed: {{str(e)}}"
            }}
        }}'''


def _generate_generic_ai_handler_body(expose: ExposeBlock, agent: AgentDefinition, param_names: List[str]) -> str:
    """Generate generic AI handler when LLM is available but no specific prompt."""
    param_str = ", ".join([f"{{params.get('{p}')}}" for p in param_names])

    return f'''    # Generic AI handler
    try:
        user_prompt = f"Process the following request for {expose.verb}:\\n"
        user_prompt += f"Parameters: {param_str}"

        messages = [HumanMessage(content=user_prompt)]
        response = llm.invoke(messages)

        return {{
            "{expose.returns[0]["name"] if expose.returns else "result"}": response.content
        }}
    except Exception as e:
        return {{
            "error": {{
                "code": "E_RUNTIME",
                "message": f"LLM call failed: {{str(e)}}"
            }}
        }}'''


def _format_params_doc(params: List[Dict[str, str]]) -> str:
    """Format parameters for docstring."""
    if not params:
        return "        None"
    return "\n".join([f'        - {p["name"]} ({p["type"]})' for p in params])


def _format_returns_doc(returns: List[Dict[str, str]]) -> str:
    """Format returns for docstring."""
    if not returns:
        return "        None"
    return "\n".join([f'        - {r["name"]} ({r["type"]})' for r in returns])


def _generate_mcp_endpoint(agent: AgentDefinition) -> str:
    """Generate main MCP JSON-RPC endpoint with full MCP protocol support."""

    # Build tool schemas for tools/list method
    tool_schemas = []
    for expose in agent.exposes:
        # Build input schema from parameters
        properties = {}
        required = []
        for param in expose.params:
            param_name = param["name"]
            param_type = param["type"]

            # Convert Promptware types to JSON Schema types
            json_schema_type = param_type
            if param_type == "int":
                json_schema_type = "integer"
            elif param_type == "bool":
                json_schema_type = "boolean"

            properties[param_name] = {
                "type": json_schema_type,
                "description": f"Parameter: {param_name}"
            }
            required.append(param_name)

        tool_schemas.append({
            "name": expose.verb,
            "description": expose.prompt_template or f"Execute {expose.verb}",
            "inputSchema": {
                "type": "object",
                "properties": properties,
                "required": required
            }
        })

    tool_schemas_json = repr(tool_schemas)

    # Build verb routing for tools/call
    verb_routes = []
    for i, expose in enumerate(agent.exposes):
        handler_name = expose.verb.replace(".", "_").replace("@", "_")
        prefix = "if" if i == 0 else "elif"
        verb_routes.append(f'''            {prefix} verb_name == "{expose.verb}":
                verb_result = handle_{handler_name}(verb_params)''')

    # If no verbs defined, add a catch-all if statement
    if not verb_routes:
        verb_routing = "            if False:  # No verbs defined\n                pass"
    else:
        verb_routing = "\n".join(verb_routes)

    return f'''@app.post("/mcp")
async def mcp_endpoint(request: Request):
    """
    Main MCP endpoint - implements full MCP JSON-RPC protocol.

    Supports methods:
    - initialize: Return server capabilities
    - tools/list: List all available tools
    - tools/call: Execute a tool/verb
    """
    try:
        body = await request.json()
        method = body.get("method")
        params = body.get("params", {{}})
        request_id = body.get("id", 1)

        if not method:
            return JSONResponse(
                status_code=400,
                content={{
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {{
                        "code": -32600,
                        "message": "Invalid Request: missing method"
                    }}
                }}
            )

        # Handle MCP protocol methods
        if method == "initialize":
            # Return server capabilities
            return JSONResponse(
                content={{
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {{
                        "protocolVersion": "0.1.0",
                        "capabilities": {{
                            "tools": {{}},
                            "prompts": {{}}
                        }},
                        "serverInfo": {{
                            "name": "{agent.name}",
                            "version": "v1"
                        }}
                    }}
                }}
            )

        elif method == "tools/list":
            # Return tool schemas
            return JSONResponse(
                content={{
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {{
                        "tools": {tool_schemas_json}
                    }}
                }}
            )

        elif method == "tools/call":
            # Execute tool with full MCP envelope
            tool_name = params.get("name")
            verb_params = params.get("arguments", {{}})

            if not tool_name:
                return JSONResponse(
                    status_code=400,
                    content={{
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {{
                            "code": -32602,
                            "message": "Invalid params: missing tool name"
                        }}
                    }}
                )

            agent_state["requests_handled"] += 1

            # Execute tools first (if agent has tools)
            tool_results = {{}}
            tools_executed = []
            if has_tools():
                tool_results = execute_tools(verb_params)
                tools_executed = list(tool_results.keys())

            # Route to appropriate verb handler
            verb_name = tool_name
            verb_result = None

{verb_routing}
            else:
                return JSONResponse(
                    status_code=404,
                    content={{
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {{
                            "code": -32601,
                            "message": f"Method not found: {{tool_name}}"
                        }}
                    }}
                )

            # Check for errors
            if verb_result and "error" in verb_result:
                return JSONResponse(
                    status_code=400,
                    content={{
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {{
                            "code": -32000,
                            "message": verb_result["error"].get("message", "Unknown error")
                        }}
                    }}
                )

            # Determine mode (IDE-integrated vs standalone AI)
            import os
            has_api_key = bool(os.environ.get("ANTHROPIC_API_KEY"))
            mode = "standalone_ai" if (has_api_key and {bool(agent.llm)}) else "ide_integrated"

            # Build MCP-compliant response
            response_data = {{
                "input_params": verb_params,
                "tool_results": tool_results,
                "metadata": {{
                    "mode": mode,
                    "agent_name": "{agent.name}",
                    "timestamp": datetime.now().isoformat(),
                    "tools_executed": tools_executed
                }}
            }}

            # Merge verb result into response
            if verb_result:
                response_data.update(verb_result)

            return JSONResponse(
                content={{
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": response_data
                }}
            )

        else:
            return JSONResponse(
                status_code=404,
                content={{
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {{
                        "code": -32601,
                        "message": f"Method not found: {{method}}"
                    }}
                }}
            )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={{
                "jsonrpc": "2.0",
                "id": body.get("id", 1) if "body" in locals() else 1,
                "error": {{
                    "code": -32603,
                    "message": f"Internal error: {{str(e)}}"
                }}
            }}
        )


{get_health_endpoints_pattern("python", agent.name)["health"]}

{get_health_endpoints_pattern("python", agent.name)["ready"]}

@app.get("/verbs")
async def list_verbs():
    """List all exposed MCP verbs."""
    return {{
        "agent": "{agent.name}",
        "verbs": {[e.verb for e in agent.exposes]}
    }}'''


def _generate_temporal_workflows(agent: AgentDefinition) -> str:
    """Generate Temporal workflow and activity classes."""
    code_parts = []

    for workflow_def in agent.workflows:
        # Generate activity functions for each step
        for step in workflow_def.steps:
            code_parts.append(_generate_activity_function(step, workflow_def))

        # Generate workflow class
        code_parts.append(_generate_workflow_class(workflow_def, agent))

    return "\n\n".join(code_parts)


def _generate_activity_function(step: WorkflowStep, workflow_def: WorkflowDefinition) -> str:
    """Generate a Temporal activity function."""
    activity_name = step.activity

    # Parse timeout (e.g., "10m" -> timedelta(minutes=10))
    timeout_code = ""
    if step.timeout:
        timeout_code = f", start_to_close_timeout=timedelta({_parse_timeout(step.timeout)})"

    return f'''@activity.defn(name="{activity_name}"{timeout_code})
async def {activity_name}(**kwargs) -> Dict[str, Any]:
    """
    Activity: {activity_name}
    Workflow: {workflow_def.name}
    """
    # TODO: Implement actual activity logic
    print(f"Executing activity: {activity_name}")
    return {{"status": "completed"}}'''


def _generate_workflow_class(workflow_def: WorkflowDefinition, agent: AgentDefinition) -> str:
    """Generate a Temporal workflow class."""
    workflow_name = workflow_def.name.replace("@", "_").replace(".", "_")

    # Build workflow steps execution
    steps_code = []
    for i, step in enumerate(workflow_def.steps):
        activity_name = step.activity

        # Build retry policy
        retry_policy = ""
        if step.retry > 0:
            retry_policy = f", retry_policy=workflow.RetryPolicy(maximum_attempts={step.retry})"

        # Build activity execution
        step_code = f'''        # Step {i+1}: {activity_name}
        result_{i} = await workflow.execute_activity(
            {activity_name},
            schedule_to_close_timeout=timedelta(minutes=10){retry_policy}
        )'''

        # Add compensation logic if on_failure is specified
        if step.on_failure:
            step_code += f'''
        if result_{i}.get("status") != "completed":
            # Compensation: {step.on_failure}
            await workflow.execute_activity(
                {step.on_failure},
                schedule_to_close_timeout=timedelta(minutes=5)
            )
            raise workflow.ApplicationError("Step {activity_name} failed")'''

        # Add approval wait if required
        if step.requires_approval:
            step_code += f'''

        # Wait for approval before continuing
        await workflow.wait_condition(lambda: workflow_state.get("approved_{i}", False))'''

        steps_code.append(step_code)

    steps_execution = "\n\n".join(steps_code)

    # Build params and returns
    param_types = ", ".join([f"{p['name']}: {_map_pw_type_to_python(p['type'])}" for p in workflow_def.params])
    return_type = "Dict[str, Any]"

    return f'''@workflow.defn(name="{workflow_def.name}")
class {workflow_name.title()}Workflow:
    """
    Temporal workflow: {workflow_def.name}

    Parameters: {", ".join([p["name"] for p in workflow_def.params])}
    Returns: {", ".join([r["name"] for r in workflow_def.returns])}
    """

    def __init__(self):
        self.workflow_state = {{}}

    @workflow.run
    async def run(self, {param_types}) -> {return_type}:
        """Execute workflow steps."""
{steps_execution}

        # Return workflow result
        return {{
            {", ".join([f'"{r["name"]}": "value"' for r in workflow_def.returns])}
        }}'''


def _parse_timeout(timeout_str: str) -> str:
    """Parse timeout string (e.g., '10m', '5s') to timedelta args."""
    if timeout_str.endswith('m'):
        return f"minutes={timeout_str[:-1]}"
    elif timeout_str.endswith('s'):
        return f"seconds={timeout_str[:-1]}"
    elif timeout_str.endswith('h'):
        return f"hours={timeout_str[:-1]}"
    else:
        return f"seconds={timeout_str}"


def _map_pw_type_to_python(pw_type: str) -> str:
    """Map .al types to Python type hints."""
    type_map = {
        "string": "str",
        "int": "int",
        "bool": "bool",
        "object": "Dict[str, Any]",
        "array": "List[Any]"
    }
    return type_map.get(pw_type, "Any")


def _generate_server_startup(agent: AgentDefinition) -> str:
    """Generate server startup code."""
    return f'''if __name__ == "__main__":
    print(f"Starting MCP server for agent: {agent.name}")
    print(f"Port: {agent.port}")
    print(f"Exposed verbs: {[e.verb for e in agent.exposes]}")
    print(f"Health check: http://127.0.0.1:{agent.port}/health")
    print(f"MCP endpoint: http://127.0.0.1:{agent.port}/mcp")

    uvicorn.run(
        app,
        host="127.0.0.1",
        port={agent.port},
        log_level="info"
    )'''


def generate_mcp_server_from_pw(pw_code: str) -> str:
    """
    Convenience function: parse .al code and generate MCP server.

    Args:
        pw_code: .al file content

    Returns:
        Python code for MCP server
    """
    from language.agent_parser import parse_agent_pw

    agent = parse_agent_pw(pw_code)
    return generate_python_mcp_server(agent)