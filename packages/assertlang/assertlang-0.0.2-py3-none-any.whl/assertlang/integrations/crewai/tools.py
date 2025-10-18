"""
CrewAI Contract Tools: Wrap PW functions as CrewAI tools with validation.

Enables CrewAI agents to call contract-validated functions with automatic
precondition and postcondition checking.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional
import inspect

try:
    from crewai.tools import tool as crewai_tool_decorator
    CREWAI_AVAILABLE = True
except ImportError:
    # Fallback if CrewAI not installed
    def crewai_tool_decorator(func):
        return func
    CREWAI_AVAILABLE = False


class ContractTool:
    """
    Wrapper for PW contract functions to use with CrewAI.

    Usage:
        ```python
        from assertlang.integrations.crewai import ContractTool

        # Create tool from validated function
        tool = ContractTool.from_function(analyzeMarket)

        # Use in CrewAI agent
        analyst = Agent(
            role="Market Analyst",
            tools=[tool.to_crewai()]
        )
        ```
    """

    def __init__(self, func: Callable, name: Optional[str] = None, description: Optional[str] = None):
        """
        Initialize ContractTool.

        Args:
            func: Python function with contract validation
            name: Tool name (defaults to function name)
            description: Tool description
        """
        self.func = func
        self.name = name or func.__name__
        self.description = description or func.__doc__ or f"Contract-validated function: {func.__name__}"

    @classmethod
    def from_function(
        cls,
        func: Callable,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> "ContractTool":
        """
        Create ContractTool from a PW-generated function.

        Args:
            func: Function with embedded contract validation
            name: Tool name (optional)
            description: Tool description (optional)

        Returns:
            ContractTool instance
        """
        return cls(func=func, name=name, description=description)

    def to_crewai(self):
        """
        Convert to CrewAI tool using decorator approach.

        Returns:
            CrewAI-compatible tool
        """
        # Create wrapper function with proper metadata
        func = self.func
        name = self.name
        desc = self.description

        # Apply CrewAI tool decorator
        @crewai_tool_decorator
        def tool_wrapper(*args, **kwargs):
            """Wrapped contract-validated function."""
            return func(*args, **kwargs)

        # Set metadata
        tool_wrapper.__name__ = name
        tool_wrapper.__doc__ = desc

        return tool_wrapper

    def __call__(self, **kwargs) -> Any:
        """Allow tool to be called directly."""
        return self.func(**kwargs)

    @classmethod
    def from_pw_file(
        cls,
        pw_file: str,
        function_name: str,
        build_first: bool = True,
    ) -> "ContractTool":
        """
        Create ContractTool from PW file.

        Args:
            pw_file: Path to .al file
            function_name: Name of function to wrap
            build_first: Whether to build Python code first

        Returns:
            ContractTool instance

        Example:
            ```python
            tool = ContractTool.from_pw_file(
                "contracts/market_analyst.al",
                "analyzeMarket"
            )
            ```
        """
        if build_first:
            import subprocess
            import tempfile
            import importlib.util
            from pathlib import Path

            # Build to temp file
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".py", delete=False
            ) as tmp:
                output_path = tmp.name

            subprocess.run(
                [
                    "python3",
                    "promptware/cli.py",
                    "build",
                    pw_file,
                    "--lang",
                    "python",
                    "-o",
                    output_path,
                ],
                check=True,
            )

            # Import generated module
            spec = importlib.util.spec_from_file_location("pw_contract", output_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Get function
            func = getattr(module, function_name)

            return cls.from_function(func)
        else:
            raise NotImplementedError("Must build Python code first")


class ContractToolCollection:
    """Collection of contract tools for an agent."""

    def __init__(self):
        self.tools: Dict[str, ContractTool] = {}

    def add_tool(self, tool: ContractTool):
        """Add tool to collection."""
        self.tools[tool.name] = tool

    def add_from_function(self, func: Callable, name: Optional[str] = None):
        """Add tool from function."""
        tool = ContractTool.from_function(func, name=name)
        self.add_tool(tool)

    def get_tool(self, name: str) -> Optional[ContractTool]:
        """Get tool by name."""
        return self.tools.get(name)

    def list_tools(self) -> List[str]:
        """List all tool names."""
        return list(self.tools.keys())

    def to_crewai_list(self) -> List:
        """Get tools as list for CrewAI agent."""
        return [tool.to_crewai() for tool in self.tools.values()]
