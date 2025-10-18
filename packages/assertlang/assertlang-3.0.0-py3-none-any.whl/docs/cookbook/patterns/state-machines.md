# Recipe: State Machine Contracts

**Problem:** Validate state transitions to prevent invalid state changes and ensure state machine correctness.

**Difficulty:** Intermediate
**Time:** 20 minutes

---

## The Problem

State machines without contracts allow:
- **Invalid transitions**: `pending` → `shipped` (skipping `paid`)
- **Terminal state changes**: Modifying `completed` or `cancelled` states
- **Missing state**: Unknown state strings
- **Concurrent transitions**: Multiple transitions happening simultaneously
- **Lost invariants**: State-specific data requirements not enforced

---

## Solution

```al
function can_transition(
    current_state: string,
    next_state: string
) -> bool {
    @requires valid_current: is_valid_state(current_state)
    @requires valid_next: is_valid_state(next_state)

    @ensures transition_decided: result == true || result == false

    // Pending can go to: paid, cancelled
    if (current_state == "pending") {
        if (next_state == "paid" || next_state == "cancelled") {
            return true;
        }
        return false;
    }

    // Paid can go to: shipped, cancelled
    if (current_state == "paid") {
        if (next_state == "shipped" || next_state == "cancelled") {
            return true;
        }
        return false;
    }

    // Shipped can go to: delivered, cancelled
    if (current_state == "shipped") {
        if (next_state == "delivered" || next_state == "cancelled") {
            return true;
        }
        return false;
    }

    // Delivered and cancelled are terminal (no transitions)
    if (current_state == "delivered" || current_state == "cancelled") {
        return false;
    }

    return false;
}

function is_valid_state(state: string) -> bool {
    @requires non_empty: len(state) > 0

    @ensures validation_complete: result == true || result == false

    if (state == "pending" || state == "paid" || state == "shipped" ||
        state == "delivered" || state == "cancelled") {
        return true;
    }

    return false;
}

function transition_state(
    current_state: string,
    next_state: string
) -> string {
    @requires valid_transition: can_transition(current_state, next_state)

    @ensures state_changed: result == next_state
    @ensures not_same: result != current_state

    return next_state;
}
```

**Generated Python:**
```python
from promptware.runtime.contracts import check_precondition, check_postcondition

def can_transition(current_state: str, next_state: str) -> bool:
    check_precondition(is_valid_state(current_state), "valid_current")
    check_precondition(is_valid_state(next_state), "valid_next")

    if current_state == "pending":
        result = next_state in ["paid", "cancelled"]
    elif current_state == "paid":
        result = next_state in ["shipped", "cancelled"]
    elif current_state == "shipped":
        result = next_state in ["delivered", "cancelled"]
    elif current_state in ["delivered", "cancelled"]:
        result = False
    else:
        result = False

    check_postcondition(result in [True, False], "transition_decided")
    return result

def transition_state(current_state: str, next_state: str) -> str:
    check_precondition(
        can_transition(current_state, next_state),
        "valid_transition",
        f"Cannot transition from {current_state} to {next_state}"
    )

    result = next_state

    check_postcondition(result == next_state, "state_changed")
    check_postcondition(result != current_state, "not_same")
    return result
```

---

## Explanation

**Three-layer validation:**

1. **State validity** - `is_valid_state()` ensures only known states
2. **Transition rules** - `can_transition()` enforces valid transitions
3. **State change** - `transition_state()` performs validated transition

**State diagram:**
```
pending → paid → shipped → delivered (terminal)
   ↓        ↓       ↓
cancelled (terminal)
```

**Contracts prevent:**
- Skipping states (pending → shipped without paid)
- Changing terminal states (delivered → anything)
- Unknown states ("processing" not in state set)

---

## Variations

### With State Data Validation
```al
function validate_state_data(
    state: string,
    data_present: bool,
    data_valid: bool
) -> bool {
    @requires valid_state: is_valid_state(state)

    @ensures validation_complete: result == true || result == false

    // Pending requires no data
    if (state == "pending") {
        return true;
    }

    // Paid requires valid payment data
    if (state == "paid") {
        return data_present && data_valid;
    }

    // Shipped requires shipping info
    if (state == "shipped") {
        return data_present;
    }

    // Delivered requires confirmation
    if (state == "delivered") {
        return data_present && data_valid;
    }

    return true;
}
```

---

### With Entry/Exit Actions
```al
function check_entry_condition(
    target_state: string,
    precondition_met: bool
) -> bool {
    @requires valid_state: is_valid_state(target_state)

    @ensures entry_decided: result == true || result == false

    // Paid requires payment verification
    if (target_state == "paid") {
        return precondition_met;
    }

    // Shipped requires tracking number
    if (target_state == "shipped") {
        return precondition_met;
    }

    // Other states have no special requirements
    return true;
}

function check_exit_condition(
    source_state: string,
    cleanup_done: bool
) -> bool {
    @requires valid_state: is_valid_state(source_state)

    @ensures exit_decided: result == true || result == false

    // Paid requires refund handling before exit
    if (source_state == "paid") {
        return cleanup_done;
    }

    // Shipped requires notification before exit
    if (source_state == "shipped") {
        return cleanup_done;
    }

    // Other states can exit freely
    return true;
}
```

---

### With Timeout Validation
```al
function check_state_timeout(
    current_state: string,
    time_in_state: int,
    timeout_seconds: int
) -> bool {
    @requires valid_state: is_valid_state(current_state)
    @requires non_negative_time: time_in_state >= 0
    @requires positive_timeout: timeout_seconds > 0

    @ensures timeout_decided: result == true || result == false

    // Pending times out after 24 hours
    if (current_state == "pending" && timeout_seconds == 86400) {
        return time_in_state >= timeout_seconds;
    }

    // Paid times out after 7 days
    if (current_state == "paid" && timeout_seconds == 604800) {
        return time_in_state >= timeout_seconds;
    }

    return false;
}
```

---

## Common Pitfalls

### ❌ String comparison without validation
```python
if current_state == "procesing":  # Typo!
    next_state = "shipped"
```

**Problem**: Typos not caught, invalid states accepted.

**Fix**: Use `is_valid_state()` first.
```al
@requires valid_state: is_valid_state(current_state)
```

---

### ❌ Allowing backwards transitions
```al
// ❌ Bad: allows any transition
function can_transition(from: string, to: string) -> bool {
    return true;  // No validation!
}
```

**Problem**: Can transition delivered → pending (backwards).

**Fix**: Explicit transition rules per state.

---

### ❌ No terminal state protection
```python
order.state = "delivered"
# ...later...
order.state = "pending"  # ❌ Modified terminal state!
```

**Fix**: Check if current state is terminal.
```al
@requires not_terminal: current_state != "delivered" && current_state != "cancelled"
```

---

### ❌ Missing state data invariants
```python
order.state = "paid"
order.payment_info = None  # ❌ Paid without payment info!
```

**Fix**: Validate state-specific data requirements.
```al
@requires paid_has_payment: state != "paid" || (data_present && data_valid)
```

---

## Real-World Example

**Order processing state machine:**
```al
class OrderStateMachine {
    state: string
    payment_verified: bool
    tracking_number: string
    delivery_confirmed: bool

    @invariant valid_state: is_valid_state(this.state)
    @invariant paid_verified: this.state != "paid" || this.payment_verified == true
    @invariant shipped_tracked: this.state != "shipped" || len(this.tracking_number) > 0
    @invariant delivered_confirmed: this.state != "delivered" || this.delivery_confirmed == true

    function transition(next_state: string) -> bool {
        @requires valid_next: is_valid_state(next_state)
        @requires can_move: can_transition(this.state, next_state)
        @requires entry_ok: check_entry_condition(next_state, meets_preconditions())
        @requires exit_ok: check_exit_condition(this.state, cleanup_done())

        @ensures transitioned: this.state == next_state
        @ensures valid_result: result == true

        let old_state = this.state;
        this.state = next_state;

        return true;
    }

    function meets_preconditions() -> bool {
        if (this.state == "pending" && next_state == "paid") {
            return this.payment_verified;
        }
        if (this.state == "paid" && next_state == "shipped") {
            return len(this.tracking_number) > 0;
        }
        return true;
    }

    function cleanup_done() -> bool {
        // Ensure state-specific cleanup before exit
        return true;
    }
}
```

**Usage:**
```python
from order_state_machine import OrderStateMachine

order = OrderStateMachine(
    state="pending",
    payment_verified=False,
    tracking_number="",
    delivery_confirmed=False
)

# ✓ Valid transition sequence
order.payment_verified = True
order.transition("paid")  # pending → paid

order.tracking_number = "TRACK123"
order.transition("shipped")  # paid → shipped

order.delivery_confirmed = True
order.transition("delivered")  # shipped → delivered

# ❌ Invalid transitions (caught by contracts)
order.transition("pending")  # Can't leave terminal state
order.transition("unknown")  # Invalid state
```

---

## Testing Pattern

```python
import pytest
from state_machine import can_transition, transition_state, is_valid_state

def test_valid_states():
    assert is_valid_state("pending")
    assert is_valid_state("delivered")
    assert not is_valid_state("unknown")

def test_valid_transitions():
    assert can_transition("pending", "paid")
    assert can_transition("paid", "shipped")
    assert can_transition("shipped", "delivered")

def test_invalid_transitions():
    assert not can_transition("pending", "shipped")  # Skip paid
    assert not can_transition("delivered", "paid")   # Terminal state
    assert not can_transition("cancelled", "pending") # Terminal state

def test_transition_enforcement():
    # Valid
    result = transition_state("pending", "paid")
    assert result == "paid"

    # Invalid
    with pytest.raises(Exception, match="valid_transition"):
        transition_state("pending", "shipped")  # Skip paid
```

---

## Integration with LangGraph

```python
from langgraph.graph import StateGraph
from typing import TypedDict
from state_machine import can_transition, transition_state

class OrderState(TypedDict):
    current_state: str
    payment_verified: bool

graph = StateGraph(OrderState)

def payment_node(state: OrderState) -> OrderState:
    # Validate can transition to paid
    if not can_transition(state["current_state"], "paid"):
        raise ValueError("Cannot transition to paid")

    # Process payment...
    state["payment_verified"] = True

    # Transition state
    state["current_state"] = transition_state(
        state["current_state"],
        "paid"
    )
    return state

graph.add_node("payment", payment_node)
```

---

## See Also

- **[State Machine Patterns Example](../../../examples/real_world/05_state_machine_patterns/)** - Complete implementation (62 tests)
- **[E-commerce Orders Example](../../../examples/real_world/01_ecommerce_orders/)** - Order state machine
- **[LangGraph State Validation](../framework-integration/langgraph-state-validation.md)** - State graphs with contracts
- **[Builder Pattern](builder-pattern.md)** - Related pattern with state

---

**Next**: Try [LangGraph State Validation](../framework-integration/langgraph-state-validation.md) for graph-based states →
