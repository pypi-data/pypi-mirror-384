"""
Contract testing utilities for Promptware.

Provides helper functions for testing contracts:
- assert_precondition_passes/fails
- assert_postcondition_holds
- Coverage tracking
- Test case generation

Usage:
    from assertlang.testing.contracts import (
        assert_precondition_passes,
        assert_precondition_fails,
        assert_postcondition_holds
    )

    def test_createUser():
        # Test valid input
        assert_precondition_passes(createUser, "Alice", "alice@example.com")

        # Test invalid inputs
        assert_precondition_fails(createUser, "", "alice@example.com", clause="name_not_empty")
        assert_precondition_fails(createUser, "Alice", "invalid", clause="email_has_at")

        # Test postconditions
        result = assert_postcondition_holds(createUser, "Alice", "alice@example.com")
        assert result.name == "Alice"
"""

from typing import Callable, Any, Optional, Dict, List
from dataclasses import dataclass

from assertlang.runtime.contracts import (
    ContractViolationError,
    ValidationMode,
    set_validation_mode,
    get_validation_mode
)


# Global coverage tracking
_clause_coverage: Dict[str, int] = {}


@dataclass
class CoverageReport:
    """Contract clause coverage report."""
    total_clauses: int
    covered_clauses: int
    coverage_percent: float
    clause_counts: Dict[str, int]
    uncovered: List[str]


def assert_precondition_passes(func: Callable, *args, **kwargs) -> Any:
    """
    Assert that preconditions pass for given arguments.

    Args:
        func: Function to test
        *args: Positional arguments
        **kwargs: Keyword arguments

    Returns:
        Function return value

    Raises:
        AssertionError: If precondition fails unexpectedly

    Example:
        assert_precondition_passes(createUser, "Alice", "alice@example.com")
    """
    # Ensure we're checking contracts
    original_mode = get_validation_mode()
    if original_mode == ValidationMode.DISABLED:
        set_validation_mode(ValidationMode.FULL)

    try:
        result = func(*args, **kwargs)
        return result
    except ContractViolationError as e:
        if e.type == "precondition":
            raise AssertionError(
                f"Precondition '{e.clause}' failed unexpectedly: {e.message}\n"
                f"Expression: {e.expression}\n"
                f"Context: {e.context}"
            )
        # Re-raise postcondition/invariant violations
        raise
    finally:
        set_validation_mode(original_mode)


def assert_precondition_fails(
    func: Callable,
    *args,
    clause: Optional[str] = None,
    **kwargs
) -> None:
    """
    Assert that preconditions fail for given arguments.

    Args:
        func: Function to test
        *args: Positional arguments
        clause: Expected clause name (optional)
        **kwargs: Keyword arguments

    Raises:
        AssertionError: If precondition passes or wrong clause fails

    Example:
        assert_precondition_fails(createUser, "", "alice@example.com", clause="name_not_empty")
    """
    # Ensure we're checking contracts
    original_mode = get_validation_mode()
    if original_mode == ValidationMode.DISABLED:
        set_validation_mode(ValidationMode.FULL)

    try:
        result = func(*args, **kwargs)
        raise AssertionError(
            f"Expected precondition to fail, but function succeeded with result: {result}"
        )
    except ContractViolationError as e:
        if e.type != "precondition":
            raise AssertionError(
                f"Expected precondition failure, but got {e.type} violation: {e.clause}"
            )
        if clause and e.clause != clause:
            raise AssertionError(
                f"Expected clause '{clause}' to fail, but '{e.clause}' failed instead"
            )
        # Success - precondition failed as expected
    finally:
        set_validation_mode(original_mode)


def assert_postcondition_holds(func: Callable, *args, **kwargs) -> Any:
    """
    Assert that postconditions hold for given arguments.

    Args:
        func: Function to test
        *args: Positional arguments
        **kwargs: Keyword arguments

    Returns:
        Function return value

    Raises:
        AssertionError: If postcondition is violated

    Example:
        result = assert_postcondition_holds(createUser, "Alice", "alice@example.com")
        assert result.id > 0
    """
    # Ensure we're checking postconditions
    original_mode = get_validation_mode()
    if original_mode != ValidationMode.FULL:
        set_validation_mode(ValidationMode.FULL)

    try:
        result = func(*args, **kwargs)
        return result
    except ContractViolationError as e:
        if e.type == "postcondition":
            raise AssertionError(
                f"Postcondition '{e.clause}' violated: {e.message}\n"
                f"Expression: {e.expression}\n"
                f"Context: {e.context}"
            )
        # Re-raise precondition violations
        raise
    finally:
        set_validation_mode(original_mode)


def assert_invariant_holds(obj: Any, method: str, *args, **kwargs) -> Any:
    """
    Assert that class invariants hold after method execution.

    Args:
        obj: Object instance
        method: Method name to call
        *args: Positional arguments
        **kwargs: Keyword arguments

    Returns:
        Method return value

    Raises:
        AssertionError: If invariant is violated

    Example:
        service = UserService()
        assert_invariant_holds(service, "createUser", "Alice", "alice@example.com")
    """
    # Ensure we're checking invariants
    original_mode = get_validation_mode()
    if original_mode != ValidationMode.FULL:
        set_validation_mode(ValidationMode.FULL)

    try:
        method_func = getattr(obj, method)
        result = method_func(*args, **kwargs)
        return result
    except ContractViolationError as e:
        if e.type == "invariant":
            raise AssertionError(
                f"Invariant '{e.clause}' violated: {e.message}\n"
                f"Expression: {e.expression}\n"
                f"Context: {e.context}"
            )
        # Re-raise other violations
        raise
    finally:
        set_validation_mode(original_mode)


# Coverage tracking functions

def track_clause_coverage(function_name: str, clause_type: str, clause_name: str):
    """
    Track that a contract clause was exercised.

    This is called automatically by the contract runtime.

    Args:
        function_name: Name of function
        clause_type: "precondition", "postcondition", or "invariant"
        clause_name: Name of clause
    """
    key = f"{function_name}.{clause_type}.{clause_name}"
    _clause_coverage[key] = _clause_coverage.get(key, 0) + 1


def get_coverage() -> Dict[str, int]:
    """
    Get contract clause coverage data.

    Returns:
        Dict mapping clause keys to execution counts

    Example:
        coverage = get_coverage()
        # {"createUser.precondition.name_not_empty": 5, ...}
    """
    return _clause_coverage.copy()


def reset_coverage():
    """Reset contract coverage tracking."""
    global _clause_coverage
    _clause_coverage = {}


def generate_coverage_report(expected_clauses: Optional[List[str]] = None) -> CoverageReport:
    """
    Generate a coverage report for contract clauses.

    Args:
        expected_clauses: List of expected clause keys (optional)

    Returns:
        CoverageReport with coverage statistics

    Example:
        report = generate_coverage_report([
            "createUser.precondition.name_not_empty",
            "createUser.precondition.email_has_at",
            "createUser.postcondition.id_positive"
        ])
        print(f"Coverage: {report.coverage_percent:.1f}%")
    """
    covered = set(_clause_coverage.keys())

    if expected_clauses:
        expected = set(expected_clauses)
        total = len(expected)
        covered_count = len(covered & expected)
        uncovered = list(expected - covered)
    else:
        # No expected clauses provided - just report what we saw
        total = len(covered)
        covered_count = total
        uncovered = []

    coverage_percent = (covered_count / total * 100) if total > 0 else 0.0

    return CoverageReport(
        total_clauses=total,
        covered_clauses=covered_count,
        coverage_percent=coverage_percent,
        clause_counts=_clause_coverage.copy(),
        uncovered=uncovered
    )


def print_coverage_report(report: CoverageReport):
    """
    Pretty-print a coverage report.

    Args:
        report: CoverageReport to print
    """
    print("\nContract Coverage Report")
    print("=" * 60)
    print(f"Total clauses: {report.total_clauses}")
    print(f"Covered: {report.covered_clauses}")
    print(f"Coverage: {report.coverage_percent:.1f}%")
    print()

    if report.clause_counts:
        print("Clause execution counts:")
        for clause, count in sorted(report.clause_counts.items()):
            print(f"  {clause}: {count}x")
        print()

    if report.uncovered:
        print(f"⚠️  {len(report.uncovered)} uncovered clause(s):")
        for clause in sorted(report.uncovered):
            print(f"  ✗ {clause}")
    else:
        print("✓ All clauses covered!")


# Test case generation helpers

def generate_boundary_values(param_type: str) -> List[Any]:
    """
    Generate boundary test values for a parameter type.

    Args:
        param_type: Type name (int, string, etc.)

    Returns:
        List of boundary values to test

    Example:
        values = generate_boundary_values("int")
        # [0, 1, -1, sys.maxsize, -sys.maxsize]
    """
    import sys

    if param_type in ['int', 'integer']:
        return [0, 1, -1, 100, -100, sys.maxsize, -sys.maxsize]
    elif param_type in ['string', 'str']:
        return ["", "a", "test", "x" * 100, "x" * 1000]
    elif param_type in ['bool', 'boolean']:
        return [True, False]
    elif param_type in ['float', 'double']:
        return [0.0, 1.0, -1.0, 0.1, 100.5, -100.5, float('inf'), float('-inf')]
    elif param_type in ['list', 'array']:
        return [[], [1], [1, 2, 3], list(range(100))]
    else:
        return [None]


def generate_invalid_values(param_type: str) -> List[Any]:
    """
    Generate invalid test values for a parameter type.

    Args:
        param_type: Type name

    Returns:
        List of values that should fail validation

    Example:
        values = generate_invalid_values("positive_int")
        # [0, -1, -100]
    """
    if "positive" in param_type.lower():
        return [0, -1, -10, -100]
    elif "non_zero" in param_type.lower():
        return [0]
    elif "non_empty" in param_type.lower():
        if "string" in param_type.lower():
            return ["", " ", "   "]
        elif "list" in param_type.lower():
            return [[]]
    return []
