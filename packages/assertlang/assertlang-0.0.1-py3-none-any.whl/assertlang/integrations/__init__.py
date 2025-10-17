"""
Promptware integrations with popular AI agent frameworks.

Supported frameworks:
- CrewAI: Multi-agent collaboration with contracts
- LangGraph: State machine agents with contract validation

Usage:
    # CrewAI Integration
    from assertlang.integrations.crewai import ContractTool, ContractRegistry

    # LangGraph Integration
    # Generate TypedDict + node functions:
    # asl build contract.al --lang python
    # Then use with LangGraph StateGraph
"""

__all__ = ["crewai", "langgraph"]
