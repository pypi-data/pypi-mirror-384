"""Tool executor for running tools referenced by agents."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List

# Add tools directory to path for imports
tools_dir = Path(__file__).parent.parent / "tools"
if str(tools_dir) not in sys.path:
    sys.path.insert(0, str(tools_dir))

from tools.envelope import error
from tools.registry import get_registry


class ToolExecutor:
    """Executes tools referenced by agents.

    This class handles:
    - Loading tools from the registry
    - Mapping agent parameters to tool inputs
    - Executing tools with proper error handling
    - Aggregating results from multiple tools
    """

    def __init__(self, agent_tools: List[str]):
        """Initialize executor with tools needed by agent.

        Args:
            agent_tools: List of tool names referenced by agent
        """
        self.registry = get_registry()
        self.tool_names = agent_tools or []
        self.loaded_tools = {}

        # Load all tools upfront
        for tool_name in self.tool_names:
            tool = self.registry.get_tool(tool_name)
            if tool:
                self.loaded_tools[tool_name] = tool

    def execute_tools(self, verb_params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute all agent's tools with given parameters.

        Args:
            verb_params: Parameters from verb invocation

        Returns:
            Dict mapping tool names to their results
        """
        if not self.loaded_tools:
            return {}

        results = {}
        for tool_name, tool in self.loaded_tools.items():
            try:
                # Map verb params to tool params
                # For now, pass all params - tools will ignore what they don't need
                tool_params = self._map_params_to_tool(tool_name, verb_params, tool)

                # Execute tool
                result = self.registry.execute_tool(tool_name, tool_params)
                results[tool_name] = result

            except Exception as e:
                results[tool_name] = error("E_EXECUTION", f"Tool {tool_name} failed: {str(e)}")

        return results

    def _map_params_to_tool(self, tool_name: str, verb_params: Dict[str, Any], tool: Dict) -> Dict[str, Any]:
        """Map verb parameters to tool-specific parameters.

        This is where we handle parameter mapping logic.
        For example:
        - github_fetch_pr tool needs: repo, pr_number
        - review.analyze@v1 verb provides: repo, pr_number
        - Direct mapping works

        Future: Add explicit mapping configuration in agent definitions.
        """
        schema = tool.get('schema', {})
        properties = schema.get('properties', {})

        # For now, simple strategy: pass params that match tool schema
        mapped_params = {}
        for key, value in verb_params.items():
            if key in properties:
                mapped_params[key] = value

        # If no params matched, pass all (tool will filter)
        if not mapped_params:
            mapped_params = verb_params.copy()

        return mapped_params

    def has_tools(self) -> bool:
        """Check if any tools were successfully loaded."""
        return len(self.loaded_tools) > 0

    def get_tool_summary(self) -> str:
        """Get human-readable summary of tools and their status."""
        if not self.tool_names:
            return "No tools configured"

        loaded = len(self.loaded_tools)
        total = len(self.tool_names)
        missing = [t for t in self.tool_names if t not in self.loaded_tools]

        summary = f"Tools: {loaded}/{total} loaded"
        if missing:
            summary += f" (missing: {', '.join(missing)})"

        return summary
