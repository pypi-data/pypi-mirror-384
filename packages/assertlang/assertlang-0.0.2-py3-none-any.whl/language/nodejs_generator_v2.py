"""
Node.js Generator V2: IR → JavaScript/TypeScript

Generates idiomatic JavaScript or TypeScript code from Promptware IR.
Supports:
- ES6+ modern JavaScript (const/let, arrow functions, template literals)
- TypeScript type annotations
- Async/await patterns
- ESM imports (not CommonJS)
- Classes with properties and methods
- Proper indentation (2 spaces - Node.js standard)

Strategy:
- Generate idiomatic modern JavaScript
- Use type_system.py for type mappings
- Handle all IR node types
- Support both JS and TS output modes
- Preserve async/await semantics
"""

from typing import List, Optional, Set

from language.library_mapping import LibraryMapper, FUNCTION_MAPPINGS, EXCEPTION_MAPPINGS, IMPORT_MAPPINGS, STRING_METHOD_MAPPINGS
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
    UnaryOperator,
)
from dsl.type_system import TypeSystem
from language.library_mapping import LibraryMapper


class NodeJSGeneratorV2:
    """Generate idiomatic JavaScript/TypeScript code from IR."""

    def __init__(self, typescript: bool = True, indent_size: int = 2):
        """
        Initialize generator.

        Args:
            typescript: Generate TypeScript (True) or JavaScript (False)
            indent_size: Number of spaces per indent level (default: 2)
        """
        self.typescript = typescript
        self.indent_size = indent_size
        self.indent_level = 0
        self.type_system = TypeSystem()
        self.library_mapper = LibraryMapper()
        self.in_class_method = False  # Track if we're inside a class method/constructor
        self.source_language: Optional[str] = None  # Track source language for mapping
        self.current_class: Optional[str] = None  # Track current class being generated
        self.in_constructor = False  # Track if we're in a constructor

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

    def generate(self, module: IRModule, typescript: Optional[bool] = None) -> str:
        """
        Generate JavaScript/TypeScript from IR module.

        Args:
            module: IR module to generate from
            typescript: Override typescript setting (optional)

        Returns:
            JavaScript or TypeScript source code
        """
        if typescript is not None:
            self.typescript = typescript

        lines = []

        # Imports
        if module.imports:
            for imp in module.imports:
                lines.append(self.generate_import(imp))
            lines.append("")

        # Type definitions (TypeScript only)
        if self.typescript and module.types:
            for type_def in module.types:
                lines.append(self.generate_type_definition(type_def))
                lines.append("")

        # Enums (TypeScript only)
        if self.typescript and module.enums:
            for enum in module.enums:
                lines.append(self.generate_enum(enum))
                lines.append("")

        # Module-level variables
        if module.module_vars:
            for var in module.module_vars:
                lines.append(self.generate_statement(var))
            lines.append("")

        # Functions
        for func in module.functions:
            lines.append(self.generate_function(func, is_export=True))
            lines.append("")

        # Classes
        for cls in module.classes:
            lines.append(self.generate_class(cls, is_export=True))
            lines.append("")

        # Join and clean up
        result = "\n".join(lines)
        # Remove excessive blank lines
        while "\n\n\n" in result:
            result = result.replace("\n\n\n", "\n\n")
        return result.strip() + "\n"

    # ========================================================================
    # Import generation
    # ========================================================================

    def generate_import(self, imp: IRImport) -> str:
        """
        Generate import statement (ESM style) with library mapping.

        Examples:
            import { tool1, tool2 } from 'module'
            import module from 'module'
            import * as alias from 'module'
        """
        # Check if this Python import needs translation
        if imp.module in IMPORT_MAPPINGS:
            js_import = IMPORT_MAPPINGS[imp.module].get("javascript")

            # None means built-in, no import needed
            if js_import is None:
                return f"// {imp.module} is built-in in JavaScript (Math, JSON, etc.)"

            # If it's a require() statement, use it directly
            if "require(" in js_import:
                return f"{js_import};"

            # Otherwise, skip the import (built-in)
            return f"// {imp.module} → built-in in JavaScript"

        # No mapping found, use original module name
        module_name = imp.module

        if imp.items:
            # Named imports: import { a, b } from 'module'
            items = ", ".join(imp.items)
            return f"import {{ {items} }} from '{module_name}';"
        elif imp.alias:
            # Default import with alias: import alias from 'module'
            return f"import {imp.alias} from '{module_name}';"
        else:
            # Side-effect import: import 'module'
            return f"import '{module_name}';"

    # ========================================================================
    # Type definition generation
    # ========================================================================

    def generate_type_definition(self, type_def: IRTypeDefinition) -> str:
        """
        Generate TypeScript interface.

        Example:
            interface User {
              id: string;
              name: string;
              age?: number;
            }
        """
        lines = []

        # JSDoc for JavaScript
        if not self.typescript and type_def.doc:
            lines.append("/**")
            lines.append(f" * {type_def.doc}")
            lines.append(" * @typedef {Object} " + type_def.name)
            for field in type_def.fields:
                optional = "?" if field.prop_type.is_optional else ""
                ts_type = self._generate_type(field.prop_type)
                lines.append(f" * @property {{{ts_type}}} {optional}{field.name}")
            lines.append(" */")
            return "\n".join(lines)

        # TypeScript interface
        lines.append(f"export interface {type_def.name} {{")
        self.increase_indent()

        for field in type_def.fields:
            optional = "?" if field.prop_type.is_optional else ""
            # Generate base type without optional wrapper for interface fields
            # The ? marker handles optionality in TypeScript interfaces
            base_type = IRType(
                name=field.prop_type.name,
                generic_args=field.prop_type.generic_args,
                is_optional=False,  # Don't wrap in | null for interfaces
                union_types=field.prop_type.union_types
            )
            ts_type = self._generate_type(base_type)
            line = f"{self.indent()}{field.name}{optional}: {ts_type};"
            lines.append(line)

        self.decrease_indent()
        lines.append("}")

        return "\n".join(lines)

    def generate_enum(self, enum: IREnum) -> str:
        """
        Generate TypeScript enum.

        Example:
            export enum Status {
              Pending = 'pending',
              Completed = 'completed',
              Failed = 'failed'
            }
        """
        if not self.typescript:
            # JavaScript: use object with frozen values
            lines = [f"export const {enum.name} = Object.freeze({{"]
            self.increase_indent()
            for variant in enum.variants:
                value = variant.value if variant.value is not None else variant.name.lower()
                if isinstance(value, str):
                    lines.append(f"{self.indent()}{variant.name}: '{value}',")
                else:
                    lines.append(f"{self.indent()}{variant.name}: {value},")
            self.decrease_indent()
            lines.append("});")
            return "\n".join(lines)

        # TypeScript enum
        lines = [f"export enum {enum.name} {{"]
        self.increase_indent()

        for i, variant in enumerate(enum.variants):
            line = f"{self.indent()}{variant.name}"
            if variant.value is not None:
                if isinstance(variant.value, str):
                    line += f" = '{variant.value}'"
                else:
                    line += f" = {variant.value}"

            # Add comma except for last item
            if i < len(enum.variants) - 1:
                line += ","
            lines.append(line)

        self.decrease_indent()
        lines.append("}")

        return "\n".join(lines)

    # ========================================================================
    # Function generation
    # ========================================================================

    def generate_function(
        self, func: IRFunction, is_export: bool = False, is_method: bool = False
    ) -> str:
        """
        Generate function declaration.

        Examples:
            export async function fetchUser(id: string): Promise<User> {
              // ...
            }

            const greet = (name: string): string => {
              return `Hello ${name}`;
            };
        """
        lines = []

        # JSDoc for JavaScript
        if not self.typescript and not is_method:
            jsdoc = self._generate_jsdoc(func)
            if jsdoc:
                lines.extend(jsdoc.split("\n"))

        # Function signature
        export_prefix = "export " if is_export and not is_method else ""
        async_prefix = "async " if func.is_async else ""

        # Method vs regular function
        if is_method:
            # Method in class
            func_name = func.name
        else:
            # Regular function
            func_name = f"function {func.name}"

        # Parameters
        params = self._generate_parameters(func.params)

        # Return type
        return_type = ""
        if self.typescript and func.return_type:
            ts_return_type = self._generate_type(func.return_type)
            if func.is_async:
                # Wrap in Promise for async functions
                return_type = f": Promise<{ts_return_type}>"
            else:
                return_type = f": {ts_return_type}"
        elif self.typescript:
            return_type = ": void"

        # Function declaration
        signature = f"{export_prefix}{async_prefix}{func_name}({params}){return_type} {{"
        lines.append(signature)

        # Set class method context
        old_in_class_method = self.in_class_method
        if is_method:
            self.in_class_method = True

        # Function body
        self.increase_indent()
        if func.body:
            for stmt in func.body:
                stmt_lines = self.generate_statement(stmt)
                lines.extend(stmt_lines.split("\n"))
        else:
            # Empty body
            lines.append(f"{self.indent()}// TODO: Implement")
        self.decrease_indent()

        # Restore context
        self.in_class_method = old_in_class_method

        lines.append("}")

        return "\n".join(lines)

    def _generate_jsdoc(self, func: IRFunction) -> Optional[str]:
        """Generate JSDoc comment for function."""
        if self.typescript:
            return None

        lines = ["/**"]

        if func.doc:
            lines.append(f" * {func.doc}")

        # Parameters
        for param in func.params:
            ts_type = self._generate_type(param.param_type)
            lines.append(f" * @param {{{ts_type}}} {param.name}")

        # Return type
        if func.return_type:
            ts_return_type = self._generate_type(func.return_type)
            if func.is_async:
                lines.append(f" * @returns {{Promise<{ts_return_type}>}}")
            else:
                lines.append(f" * @returns {{{ts_return_type}}}")

        lines.append(" */")
        return "\n".join(lines)

    def _generate_parameters(self, params: List[IRParameter]) -> str:
        """Generate function parameter list."""
        param_strs = []

        for param in params:
            param_str = param.name

            # Type annotation (TypeScript)
            if self.typescript:
                ts_type = self._generate_type(param.param_type)
                param_str += f": {ts_type}"

            # Default value
            if param.default_value:
                default = self.generate_expression(param.default_value)
                param_str += f" = {default}"

            param_strs.append(param_str)

        return ", ".join(param_strs)

    # ========================================================================
    # Class generation
    # ========================================================================

    def _generate_type(self, ir_type: IRType) -> str:
        """
        Generate TypeScript/JavaScript type from IR type.

        Handles:
        - Self type → current class name
        - Array<T> generic syntax (not Array[T])
        """
        # Handle Self type - replace with current class name
        if ir_type.name == "Self" and self.current_class:
            return self.current_class

        # Use type system for standard mapping
        ts_type = self.type_system.map_to_language(ir_type, "nodejs")

        # Fix Array[T] → Array<T> syntax for TypeScript
        if self.typescript and "[" in ts_type and "]" in ts_type:
            # Replace Array[string] with Array<string>
            # Replace List[int] with Array<number>
            ts_type = ts_type.replace("[", "<").replace("]", ">")

        return ts_type

    def generate_class(self, cls: IRClass, is_export: bool = False) -> str:
        """
        Generate class declaration.

        Example:
            export class UserService {
              private apiKey: string;
              private baseUrl: string;

              constructor(apiKey: string, baseUrl: string) {
                this.apiKey = apiKey;
                this.baseUrl = baseUrl;
              }

              async fetchUser(id: string): Promise<User> {
                // ...
              }
            }
        """
        lines = []

        # Set current class context
        old_class = self.current_class
        self.current_class = cls.name

        # Class declaration
        export_prefix = "export " if is_export else ""
        class_line = f"{export_prefix}class {cls.name}"

        # Base class
        if cls.base_classes:
            class_line += f" extends {cls.base_classes[0]}"

        class_line += " {"
        lines.append(class_line)

        self.increase_indent()

        # Properties
        if self.typescript and cls.properties:
            for prop in cls.properties:
                if prop is not None:
                    lines.append(self.generate_property(prop))

        # Constructor
        if cls.constructor:
            if self.typescript and cls.properties:
                lines.append("")  # Blank line before constructor
            lines.append(self.generate_constructor(cls.constructor))

        # Methods
        for method in cls.methods:
            lines.append("")  # Blank line before method
            method_lines = self.generate_function(method, is_method=True)
            lines.extend(method_lines.split("\n"))

        self.decrease_indent()
        lines.append("}")

        # Restore previous class context
        self.current_class = old_class

        return "\n".join(lines)

    def generate_property(self, prop: IRProperty) -> str:
        """
        Generate class property.

        Example:
            private apiKey: string;
            readonly baseUrl: string;
        """
        visibility = "private " if prop.is_private else ""
        readonly = "readonly " if prop.is_readonly else ""
        ts_type = self._generate_type(prop.prop_type)

        line = f"{self.indent()}{visibility}{readonly}{prop.name}: {ts_type};"
        return line

    def generate_constructor(self, constructor: IRFunction) -> str:
        """
        Generate class constructor.

        Example:
            constructor(apiKey: string, baseUrl: string) {
              this.apiKey = apiKey;
              this.baseUrl = baseUrl;
            }
        """
        lines = []

        # Parameters
        params = self._generate_parameters(constructor.params)

        lines.append(f"{self.indent()}constructor({params}) {{")

        # Set class method context for constructor
        old_in_class_method = self.in_class_method
        self.in_class_method = True

        # Constructor body
        self.increase_indent()
        if constructor.body:
            for stmt in constructor.body:
                stmt_lines = self.generate_statement(stmt)
                lines.extend(stmt_lines.split("\n"))
        self.decrease_indent()

        # Restore context
        self.in_class_method = old_in_class_method

        lines.append(f"{self.indent()}}}")

        return "\n".join(lines)

    # ========================================================================
    # Statement generation
    # ========================================================================

    def generate_statement(self, stmt: IRStatement) -> str:
        """Generate statement."""
        if isinstance(stmt, IRAssignment):
            return self.generate_assignment(stmt)
        elif isinstance(stmt, IRIf):
            return self.generate_if(stmt)
        elif isinstance(stmt, IRForCStyle):
            return self.generate_for_c_style(stmt)
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
            return f"{self.indent()}break;"
        elif isinstance(stmt, IRContinue):
            return f"{self.indent()}continue;"
        elif isinstance(stmt, IRPass):
            return f"{self.indent()}// pass"
        elif isinstance(stmt, IRCall):
            # Expression statement (function call)
            return f"{self.indent()}{self.generate_expression(stmt)};"
        else:
            return f"{self.indent()}// Unknown statement: {type(stmt).__name__}"

    def generate_assignment(self, stmt: IRAssignment) -> str:
        """
        Generate assignment statement.

        Examples:
            const user = await fetchUser(id);
            let count = 0;
            user.name = 'John';
            this.db = database;  // Property assignment in constructor
        """
        value_expr = self.generate_expression(stmt.value)

        # Generate target (could be variable or property access)
        if stmt.target:
            if isinstance(stmt.target, str):
                target = stmt.target
                # Check if this is a property assignment (e.g., "this.db" or "self.db")
                is_property_assignment = "." in target
            else:
                # Target is an expression (property access, array index, etc.)
                target = self.generate_expression(stmt.target)
                is_property_assignment = True  # Expressions are not simple declarations
        else:
            target = "_unknown"
            is_property_assignment = False

        if stmt.is_declaration and not is_property_assignment:
            # New variable declaration
            keyword = "const"  # Default to const (immutable)

            # Use let if reassignment might be needed (heuristic)
            # In a real implementation, we'd track variable usage
            if stmt.var_type and stmt.var_type.name in ["int", "float"]:
                keyword = "let"

            # Type annotation (TypeScript)
            type_annotation = ""
            if self.typescript and stmt.var_type:
                ts_type = self._generate_type(stmt.var_type)
                type_annotation = f": {ts_type}"

            return f"{self.indent()}{keyword} {target}{type_annotation} = {value_expr};"
        else:
            # Re-assignment or property assignment
            # For property assignments like "this.db" or "self.db", we need to convert self → this
            if self.in_class_method and isinstance(stmt.target, str) and target.startswith("self."):
                target = "this." + target[5:]  # Replace "self." with "this."

            return f"{self.indent()}{target} = {value_expr};"

    def generate_if(self, stmt: IRIf) -> str:
        """
        Generate if statement.

        Example:
            if (user === null) {
              throw new Error('User not found');
            } else {
              return user;
            }
        """
        lines = []
        condition = self.generate_expression(stmt.condition)
        lines.append(f"{self.indent()}if ({condition}) {{")

        self.increase_indent()
        for s in stmt.then_body:
            lines.append(self.generate_statement(s))
        self.decrease_indent()

        if stmt.else_body:
            lines.append(f"{self.indent()}}} else {{")
            self.increase_indent()
            for s in stmt.else_body:
                lines.append(self.generate_statement(s))
            self.decrease_indent()
            lines.append(f"{self.indent()}}}")
        else:
            lines.append(f"{self.indent()}}}")

        return "\n".join(lines)

    def generate_for(self, stmt: IRFor) -> str:
        """
        Generate for loop.

        Example:
            for (const item of items) {
              process(item);
            }
        """
        lines = []
        iterable = self.generate_expression(stmt.iterable)
        lines.append(f"{self.indent()}for (const {stmt.iterator} of {iterable}) {{")

        self.increase_indent()
        for s in stmt.body:
            lines.append(self.generate_statement(s))
        self.decrease_indent()

        lines.append(f"{self.indent()}}}")

        return "\n".join(lines)

    def generate_for_c_style(self, stmt: IRForCStyle) -> str:
        """
        Generate C-style for loop (TypeScript/JavaScript supports this natively).

        Example:
            for (let i = 0; i < 10; i = i + 1) {
                ...
            }
        """
        lines = []

        # Generate init statement
        init_line = self.generate_statement(stmt.init).strip()

        # Generate condition
        condition = self.generate_expression(stmt.condition)

        # Generate increment
        increment_line = self.generate_statement(stmt.increment).strip()

        # Build for loop header
        lines.append(f"{self.indent()}for ({init_line}; {condition}; {increment_line}) {{")

        # Generate body
        self.increase_indent()
        for s in stmt.body:
            lines.append(self.generate_statement(s))
        self.decrease_indent()

        lines.append(f"{self.indent()}}}")

        return "\n".join(lines)

    def generate_while(self, stmt: IRWhile) -> str:
        """
        Generate while loop.

        Example:
            while (count > 0) {
              count = count - 1;
            }
        """
        lines = []
        condition = self.generate_expression(stmt.condition)
        lines.append(f"{self.indent()}while ({condition}) {{")

        self.increase_indent()
        for s in stmt.body:
            lines.append(self.generate_statement(s))
        self.decrease_indent()

        lines.append(f"{self.indent()}}}")

        return "\n".join(lines)

    def generate_try(self, stmt: IRTry) -> str:
        """
        Generate try-catch statement.

        Example:
            try {
              const result = await riskyOperation();
            } catch (error) {
              console.error(error);
            } finally {
              cleanup();
            }
        """
        lines = []
        lines.append(f"{self.indent()}try {{")

        self.increase_indent()
        if stmt.try_body:
            for s in stmt.try_body:
                lines.append(self.generate_statement(s))
        else:
            lines.append(f"{self.indent()}// Empty try block")
        self.decrease_indent()

        # Generate catch blocks
        if stmt.catch_blocks:
            for catch in stmt.catch_blocks:
                error_var = catch.exception_var or "error"

                # TypeScript: type annotation for catch parameter
                type_annotation = ""
                if self.typescript and catch.exception_type:
                    # Map Python exception type to JavaScript
                    js_exception = EXCEPTION_MAPPINGS.get(catch.exception_type, {}).get("javascript", "Error")
                    type_annotation = f": {js_exception}"

                lines.append(f"{self.indent()}}} catch ({error_var}{type_annotation}) {{")

                self.increase_indent()
                if catch.body:
                    for s in catch.body:
                        lines.append(self.generate_statement(s))
                else:
                    lines.append(f"{self.indent()}// Empty catch block")
                self.decrease_indent()

        # Generate finally block
        if stmt.finally_body:
            lines.append(f"{self.indent()}}} finally {{")
            self.increase_indent()
            for s in stmt.finally_body:
                lines.append(self.generate_statement(s))
            self.decrease_indent()
            lines.append(f"{self.indent()}}}")
        else:
            # Close the try or last catch block
            lines.append(f"{self.indent()}}}")

        return "\n".join(lines)

    def generate_return(self, stmt: IRReturn) -> str:
        """
        Generate return statement.

        Example:
            return { status: 'ok', data: result };
        """
        if stmt.value:
            value = self.generate_expression(stmt.value)
            return f"{self.indent()}return {value};"
        else:
            return f"{self.indent()}return;"

    def generate_throw(self, stmt: IRThrow) -> str:
        """
        Generate throw statement.

        Example:
            throw new Error('Invalid input');
        """
        exception = self.generate_expression(stmt.exception)
        return f"{self.indent()}throw {exception};"

    # ========================================================================
    # Expression generation
    # ========================================================================

    def generate_expression(self, expr: IRExpression) -> str:
        """Generate expression."""
        if isinstance(expr, IRLiteral):
            return self.generate_literal(expr)
        elif isinstance(expr, IRIdentifier):
            # Convert 'self' to 'this' in class methods
            if expr.name == "self" and self.in_class_method:
                return "this"
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
            prop = expr.property

            # Map Python string methods to JavaScript equivalents
            if prop in STRING_METHOD_MAPPINGS:
                js_method = STRING_METHOD_MAPPINGS[prop].get("javascript")
                if js_method:
                    prop = js_method

            return f"{obj}.{prop}"
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
        elif isinstance(expr, IRFString):
            return self.generate_fstring(expr)
        elif isinstance(expr, IRComprehension):
            return self.generate_comprehension(expr)
        else:
            # Unknown expression type - generate valid null fallback
            return "null"

    def generate_literal(self, lit: IRLiteral) -> str:
        """
        Generate literal value.

        Examples:
            "hello world"
            42
            3.14
            true
            null
        """
        if lit.literal_type == LiteralType.STRING:
            # Use template literals for strings (modern JS)
            value = str(lit.value).replace("\\", "\\\\").replace("`", "\\`")
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
        """
        Generate binary operation.

        Examples:
            a + b
            x === y
            count > 0
        """
        left = self.generate_expression(expr.left)
        right = self.generate_expression(expr.right)

        # Map IR operators to JavaScript operators
        op_map = {
            BinaryOperator.ADD: "+",
            BinaryOperator.SUBTRACT: "-",
            BinaryOperator.MULTIPLY: "*",
            BinaryOperator.DIVIDE: "/",
            BinaryOperator.MODULO: "%",
            BinaryOperator.POWER: "**",
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
            BinaryOperator.LEFT_SHIFT: "<<",
            BinaryOperator.RIGHT_SHIFT: ">>",
            BinaryOperator.IN: "in",
            BinaryOperator.NOT_IN: "!in",  # No direct equivalent
            BinaryOperator.IS: "===",
            BinaryOperator.IS_NOT: "!==",
        }

        op = op_map.get(expr.op, expr.op.value)

        # Add parentheses for clarity
        return f"({left} {op} {right})"

    def generate_unary_op(self, expr: IRUnaryOp) -> str:
        """
        Generate unary operation.

        Examples:
            !condition
            -count
            +value
        """
        operand = self.generate_expression(expr.operand)

        # Map IR unary operators to JavaScript
        op_map = {
            UnaryOperator.NOT: "!",
            UnaryOperator.NEGATE: "-",
            UnaryOperator.POSITIVE: "+",
            UnaryOperator.BIT_NOT: "~",
        }

        op = op_map.get(expr.op, expr.op.value)
        return f"{op}{operand}"

    def generate_call(self, expr: IRCall) -> str:
        """
        Generate function call with library mapping support.

        Examples:
            fetchUser(id)
            database.query('SELECT * FROM users')
            process(x, y, { option: true })
            Math.sqrt(4)  # mapped from math.sqrt
            console.log('hello')  # mapped from print
        """
        # Try to map the function if it's a property access (e.g., math.sqrt)
        func = self.generate_expression(expr.function)

        # Check if this is a stdlib call that needs mapping
        if isinstance(expr.function, IRPropertyAccess):
            # Special case: Python string methods with reversed arg order
            # "sep".join(array) → array.join("sep")
            if expr.function.property == "join" and isinstance(expr.function.object, IRLiteral):
                if expr.function.object.literal_type == LiteralType.STRING and len(expr.args) == 1:
                    separator = self.generate_expression(expr.function.object)
                    array = self.generate_expression(expr.args[0])
                    return f"{array}.join({separator})"

            # Handle module.function pattern (e.g., math.sqrt)
            obj_name = expr.function.object.name if isinstance(expr.function.object, IRIdentifier) else None
            if obj_name:
                py_call = f"{obj_name}.{expr.function.property}"
                if py_call in FUNCTION_MAPPINGS:
                    mapped = FUNCTION_MAPPINGS[py_call].get("javascript")
                    if mapped:
                        func = mapped
        elif isinstance(expr.function, IRIdentifier):
            # Handle built-in functions (e.g., print, range)
            func_name = expr.function.name

            # Special case: len() → .length (property access, not function call)
            if func_name == "len" and len(expr.args) == 1:
                obj = self.generate_expression(expr.args[0])
                return f"{obj}.length"

            # Special case: range() → Array.from() with proper arguments
            if func_name == "range":
                if len(expr.args) == 1:
                    # range(n) → Array.from({length: n}, (_, i) => i)
                    n = self.generate_expression(expr.args[0])
                    return f"Array.from({{length: {n}}}, (_, i) => i)"
                elif len(expr.args) == 2:
                    # range(start, stop) → Array.from({length: stop-start}, (_, i) => i+start)
                    start = self.generate_expression(expr.args[0])
                    stop = self.generate_expression(expr.args[1])
                    return f"Array.from({{length: {stop}-{start}}}, (_, i) => i+{start})"
                elif len(expr.args) == 3:
                    # range(start, stop, step) → Array.from with step calculation
                    start = self.generate_expression(expr.args[0])
                    stop = self.generate_expression(expr.args[1])
                    step = self.generate_expression(expr.args[2])
                    return f"Array.from({{length: Math.ceil(({stop}-{start})/{step})}}, (_, i) => {start}+i*{step})"

            # Other built-ins (print, etc.)
            if func_name in FUNCTION_MAPPINGS:
                mapped = FUNCTION_MAPPINGS[func_name].get("javascript")
                if mapped:
                    func = mapped

        # Positional arguments
        args = [self.generate_expression(arg) for arg in expr.args]

        # Named arguments (convert to object)
        if expr.kwargs:
            kwargs_obj = "{ " + ", ".join(
                f"{k}: {self.generate_expression(v)}" for k, v in expr.kwargs.items()
            ) + " }"
            args.append(kwargs_obj)

        return f"{func}({', '.join(args)})"

    def generate_array(self, expr: IRArray) -> str:
        """
        Generate array literal.

        Example:
            [1, 2, 3]
        """
        elements = [self.generate_expression(el) for el in expr.elements]
        return f"[{', '.join(elements)}]"

    def generate_map(self, expr: IRMap) -> str:
        """
        Generate object literal.

        Example:
            { name: 'John', age: 30 }
        """
        if not expr.entries:
            return "{}"

        entries = []
        for key, value in expr.entries.items():
            value_str = self.generate_expression(value)
            # Quote key if it's not a valid identifier
            if not key.isidentifier():
                entries.append(f'"{key}": {value_str}')
            else:
                entries.append(f"{key}: {value_str}")

        return "{ " + ", ".join(entries) + " }"

    def generate_ternary(self, expr: IRTernary) -> str:
        """
        Generate ternary conditional.

        Example:
            condition ? trueValue : falseValue
        """
        condition = self.generate_expression(expr.condition)
        true_val = self.generate_expression(expr.true_value)
        false_val = self.generate_expression(expr.false_value)
        return f"({condition} ? {true_val} : {false_val})"

    def generate_lambda(self, expr: IRLambda) -> str:
        """
        Generate arrow function.

        Examples:
            (x) => x * 2
            (x, y) => x + y
            (user) => {
              return user.name;
            }
        """
        # Parameters
        if len(expr.params) == 1:
            params = expr.params[0].name
        else:
            param_strs = []
            for param in expr.params:
                param_str = param.name
                if self.typescript:
                    ts_type = self._generate_type(param.param_type)
                    param_str += f": {ts_type}"
                param_strs.append(param_str)
            params = f"({', '.join(param_strs)})"

        # Body
        if isinstance(expr.body, list):
            # Multi-statement body
            lines = [f"{params} => {{"]
            self.increase_indent()
            for stmt in expr.body:
                stmt_lines = self.generate_statement(stmt)
                lines.append(stmt_lines)
            self.decrease_indent()
            lines.append("}")
            return "\n".join(lines)
        else:
            # Single expression
            body = self.generate_expression(expr.body)
            return f"{params} => {body}"

    def generate_fstring(self, expr: IRFString) -> str:
        """
        Generate template literal from f-string.

        Examples:
            f"Hello, {name}!" -> `Hello, ${name}!`
            f"User {user.id}: {user.name}" -> `User ${user.id}: ${user.name}`
        """
        if not expr.parts:
            return '""'

        # Build template literal
        template_parts = []
        for part in expr.parts:
            if isinstance(part, str):
                # Static string - escape backticks and backslashes
                escaped = part.replace("\\", "\\\\").replace("`", "\\`")
                template_parts.append(escaped)
            else:
                # Expression - convert to ${...}
                expr_str = self.generate_expression(part)
                template_parts.append(f"${{{expr_str}}}")

        # Join all parts into a single template literal
        content = "".join(template_parts)
        return f"`{content}`"

    def generate_comprehension(self, expr: IRComprehension) -> str:
        """
        Generate JavaScript array methods from IRComprehension.

        Examples:
            [x * 2 for x in items] -> items.map(x => x * 2)
            [x for x in items if x > 0] -> items.filter(x => x > 0)
            [x * 2 for x in items if x > 0] -> items.filter(x => x > 0).map(x => x * 2)
        """
        iterable = self.generate_expression(expr.iterable)
        iterator = expr.iterator
        element = self.generate_expression(expr.target)

        # Check if element is just the iterator (no transformation)
        is_identity = (isinstance(expr.target, IRIdentifier) and
                      expr.target.name == iterator)

        # Build the result
        if expr.condition:
            # Has filter condition
            condition = self.generate_expression(expr.condition)
            filter_lambda = f"{iterator} => {condition}"

            if is_identity:
                # Just filter, no map: items.filter(x => x > 0)
                return f"{iterable}.filter({filter_lambda})"
            else:
                # Filter + map: items.filter(x => x > 0).map(x => x * 2)
                map_lambda = f"{iterator} => {element}"
                return f"{iterable}.filter({filter_lambda}).map({map_lambda})"
        else:
            # No filter, just transformation
            if is_identity:
                # No-op: just return the iterable (rare case)
                return iterable
            else:
                # Just map: items.map(x => x * 2)
                map_lambda = f"{iterator} => {element}"
                return f"{iterable}.map({map_lambda})"


# ============================================================================
# Public API
# ============================================================================


def generate_nodejs(module: IRModule, typescript: bool = True) -> str:
    """
    Generate JavaScript or TypeScript code from IR module.

    Args:
        module: IR module to generate from
        typescript: Generate TypeScript (True) or JavaScript (False)

    Returns:
        JavaScript or TypeScript source code

    Examples:
        >>> from dsl.ir import IRModule, IRFunction, IRType
        >>> module = IRModule(name="example", functions=[...])
        >>> ts_code = generate_nodejs(module, typescript=True)
        >>> js_code = generate_nodejs(module, typescript=False)
    """
    generator = NodeJSGeneratorV2(typescript=typescript)
    return generator.generate(module)
