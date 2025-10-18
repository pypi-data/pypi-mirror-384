"""
LangGraph integration for Promptware contracts.

Enables LangGraph state machines to use PW contracts for validated state management.

Components:
- ContractNode: Optional wrapper for additional validation features
- State schema generation via TypedDict
- Node functions with embedded contract validation

Usage:
    ```python
    # Generate TypedDict state + node functions from PW contract
    asl build contract.al --lang python --typeddict -o state.py

    # Use in LangGraph
    from langgraph.graph import StateGraph, END
    from state import ProcessorState, loadData, processData

    workflow = StateGraph(ProcessorState)
    workflow.add_node("load", loadData)
    workflow.add_node("process", processData)
    workflow.add_edge("load", "process")
    workflow.add_edge("process", END)
    workflow.set_entry_point("load")

    app = workflow.compile()
    result = app.invoke(initial_state)
    # Contracts validate automatically at each node
    ```
"""

__all__ = []
