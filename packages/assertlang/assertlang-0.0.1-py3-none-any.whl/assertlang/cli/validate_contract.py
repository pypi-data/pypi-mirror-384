"""
Contract validation for Promptware.

Validates .al files for contract syntax and semantic correctness:
- Syntax correctness
- Clause naming (all @requires, @ensures, @invariant have names)
- Expression validity (boolean expressions, no side effects)
- Completeness checks (warnings for missing contracts)
- Best practices

Usage:
    promptware validate contract.al
    promptware validate contract.al --verbose
"""

from dataclasses import dataclass
from typing import List, Set, Dict, Any
from pathlib import Path

from dsl.pw_parser import Lexer, Parser
from dsl.ir import (
    IRModule, IRFunction, IRClass, IRContractClause,
    IRExpression, IROldExpr, IRBinaryOp, IRUnaryOp,
    IRCall, IRIdentifier, IRPropertyAccess
)


@dataclass
class ValidationResult:
    """Result of contract validation."""
    valid: bool
    errors: List[str]
    warnings: List[str]

    def __bool__(self):
        return self.valid


class ContractValidator:
    """Validates PW contracts for correctness and best practices."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate_file(self, file_path: str) -> ValidationResult:
        """
        Validate a PW contract file.

        Args:
            file_path: Path to .al file

        Returns:
            ValidationResult with errors and warnings
        """
        self.errors = []
        self.warnings = []

        # Read file
        try:
            code = Path(file_path).read_text()
        except Exception as e:
            self.errors.append(f"Failed to read file: {e}")
            return ValidationResult(False, self.errors, self.warnings)

        # Parse
        try:
            lexer = Lexer(code)
            tokens = lexer.tokenize()
            parser = Parser(tokens)
            module = parser.parse()
        except Exception as e:
            self.errors.append(f"Syntax error: {e}")
            return ValidationResult(False, self.errors, self.warnings)

        # Validate module
        self._validate_module(module)

        return ValidationResult(
            valid=len(self.errors) == 0,
            errors=self.errors,
            warnings=self.warnings
        )

    def _validate_module(self, module: IRModule):
        """Validate entire module."""
        # Validate functions
        for func in module.functions:
            self._validate_function(func)

        # Validate classes
        for cls in module.classes:
            self._validate_class(cls)

    def _validate_function(self, func: IRFunction):
        """Validate function contracts."""
        # Check preconditions
        for req in func.requires:
            self._validate_clause(req, func.name, "precondition")

        # Check postconditions
        for ens in func.ensures:
            self._validate_clause(ens, func.name, "postcondition")

        # Check for old in preconditions (error)
        for req in func.requires:
            if self._contains_old(req.expression):
                self.errors.append(
                    f"Function '{func.name}': 'old' keyword not allowed in preconditions"
                )

        # Check for result in preconditions (error)
        for req in func.requires:
            if self._contains_result(req.expression):
                self.errors.append(
                    f"Function '{func.name}': 'result' keyword not allowed in preconditions"
                )

        # Completeness warnings
        if func.name.startswith("_"):
            # Private function, skip warnings
            pass
        else:
            # Public function - recommend contracts
            if len(func.requires) == 0 and len(func.params) > 0:
                self.warnings.append(
                    f"Function '{func.name}': Consider adding preconditions for input validation"
                )

            if len(func.ensures) == 0 and func.return_type and func.return_type != "void":
                if self._is_complex_function(func):
                    self.warnings.append(
                        f"Function '{func.name}': Consider adding postconditions for complex logic"
                    )

    def _validate_class(self, cls: IRClass):
        """Validate class contracts."""
        # Check invariants
        for inv in cls.invariants:
            self._validate_clause(inv, cls.name, "invariant")

        # Validate methods
        for method in cls.methods:
            self._validate_function(method)

        # Completeness warnings
        if len(cls.invariants) == 0 and not cls.name.startswith("_"):
            self.warnings.append(
                f"Class '{cls.name}': Consider adding invariants for class state"
            )

    def _validate_clause(self, clause: IRContractClause, context: str, clause_type: str):
        """
        Validate a single contract clause.

        Checks:
        - Clause has a name
        - Name is valid identifier
        - Expression is boolean
        - No side effects in expression
        """
        # Check clause has name
        if not clause.name:
            self.errors.append(
                f"{context}: {clause_type} clause missing name"
            )
            return

        # Check name is valid identifier
        if not self._is_valid_identifier(clause.name):
            self.errors.append(
                f"{context}: Invalid clause name '{clause.name}' (must be valid identifier)"
            )

        # Check expression validity
        if not self._is_boolean_expression(clause.expression):
            self.warnings.append(
                f"{context}: Clause '{clause.name}' may not return boolean"
            )

        # Check for side effects
        if self._has_side_effects(clause.expression):
            self.errors.append(
                f"{context}: Clause '{clause.name}' contains side effects (assignments, calls)"
            )

    def _is_valid_identifier(self, name: str) -> bool:
        """Check if name is a valid identifier."""
        if not name:
            return False
        if not name[0].isalpha() and name[0] != '_':
            return False
        return all(c.isalnum() or c == '_' for c in name)

    def _is_boolean_expression(self, expr: IRExpression) -> bool:
        """
        Check if expression likely returns boolean.

        This is a heuristic check - we look for:
        - Binary comparison operators (==, !=, <, >, <=, >=)
        - Logical operators (&&, ||)
        - Unary ! operator
        - Boolean literals (true, false)
        """
        if isinstance(expr, IRBinaryOp):
            return expr.op in ['==', '!=', '<', '>', '<=', '>=', '&&', '||', 'and', 'or']
        elif isinstance(expr, IRUnaryOp):
            return expr.op in ['!', 'not']
        elif isinstance(expr, IRIdentifier):
            return expr.name in ['true', 'false', 'True', 'False']
        # Can't determine statically for other cases
        return True

    def _has_side_effects(self, expr: IRExpression) -> bool:
        """
        Check if expression has side effects.

        Side effects include:
        - Assignments
        - Function calls (except pure functions like len, str.contains)
        - Property setters
        """
        # For now, just check for function calls
        # We'd need more sophisticated analysis for a real implementation
        if isinstance(expr, IRCall):
            # Allow known pure functions
            pure_functions = {'len', 'str.length', 'str.contains', 'all', 'any', 'map', 'filter'}
            func_name = expr.name
            if hasattr(expr, 'func') and hasattr(expr.func, 'name'):
                func_name = expr.func.name
            if func_name not in pure_functions:
                return True

        # Recursively check sub-expressions
        if isinstance(expr, IRBinaryOp):
            return self._has_side_effects(expr.left) or self._has_side_effects(expr.right)
        elif isinstance(expr, IRUnaryOp):
            return self._has_side_effects(expr.operand)
        elif isinstance(expr, IROldExpr):
            return self._has_side_effects(expr.expression)

        return False

    def _contains_old(self, expr: IRExpression) -> bool:
        """Check if expression contains 'old' keyword."""
        if isinstance(expr, IROldExpr):
            return True
        elif isinstance(expr, IRBinaryOp):
            return self._contains_old(expr.left) or self._contains_old(expr.right)
        elif isinstance(expr, IRUnaryOp):
            return self._contains_old(expr.operand)
        elif isinstance(expr, IRCall):
            return any(self._contains_old(arg) for arg in expr.args)
        return False

    def _contains_result(self, expr: IRExpression) -> bool:
        """Check if expression references 'result'."""
        if isinstance(expr, IRIdentifier):
            return expr.name == 'result'
        elif isinstance(expr, IRBinaryOp):
            return self._contains_result(expr.left) or self._contains_result(expr.right)
        elif isinstance(expr, IRUnaryOp):
            return self._contains_result(expr.operand)
        elif isinstance(expr, IRPropertyAccess):
            return self._contains_result(expr.object)
        elif isinstance(expr, IRCall):
            return any(self._contains_result(arg) for arg in expr.args)
        return False

    def _is_complex_function(self, func: IRFunction) -> bool:
        """
        Heuristic to determine if function is complex enough to warrant postconditions.

        Complex if:
        - Has loops
        - Has conditionals
        - Has multiple statements
        - Modifies state
        """
        # Simple heuristic: if function has body with >3 statements
        if hasattr(func, 'body') and func.body:
            if isinstance(func.body, list):
                return len(func.body) > 3
        return False


def validate_contract(file_path: str, verbose: bool = False) -> ValidationResult:
    """
    Validate a PW contract file.

    Args:
        file_path: Path to .al file
        verbose: Show detailed output

    Returns:
        ValidationResult

    Example:
        result = validate_contract("contract.al")
        if result.valid:
            print("Valid!")
        else:
            for error in result.errors:
                print(f"Error: {error}")
    """
    validator = ContractValidator(verbose=verbose)
    return validator.validate_file(file_path)


def print_validation_result(result: ValidationResult, verbose: bool = False):
    """
    Pretty-print validation result.

    Args:
        result: ValidationResult to print
        verbose: Show additional details
    """
    if result.valid:
        print("✓ Syntax valid")
        print("✓ All contract clauses have names")
        print("✓ Expressions are well-formed")
        print("✓ No forbidden keywords in wrong contexts")

        if len(result.warnings) == 0:
            print("✓ No warnings")
        else:
            print(f"\n⚠️  {len(result.warnings)} warning(s):")
            for warning in result.warnings:
                print(f"  - {warning}")
    else:
        print(f"✗ Validation failed with {len(result.errors)} error(s):")
        for error in result.errors:
            print(f"  - {error}")

        if len(result.warnings) > 0:
            print(f"\n⚠️  {len(result.warnings)} warning(s):")
            for warning in result.warnings:
                print(f"  - {warning}")

    if verbose and result.valid:
        print("\n📋 Validation Details:")
        print("  All checks passed")
