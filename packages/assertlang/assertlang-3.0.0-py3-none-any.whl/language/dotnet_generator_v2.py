"""
.NET Generator V2 - IR to Idiomatic C# Code

Converts Promptware IR into production-quality, idiomatic C# code.

This generator:
- Produces idiomatic C# with proper conventions
- Handles async/await patterns
- Maps LINQ expressions naturally
- Generates properties with auto-property syntax
- Follows C# naming conventions (PascalCase for public members)
- Uses nullable reference types (C# 8.0+)
- Generates proper namespace and using directives

Design Principles:
1. Idiomatic C# - Code that looks hand-written by a C# developer
2. Type Safety - Leverage C#'s strong type system
3. Modern Syntax - Use C# 8.0+ features (nullable, records, etc.)
4. Readability - Clean, well-formatted code with proper indentation
5. Completeness - Handle all IR node types
"""

from __future__ import annotations

from typing import List, Optional, Set

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
    UnaryOperator,
)
from dsl.type_system import TypeSystem
from language.library_mapping import LibraryMapper


class DotNetGeneratorV2:
    """
    Generate idiomatic C# code from Promptware IR.

    Supports:
    - Classes with properties (auto-properties)
    - Methods and constructors
    - Async/await patterns
    - LINQ expressions (abstracted as operations)
    - Full type system with nullable reference types
    - Proper namespace and using directives
    - Exception handling
    - All IR statement and expression types
    """

    def __init__(self, namespace: str = "Generated", indent_size: int = 4):
        """
        Initialize the generator.

        Args:
            namespace: Default namespace for generated code
            indent_size: Number of spaces per indent level (C# standard: 4)
        """
        self.namespace = namespace
        self.indent_size = indent_size
        self.indent_level = 0
        self.type_system = TypeSystem()
        self.library_mapper = LibraryMapper()
        self.variable_types: dict[str, IRType] = {}  # Track variable types for safe map indexing
        self.required_imports: Set[str] = set()
        self.source_language: Optional[str] = None  # Track source language for mapping

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
        Generate C# code from IR module.

        Args:
            module: IR module to generate from

        Returns:
            Complete C# source code
        """
        # Reset state
        self.required_imports = set()
        self.indent_level = 0

        lines = []

        # Generate using directives
        self._collect_imports(module)
        using_lines = self._generate_using_directives(module)
        if using_lines:
            lines.extend(using_lines)
            lines.append("")

        # Generate namespace
        # Use module name in PascalCase if namespace is default "Generated"
        if self.namespace == "Generated":
            namespace_name = self._to_pascal_case(module.name)
        else:
            namespace_name = self.namespace
        lines.append(f"namespace {namespace_name}")
        lines.append("{")
        self.increase_indent()

        # Generate type definitions
        for type_def in module.types:
            lines.extend(self._generate_type_definition(type_def))
            lines.append("")

        # Generate enums
        for enum in module.enums:
            lines.extend(self._generate_enum(enum))
            lines.append("")

        # Generate classes
        for cls in module.classes:
            if cls is None:
                continue
            lines.extend(self._generate_class(cls))
            lines.append("")

        # Generate standalone functions (as static class)
        if module.functions:
            lines.extend(self._generate_functions_class(module.functions))
            lines.append("")

        self.decrease_indent()
        lines.append("}")

        # Join and clean up
        result = "\n".join(lines)
        # Remove excessive blank lines
        while "\n\n\n" in result:
            result = result.replace("\n\n\n", "\n\n")
        return result.strip() + "\n"

    # ========================================================================
    # Import/Using Directive Generation
    # ========================================================================

    def _collect_imports(self, module: IRModule) -> None:
        """Collect all required using directives."""
        # Standard imports
        self.required_imports.add("using System;")

        # Check for collections
        for cls in module.classes:
            if cls is None:
                continue
            for prop in cls.properties:
                if prop is not None and prop.prop_type:
                    self._check_type_imports(prop.prop_type)
            for method in cls.methods:
                if method.return_type:
                    self._check_type_imports(method.return_type)
                for param in method.params:
                    self._check_type_imports(param.param_type)

        # Check for async
        for cls in module.classes:
            if cls is None:
                continue
            for method in cls.methods:
                if method.is_async:
                    self.required_imports.add("using System.Threading.Tasks;")
                    break

    def _check_type_imports(self, ir_type: IRType) -> None:
        """Check if type requires imports."""
        lang_type = self.type_system.map_to_language(ir_type, "dotnet")

        # Collections
        if "List" in lang_type or "Dictionary" in lang_type:
            self.required_imports.add("using System.Collections.Generic;")

        # LINQ
        if "IEnumerable" in lang_type:
            self.required_imports.add("using System.Linq;")

        # Check generic args
        for arg in ir_type.generic_args:
            self._check_type_imports(arg)

    def _generate_using_directives(self, module: IRModule) -> List[str]:
        """Generate using directives."""
        lines = []

        # Add collected imports
        for using in sorted(self.required_imports):
            lines.append(using)

        # Add module-specific imports
        for imp in module.imports:
            # Map IR imports to C# using directives with library mapping
            module_name = imp.module
            comment = ""
            if self.source_language and self.source_language != "csharp":
                translated = self.library_mapper.translate_import(
                    imp.module,
                    from_lang=self.source_language,
                    to_lang="csharp"
                )
                if translated:
                    module_name = translated["module"]
                    comment = f"  // from {self.source_language}: {imp.module}"

            if imp.alias:
                lines.append(f"using {imp.alias} = {module_name};{comment}")
            else:
                lines.append(f"using {module_name};{comment}")

        return lines

    # ========================================================================
    # Type Definition Generation
    # ========================================================================

    def _generate_type_definition(self, type_def: IRTypeDefinition) -> List[str]:
        """Generate class for type definition (DTO/POCO)."""
        lines = []

        # Doc comment
        if type_def.doc:
            lines.append(f"{self.indent()}/// <summary>")
            lines.append(f"{self.indent()}/// {type_def.doc}")
            lines.append(f"{self.indent()}/// </summary>")

        # Class declaration
        class_name = self._to_pascal_case(type_def.name)
        lines.append(f"{self.indent()}public class {class_name}")
        lines.append(f"{self.indent()}{{")
        self.increase_indent()

        # Properties (auto-properties)
        for field in type_def.fields:
            prop_name = self._to_pascal_case(field.name)
            prop_type = self._generate_type(field.prop_type)

            # Auto-property with initializer
            if field.default_value:
                default_val = self._generate_expression(field.default_value)
                lines.append(f"{self.indent()}public {prop_type} {prop_name} {{ get; set; }} = {default_val};")
            else:
                lines.append(f"{self.indent()}public {prop_type} {prop_name} {{ get; set; }}")

        self.decrease_indent()
        lines.append(f"{self.indent()}}}")

        return lines

    def _generate_enum(self, enum: IREnum) -> List[str]:
        """Generate enum definition."""
        lines = []

        # Doc comment
        if enum.doc:
            lines.append(f"{self.indent()}/// <summary>")
            lines.append(f"{self.indent()}/// {enum.doc}")
            lines.append(f"{self.indent()}/// </summary>")

        # Enum declaration
        enum_name = self._to_pascal_case(enum.name)
        lines.append(f"{self.indent()}public enum {enum_name}")
        lines.append(f"{self.indent()}{{")
        self.increase_indent()

        # Variants
        for i, variant in enumerate(enum.variants):
            variant_name = self._to_pascal_case(variant.name)
            if variant.value is not None:
                lines.append(f"{self.indent()}{variant_name} = {variant.value},")
            else:
                lines.append(f"{self.indent()}{variant_name},")

        self.decrease_indent()
        lines.append(f"{self.indent()}}}")

        return lines

    # ========================================================================
    # Class Generation
    # ========================================================================

    def _generate_class(self, cls: IRClass) -> List[str]:
        """Generate class definition."""
        lines = []

        # Doc comment
        if cls.doc:
            lines.append(f"{self.indent()}/// <summary>")
            lines.append(f"{self.indent()}/// {cls.doc}")
            lines.append(f"{self.indent()}/// </summary>")

        # Class declaration with base classes
        class_name = self._to_pascal_case(cls.name)
        if cls.base_classes:
            base_list = ", ".join(self._to_pascal_case(b) for b in cls.base_classes)
            lines.append(f"{self.indent()}public class {class_name} : {base_list}")
        else:
            lines.append(f"{self.indent()}public class {class_name}")

        lines.append(f"{self.indent()}{{")
        self.increase_indent()

        # Properties
        for prop in cls.properties:
            if prop is not None:
                lines.extend(self._generate_property(prop))
                lines.append("")

        # Constructor
        if cls.constructor:
            lines.extend(self._generate_constructor(cls.constructor, class_name))
            lines.append("")

        # Methods
        for method in cls.methods:
            lines.extend(self._generate_method(method))
            lines.append("")

        self.decrease_indent()
        lines.append(f"{self.indent()}}}")

        return lines

    def _generate_property(self, prop: IRProperty) -> List[str]:
        """Generate property declaration."""
        lines = []

        prop_name = self._to_pascal_case(prop.name)
        prop_type = self._generate_type(prop.prop_type)

        # Access modifier
        access = "private" if prop.is_private else "public"

        # Auto-property with initializer
        if prop.default_value:
            default_val = self._generate_expression(prop.default_value)
            if prop.is_readonly:
                lines.append(f"{self.indent()}{access} {prop_type} {prop_name} {{ get; }} = {default_val};")
            else:
                lines.append(f"{self.indent()}{access} {prop_type} {prop_name} {{ get; set; }} = {default_val};")
        else:
            if prop.is_readonly:
                lines.append(f"{self.indent()}{access} {prop_type} {prop_name} {{ get; }}")
            else:
                lines.append(f"{self.indent()}{access} {prop_type} {prop_name} {{ get; set; }}")

        return lines

    def _generate_constructor(self, ctor: IRFunction, class_name: str) -> List[str]:
        """Generate constructor."""
        lines = []

        # Doc comment
        if ctor.doc:
            lines.append(f"{self.indent()}/// <summary>")
            lines.append(f"{self.indent()}/// {ctor.doc}")
            lines.append(f"{self.indent()}/// </summary>")

        # Constructor signature
        params_str = self._generate_parameters(ctor.params)
        lines.append(f"{self.indent()}public {class_name}({params_str})")
        lines.append(f"{self.indent()}{{")
        self.increase_indent()

        # Body
        for stmt in ctor.body:
            lines.extend(self._generate_statement(stmt))

        self.decrease_indent()
        lines.append(f"{self.indent()}}}")

        return lines

    def _generate_method(self, method: IRFunction) -> List[str]:
        """Generate method definition."""
        lines = []

        # Register parameter types for safe map/array indexing
        for param in method.params:
            self.variable_types[param.name] = param.param_type

        # Doc comment
        if method.doc:
            lines.append(f"{self.indent()}/// <summary>")
            lines.append(f"{self.indent()}/// {method.doc}")
            lines.append(f"{self.indent()}/// </summary>")

        # Access modifier
        access = "private" if method.is_private else "public"
        static = "static " if method.is_static else ""
        async_kw = "async " if method.is_async else ""

        # Return type
        if method.return_type:
            if method.is_async:
                return_type = f"Task<{self._generate_type(method.return_type)}>"
            else:
                return_type = self._generate_type(method.return_type)
        else:
            if method.is_async:
                return_type = "Task"
            else:
                return_type = "void"

        # Method signature
        method_name = self._to_pascal_case(method.name)
        params_str = self._generate_parameters(method.params)
        lines.append(f"{self.indent()}{access} {static}{async_kw}{return_type} {method_name}({params_str})")
        lines.append(f"{self.indent()}{{")
        self.increase_indent()

        # Body
        for stmt in method.body:
            lines.extend(self._generate_statement(stmt))

        self.decrease_indent()
        lines.append(f"{self.indent()}}}")

        # Clear variable types for this function scope
        self.variable_types.clear()

        return lines

    def _generate_functions_class(self, functions: List[IRFunction]) -> List[str]:
        """Generate static class for standalone functions."""
        lines = []

        lines.append(f"{self.indent()}public static class Functions")
        lines.append(f"{self.indent()}{{")
        self.increase_indent()

        for func in functions:
            # Force static for standalone functions
            func.is_static = True
            lines.extend(self._generate_method(func))
            lines.append("")

        self.decrease_indent()
        lines.append(f"{self.indent()}}}")

        return lines

    # ========================================================================
    # Type Generation
    # ========================================================================

    def _generate_type(self, ir_type: IRType) -> str:
        """
        Generate C# type from IR type.

        Examples:
        - string → string
        - int → int
        - array<string> → List<string>
        - map<string, int> → Dictionary<string, int>
        - int? → int?
        """
        # Use type system for mapping
        lang_type = self.type_system.map_to_language(ir_type, "dotnet")

        # If it's a custom type (not primitive), convert to PascalCase
        # Primitives: string, int, double, bool, null, object
        primitives = {"string", "int", "double", "bool", "null", "object", "void", "int?", "double?", "bool?"}

        # Extract base type (remove ? suffix for checking)
        base_type = lang_type.rstrip("?")

        # Check if it's a custom type (not primitive or standard library type)
        if base_type not in primitives and not lang_type.startswith(("List", "Dictionary", "Task")):
            # It's a custom type, convert to PascalCase
            lang_type = self._to_pascal_case(lang_type)

        return lang_type

    def _generate_parameters(self, params: List[IRParameter]) -> str:
        """Generate parameter list for method signature."""
        param_strs = []

        for param in params:
            param_type = self._generate_type(param.param_type)
            param_name = self._to_camel_case(param.name)

            if param.default_value:
                default_val = self._generate_expression(param.default_value)
                param_strs.append(f"{param_type} {param_name} = {default_val}")
            else:
                param_strs.append(f"{param_type} {param_name}")

        return ", ".join(param_strs)

    # ========================================================================
    # Statement Generation
    # ========================================================================

    def _generate_statement(self, stmt: IRStatement) -> List[str]:
        """Generate C# statement from IR statement."""
        if isinstance(stmt, IRAssignment):
            return self._generate_assignment(stmt)
        elif isinstance(stmt, IRIf):
            return self._generate_if(stmt)
        elif isinstance(stmt, IRForCStyle):
            return self._generate_for_c_style(stmt)
        elif isinstance(stmt, IRFor):
            return self._generate_for(stmt)
        elif isinstance(stmt, IRWhile):
            return self._generate_while(stmt)
        elif isinstance(stmt, IRTry):
            return self._generate_try(stmt)
        elif isinstance(stmt, IRReturn):
            return self._generate_return(stmt)
        elif isinstance(stmt, IRThrow):
            return self._generate_throw(stmt)
        elif isinstance(stmt, IRBreak):
            return [f"{self.indent()}break;"]
        elif isinstance(stmt, IRContinue):
            return [f"{self.indent()}continue;"]
        elif isinstance(stmt, IRPass):
            return [f"{self.indent()}// pass"]
        elif isinstance(stmt, IRCall):
            # Expression statement
            expr = self._generate_expression(stmt)
            # Handle await for async calls
            if self._is_async_call(stmt):
                return [f"{self.indent()}await {expr};"]
            return [f"{self.indent()}{expr};"]
        else:
            return [f"{self.indent()}// Unknown statement: {type(stmt).__name__}"]

    def _generate_assignment(self, stmt: IRAssignment) -> List[str]:
        """Generate assignment statement."""
        value = self._generate_expression(stmt.value)

        # Generate target (could be variable or property access)
        if stmt.target:
            if isinstance(stmt.target, str):
                target = self._to_camel_case(stmt.target)
            elif isinstance(stmt.target, IRIndex):
                # Special case: Index assignment (map[key] = value or arr[i] = value)
                # Use direct bracket notation for assignment (don't use ContainsKey check)
                obj = self._generate_expression(stmt.target.object)
                idx = self._generate_expression(stmt.target.index)
                target = f"{obj}[{idx}]"
            else:
                # Target is an expression (property access, etc.)
                target = self._generate_expression(stmt.target)
        else:
            target = "_unknown"

        # Handle await for async values
        if self._is_async_expression(stmt.value):
            value = f"await {value}"

        if stmt.is_declaration:
            if stmt.var_type:
                var_type = self._generate_type(stmt.var_type)
                return [f"{self.indent()}{var_type} {target} = {value};"]
            else:
                return [f"{self.indent()}var {target} = {value};"]
        else:
            return [f"{self.indent()}{target} = {value};"]

    def _generate_if(self, stmt: IRIf) -> List[str]:
        """Generate if statement."""
        lines = []

        condition = self._generate_expression(stmt.condition)
        lines.append(f"{self.indent()}if ({condition})")
        lines.append(f"{self.indent()}{{")
        self.increase_indent()

        for s in stmt.then_body:
            lines.extend(self._generate_statement(s))

        self.decrease_indent()
        lines.append(f"{self.indent()}}}")

        if stmt.else_body:
            lines.append(f"{self.indent()}else")
            lines.append(f"{self.indent()}{{")
            self.increase_indent()

            for s in stmt.else_body:
                lines.extend(self._generate_statement(s))

            self.decrease_indent()
            lines.append(f"{self.indent()}}}")

        return lines

    def _generate_for(self, stmt: IRFor) -> List[str]:
        """Generate foreach loop."""
        lines = []

        iterator = self._to_camel_case(stmt.iterator)
        iterable = self._generate_expression(stmt.iterable)

        lines.append(f"{self.indent()}foreach (var {iterator} in {iterable})")
        lines.append(f"{self.indent()}{{")
        self.increase_indent()

        for s in stmt.body:
            lines.extend(self._generate_statement(s))

        self.decrease_indent()
        lines.append(f"{self.indent()}}}")

        return lines

    def _generate_for_c_style(self, stmt: IRForCStyle) -> List[str]:
        """
        Generate C-style for loop (C# supports this natively).

        Example:
            for (int i = 0; i < 10; i = i + 1)
            {
                ...
            }
        """
        lines = []

        # Generate init statement
        init_lines = self._generate_statement(stmt.init)
        init_str = init_lines[0].strip() if init_lines else ""

        # Generate condition
        condition = self._generate_expression(stmt.condition)

        # Generate increment
        increment_lines = self._generate_statement(stmt.increment)
        increment_str = increment_lines[0].strip() if increment_lines else ""

        # Build for loop header
        lines.append(f"{self.indent()}for ({init_str}; {condition}; {increment_str})")
        lines.append(f"{self.indent()}{{")
        self.increase_indent()

        for s in stmt.body:
            lines.extend(self._generate_statement(s))

        self.decrease_indent()
        lines.append(f"{self.indent()}}}")

        return lines

    def _generate_while(self, stmt: IRWhile) -> List[str]:
        """Generate while loop."""
        lines = []

        condition = self._generate_expression(stmt.condition)
        lines.append(f"{self.indent()}while ({condition})")
        lines.append(f"{self.indent()}{{")
        self.increase_indent()

        for s in stmt.body:
            lines.extend(self._generate_statement(s))

        self.decrease_indent()
        lines.append(f"{self.indent()}}}")

        return lines

    def _generate_try(self, stmt: IRTry) -> List[str]:
        """Generate try-catch statement."""
        lines = []

        lines.append(f"{self.indent()}try")
        lines.append(f"{self.indent()}{{")
        self.increase_indent()

        for s in stmt.try_body:
            lines.extend(self._generate_statement(s))

        self.decrease_indent()
        lines.append(f"{self.indent()}}}")

        # Catch blocks
        for catch in stmt.catch_blocks:
            if catch.exception_type:
                # Handle both IRType objects and string types
                if hasattr(catch.exception_type, 'name'):
                    ex_type = self._to_pascal_case(catch.exception_type.name)
                else:
                    ex_type = self._to_pascal_case(str(catch.exception_type))

                if catch.exception_var:
                    ex_var = self._to_camel_case(catch.exception_var)
                    lines.append(f"{self.indent()}catch ({ex_type} {ex_var})")
                else:
                    lines.append(f"{self.indent()}catch ({ex_type})")
            else:
                lines.append(f"{self.indent()}catch")

            lines.append(f"{self.indent()}{{")
            self.increase_indent()

            for s in catch.body:
                lines.extend(self._generate_statement(s))

            self.decrease_indent()
            lines.append(f"{self.indent()}}}")

        # Finally block
        if stmt.finally_body:
            lines.append(f"{self.indent()}finally")
            lines.append(f"{self.indent()}{{")
            self.increase_indent()

            for s in stmt.finally_body:
                lines.extend(self._generate_statement(s))

            self.decrease_indent()
            lines.append(f"{self.indent()}}}")

        return lines

    def _generate_return(self, stmt: IRReturn) -> List[str]:
        """Generate return statement."""
        if stmt.value:
            value = self._generate_expression(stmt.value)
            # Handle await
            if self._is_async_expression(stmt.value):
                value = f"await {value}"
            return [f"{self.indent()}return {value};"]
        else:
            return [f"{self.indent()}return;"]

    def _generate_throw(self, stmt: IRThrow) -> List[str]:
        """Generate throw statement."""
        exception = self._generate_expression(stmt.exception)
        return [f"{self.indent()}throw {exception};"]

    # ========================================================================
    # Expression Generation
    # ========================================================================

    def _generate_expression(self, expr: IRExpression) -> str:
        """Generate C# expression from IR expression."""
        if isinstance(expr, IRLiteral):
            return self._generate_literal(expr)
        elif isinstance(expr, IRIdentifier):
            return self._to_camel_case(expr.name)
        elif isinstance(expr, IRAwait):
            # C# uses await keyword (same as Python/JavaScript)
            inner = self._generate_expression(expr.expression)
            return f"await {inner}"
        elif isinstance(expr, IRBinaryOp):
            return self._generate_binary_op(expr)
        elif isinstance(expr, IRUnaryOp):
            return self._generate_unary_op(expr)
        elif isinstance(expr, IRCall):
            return self._generate_call(expr)
        elif isinstance(expr, IRPropertyAccess):
            obj = self._generate_expression(expr.object)
            # Special case: .length property
            # In C#: strings and arrays use .Length, but List<T> uses .Count
            # Since PW arrays map to List<T>, we use .Count for better compatibility
            # Note: This won't work for string.length - that's a known limitation
            if expr.property == "length":
                return f"{obj}.Count"
            prop = self._to_pascal_case(expr.property)
            return f"{obj}.{prop}"
        elif isinstance(expr, IRIndex):
            obj = self._generate_expression(expr.object)
            idx = self._generate_expression(expr.index)

            # Determine if object is a map/Dictionary (use TryGetValue or ContainsKey) or array/List (use [index])
            is_map = False

            # Check if object is an identifier with known type
            if isinstance(expr.object, IRIdentifier):
                var_name = expr.object.name
                if var_name in self.variable_types:
                    var_type = self.variable_types[var_name]
                    # Check if type is "map" or "Dictionary"
                    if var_type.name in ("map", "dict", "Dict", "Dictionary", "dictionary"):
                        is_map = True

            # If not determined by variable type, use index type as heuristic
            if not is_map and isinstance(expr.index, IRLiteral) and expr.index.literal_type == LiteralType.STRING:
                # String key → likely map/dict access
                is_map = True

            # Generate safe map access with null coalescing or regular array access
            if is_map:
                # C# Dictionary: use ContainsKey() ? dict[key] : null pattern
                # Or use TryGetValue, but that's more complex
                # For now, use the ternary pattern that matches other generators
                return f"({obj}.ContainsKey({idx}) ? {obj}[{idx}] : null)"
            else:
                return f"{obj}[{idx}]"
        elif isinstance(expr, IRArray):
            return self._generate_array(expr)
        elif isinstance(expr, IRMap):
            return self._generate_map(expr)
        elif isinstance(expr, IRTernary):
            return self._generate_ternary(expr)
        elif isinstance(expr, IRLambda):
            return self._generate_lambda(expr)
        elif isinstance(expr, IRComprehension):
            return self._generate_comprehension(expr)
        else:
            # Unknown expression type - generate valid null fallback
            return "null"

    def _generate_literal(self, lit: IRLiteral) -> str:
        """Generate literal value."""
        if lit.literal_type == LiteralType.STRING:
            # Escape string
            value = str(lit.value).replace("\\", "\\\\").replace('"', '\\"')
            return f'"{value}"'
        elif lit.literal_type == LiteralType.INTEGER:
            return str(lit.value)
        elif lit.literal_type == LiteralType.FLOAT:
            # C# requires 'd' suffix for double or 'f' for float
            return f"{lit.value}d"
        elif lit.literal_type == LiteralType.BOOLEAN:
            return "true" if lit.value else "false"
        elif lit.literal_type == LiteralType.NULL:
            return "null"
        else:
            return str(lit.value)

    def _generate_binary_op(self, expr: IRBinaryOp) -> str:
        """Generate binary operation."""
        left = self._generate_expression(expr.left)
        right = self._generate_expression(expr.right)

        # Map operators
        op_map = {
            BinaryOperator.ADD: "+",
            BinaryOperator.SUBTRACT: "-",
            BinaryOperator.MULTIPLY: "*",
            BinaryOperator.DIVIDE: "/",
            BinaryOperator.MODULO: "%",
            BinaryOperator.POWER: "**",  # C# doesn't have ** operator, use Math.Pow
            BinaryOperator.EQUAL: "==",
            BinaryOperator.NOT_EQUAL: "!=",
            BinaryOperator.LESS_THAN: "<",
            BinaryOperator.LESS_EQUAL: "<=",
            BinaryOperator.GREATER_THAN: ">",
            BinaryOperator.GREATER_EQUAL: ">=",
            BinaryOperator.AND: "&&",
            BinaryOperator.OR: "||",
            BinaryOperator.BIT_AND: "&",
            BinaryOperator.BIT_OR: "|",
            BinaryOperator.BIT_XOR: "^",
            BinaryOperator.LEFT_SHIFT: "<<",
            BinaryOperator.RIGHT_SHIFT: ">>",
        }

        # Special case: power operator
        if expr.op == BinaryOperator.POWER:
            return f"Math.Pow({left}, {right})"

        # Special case: in/not in
        if expr.op == BinaryOperator.IN:
            return f"{right}.Contains({left})"
        if expr.op == BinaryOperator.NOT_IN:
            return f"!{right}.Contains({left})"

        op = op_map.get(expr.op, str(expr.op.value))
        return f"({left} {op} {right})"

    def _generate_unary_op(self, expr: IRUnaryOp) -> str:
        """Generate unary operation."""
        operand = self._generate_expression(expr.operand)

        op_map = {
            UnaryOperator.NOT: "!",
            UnaryOperator.NEGATE: "-",
            UnaryOperator.POSITIVE: "+",
            UnaryOperator.BIT_NOT: "~",
        }

        op = op_map.get(expr.op, str(expr.op.value))
        return f"{op}{operand}"

    def _generate_call(self, expr: IRCall) -> str:
        """Generate function call."""
        func = self._generate_expression(expr.function)

        # Positional arguments
        args = [self._generate_expression(arg) for arg in expr.args]

        # Named arguments (C# syntax: name: value)
        kwargs = [f"{k}: {self._generate_expression(v)}" for k, v in expr.kwargs.items()]

        all_args = args + kwargs
        return f"{func}({', '.join(all_args)})"

    def _generate_array(self, expr: IRArray) -> str:
        """Generate array literal."""
        elements = [self._generate_expression(el) for el in expr.elements]
        return f"new[] {{ {', '.join(elements)} }}"

    def _generate_map(self, expr: IRMap) -> str:
        """Generate dictionary literal."""
        if not expr.entries:
            return "new Dictionary<string, object>()"

        entries = [f'["{k}"] = {self._generate_expression(v)}' for k, v in expr.entries.items()]
        return "new Dictionary<string, object> { " + ", ".join(entries) + " }"

    def _generate_ternary(self, expr: IRTernary) -> str:
        """Generate ternary expression."""
        condition = self._generate_expression(expr.condition)
        true_val = self._generate_expression(expr.true_value)
        false_val = self._generate_expression(expr.false_value)
        return f"({condition} ? {true_val} : {false_val})"

    def _generate_lambda(self, expr: IRLambda) -> str:
        """Generate lambda expression."""
        params = ", ".join(self._to_camel_case(p.name) for p in expr.params)

        if isinstance(expr.body, list):
            # Multi-statement lambda (not standard C#, use delegate)
            return f"({params}) => {{ /* multi-statement */ }}"
        else:
            body = self._generate_expression(expr.body)
            return f"{params} => {body}"

    def _generate_comprehension(self, expr: IRComprehension) -> str:
        """
        Generate C# LINQ method syntax from IR comprehension.

        Outputs: items.Where(x => cond).Select(x => expr).ToList()
        """
        iterable = self._generate_expression(expr.iterable)
        iterator = expr.iterator
        target = self._generate_expression(expr.target)

        result = iterable

        # Add .Where() if condition exists
        if expr.condition:
            condition = self._generate_expression(expr.condition)
            result += f".Where({iterator} => {condition})"

        # Check if we need .Select() (only if target != iterator)
        needs_select = not (isinstance(expr.target, IRIdentifier) and expr.target.name == iterator)

        if needs_select:
            result += f".Select({iterator} => {target})"

        # Add .ToList()
        result += ".ToList()"

        return result

    # ========================================================================
    # Utility Methods
    # ========================================================================

    def _to_pascal_case(self, name: str) -> str:
        """Convert snake_case/camelCase to PascalCase."""
        # Split by underscore or camelCase boundaries
        if "_" in name:
            parts = name.split("_")
        else:
            # Handle camelCase
            parts = []
            current = []
            for char in name:
                if char.isupper() and current:
                    parts.append("".join(current))
                    current = [char]
                else:
                    current.append(char)
            if current:
                parts.append("".join(current))

        return "".join(p.capitalize() for p in parts if p)

    def _to_camel_case(self, name: str) -> str:
        """Convert snake_case/PascalCase to camelCase."""
        pascal = self._to_pascal_case(name)
        if pascal:
            return pascal[0].lower() + pascal[1:]
        return name

    def _is_async_call(self, call: IRCall) -> bool:
        """Check if a call is async (heuristic: ends with Async)."""
        if isinstance(call.function, IRIdentifier):
            return call.function.name.endswith("Async") or call.function.name.endswith("async")
        elif isinstance(call.function, IRPropertyAccess):
            return call.function.property.endswith("Async") or call.function.property.endswith("async")
        return False

    def _is_async_expression(self, expr: IRExpression) -> bool:
        """Check if expression is async."""
        if isinstance(expr, IRCall):
            return self._is_async_call(expr)
        return False


# ============================================================================
# Public API
# ============================================================================


def generate_csharp(module: IRModule, namespace: str = "Generated") -> str:
    """
    Generate C# code from IR module.

    Args:
        module: IR module to generate from
        namespace: Namespace for generated code

    Returns:
        Complete C# source code

    Example:
        >>> from dsl.ir import *
        >>> module = IRModule(name="example", functions=[...])
        >>> code = generate_csharp(module, namespace="MyApp")
    """
    generator = DotNetGeneratorV2(namespace=namespace)
    return generator.generate(module)
