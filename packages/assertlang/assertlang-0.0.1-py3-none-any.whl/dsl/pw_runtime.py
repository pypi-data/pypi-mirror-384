"""
Promptware Runtime Interpreter

This module implements the PW runtime that executes Promptware IR directly
without transpilation. This IS the runtime for the PW programming language.

Architecture:
- Tree-walking interpreter over IR nodes
- Direct execution without code generation
- Support for generics via monomorphization
- Pattern matching for enum variants
- Built-in stdlib support (Option, Result)

Performance:
- Fast enough for development (optimize later)
- Reasonable memory usage
- Source location tracking for errors
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from dsl.ir import (
    BinaryOperator,
    IRArray,
    IRAssignment,
    IRBinaryOp,
    IRBreak,
    IRCall,
    IRContinue,
    IREnum,
    IREnumVariant,
    IRExpression,
    IRFor,
    IRForCStyle,
    IRFunction,
    IRIdentifier,
    IRIf,
    IRIndex,
    IRLambda,
    IRLiteral,
    IRMap,
    IRModule,
    IRParameter,
    IRPropertyAccess,
    IRReturn,
    IRStatement,
    IRTernary,
    IRType,
    IRUnaryOp,
    IRWhile,
    LiteralType,
    SourceLocation,
    UnaryOperator,
)
from dsl.pw_parser import parse_pw


# ============================================================================
# Runtime Errors and Control Flow
# ============================================================================


class PWRuntimeError(Exception):
    """Runtime error in PW interpreter"""

    def __init__(self, message: str, location: Optional[SourceLocation] = None):
        super().__init__(message)
        self.message = message
        self.location = location

    def __str__(self) -> str:
        if self.location:
            return f"{self.location}: {self.message}"
        return self.message


@dataclass
class ReturnValue:
    """Signal for function return"""

    value: Any


@dataclass
class BreakSignal:
    """Signal for loop break"""

    pass


@dataclass
class ContinueSignal:
    """Signal for loop continue"""

    pass


# ============================================================================
# Enum Variant Runtime Representation
# ============================================================================


@dataclass
class EnumVariantInstance:
    """
    Runtime instance of an enum variant.

    Examples:
        Some(42) -> EnumVariantInstance("Some", [42])
        None -> EnumVariantInstance("None", [])
        Ok(100) -> EnumVariantInstance("Ok", [100])
        Err("failed") -> EnumVariantInstance("Err", ["failed"])
    """

    variant_name: str
    values: List[Any]

    def __repr__(self) -> str:
        if self.values:
            values_str = ", ".join(repr(v) for v in self.values)
            return f"{self.variant_name}({values_str})"
        return self.variant_name


# ============================================================================
# Pattern Matching
# ============================================================================


@dataclass
class PatternMatch:
    """Result of pattern matching"""

    matched: bool
    bindings: Dict[str, Any]


class PatternMatcher:
    """Pattern matching support for enum variants"""

    @staticmethod
    def match(value: Any, pattern: str) -> PatternMatch:
        """
        Match a value against a pattern.

        Patterns:
            "Some(val)" - Match Some variant, bind value to 'val'
            "Some(_)" - Match Some variant, ignore value
            "None" - Match None variant (no value)
            "Ok(x)" - Match Ok variant, bind value to 'x'
            "Err(e)" - Match Err variant, bind error to 'e'

        Returns:
            PatternMatch with matched=True and bindings if successful
            PatternMatch with matched=False if unsuccessful
        """
        if not isinstance(value, EnumVariantInstance):
            return PatternMatch(matched=False, bindings={})

        # Parse pattern: "Name" or "Name(binding)"
        if "(" in pattern:
            # Extract variant name and binding
            variant_name = pattern[: pattern.index("(")]
            binding_part = pattern[pattern.index("(") + 1 : pattern.rindex(")")]

            if value.variant_name != variant_name:
                return PatternMatch(matched=False, bindings={})

            # Check if binding is wildcard
            if binding_part == "_":
                return PatternMatch(matched=True, bindings={})

            # Bind value (only supports single value for now)
            if len(value.values) == 1:
                return PatternMatch(matched=True, bindings={binding_part: value.values[0]})
            elif len(value.values) == 0:
                return PatternMatch(matched=False, bindings={})
            else:
                # Multiple values - bind as tuple
                return PatternMatch(matched=True, bindings={binding_part: tuple(value.values)})
        else:
            # Simple pattern: just variant name
            if value.variant_name != pattern:
                return PatternMatch(matched=False, bindings={})
            return PatternMatch(matched=True, bindings={})


# ============================================================================
# PW Runtime Interpreter
# ============================================================================


class PWRuntime:
    """
    Promptware Runtime Interpreter

    Executes Promptware IR directly without transpilation.
    This IS the runtime for the PW programming language.
    """

    def __init__(self):
        self.globals: Dict[str, Any] = {}  # Global scope
        self.call_stack: List[str] = []  # Call stack for debugging
        self.stdlib_loaded = False  # Track if stdlib is loaded

    def load_stdlib(self) -> None:
        """Load standard library (Option, Result enums and functions)"""
        if self.stdlib_loaded:
            return

        # Parse stdlib/core_simple.al (temporary until parser supports pattern matching)
        stdlib_path = Path(__file__).parent.parent / "stdlib" / "core_simple.al"
        if not stdlib_path.exists():
            # Fallback to core.al if simple version doesn't exist
            stdlib_path = Path(__file__).parent.parent / "stdlib" / "core.al"
            if not stdlib_path.exists():
                raise PWRuntimeError(f"stdlib not found")

        with open(stdlib_path, "r") as f:
            stdlib_source = f.read()

        module = parse_pw(stdlib_source)

        # Register enums (Option, Result)
        for enum in module.enums:
            self.globals[enum.name] = enum

            # Register variant constructors (Some, None, Ok, Err)
            for variant in enum.variants:
                # Create constructor function
                def make_variant_constructor(variant_name: str):
                    def constructor(*args):
                        return EnumVariantInstance(variant_name, list(args))

                    return constructor

                # Register as global: Option.Some, Option.None, Result.Ok, Result.Err
                self.globals[variant.name] = make_variant_constructor(variant.name)

        # Register functions (option_some, option_map, result_ok, etc.)
        for func in module.functions:
            self.globals[func.name] = func

        self.stdlib_loaded = True

    def execute_module(self, module: IRModule) -> Any:
        """Execute a PW module (top-level entry point)"""
        # Load stdlib first
        self.load_stdlib()

        # Register module enums
        for enum in module.enums:
            self.globals[enum.name] = enum
            for variant in enum.variants:

                def make_variant_constructor(variant_name: str):
                    def constructor(*args):
                        return EnumVariantInstance(variant_name, list(args))

                    return constructor

                self.globals[variant.name] = make_variant_constructor(variant.name)

        # Register module functions
        for func in module.functions:
            self.globals[func.name] = func

        # Execute module-level assignments
        last_result = None
        for assignment in module.module_vars:
            last_result = self.execute_statement(assignment, self.globals)

        return last_result

    def execute_function(self, func: Union[IRFunction, callable], args: List[Any]) -> Any:
        """Execute a PW function with arguments"""
        # Handle Python built-in functions
        if callable(func) and not isinstance(func, IRFunction):
            return func(*args)

        if not isinstance(func, IRFunction):
            raise PWRuntimeError(f"Cannot call non-function: {type(func)}")

        # Push to call stack
        self.call_stack.append(func.name)

        try:
            # Create local scope
            local_scope = {}

            # Bind parameters
            for i, param in enumerate(func.params):
                if i < len(args):
                    local_scope[param.name] = args[i]
                elif param.default_value:
                    local_scope[param.name] = self.evaluate_expression(
                        param.default_value, local_scope
                    )
                else:
                    raise PWRuntimeError(
                        f"Missing required argument: {param.name}", func.location
                    )

            # Execute function body
            result = None
            for stmt in func.body:
                result = self.execute_statement(stmt, local_scope)

                # Handle return
                if isinstance(result, ReturnValue):
                    return result.value

            # No explicit return - return None
            return result

        finally:
            # Pop from call stack
            self.call_stack.pop()

    def execute_statement(self, stmt: IRStatement, scope: Dict[str, Any]) -> Any:
        """Execute a single statement"""
        if isinstance(stmt, IRReturn):
            if stmt.value:
                value = self.evaluate_expression(stmt.value, scope)
                return ReturnValue(value)
            return ReturnValue(None)

        elif isinstance(stmt, IRAssignment):
            value = self.evaluate_expression(stmt.value, scope)

            # Handle different assignment targets
            if isinstance(stmt.target, str):
                # Simple assignment: x = value
                if stmt.is_declaration or stmt.target in scope:
                    scope[stmt.target] = value
                elif stmt.target in self.globals:
                    self.globals[stmt.target] = value
                else:
                    # New variable in current scope
                    scope[stmt.target] = value
            elif isinstance(stmt.target, IRIndex):
                # Indexed assignment: arr[0] = value
                obj = self.evaluate_expression(stmt.target.object, scope)
                index = self.evaluate_expression(stmt.target.index, scope)
                obj[index] = value
            elif isinstance(stmt.target, IRPropertyAccess):
                # Property assignment: obj.prop = value
                obj = self.evaluate_expression(stmt.target.object, scope)
                setattr(obj, stmt.target.property, value)
            else:
                raise PWRuntimeError(f"Invalid assignment target: {type(stmt.target)}")

            return value

        elif isinstance(stmt, IRIf):
            condition = self.evaluate_expression(stmt.condition, scope)

            if self._is_truthy(condition):
                return self.execute_block(stmt.then_body, scope)
            elif stmt.else_body:
                return self.execute_block(stmt.else_body, scope)

        elif isinstance(stmt, IRFor):
            iterable = self.evaluate_expression(stmt.iterable, scope)

            # Create new scope for loop variable
            loop_scope = dict(scope)

            for item in iterable:
                loop_scope[stmt.iterator] = item

                result = self.execute_block(stmt.body, loop_scope)

                if isinstance(result, ReturnValue):
                    return result
                if isinstance(result, BreakSignal):
                    break
                if isinstance(result, ContinueSignal):
                    continue

            # Copy loop scope changes back to parent scope
            scope.update(loop_scope)

        elif isinstance(stmt, IRForCStyle):
            # Initialize
            self.execute_statement(stmt.init, scope)

            # Loop
            while True:
                condition = self.evaluate_expression(stmt.condition, scope)
                if not self._is_truthy(condition):
                    break

                result = self.execute_block(stmt.body, scope)

                if isinstance(result, ReturnValue):
                    return result
                if isinstance(result, BreakSignal):
                    break
                if isinstance(result, ContinueSignal):
                    pass  # Continue to increment

                # Increment
                self.execute_statement(stmt.increment, scope)

        elif isinstance(stmt, IRWhile):
            while True:
                condition = self.evaluate_expression(stmt.condition, scope)
                if not self._is_truthy(condition):
                    break

                result = self.execute_block(stmt.body, scope)

                if isinstance(result, ReturnValue):
                    return result
                if isinstance(result, BreakSignal):
                    break

        elif isinstance(stmt, IRBreak):
            return BreakSignal()

        elif isinstance(stmt, IRContinue):
            return ContinueSignal()

        elif isinstance(stmt, IRCall):
            # Expression statement (function call without using result)
            return self.evaluate_expression(stmt, scope)

        else:
            raise PWRuntimeError(f"Unsupported statement type: {type(stmt)}")

    def execute_block(self, statements: List[IRStatement], scope: Dict[str, Any]) -> Any:
        """Execute a block of statements"""
        result = None
        for stmt in statements:
            result = self.execute_statement(stmt, scope)

            # Propagate control flow signals
            if isinstance(result, (ReturnValue, BreakSignal, ContinueSignal)):
                return result

        return result

    def evaluate_expression(self, expr: IRExpression, scope: Dict[str, Any]) -> Any:
        """Evaluate an expression and return its value"""
        if isinstance(expr, IRLiteral):
            return expr.value

        elif isinstance(expr, IRIdentifier):
            # Look up variable
            if expr.name in scope:
                return scope[expr.name]
            elif expr.name in self.globals:
                return self.globals[expr.name]
            else:
                raise PWRuntimeError(f"Undefined variable: {expr.name}", expr.location)

        elif isinstance(expr, IRBinaryOp):
            left = self.evaluate_expression(expr.left, scope)
            right = self.evaluate_expression(expr.right, scope)
            return self._apply_binary_op(expr.op, left, right)

        elif isinstance(expr, IRUnaryOp):
            operand = self.evaluate_expression(expr.operand, scope)
            return self._apply_unary_op(expr.op, operand)

        elif isinstance(expr, IRCall):
            func = self.evaluate_expression(expr.function, scope)
            args = [self.evaluate_expression(arg, scope) for arg in expr.args]

            # Handle IRFunction objects (from stdlib or user code)
            if isinstance(func, IRFunction):
                return self.execute_function(func, args)
            # Handle Python callables (enum constructors, lambdas)
            elif callable(func):
                return self.execute_function(func, args)
            else:
                raise PWRuntimeError(f"Cannot call non-function: {type(func)}")

        elif isinstance(expr, IRArray):
            return [self.evaluate_expression(elem, scope) for elem in expr.elements]

        elif isinstance(expr, IRMap):
            return {key: self.evaluate_expression(val, scope) for key, val in expr.entries.items()}

        elif isinstance(expr, IRIndex):
            obj = self.evaluate_expression(expr.object, scope)
            index = self.evaluate_expression(expr.index, scope)
            return obj[index]

        elif isinstance(expr, IRPropertyAccess):
            obj = self.evaluate_expression(expr.object, scope)

            # Handle enum variant access (e.g., Option.Some)
            if isinstance(obj, IREnum):
                # Look up variant by name
                for variant in obj.variants:
                    if variant.name == expr.property:
                        # Return constructor
                        def make_constructor(variant_name: str):
                            def constructor(*args):
                                return EnumVariantInstance(variant_name, list(args))

                            return constructor

                        return make_constructor(variant.name)
                raise PWRuntimeError(f"Enum {obj.name} has no variant {expr.property}")

            # Regular property access
            if hasattr(obj, expr.property):
                return getattr(obj, expr.property)
            elif isinstance(obj, dict):
                return obj.get(expr.property)
            else:
                raise PWRuntimeError(f"Object has no property: {expr.property}")

        elif isinstance(expr, IRTernary):
            condition = self.evaluate_expression(expr.condition, scope)
            if self._is_truthy(condition):
                return self.evaluate_expression(expr.true_value, scope)
            else:
                return self.evaluate_expression(expr.false_value, scope)

        elif isinstance(expr, IRLambda):
            # Return lambda as closure
            def lambda_func(*args):
                # Create new scope with parameters
                lambda_scope = dict(scope)
                for i, param in enumerate(expr.params):
                    if i < len(args):
                        lambda_scope[param.name] = args[i]

                # Execute body
                if isinstance(expr.body, list):
                    return self.execute_block(expr.body, lambda_scope)
                else:
                    return self.evaluate_expression(expr.body, lambda_scope)

            return lambda_func

        else:
            raise PWRuntimeError(f"Unsupported expression type: {type(expr)}")

    def _apply_binary_op(self, op: BinaryOperator, left: Any, right: Any) -> Any:
        """Apply binary operator"""
        if op == BinaryOperator.ADD:
            return left + right
        elif op == BinaryOperator.SUBTRACT:
            return left - right
        elif op == BinaryOperator.MULTIPLY:
            return left * right
        elif op == BinaryOperator.DIVIDE:
            if right == 0:
                raise PWRuntimeError("Division by zero")
            return left / right
        elif op == BinaryOperator.MODULO:
            return left % right
        elif op == BinaryOperator.POWER:
            return left**right
        elif op == BinaryOperator.FLOOR_DIVIDE:
            return left // right

        elif op == BinaryOperator.EQUAL:
            return self._equals(left, right)
        elif op == BinaryOperator.NOT_EQUAL:
            return not self._equals(left, right)
        elif op == BinaryOperator.LESS_THAN:
            return left < right
        elif op == BinaryOperator.LESS_EQUAL:
            return left <= right
        elif op == BinaryOperator.GREATER_THAN:
            return left > right
        elif op == BinaryOperator.GREATER_EQUAL:
            return left >= right

        elif op == BinaryOperator.AND:
            return self._is_truthy(left) and self._is_truthy(right)
        elif op == BinaryOperator.OR:
            return self._is_truthy(left) or self._is_truthy(right)

        elif op == BinaryOperator.BIT_AND:
            return left & right
        elif op == BinaryOperator.BIT_OR:
            return left | right
        elif op == BinaryOperator.BIT_XOR:
            return left ^ right
        elif op == BinaryOperator.LEFT_SHIFT:
            return left << right
        elif op == BinaryOperator.RIGHT_SHIFT:
            return left >> right

        elif op == BinaryOperator.IN:
            return left in right

        else:
            raise PWRuntimeError(f"Unsupported binary operator: {op}")

    def _apply_unary_op(self, op: UnaryOperator, operand: Any) -> Any:
        """Apply unary operator"""
        if op == UnaryOperator.NOT:
            return not self._is_truthy(operand)
        elif op == UnaryOperator.NEGATE:
            return -operand
        elif op == UnaryOperator.POSITIVE:
            return +operand
        elif op == UnaryOperator.BIT_NOT:
            return ~operand
        else:
            raise PWRuntimeError(f"Unsupported unary operator: {op}")

    def _is_truthy(self, value: Any) -> bool:
        """Determine if a value is truthy (for conditionals)"""
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value != 0
        if isinstance(value, str):
            return len(value) > 0
        if isinstance(value, (list, dict)):
            return len(value) > 0
        # EnumVariantInstance is always truthy
        return True

    def _equals(self, left: Any, right: Any) -> bool:
        """Check equality (handles enum variants)"""
        if isinstance(left, EnumVariantInstance) and isinstance(right, EnumVariantInstance):
            return left.variant_name == right.variant_name and left.values == right.values
        return left == right

    def evaluate_pattern_is(
        self, value: Any, pattern: str, scope: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Evaluate "is" pattern matching.

        Examples:
            opt is Some(val) - Match and bind val
            opt is None - Match None
            res is Ok(x) - Match Ok and bind x
            res is Err(_) - Match Err, ignore value

        Returns:
            Dict of bindings if matched, None if not matched
        """
        match_result = PatternMatcher.match(value, pattern)
        if match_result.matched:
            return match_result.bindings
        return None
