"""
Promptware Contract Runtime Validation

This module provides runtime enforcement of Design-by-Contract assertions:
- Preconditions (@requires) - Checked at function entry
- Postconditions (@ensures) - Checked at function exit
- Invariants (@invariant) - Checked after public methods
- Old value capture (old keyword) - Captures pre-state for postconditions

Design Principles:
1. Helpful error messages - Include clause name, expression, context
2. Validation modes - Development (full), production (optimized), test (coverage)
3. Performance - Minimal overhead, optional disabling
4. Framework-agnostic - No dependencies on specific frameworks
"""

from enum import Enum
from typing import Any, Dict, Optional


class ValidationMode(Enum):
    """Contract validation modes."""

    DISABLED = "disabled"              # No contract checking (production)
    PRECONDITIONS_ONLY = "preconditions"  # Only check preconditions (production with validation)
    FULL = "full"                     # Check all contracts (development/testing)


# Global validation mode
_VALIDATION_MODE = ValidationMode.FULL

# Global coverage tracking
_CLAUSE_COVERAGE: Dict[str, int] = {}


def set_validation_mode(mode: ValidationMode) -> None:
    """
    Set global contract validation mode.

    Args:
        mode: Validation mode to enable

    Example:
        # Production mode (preconditions only)
        set_validation_mode(ValidationMode.PRECONDITIONS_ONLY)

        # Development mode (all checks)
        set_validation_mode(ValidationMode.FULL)

        # Performance mode (no checks)
        set_validation_mode(ValidationMode.DISABLED)
    """
    global _VALIDATION_MODE
    _VALIDATION_MODE = mode


def get_validation_mode() -> ValidationMode:
    """Get current validation mode."""
    return _VALIDATION_MODE


def should_check_preconditions() -> bool:
    """Check if preconditions should be validated."""
    return _VALIDATION_MODE in [ValidationMode.PRECONDITIONS_ONLY, ValidationMode.FULL]


def should_check_postconditions() -> bool:
    """Check if postconditions should be validated."""
    return _VALIDATION_MODE == ValidationMode.FULL


def should_check_invariants() -> bool:
    """Check if invariants should be validated."""
    return _VALIDATION_MODE == ValidationMode.FULL


class ContractViolationError(Exception):
    """
    Raised when a contract clause is violated.

    Provides detailed error information for debugging:
    - Type of violation (precondition, postcondition, invariant)
    - Clause name and expression
    - Function/class location
    - Variable values at time of violation
    """

    def __init__(
        self,
        type: str,                      # "precondition", "postcondition", or "invariant"
        clause: str,                    # Clause name (e.g., "name_not_empty")
        expression: str,                # Expression string (e.g., "len(name) >= 1")
        message: str,                   # Human-readable message
        function: Optional[str] = None, # Function name
        class_name: Optional[str] = None,  # Class name
        location: Optional[str] = None, # Source location (file:line)
        context: Optional[Dict[str, Any]] = None  # Variable values
    ):
        self.type = type
        self.clause = clause
        self.expression = expression
        self.message = message
        self.function = function
        self.class_name = class_name
        self.location = location
        self.context = context or {}

        super().__init__(self._format_message())

    def _format_message(self) -> str:
        """
        Format helpful error message.

        Returns:
            Multi-line error message with all context

        Example:
            Contract Violation: Precondition
              Function: UserService.createUser
              Clause: 'name_not_empty'
              Expression: len(name) >= 1
              Context:
                name = ""
                len(name) = 0
        """
        parts = []

        # Header
        parts.append(f"Contract Violation: {self.type.title()}")

        # Location
        if self.function:
            if self.class_name:
                parts.append(f"  Function: {self.class_name}.{self.function}")
            else:
                parts.append(f"  Function: {self.function}")
        elif self.class_name:
            parts.append(f"  Class: {self.class_name}")

        if self.location:
            parts.append(f"  Location: {self.location}")

        # Clause details
        parts.append(f"  Clause: '{self.clause}'")
        parts.append(f"  Expression: {self.expression}")

        # Message
        if self.message:
            parts.append(f"  Message: {self.message}")

        # Context (if available)
        if self.context:
            parts.append("  Context:")
            for key, value in self.context.items():
                parts.append(f"    {key} = {repr(value)}")

        return "\n".join(parts)


class OldValue:
    """
    Container for capturing 'old' values in postconditions.

    Captures the value of an expression before function execution,
    allowing postconditions to reference pre-state.

    Example:
        # Before function execution
        old_balance = OldValue(account.balance)

        # After function execution, in postcondition
        assert account.balance == old_balance.value + amount
    """

    def __init__(self, value: Any):
        self.value = value

    def __repr__(self) -> str:
        return f"OldValue({repr(self.value)})"


def capture_old_values(old_expressions: Dict[str, Any]) -> Dict[str, OldValue]:
    """
    Capture values for 'old' expressions before function execution.

    Args:
        old_expressions: Dict mapping variable names to current values

    Returns:
        Dict mapping variable names to OldValue containers

    Example:
        # Capture old values
        old_values = capture_old_values({
            'balance': account.balance,
            'count': len(items)
        })

        # Later, reference in postcondition
        assert account.balance == old_values['balance'].value + amount
    """
    return {name: OldValue(value) for name, value in old_expressions.items()}


# ============================================================================
# Helper Functions for Generated Code
# ============================================================================


def check_precondition(
    condition: bool,
    clause_name: str,
    expression: str,
    function_name: str,
    class_name: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None
) -> None:
    """
    Check a precondition assertion.

    Called by generated code at function entry.

    Args:
        condition: Result of evaluating the precondition expression
        clause_name: Name of the clause (for error reporting)
        expression: String representation of the expression
        function_name: Name of the function
        class_name: Name of the class (if method)
        context: Variable values for error reporting

    Raises:
        ContractViolationError: If condition is False

    Example:
        check_precondition(
            len(name) >= 1,
            "name_not_empty",
            "len(name) >= 1",
            "createUser",
            context={"name": name, "len(name)": len(name)}
        )
    """
    if not should_check_preconditions():
        return

    # Track coverage
    full_name = f"{class_name}.{function_name}" if class_name else function_name
    key = f"{full_name}.requires.{clause_name}"
    _CLAUSE_COVERAGE[key] = _CLAUSE_COVERAGE.get(key, 0) + 1

    if not condition:
        raise ContractViolationError(
            type="precondition",
            clause=clause_name,
            expression=expression,
            message=f"Precondition '{clause_name}' violated",
            function=function_name,
            class_name=class_name,
            context=context
        )


def check_postcondition(
    condition: bool,
    clause_name: str,
    expression: str,
    function_name: str,
    class_name: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None
) -> None:
    """
    Check a postcondition assertion.

    Called by generated code at function exit.

    Args:
        condition: Result of evaluating the postcondition expression
        clause_name: Name of the clause (for error reporting)
        expression: String representation of the expression
        function_name: Name of the function
        class_name: Name of the class (if method)
        context: Variable values for error reporting (including 'result')

    Raises:
        ContractViolationError: If condition is False

    Example:
        check_postcondition(
            result > 0,
            "result_positive",
            "result > 0",
            "createUser",
            context={"result": result, "result.id": result.id}
        )
    """
    if not should_check_postconditions():
        return

    # Track coverage
    full_name = f"{class_name}.{function_name}" if class_name else function_name
    key = f"{full_name}.ensures.{clause_name}"
    _CLAUSE_COVERAGE[key] = _CLAUSE_COVERAGE.get(key, 0) + 1

    if not condition:
        raise ContractViolationError(
            type="postcondition",
            clause=clause_name,
            expression=expression,
            message=f"Postcondition '{clause_name}' violated",
            function=function_name,
            class_name=class_name,
            context=context
        )


def check_invariant(
    condition: bool,
    clause_name: str,
    expression: str,
    class_name: str,
    context: Optional[Dict[str, Any]] = None
) -> None:
    """
    Check a class invariant assertion.

    Called by generated code after public method execution.

    Args:
        condition: Result of evaluating the invariant expression
        clause_name: Name of the clause (for error reporting)
        expression: String representation of the expression
        class_name: Name of the class
        context: Variable values for error reporting

    Raises:
        ContractViolationError: If condition is False

    Example:
        check_invariant(
            len(self.users) >= 0,
            "user_count_positive",
            "len(self.users) >= 0",
            "UserService",
            context={"len(self.users)": len(self.users)}
        )
    """
    if not should_check_invariants():
        return

    # Track coverage
    key = f"{class_name}.invariant.{clause_name}"
    _CLAUSE_COVERAGE[key] = _CLAUSE_COVERAGE.get(key, 0) + 1

    if not condition:
        raise ContractViolationError(
            type="invariant",
            clause=clause_name,
            expression=expression,
            message=f"Invariant '{clause_name}' violated",
            class_name=class_name,
            context=context
        )


# ============================================================================
# Coverage Tracking Functions
# ============================================================================


def get_coverage() -> Dict[str, int]:
    """
    Get contract clause coverage data.

    Returns:
        Dict mapping clause keys to execution counts

    Example:
        coverage = get_coverage()
        # {"createUser.requires.name_not_empty": 5, ...}
    """
    return _CLAUSE_COVERAGE.copy()


def reset_coverage() -> None:
    """Reset contract coverage tracking."""
    global _CLAUSE_COVERAGE
    _CLAUSE_COVERAGE = {}
