"""
Contract Registry: Enable agent contract discovery and validation.

Allows agents to:
- Register their contracts
- Discover other agents' contracts
- Validate calls to other agents before execution
"""

from __future__ import annotations

from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
import importlib.util

from dsl.pw_parser import parse_pw
from dsl.ir import IRModule, IRFunction
from assertlang.integrations.crewai.tools import ContractTool


class ContractRegistry:
    """
    Registry of agent contracts for discovery and validation.

    Usage:
        ```python
        from assertlang.integrations.crewai import ContractRegistry

        # Create registry
        registry = ContractRegistry()

        # Register agent contracts
        registry.register("analyst", "contracts/market_analyst.al")
        registry.register("researcher", "contracts/researcher.al")

        # Discover contracts
        analyst_contract = registry.get_contract("analyst")
        functions = registry.list_functions("analyst")

        # Get tool for cross-agent calls
        tool = registry.get_tool("analyst", "analyzeMarket")
        ```
    """

    def __init__(self):
        """Initialize contract registry."""
        self.contracts: Dict[str, IRModule] = {}
        self.tools: Dict[str, Dict[str, ContractTool]] = {}
        self.python_modules: Dict[str, Any] = {}

    def register(
        self,
        agent_name: str,
        contract_path: str,
        build_python: bool = True,
    ):
        """
        Register agent's contract.

        Args:
            agent_name: Name of the agent
            contract_path: Path to .al contract file
            build_python: Whether to build Python code

        Example:
            ```python
            registry.register("analyst", "contracts/analyst.al")
            ```
        """
        # Parse PW contract
        with open(contract_path, "r") as f:
            source = f.read()

        module = parse_pw(source)
        self.contracts[agent_name] = module

        # Build and import Python code if requested
        if build_python:
            self._build_and_import(agent_name, contract_path)

    def _build_and_import(self, agent_name: str, contract_path: str):
        """Build Python code and import for runtime use."""
        import subprocess
        import tempfile

        # Build to temp file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as tmp:
            output_path = tmp.name

        try:
            subprocess.run(
                [
                    "python",
                    "promptware/cli.py",
                    "build",
                    contract_path,
                    "--lang",
                    "python",
                    "-o",
                    output_path,
                ],
                check=True,
                capture_output=True,
            )

            # Import generated module
            spec = importlib.util.spec_from_file_location(
                f"pw_contract_{agent_name}", output_path
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            self.python_modules[agent_name] = module

            # Create tools for all functions
            ir_module = self.contracts[agent_name]
            self.tools[agent_name] = {}

            for func in ir_module.functions:
                # Get Python function
                py_func = getattr(module, func.name, None)
                if py_func:
                    tool = ContractTool.from_function(
                        py_func,
                        name=func.name,
                        description=func.doc or f"Contract function: {func.name}",
                    )
                    self.tools[agent_name][func.name] = tool

        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"Failed to build contract for {agent_name}: {e.stderr.decode()}"
            )

    def get_contract(self, agent_name: str) -> Optional[IRModule]:
        """
        Get agent's contract IR.

        Args:
            agent_name: Name of the agent

        Returns:
            IR module or None if not found
        """
        return self.contracts.get(agent_name)

    def get_tool(self, agent_name: str, function_name: str) -> Optional[ContractTool]:
        """
        Get contract tool for calling agent function.

        Args:
            agent_name: Name of the agent
            function_name: Name of the function

        Returns:
            ContractTool or None if not found
        """
        agent_tools = self.tools.get(agent_name, {})
        return agent_tools.get(function_name)

    def list_agents(self) -> List[str]:
        """List all registered agents."""
        return list(self.contracts.keys())

    def list_functions(self, agent_name: str) -> List[str]:
        """
        List all functions for an agent.

        Args:
            agent_name: Name of the agent

        Returns:
            List of function names
        """
        contract = self.contracts.get(agent_name)
        if not contract:
            return []

        return [func.name for func in contract.functions]

    def get_function_signature(
        self, agent_name: str, function_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get function signature including contracts.

        Args:
            agent_name: Name of the agent
            function_name: Name of the function

        Returns:
            Function signature dict with parameters, return type, contracts
        """
        contract = self.contracts.get(agent_name)
        if not contract:
            return None

        for func in contract.functions:
            if func.name == function_name:
                return {
                    "name": func.name,
                    "parameters": [
                        {
                            "name": param.name,
                            "type": param.param_type.name
                            if param.param_type
                            else "any",
                        }
                        for param in func.params
                    ],
                    "return_type": func.return_type.name if func.return_type else "void",
                    "preconditions": [
                        {"name": clause.name, "expression": str(clause.expression)}
                        for clause in func.requires
                    ],
                    "postconditions": [
                        {"name": clause.name, "expression": str(clause.expression)}
                        for clause in func.ensures
                    ],
                    "doc": func.doc,
                }

        return None

    def validate_call(
        self,
        agent_name: str,
        function_name: str,
        **kwargs,
    ) -> bool:
        """
        Validate a call to another agent's function (preconditions only).

        Args:
            agent_name: Name of the agent
            function_name: Name of the function
            **kwargs: Function arguments

        Returns:
            True if preconditions pass

        Raises:
            ContractViolationError: If preconditions fail
        """
        tool = self.get_tool(agent_name, function_name)
        if not tool:
            raise ValueError(
                f"No tool found for {agent_name}.{function_name}"
            )

        # Call the tool (which has built-in contract validation)
        # This validates preconditions before execution
        try:
            tool(**kwargs)
            return True
        except Exception:
            raise

    def discover(self, agent_name: str) -> Dict[str, Any]:
        """
        Discover agent's full contract.

        Args:
            agent_name: Name of the agent

        Returns:
            Full contract information
        """
        contract = self.contracts.get(agent_name)
        if not contract:
            return {}

        return {
            "agent": agent_name,
            "functions": [
                self.get_function_signature(agent_name, func.name)
                for func in contract.functions
            ],
            "types": [
                {"name": type_def.name, "fields": [f.name for f in type_def.fields]}
                for type_def in contract.types
            ],
        }


# Global registry instance
_global_registry = ContractRegistry()


def get_global_registry() -> ContractRegistry:
    """Get the global contract registry."""
    return _global_registry
