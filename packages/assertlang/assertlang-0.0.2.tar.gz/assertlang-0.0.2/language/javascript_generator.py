"""
JavaScript Generator: IR → Idiomatic JavaScript Code

This generator converts the universal Intermediate Representation (IR) into
production-quality, idiomatic JavaScript (ES2020+) code. It handles:

- Type annotations (JSDoc)
- Async/await patterns
- Contract runtime validation
- Proper imports and organization
- Clean formatting
- Exception handling (try/catch)
- Classes with properties, methods, constructors

Design Principles:
1. Idiomatic - Generate JavaScript-native code
2. Clean - Follow modern JS conventions
3. Contract-aware - Full contract support matching Python generator
4. Zero dependencies - Only uses Node.js built-ins (except contracts runtime)
"""

from __future__ import annotations

from typing import Dict, List, Optional, Set

from dsl.ir import (
    BinaryOperator,
    IRArray,
    IRAssignment,
    IRAwait,
    IRBinaryOp,
    IRBreak,
    IRCall,
    IRCatch,
    IRClass,
    IRComprehension,
    IRContractClause,
    IRContinue,
    IREnum,
    IREnumVariant,
    IRExpression,
    IRFor,
    IRForCStyle,
    IRFunction,
    IRIdentifier,
    IRIf,
    IRImport,
    IRIndex,
    IRLambda,
    IRLiteral,
    IRMap,
    IRModule,
    IROldExpr,
    IRParameter,
    IRPass,
    IRPatternMatch,
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
    IRWith,
    LiteralType,
    UnaryOperator,
)
from dsl.type_system import TypeSystem


class JavaScriptGenerator:
    """
    Generate idiomatic JavaScript code from IR.

    Converts language-agnostic IR into production-quality JavaScript with:
    - JSDoc type annotations
    - Contract runtime validation
    - Proper imports
    - Modern JS formatting
    """

    def __init__(self):
        self.type_system = TypeSystem()
        self.indent_level = 0
        self.indent_size = 4  # 4 spaces
        self.required_imports: Set[str] = set()
        self.variable_types: Dict[str, IRType] = {}
        self.property_types: Dict[str, IRType] = {}
        self.function_return_types: Dict[str, IRType] = {}
        self.method_return_types: Dict[str, Dict[str, IRType]] = {}
        self.current_class: Optional[str] = None

    # ========================================================================
    # Indentation Management
    # ========================================================================

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
    # Main Entry Point
    # ========================================================================

    def generate(self, module: IRModule) -> str:
        """
        Generate JavaScript code from IR module.

        Args:
            module: IR module to convert

        Returns:
            JavaScript source code as string
        """
        self.required_imports.clear()
        lines = []

        # Module docstring
        if module.metadata.get("doc"):
            lines.append(f'/**\n * {module.metadata["doc"]}\n */')
            lines.append("")

        # Collect required imports from types
        self._collect_imports(module)

        # Track function return types
        self._register_function_signatures(module)

        # Contract runtime import if needed
        if self.required_imports:
            for imp in sorted(self.required_imports):
                lines.append(imp)
            lines.append("")

        # User imports
        for imp in module.imports:
            lines.append(self.generate_import(imp))
        if module.imports:
            lines.append("")

        # Enums
        for enum in module.enums:
            lines.append(self.generate_enum(enum))
            lines.append("")
            lines.append("")

        # Type definitions (classes)
        for type_def in module.types:
            lines.append(self.generate_type_definition(type_def))
            lines.append("")
            lines.append("")

        # Classes
        for cls in module.classes:
            lines.append(self.generate_class(cls))
            lines.append("")
            lines.append("")

        # Module-level variables
        for var in module.module_vars:
            lines.append(self.generate_statement(var))
            lines.append("")

        # Functions
        for func in module.functions:
            lines.append(self.generate_function(func))
            lines.append("")
            lines.append("")

        # Clean up and return
        result = "\n".join(lines)
        # Remove excessive blank lines
        while "\n\n\n\n" in result:
            result = result.replace("\n\n\n\n", "\n\n\n")
        return result.rstrip() + "\n"

    # ========================================================================
    # Import Collection and Generation
    # ========================================================================

    def _register_function_signatures(self, module: IRModule) -> None:
        """Register function and method return types."""
        for func in module.functions:
            if func.return_type:
                self.function_return_types[func.name] = func.return_type

        for cls in module.classes:
            if cls.name not in self.method_return_types:
                self.method_return_types[cls.name] = {}

            for method in cls.methods:
                if method.return_type:
                    self.method_return_types[cls.name][method.name] = method.return_type

    def _collect_imports(self, module: IRModule) -> None:
        """Collect all required imports from contract usage."""
        # Check if any functions have contracts
        for func in module.functions:
            if func.requires or func.ensures:
                # Add contract runtime import
                self.required_imports.add("const { ContractViolationError, shouldCheckPreconditions, shouldCheckPostconditions } = require('./contracts.js');")
                break

        # Check classes
        for cls in module.classes:
            for method in cls.methods:
                if method.requires or method.ensures:
                    self.required_imports.add("const { ContractViolationError, shouldCheckPreconditions, shouldCheckPostconditions } = require('./contracts.js');")
                    break
            if cls.invariants:
                self.required_imports.add("const { ContractViolationError, shouldCheckPreconditions, shouldCheckPostconditions } = require('./contracts.js');")

    def generate_import(self, imp: IRImport) -> str:
        """Generate JavaScript import statement."""
        if imp.items:
            # const { item1, item2 } = require('module')
            items = ", ".join(imp.items)
            return f"const {{ {items} }} = require('{imp.module}');"
        elif imp.alias:
            # const alias = require('module')
            return f"const {imp.alias} = require('{imp.module}');"
        else:
            # const module = require('module')
            return f"const {imp.module.split('/')[-1]} = require('{imp.module}');"

    # ========================================================================
    # Type Generation
    # ========================================================================

    def generate_type(self, ir_type: IRType) -> str:
        """Generate JSDoc type annotation from IR type."""
        # Map IR types to JS/JSDoc types
        type_map = {
            'int': 'number',
            'float': 'number',
            'string': 'string',
            'bool': 'boolean',
            'void': 'undefined',
            'any': 'any',
            'null': 'null',
            'list': 'Array',
            'array': 'Array',
            'map': 'Object',
            'dict': 'Object',
        }

        base_type = type_map.get(ir_type.name, ir_type.name)

        # Handle generic types
        if ir_type.generic_args:
            args = ', '.join(self.generate_type(arg) for arg in ir_type.generic_args)
            return f"{base_type}<{args}>"

        return base_type

    # ========================================================================
    # Enum and Type Definition Generation
    # ========================================================================

    def generate_enum(self, enum: IREnum) -> str:
        """Generate JavaScript enum (as object with variants)."""
        lines = []

        if enum.doc:
            lines.append(f"/**\n * {enum.doc}\n */")

        # Simple enum (non-generic)
        if not enum.generic_params:
            lines.append(f"const {enum.name} = {{")
            self.increase_indent()

            for variant in enum.variants:
                if variant.value is not None:
                    if isinstance(variant.value, str):
                        lines.append(f'{self.indent()}{variant.name}: "{variant.value}",')
                    else:
                        lines.append(f'{self.indent()}{variant.name}: {variant.value},')
                else:
                    lines.append(f'{self.indent()}{variant.name}: "{variant.name}",')

            self.decrease_indent()
            lines.append("};")
            return "\n".join(lines)

        # Generic enum (like Option<T>) - generate as classes
        lines = []
        for variant in enum.variants:
            if variant.associated_types:
                # Variant with data
                lines.append(f"class {variant.name} {{")
                self.increase_indent()

                lines.append(f"{self.indent()}constructor(value) {{")
                self.increase_indent()
                lines.append(f"{self.indent()}this.value = value;")
                self.decrease_indent()
                lines.append(f"{self.indent()}}}")

                self.decrease_indent()
                lines.append("}")
                lines.append("")
            else:
                # Variant without data
                variant_name = f"{variant.name}_" if variant.name in ("None", "True", "False") else variant.name
                lines.append(f"class {variant_name} {{")
                self.increase_indent()
                lines.append(f"{self.indent()}// Empty variant")
                self.decrease_indent()
                lines.append("}")
                lines.append("")

        return "\n".join(lines).rstrip()

    def generate_type_definition(self, type_def: IRTypeDefinition) -> str:
        """Generate JavaScript class for type definition."""
        lines = []

        if type_def.doc:
            lines.append(f"/**\n * {type_def.doc}\n */")

        lines.append(f"class {type_def.name} {{")
        self.increase_indent()

        # Constructor
        params = []
        assignments = []
        for field in type_def.fields:
            params.append(field.name)
            assignments.append(f"{self.indent()}this.{field.name} = {field.name};")

        lines.append(f"{self.indent()}constructor({', '.join(params)}) {{")
        self.increase_indent()
        for assignment in assignments:
            lines.append(assignment)
        self.decrease_indent()
        lines.append(f"{self.indent()}}}")

        self.decrease_indent()
        lines.append("}")

        return "\n".join(lines)

    # ========================================================================
    # Class Generation
    # ========================================================================

    def generate_class(self, cls: IRClass) -> str:
        """Generate JavaScript class."""
        lines = []

        self.current_class = cls.name

        # Register class properties
        for prop in cls.properties:
            if prop and hasattr(prop, 'prop_type'):
                self.property_types[prop.name] = prop.prop_type

        if cls.doc:
            lines.append(f"/**\n * {cls.doc}\n */")

        lines.append(f"class {cls.name} {{")
        self.increase_indent()

        # Constructor
        if cls.constructor:
            lines.append(self.generate_constructor(cls.constructor, cls.properties))
            lines.append("")

        # Methods
        for method in cls.methods:
            lines.append(self.generate_method(method))
            lines.append("")

        # Remove trailing empty line
        while lines and lines[-1] == "":
            lines.pop()

        self.decrease_indent()
        lines.append("}")

        self.property_types.clear()
        self.current_class = None

        return "\n".join(lines)

    def generate_constructor(self, constructor: IRFunction, properties: List[IRProperty]) -> str:
        """Generate constructor method."""
        lines = []

        params = [param.name for param in constructor.params]
        lines.append(f"{self.indent()}constructor({', '.join(params)}) {{")

        self.increase_indent()

        # Body
        if constructor.body:
            for i, stmt in enumerate(constructor.body):
                next_stmt = constructor.body[i + 1] if i + 1 < len(constructor.body) else None
                stmt_code = self.generate_statement(stmt, next_stmt)
                if stmt_code is not None:  # Skip None (IRMap workaround)
                    lines.append(stmt_code)
        else:
            lines.append(f"{self.indent()}// Empty constructor")

        self.decrease_indent()
        lines.append(f"{self.indent()}}}")

        return "\n".join(lines)

    def generate_method(self, method: IRFunction) -> str:
        """Generate class method."""
        lines = []

        # Register parameter types
        for param in method.params:
            self.variable_types[param.name] = param.param_type

        # Static method
        if method.is_static:
            prefix = "static "
        else:
            prefix = ""

        # Async
        func_def = f"{prefix}async " if method.is_async else prefix

        params = [param.name for param in method.params]
        lines.append(f"{self.indent()}{func_def}{method.name}({', '.join(params)}) {{")

        self.increase_indent()

        # Body
        if method.body:
            for i, stmt in enumerate(method.body):
                next_stmt = method.body[i + 1] if i + 1 < len(method.body) else None
                stmt_code = self.generate_statement(stmt, next_stmt)
                if stmt_code is not None:  # Skip None (IRMap workaround)
                    lines.append(stmt_code)
        else:
            lines.append(f"{self.indent()}// Empty method")

        self.decrease_indent()
        lines.append(f"{self.indent()}}}")

        return "\n".join(lines)

    # ========================================================================
    # Function Generation
    # ========================================================================

    def generate_function(self, func: IRFunction) -> str:
        """Generate standalone function with contract checks."""
        lines = []

        # Register parameter types
        for param in func.params:
            self.variable_types[param.name] = param.param_type

        # JSDoc comment
        if func.doc or func.params or func.return_type:
            lines.append("/**")
            if func.doc:
                lines.append(f" * {func.doc}")
            for param in func.params:
                param_type = self.generate_type(param.param_type)
                lines.append(f" * @param {{{param_type}}} {param.name}")
            if func.return_type:
                return_type = self.generate_type(func.return_type)
                lines.append(f" * @returns {{{return_type}}}")
            lines.append(" */")

        # Function signature
        func_def = "async function" if func.is_async else "function"
        params = [param.name for param in func.params]
        lines.append(f"{func_def} {func.name}({', '.join(params)}) {{")

        self.increase_indent()

        # Generate contract checks
        preconditions, postcondition_setup, postcondition_checks = self.generate_contract_checks(func)

        # Precondition checks
        for check in preconditions:
            lines.append(f"{self.indent()}{check}")

        # Capture old values
        for old_capture in postcondition_setup:
            lines.append(f"{self.indent()}{old_capture}")

        if postcondition_checks:
            # Wrap body in try/finally
            lines.append(f"{self.indent()}let __result;")
            lines.append(f"{self.indent()}try {{")
            self.increase_indent()

            # Body
            if func.body:
                for i, stmt in enumerate(func.body):
                    next_stmt = func.body[i + 1] if i + 1 < len(func.body) else None
                    stmt_code = self.generate_statement(stmt, next_stmt)
                    if stmt_code is not None:  # Skip None (IRMap workaround)
                        # Replace 'return X' with '__result = X'
                        if stmt_code.strip().startswith("return "):
                            return_val = stmt_code.strip()[7:-1] if stmt_code.strip().endswith(';') else stmt_code.strip()[7:]
                            lines.append(f"{self.indent()}__result = {return_val};")
                        else:
                            lines.append(stmt_code)
            else:
                lines.append(f"{self.indent()}// Empty function")

            self.decrease_indent()
            lines.append(f"{self.indent()}}} finally {{")
            self.increase_indent()

            # Postcondition checks
            for check in postcondition_checks:
                lines.append(f"{self.indent()}{check}")

            self.decrease_indent()
            lines.append(f"{self.indent()}}}")

            # Return result
            lines.append(f"{self.indent()}return __result;")
        else:
            # No postconditions, just body
            if func.body:
                for i, stmt in enumerate(func.body):
                    next_stmt = func.body[i + 1] if i + 1 < len(func.body) else None
                    stmt_code = self.generate_statement(stmt, next_stmt)
                    if stmt_code is not None:  # Skip None (IRMap workaround)
                        lines.append(stmt_code)
            else:
                lines.append(f"{self.indent()}// Empty function")

        self.decrease_indent()
        lines.append("}")

        # Clear variable types
        self.variable_types.clear()

        return "\n".join(lines)

    # ========================================================================
    # Contract Generation
    # ========================================================================

    def generate_contract_checks(self, func: IRFunction) -> tuple[List[str], List[str], List[str]]:
        """Generate contract checking code for a function."""
        precondition_lines = []
        postcondition_setup = []
        postcondition_checks = []

        # Preconditions
        if func.requires:
            for clause in func.requires:
                condition_expr = self.generate_expression(clause.expression)
                expr_str = self._expression_to_string(clause.expression)

                # Build context object
                context_items = []
                for param in func.params:
                    context_items.append(f"{param.name}")

                context_str = f"{{ {', '.join(context_items)} }}" if context_items else "{}"

                check = (
                    f"if (shouldCheckPreconditions()) {{\n"
                    f"{self.indent()}    if (!({condition_expr})) {{\n"
                    f"{self.indent()}        throw new ContractViolationError({{\n"
                    f"{self.indent()}            type: 'precondition',\n"
                    f"{self.indent()}            function: '{func.name}',\n"
                    f"{self.indent()}            clause: '{clause.name}',\n"
                    f"{self.indent()}            expression: '{expr_str}',\n"
                    f"{self.indent()}            context: {context_str}\n"
                    f"{self.indent()}        }});\n"
                    f"{self.indent()}    }}\n"
                    f"{self.indent()}}}"
                )
                precondition_lines.append(check)

        # Postconditions
        if func.ensures:
            # Find old expressions
            old_exprs = self._find_old_expressions(func.ensures)

            # Capture old values
            for old_expr in old_exprs:
                expr_code = self.generate_expression(old_expr)
                var_name = expr_code.replace(".", "_").replace("[", "_").replace("]", "").replace("(", "").replace(")", "")
                postcondition_setup.append(f"const __old_{var_name} = {expr_code};")

            # Generate postcondition checks
            for clause in func.ensures:
                condition_expr = self._replace_result_with_underscore(clause.expression)
                expr_str = self._expression_to_string(clause.expression)

                # Build context
                context_items = ["result: __result"]
                for param in func.params:
                    context_items.append(f"{param.name}: {param.name}")

                context_str = "{ " + ", ".join(context_items) + " }"

                check = (
                    f"if (shouldCheckPostconditions()) {{\n"
                    f"{self.indent()}        if (!({condition_expr})) {{\n"
                    f"{self.indent()}            throw new ContractViolationError({{\n"
                    f"{self.indent()}                type: 'postcondition',\n"
                    f"{self.indent()}                function: '{func.name}',\n"
                    f"{self.indent()}                clause: '{clause.name}',\n"
                    f"{self.indent()}                expression: '{expr_str}',\n"
                    f"{self.indent()}                context: {context_str}\n"
                    f"{self.indent()}            }});\n"
                    f"{self.indent()}        }}\n"
                    f"{self.indent()}    }}"
                )
                postcondition_checks.append(check)

        return precondition_lines, postcondition_setup, postcondition_checks

    def _find_old_expressions(self, clauses: List[IRContractClause]) -> List[IRExpression]:
        """Find all 'old' expressions in contract clauses."""
        old_exprs = []

        def visit_expr(expr: IRExpression):
            if isinstance(expr, IROldExpr):
                old_exprs.append(expr.expression)
            elif isinstance(expr, IRBinaryOp):
                visit_expr(expr.left)
                visit_expr(expr.right)
            elif isinstance(expr, IRUnaryOp):
                visit_expr(expr.operand)
            elif isinstance(expr, IRCall):
                for arg in expr.args:
                    visit_expr(arg)

        for clause in clauses:
            visit_expr(clause.expression)

        return old_exprs

    def _replace_result_with_underscore(self, expr: IRExpression) -> str:
        """Replace 'result' identifier with '__result'."""
        if isinstance(expr, IRIdentifier):
            if expr.name == "result":
                return "__result"
            return self.generate_expression(expr)
        elif isinstance(expr, IRBinaryOp):
            left = self._replace_result_with_underscore(expr.left)
            right = self._replace_result_with_underscore(expr.right)
            op_map = {
                BinaryOperator.ADD: "+",
                BinaryOperator.SUBTRACT: "-",
                BinaryOperator.MULTIPLY: "*",
                BinaryOperator.DIVIDE: "/",
                BinaryOperator.MODULO: "%",
                BinaryOperator.EQUAL: "===",
                BinaryOperator.NOT_EQUAL: "!==",
                BinaryOperator.LESS_THAN: "<",
                BinaryOperator.LESS_EQUAL: "<=",
                BinaryOperator.GREATER_THAN: ">",
                BinaryOperator.GREATER_EQUAL: ">=",
                BinaryOperator.AND: "&&",
                BinaryOperator.OR: "||",
            }
            op = op_map.get(expr.op, "+")
            return f"({left} {op} {right})"
        elif isinstance(expr, IROldExpr):
            return self.generate_old_expr(expr)
        else:
            return self.generate_expression(expr)

    def _expression_to_string(self, expr: IRExpression) -> str:
        """Convert expression to readable string for error messages."""
        if isinstance(expr, IRBinaryOp):
            left = self._expression_to_string(expr.left)
            right = self._expression_to_string(expr.right)
            return f"{left} {expr.op.value} {right}"
        elif isinstance(expr, IRIdentifier):
            return expr.name
        elif isinstance(expr, IRLiteral):
            if expr.literal_type == LiteralType.STRING:
                return f'"{expr.value}"'
            return str(expr.value)
        elif isinstance(expr, IROldExpr):
            inner = self._expression_to_string(expr.expression)
            return f"old {inner}"
        else:
            return "<expr>"

    def generate_old_expr(self, expr: IROldExpr) -> str:
        """Generate 'old' expression reference."""
        inner_expr = self.generate_expression(expr.expression)
        var_name = inner_expr.replace(".", "_").replace("[", "_").replace("]", "").replace("(", "").replace(")", "")
        return f"__old_{var_name}"

    # ========================================================================
    # Statement Generation
    # ========================================================================

    def generate_statement(self, stmt: IRStatement, next_stmt: IRStatement = None) -> str:
        """Generate JavaScript statement from IR."""
        if isinstance(stmt, IRAssignment):
            return self.generate_assignment(stmt, next_stmt)
        elif isinstance(stmt, IRIf):
            return self.generate_if(stmt)
        elif isinstance(stmt, IRFor):
            return self.generate_for(stmt)
        elif isinstance(stmt, IRForCStyle):
            return self.generate_for_c_style(stmt)
        elif isinstance(stmt, IRWhile):
            return self.generate_while(stmt)
        elif isinstance(stmt, IRTry):
            return self.generate_try(stmt)
        elif isinstance(stmt, IRReturn):
            return self.generate_return(stmt)
        elif isinstance(stmt, IRThrow):
            return self.generate_throw(stmt)
        elif isinstance(stmt, IRBreak):
            return f"{self.indent()}break;"
        elif isinstance(stmt, IRContinue):
            return f"{self.indent()}continue;"
        elif isinstance(stmt, IRPass):
            return f"{self.indent()}// pass"
        elif isinstance(stmt, IRCall):
            return f"{self.indent()}{self.generate_expression(stmt)};"
        elif isinstance(stmt, IRMap):
            # IRMap as statement is a parser bug workaround marker - skip it
            return None  # Signal to skip this statement
        else:
            return f"{self.indent()}// Unknown statement: {type(stmt).__name__}"

    def generate_assignment(self, stmt: IRAssignment, next_stmt: IRStatement = None) -> str:
        """Generate assignment statement."""
        # Check if next statement is IRMap (parser bug workaround for class initialization)
        if next_stmt and isinstance(next_stmt, IRMap) and isinstance(stmt.value, IRIdentifier):
            # For JavaScript, generate as object literal: const x = { field: value, ... }
            target = stmt.target if isinstance(stmt.target, str) else self.generate_expression(stmt.target)

            if next_stmt.entries:
                entries = []
                for key, val_expr in next_stmt.entries.items():
                    val = self.generate_expression(val_expr)
                    entries.append(f"{key}: {val}")
                obj_literal = "{ " + ", ".join(entries) + " }"
            else:
                obj_literal = "{}"

            # Track variable types
            if isinstance(stmt.target, str) and stmt.var_type:
                self.variable_types[stmt.target] = stmt.var_type

            if stmt.is_declaration:
                return f"{self.indent()}const {target} = {obj_literal};"
            else:
                return f"{self.indent()}{target} = {obj_literal};"

        # Normal assignment (existing code)
        value = self.generate_expression(stmt.value)
        target = stmt.target if isinstance(stmt.target, str) else self.generate_expression(stmt.target)

        # Track variable types
        if isinstance(stmt.target, str) and stmt.var_type:
            self.variable_types[stmt.target] = stmt.var_type

        # Use const for declarations, regular assignment otherwise
        if stmt.is_declaration:
            return f"{self.indent()}const {target} = {value};"
        else:
            return f"{self.indent()}{target} = {value};"

    def generate_if(self, stmt: IRIf) -> str:
        """Generate if statement."""
        lines = []

        condition = self.generate_expression(stmt.condition)
        lines.append(f"{self.indent()}if ({condition}) {{")

        self.increase_indent()
        if stmt.then_body:
            for i, s in enumerate(stmt.then_body):
                next_stmt = stmt.then_body[i + 1] if i + 1 < len(stmt.then_body) else None
                stmt_code = self.generate_statement(s, next_stmt)
                if stmt_code is not None:  # Skip None (IRMap workaround)
                    lines.append(stmt_code)
        else:
            lines.append(f"{self.indent()}// Empty")
        self.decrease_indent()

        if stmt.else_body:
            lines.append(f"{self.indent()}}} else {{")
            self.increase_indent()
            for i, s in enumerate(stmt.else_body):
                next_stmt = stmt.else_body[i + 1] if i + 1 < len(stmt.else_body) else None
                stmt_code = self.generate_statement(s, next_stmt)
                if stmt_code is not None:  # Skip None (IRMap workaround)
                    lines.append(stmt_code)
            self.decrease_indent()

        lines.append(f"{self.indent()}}}")

        return "\n".join(lines)

    def generate_for(self, stmt: IRFor) -> str:
        """Generate for loop."""
        lines = []

        iterable = self.generate_expression(stmt.iterable)
        lines.append(f"{self.indent()}for (const {stmt.iterator} of {iterable}) {{")

        self.increase_indent()
        if stmt.body:
            for i, s in enumerate(stmt.body):
                next_stmt = stmt.body[i + 1] if i + 1 < len(stmt.body) else None
                stmt_code = self.generate_statement(s, next_stmt)
                if stmt_code is not None:  # Skip None (IRMap workaround)
                    lines.append(stmt_code)
        else:
            lines.append(f"{self.indent()}// Empty")
        self.decrease_indent()

        lines.append(f"{self.indent()}}}")

        return "\n".join(lines)

    def generate_for_c_style(self, stmt: IRForCStyle) -> str:
        """Generate C-style for loop."""
        lines = []

        init = self.generate_statement(stmt.init).strip().rstrip(';')
        condition = self.generate_expression(stmt.condition)
        increment = self.generate_statement(stmt.increment).strip().rstrip(';')

        lines.append(f"{self.indent()}for ({init}; {condition}; {increment}) {{")

        self.increase_indent()
        if stmt.body:
            for i, s in enumerate(stmt.body):
                next_stmt = stmt.body[i + 1] if i + 1 < len(stmt.body) else None
                stmt_code = self.generate_statement(s, next_stmt)
                if stmt_code is not None:  # Skip None (IRMap workaround)
                    lines.append(stmt_code)
        else:
            lines.append(f"{self.indent()}// Empty")
        self.decrease_indent()

        lines.append(f"{self.indent()}}}")

        return "\n".join(lines)

    def generate_while(self, stmt: IRWhile) -> str:
        """Generate while loop."""
        lines = []

        condition = self.generate_expression(stmt.condition)
        lines.append(f"{self.indent()}while ({condition}) {{")

        self.increase_indent()
        if stmt.body:
            for i, s in enumerate(stmt.body):
                next_stmt = stmt.body[i + 1] if i + 1 < len(stmt.body) else None
                stmt_code = self.generate_statement(s, next_stmt)
                if stmt_code is not None:  # Skip None (IRMap workaround)
                    lines.append(stmt_code)
        else:
            lines.append(f"{self.indent()}// Empty")
        self.decrease_indent()

        lines.append(f"{self.indent()}}}")

        return "\n".join(lines)

    def generate_try(self, stmt: IRTry) -> str:
        """Generate try/catch statement."""
        lines = []

        lines.append(f"{self.indent()}try {{")
        self.increase_indent()
        if stmt.try_body:
            for i, s in enumerate(stmt.try_body):
                next_stmt = stmt.try_body[i + 1] if i + 1 < len(stmt.try_body) else None
                stmt_code = self.generate_statement(s, next_stmt)
                if stmt_code is not None:  # Skip None (IRMap workaround)
                    lines.append(stmt_code)
        else:
            lines.append(f"{self.indent()}// Empty")
        self.decrease_indent()

        for catch in stmt.catch_blocks:
            if catch.exception_type:
                lines.append(f"{self.indent()}}} catch ({catch.exception_var or 'e'}) {{")
            else:
                lines.append(f"{self.indent()}}} catch ({catch.exception_var or 'e'}) {{")

            self.increase_indent()
            if catch.body:
                for i, s in enumerate(catch.body):
                    next_stmt = catch.body[i + 1] if i + 1 < len(catch.body) else None
                    stmt_code = self.generate_statement(s, next_stmt)
                    if stmt_code is not None:  # Skip None (IRMap workaround)
                        lines.append(stmt_code)
            else:
                lines.append(f"{self.indent()}// Empty")
            self.decrease_indent()

        if stmt.finally_body:
            lines.append(f"{self.indent()}}} finally {{")
            self.increase_indent()
            for i, s in enumerate(stmt.finally_body):
                next_stmt = stmt.finally_body[i + 1] if i + 1 < len(stmt.finally_body) else None
                stmt_code = self.generate_statement(s, next_stmt)
                if stmt_code is not None:  # Skip None (IRMap workaround)
                    lines.append(stmt_code)
            self.decrease_indent()

        lines.append(f"{self.indent()}}}")

        return "\n".join(lines)

    def generate_return(self, stmt: IRReturn) -> str:
        """Generate return statement."""
        if stmt.value:
            value = self.generate_expression(stmt.value)
            return f"{self.indent()}return {value};"
        else:
            return f"{self.indent()}return;"

    def generate_throw(self, stmt: IRThrow) -> str:
        """Generate throw statement."""
        exception = self.generate_expression(stmt.exception)
        return f"{self.indent()}throw {exception};"

    # ========================================================================
    # Expression Generation
    # ========================================================================

    def generate_expression(self, expr: IRExpression) -> str:
        """Generate JavaScript expression from IR."""
        if isinstance(expr, IRLiteral):
            return self.generate_literal(expr)
        elif isinstance(expr, IRIdentifier):
            return expr.name
        elif isinstance(expr, IRAwait):
            inner = self.generate_expression(expr.expression)
            return f"await {inner}"
        elif isinstance(expr, IRBinaryOp):
            return self.generate_binary_op(expr)
        elif isinstance(expr, IRUnaryOp):
            return self.generate_unary_op(expr)
        elif isinstance(expr, IRCall):
            return self.generate_call(expr)
        elif isinstance(expr, IRPropertyAccess):
            obj = self.generate_expression(expr.object)
            if expr.property == "length":
                return f"{obj}.length"
            return f"{obj}.{expr.property}"
        elif isinstance(expr, IRIndex):
            obj = self.generate_expression(expr.object)
            index = self.generate_expression(expr.index)
            return f"{obj}[{index}]"
        elif isinstance(expr, IRArray):
            return self.generate_array(expr)
        elif isinstance(expr, IRMap):
            return self.generate_map(expr)
        elif isinstance(expr, IRTernary):
            return self.generate_ternary(expr)
        elif isinstance(expr, IRLambda):
            return self.generate_lambda(expr)
        elif isinstance(expr, IROldExpr):
            return self.generate_old_expr(expr)
        else:
            return f"/* unknown: {type(expr).__name__} */"

    def generate_literal(self, lit: IRLiteral) -> str:
        """Generate JavaScript literal."""
        if lit.literal_type == LiteralType.STRING:
            value = str(lit.value).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
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

        op_map = {
            BinaryOperator.ADD: "+",
            BinaryOperator.SUBTRACT: "-",
            BinaryOperator.MULTIPLY: "*",
            BinaryOperator.DIVIDE: "/",
            BinaryOperator.MODULO: "%",
            BinaryOperator.POWER: "**",
            BinaryOperator.FLOOR_DIVIDE: "//",
            BinaryOperator.EQUAL: "===",
            BinaryOperator.NOT_EQUAL: "!==",
            BinaryOperator.LESS_THAN: "<",
            BinaryOperator.LESS_EQUAL: "<=",
            BinaryOperator.GREATER_THAN: ">",
            BinaryOperator.GREATER_EQUAL: ">=",
            BinaryOperator.AND: "&&",
            BinaryOperator.OR: "||",
            BinaryOperator.BIT_AND: "&",
            BinaryOperator.BIT_OR: "|",
            BinaryOperator.BIT_XOR: "^",
        }

        op = op_map.get(expr.op, "+")
        return f"({left} {op} {right})"

    def generate_unary_op(self, expr: IRUnaryOp) -> str:
        """Generate unary operation."""
        operand = self.generate_expression(expr.operand)

        if expr.op == UnaryOperator.NOT:
            return f"!{operand}"
        elif expr.op == UnaryOperator.NEGATE:
            return f"-{operand}"
        elif expr.op == UnaryOperator.POSITIVE:
            return f"+{operand}"
        else:
            return operand

    def generate_call(self, expr: IRCall) -> str:
        """Generate function call."""
        # STDLIB TRANSLATION: Translate stdlib calls to JavaScript equivalents
        if isinstance(expr.function, IRPropertyAccess):
            obj = expr.function.object
            method = expr.function.property

            # str.length(x) → x.length
            if isinstance(obj, IRIdentifier) and obj.name == "str" and method == "length":
                if len(expr.args) == 1:
                    arg = self.generate_expression(expr.args[0])
                    return f"{arg}.length"

            # str.contains(s, substr) → s.includes(substr)
            if isinstance(obj, IRIdentifier) and obj.name == "str" and method == "contains":
                if len(expr.args) == 2:
                    string_arg = self.generate_expression(expr.args[0])
                    substr_arg = self.generate_expression(expr.args[1])
                    return f"{string_arg}.includes({substr_arg})"

        func = self.generate_expression(expr.function)
        args = [self.generate_expression(arg) for arg in expr.args]
        return f"{func}({', '.join(args)})"

    def generate_array(self, expr: IRArray) -> str:
        """Generate array literal."""
        elements = [self.generate_expression(el) for el in expr.elements]
        return f"[{', '.join(elements)}]"

    def generate_map(self, expr: IRMap) -> str:
        """Generate object literal."""
        if not expr.entries:
            return "{}"

        entries = [f'{k}: {self.generate_expression(v)}' for k, v in expr.entries.items()]
        return "{ " + ", ".join(entries) + " }"

    def generate_ternary(self, expr: IRTernary) -> str:
        """Generate ternary expression."""
        cond = self.generate_expression(expr.condition)
        true_val = self.generate_expression(expr.true_value)
        false_val = self.generate_expression(expr.false_value)
        return f"{cond} ? {true_val} : {false_val}"

    def generate_lambda(self, expr: IRLambda) -> str:
        """Generate arrow function."""
        params = ", ".join(p.name for p in expr.params)

        if isinstance(expr.body, list):
            return f"({params}) => {{ /* multi-statement */ }}"
        else:
            body = self.generate_expression(expr.body)
            return f"({params}) => {body}"


# ============================================================================
# Public API
# ============================================================================


def generate_javascript(module: IRModule) -> str:
    """
    Generate JavaScript code from IR module.

    Args:
        module: IR module to convert

    Returns:
        JavaScript source code as string
    """
    generator = JavaScriptGenerator()
    return generator.generate(module)
