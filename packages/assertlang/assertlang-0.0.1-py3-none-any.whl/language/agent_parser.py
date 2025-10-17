"""
Agent-specific DSL parser extensions for Promptware.

Extends the core parser to handle:
- `agent <name>` directive
- `port <number>` directive
- `expose <verb>` blocks with params/returns
- Agent-to-agent `call` statements
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class WorkflowStep:
    """Represents a step in a Temporal workflow."""
    activity: str
    timeout: Optional[str] = None  # e.g., "10m", "5s"
    retry: int = 0
    on_failure: Optional[str] = None  # Compensation activity
    requires_approval: bool = False


@dataclass
class WorkflowDefinition:
    """Represents a Temporal workflow."""
    name: str  # e.g., "deploy_service@v1"
    params: List[Dict[str, str]] = field(default_factory=list)
    returns: List[Dict[str, str]] = field(default_factory=list)
    steps: List[WorkflowStep] = field(default_factory=list)


@dataclass
class ExposeBlock:
    """Represents an MCP verb exposed by an agent."""
    verb: str  # e.g., "task.execute@v1"
    params: List[Dict[str, str]] = field(default_factory=list)  # [{"name": "task_id", "type": "string"}]
    returns: List[Dict[str, str]] = field(default_factory=list)  # [{"name": "status", "type": "string"}]
    handler_code: Optional[str] = None  # Optional handler implementation
    prompt_template: Optional[str] = None  # Per-verb prompt template (for AI agents)

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "verb": self.verb,
            "params": self.params,
            "returns": self.returns,
        }
        if self.handler_code:
            result["handler_code"] = self.handler_code
        if self.prompt_template:
            result["prompt_template"] = self.prompt_template
        return result


@dataclass
class ObservabilityConfig:
    """Observability configuration for an agent."""
    traces: bool = True
    metrics: bool = True
    logs: str = "structured"  # "structured", "json", "plain"
    export_to: Optional[str] = None  # "jaeger", "grafana", "honeycomb", "console"


@dataclass
class AgentDefinition:
    """Represents a complete agent definition from .al file."""
    name: str
    lang: str
    port: int = 23456
    exposes: List[ExposeBlock] = field(default_factory=list)
    calls: List[Dict[str, Any]] = field(default_factory=list)  # Calls to other agents
    files: List[Dict[str, Any]] = field(default_factory=list)
    # AI-specific fields
    llm: Optional[str] = None  # e.g., "anthropic claude-3-5-sonnet-20241022"
    tools: List[str] = field(default_factory=list)  # Tool names available to agent
    memory: Optional[str] = None  # Memory configuration (e.g., "buffer", "summary")
    prompt_template: Optional[str] = None  # System prompt template
    # Observability
    observability: Optional[ObservabilityConfig] = None
    # Temporal workflows
    temporal: bool = False  # Whether agent uses Temporal
    workflows: List[WorkflowDefinition] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "agent": self.name,
            "lang": self.lang,
            "port": self.port,
            "exposes": [e.to_dict() for e in self.exposes],
            "calls": self.calls,
            "files": self.files,
        }
        # Include AI fields if present
        if self.llm:
            result["llm"] = self.llm
        if self.tools:
            result["tools"] = self.tools
        if self.memory:
            result["memory"] = self.memory
        if self.prompt_template:
            result["prompt_template"] = self.prompt_template
        return result


def parse_agent_pw(text: str) -> AgentDefinition:
    """
    Parse a .al file that defines an agent.

    Example:
        lang python
        agent code-reviewer
        port 23456

        expose review.submit@v1:
          params:
            pr_url string
          returns:
            review_id string
            status string

        call notifier send.slack@v1 message="Review complete"
    """
    lines = text.splitlines()
    agent_def = None
    current_expose = None
    current_workflow = None
    current_workflow_step = None
    current_section = None  # "params", "returns", "workflow", "workflow_steps", etc.

    i = 0
    while i < len(lines):
        raw_line = lines[i]
        stripped = raw_line.strip()

        # Skip empty lines and comments
        if not stripped or stripped.startswith("#"):
            i += 1
            continue

        indent = len(raw_line) - len(raw_line.lstrip(" "))
        tokens = _tokenize(stripped)

        if not tokens:
            i += 1
            continue

        head = tokens[0]
        args = tokens[1:]

        # Parse directives
        if head == "lang":
            if not args:
                raise ValueError("lang directive requires a value")
            if agent_def is None:
                agent_def = AgentDefinition(name="unnamed", lang=args[0])
            else:
                agent_def.lang = args[0]

        elif head == "agent":
            if not args:
                raise ValueError("agent directive requires a name")
            # Agent name can be multi-word, join all args
            agent_name = " ".join(args)
            if agent_def is None:
                agent_def = AgentDefinition(name=agent_name, lang="python")
            else:
                agent_def.name = agent_name

        elif head == "port":
            if not args:
                raise ValueError("port directive requires a number")
            if agent_def is None:
                raise ValueError("port directive must come after agent/lang")
            agent_def.port = int(args[0])

        elif head == "llm":
            # Parse: llm anthropic claude-3-5-sonnet-20241022
            if not args:
                raise ValueError("llm directive requires provider and model")
            if agent_def is None:
                raise ValueError("llm directive must come after agent/lang")
            # Combine all args as the LLM spec
            agent_def.llm = " ".join(args)

        elif head == "memory":
            # Parse: memory buffer / memory summary
            if not args:
                raise ValueError("memory directive requires a type")
            if agent_def is None:
                raise ValueError("memory directive must come after agent/lang")
            agent_def.memory = args[0]

        elif head == "temporal:":
            # Parse: temporal: true
            if not args:
                raise ValueError("temporal directive requires a value")
            if agent_def is None:
                raise ValueError("temporal directive must come after agent/lang")
            agent_def.temporal = args[0].lower() in ("true", "yes", "1")

        elif head == "workflow" and stripped.endswith(":"):
            # Start workflow block
            workflow_name = stripped[9:-1].strip()  # Remove "workflow " and ":"
            if not workflow_name:
                raise ValueError(f"Missing workflow name on line {i+1}")
            current_workflow = WorkflowDefinition(name=workflow_name)
            current_section = "workflow"
            if agent_def:
                agent_def.workflows.append(current_workflow)

        elif head == "params:" and current_section == "workflow":
            current_section = "workflow_params"

        elif head == "returns:" and current_section == "workflow":
            current_section = "workflow_returns"

        elif head == "returns:" and current_section == "workflow_params":
            # Switch from params to returns
            current_section = "workflow_returns"

        elif head == "steps:" and current_section in ("workflow", "workflow_params", "workflow_returns"):
            current_section = "workflow_steps"

        elif indent > 0 and current_workflow and current_section in ("workflow_params", "workflow_returns"):
            # Parse workflow param/return definition
            if len(tokens) >= 2:
                param_name = tokens[0]
                param_type = tokens[1]
                entry = {"name": param_name, "type": param_type}

                if current_section == "workflow_params":
                    current_workflow.params.append(entry)
                elif current_section == "workflow_returns":
                    current_workflow.returns.append(entry)

        elif stripped.startswith("- activity:") and current_section == "workflow_steps":
            # Start new workflow step
            activity_name = stripped[11:].strip()  # Remove "- activity:"
            if activity_name and current_workflow:
                current_workflow_step = WorkflowStep(activity=activity_name)
                current_workflow.steps.append(current_workflow_step)

        elif current_section == "workflow_steps" and current_workflow_step and indent > 2 and ":" in stripped:
            # Parse step attributes (timeout, retry, on_failure, requires_approval)
            key, value = stripped.split(":", 1)
            key = key.strip()
            value = value.strip()

            if key == "timeout":
                current_workflow_step.timeout = value
            elif key == "retry":
                current_workflow_step.retry = int(value)
            elif key == "on_failure":
                current_workflow_step.on_failure = value
            elif key == "requires_approval":
                current_workflow_step.requires_approval = value.lower() in ("true", "yes", "1")

        elif head == "tools:":
            # Start tools block (next lines are tool names)
            # Will be handled by next iteration with indent check
            current_section = "tools"

        elif head == "prompt_template:" and not current_expose:
            # Global prompt template block (agent-level, not verb-level)
            current_section = "prompt_template"
            prompt_lines = []
            i += 1
            while i < len(lines):
                next_line = lines[i]
                if not next_line.strip():
                    i += 1
                    continue
                next_indent = len(next_line) - len(next_line.lstrip(" "))
                if next_indent <= indent and next_line.strip() and not next_line.strip().startswith("#"):
                    break
                prompt_lines.append(next_line.strip())
                i += 1
            if agent_def and prompt_lines:
                agent_def.prompt_template = "\n".join(prompt_lines)
            continue  # Already incremented i

        elif current_section == "tools" and indent > 0:
            # Parse tool name (e.g., "- github_fetch_pr")
            tool_name = stripped.lstrip("- ").strip()
            if tool_name and agent_def:
                agent_def.tools.append(tool_name)

        elif head == "observability:":
            # Start observability block
            current_section = "observability"
            if agent_def and not agent_def.observability:
                agent_def.observability = ObservabilityConfig()

        elif current_section == "observability" and indent > 0 and ":" in stripped:
            # Parse observability config (e.g., "traces: true")
            key, value = stripped.split(":", 1)
            key = key.strip()
            value = value.strip().lower()

            if agent_def and agent_def.observability:
                if key == "traces":
                    agent_def.observability.traces = value in ("true", "yes", "1")
                elif key == "metrics":
                    agent_def.observability.metrics = value in ("true", "yes", "1")
                elif key == "logs":
                    agent_def.observability.logs = value
                elif key == "export_to":
                    agent_def.observability.export_to = value

        elif head == "expose" and stripped.endswith(":"):
            # Start new expose block
            verb = stripped[7:-1].strip()  # Remove "expose " and ":"
            if not verb:
                raise ValueError(f"Missing verb name on line {i+1}")
            current_expose = ExposeBlock(verb=verb)
            current_section = "expose"  # Reset section tracking
            if agent_def:
                agent_def.exposes.append(current_expose)

        elif head == "params:" and current_expose:
            current_section = "params"

        elif head == "returns:" and current_expose:
            current_section = "returns"

        elif head == "prompt_template:" and current_expose:
            # Per-verb prompt template (inside expose block)
            current_section = "verb_prompt_template"
            base_indent = indent  # Save current indent level (e.g., 2 for expose content)
            prompt_lines = []
            i += 1
            while i < len(lines):
                next_line = lines[i]
                if not next_line.strip():
                    i += 1
                    continue
                next_indent = len(next_line) - len(next_line.lstrip(" "))
                # Stop if we hit a line at same or lower indent (new section)
                if next_indent <= base_indent:
                    break
                prompt_lines.append(next_line.strip())
                i += 1
            if current_expose and prompt_lines:
                current_expose.prompt_template = "\n".join(prompt_lines)
            continue  # Already incremented i

        elif indent > 0 and current_expose and current_section in ("params", "returns"):
            # Parse param/return definition
            # Format: "name type" (e.g., "task_id string", "priority int")
            if len(tokens) >= 2:
                param_name = tokens[0]
                param_type = tokens[1]
                entry = {"name": param_name, "type": param_type}

                if current_section == "params":
                    current_expose.params.append(entry)
                elif current_section == "returns":
                    current_expose.returns.append(entry)

        elif head == "call":
            # Agent-to-agent call
            if not args:
                raise ValueError("call directive requires agent and verb")
            # Parse: call <agent-name> <verb> <params...>
            if len(args) < 2:
                raise ValueError("call requires agent name and verb")

            agent_name = args[0]
            verb = args[1]
            params_raw = args[2:]

            # Parse key=value params
            params = {}
            for param in params_raw:
                if "=" in param:
                    key, value = param.split("=", 1)
                    params[key] = _decode_value(value.strip())

            if agent_def:
                agent_def.calls.append({
                    "agent": agent_name,
                    "verb": verb,
                    "params": params,
                })

        elif head == "file" and stripped.endswith(":"):
            # File block (same as regular .al)
            path = stripped[5:-1].strip()
            if not path:
                raise ValueError(f"Missing path for file on line {i+1}")

            # Collect file content (next lines with indent)
            content_lines = []
            i += 1
            while i < len(lines):
                next_line = lines[i]
                if not next_line.strip():
                    i += 1
                    continue
                next_indent = len(next_line) - len(next_line.lstrip(" "))
                if next_indent <= indent:
                    break
                content_lines.append(next_line[indent + 2:])  # Remove base indent
                i += 1

            if agent_def:
                agent_def.files.append({
                    "path": path.strip('"').strip("'"),
                    "content": "\n".join(content_lines),
                })
            continue  # Already incremented i in inner loop

        i += 1

    if agent_def is None:
        raise ValueError("No agent definition found (must specify 'agent' and 'lang')")

    return agent_def


def _tokenize(line: str) -> List[str]:
    """Simple tokenizer that splits on whitespace, preserving quoted strings."""
    tokens = []
    current = []
    in_quotes = False
    quote_char = None

    for char in line:
        if char in ('"', "'") and not in_quotes:
            in_quotes = True
            quote_char = char
            current.append(char)
        elif char == quote_char and in_quotes:
            in_quotes = False
            quote_char = None
            current.append(char)
        elif char.isspace() and not in_quotes:
            if current:
                tokens.append("".join(current))
                current = []
        else:
            current.append(char)

    if current:
        tokens.append("".join(current))

    return tokens


def _decode_value(value: str) -> Any:
    """Decode a value from .al syntax."""
    value = value.strip()

    # Remove quotes
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1]

    # Try int
    try:
        return int(value)
    except ValueError:
        pass

    # Try bool
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False

    # Return as-is (might be a reference)
    return value