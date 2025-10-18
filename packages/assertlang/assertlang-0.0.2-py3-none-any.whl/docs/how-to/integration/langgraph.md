# How to Integrate with LangGraph

**Add contract validation to LangGraph state machines and multi-step workflows.**

---

## What You'll Learn

- Validate LangGraph state transitions
- Add contracts to graph nodes
- Ensure state consistency
- Test state machine workflows
- Handle state validation errors

**Prerequisites**:
- AssertLang installed
- LangGraph installed (`pip install langgraph`)
- Basic LangGraph knowledge

**Time**: 30 minutes

**Difficulty**: Intermediate

---

## Why Add Contracts to LangGraph?

**LangGraph challenges:**
- State can become invalid between nodes
- No validation of state transitions
- Hard to debug state corruption
- Unclear why workflows fail

**Contracts solve this:**
- ✅ Validate state before/after each node
- ✅ Ensure valid state transitions
- ✅ Catch state corruption early
- ✅ Clear error messages with context

---

## Step 1: Create State Contracts

Create `workflow_contracts.al`:

```al
// User onboarding workflow state contracts

function validate_initial_state(
    user_id: string,
    email: string,
    status: string
) -> bool {
    @requires user_id_valid: len(user_id) > 0
    @requires email_valid: "@" in email && "." in email
    @requires status_is_new: status == "new"

    @ensures validation_complete: result == true || result == false

    return true;
}

function validate_verified_state(
    user_id: string,
    email: string,
    status: string,
    verification_code: string
) -> bool {
    @requires user_id_valid: len(user_id) > 0
    @requires email_valid: "@" in email
    @requires status_verified: status == "verified"
    @requires has_code: len(verification_code) == 6

    @ensures validation_complete: result == true || result == false

    return true;
}

function validate_active_state(
    user_id: string,
    status: string,
    profile_complete: bool
) -> bool {
    @requires user_id_valid: len(user_id) > 0
    @requires status_active: status == "active"
    @requires profile_ready: profile_complete == true

    @ensures validation_complete: result == true || result == false

    return true;
}

function validate_state_transition(
    from_status: string,
    to_status: string
) -> bool {
    @requires from_valid: from_status == "new" || from_status == "verified" || from_status == "active"
    @requires to_valid: to_status == "new" || to_status == "verified" || to_status == "active"
    @requires valid_transition:
        (from_status == "new" && to_status == "verified") ||
        (from_status == "verified" && to_status == "active")

    @ensures transition_validated: result == true || result == false

    return true;
}
```

Generate Python:

```bash
asl build workflow_contracts.al -o workflow_contracts.py
```

---

## Step 2: Create LangGraph Workflow with Contracts

Create `onboarding_workflow.py`:

```python
from typing import TypedDict
from langgraph.graph import StateGraph, END
from workflow_contracts import (
    validate_initial_state,
    validate_verified_state,
    validate_active_state,
    validate_state_transition
)
from promptware.runtime.contracts import ContractViolationError


# Define state schema
class OnboardingState(TypedDict):
    user_id: str
    email: str
    status: str
    verification_code: str
    profile_complete: bool
    error: str | None


class OnboardingWorkflow:
    """User onboarding workflow with contract validation."""

    def __init__(self):
        self.graph = StateGraph(OnboardingState)

        # Add nodes
        self.graph.add_node("send_verification", self.send_verification)
        self.graph.add_node("verify_email", self.verify_email)
        self.graph.add_node("complete_profile", self.complete_profile)

        # Add edges
        self.graph.set_entry_point("send_verification")
        self.graph.add_edge("send_verification", "verify_email")
        self.graph.add_edge("verify_email", "complete_profile")
        self.graph.add_edge("complete_profile", END)

        self.app = self.graph.compile()

    def send_verification(self, state: OnboardingState) -> OnboardingState:
        """Send verification email (node 1)."""
        print(f"📧 Sending verification to {state['email']}...")

        # Validate state before processing
        try:
            validate_initial_state(
                user_id=state["user_id"],
                email=state["email"],
                status=state["status"]
            )
        except ContractViolationError as e:
            return {
                **state,
                "error": f"Invalid initial state: {e.clause}"
            }

        # Send verification (simulated)
        import random
        verification_code = str(random.randint(100000, 999999))

        # Prepare next state
        next_state = {
            **state,
            "verification_code": verification_code,
            "status": "verification_sent"
        }

        return next_state

    def verify_email(self, state: OnboardingState) -> OnboardingState:
        """Verify email address (node 2)."""
        print(f"✓ Verifying email for {state['user_id']}...")

        # Validate state transition
        try:
            validate_state_transition(
                from_status="new",
                to_status="verified"
            )
        except ContractViolationError as e:
            return {
                **state,
                "error": f"Invalid state transition: {e.clause}"
            }

        # Verify email (simulated)
        next_state = {
            **state,
            "status": "verified"
        }

        # Validate output state
        try:
            validate_verified_state(
                user_id=next_state["user_id"],
                email=next_state["email"],
                status=next_state["status"],
                verification_code=next_state["verification_code"]
            )
        except ContractViolationError as e:
            return {
                **state,
                "error": f"Invalid verified state: {e.clause}"
            }

        return next_state

    def complete_profile(self, state: OnboardingState) -> OnboardingState:
        """Complete user profile (node 3)."""
        print(f"👤 Completing profile for {state['user_id']}...")

        # Validate state transition
        try:
            validate_state_transition(
                from_status="verified",
                to_status="active"
            )
        except ContractViolationError as e:
            return {
                **state,
                "error": f"Invalid state transition: {e.clause}"
            }

        # Complete profile (simulated)
        next_state = {
            **state,
            "status": "active",
            "profile_complete": True
        }

        # Validate final state
        try:
            validate_active_state(
                user_id=next_state["user_id"],
                status=next_state["status"],
                profile_complete=next_state["profile_complete"]
            )
        except ContractViolationError as e:
            return {
                **state,
                "error": f"Invalid active state: {e.clause}"
            }

        print(f"✓ Onboarding complete for {next_state['user_id']}")
        return next_state

    def run(self, user_id: str, email: str) -> OnboardingState:
        """
        Execute onboarding workflow.

        Args:
            user_id: Unique user ID
            email: User email address

        Returns:
            Final state after workflow completion
        """
        initial_state: OnboardingState = {
            "user_id": user_id,
            "email": email,
            "status": "new",
            "verification_code": "",
            "profile_complete": False,
            "error": None
        }

        # Execute workflow
        final_state = self.app.invoke(initial_state)

        return final_state


# Usage
if __name__ == "__main__":
    workflow = OnboardingWorkflow()

    # ✓ Valid workflow
    result = workflow.run(
        user_id="user123",
        email="alice@example.com"
    )

    if result["error"]:
        print(f"✗ Workflow failed: {result['error']}")
    else:
        print(f"✓ Workflow completed: {result['status']}")

    # ✗ Invalid email
    result = workflow.run(
        user_id="user456",
        email="invalid-email"  # No @ or .
    )

    if result["error"]:
        print(f"✗ Workflow failed: {result['error']}")
```

---

## Step 3: Add Conditional State Validation

Create `conditional_workflow.py`:

```python
from typing import TypedDict
from langgraph.graph import StateGraph, END
from workflow_contracts import validate_state_transition
from promptware.runtime.contracts import ContractViolationError


class PaymentState(TypedDict):
    order_id: str
    amount: float
    status: str
    payment_method: str
    error: str | None


def validate_payment_state(state: PaymentState) -> PaymentState:
    """Validate payment state with contracts."""
    # Status-specific validation
    if state["status"] == "pending":
        if state["amount"] <= 0:
            state["error"] = "Invalid amount for pending payment"

    elif state["status"] == "processing":
        if not state["payment_method"]:
            state["error"] = "Payment method required for processing"

    elif state["status"] == "completed":
        if state["amount"] <= 0:
            state["error"] = "Completed payment must have positive amount"

    return state


class PaymentWorkflow:
    """Payment workflow with conditional validation."""

    def __init__(self):
        self.graph = StateGraph(PaymentState)

        # Add nodes
        self.graph.add_node("initiate", self.initiate_payment)
        self.graph.add_node("process", self.process_payment)
        self.graph.add_node("complete", self.complete_payment)
        self.graph.add_node("validate", validate_payment_state)

        # Add edges with validation checkpoints
        self.graph.set_entry_point("initiate")
        self.graph.add_edge("initiate", "validate")
        self.graph.add_conditional_edges(
            "validate",
            lambda s: "error" if s.get("error") else "continue",
            {
                "error": END,
                "continue": "process"
            }
        )
        self.graph.add_edge("process", "validate")
        self.graph.add_edge("complete", END)

        self.app = self.graph.compile()

    def initiate_payment(self, state: PaymentState) -> PaymentState:
        """Initiate payment."""
        return {**state, "status": "pending"}

    def process_payment(self, state: PaymentState) -> PaymentState:
        """Process payment."""
        return {**state, "status": "processing"}

    def complete_payment(self, state: PaymentState) -> PaymentState:
        """Complete payment."""
        return {**state, "status": "completed"}
```

---

## Step 4: Test State Machine Workflows

Create `test_onboarding.py`:

```python
import pytest
from onboarding_workflow import OnboardingWorkflow, OnboardingState


class TestOnboardingWorkflow:
    """Test onboarding workflow with contracts."""

    def test_valid_workflow(self):
        """Test complete workflow with valid inputs."""
        workflow = OnboardingWorkflow()
        result = workflow.run(
            user_id="test123",
            email="test@example.com"
        )

        assert result["status"] == "active"
        assert result["profile_complete"] is True
        assert result["error"] is None

    def test_invalid_email(self):
        """Test workflow rejects invalid email."""
        workflow = OnboardingWorkflow()
        result = workflow.run(
            user_id="test123",
            email="invalid-email"  # No @ or .
        )

        assert result["error"] is not None
        assert "email_valid" in result["error"]

    def test_empty_user_id(self):
        """Test workflow rejects empty user ID."""
        workflow = OnboardingWorkflow()
        result = workflow.run(
            user_id="",
            email="test@example.com"
        )

        assert result["error"] is not None
        assert "user_id_valid" in result["error"]

    def test_state_transitions(self):
        """Test state transitions are validated."""
        workflow = OnboardingWorkflow()

        # Valid transition: new → verified → active
        initial: OnboardingState = {
            "user_id": "test123",
            "email": "test@example.com",
            "status": "new",
            "verification_code": "",
            "profile_complete": False,
            "error": None
        }

        # Execute workflow step by step
        state1 = workflow.send_verification(initial)
        assert state1["status"] == "verification_sent"

        state2 = workflow.verify_email(state1)
        assert state2["status"] == "verified"

        state3 = workflow.complete_profile(state2)
        assert state3["status"] == "active"
```

---

## Integration Patterns

### Pattern 1: State Validation Middleware

**Validate state before/after every node:**

```python
def with_validation(node_fn):
    """Decorator to add state validation to nodes."""
    def wrapper(state):
        # Validate input state
        validate_state(state)

        # Execute node
        next_state = node_fn(state)

        # Validate output state
        validate_state(next_state)

        return next_state
    return wrapper


@with_validation
def my_node(state):
    return {**state, "processed": True}
```

---

### Pattern 2: Transition Guards

**Validate state transitions with guards:**

```python
def can_transition(from_status: str, to_status: str) -> bool:
    """Check if state transition is valid."""
    try:
        validate_state_transition(from_status, to_status)
        return True
    except ContractViolationError:
        return False


# Use in conditional edges
graph.add_conditional_edges(
    "current_node",
    lambda s: "next" if can_transition(s["old_status"], s["new_status"]) else "error",
    {
        "next": "next_node",
        "error": "error_handler"
    }
)
```

---

### Pattern 3: Checkpoint Validation

**Add validation checkpoints between stages:**

```python
graph = StateGraph(MyState)

# Add validation checkpoint
graph.add_node("validate_checkpoint", validate_state)

# Insert between stages
graph.add_edge("stage_1", "validate_checkpoint")
graph.add_edge("validate_checkpoint", "stage_2")
```

---

## Advanced: State Invariants

Create `state_invariants.al`:

```al
class WorkflowState {
    user_id: string
    status: string
    steps_completed: int
    total_steps: int

    @invariant user_id_valid: len(this.user_id) > 0
    @invariant valid_status: this.status == "new" || this.status == "in_progress" || this.status == "completed"
    @invariant progress_valid: this.steps_completed >= 0 && this.steps_completed <= this.total_steps
    @invariant completed_means_done: this.status != "completed" || this.steps_completed == this.total_steps

    function advance_step() -> bool {
        @requires not_completed: this.status != "completed"
        @requires steps_remaining: this.steps_completed < this.total_steps

        @ensures step_increased: this.steps_completed == old(this.steps_completed) + 1

        this.steps_completed = this.steps_completed + 1;

        if (this.steps_completed == this.total_steps) {
            this.status = "completed";
        } else {
            this.status = "in_progress";
        }

        return true;
    }
}
```

---

## What You Learned

✅ **Validate LangGraph state** - Check state at each node
✅ **State transitions** - Ensure valid transitions between statuses
✅ **Conditional validation** - Validate based on state conditions
✅ **Test workflows** - Verify state machine behavior
✅ **State invariants** - Maintain consistency throughout workflow

---

## Next Steps

**Advanced workflows**:
- [Cookbook: State Machines](../../cookbook/patterns/state-machines.md)
- [How-To: Integrate with CrewAI](crewai.md)

**Learn more**:
- [Contract Syntax](../../reference/contract-syntax.md)
- [Runtime API](../../reference/runtime-api.md)

---

## See Also

- **[CrewAI Integration](crewai.md)** - Multi-agent validation
- **[State Machines Recipe](../../cookbook/patterns/state-machines.md)** - State patterns
- **[Testing Contracts](../getting-started/testing-contracts.md)** - Test workflows

---

**[← CrewAI Integration](crewai.md)** | **[How-To Index →](../index.md)**
