"""Tool registry for dynamic tool loading and execution."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from tools.envelope import error, ok


class ToolRegistry:
    """Central registry for all available tools.

    Tools are discovered from the tools/ directory and can be loaded
    dynamically by name. Each tool must have:
    - A schema file: schemas/tools/{tool_name}.v1.json
    - An adapter: tools/{tool_name}/adapters/adapter_py.py with handle() function
    """

    def __init__(self):
        self.tools_dir = Path(__file__).parent
        self.schemas_dir = self.tools_dir.parent / "schemas" / "tools"
        self._cache: Dict[str, Any] = {}
        self._schema_cache: Dict[str, Dict] = {}

    def get_tool(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Load tool implementation and schema by name.

        Args:
            tool_name: Name of tool (e.g., 'http', 'storage', 'auth')

        Returns:
            Dict with 'handle' function and 'schema', or None if not found
        """
        if tool_name in self._cache:
            return self._cache[tool_name]

        # Find adapter
        adapter_paths = [
            self.tools_dir / tool_name / "adapters" / "adapter_py.py",
            self.tools_dir / tool_name.replace("_", "-") / "adapters" / "adapter_py.py",
        ]

        adapter_module = None
        for adapter_path in adapter_paths:
            if adapter_path.exists():
                adapter_module = self._load_module(adapter_path)
                break

        if not adapter_module:
            return None

        # Check for handle function
        if not hasattr(adapter_module, 'handle'):
            return None

        # Load schema
        schema = self._load_schema(tool_name)

        tool_impl = {
            'handle': adapter_module.handle,
            'schema': schema,
            'version': getattr(adapter_module, 'VERSION', 'v1'),
            'name': tool_name
        }

        self._cache[tool_name] = tool_impl
        return tool_impl

    def _load_module(self, module_path: Path) -> Optional[Any]:
        """Dynamically load Python module from file path."""
        try:
            spec = importlib.util.spec_from_file_location("tool_adapter", module_path)
            if not spec or not spec.loader:
                return None

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
        except Exception:
            return None

    def _load_schema(self, tool_name: str) -> Optional[Dict]:
        """Load JSON schema for tool."""
        if tool_name in self._schema_cache:
            return self._schema_cache[tool_name]

        schema_paths = [
            self.schemas_dir / f"{tool_name}.v1.json",
            self.schemas_dir / f"{tool_name.replace('_', '-')}.v1.json",
        ]

        for schema_path in schema_paths:
            if schema_path.exists():
                try:
                    with open(schema_path, 'r') as f:
                        schema = json.load(f)
                        self._schema_cache[tool_name] = schema
                        return schema
                except Exception:
                    pass

        return None

    def list_available_tools(self) -> List[str]:
        """List all available tools in tools/ directory."""
        tools = []
        for item in self.tools_dir.iterdir():
            if item.is_dir() and not item.name.startswith("_"):
                # Check if has adapter
                adapter_path = item / "adapters" / "adapter_py.py"
                if adapter_path.exists():
                    tools.append(item.name)
        return sorted(tools)

    def execute_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool with given parameters.

        Args:
            tool_name: Name of tool to execute
            params: Parameters to pass to tool (matches tool schema)

        Returns:
            Tool response in envelope format: {ok: bool, version: str, data?: dict, error?: dict}
        """
        tool = self.get_tool(tool_name)
        if not tool:
            return error("E_TOOL_NOT_FOUND", f"Tool not found: {tool_name}")

        try:
            result = tool['handle'](params)

            # Tools already return envelope format
            if isinstance(result, dict) and 'ok' in result:
                return result

            # Wrap non-envelope responses
            return ok({"result": result})

        except Exception as e:
            return error("E_TOOL_EXECUTION", f"Tool execution failed: {str(e)}")


# Global registry instance
_registry = None


def get_registry() -> ToolRegistry:
    """Get the global tool registry instance."""
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry
