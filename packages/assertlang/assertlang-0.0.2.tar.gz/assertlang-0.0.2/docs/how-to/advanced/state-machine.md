# How-To: Build a State Machine

**Implement validated state machines for workflows, agents, and complex systems.**

---

## Overview

**What you'll learn:**
- Model state machines with PW contracts
- Validate state transitions
- Enforce state invariants
- Implement terminal states
- Use with LangGraph and agent frameworks

**Time:** 45 minutes
**Difficulty:** Advanced
**Prerequisites:** [Handle Complex Types](complex-types.md), [Use Pattern Matching](pattern-matching.md)

---

## The Problem

Multi-agent systems and workflows often involve complex state transitions:
- Order processing (pending → confirmed → shipped → delivered)
- Game states (menu → playing → paused → game_over)
- Workflow execution (idle → running → completed → failed)

**Challenges:**
1. **Invalid transitions** - Moving from "delivered" back to "pending"
2. **Missing validation** - No checks before state changes
3. **State corruption** - States with invalid data (negative quantities, etc.)
4. **Unclear terminal states** - When is workflow complete?

---

## The Solution

Use PW contracts to model state machines with guaranteed valid transitions:

```promptware
# State definition
enum OrderState:
  Pending
  Confirmed
  Shipped
  Delivered
  Cancelled
end

# Transition validation
function confirm_order(state: OrderState) -> OrderState
  requires:
    state == OrderState.Pending
  ensures:
    result == OrderState.Confirmed
  do
    return OrderState.Confirmed
  end
end
```

Contracts ensure:
- Only valid transitions allowed
- State data always valid
- Terminal states respected
- Invariants maintained

---

## Step 1: Define States

### Simple Enum States

```promptware
enum TrafficLight:
  Red
  Yellow
  Green
end

function next_light(current: TrafficLight) -> TrafficLight
  do
    return match current:
      case TrafficLight.Red: TrafficLight.Green
      case TrafficLight.Green: TrafficLight.Yellow
      case TrafficLight.Yellow: TrafficLight.Red
    end
  end
end
```

### States with Data

```promptware
type WorkflowState:
  status: String
  progress: Float
  errors: List<String>
  metadata: Map<String, String>
end

function create_workflow() -> WorkflowState
  ensures:
    result.status == "idle"
    result.progress == 0.0
    len(result.errors) == 0
  do
    return WorkflowState(
      status="idle",
      progress=0.0,
      errors=[],
      metadata={}
    )
  end
end
```

### Complex State Types

```promptware
type OrderData:
  order_id: String
  items: List<String>
  total: Float
end

type OrderStateMachine:
  state: OrderState
  data: OrderData
  timestamp: String
end
```

---

## Step 2: Validate Transitions

### Basic Transition Validation

```promptware
enum GameState:
  Menu
  Playing
  Paused
  GameOver
end

function start_game(state: GameState) -> GameState
  requires:
    state == GameState.Menu
  ensures:
    result == GameState.Playing
  do
    return GameState.Playing
  end
end

function pause_game(state: GameState) -> GameState
  requires:
    state == GameState.Playing
  ensures:
    result == GameState.Paused
  do
    return GameState.Paused
  end
end

function resume_game(state: GameState) -> GameState
  requires:
    state == GameState.Paused
  ensures:
    result == GameState.Playing
  do
    return GameState.Playing
  end
end

function end_game(state: GameState) -> GameState
  requires:
    state == GameState.Playing or state == GameState.Paused
  ensures:
    result == GameState.GameOver
  do
    return GameState.GameOver
  end
end
```

**Key points:**
- `requires:` validates current state before transition
- `ensures:` guarantees new state after transition
- Contracts prevent invalid transitions (e.g., Menu → Paused)

### Transition with Data Validation

```promptware
type Order:
  state: String
  items: List<String>
  total: Float
  paid: Bool
end

function confirm_order(order: Order) -> Order
  requires:
    order.state == "pending"
    len(order.items) > 0
    order.total > 0.0
  ensures:
    result.state == "confirmed"
    result.items == order.items
    result.total == order.total
  do
    return Order(
      state="confirmed",
      items=order.items,
      total=order.total,
      paid=order.paid
    )
  end
end

function ship_order(order: Order) -> Order
  requires:
    order.state == "confirmed"
    order.paid == true
  ensures:
    result.state == "shipped"
  do
    return Order(
      state="shipped",
      items=order.items,
      total=order.total,
      paid=order.paid
    )
  end
end
```

---

## Step 3: State Invariants

### Enforce Invariants Across All States

```promptware
type WorkflowState:
  status: String
  progress: Float
  completed_steps: List<String>
  total_steps: Int
end

function validate_workflow_state(state: WorkflowState) -> Bool
  # Invariants that must always hold
  do
    return (
      state.progress >= 0.0 and
      state.progress <= 100.0 and
      len(state.completed_steps) <= state.total_steps and
      state.total_steps > 0
    )
  end
end

function advance_workflow(state: WorkflowState, step: String) -> WorkflowState
  requires:
    validate_workflow_state(state)
    state.status == "running"
    not (step in state.completed_steps)
  ensures:
    validate_workflow_state(result)
    step in result.completed_steps
    result.progress >= state.progress
  do
    new_completed = state.completed_steps + [step]
    new_progress = (len(new_completed) * 100.0) / state.total_steps

    return WorkflowState(
      status=state.status,
      progress=new_progress,
      completed_steps=new_completed,
      total_steps=state.total_steps
    )
  end
end
```

**Invariants:**
- `progress` always between 0.0 and 100.0
- `completed_steps` never exceeds `total_steps`
- `total_steps` always positive
- Checked in preconditions and postconditions

---

## Step 4: Terminal States

### Detecting Terminal States

```promptware
enum ProcessState:
  Pending
  Running
  Completed
  Failed
end

function is_terminal_state(state: ProcessState) -> Bool
  do
    return match state:
      case ProcessState.Completed: true
      case ProcessState.Failed: true
      case _: false
    end
  end
end

function transition(state: ProcessState, event: String) -> ProcessState
  requires:
    not is_terminal_state(state)  # Can't transition from terminal states
  do
    return match (state, event):
      case (ProcessState.Pending, "start"): ProcessState.Running
      case (ProcessState.Running, "complete"): ProcessState.Completed
      case (ProcessState.Running, "fail"): ProcessState.Failed
      case _: state  # No transition
    end
  end
end
```

### Preventing Transitions from Terminal States

```promptware
type TaskState:
  status: String
  result: Option<String>
  error: Option<String>
end

function is_terminal(task: TaskState) -> Bool
  do
    return task.status == "completed" or task.status == "failed"
  end
end

function complete_task(task: TaskState, result: String) -> TaskState
  requires:
    not is_terminal(task)
    task.status == "running"
    len(result) > 0
  ensures:
    is_terminal(result)
    result.status == "completed"
  do
    return TaskState(
      status="completed",
      result=Some(result),
      error=None
    )
  end
end

function fail_task(task: TaskState, error: String) -> TaskState
  requires:
    not is_terminal(task)
    len(error) > 0
  ensures:
    is_terminal(result)
    result.status == "failed"
  do
    return TaskState(
      status="failed",
      result=None,
      error=Some(error)
    )
  end
end
```

---

## Step 5: Real-World Example - Order Processing

### Complete State Machine

```promptware
# State definition
enum OrderStatus:
  Draft
  Pending
  Confirmed
  Processing
  Shipped
  Delivered
  Cancelled
  Refunded
end

# Order data
type Order:
  id: String
  status: OrderStatus
  items: List<String>
  total: Float
  paid: Bool
  shipped_at: Option<String>
  delivered_at: Option<String>
end

# Terminal states
function is_terminal_order(order: Order) -> Bool
  do
    return match order.status:
      case OrderStatus.Delivered: true
      case OrderStatus.Cancelled: true
      case OrderStatus.Refunded: true
      case _: false
    end
  end
end

# State transitions
function submit_order(order: Order) -> Order
  requires:
    order.status == OrderStatus.Draft
    len(order.items) > 0
    order.total > 0.0
  ensures:
    result.status == OrderStatus.Pending
  do
    return Order(
      id=order.id,
      status=OrderStatus.Pending,
      items=order.items,
      total=order.total,
      paid=false,
      shipped_at=None,
      delivered_at=None
    )
  end
end

function confirm_order(order: Order) -> Order
  requires:
    order.status == OrderStatus.Pending
  ensures:
    result.status == OrderStatus.Confirmed
  do
    return Order(
      id=order.id,
      status=OrderStatus.Confirmed,
      items=order.items,
      total=order.total,
      paid=order.paid,
      shipped_at=order.shipped_at,
      delivered_at=order.delivered_at
    )
  end
end

function process_payment(order: Order) -> Order
  requires:
    order.status == OrderStatus.Confirmed
    not order.paid
  ensures:
    result.status == OrderStatus.Processing
    result.paid == true
  do
    return Order(
      id=order.id,
      status=OrderStatus.Processing,
      items=order.items,
      total=order.total,
      paid=true,
      shipped_at=order.shipped_at,
      delivered_at=order.delivered_at
    )
  end
end

function ship_order(order: Order, timestamp: String) -> Order
  requires:
    order.status == OrderStatus.Processing
    order.paid == true
    len(timestamp) > 0
  ensures:
    result.status == OrderStatus.Shipped
    result.shipped_at != None
  do
    return Order(
      id=order.id,
      status=OrderStatus.Shipped,
      items=order.items,
      total=order.total,
      paid=true,
      shipped_at=Some(timestamp),
      delivered_at=None
    )
  end
end

function deliver_order(order: Order, timestamp: String) -> Order
  requires:
    order.status == OrderStatus.Shipped
    order.shipped_at != None
    len(timestamp) > 0
  ensures:
    result.status == OrderStatus.Delivered
    result.delivered_at != None
    is_terminal_order(result)
  do
    return Order(
      id=order.id,
      status=OrderStatus.Delivered,
      items=order.items,
      total=order.total,
      paid=true,
      shipped_at=order.shipped_at,
      delivered_at=Some(timestamp)
    )
  end
end

function cancel_order(order: Order) -> Order
  requires:
    not is_terminal_order(order)
    order.status != OrderStatus.Shipped  # Can't cancel after shipping
  ensures:
    result.status == OrderStatus.Cancelled
    is_terminal_order(result)
  do
    return Order(
      id=order.id,
      status=OrderStatus.Cancelled,
      items=order.items,
      total=order.total,
      paid=order.paid,
      shipped_at=order.shipped_at,
      delivered_at=order.delivered_at
    )
  end
end

function refund_order(order: Order) -> Order
  requires:
    order.status == OrderStatus.Delivered
    order.paid == true
  ensures:
    result.status == OrderStatus.Refunded
    is_terminal_order(result)
  do
    return Order(
      id=order.id,
      status=OrderStatus.Refunded,
      items=order.items,
      total=order.total,
      paid=false,
      shipped_at=order.shipped_at,
      delivered_at=order.delivered_at
    )
  end
end
```

### State Transition Diagram

```
Draft → submit_order() → Pending
                            ↓ confirm_order()
                          Confirmed
                            ↓ process_payment()
                          Processing
                            ↓ ship_order()
                          Shipped
                            ↓ deliver_order()
                          Delivered ← Terminal
                            ↓ refund_order()
                          Refunded ← Terminal

Cancel branch:
Draft/Pending/Confirmed/Processing → cancel_order() → Cancelled ← Terminal
```

---

## Step 6: Integration with LangGraph

### Define State for LangGraph

```promptware
# workflow_state.al
type AgentWorkflowState:
  current_step: String
  completed_steps: List<String>
  data: Map<String, String>
  errors: List<String>
  is_complete: Bool
end

function init_workflow() -> AgentWorkflowState
  ensures:
    result.current_step == "start"
    len(result.completed_steps) == 0
    result.is_complete == false
  do
    return AgentWorkflowState(
      current_step="start",
      completed_steps=[],
      data={},
      errors=[],
      is_complete=false
    )
  end
end

function transition_to_step(
    state: AgentWorkflowState,
    next_step: String
) -> AgentWorkflowState
  requires:
    not state.is_complete
    not (next_step in state.completed_steps)
    len(next_step) > 0
  ensures:
    result.current_step == next_step
    state.current_step in result.completed_steps
  do
    return AgentWorkflowState(
      current_step=next_step,
      completed_steps=state.completed_steps + [state.current_step],
      data=state.data,
      errors=state.errors,
      is_complete=false
    )
  end
end

function complete_workflow(state: AgentWorkflowState) -> AgentWorkflowState
  requires:
    not state.is_complete
  ensures:
    result.is_complete == true
    state.current_step in result.completed_steps
  do
    return AgentWorkflowState(
      current_step=state.current_step,
      completed_steps=state.completed_steps + [state.current_step],
      data=state.data,
      errors=state.errors,
      is_complete=true
    )
  end
end
```

### Generate TypedDict for LangGraph

```bash
asl build workflow_state.al --lang typeddict -o workflow_state.py
```

### Use in LangGraph

```python
# workflow.py
from langgraph.graph import StateGraph, END
from workflow_state import AgentWorkflowState
from workflow_state_contracts import (
    init_workflow,
    transition_to_step,
    complete_workflow
)

# Initialize workflow
def start_node(state: AgentWorkflowState) -> AgentWorkflowState:
    """Contracts validate initial state."""
    if not state:
        return init_workflow()
    return state

# Validated transitions
def process_node(state: AgentWorkflowState) -> AgentWorkflowState:
    """Contract ensures valid transition."""
    return transition_to_step(state, "processing")

def review_node(state: AgentWorkflowState) -> AgentWorkflowState:
    """Contract ensures valid transition."""
    return transition_to_step(state, "review")

def finish_node(state: AgentWorkflowState) -> AgentWorkflowState:
    """Contract marks workflow complete."""
    return complete_workflow(state)

# Build graph
workflow = StateGraph(AgentWorkflowState)
workflow.add_node("start", start_node)
workflow.add_node("process", process_node)
workflow.add_node("review", review_node)
workflow.add_node("finish", finish_node)

workflow.set_entry_point("start")
workflow.add_edge("start", "process")
workflow.add_edge("process", "review")
workflow.add_edge("review", "finish")
workflow.add_edge("finish", END)

app = workflow.compile()

# Execute with validated state transitions
result = app.invoke({})
print(f"Final state: {result}")
print(f"Completed: {result['is_complete']}")  # Guaranteed true by contract
```

---

## Step 7: Testing State Machines

### Test Valid Transitions

```python
# Python (pytest)
import pytest
from order_state_machine import (
    Order, OrderStatus,
    submit_order, confirm_order, ship_order
)

def test_valid_order_flow():
    # Create draft order
    order = Order(
        id="ORD-123",
        status=OrderStatus.Draft,
        items=["item1", "item2"],
        total=99.99,
        paid=False,
        shipped_at=None,
        delivered_at=None
    )

    # Submit (Draft → Pending)
    order = submit_order(order)
    assert order.status == OrderStatus.Pending

    # Confirm (Pending → Confirmed)
    order = confirm_order(order)
    assert order.status == OrderStatus.Confirmed

    # ... continue through workflow
```

### Test Invalid Transitions

```python
def test_invalid_transitions():
    order = Order(
        id="ORD-123",
        status=OrderStatus.Pending,
        items=["item1"],
        total=50.0,
        paid=False,
        shipped_at=None,
        delivered_at=None
    )

    # Can't ship from Pending (must be Processing)
    with pytest.raises(ContractViolation) as exc:
        ship_order(order, "2025-10-15T10:00:00Z")

    assert "requires" in str(exc.value)
    assert "order.status == OrderStatus.Processing" in str(exc.value)
```

### Test Terminal States

```python
def test_terminal_states():
    # Delivered order (terminal)
    delivered = Order(
        id="ORD-123",
        status=OrderStatus.Delivered,
        items=["item1"],
        total=50.0,
        paid=True,
        shipped_at=Some("2025-10-14T10:00:00Z"),
        delivered_at=Some("2025-10-15T10:00:00Z")
    )

    # Can't transition from terminal states
    with pytest.raises(ContractViolation):
        ship_order(delivered, "2025-10-16T10:00:00Z")
```

---

## Best Practices

### 1. Define Clear States

Use enums for discrete states:
```promptware
enum Status:
  Idle
  Running
  Completed
  Failed
end
```

### 2. Validate All Transitions

Every transition should have:
- **Precondition** - Valid starting state(s)
- **Postcondition** - Guaranteed ending state

### 3. Use Immutable State Updates

Return new state, don't mutate:
```promptware
function update_state(state: State) -> State
  # Return NEW state, don't modify input
  do
    return State(status="new", data=state.data)
  end
end
```

### 4. Document State Diagrams

Include state transition diagram in comments:
```promptware
# State Machine: Order Processing
#
#   Draft → Pending → Confirmed → Processing → Shipped → Delivered
#                                      ↓
#                                  Cancelled
```

### 5. Test Boundary Cases

Test all edges in state graph:
- Valid transitions
- Invalid transitions
- Terminal states
- Edge cases (empty data, null values)

---

## Summary

**State machine with PW contracts:**
- **Define states** - Enums or types with state data
- **Validate transitions** - requires/ensures contracts
- **Enforce invariants** - Conditions that always hold
- **Terminal states** - Prevent transitions after completion
- **Integration** - LangGraph, agents, workflows

**Benefits:**
- Guaranteed valid transitions
- State corruption impossible
- Clear terminal states
- Easy testing
- Multi-language (Python, JS, Go, etc.)

---

## Next Steps

- **[Use Pattern Matching](pattern-matching.md)** - Pattern match on states
- **[Handle Complex Types](complex-types.md)** - Option/Result for state data
- **[Integrate with LangGraph](../../integration/langgraph.md)** - Complete LangGraph integration
- **[Monitor Contract Violations](../../deployment/monitoring.md)** - Track state violations

---

## See Also

- **[Cookbook: State Machines](../../../cookbook/patterns/state-machines.md)** - More state machine patterns
- **[API Reference: Pattern Matching](../../../reference/contract-syntax.md#pattern-matching)** - Match syntax
- **[Example: Order Processing](../../../examples/real_world/)** - Full order processing system

---

**Difficulty:** Advanced
**Time:** 45 minutes
**Last Updated:** 2025-10-15
