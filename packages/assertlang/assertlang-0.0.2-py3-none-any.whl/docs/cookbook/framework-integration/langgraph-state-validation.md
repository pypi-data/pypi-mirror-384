# LangGraph State Validation

**Validate state transitions in LangGraph workflows with AssertLang contracts for reliable multi-agent coordination.**

---

## Problem

LangGraph state machines need validation:
- Invalid state transitions cause silent bugs
- Malformed state objects crash workflows
- No compile-time guarantees on state shape
- Hard to debug state-related issues
- Missing fields go undetected

**Bad approach:**
```python
# Python: No state validation
def process_node(state: dict):
    # What if 'messages' is missing?
    # What if 'current_step' is invalid?
    messages = state['messages']  # KeyError!
    step = state['current_step']  # Could be anything!
    # ...
```

**Issues:**
- Runtime crashes on missing fields
- Invalid state allowed
- No validation on transitions
- Hard to track state evolution

---

## Solution

Use AssertLang contracts with LangGraph TypedDict:

**1. Define state with contracts:**
```promptware
type AgentState:
  messages: List<String>
  current_step: String
  result: Option<String>
end

function validate_state(state: AgentState) -> Result<AgentState, String>
  requires:
    len(state.messages) >= 0
    len(state.current_step) > 0
  do
    # Validate current_step is valid
    let valid_steps = ["research", "analyze", "summarize", "complete"]
    let step_valid = false

    for step in valid_steps:
      if state.current_step == step:
        step_valid = true
      end
    end

    if not step_valid:
      return Err("Invalid step: " + state.current_step)
    end

    return Ok(state)
  end
end
```

**2. Generate Python TypedDict:**
```bash
asl build agent_state.al --lang typeddict -o state.py
```

**3. Use in LangGraph:**
```python
from langgraph.graph import StateGraph
from state import AgentState
from agent_validation import validate_state, Err

def research_node(state: AgentState) -> AgentState:
    """Research node with state validation."""

    # Validate input state
    result = validate_state(state)
    if isinstance(result, Err):
        raise ValueError(f"Invalid state: {result.error}")

    # Process node
    state["messages"].append("Research complete")
    state["current_step"] = "analyze"

    # Validate output state
    result = validate_state(state)
    if isinstance(result, Err):
        raise ValueError(f"Invalid output state: {result.error}")

    return state
```

---

## Basic State Patterns

### Simple State Machine

```promptware
type WorkflowState:
  status: String  # "pending" | "processing" | "complete" | "failed"
  data: Option<String>
  error: Option<String>
end

function can_transition(current: String, next: String) -> Bool
  do
    # Pending → Processing
    if current == "pending" and next == "processing":
      return true
    end

    # Processing → Complete | Failed
    if current == "processing":
      return next == "complete" or next == "failed"
    end

    # Terminal states cannot transition
    if current == "complete" or current == "failed":
      return false
    end

    return false
  end
end

function validate_transition(
    current_state: WorkflowState,
    next_status: String
) -> Result<WorkflowState, String>
  do
    if not can_transition(current_state.status, next_status):
      return Err("Invalid transition: " + current_state.status + " -> " + next_status)
    end

    return Ok(WorkflowState(
      status=next_status,
      data=current_state.data,
      error=current_state.error
    ))
  end
end
```

---

## Multi-Agent Coordination

### Research → Analyze → Summarize Pipeline

```promptware
type ResearchState:
  query: String
  research_results: Option<List<String>>
  analysis: Option<String>
  summary: Option<String>
  current_step: String
end

function validate_research_state(state: ResearchState) -> Result<ResearchState, List<String>>
  do
    let errors = []

    # Query always required
    if len(state.query) == 0:
      errors = errors + ["Query cannot be empty"]
    end

    # Validate step-specific requirements
    if state.current_step == "research":
      # Starting state: no results yet
      if state.research_results is Some:
        errors = errors + ["Research results should be None in 'research' step"]
      end
    else if state.current_step == "analyze":
      # Analysis step: must have research results
      if state.research_results is None:
        errors = errors + ["Analysis step requires research results"]
      else if state.research_results is Some(results):
        if len(results) == 0:
          errors = errors + ["Research results cannot be empty"]
        end
      end
    else if state.current_step == "summarize":
      # Summary step: must have analysis
      if state.analysis is None:
        errors = errors + ["Summary step requires analysis"]
      end
    else if state.current_step == "complete":
      # Complete: must have summary
      if state.summary is None:
        errors = errors + ["Complete step requires summary"]
      end
    else:
      errors = errors + ["Unknown step: " + state.current_step]
    end

    if len(errors) > 0:
      return Err(errors)
    end

    return Ok(state)
  end
end
```

---

## Field-Level Validation

### Validate Individual Fields

```promptware
function validate_messages(messages: List<String>) -> Result<List<String>, String>
  do
    if len(messages) == 0:
      return Ok(messages)  # Empty is valid
    end

    # Check each message
    for msg in messages:
      if len(msg) == 0:
        return Err("Message cannot be empty")
      end

      if len(msg) > 10000:
        return Err("Message too long (max 10,000 chars)")
      end
    end

    return Ok(messages)
  end
end

function validate_agent_state_fields(state: AgentState) -> Result<AgentState, List<String>>
  do
    let errors = []

    # Validate messages
    let msg_result = validate_messages(state.messages)
    if msg_result is Err(msg):
      errors = errors + ["Messages: " + msg]
    end

    # Validate current_step
    if len(state.current_step) == 0:
      errors = errors + ["Current step cannot be empty"]
    end

    # Validate result if present
    if state.result is Some(res):
      if len(res) == 0:
        errors = errors + ["Result cannot be empty if present"]
      end
    end

    if len(errors) > 0:
      return Err(errors)
    end

    return Ok(state)
  end
end
```

---

## Real-World Example: Multi-Agent Research

**AssertLang Contract:**
```promptware
# research_workflow.al
type ResearchWorkflowState:
  topic: String
  research_results: Option<List<String>>
  analysis: Option<String>
  summary: Option<String>
  current_agent: String
  step_count: Int
end

function validate_workflow_state(
    state: ResearchWorkflowState
) -> Result<ResearchWorkflowState, List<String>>
  requires:
    state.step_count >= 0
    state.step_count <= 100
  do
    let errors = []

    # Topic always required
    if len(state.topic) == 0:
      errors = errors + ["Topic required"]
    end

    # Validate agent-specific state
    if state.current_agent == "researcher":
      if state.research_results is Some:
        errors = errors + ["Researcher should not have results yet"]
      end
    else if state.current_agent == "analyst":
      if state.research_results is None:
        errors = errors + ["Analyst requires research results"]
      end
    else if state.current_agent == "summarizer":
      if state.analysis is None:
        errors = errors + ["Summarizer requires analysis"]
      end
    end

    if len(errors) > 0:
      return Err(errors)
    end

    return Ok(state)
  end
end
```

**Generate TypedDict:**
```bash
asl build research_workflow.al --lang typeddict -o research_state.py
```

**LangGraph Integration:**
```python
# research_workflow.py
from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Optional
from research_state import ResearchWorkflowState
from research_validation import validate_workflow_state, Err

def research_node(state: ResearchWorkflowState) -> ResearchWorkflowState:
    """Research agent with contract validation."""

    # Validate input state
    result = validate_workflow_state(state)
    if isinstance(result, Err):
        raise ValueError(f"Invalid state entering research node: {result.error}")

    # Perform research
    research_results = perform_research(state["topic"])

    # Update state
    state["research_results"] = research_results
    state["current_agent"] = "analyst"
    state["step_count"] += 1

    # Validate output state
    result = validate_workflow_state(state)
    if isinstance(result, Err):
        raise ValueError(f"Invalid state leaving research node: {result.error}")

    return state

def analysis_node(state: ResearchWorkflowState) -> ResearchWorkflowState:
    """Analysis agent with contract validation."""

    result = validate_workflow_state(state)
    if isinstance(result, Err):
        raise ValueError(f"Invalid state: {result.error}")

    # Analyze research results
    analysis = analyze_results(state["research_results"])

    # Update state
    state["analysis"] = analysis
    state["current_agent"] = "summarizer"
    state["step_count"] += 1

    # Validate output
    result = validate_workflow_state(state)
    if isinstance(result, Err):
        raise ValueError(f"Invalid state: {result.error}")

    return state

def summary_node(state: ResearchWorkflowState) -> ResearchWorkflowState:
    """Summary agent with contract validation."""

    result = validate_workflow_state(state)
    if isinstance(result, Err):
        raise ValueError(f"Invalid state: {result.error}")

    # Create summary
    summary = create_summary(state["analysis"])

    # Update state
    state["summary"] = summary
    state["current_agent"] = "complete"
    state["step_count"] += 1

    return state

# Build workflow
workflow = StateGraph(ResearchWorkflowState)

workflow.add_node("research", research_node)
workflow.add_node("analyze", analysis_node)
workflow.add_node("summarize", summary_node)

workflow.set_entry_point("research")
workflow.add_edge("research", "analyze")
workflow.add_edge("analyze", "summarize")
workflow.add_edge("summarize", END)

app = workflow.compile()

# Run workflow
initial_state = {
    "topic": "Multi-agent AI frameworks",
    "research_results": None,
    "analysis": None,
    "summary": None,
    "current_agent": "researcher",
    "step_count": 0
}

final_state = app.invoke(initial_state)
print(f"Summary: {final_state['summary']}")
```

---

## Testing LangGraph State

```python
# test_langgraph_validation.py
import pytest
from research_validation import *

def test_validate_workflow_state_valid():
    state = ResearchWorkflowState(
        topic="AI Safety",
        research_results=None_(),
        analysis=None_(),
        summary=None_(),
        current_agent="researcher",
        step_count=0
    )

    result = validate_workflow_state(state)
    assert isinstance(result, Ok)

def test_validate_workflow_state_invalid_agent():
    state = ResearchWorkflowState(
        topic="AI Safety",
        research_results=None_(),
        analysis=None_(),
        summary=None_(),
        current_agent="analyst",  # Analyst needs research results!
        step_count=0
    )

    result = validate_workflow_state(state)
    assert isinstance(result, Err)
    assert any("requires research results" in err for err in result.error)

def test_state_transition():
    # Initial state
    state = ResearchWorkflowState(
        topic="AI Safety",
        research_results=None_(),
        analysis=None_(),
        summary=None_(),
        current_agent="researcher",
        step_count=0
    )

    # After research
    state["research_results"] = ["Result 1", "Result 2"]
    state["current_agent"] = "analyst"
    state["step_count"] += 1

    result = validate_workflow_state(state)
    assert isinstance(result, Ok)
```

---

## Common Pitfalls

### ❌ No State Validation

```python
# Bad: Any state shape accepted
def my_node(state: dict):
    # Crashes if 'messages' missing
    messages = state['messages']
    return state
```

### ✅ Validate State

```python
# Good: Contract enforces state shape
def my_node(state: AgentState):
    result = validate_state(state)
    if isinstance(result, Err):
        raise ValueError(f"Invalid state: {result.error}")

    # Safe to access state fields
    messages = state["messages"]
    return state
```

### ❌ Invalid Transitions Allowed

```python
# Bad: Any status change allowed
def my_node(state):
    state["status"] = "invalid"  # No validation!
    return state
```

### ✅ Validate Transitions

```promptware
# Good: Only valid transitions allowed
function transition_state(state: State, next_status: String) -> Result<State, String>
  do
    if not can_transition(state.status, next_status):
      return Err("Invalid transition")
    end

    return Ok(State(status=next_status, ...))
  end
end
```

---

## See Also

- [CrewAI Agent Contracts](crewai-agent-contracts.md) - CrewAI tool validation
- [Agent Coordination](agent-coordination.md) - Multi-agent workflows
- [State Machines](../patterns/state-machines.md) - State transition patterns
- [FastAPI Integration](../framework-integration/fastapi-endpoints.md) - API validation

---

**Difficulty:** Intermediate
**Time:** 15 minutes
**Category:** Framework Integration
**Last Updated:** 2025-10-15
