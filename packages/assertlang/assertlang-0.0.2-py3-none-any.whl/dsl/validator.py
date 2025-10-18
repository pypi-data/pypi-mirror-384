"""
Promptware IR Semantic Validator

This module provides semantic validation for IR trees. It ensures that:
1. Type consistency - Types are used correctly
2. Semantic correctness - Control flow, scoping, etc.
3. Structural integrity - Required fields present, proper nesting
4. Reference validity - Variables/functions are defined before use

The validator catches errors early, before code generation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Set

from dsl.ir import (
    BinaryOperator,
    IRAssignment,
    IRBinaryOp,
    IRBreak,
    IRCall,
    IRCatch,
    IRClass,
    IRContinue,
    IREnum,
    IRExpression,
    IRFor,
    IRFunction,
    IRIdentifier,
    IRIf,
    IRImport,
    IRIndex,
    IRLambda,
    IRLiteral,
    IRMap,
    IRModule,
    IRNode,
    IRParameter,
    IRPropertyAccess,
    IRReturn,
    IRStatement,
    IRThrow,
    IRTry,
    IRType,
    IRTypeDefinition,
    IRUnaryOp,
    IRWhile,
    NodeType,
    UnaryOperator,
)


class ValidationError(Exception):
    """Raised when IR validation fails."""

    def __init__(self, message: str, node: Optional[IRNode] = None):
        self.message = message
        self.node = node
        location = node.location if node else None
        if location:
            super().__init__(f"{location}: {message}")
        else:
            super().__init__(message)


@dataclass
class ValidationContext:
    """Context for validation, tracking scopes and symbols."""

    # Symbol tables (stack of scopes)
    scopes: List[Dict[str, IRNode]] = None

    # Defined types
    types: Set[str] = None

    # Defined functions
    functions: Set[str] = None

    # Current function (for return validation)
    current_function: Optional[IRFunction] = None

    # Loop depth (for break/continue validation)
    loop_depth: int = 0

    def __post_init__(self):
        if self.scopes is None:
            self.scopes = [{}]  # Global scope
        if self.types is None:
            self.types = {
                # Primitive types
                "string", "int", "float", "bool", "null", "any",
                # Collection types (generic)
                "array", "map",
            }
        if self.functions is None:
            self.functions = set()

    def enter_scope(self) -> None:
        """Enter a new scope."""
        self.scopes.append({})

    def exit_scope(self) -> None:
        """Exit current scope."""
        if len(self.scopes) > 1:
            self.scopes.pop()

    def define_symbol(self, name: str, node: IRNode) -> None:
        """Define a symbol in current scope."""
        self.scopes[-1][name] = node

    def lookup_symbol(self, name: str) -> Optional[IRNode]:
        """Look up a symbol in all scopes (innermost first)."""
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return None

    def is_symbol_defined(self, name: str) -> bool:
        """Check if symbol is defined in any scope."""
        return self.lookup_symbol(name) is not None


class IRValidator:
    """
    Validates IR trees for semantic correctness.

    Usage:
        validator = IRValidator()
        validator.validate(ir_module)  # Raises ValidationError if invalid
    """

    def __init__(self):
        self.errors: List[ValidationError] = []
        self.warnings: List[str] = []

    def validate(self, module: IRModule, strict: bool = True) -> None:
        """
        Validate an IR module.

        Args:
            module: The IR module to validate
            strict: If True, raise on first error. If False, collect all errors.

        Raises:
            ValidationError: If validation fails and strict=True
        """
        self.errors = []
        self.warnings = []
        ctx = ValidationContext()

        try:
            self._validate_module(module, ctx)
        except ValidationError as e:
            if strict:
                raise
            self.errors.append(e)

        if strict and self.errors:
            raise self.errors[0]

    def _validate_module(self, module: IRModule, ctx: ValidationContext) -> None:
        """Validate a module."""
        if not module.name:
            raise ValidationError("Module must have a name", module)

        # Validate imports
        for imp in module.imports:
            self._validate_import(imp, ctx)

        # Register all type definitions first
        for type_def in module.types:
            if type_def.name in ctx.types:
                raise ValidationError(f"Duplicate type definition: {type_def.name}", type_def)
            ctx.types.add(type_def.name)

        # Register all enum definitions
        for enum in module.enums:
            if enum.name in ctx.types:
                raise ValidationError(f"Duplicate type definition: {enum.name}", enum)
            ctx.types.add(enum.name)

        # Register all function definitions
        for func in module.functions:
            if func.name in ctx.functions:
                raise ValidationError(f"Duplicate function definition: {func.name}", func)
            ctx.functions.add(func.name)

        # Register all class definitions
        for cls in module.classes:
            if cls.name in ctx.types:
                raise ValidationError(f"Duplicate type definition: {cls.name}", cls)
            ctx.types.add(cls.name)
            # Also register class methods as functions
            for method in cls.methods:
                ctx.functions.add(f"{cls.name}.{method.name}")

        # Now validate type definitions
        for type_def in module.types:
            self._validate_type_definition(type_def, ctx)

        # Validate enums
        for enum in module.enums:
            self._validate_enum(enum, ctx)

        # Validate functions
        for func in module.functions:
            self._validate_function(func, ctx)

        # Validate classes
        for cls in module.classes:
            self._validate_class(cls, ctx)

        # Validate module-level variables
        for var in module.module_vars:
            self._validate_statement(var, ctx)

    def _validate_import(self, imp: IRImport, ctx: ValidationContext) -> None:
        """Validate an import."""
        if not imp.module:
            raise ValidationError("Import must specify a module", imp)

    def _validate_type_definition(self, type_def: IRTypeDefinition, ctx: ValidationContext) -> None:
        """Validate a type definition."""
        if not type_def.name:
            raise ValidationError("Type definition must have a name", type_def)

        # Validate all field types
        field_names = set()
        for field in type_def.fields:
            if field.name in field_names:
                raise ValidationError(
                    f"Duplicate field '{field.name}' in type {type_def.name}",
                    field
                )
            field_names.add(field.name)
            self._validate_type(field.prop_type, ctx)

    def _validate_enum(self, enum: IREnum, ctx: ValidationContext) -> None:
        """Validate an enum."""
        if not enum.name:
            raise ValidationError("Enum must have a name", enum)

        variant_names = set()
        for variant in enum.variants:
            if variant.name in variant_names:
                raise ValidationError(
                    f"Duplicate variant '{variant.name}' in enum {enum.name}",
                    variant
                )
            variant_names.add(variant.name)

    def _validate_function(self, func: IRFunction, ctx: ValidationContext) -> None:
        """Validate a function."""
        if not func.name:
            raise ValidationError("Function must have a name", func)

        # Enter function scope
        ctx.enter_scope()
        old_func = ctx.current_function
        ctx.current_function = func

        # Validate parameters
        param_names = set()
        for param in func.params:
            if param.name in param_names:
                raise ValidationError(f"Duplicate parameter '{param.name}'", param)
            param_names.add(param.name)
            self._validate_type(param.param_type, ctx)
            ctx.define_symbol(param.name, param)

            # Validate default value if present
            if param.default_value:
                self._validate_expression(param.default_value, ctx)

        # Validate return type
        if func.return_type:
            self._validate_type(func.return_type, ctx)

        # Validate body
        for stmt in func.body:
            self._validate_statement(stmt, ctx)

        # Exit function scope
        ctx.current_function = old_func
        ctx.exit_scope()

    def _validate_class(self, cls: IRClass, ctx: ValidationContext) -> None:
        """Validate a class."""
        if not cls.name:
            raise ValidationError("Class must have a name", cls)

        # Enter class scope
        ctx.enter_scope()

        # Validate properties
        prop_names = set()
        for prop in cls.properties:
            if prop.name in prop_names:
                raise ValidationError(f"Duplicate property '{prop.name}'", prop)
            prop_names.add(prop.name)
            self._validate_type(prop.prop_type, ctx)
            ctx.define_symbol(prop.name, prop)

        # Validate constructor
        if cls.constructor:
            self._validate_function(cls.constructor, ctx)

        # Validate methods
        method_names = set()
        for method in cls.methods:
            if method.name in method_names:
                raise ValidationError(f"Duplicate method '{method.name}'", method)
            method_names.add(method.name)
            self._validate_function(method, ctx)

        ctx.exit_scope()

    def _validate_type(self, type_ref: IRType, ctx: ValidationContext) -> None:
        """Validate a type reference."""
        # Check if base type exists
        if type_ref.name not in ctx.types:
            # Allow generic type parameters (single uppercase letters)
            if not (len(type_ref.name) == 1 and type_ref.name.isupper()):
                self.warnings.append(f"Unknown type: {type_ref.name}")

        # Validate generic arguments
        for arg in type_ref.generic_args:
            self._validate_type(arg, ctx)

        # Validate union types
        for union_type in type_ref.union_types:
            self._validate_type(union_type, ctx)

    def _validate_statement(self, stmt: IRStatement, ctx: ValidationContext) -> None:
        """Validate a statement."""
        if isinstance(stmt, IRIf):
            self._validate_expression(stmt.condition, ctx)
            for s in stmt.then_body:
                self._validate_statement(s, ctx)
            for s in stmt.else_body:
                self._validate_statement(s, ctx)

        elif isinstance(stmt, IRFor):
            ctx.enter_scope()
            ctx.loop_depth += 1
            # Define iterator variable
            ctx.define_symbol(stmt.iterator, stmt)
            self._validate_expression(stmt.iterable, ctx)
            for s in stmt.body:
                self._validate_statement(s, ctx)
            ctx.loop_depth -= 1
            ctx.exit_scope()

        elif isinstance(stmt, IRWhile):
            ctx.loop_depth += 1
            self._validate_expression(stmt.condition, ctx)
            for s in stmt.body:
                self._validate_statement(s, ctx)
            ctx.loop_depth -= 1

        elif isinstance(stmt, IRTry):
            # Validate try body
            for s in stmt.try_body:
                self._validate_statement(s, ctx)

            # Validate catch blocks
            for catch in stmt.catch_blocks:
                ctx.enter_scope()
                if catch.exception_var:
                    ctx.define_symbol(catch.exception_var, catch)
                for s in catch.body:
                    self._validate_statement(s, ctx)
                ctx.exit_scope()

            # Validate finally body
            for s in stmt.finally_body:
                self._validate_statement(s, ctx)

        elif isinstance(stmt, IRAssignment):
            self._validate_expression(stmt.value, ctx)
            # Define symbol in current scope
            ctx.define_symbol(stmt.target, stmt)

        elif isinstance(stmt, IRReturn):
            if ctx.current_function is None:
                raise ValidationError("Return outside of function", stmt)
            if stmt.value:
                self._validate_expression(stmt.value, ctx)

        elif isinstance(stmt, IRThrow):
            self._validate_expression(stmt.exception, ctx)

        elif isinstance(stmt, IRBreak):
            if ctx.loop_depth == 0:
                raise ValidationError("Break outside of loop", stmt)

        elif isinstance(stmt, IRContinue):
            if ctx.loop_depth == 0:
                raise ValidationError("Continue outside of loop", stmt)

        elif isinstance(stmt, IRCall):
            # Expression statement
            self._validate_expression(stmt, ctx)

    def _validate_expression(self, expr: IRExpression, ctx: ValidationContext) -> None:
        """Validate an expression."""
        if isinstance(expr, IRCall):
            self._validate_expression(expr.function, ctx)
            for arg in expr.args:
                self._validate_expression(arg, ctx)
            for kwarg_val in expr.kwargs.values():
                self._validate_expression(kwarg_val, ctx)

        elif isinstance(expr, IRBinaryOp):
            self._validate_expression(expr.left, ctx)
            self._validate_expression(expr.right, ctx)

        elif isinstance(expr, IRUnaryOp):
            self._validate_expression(expr.operand, ctx)

        elif isinstance(expr, IRIdentifier):
            # Check if identifier is defined
            if not ctx.is_symbol_defined(expr.name):
                # Could be a function or module reference
                if expr.name not in ctx.functions:
                    self.warnings.append(f"Undefined identifier: {expr.name}")

        elif isinstance(expr, IRPropertyAccess):
            self._validate_expression(expr.object, ctx)

        elif isinstance(expr, IRIndex):
            self._validate_expression(expr.object, ctx)
            self._validate_expression(expr.index, ctx)

        elif isinstance(expr, IRLambda):
            ctx.enter_scope()
            for param in expr.params:
                ctx.define_symbol(param.name, param)
            if isinstance(expr.body, list):
                for stmt in expr.body:
                    self._validate_statement(stmt, ctx)
            else:
                self._validate_expression(expr.body, ctx)
            ctx.exit_scope()

        elif isinstance(expr, (IRLiteral,)):
            # Literals are always valid
            pass

        # Validate container expressions
        from dsl.ir import IRArray, IRMap, IRTernary

        if isinstance(expr, IRArray):
            for elem in expr.elements:
                self._validate_expression(elem, ctx)

        elif isinstance(expr, IRMap):
            for value in expr.entries.values():
                self._validate_expression(value, ctx)

        elif isinstance(expr, IRTernary):
            self._validate_expression(expr.condition, ctx)
            self._validate_expression(expr.true_value, ctx)
            self._validate_expression(expr.false_value, ctx)


def validate_ir(module: IRModule, strict: bool = True) -> None:
    """
    Convenience function to validate an IR module.

    Args:
        module: The IR module to validate
        strict: If True, raise on first error

    Raises:
        ValidationError: If validation fails and strict=True
    """
    validator = IRValidator()
    validator.validate(module, strict=strict)
