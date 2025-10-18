"""
PW DSL 2.0 Generator

Converts IR (Intermediate Representation) back into PW DSL 2.0 text.

This enables round-trip translation:
  PW text → Parser → IR → Generator → PW text

The generator produces idiomatic, readable PW code with proper indentation.
"""

from __future__ import annotations

from typing import List, Optional

from dsl.ir import (
    BinaryOperator,
    IRArray,
    IRAssignment,
    IRBinaryOp,
    IRBreak,
    IRCall,
    IRCatch,
    IRClass,
    IRComprehension,
    IRContinue,
    IREnum,
    IREnumVariant,
    IRExpression,
    IRFor,
    IRFString,
    IRFunction,
    IRIdentifier,
    IRIf,
    IRImport,
    IRIndex,
    IRLambda,
    IRLiteral,
    IRMap,
    IRModule,
    IRParameter,
    IRPass,
    IRProperty,
    IRPropertyAccess,
    IRReturn,
    IRStatement,
    IRTernary,
    IRThrow,
    IRTry,
    IRType,
    IRTypeDefinition,
    IRUnaryOp,
    IRWhile,
    LiteralType,
    NodeType,
    UnaryOperator,
)


class PWGenerator:
    """Generate PW DSL 2.0 text from IR."""

    def __init__(self, indent_size: int = 2):
        self.indent_size = indent_size
        self.indent_level = 0

    def indent(self) -> str:
        """Get current indentation string."""
        return " " * (self.indent_level * self.indent_size)

    def increase_indent(self) -> None:
        """Increase indentation level."""
        self.indent_level += 1

    def decrease_indent(self) -> None:
        """Decrease indentation level."""
        if self.indent_level > 0:
            self.indent_level -= 1

    # ========================================================================
    # Top-level generation
    # ========================================================================

    def generate(self, module: IRModule) -> str:
        """Generate PW DSL 2.0 text from IR module."""
        lines = []

        # Module declaration
        lines.append(f"module {module.name}")
        lines.append(f"version {module.version}")
        lines.append("")

        # Imports
        for imp in module.imports:
            lines.append(self.generate_import(imp))
        if module.imports:
            lines.append("")

        # Type definitions
        for type_def in module.types:
            lines.append(self.generate_type_definition(type_def))
            lines.append("")

        # Enums
        for enum in module.enums:
            lines.append(self.generate_enum(enum))
            lines.append("")

        # Module-level variables/constants
        for var in module.module_vars:
            lines.append(self.generate_module_var(var))
        if module.module_vars:
            lines.append("")

        # Functions
        for func in module.functions:
            lines.append(self.generate_function(func))
            lines.append("")

        # Classes
        for cls in module.classes:
            lines.append(self.generate_class(cls))
            lines.append("")

        # Join and clean up
        result = "\n".join(lines)
        # Remove excessive blank lines
        while "\n\n\n" in result:
            result = result.replace("\n\n\n", "\n\n")
        return result.strip() + "\n"

    def generate_import(self, imp: IRImport) -> str:
        """Generate import statement."""
        if imp.alias:
            if imp.items:  # from package import module as alias
                return f"import {imp.module} from {imp.alias}"
            else:  # import module as alias
                return f"import {imp.module} as {imp.alias}"
        else:
            return f"import {imp.module}"

    def generate_type_definition(self, type_def: IRTypeDefinition) -> str:
        """Generate type definition."""
        lines = [f"type {type_def.name}:"]
        self.increase_indent()

        for field in type_def.fields:
            field_line = f"{self.indent()}{field.name} {self.generate_type(field.prop_type)}"
            if field.default_value:
                field_line += f" = {self.generate_expression(field.default_value)}"
            lines.append(field_line)

        self.decrease_indent()
        return "\n".join(lines)

    def generate_enum(self, enum: IREnum) -> str:
        """Generate enum definition."""
        lines = [f"enum {enum.name}:"]
        self.increase_indent()

        for variant in enum.variants:
            variant_line = f"{self.indent()}- {variant.name}"
            if variant.associated_types:
                types = ", ".join(self.generate_type(t) for t in variant.associated_types)
                variant_line += f"({types})"
            lines.append(variant_line)

        self.decrease_indent()
        return "\n".join(lines)

    def generate_module_var(self, var: 'IRAssignment') -> str:
        """Generate module-level variable/constant declaration."""
        # Module vars are just assignments at the top level
        target = self.generate_expression(var.target)
        value = self.generate_expression(var.value)
        return f"let {target} = {value}"

    def generate_function(self, func: IRFunction) -> str:
        """Generate function definition."""
        lines = []

        # Function signature
        prefix = "async " if func.is_async else ""
        lines.append(f"{prefix}function {func.name}:")

        self.increase_indent()

        # Parameters
        if func.params:
            lines.append(f"{self.indent()}params:")
            self.increase_indent()
            for param in func.params:
                param_line = f"{self.indent()}{param.name} {self.generate_type(param.param_type)}"
                if param.default_value:
                    param_line += f" = {self.generate_expression(param.default_value)}"
                lines.append(param_line)
            self.decrease_indent()

        # Return type
        if func.return_type:
            lines.append(f"{self.indent()}returns:")
            self.increase_indent()
            # For now, assume single return value named "result"
            lines.append(f"{self.indent()}result {self.generate_type(func.return_type)}")
            self.decrease_indent()

        # Throws
        if func.throws:
            lines.append(f"{self.indent()}throws:")
            self.increase_indent()
            for exception in func.throws:
                lines.append(f"{self.indent()}- {exception}")
            self.decrease_indent()

        # Body
        if func.body:
            lines.append(f"{self.indent()}body:")
            self.increase_indent()
            for stmt in func.body:
                stmt_lines = self.generate_statement(stmt)
                lines.extend(stmt_lines.split("\n"))
            self.decrease_indent()

        self.decrease_indent()
        return "\n".join(lines)

    def generate_class(self, cls: IRClass) -> str:
        """Generate class definition."""
        lines = []

        # Class signature
        class_line = f"class {cls.name}"
        if cls.base_classes:
            class_line += ": " + ", ".join(cls.base_classes)
        class_line += ":"
        lines.append(class_line)

        self.increase_indent()

        # Properties
        if cls.properties:
            lines.append(f"{self.indent()}properties:")
            self.increase_indent()
            for prop in cls.properties:
                prop_line = f"{self.indent()}{prop.name} {self.generate_type(prop.prop_type)}"
                if prop.default_value:
                    prop_line += f" = {self.generate_expression(prop.default_value)}"
                lines.append(prop_line)
            self.decrease_indent()

        # Constructor
        if cls.constructor:
            lines.append(f"{self.indent()}constructor:")
            self.increase_indent()

            if cls.constructor.params:
                lines.append(f"{self.indent()}params:")
                self.increase_indent()
                for param in cls.constructor.params:
                    param_line = f"{self.indent()}{param.name} {self.generate_type(param.param_type)}"
                    if param.default_value:
                        param_line += f" = {self.generate_expression(param.default_value)}"
                    lines.append(param_line)
                self.decrease_indent()

            if cls.constructor.body:
                lines.append(f"{self.indent()}body:")
                self.increase_indent()
                for stmt in cls.constructor.body:
                    stmt_lines = self.generate_statement(stmt)
                    lines.extend(stmt_lines.split("\n"))
                self.decrease_indent()

            self.decrease_indent()

        # Methods
        for method in cls.methods:
            lines.append(f"{self.indent()}method {method.name}:")
            self.increase_indent()

            if method.params:
                lines.append(f"{self.indent()}params:")
                self.increase_indent()
                for param in method.params:
                    param_line = f"{self.indent()}{param.name} {self.generate_type(param.param_type)}"
                    if param.default_value:
                        param_line += f" = {self.generate_expression(param.default_value)}"
                    lines.append(param_line)
                self.decrease_indent()

            if method.return_type:
                lines.append(f"{self.indent()}returns:")
                self.increase_indent()
                lines.append(f"{self.indent()}result {self.generate_type(method.return_type)}")
                self.decrease_indent()

            if method.throws:
                lines.append(f"{self.indent()}throws:")
                self.increase_indent()
                for exception in method.throws:
                    lines.append(f"{self.indent()}- {exception}")
                self.decrease_indent()

            if method.body:
                lines.append(f"{self.indent()}body:")
                self.increase_indent()
                for stmt in method.body:
                    stmt_lines = self.generate_statement(stmt)
                    lines.extend(stmt_lines.split("\n"))
                self.decrease_indent()

            self.decrease_indent()

        self.decrease_indent()
        return "\n".join(lines)

    # ========================================================================
    # Type generation
    # ========================================================================

    def generate_type(self, typ: IRType) -> str:
        """Generate type annotation."""
        result = typ.name

        # Generic arguments
        if typ.generic_args:
            args = ", ".join(self.generate_type(t) for t in typ.generic_args)
            result = f"{result}<{args}>"

        # Union types
        if typ.union_types:
            union_parts = [result] + [self.generate_type(t) for t in typ.union_types]
            result = " | ".join(union_parts)

        # Optional marker
        if typ.is_optional:
            result = f"{result}?"

        return result

    # ========================================================================
    # Statement generation
    # ========================================================================

    def generate_statement(self, stmt: IRStatement) -> str:
        """Generate statement."""
        if isinstance(stmt, IRAssignment):
            return self.generate_assignment(stmt)
        elif isinstance(stmt, IRIf):
            return self.generate_if(stmt)
        elif isinstance(stmt, IRFor):
            return self.generate_for(stmt)
        elif isinstance(stmt, IRWhile):
            return self.generate_while(stmt)
        elif isinstance(stmt, IRTry):
            return self.generate_try(stmt)
        elif isinstance(stmt, IRReturn):
            return self.generate_return(stmt)
        elif isinstance(stmt, IRThrow):
            return self.generate_throw(stmt)
        elif isinstance(stmt, IRBreak):
            return f"{self.indent()}break"
        elif isinstance(stmt, IRContinue):
            return f"{self.indent()}continue"
        elif isinstance(stmt, IRPass):
            return f"{self.indent()}pass"
        elif isinstance(stmt, IRCall):
            # Expression statement (function call)
            return f"{self.indent()}{self.generate_expression(stmt)}"
        else:
            return f"{self.indent()}# Unknown statement: {type(stmt).__name__}"

    def generate_assignment(self, stmt: IRAssignment) -> str:
        """Generate assignment statement."""
        prefix = "let " if stmt.is_declaration else ""
        return f"{self.indent()}{prefix}{stmt.target} = {self.generate_expression(stmt.value)}"

    def generate_if(self, stmt: IRIf) -> str:
        """Generate if statement."""
        lines = []
        lines.append(f"{self.indent()}if {self.generate_expression(stmt.condition)}:")

        self.increase_indent()
        for s in stmt.then_body:
            lines.append(self.generate_statement(s))
        self.decrease_indent()

        if stmt.else_body:
            lines.append(f"{self.indent()}else:")
            self.increase_indent()
            for s in stmt.else_body:
                lines.append(self.generate_statement(s))
            self.decrease_indent()

        return "\n".join(lines)

    def generate_for(self, stmt: IRFor) -> str:
        """Generate for loop."""
        lines = []
        lines.append(f"{self.indent()}for {stmt.iterator} in {self.generate_expression(stmt.iterable)}:")

        self.increase_indent()
        for s in stmt.body:
            lines.append(self.generate_statement(s))
        self.decrease_indent()

        return "\n".join(lines)

    def generate_while(self, stmt: IRWhile) -> str:
        """Generate while loop."""
        lines = []
        lines.append(f"{self.indent()}while {self.generate_expression(stmt.condition)}:")

        self.increase_indent()
        for s in stmt.body:
            lines.append(self.generate_statement(s))
        self.decrease_indent()

        return "\n".join(lines)

    def generate_try(self, stmt: IRTry) -> str:
        """Generate try-catch statement."""
        lines = []
        lines.append(f"{self.indent()}try:")

        self.increase_indent()
        for s in stmt.try_body:
            lines.append(self.generate_statement(s))
        self.decrease_indent()

        for catch in stmt.catch_blocks:
            catch_line = f"{self.indent()}catch"
            if catch.exception_type:
                catch_line += f" {catch.exception_type}"
                if catch.exception_var:
                    catch_line += f" {catch.exception_var}"
            catch_line += ":"
            lines.append(catch_line)

            self.increase_indent()
            for s in catch.body:
                lines.append(self.generate_statement(s))
            self.decrease_indent()

        if stmt.finally_body:
            lines.append(f"{self.indent()}finally:")
            self.increase_indent()
            for s in stmt.finally_body:
                lines.append(self.generate_statement(s))
            self.decrease_indent()

        return "\n".join(lines)

    def generate_return(self, stmt: IRReturn) -> str:
        """Generate return statement."""
        if stmt.value:
            return f"{self.indent()}return {self.generate_expression(stmt.value)}"
        else:
            return f"{self.indent()}return"

    def generate_throw(self, stmt: IRThrow) -> str:
        """Generate throw statement."""
        return f"{self.indent()}throw {self.generate_expression(stmt.exception)}"

    # ========================================================================
    # Expression generation
    # ========================================================================

    def generate_expression(self, expr: IRExpression) -> str:
        """Generate expression."""
        if isinstance(expr, IRLiteral):
            return self.generate_literal(expr)
        elif isinstance(expr, IRIdentifier):
            return expr.name
        elif isinstance(expr, IRBinaryOp):
            return self.generate_binary_op(expr)
        elif isinstance(expr, IRUnaryOp):
            return self.generate_unary_op(expr)
        elif isinstance(expr, IRCall):
            return self.generate_call(expr)
        elif isinstance(expr, IRPropertyAccess):
            return f"{self.generate_expression(expr.object)}.{expr.property}"
        elif isinstance(expr, IRIndex):
            return f"{self.generate_expression(expr.object)}[{self.generate_expression(expr.index)}]"
        elif isinstance(expr, IRArray):
            return self.generate_array(expr)
        elif isinstance(expr, IRMap):
            return self.generate_map(expr)
        elif isinstance(expr, IRTernary):
            return self.generate_ternary(expr)
        elif isinstance(expr, IRLambda):
            return self.generate_lambda(expr)
        elif isinstance(expr, IRComprehension):
            return self.generate_comprehension(expr)
        elif isinstance(expr, IRFString):
            return self.generate_fstring(expr)
        else:
            return f"<unknown: {type(expr).__name__}>"

    def generate_literal(self, lit: IRLiteral) -> str:
        """Generate literal value."""
        if lit.literal_type == LiteralType.STRING:
            # Escape string properly
            value = str(lit.value).replace("\\", "\\\\").replace('"', '\\"')
            return f'"{value}"'
        elif lit.literal_type == LiteralType.INTEGER:
            return str(lit.value)
        elif lit.literal_type == LiteralType.FLOAT:
            return str(lit.value)
        elif lit.literal_type == LiteralType.BOOLEAN:
            return "true" if lit.value else "false"
        elif lit.literal_type == LiteralType.NULL:
            return "null"
        else:
            return str(lit.value)

    def generate_binary_op(self, expr: IRBinaryOp) -> str:
        """Generate binary operation."""
        left = self.generate_expression(expr.left)
        right = self.generate_expression(expr.right)
        op = expr.op.value  # Use enum value

        # Add parentheses for clarity
        return f"({left} {op} {right})"

    def generate_unary_op(self, expr: IRUnaryOp) -> str:
        """Generate unary operation."""
        operand = self.generate_expression(expr.operand)
        op = expr.op.value

        if expr.op == UnaryOperator.NOT:
            return f"not {operand}"
        else:
            return f"{op}{operand}"

    def generate_call(self, expr: IRCall) -> str:
        """Generate function call."""
        func = self.generate_expression(expr.function)

        # Positional arguments
        args = [self.generate_expression(arg) for arg in expr.args]

        # Named arguments
        kwargs = [f"{k}: {self.generate_expression(v)}" for k, v in expr.kwargs.items()]

        all_args = args + kwargs
        return f"{func}({', '.join(all_args)})"

    def generate_array(self, expr: IRArray) -> str:
        """Generate array literal."""
        elements = [self.generate_expression(el) for el in expr.elements]
        return f"[{', '.join(elements)}]"

    def generate_map(self, expr: IRMap) -> str:
        """Generate map literal."""
        entries = [f"{k}: {self.generate_expression(v)}" for k, v in expr.entries.items()]
        if not entries:
            return "{}"
        return "{" + ", ".join(entries) + "}"

    def generate_ternary(self, expr: IRTernary) -> str:
        """Generate ternary expression."""
        true_val = self.generate_expression(expr.true_value)
        cond = self.generate_expression(expr.condition)
        false_val = self.generate_expression(expr.false_value)
        return f"{true_val} if {cond} else {false_val}"

    def generate_lambda(self, expr: IRLambda) -> str:
        """Generate lambda expression."""
        params = ", ".join(p.name for p in expr.params)
        if isinstance(expr.body, list):
            # Multi-statement lambda (not standard, but handle it)
            return f"lambda {params}: ..."
        else:
            body = self.generate_expression(expr.body)
            return f"lambda {params}: {body}"

    def generate_comprehension(self, expr: IRComprehension) -> str:
        """
        Generate list/dict/set comprehension.

        Examples:
            [x * 2 for x in items]
            {k: v for k, v in items}
            {x for x in items if x > 0}
        """
        target = self.generate_expression(expr.target)
        iterator = expr.iterator
        iterable = self.generate_expression(expr.iterable)

        # Build comprehension string
        if expr.comprehension_type == "dict":
            # Dict comprehension has special target format
            if isinstance(expr.target, IRMap) and "__key__" in expr.target.entries:
                key = self.generate_expression(expr.target.entries["__key__"])
                value = self.generate_expression(expr.target.entries["__value__"])
                comp = f"{{{key}: {value} for {iterator} in {iterable}"
            else:
                comp = f"{{{target} for {iterator} in {iterable}"
        elif expr.comprehension_type == "set":
            comp = f"{{{target} for {iterator} in {iterable}"
        elif expr.comprehension_type == "generator":
            comp = f"({target} for {iterator} in {iterable}"
        else:  # list
            comp = f"[{target} for {iterator} in {iterable}"

        # Add condition if present
        if expr.condition:
            condition = self.generate_expression(expr.condition)
            comp += f" if {condition}"

        # Close bracket
        if expr.comprehension_type == "dict" or expr.comprehension_type == "set":
            comp += "}"
        elif expr.comprehension_type == "generator":
            comp += ")"
        else:
            comp += "]"

        return comp

    def generate_fstring(self, expr: IRFString) -> str:
        """
        Generate f-string / template literal.

        Example: f"Hello {name}, you are {age} years old"
        """
        result = 'f"'
        for part in expr.parts:
            if isinstance(part, str):
                # Static string part - escape quotes
                result += part.replace('"', '\\"')
            else:
                # Expression part
                result += "{" + self.generate_expression(part) + "}"
        result += '"'
        return result


# ============================================================================
# Public API
# ============================================================================


def generate_pw(module: IRModule) -> str:
    """
    Generate PW DSL 2.0 text from IR module.

    Args:
        module: IR module to generate from

    Returns:
        str: PW DSL 2.0 source code
    """
    generator = PWGenerator()
    return generator.generate(module)
