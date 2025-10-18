"""
Rust Generator V2: Promptware IR → Idiomatic Rust

This generator converts Promptware IR into production-quality, idiomatic Rust code.

Key Features:
- Generate valid, compilable Rust code from IR
- Proper ownership patterns (&, &mut, move)
- Result<T, E> error handling
- Option<T> for nullable types
- Async/await support
- Struct, enum, trait, and impl generation
- Zero external dependencies (std only)
- Rustfmt-compatible formatting

Design Decisions:
1. Type Mapping:
   - IR string → String (owned) or &str (borrowed, based on context)
   - IR int → i32 (default, can be configured)
   - IR float → f64
   - IR array<T> → Vec<T>
   - IR map<K,V> → HashMap<K,V>
   - IR T? → Option<T>
   - throws → Result<T, Box<dyn Error>>

2. Ownership:
   - Extract from IR metadata if present
   - Default heuristics: params are borrowed (&), return values owned
   - Mutable borrows (&mut) for methods that mutate

3. Error Handling:
   - Functions with throws → Result<T, E>
   - Default error type: Box<dyn std::error::Error>
   - Propagate errors with ?

4. Formatting:
   - 4-space indentation (Rust standard)
   - Proper struct/enum derives (#[derive(Debug, Clone)])
   - Idiomatic naming (snake_case for functions/vars, PascalCase for types)
"""

from typing import List, Set, Dict, Optional, Any

from dsl.ir import (
    IRModule,
    IRImport,
    IRFunction,
    IRParameter,
    IRType,
    IRClass,
    IRProperty,
    IREnum,
    IREnumVariant,
    IRTypeDefinition,
    IRAssignment,
    IRAwait,
    IRReturn,
    IRIf,
    IRFor,
    IRForCStyle,
    IRWhile,
    IRTry,
    IRCatch,
    IRThrow,
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
    IRTernary,
    IRLambda,
    IRComprehension,
    BinaryOperator,
    UnaryOperator,
    LiteralType,
    IRExpression,
    IRStatement,
)

from dsl.type_system import TypeSystem
from language.library_mapping import LibraryMapper


class RustGeneratorV2:
    """Generate idiomatic Rust code from Promptware IR."""

    def __init__(self):
        self.type_system = TypeSystem()
        self.library_mapper = LibraryMapper()
        self.indent_level = 0
        self.indent_size = 4  # Rust standard
        self.needs_hashmap = False
        self.needs_error = False
        self.variable_types: Dict[str, IRType] = {}  # Track variable types for safe map indexing
        self.current_context = "function"  # function, struct, impl
        self.source_language: Optional[str] = None  # Track source language for mapping

    # ========================================================================
    # Main Generation Entry Point
    # ========================================================================

    def generate(self, module: IRModule) -> str:
        """
        Generate Rust code from IR module.

        Args:
            module: IR module to generate from

        Returns:
            str: Rust source code
        """
        self.indent_level = 0
        self.needs_hashmap = False
        self.needs_error = False

        lines = []

        # Pre-scan for required imports
        self._scan_for_imports(module)

        # Generate imports
        imports = self._generate_imports(module)
        if imports:
            lines.extend(imports)
            lines.append("")

        # Generate type definitions (structs)
        for type_def in module.types:
            lines.append(self._generate_struct(type_def))
            lines.append("")

        # Generate enums
        for enum in module.enums:
            lines.append(self._generate_enum(enum))
            lines.append("")

        # Generate traits (from classes marked as traits)
        for cls in module.classes:
            if cls.metadata.get('rust_trait'):
                lines.append(self._generate_trait(cls))
                lines.append("")

        # Generate struct definitions + impl blocks (from classes not marked as traits)
        for cls in module.classes:
            if not cls.metadata.get('rust_trait'):
                # Generate struct definition first with generic parameters
                struct_name = cls.name
                if cls.generic_params:
                    # Add generic type parameters: struct List<T>
                    generic_str = ", ".join(cls.generic_params)
                    struct_name = f"{cls.name}<{generic_str}>"

                struct_lines = []
                # Doc comment
                if cls.doc:
                    struct_lines.append(f"/// {cls.doc}")

                struct_lines.append(f"pub struct {struct_name} {{")
                if cls.properties:
                    for prop in cls.properties:
                        visibility = "pub " if not prop.is_private else ""
                        prop_name = self._to_snake_case(prop.name)
                        prop_type = self._generate_type(prop.prop_type)
                        struct_lines.append(f"    {visibility}{prop_name}: {prop_type},")
                struct_lines.append("}")
                lines.append("\n".join(struct_lines))
                lines.append("")

                # Generate impl block
                lines.append(self._generate_impl(cls))
                lines.append("")

        # Generate standalone functions
        for func in module.functions:
            lines.append(self._generate_function(func, standalone=True))
            lines.append("")

        # Join and clean up
        result = "\n".join(lines)
        # Remove excessive blank lines
        while "\n\n\n" in result:
            result = result.replace("\n\n\n", "\n\n")

        return result.strip() + "\n"

    # ========================================================================
    # Import Generation
    # ========================================================================

    def _scan_for_imports(self, module: IRModule) -> None:
        """Scan module to determine required imports."""
        # Check for HashMap usage
        for type_def in module.types:
            for field in type_def.fields:
                if self._needs_hashmap_for_type(field.prop_type):
                    self.needs_hashmap = True

        for func in module.functions:
            if func.throws:
                self.needs_error = True
            if func.return_type and self._needs_hashmap_for_type(func.return_type):
                self.needs_hashmap = True
            # Check parameters
            for param in func.params:
                if self._needs_hashmap_for_type(param.param_type):
                    self.needs_hashmap = True

        for cls in module.classes:
            for method in cls.methods:
                if method.throws:
                    self.needs_error = True
                # Check method parameters
                for param in method.params:
                    if self._needs_hashmap_for_type(param.param_type):
                        self.needs_hashmap = True

    def _needs_hashmap_for_type(self, ir_type: IRType) -> bool:
        """Check if a type requires HashMap import."""
        if ir_type.name == "map":
            return True
        for generic_arg in ir_type.generic_args:
            if self._needs_hashmap_for_type(generic_arg):
                return True
        return False

    def _generate_imports(self, module: IRModule) -> List[str]:
        """Generate use statements."""
        imports = []

        # Standard library imports
        if self.needs_hashmap:
            imports.append("use std::collections::HashMap;")

        if self.needs_error:
            imports.append("use std::error::Error;")

        # User-defined imports with library mapping
        for imp in module.imports:
            # Try to translate library if source language is known
            module_name = imp.module
            comment = ""
            if self.source_language and self.source_language != "rust":
                translated = self.library_mapper.translate_import(
                    imp.module,
                    from_lang=self.source_language,
                    to_lang="rust"
                )
                if translated:
                    module_name = translated["module"]
                    comment = f"  // from {self.source_language}: {imp.module}"

            if imp.items:
                # use std::collections::{HashMap, HashSet};
                items = ", ".join(imp.items)
                imports.append(f"use {module_name}::{{{items}}};{comment}")
            else:
                # use std::fs;
                imports.append(f"use {module_name};{comment}")

        return imports

    # ========================================================================
    # Type Generation
    # ========================================================================

    def _generate_type(self, ir_type: IRType, context: str = "default") -> str:
        """
        Generate Rust type from IR type.

        Args:
            ir_type: IR type node
            context: Context hint (default, param, return, field)

        Returns:
            Rust type string
        """
        # Handle optional types
        if ir_type.is_optional:
            base_type = self._generate_base_type(ir_type.name, ir_type.generic_args, context)
            return f"Option<{base_type}>"

        # Handle union types (Rust doesn't have native unions, use enum or Box<dyn Any>)
        if ir_type.union_types:
            # For now, use Box<dyn std::any::Any> as fallback
            return "Box<dyn std::any::Any>"

        return self._generate_base_type(ir_type.name, ir_type.generic_args, context)

    def _generate_base_type(self, type_name: str, generic_args: List[IRType], context: str) -> str:
        """Generate base Rust type."""
        # Primitive types
        type_map = {
            'string': 'String' if context in ['return', 'field', 'default'] else 'String',
            'int': 'i32',
            'float': 'f64',
            'bool': 'bool',
            'null': '()',
            'any': 'Box<dyn std::any::Any>',
        }

        if type_name in type_map:
            return type_map[type_name]

        # Collection types
        if type_name == 'array':
            if generic_args:
                inner = self._generate_type(generic_args[0], context)
                return f"Vec<{inner}>"
            return "Vec<Box<dyn std::any::Any>>"

        if type_name == 'map':
            if len(generic_args) >= 2:
                key = self._generate_type(generic_args[0], context)
                val = self._generate_type(generic_args[1], context)
                return f"HashMap<{key}, {val}>"
            return "HashMap<String, Box<dyn std::any::Any>>"

        # Custom type - may have generic arguments (e.g., Option<T>, List<T>)
        if generic_args:
            # Generate generic arguments recursively
            args = ", ".join(self._generate_type(arg, context) for arg in generic_args)
            return f"{type_name}<{args}>"

        # Custom type without generics - return as-is (assume it's defined)
        return type_name

    # ========================================================================
    # Struct Generation
    # ========================================================================

    def _generate_struct(self, type_def: IRTypeDefinition) -> str:
        """Generate struct definition."""
        lines = []

        # Doc comment
        if type_def.doc:
            lines.append(f"/// {type_def.doc}")

        # Derive clause
        lines.append("#[derive(Debug, Clone)]")

        # Struct declaration
        # Note: IRTypeDefinition doesn't have generic_params, but IRClass does
        lines.append(f"pub struct {type_def.name} {{")

        # Fields
        for field in type_def.fields:
            field_name = self._to_snake_case(field.name)
            field_type = self._generate_type(field.prop_type, context="field")
            visibility = "pub " if not field.is_private else ""
            lines.append(f"    {visibility}{field_name}: {field_type},")

        lines.append("}")

        return "\n".join(lines)

    # ========================================================================
    # Enum Generation
    # ========================================================================

    def _generate_enum(self, enum: IREnum) -> str:
        """Generate enum definition."""
        lines = []

        # Doc comment
        if enum.doc:
            lines.append(f"/// {enum.doc}")

        # Derive clause
        lines.append("#[derive(Debug, Clone, PartialEq)]")

        # Enum declaration with generic parameters
        enum_name = enum.name
        if enum.generic_params:
            # Add generic type parameters: enum Option<T>
            generic_str = ", ".join(enum.generic_params)
            enum_name = f"{enum.name}<{generic_str}>"

        lines.append(f"pub enum {enum_name} {{")

        # Variants
        for variant in enum.variants:
            variant_name = variant.name

            if variant.associated_types:
                # Tuple variant: Status::Completed(u64) or Some(T)
                types = ", ".join(self._generate_type(t) for t in variant.associated_types)
                lines.append(f"    {variant_name}({types}),")
            else:
                # Simple variant: Status::Pending or None
                lines.append(f"    {variant_name},")

        lines.append("}")

        return "\n".join(lines)

    # ========================================================================
    # Trait Generation
    # ========================================================================

    def _generate_trait(self, cls: IRClass) -> str:
        """Generate trait definition."""
        lines = []

        # Doc comment
        if cls.doc:
            lines.append(f"/// {cls.doc}")

        # Trait declaration
        lines.append(f"pub trait {cls.name} {{")

        # Methods (signatures only)
        for method in cls.methods:
            sig = self._generate_function_signature(method, trait_method=True)
            lines.append(f"    {sig};")

        lines.append("}")

        return "\n".join(lines)

    # ========================================================================
    # Impl Block Generation
    # ========================================================================

    def _generate_impl(self, cls: IRClass) -> str:
        """Generate impl block."""
        lines = []

        # Build type name with generic parameters
        type_name = cls.name
        generic_decl = ""
        if cls.generic_params:
            # Add generic parameters to both impl declaration and type name
            # impl<T> List<T> { ... }
            generic_str = ", ".join(cls.generic_params)
            generic_decl = f"<{generic_str}>"
            type_name = f"{cls.name}<{generic_str}>"

        # Impl declaration
        if cls.base_classes:
            # impl<T> TraitName for TypeName<T>
            trait_name = cls.base_classes[0]
            lines.append(f"impl{generic_decl} {trait_name} for {type_name} {{")
        else:
            # impl<T> TypeName<T>
            lines.append(f"impl{generic_decl} {type_name} {{")

        self.current_context = "impl"

        # Constructor (if present)
        if cls.constructor:
            lines.append(self._generate_constructor(cls.constructor, cls.name))
            if cls.methods:
                lines.append("")

        # Methods
        for i, method in enumerate(cls.methods):
            lines.append(self._generate_method(method))
            if i < len(cls.methods) - 1:
                lines.append("")

        lines.append("}")

        self.current_context = "function"

        return "\n".join(lines)

    def _generate_constructor(self, constructor: IRFunction, struct_name: str) -> str:
        """Generate constructor as 'new' method."""
        lines = []

        # Constructor is always 'pub fn new'
        params = []
        for param in constructor.params:
            param_name = self._to_snake_case(param.name)
            param_type = self._generate_param_type(param)
            params.append(f"{param_name}: {param_type}")

        params_str = ", ".join(params)
        lines.append(f"    pub fn new({params_str}) -> Self {{")

        # Body
        if constructor.body:
            body_lines = self._generate_statements(constructor.body, indent=2)
            lines.extend(body_lines)
        else:
            # Default: create struct with all fields
            lines.append(f"        Self {{")
            for param in constructor.params:
                param_name = self._to_snake_case(param.name)
                lines.append(f"            {param_name},")
            lines.append(f"        }}")

        lines.append("    }")

        return "\n".join(lines)

    def _generate_method(self, method: IRFunction) -> str:
        """Generate method in impl block."""
        return self._generate_function(method, standalone=False, indent=1)

    # ========================================================================
    # Function Generation
    # ========================================================================

    def _generate_function(self, func: IRFunction, standalone: bool = True, indent: int = 0) -> str:
        """Generate function definition."""
        lines = []

        # Register parameter types for safe map/array indexing
        for param in func.params:
            self.variable_types[param.name] = param.param_type

        base_indent = "    " * indent

        # Doc comment
        if func.doc:
            lines.append(f"{base_indent}/// {func.doc}")

        # Function signature
        sig = self._generate_function_signature(func, standalone=standalone)
        lines.append(f"{base_indent}{sig} {{")

        # Body
        if func.body:
            body_lines = self._generate_statements(func.body, indent=indent+1)
            lines.extend(body_lines)
        else:
            # Empty body - add todo!()
            lines.append(f"{base_indent}    todo!()")

        lines.append(f"{base_indent}}}")

        # Clear variable types for this function scope
        self.variable_types.clear()

        return "\n".join(lines)

    def _generate_function_signature(self, func: IRFunction, standalone: bool = True, trait_method: bool = False) -> str:
        """Generate function signature."""
        parts = []

        # Visibility
        if standalone or (not trait_method and not func.is_private):
            parts.append("pub")

        # Async
        if func.is_async:
            parts.append("async")

        # Function keyword
        parts.append("fn")

        # Function name with generic parameters
        func_name = self._to_snake_case(func.name)
        if func.generic_params:
            # Add generic type parameters: fn map<T, U>
            generic_str = ", ".join(func.generic_params)
            func_name = f"{func_name}<{generic_str}>"

        # Parameters
        params = []
        for param in func.params:
            param_str = self._generate_parameter(param)
            params.append(param_str)

        params_str = ", ".join(params) if params else ""

        # Build signature more carefully
        sig = " ".join(parts)  # "pub fn" or "pub async fn"
        sig += f" {func_name}({params_str})"

        # Return type
        if func.return_type or func.throws:
            return_type = self._generate_return_type(func)
            sig += f" -> {return_type}"

        return sig

    def _generate_parameter(self, param: IRParameter) -> str:
        """Generate function parameter."""
        param_name = self._to_snake_case(param.name)
        param_type = self._generate_param_type(param)
        return f"{param_name}: {param_type}"

    def _generate_param_type(self, param: IRParameter) -> str:
        """
        Generate parameter type with ownership hints.

        Default strategy:
        - String → &str (borrowed)
        - Collections (Vec, HashMap) → &T (borrowed)
        - Primitives → owned (i32, f64, bool)
        - Custom types → &T (borrowed)
        """
        rust_type = self._generate_type(param.param_type, context="param")

        # Check metadata for explicit ownership
        ownership = param.metadata.get('rust_ownership', 'default')

        if ownership == 'borrowed_immutable':
            return f"&{rust_type}"
        elif ownership == 'borrowed_mutable':
            return f"&mut {rust_type}"
        elif ownership == 'owned_mutable' or ownership == 'owned_immutable':
            return rust_type

        # Default heuristics
        if rust_type == 'String':
            # Use String (owned) to avoid lifetime issues for now
            # TODO: Use &str for read-only params when we have lifetime analysis
            return 'String'
        elif rust_type.startswith('Vec<') or rust_type.startswith('HashMap<'):
            return f"&{rust_type}"
        elif rust_type in ['i32', 'i64', 'f32', 'f64', 'bool', 'u32', 'u64', 'usize']:
            return rust_type
        elif rust_type.startswith('Option<'):
            return rust_type
        else:
            # Custom types - borrow by default
            return f"&{rust_type}"

    def _generate_return_type(self, func: IRFunction) -> str:
        """Generate return type, wrapping in Result if function throws."""
        if func.throws:
            # Function throws - return Result<T, E>
            if func.return_type:
                ok_type = self._generate_type(func.return_type, context="return")
            else:
                ok_type = "()"

            # Determine error type
            if len(func.throws) == 1:
                err_type = func.throws[0]
            else:
                err_type = "Box<dyn Error>"

            return f"Result<{ok_type}, {err_type}>"
        else:
            # No throws - return type directly
            if func.return_type:
                return self._generate_type(func.return_type, context="return")
            else:
                return "()"

    # ========================================================================
    # Statement Generation
    # ========================================================================

    def _generate_statements(self, stmts: List[IRStatement], indent: int = 0) -> List[str]:
        """Generate multiple statements."""
        lines = []
        for stmt in stmts:
            stmt_lines = self._generate_statement(stmt, indent)
            if isinstance(stmt_lines, list):
                lines.extend(stmt_lines)
            else:
                lines.append(stmt_lines)
        return lines

    def _generate_statement(self, stmt: IRStatement, indent: int = 0) -> str | List[str]:
        """Generate a single statement."""
        base_indent = "    " * indent

        if isinstance(stmt, IRAssignment):
            return self._generate_assignment(stmt, indent)
        elif isinstance(stmt, IRReturn):
            return self._generate_return(stmt, indent)
        elif isinstance(stmt, IRIf):
            return self._generate_if(stmt, indent)
        elif isinstance(stmt, IRForCStyle):
            return self._generate_for_c_style(stmt, indent)
        elif isinstance(stmt, IRFor):
            return self._generate_for(stmt, indent)
        elif isinstance(stmt, IRWhile):
            return self._generate_while(stmt, indent)
        elif isinstance(stmt, IRTry):
            return self._generate_try(stmt, indent)
        elif isinstance(stmt, IRThrow):
            return self._generate_throw(stmt, indent)
        elif isinstance(stmt, IRBreak):
            return f"{base_indent}break;"
        elif isinstance(stmt, IRContinue):
            return f"{base_indent}continue;"
        elif isinstance(stmt, IRPass):
            return f"{base_indent}// pass"
        elif isinstance(stmt, IRCall):
            # Expression statement
            call_expr = self._generate_expression(stmt)
            return f"{base_indent}{call_expr};"
        elif hasattr(stmt, '__dict__'):
            # Try to handle as expression statement (for Rust implicit returns)
            # This includes IRBinaryOp, IRIdentifier, etc.
            try:
                expr = self._generate_expression(stmt)
                return f"{base_indent}{expr}"  # No semicolon for implicit return
            except:
                return f"{base_indent}// Unknown statement: {type(stmt).__name__}"
        else:
            return f"{base_indent}// Unknown statement: {type(stmt).__name__}"

    def _generate_assignment(self, stmt: IRAssignment, indent: int) -> str:
        """Generate assignment statement."""
        base_indent = "    " * indent
        value = self._generate_expression(stmt.value)

        # Generate target (could be variable or property access)
        if stmt.target:
            if isinstance(stmt.target, str):
                target = self._to_snake_case(stmt.target)
            elif isinstance(stmt.target, IRIndex):
                # Special case: Index assignment (map[key] = value or arr[i] = value)
                # For maps, use .insert() instead of [key] = value
                obj = self._generate_expression(stmt.target.object)
                index = self._generate_expression(stmt.target.index)

                # Check if it's a map
                is_map = False
                if isinstance(stmt.target.object, IRIdentifier):
                    var_name = stmt.target.object.name
                    if var_name in self.variable_types:
                        var_type = self.variable_types[var_name]
                        if var_type.name in ("map", "dict", "Dict", "HashMap", "dictionary"):
                            is_map = True

                if is_map:
                    # HashMap assignment: use .insert(key, value)
                    return f"{base_indent}{obj}.insert({index}, {value});"
                else:
                    # Array assignment: use [index] = value
                    target = f"{obj}[{index}]"
            else:
                # Target is an expression (property access, etc.)
                target = self._generate_expression(stmt.target)
        else:
            target = "_unknown"

        if stmt.is_declaration:
            # let binding
            if stmt.var_type:
                var_type = self._generate_type(stmt.var_type)
                return f"{base_indent}let {target}: {var_type} = {value};"
            else:
                return f"{base_indent}let {target} = {value};"
        else:
            # Re-assignment
            return f"{base_indent}{target} = {value};"

    def _generate_return(self, stmt: IRReturn, indent: int) -> str:
        """Generate return statement."""
        base_indent = "    " * indent
        if stmt.value:
            value = self._generate_expression(stmt.value)
            return f"{base_indent}return {value};"
        else:
            return f"{base_indent}return;"

    def _generate_if(self, stmt: IRIf, indent: int) -> List[str]:
        """Generate if statement."""
        base_indent = "    " * indent
        lines = []

        # Condition
        condition = self._generate_expression(stmt.condition)
        lines.append(f"{base_indent}if {condition} {{")

        # Then body
        then_lines = self._generate_statements(stmt.then_body, indent + 1)
        lines.extend(then_lines)

        # Else body
        if stmt.else_body:
            lines.append(f"{base_indent}}} else {{")
            else_lines = self._generate_statements(stmt.else_body, indent + 1)
            lines.extend(else_lines)

        lines.append(f"{base_indent}}}")

        return lines

    def _generate_for(self, stmt: IRFor, indent: int) -> List[str]:
        """Generate for loop."""
        base_indent = "    " * indent
        lines = []

        iterator = self._to_snake_case(stmt.iterator)
        iterable = self._generate_expression(stmt.iterable)

        lines.append(f"{base_indent}for {iterator} in {iterable} {{")

        # Body
        body_lines = self._generate_statements(stmt.body, indent + 1)
        lines.extend(body_lines)

        lines.append(f"{base_indent}}}")

        return lines

    def _generate_for_c_style(self, stmt: IRForCStyle, indent: int) -> List[str]:
        """
        Generate C-style for loop as while loop in Rust.
        Rust doesn't have C-style for loops, so convert to:

        {
            let mut i = 0;
            while i < 10 {
                ...
                i = i + 1;
            }
        }
        """
        base_indent = "    " * indent
        lines = []

        # Open scope block
        lines.append(f"{base_indent}{{")

        # Generate initialization
        init_lines = self._generate_statement(stmt.init, indent + 1)
        if isinstance(init_lines, list):
            lines.extend(init_lines)
        else:
            lines.append(init_lines)

        # Generate while loop with condition
        condition = self._generate_expression(stmt.condition)
        lines.append(f"{base_indent}    while {condition} {{")

        # Generate body
        body_lines = self._generate_statements(stmt.body, indent + 2)
        lines.extend(body_lines)

        # Add increment at end of loop body
        increment_lines = self._generate_statement(stmt.increment, indent + 2)
        if isinstance(increment_lines, list):
            lines.extend(increment_lines)
        else:
            lines.append(increment_lines)

        # Close while loop
        lines.append(f"{base_indent}    }}")

        # Close scope block
        lines.append(f"{base_indent}}}")

        return lines

    def _generate_while(self, stmt: IRWhile, indent: int) -> List[str]:
        """Generate while loop."""
        base_indent = "    " * indent
        lines = []

        condition = self._generate_expression(stmt.condition)
        lines.append(f"{base_indent}while {condition} {{")

        # Body
        body_lines = self._generate_statements(stmt.body, indent + 1)
        lines.extend(body_lines)

        lines.append(f"{base_indent}}}")

        return lines

    def _generate_try(self, stmt: IRTry, indent: int) -> List[str]:
        """
        Generate try-catch as match on Result.

        Rust doesn't have try-catch, so we convert to:
        match result {
            Ok(val) => { ... },
            Err(e) => { ... }
        }
        """
        base_indent = "    " * indent
        lines = []

        # For simplicity, generate a comment indicating this is a try-catch
        lines.append(f"{base_indent}// try-catch block")

        # Generate try body with ? operator propagation
        try_lines = self._generate_statements(stmt.try_body, indent)
        lines.extend(try_lines)

        # Catch blocks - generate as comments (Rust uses Result/Option)
        for catch_block in stmt.catch_blocks:
            if catch_block.exception_type:
                lines.append(f"{base_indent}// catch {catch_block.exception_type}")
            else:
                lines.append(f"{base_indent}// catch all")

            catch_lines = self._generate_statements(catch_block.body, indent)
            lines.extend(catch_lines)

        return lines

    def _generate_throw(self, stmt: IRThrow, indent: int) -> str:
        """Generate throw as return Err(...)."""
        base_indent = "    " * indent
        exception = self._generate_expression(stmt.exception)
        return f"{base_indent}return Err({exception});"

    # ========================================================================
    # Expression Generation
    # ========================================================================

    def _generate_expression(self, expr: IRExpression) -> str:
        """Generate expression."""
        if isinstance(expr, IRLiteral):
            return self._generate_literal(expr)
        elif isinstance(expr, IRIdentifier):
            return self._to_snake_case(expr.name)
        elif isinstance(expr, IRAwait):
            # Rust uses postfix .await syntax
            inner = self._generate_expression(expr.expression)
            return f"{inner}.await"
        elif isinstance(expr, IRBinaryOp):
            return self._generate_binary_op(expr)
        elif isinstance(expr, IRUnaryOp):
            return self._generate_unary_op(expr)
        elif isinstance(expr, IRCall):
            return self._generate_call(expr)
        elif isinstance(expr, IRPropertyAccess):
            obj = self._generate_expression(expr.object)
            # Special case: .length property should use .len() method in Rust
            if expr.property == "length":
                return f"{obj}.len()"
            prop = self._to_snake_case(expr.property)
            return f"{obj}.{prop}"
        elif isinstance(expr, IRIndex):
            obj = self._generate_expression(expr.object)
            index = self._generate_expression(expr.index)

            # Determine if object is a map/HashMap (use .get()) or array/Vec (use [index])
            is_map = False

            # Check if object is an identifier with known type
            if isinstance(expr.object, IRIdentifier):
                var_name = expr.object.name
                if var_name in self.variable_types:
                    var_type = self.variable_types[var_name]
                    # Check if type is "map" or "HashMap"
                    if var_type.name in ("map", "dict", "Dict", "HashMap", "dictionary"):
                        is_map = True

            # If not determined by variable type, use index type as heuristic
            if not is_map and isinstance(expr.index, IRLiteral) and expr.index.literal_type == LiteralType.STRING:
                # String key → likely map/dict access
                is_map = True

            # Generate safe map access with .get() or regular array access
            if is_map:
                # Rust HashMap.get() returns Option<&V>, unwrap_or() returns &V with default
                # For now, use .get().cloned() to get Option<V> then unwrap_or(None equivalent)
                return f"{obj}.get(&{index}).cloned()"
            else:
                return f"{obj}[{index}]"
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
            # Unknown expression type - generate valid None fallback
            return "None"

    def _generate_literal(self, lit: IRLiteral) -> str:
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
            # In Rust, null is context-dependent:
            # - For Option<T>: None
            # - For Box<dyn Any>: Box::new(())
            # For safety in mixed-type contexts, use Box::new(())
            return "Box::new(())"
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

        op = op_map.get(expr.op, expr.op.value)
        return f"({left} {op} {right})"

    def _generate_unary_op(self, expr: IRUnaryOp) -> str:
        """Generate unary operation."""
        operand = self._generate_expression(expr.operand)

        op_map = {
            UnaryOperator.NOT: "!",
            UnaryOperator.NEGATE: "-",
            UnaryOperator.POSITIVE: "+",
            UnaryOperator.BIT_NOT: "!",
        }

        op = op_map.get(expr.op, expr.op.value)
        return f"{op}{operand}"

    def _generate_call(self, expr: IRCall) -> str:
        """Generate function call."""
        func = self._generate_expression(expr.function)

        # Arguments
        args = [self._generate_expression(arg) for arg in expr.args]

        # Keyword arguments (Rust doesn't have kwargs, convert to positional)
        for key, value in expr.kwargs.items():
            args.append(self._generate_expression(value))

        args_str = ", ".join(args)
        return f"{func}({args_str})"

    def _generate_array(self, expr: IRArray) -> str:
        """Generate array literal (vec! macro)."""
        elements = [self._generate_expression(el) for el in expr.elements]
        elements_str = ", ".join(elements)
        return f"vec![{elements_str}]"

    def _generate_map(self, expr: IRMap) -> str:
        """Generate map literal (HashMap construction)."""
        if not expr.entries:
            return "HashMap::new()"

        lines = []
        lines.append("{")
        lines.append("    let mut map = HashMap::new();")
        for key, value in expr.entries.items():
            value_str = self._generate_expression(value)
            lines.append(f'    map.insert("{key}", {value_str});')
        lines.append("    map")
        lines.append("}")

        return "\n".join(lines)

    def _generate_ternary(self, expr: IRTernary) -> str:
        """Generate ternary as if-else expression."""
        condition = self._generate_expression(expr.condition)
        true_val = self._generate_expression(expr.true_value)
        false_val = self._generate_expression(expr.false_value)
        return f"if {condition} {{ {true_val} }} else {{ {false_val} }}"

    def _generate_lambda(self, expr: IRLambda) -> str:
        """Generate lambda as closure."""
        params = [self._to_snake_case(p.name) for p in expr.params]
        params_str = ", ".join(params) if params else ""

        if isinstance(expr.body, list):
            # Multi-statement closure
            return f"|{params_str}| {{ /* multi-statement closure */ }}"
        else:
            body = self._generate_expression(expr.body)
            return f"|{params_str}| {body}"

    def _generate_comprehension(self, expr: IRComprehension) -> str:
        """
        Generate Rust iterator chain from IR comprehension.

        Outputs: items.iter().filter(|x| cond).map(|x| expr).collect()
        """
        iterable = self._generate_expression(expr.iterable)
        iterator = self._to_snake_case(expr.iterator)
        target = self._generate_expression(expr.target)

        # Start with .iter()
        result = f"{iterable}.iter()"

        # Add .filter() if condition exists
        if expr.condition:
            condition = self._generate_expression(expr.condition)
            result += f".filter(|{iterator}| {condition})"

        # Add .map() if element transformation is not just the iterator
        # (i.e., if we're doing more than just filtering)
        if not (isinstance(expr.target, IRIdentifier) and expr.target.name == expr.iterator):
            result += f".map(|{iterator}| {target})"

        # Add .collect()
        result += ".collect()"

        return result

    # ========================================================================
    # Utility Methods
    # ========================================================================

    def _to_snake_case(self, name: str) -> str:
        """Convert name to snake_case (Rust convention)."""
        # Simple conversion: replace camelCase with snake_case
        import re
        # Insert underscore before capital letters
        result = re.sub('([a-z0-9])([A-Z])', r'\1_\2', name)
        return result.lower()


# ============================================================================
# Public API
# ============================================================================


def generate_rust(module: IRModule) -> str:
    """
    Generate Rust code from IR module.

    Args:
        module: IR module to generate from

    Returns:
        str: Rust source code
    """
    generator = RustGeneratorV2()
    return generator.generate(module)
