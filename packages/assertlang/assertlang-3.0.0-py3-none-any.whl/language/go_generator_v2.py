"""
Go Generator V2 - IR → Idiomatic Go Code

This generator converts Promptware's Intermediate Representation (IR) into
production-quality, idiomatic Go code. Unlike V1 (which generated MCP servers),
V2 generates arbitrary Go code with full language support.

Key Features:
- Idiomatic Go: Follows Go conventions (gofmt, naming, error handling)
- Error handling: Converts IR throws → (result, error) return pattern
- Goroutines: Converts is_async → goroutine invocations
- Type safety: Proper type mapping via type_system
- Zero dependencies: Only uses Go stdlib
- Readable output: Proper formatting, comments, documentation

Strategy:
- Generate valid, compilable Go (must pass go build)
- Preserve semantics from IR
- Handle edge cases gracefully
- Follow Go proverbs (clear is better than clever)
"""

from typing import List, Dict, Set, Optional, Tuple
from language.library_mapping import LibraryMapper, FUNCTION_MAPPINGS, IMPORT_MAPPINGS
from language import go_helpers
from dsl.ir import (
    IRModule,
    IRImport,
    IRFunction,
    IRParameter,
    IRClass,
    IRProperty,
    IRTypeDefinition,
    IREnum,
    IREnumVariant,
    IRType,
    IRStatement,
    IRExpression,
    IRAssignment,
    IRAwait,
    IRReturn,
    IRThrow,
    IRIf,
    IRFor,
    IRForCStyle,
    IRWhile,
    IRTry,
    IRCatch,
    IRBreak,
    IRContinue,
    IRPass,
    IRCall,
    IRIdentifier,
    IRLiteral,
    IRBinaryOp,
    IRUnaryOp,
    IRPropertyAccess,
    IRIndex,
    IRArray,
    IRMap,
    IRComprehension,
    IRTernary,
    IRLambda,
    IRFString,
    BinaryOperator,
    UnaryOperator,
    LiteralType,
    NodeType,
)
from dsl.type_system import TypeSystem
from dsl.type_inference import TypeInferenceEngine
from dsl.idiom_translator import IdiomTranslator
from language.library_mapping import LibraryMapper


class GoGeneratorV2:
    """Generate idiomatic Go code from IR."""

    def __init__(self):
        self.type_system = TypeSystem()
        self.library_mapper = LibraryMapper()
        self.type_inference = TypeInferenceEngine()
        self.idiom_translator = IdiomTranslator(source_lang="python", target_lang="go")
        self.inferred_types: Dict[str, IRType] = {}
        self.indent_level = 0
        self.indent_char = "\t"  # Go uses tabs
        self.imports_needed: Set[str] = set()
        self.current_receiver: Optional[str] = None  # Track receiver variable in methods
        self.in_constructor: bool = False  # Track if we're in a constructor
        self.current_class: Optional[str] = None  # Track current class name
        self.source_language: Optional[str] = None  # Track source language for mapping

    def indent(self) -> str:
        """Get current indentation."""
        return self.indent_char * self.indent_level

    def increase_indent(self):
        """Increase indentation level."""
        self.indent_level += 1

    def decrease_indent(self):
        """Decrease indentation level."""
        if self.indent_level > 0:
            self.indent_level -= 1

    # ========================================================================
    # Top-level generation
    # ========================================================================

    def generate(self, module: IRModule) -> str:
        """
        Generate complete Go source file from IR module.

        Args:
            module: IR module to convert

        Returns:
            Complete Go source code as string
        """
        # Reset state
        self.imports_needed = set()
        self.indent_level = 0
        go_helpers.reset_helpers()

        # Run type inference on module
        self.type_inference.infer_module_types(module)
        self.inferred_types = self.type_inference.type_env

        lines = []

        # Package declaration
        lines.append(f"package {self._normalize_package_name(module.name)}")
        lines.append("")

        # Collect imports needed
        self._collect_imports(module)

        # Generate imports block
        if self.imports_needed:
            lines.append(self._generate_imports_block())
            lines.append("")

        # Generate type definitions
        for type_def in module.types:
            lines.append(self._generate_type_definition(type_def))
            lines.append("")

        # Generate enums (as custom types in Go)
        for enum in module.enums:
            lines.append(self._generate_enum(enum))
            lines.append("")

        # Generate module-level constants/variables
        if module.module_vars:
            for var in module.module_vars:
                lines.append(self._generate_module_var(var))
            lines.append("")

        # Generate helper functions (before main code)
        # Note: We'll add these at the end after detecting what's needed

        # Generate classes (as structs with methods)
        for cls in module.classes:
            lines.append(self._generate_class(cls))
            lines.append("")

        # Generate functions
        for func in module.functions:
            lines.append(self._generate_function(func))
            lines.append("")

        # Join initial code
        initial_code = "\n".join(lines)

        # Detect needed helper functions
        helpers_needed = go_helpers.detect_needed_helpers(initial_code)
        for helper in helpers_needed:
            go_helpers.mark_helper_needed(helper)

        # Generate helpers if any were detected
        helper_code = go_helpers.generate_needed_helpers()
        if helper_code:
            # Insert helpers after package + imports, before main code
            # Find end of imports block
            import_end = initial_code.find(")\n\n")
            if import_end != -1:
                # Found import block
                before = initial_code[:import_end+2]
                after = initial_code[import_end+2:]
                result = before + "\n" + helper_code + after
            else:
                # No imports or different format, append after first section
                parts = initial_code.split("\n\n", 2)
                if len(parts) >= 2:
                    result = parts[0] + "\n\n" + helper_code + "\n\n" + "\n\n".join(parts[1:])
                else:
                    result = initial_code + "\n\n" + helper_code
        else:
            result = initial_code

        # Remove excessive blank lines
        while "\n\n\n" in result:
            result = result.replace("\n\n\n", "\n\n")

        # Ensure ends with single newline
        result = result.rstrip()
        if result:
            return result + "\n"
        return "package main\n"

    def _normalize_package_name(self, name: str) -> str:
        """Normalize package name to Go conventions."""
        # Lowercase, no underscores
        name = name.lower().replace("-", "").replace("_", "")
        return name if name else "main"

    def _collect_imports(self, module: IRModule):
        """Analyze module and collect required imports with library mapping."""
        # Standard imports from IR imports
        for imp in module.imports:
            # Skip PW-specific imports
            if imp.module.startswith("pw_"):
                continue

            # Check if this Python import needs translation
            if imp.module in IMPORT_MAPPINGS:
                go_import = IMPORT_MAPPINGS[imp.module].get("go")

                # None means not needed in Go (built-in or different paradigm)
                if go_import is not None:
                    self.imports_needed.add(go_import)
            else:
                # No mapping found, use original
                self.imports_needed.add(imp.module)

        # Check for error handling needs
        has_errors = False
        for func in module.functions:
            if func.throws or self._function_needs_error_handling(func):
                has_errors = True
                break

        if has_errors:
            self.imports_needed.add("errors")

        # Check for fmt needs (if we have prints or string formatting)
        # For now, always include fmt for common usage
        if module.functions:
            self.imports_needed.add("fmt")

    def _function_needs_error_handling(self, func: IRFunction) -> bool:
        """Check if function needs error handling."""
        # Check if any throws exist in body
        for stmt in func.body:
            if isinstance(stmt, IRThrow):
                return True
            if isinstance(stmt, IRTry):
                return True
            # If function has return statements and a return type, use error pattern
            if isinstance(stmt, IRReturn) and func.return_type:
                return True
        return False

    def _generate_imports_block(self) -> str:
        """Generate Go imports block."""
        if not self.imports_needed:
            return ""

        sorted_imports = sorted(self.imports_needed)

        if len(sorted_imports) == 1:
            return f'import "{sorted_imports[0]}"'

        lines = ["import ("]
        for imp in sorted_imports:
            lines.append(f'\t"{imp}"')
        lines.append(")")
        return "\n".join(lines)

    # ========================================================================
    # Type generation
    # ========================================================================

    def _generate_type(self, ir_type: IRType) -> str:
        """Generate Go type from IR type."""
        # Handle Self type - replace with current class name
        if ir_type.name == "Self" and self.current_class:
            # For Go constructors, return pointer to struct
            if self.in_constructor:
                return f"*{self.current_class}"
            return self.current_class

        return self.type_system.map_to_language(ir_type, "go")

    def _generate_type_definition(self, type_def: IRTypeDefinition) -> str:
        """Generate struct type definition."""
        lines = []

        # Add documentation if available
        if type_def.doc:
            lines.append(f"// {type_def.doc}")

        # Struct declaration
        struct_name = self._capitalize(type_def.name)
        lines.append(f"type {struct_name} struct {{")

        # Fields
        for field in type_def.fields:
            field_name = self._capitalize(field.name)
            field_type = self._generate_type(field.prop_type)

            # Add JSON tags for serialization
            json_tag = f'`json:"{field.name}"`'
            lines.append(f"\t{field_name} {field_type} {json_tag}")

        lines.append("}")

        return "\n".join(lines)

    def _generate_enum(self, enum: IREnum) -> str:
        """
        Generate enum as Go constants.

        Go doesn't have native enums, so we use typed constants:
        type Status int
        const (
            StatusPending Status = iota
            StatusCompleted
        )
        """
        lines = []

        # Add documentation
        if enum.doc:
            lines.append(f"// {enum.doc}")

        # Type alias
        enum_name = self._capitalize(enum.name)
        lines.append(f"type {enum_name} int")
        lines.append("")

        # Constants
        lines.append("const (")
        for i, variant in enumerate(enum.variants):
            variant_name = self._capitalize(f"{enum_name}_{variant.name}")
            if i == 0:
                lines.append(f"\t{variant_name} {enum_name} = iota")
            else:
                lines.append(f"\t{variant_name}")
        lines.append(")")

        return "\n".join(lines)

    # ========================================================================
    # Class generation (structs + methods)
    # ========================================================================

    def _generate_class(self, cls: IRClass) -> str:
        """Generate class as Go struct with methods."""
        lines = []

        # Struct definition
        if cls.doc:
            lines.append(f"// {cls.doc}")

        class_name = self._capitalize(cls.name)
        lines.append(f"type {class_name} struct {{")

        # Properties
        for prop in cls.properties:
            prop_name = self._capitalize(prop.name)
            prop_type = self._generate_type(prop.prop_type)
            lines.append(f"\t{prop_name} {prop_type}")

        lines.append("}")
        lines.append("")

        # Constructor (as New function)
        if cls.constructor:
            lines.append(self._generate_constructor(cls.name, cls.constructor))
            lines.append("")

        # Methods
        for method in cls.methods:
            lines.append(self._generate_method(cls.name, method))
            lines.append("")

        return "\n".join(lines).rstrip()

    def _generate_constructor(self, class_name: str, constructor: IRFunction) -> str:
        """Generate constructor as New* function."""
        lines = []

        class_name = self._capitalize(class_name)
        func_name = f"New{class_name}"

        # Function signature
        params = self._generate_parameters(constructor.params)

        # Constructor returns pointer to struct
        return_type = f"*{class_name}"

        # Add error if needed
        if constructor.throws or self._function_needs_error_handling(constructor):
            return_type = f"({return_type}, error)"

        lines.append(f"func {func_name}({params}) {return_type} {{")

        # Body
        self.increase_indent()

        # Set context
        old_in_constructor = self.in_constructor
        old_class = self.current_class
        self.in_constructor = True
        self.current_class = class_name

        # Collect struct field initializations from self.property = value assignments
        struct_fields = {}
        other_statements = []

        for stmt in constructor.body:
            if isinstance(stmt, IRAssignment) and isinstance(stmt.target, str) and stmt.target.startswith("self."):
                # Extract field name: self.db -> Db
                field_name = self._capitalize(stmt.target[5:])  # Remove "self."
                field_value = self._generate_expression(stmt.value)
                struct_fields[field_name] = field_value
            else:
                other_statements.append(stmt)

        # Generate non-self-assignment statements first (if any)
        for stmt in other_statements:
            stmt_lines = self._generate_statement(stmt)
            lines.extend(stmt_lines)

        # Generate struct initialization
        if struct_fields:
            lines.append(f"{self.indent()}return &{class_name}{{")
            self.increase_indent()
            for field_name, field_value in struct_fields.items():
                lines.append(f"{self.indent()}{field_name}: {field_value},")
            self.decrease_indent()
            if constructor.throws or self._function_needs_error_handling(constructor):
                lines.append(f"{self.indent()}}}, nil")
            else:
                lines.append(f"{self.indent()}}}")
        elif constructor.throws or self._function_needs_error_handling(constructor):
            # Empty struct but needs error return
            lines.append(f"{self.indent()}return &{class_name}{{}}, nil")
        else:
            # Empty struct
            lines.append(f"{self.indent()}return &{class_name}{{}}")

        # Restore context
        self.in_constructor = old_in_constructor
        self.current_class = old_class
        self.decrease_indent()
        lines.append("}")

        return "\n".join(lines)

    def _generate_method(self, class_name: str, method: IRFunction) -> str:
        """Generate struct method."""
        lines = []

        # Add documentation
        if method.doc:
            for line in method.doc.split("\n"):
                lines.append(f"// {line}")

        class_name = self._capitalize(class_name)
        method_name = self._capitalize(method.name)

        # Set current class context (needed for Self type resolution)
        old_class = self.current_class
        self.current_class = class_name

        # Receiver
        receiver_var = class_name[0].lower()
        receiver = f"{receiver_var} *{class_name}"

        # Parameters
        params = self._generate_parameters(method.params)

        # Return type
        return_type = ""
        if method.return_type:
            return_type = self._generate_type(method.return_type)

            # Add error return if function throws
            if method.throws or self._function_needs_error_handling(method):
                return_type = f"({return_type}, error)"
        elif method.throws or self._function_needs_error_handling(method):
            return_type = "error"

        # Function signature
        sig_parts = [f"func ({receiver}) {method_name}"]
        if params:
            sig_parts.append(f"({params})")
        else:
            sig_parts.append("()")
        if return_type:
            sig_parts.append(f" {return_type}")
        sig_parts.append(" {")

        lines.append("".join(sig_parts))

        # Body
        self.increase_indent()

        # Set receiver context for method body generation
        old_receiver = self.current_receiver
        self.current_receiver = receiver_var

        for stmt in method.body:
            stmt_lines = self._generate_statement(stmt)
            lines.extend(stmt_lines)

        # Restore context
        self.current_receiver = old_receiver
        self.current_class = old_class  # Restore class context set at method start
        self.decrease_indent()

        lines.append("}")

        return "\n".join(lines)

    # ========================================================================
    # Module-level variable generation
    # ========================================================================

    def _generate_module_var(self, var: IRAssignment) -> str:
        """
        Generate module-level constant or variable.

        In Go, module-level vars use:
        - const for literals
        - var for expressions or mutable values
        """
        var_name = self._capitalize(var.target)  # Capitalize for export
        var_type = self._generate_type(var.var_type) if var.var_type else "interface{}"
        value = self._generate_expression(var.value)

        # Check if value is a simple literal (can use const)
        is_literal = isinstance(var.value, IRLiteral)

        if is_literal:
            return f"const {var_name} {var_type} = {value}"
        else:
            return f"var {var_name} {var_type} = {value}"

    # ========================================================================
    # Function generation
    # ========================================================================

    def _generate_function(self, func: IRFunction) -> str:
        """Generate top-level function."""
        lines = []

        # Add documentation
        if func.doc:
            for line in func.doc.split("\n"):
                lines.append(f"// {line}")

        func_name = self._capitalize(func.name)

        # Parameters
        params = self._generate_parameters(func.params)

        # Return type
        return_type = ""
        if func.return_type:
            return_type = self._generate_type(func.return_type)

            # Add error return if function throws
            if func.throws or self._function_needs_error_handling(func):
                return_type = f"({return_type}, error)"
        elif func.throws or self._function_needs_error_handling(func):
            return_type = "error"

        # Function signature
        sig_parts = [f"func {func_name}"]
        if params:
            sig_parts.append(f"({params})")
        else:
            sig_parts.append("()")
        if return_type:
            sig_parts.append(f" {return_type}")
        sig_parts.append(" {")

        lines.append("".join(sig_parts))

        # Body
        self.increase_indent()

        # If function is async, wrap body in goroutine
        if func.is_async:
            lines.append(f"{self.indent()}go func() {{")
            self.increase_indent()

        for stmt in func.body:
            stmt_lines = self._generate_statement(stmt)
            lines.extend(stmt_lines)

        if func.is_async:
            self.decrease_indent()
            lines.append(f"{self.indent()}}}()")

        self.decrease_indent()
        lines.append("}")

        return "\n".join(lines)

    def _generate_parameters(self, params: List[IRParameter]) -> str:
        """Generate function parameters."""
        if not params:
            return ""

        param_parts = []
        for param in params:
            param_name = param.name
            param_type = self._generate_type(param.param_type)

            # Handle variadic
            if param.is_variadic:
                param_type = "..." + param_type.lstrip("[]")

            param_parts.append(f"{param_name} {param_type}")

        return ", ".join(param_parts)

    # ========================================================================
    # Statement generation
    # ========================================================================

    def _generate_statement(self, stmt: IRStatement) -> List[str]:
        """Generate statement, returning list of lines."""
        if isinstance(stmt, IRAssignment):
            return self._generate_assignment(stmt)
        elif isinstance(stmt, IRReturn):
            return self._generate_return(stmt)
        elif isinstance(stmt, IRThrow):
            return self._generate_throw(stmt)
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
        elif isinstance(stmt, IRBreak):
            return [f"{self.indent()}break"]
        elif isinstance(stmt, IRContinue):
            return [f"{self.indent()}continue"]
        elif isinstance(stmt, IRPass):
            return [f"{self.indent()}// pass"]
        elif isinstance(stmt, IRCall):
            # Expression statement
            expr = self._generate_expression(stmt)
            return [f"{self.indent()}{expr}"]
        else:
            return [f"{self.indent()}// Unknown statement: {type(stmt).__name__}"]

    def _generate_assignment(self, stmt: IRAssignment) -> List[str]:
        """Generate assignment/variable declaration."""

        # Special case: comprehension in assignment - expand to clean loop
        if isinstance(stmt.value, IRComprehension):
            return self._generate_comprehension_as_statements(stmt)

        # Special case: ternary in assignment - expand to if/else
        if isinstance(stmt.value, IRTernary):
            return self._generate_ternary_as_statements(stmt)

        value_expr = self._generate_expression(stmt.value)

        # Generate target (could be variable or property access)
        if stmt.target:
            if isinstance(stmt.target, str):
                target = self._transform_assignment_target(stmt.target)
                target_name = stmt.target
            else:
                # Target is an expression (property access, array index, etc.)
                target = self._generate_expression(stmt.target)
                target_name = None  # Can't infer type for complex targets
        else:
            target = "_unknown"
            target_name = None

        # Special case: Empty array with inferred element type
        # Fix the initializer to match the inferred type
        if isinstance(stmt.value, IRArray) and not stmt.value.elements:
            if target_name and target_name in self.inferred_types:
                inferred_type = self.inferred_types[target_name]
                # Check if it's an array type with specific element type
                if inferred_type.name == "array" and inferred_type.generic_args:
                    elem_type = self._generate_type(inferred_type.generic_args[0])
                    value_expr = f"[]{elem_type}{{}}"

        if stmt.is_declaration:
            # var x Type = value OR x := value
            # Check if we have a better inferred type than the IR's var_type
            use_inferred = False
            if target_name and target_name in self.inferred_types:
                inferred_type = self.inferred_types[target_name]
                # Prefer inferred type if:
                # 1. No explicit type in IR, OR
                # 2. IR type is generic (any/interface{})
                if not stmt.var_type or stmt.var_type.name in ["any", "interface{}"]:
                    use_inferred = True
                # Also prefer if inferred is more specific
                elif inferred_type.name not in ["any", "interface{}"]:
                    use_inferred = True

            if use_inferred:
                # Use inferred type
                inferred_type = self.inferred_types[target_name]
                var_type = self._generate_type(inferred_type)
                return [f"{self.indent()}var {target} {var_type} = {value_expr}"]
            elif stmt.var_type:
                # Use explicit type from IR
                var_type = self._generate_type(stmt.var_type)
                return [f"{self.indent()}var {target} {var_type} = {value_expr}"]
            else:
                # Short declaration
                return [f"{self.indent()}{target} := {value_expr}"]
        else:
            # Assignment
            return [f"{self.indent()}{target} = {value_expr}"]

    def _transform_assignment_target(self, target: str) -> str:
        """Transform assignment target from IR form to Go form.

        Examples:
            self.db -> u.Db (in methods)
            self.cache[key] -> u.Cache[key] (in methods)
        """
        if not target.startswith("self."):
            return target

        # In constructor, self.property assignments are handled specially
        if self.in_constructor:
            return target

        # In method, replace self with receiver variable
        if self.current_receiver:
            # Extract property name: self.db -> db
            rest = target[5:]  # Remove "self."

            # Check if it contains indexing: cache[key]
            if "[" in rest:
                # Split property and index: cache[key] -> cache, [key]
                prop_name, index_part = rest.split("[", 1)
                prop_name = self._capitalize(prop_name)
                return f"{self.current_receiver}.{prop_name}[{index_part}"
            else:
                # Simple property access: self.db -> u.Db
                prop_name = self._capitalize(rest)
                return f"{self.current_receiver}.{prop_name}"

        # Fallback: just capitalize the property
        return self._capitalize(target[5:])

    def _generate_return(self, stmt: IRReturn) -> List[str]:
        """Generate return statement."""
        if stmt.value:
            # IRArray should be generated as a slice literal, not unpacked
            # (Go functions with error return need: return value, nil)
            value_expr = self._generate_expression(stmt.value)

            # Check if the value expression already contains an error return
            # (e.g., already has ", nil" or ", err")
            if ', nil' in value_expr or ', err' in value_expr:
                # Already has error handling, don't add another nil
                return [f"{self.indent()}return {value_expr}"]

            # Check if we need to return error as well
            # For now, assume nil error on success for functions with return types
            return [f"{self.indent()}return {value_expr}, nil"]
        else:
            return [f"{self.indent()}return"]

    def _generate_throw(self, stmt: IRThrow) -> List[str]:
        """
        Generate throw as return error.

        In Go, throwing becomes: return nil, errors.New("message")
        or return zeroValue, err
        """
        error_expr = self._generate_expression(stmt.exception)

        # Generate error creation
        if isinstance(stmt.exception, IRCall):
            # Error constructor call
            return [f'{self.indent()}return nil, {error_expr}']
        else:
            # Simple error message
            return [f'{self.indent()}return nil, errors.New({error_expr})']

    def _generate_if(self, stmt: IRIf) -> List[str]:
        """Generate if statement."""
        lines = []

        condition = self._generate_expression(stmt.condition)
        lines.append(f"{self.indent()}if {condition} {{")

        # Then body
        self.increase_indent()
        for s in stmt.then_body:
            lines.extend(self._generate_statement(s))
        self.decrease_indent()

        # Else body
        if stmt.else_body:
            lines.append(f"{self.indent()}}} else {{")
            self.increase_indent()
            for s in stmt.else_body:
                lines.extend(self._generate_statement(s))
            self.decrease_indent()
            lines.append(f"{self.indent()}}}")
        else:
            lines.append(f"{self.indent()}}}")

        return lines

    def _generate_for(self, stmt: IRFor) -> List[str]:
        """Generate for loop (range-based or C-style)."""
        lines = []

        # Special case: Python range() → C-style for loop in Go
        if isinstance(stmt.iterable, IRCall) and isinstance(stmt.iterable.function, IRIdentifier):
            if stmt.iterable.function.name == "range":
                args = stmt.iterable.args
                if len(args) == 1:
                    # for i in range(n) → for i := 0; i < n; i++
                    n = self._generate_expression(args[0])
                    lines.append(f"{self.indent()}for {stmt.iterator} := 0; {stmt.iterator} < {n}; {stmt.iterator}++ {{")
                elif len(args) == 2:
                    # for i in range(start, stop) → for i := start; i < stop; i++
                    start = self._generate_expression(args[0])
                    stop = self._generate_expression(args[1])
                    lines.append(f"{self.indent()}for {stmt.iterator} := {start}; {stmt.iterator} < {stop}; {stmt.iterator}++ {{")
                elif len(args) == 3:
                    # for i in range(start, stop, step) → for i := start; i < stop; i += step
                    start = self._generate_expression(args[0])
                    stop = self._generate_expression(args[1])
                    step = self._generate_expression(args[2])
                    lines.append(f"{self.indent()}for {stmt.iterator} := {start}; {stmt.iterator} < {stop}; {stmt.iterator} += {step} {{")

                self.increase_indent()
                for s in stmt.body:
                    lines.extend(self._generate_statement(s))
                self.decrease_indent()

                lines.append(f"{self.indent()}}}")
                return lines

        # Regular range-based for loop
        iterable = self._generate_expression(stmt.iterable)
        lines.append(f"{self.indent()}for _, {stmt.iterator} := range {iterable} {{")

        self.increase_indent()
        for s in stmt.body:
            lines.extend(self._generate_statement(s))
        self.decrease_indent()

        lines.append(f"{self.indent()}}}")

        return lines

    def _generate_for_c_style(self, stmt: IRForCStyle) -> List[str]:
        """
        Generate C-style for loop.

        for (let i = 0; i < 10; i = i + 1) { ... }
        becomes:
        for i := 0; i < 10; i = i + 1 {
            ...
        }
        """
        lines = []

        # Generate init (convert IRAssignment to Go initialization)
        # Extract the parts from init statement
        init_lines = self._generate_statement(stmt.init)
        init_str = init_lines[0].strip() if init_lines else ""

        # Generate condition
        condition = self._generate_expression(stmt.condition)

        # Generate increment (convert IRAssignment to Go increment)
        increment_lines = self._generate_statement(stmt.increment)
        increment_str = increment_lines[0].strip() if increment_lines else ""

        # Build for loop header
        lines.append(f"{self.indent()}for {init_str}; {condition}; {increment_str} {{")

        # Generate body
        self.increase_indent()
        for s in stmt.body:
            lines.extend(self._generate_statement(s))
        self.decrease_indent()

        lines.append(f"{self.indent()}}}")

        return lines

    def _generate_while(self, stmt: IRWhile) -> List[str]:
        """Generate while loop (as for loop in Go)."""
        lines = []

        condition = self._generate_expression(stmt.condition)
        lines.append(f"{self.indent()}for {condition} {{")

        self.increase_indent()
        for s in stmt.body:
            lines.extend(self._generate_statement(s))
        self.decrease_indent()

        lines.append(f"{self.indent()}}}")

        return lines

    def _generate_try(self, stmt: IRTry) -> List[str]:
        """
        Generate try-catch as error handling pattern.

        Go doesn't have try-catch, so we convert to:
        - Function calls with error checking
        - Deferred cleanup
        """
        lines = []

        # Generate try body with error checks
        for s in stmt.try_body:
            lines.extend(self._generate_statement(s))

        # Generate catch blocks as error handling
        # This is simplified - real translation would need more context
        for catch in stmt.catch_blocks:
            lines.append(f"{self.indent()}// catch {catch.exception_type or 'all'}")
            if catch.body:
                for s in catch.body:
                    lines.extend(self._generate_statement(s))

        # Finally block as defer
        if stmt.finally_body:
            lines.append(f"{self.indent()}defer func() {{")
            self.increase_indent()
            for s in stmt.finally_body:
                lines.extend(self._generate_statement(s))
            self.decrease_indent()
            lines.append(f"{self.indent()}}}()")

        return lines

    # ========================================================================
    # Expression generation
    # ========================================================================

    def _generate_expression(self, expr: IRExpression) -> str:
        """Generate expression."""
        if isinstance(expr, IRLiteral):
            return self._generate_literal(expr)
        elif isinstance(expr, IRIdentifier):
            # Handle 'self' identifier
            if expr.name == "self" and self.current_receiver:
                return self.current_receiver
            return expr.name
        elif isinstance(expr, IRAwait):
            # Go doesn't have await - goroutines handle concurrency differently
            # For async/await patterns, we'd typically use channels
            # For now, just generate the expression (comment out await)
            inner = self._generate_expression(expr.expression)
            return f"{inner}  // Note: Go uses goroutines, not await"
        elif isinstance(expr, IRBinaryOp):
            return self._generate_binary_op(expr)
        elif isinstance(expr, IRUnaryOp):
            return self._generate_unary_op(expr)
        elif isinstance(expr, IRCall):
            return self._generate_call(expr)
        elif isinstance(expr, IRPropertyAccess):
            obj = self._generate_expression(expr.object)
            # Special case: .length property should use len() in Go
            if expr.property == "length":
                return f"len({obj})"
            # Capitalize property for Go exported fields
            prop = self._capitalize(expr.property)
            return f"{obj}.{prop}"
        elif isinstance(expr, IRIndex):
            obj = self._generate_expression(expr.object)
            idx = self._generate_expression(expr.index)
            return f"{obj}[{idx}]"
        elif isinstance(expr, IRArray):
            return self._generate_array(expr)
        elif isinstance(expr, IRMap):
            return self._generate_map(expr)
        elif isinstance(expr, IRTernary):
            return self._generate_ternary(expr)
        elif isinstance(expr, IRLambda):
            return self._generate_lambda(expr)
        elif isinstance(expr, IRFString):
            return self._generate_fstring(expr)
        elif isinstance(expr, IRComprehension):
            return self._generate_comprehension_inline(expr)
        else:
            # Unknown expression type - generate valid nil fallback
            return "nil"

    def _generate_literal(self, lit: IRLiteral) -> str:
        """Generate literal value."""
        if lit.literal_type == LiteralType.STRING:
            # Escape string - use Python's built-in repr and clean it up
            # This handles all escape sequences correctly
            value = repr(lit.value)
            # repr() adds quotes and escapes properly, but we need to:
            # 1. Remove the outer quotes (repr adds them)
            # 2. Change single quotes to double quotes if needed
            if value.startswith("'") and value.endswith("'"):
                value = value[1:-1]  # Remove quotes
                value = value.replace('"', '\\"')  # Escape any internal double quotes
            elif value.startswith('"') and value.endswith('"'):
                value = value[1:-1]  # Just remove quotes, already escaped
            return f'"{value}"'
        elif lit.literal_type == LiteralType.INTEGER:
            return str(lit.value)
        elif lit.literal_type == LiteralType.FLOAT:
            return str(lit.value)
        elif lit.literal_type == LiteralType.BOOLEAN:
            return "true" if lit.value else "false"
        elif lit.literal_type == LiteralType.NULL:
            return "nil"
        else:
            return str(lit.value)

    def _generate_binary_op(self, expr: IRBinaryOp) -> str:
        """Generate binary operation."""
        left = self._generate_expression(expr.left)
        right = self._generate_expression(expr.right)

        # Handle special operators
        if expr.op == BinaryOperator.IN:
            # Python "x in list" → Go function call (need helper or manual check)
            # For now, generate comment indicating need for containment check
            return f"contains({right}, {left})  // TODO: implement contains() helper"
        elif expr.op == BinaryOperator.NOT_IN:
            return f"!contains({right}, {left})  // TODO: implement contains() helper"
        elif expr.op == BinaryOperator.POWER:
            # Python ** → Go math.Pow()
            self.imports_needed.add("math")
            return f"math.Pow({left}, {right})"

        # Map operators
        op_map = {
            BinaryOperator.AND: "&&",
            BinaryOperator.OR: "||",
            BinaryOperator.NOT_EQUAL: "!=",
            BinaryOperator.EQUAL: "==",
        }

        op_str = op_map.get(expr.op, expr.op.value)
        return f"({left} {op_str} {right})"

    def _generate_unary_op(self, expr: IRUnaryOp) -> str:
        """Generate unary operation."""
        operand = self._generate_expression(expr.operand)

        if expr.op == UnaryOperator.NOT:
            return f"!{operand}"
        elif expr.op == UnaryOperator.NEGATE:
            return f"-{operand}"
        elif expr.op == UnaryOperator.BIT_NOT:
            return f"^{operand}"
        else:
            return f"{expr.op.value}{operand}"

    def _generate_call(self, expr: IRCall) -> str:
        """Generate function call or struct literal with library mapping."""
        func = self._generate_expression(expr.function)

        # Check if this is a stdlib call that needs mapping
        if isinstance(expr.function, IRPropertyAccess):
            # Handle special Python list/string methods
            method_name = expr.function.property
            obj_expr = self._generate_expression(expr.function.object)

            # Python list.append() → Go append()
            if method_name == "append" or method_name == "Append":
                if len(expr.args) == 1:
                    arg = self._generate_expression(expr.args[0])
                    return f"{obj_expr} = append({obj_expr}, {arg})"

            # Python str.join() → Go strings.Join()
            if method_name == "join" or method_name == "Join":
                if len(expr.args) == 1:
                    self.imports_needed.add("strings")
                    arg = self._generate_expression(expr.args[0])
                    return f"strings.Join({arg}, {obj_expr})"

            # JavaScript Number.toFixed(n) → Go fmt.Sprintf("%.{n}f", value)
            if method_name == "toFixed" or method_name == "ToFixed":
                if len(expr.args) == 1:
                    self.imports_needed.add("fmt")
                    precision = self._generate_expression(expr.args[0])
                    # Try to extract integer value for format string
                    if isinstance(expr.args[0], IRLiteral):
                        prec_val = expr.args[0].value
                        return f'fmt.Sprintf("%.{prec_val}f", {obj_expr})'
                    else:
                        # Dynamic precision - harder, use generic formatting
                        return f'fmt.Sprintf("%.*f", {precision}, {obj_expr})'

            # Handle module.function pattern (e.g., math.sqrt, random.choice)
            obj_name = expr.function.object.name if isinstance(expr.function.object, IRIdentifier) else None
            if obj_name:
                py_call = f"{obj_name}.{expr.function.property}"

                # Special case: random.choice with typed array
                if py_call == "random.choice" and len(expr.args) == 1:
                    arg = expr.args[0]
                    # Check if arg is an array with consistent type
                    if isinstance(arg, IRArray) and arg.elements:
                        first_elem = arg.elements[0]
                        if isinstance(first_elem, IRLiteral):
                            if first_elem.literal_type == LiteralType.STRING:
                                # Use ChoiceString for string arrays
                                self.imports_needed.add("math/rand")
                                arg_str = self._generate_expression(arg)
                                return f"ChoiceString({arg_str})"
                            elif first_elem.literal_type == LiteralType.INTEGER:
                                # Use ChoiceInt for int arrays
                                self.imports_needed.add("math/rand")
                                arg_str = self._generate_expression(arg)
                                return f"ChoiceInt({arg_str})"

                if py_call in FUNCTION_MAPPINGS:
                    mapped = FUNCTION_MAPPINGS[py_call].get("go")
                    if mapped:
                        func = mapped
        elif isinstance(expr.function, IRIdentifier):
            # Handle built-in functions (e.g., len, print, range)
            func_name = expr.function.name

            # Special case: range() in Python → simple for loop in Go (not a function call)
            # This shouldn't be called directly - should be handled in for loop generation
            # But if it is, we'll generate a slice
            if func_name == "range":
                if len(expr.args) == 1:
                    # range(n) → make([]int, n)
                    n = self._generate_expression(expr.args[0])
                    return f"make([]int, {n})"
                elif len(expr.args) == 2:
                    # range(start, stop) → need to manually create slice
                    start = self._generate_expression(expr.args[0])
                    stop = self._generate_expression(expr.args[1])
                    # This is complex - better handled in for loop
                    return f"/* range({start}, {stop}) - should be in for loop */"

            if func_name in FUNCTION_MAPPINGS:
                mapped = FUNCTION_MAPPINGS[func_name].get("go")
                if mapped:
                    func = mapped

        # Check if this is a struct literal (has kwargs but no args, or no args AND type looks like a struct)
        # Struct literals: User{Name: "Alice", Age: 30} or User{}
        # Function calls: DoSomething("Alice", 30) or fmt.Println()

        # Heuristic: If function name is capitalized (like a type) and has no args, it's likely a struct
        # This handles both User{fields} and User{}
        is_likely_struct_literal = (
            not expr.args and  # No positional arguments
            isinstance(expr.function, IRIdentifier) and  # Simple identifier (not pkg.Func)
            expr.function.name[0].isupper()  # Capitalized (Go type convention)
        )

        if is_likely_struct_literal:
            # This is a struct literal with named fields or empty
            if expr.kwargs:
                fields = []
                for key, value in expr.kwargs.items():
                    # Capitalize field name for Go exported fields
                    field_name = self._capitalize(key)
                    field_value = self._generate_expression(value)
                    fields.append(f"{field_name}: {field_value}")
                return f"{func}{{{', '.join(fields)}}}"
            else:
                # Empty struct literal
                return f"{func}{{}}"

        # Regular function call
        args = [self._generate_expression(arg) for arg in expr.args]

        # Named arguments (not directly supported in Go, treat as positional)
        for key, value in expr.kwargs.items():
            args.append(self._generate_expression(value))

        return f"{func}({', '.join(args)})"

    def _generate_array(self, expr: IRArray) -> str:
        """Generate array literal."""
        elements = [self._generate_expression(el) for el in expr.elements]

        if not elements:
            return "[]interface{}{}"

        # Try to infer element type from first element
        element_type = "interface{}"
        if expr.elements:
            first_elem = expr.elements[0]
            if isinstance(first_elem, IRLiteral):
                if first_elem.literal_type == LiteralType.STRING:
                    element_type = "string"
                elif first_elem.literal_type == LiteralType.INTEGER:
                    element_type = "int"
                elif first_elem.literal_type == LiteralType.FLOAT:
                    element_type = "float64"
                elif first_elem.literal_type == LiteralType.BOOLEAN:
                    element_type = "bool"

        elements_str = ', '.join(elements)
        return f"[]{element_type}" + "{" + elements_str + "}"

    def _generate_map(self, expr: IRMap) -> str:
        """Generate map literal."""
        if not expr.entries:
            return "map[string]interface{}{}"

        # Try to infer value type from first entry
        value_type = "interface{}"
        if expr.entries:
            first_value = next(iter(expr.entries.values()))
            if isinstance(first_value, IRLiteral):
                if first_value.literal_type == LiteralType.STRING:
                    value_type = "string"
                elif first_value.literal_type == LiteralType.INTEGER:
                    value_type = "int"
                elif first_value.literal_type == LiteralType.FLOAT:
                    value_type = "float64"
                elif first_value.literal_type == LiteralType.BOOLEAN:
                    value_type = "bool"

        entries = [
            f'"{key}": {self._generate_expression(value)}'
            for key, value in expr.entries.items()
        ]

        entries_str = ', '.join(entries)
        return f"map[string]{value_type}" + "{" + entries_str + "}"

    def _generate_ternary(self, expr: IRTernary) -> str:
        """
        Generate ternary expression.

        Go doesn't have ternary, so we convert to immediately-invoked function:
        func() T { if cond { return a } else { return b } }()

        We try to infer the return type T from the values.
        """
        cond = self._generate_expression(expr.condition)
        true_val = self._generate_expression(expr.true_value)
        false_val = self._generate_expression(expr.false_value)

        # Infer return type from values
        return_type = "interface{}"
        if isinstance(expr.true_value, IRLiteral):
            if expr.true_value.literal_type == LiteralType.STRING:
                return_type = "string"
            elif expr.true_value.literal_type == LiteralType.INTEGER:
                return_type = "int"
            elif expr.true_value.literal_type == LiteralType.FLOAT:
                return_type = "float64"
            elif expr.true_value.literal_type == LiteralType.BOOLEAN:
                return_type = "bool"

        # Use immediately-invoked function expression (valid Go)
        return f"func() {return_type} {{ if {cond} {{ return {true_val} }} else {{ return {false_val} }} }}()"

    def _generate_lambda(self, expr: IRLambda) -> str:
        """Generate lambda as anonymous function."""
        # Parameters
        params = self._generate_parameters(expr.params)

        # Body (simplified)
        if isinstance(expr.body, list):
            # Multi-statement
            return f"func({params}) {{ /* ... */ }}"
        else:
            # Single expression
            body_expr = self._generate_expression(expr.body)
            return f"func({params}) {{ return {body_expr} }}"

    # ========================================================================
    # Utilities
    # ========================================================================

    def _generate_fstring(self, expr: IRFString) -> str:
        """
        Generate f-string as fmt.Sprintf.

        Examples:
            f"Hello, {name}!" -> fmt.Sprintf("Hello, %s!", name)
            f"User {id}: {name}" -> fmt.Sprintf("User %v: %v", id, name)
        """
        if not expr.parts:
            return '""'

        # Build format string and collect arguments
        format_parts = []
        args = []

        for part in expr.parts:
            if isinstance(part, str):
                # Static string - use repr to escape properly
                escaped = repr(part)
                # repr adds quotes, remove them
                if escaped.startswith("'") and escaped.endswith("'"):
                    escaped = escaped[1:-1]
                    escaped = escaped.replace('"', '\\"')  # Escape double quotes
                elif escaped.startswith('"') and escaped.endswith('"'):
                    escaped = escaped[1:-1]
                format_parts.append(escaped)
            else:
                # Expression - add %v placeholder and collect arg
                format_parts.append("%v")
                args.append(self._generate_expression(part))

        # Generate fmt.Sprintf call
        format_str = "".join(format_parts)
        if args:
            args_str = ", ".join(args)
            # Use string concatenation to avoid f-string re-interpretation
            return 'fmt.Sprintf("' + format_str + '", ' + args_str + ')'
        else:
            # No interpolations - just return the string
            # Use string concatenation to avoid f-string re-interpretation
            return '"' + format_str + '"'

    def _generate_comprehension_as_statements(self, stmt: IRAssignment) -> List[str]:
        """
        Generate comprehension as clean statements (not IIFE).

        Python:
            result = [x * 2 for x in items if x > 0]

        Go (clean):
            result := []int{}
            for _, x := range items {
                if x > 0 {
                    result = append(result, x * 2)
                }
            }

        This is much cleaner than the IIFE approach.
        """
        comp = stmt.value
        assert isinstance(comp, IRComprehension)

        # Get target variable name
        if isinstance(stmt.target, IRIdentifier):
            target_var = stmt.target.name
        elif isinstance(stmt.target, str):
            target_var = stmt.target
        else:
            target_var = str(stmt.target)

        lines = []

        # 1. Initialize result variable
        if comp.comprehension_type == "list":
            # Infer element type if possible
            element_type = "interface{}"
            # TODO: Could use type inference here
            lines.append(f"{self.indent()}{target_var} := []{element_type}{{}}")
        elif comp.comprehension_type == "dict":
            lines.append(f"{self.indent()}{target_var} := map[string]interface{{}}{{}}")
        elif comp.comprehension_type == "set":
            lines.append(f"{self.indent()}{target_var} := map[interface{{}}]bool{{}}")
        else:
            lines.append(f"{self.indent()}{target_var} := []interface{{}}{{}}")

        # 2. Generate for loop
        iterable = self._generate_expression(comp.iterable)
        iterator = comp.iterator
        target = self._generate_expression(comp.target)

        lines.append(f"{self.indent()}for _, {iterator} := range {iterable} {{")
        self.increase_indent()

        # 3. Add condition if present
        if comp.condition:
            condition = self._generate_expression(comp.condition)
            lines.append(f"{self.indent()}if {condition} {{")
            self.increase_indent()
            lines.append(f"{self.indent()}{target_var} = append({target_var}, {target})")
            self.decrease_indent()
            lines.append(f"{self.indent()}}}")
        else:
            lines.append(f"{self.indent()}{target_var} = append({target_var}, {target})")

        self.decrease_indent()
        lines.append(f"{self.indent()}}}")

        return lines

    def _generate_ternary_as_statements(self, stmt: IRAssignment) -> List[str]:
        """
        Generate ternary as clean if/else statements (not IIFE).

        Python:
            cmd = "cls" if os.name == "nt" else "clear"

        Go (clean):
            var cmd string
            if os.Name == "nt" {
                cmd = "cls"
            } else {
                cmd = "clear"
            }

        This is much cleaner and more idiomatic than IIFE.
        """
        ternary = stmt.value
        assert isinstance(ternary, IRTernary)

        # Get target variable name
        if isinstance(stmt.target, IRIdentifier):
            target_var = stmt.target.name
        elif isinstance(stmt.target, str):
            target_var = stmt.target
        else:
            target_var = str(stmt.target)

        lines = []

        # 1. Declare variable (infer type if possible)
        var_type = "interface{}"

        # Try to infer type from true/false values
        if isinstance(ternary.true_value, IRLiteral):
            if ternary.true_value.literal_type == LiteralType.STRING:
                var_type = "string"
            elif ternary.true_value.literal_type == LiteralType.INTEGER:
                var_type = "int"
            elif ternary.true_value.literal_type == LiteralType.FLOAT:
                var_type = "float64"
            elif ternary.true_value.literal_type == LiteralType.BOOLEAN:
                var_type = "bool"

        # Check if we already have an inferred type
        if target_var in self.inferred_types:
            inferred_type = self.inferred_types[target_var]
            if inferred_type.name not in ["any", "interface{}"]:
                var_type = self._generate_type(inferred_type)

        # Declare variable
        if stmt.is_declaration:
            lines.append(f"{self.indent()}var {target_var} {var_type}")

        # 2. Generate if/else
        condition = self._generate_expression(ternary.condition)
        true_val = self._generate_expression(ternary.true_value)
        false_val = self._generate_expression(ternary.false_value)

        lines.append(f"{self.indent()}if {condition} {{")
        self.increase_indent()
        lines.append(f"{self.indent()}{target_var} = {true_val}")
        self.decrease_indent()
        lines.append(f"{self.indent()}}} else {{")
        self.increase_indent()
        lines.append(f"{self.indent()}{target_var} = {false_val}")
        self.decrease_indent()
        lines.append(f"{self.indent()}}}")

        return lines

    def _generate_comprehension_inline(self, expr: IRComprehension) -> str:
        """
        Generate Go inline function for comprehension (expression context).

        Since Go doesn't have comprehensions, we use an immediately-invoked function:
        func() []interface{} {
            result := []interface{}{}
            for _, item := range items {
                if condition {
                    result = append(result, transform)
                }
            }
            return result
        }()

        NOTE: This is only used when comprehension appears in expression context
        (e.g., as function argument). For assignments, we use _generate_comprehension_as_statements.
        """
        iterable = self._generate_expression(expr.iterable)
        iterator = expr.iterator
        target = self._generate_expression(expr.target)

        # Generate inline function
        lines = []
        lines.append("func() []interface{} {")
        lines.append("\tresult := []interface{}{}")
        lines.append(f"\tfor _, {iterator} := range {iterable} {{")

        if expr.condition:
            condition = self._generate_expression(expr.condition)
            lines.append(f"\t\tif {condition} {{")
            lines.append(f"\t\t\tresult = append(result, {target})")
            lines.append("\t\t}")
        else:
            lines.append(f"\t\tresult = append(result, {target})")

        lines.append("\t}")
        lines.append("\treturn result")
        lines.append("}()")

        return "\n".join(lines)

    def _capitalize(self, name: str) -> str:
        """
        Capitalize name for export (Go convention).

        Examples:
            user -> User
            api_key -> ApiKey
            getUserData -> GetUserData
        """
        if not name:
            return name

        # Handle snake_case
        if "_" in name:
            parts = name.split("_")
            return "".join(p.capitalize() for p in parts)

        # Handle camelCase
        return name[0].upper() + name[1:]


# ============================================================================
# Public API
# ============================================================================


def generate_go(module: IRModule) -> str:
    """
    Generate idiomatic Go code from IR module.

    Args:
        module: IR module to convert

    Returns:
        Complete Go source code

    Example:
        >>> from dsl.ir import IRModule, IRFunction, IRType
        >>> module = IRModule(name="example", version="1.0.0")
        >>> func = IRFunction(name="greet", params=[], return_type=IRType("string"))
        >>> module.functions.append(func)
        >>> code = generate_go(module)
        >>> print(code)
        package example

        func Greet() string {
        }
    """
    generator = GoGeneratorV2()
    return generator.generate(module)
