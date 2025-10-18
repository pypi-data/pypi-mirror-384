"""
CrewAI integration for Promptware contracts.

Enables CrewAI agents to use PW contracts for type-safe coordination.

Components:
- ContractTool: Wraps PW functions as CrewAI tools with validation
- ContractRegistry: Enables agent contract discovery
- ContractAgent: CrewAI agent with built-in contract support
"""

from .tools import ContractTool
from .registry import ContractRegistry

__all__ = ["ContractTool", "ContractRegistry"]
