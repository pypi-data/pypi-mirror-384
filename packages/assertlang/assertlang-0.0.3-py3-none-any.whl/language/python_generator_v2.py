"""
Python Generator V2: IR → Idiomatic Python Code

This generator converts the universal Intermediate Representation (IR) into
production-quality, idiomatic Python code. It handles:

- Type hints (PEP 484/585)
- Async/await patterns
- Decorators from metadata
- Proper imports and organization
- PEP 8 style formatting
- List comprehensions and Python idioms
- Exception handling (try/except)
- Classes with properties, methods, constructors
- Dataclasses and Enums

Design Principles:
1. Idiomatic - Generate Pythonic code, not just syntactically correct
2. Type-safe - Full type hint support via typing module
3. Clean - PEP 8 compliant formatting
4. Zero dependencies - Only uses Python stdlib
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
from language.library_mapping import LibraryMapper


class PythonGeneratorV2:
    """
    Generate idiomatic Python code from IR.

    Converts language-agnostic IR into production-quality Python with:
    - Full type hints
    - Proper imports
    - PEP 8 formatting
    - Python-specific idioms
    """

    def __init__(self):
        self.type_system = TypeSystem()
        self.library_mapper = LibraryMapper()
        self.indent_level = 0
        self.indent_size = 4  # PEP 8 standard
        self.required_imports: Set[str] = set()
        self.source_language: Optional[str] = None  # Track source language for mapping
        self.variable_types: Dict[str, IRType] = {}  # Track variable types for safe map indexing
        self.property_types: Dict[str, IRType] = {}  # Track class property types (e.g., "users": map)
        self.function_return_types: Dict[str, IRType] = {}  # Track function return types
        self.method_return_types: Dict[str, Dict[str, IRType]] = {}  # Track method return types by class
        self.current_class: Optional[str] = None  # Track current class being generated (for 'self' type inference)
        self.capturing_returns = False  # Track if we should capture return values for postconditions

    # ========================================================================
    # Indentation Management
    # ========================================================================

    def indent(self) -> str:
        """Get current indentation string (4 spaces per PEP 8)."""
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
        Generate Python code from IR module.

        Args:
            module: IR module to convert

        Returns:
            Python source code as string
        """
        self.required_imports.clear()
        lines = []

        # Module docstring
        if module.metadata.get("doc"):
            lines.append(f'"""{module.metadata["doc"]}"""')
            lines.append("")

        # Collect required imports from types
        self._collect_imports(module)

        # Track function return types for type-aware code generation
        self._register_function_signatures(module)

        # Collect all TypeVars needed in the module
        type_vars = self._collect_type_vars(module)

        # Add future imports first (PEP 563)
        lines.append("from __future__ import annotations")
        lines.append("")

        # Special imports (enum, dataclass) - add to required
        if module.enums:
            self.required_imports.add("from enum import Enum")
        if module.types:
            self.required_imports.add("from dataclasses import dataclass")

        # If we have TypeVars, add the import
        if type_vars:
            self.required_imports.add("from typing import TypeVar")
            self.required_imports.add("from typing import Generic")

        # Standard library imports (non-typing)
        stdlib_imports = sorted([imp for imp in self.required_imports
                                if not imp.startswith("from typing") and imp.startswith("from ")])
        if stdlib_imports:
            for imp in stdlib_imports:
                lines.append(imp)
            lines.append("")

        # Typing imports
        typing_imports = sorted([imp for imp in self.required_imports if imp.startswith("from typing")])
        if typing_imports:
            # Combine typing imports
            all_types = set()
            for imp in typing_imports:
                types = imp.replace("from typing import ", "").split(", ")
                all_types.update(types)
            lines.append(f"from typing import {', '.join(sorted(all_types))}")
            lines.append("")

        # User imports
        for imp in module.imports:
            lines.append(self.generate_import(imp))
        if module.imports:
            lines.append("")

        # TypeVar definitions (module-level, before any classes/functions that use them)
        if type_vars:
            for type_var in sorted(type_vars):
                lines.append(f"{type_var} = TypeVar('{type_var}')")
            lines.append("")
            lines.append("")

        # Enums
        for enum in module.enums:
            lines.append(self.generate_enum(enum))
            lines.append("")
            lines.append("")

        # Type definitions (dataclasses)
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

    def _collect_type_vars(self, module: IRModule) -> Set[str]:
        """
        Collect all TypeVar names used in the module.

        This scans enums, classes, and functions for generic_params.
        """
        type_vars = set()

        # Collect from enums
        for enum in module.enums:
            if enum.generic_params:
                type_vars.update(enum.generic_params)

        # Collect from classes
        for cls in module.classes:
            if cls.generic_params:
                type_vars.update(cls.generic_params)

        # Collect from functions
        for func in module.functions:
            if func.generic_params:
                type_vars.update(func.generic_params)

        return type_vars

    # ========================================================================
    # Import Collection and Generation
    # ========================================================================

    def _register_function_signatures(self, module: IRModule) -> None:
        """Register function and method return types for type-aware code generation."""
        # Register standalone function return types
        for func in module.functions:
            if func.return_type:
                self.function_return_types[func.name] = func.return_type

        # Register class method return types
        for cls in module.classes:
            if cls.name not in self.method_return_types:
                self.method_return_types[cls.name] = {}

            for method in cls.methods:
                if method.return_type:
                    self.method_return_types[cls.name][method.name] = method.return_type

    def _collect_imports(self, module: IRModule) -> None:
        """Collect all required imports from types used in module."""
        all_types = []

        # Collect types from functions
        for func in module.functions:
            for param in func.params:
                all_types.append(param.param_type)
            if func.return_type:
                all_types.append(func.return_type)

            # Check if function has contracts - add contract imports if needed
            if func.requires or func.ensures:
                if func.requires:
                    self.required_imports.add("from assertlang.runtime.contracts import check_precondition")
                if func.ensures:
                    self.required_imports.add("from assertlang.runtime.contracts import check_postcondition")

        # Collect types from classes
        for cls in module.classes:
            for prop in cls.properties:
                if prop and prop.prop_type:
                    all_types.append(prop.prop_type)
            for method in cls.methods:
                for param in method.params:
                    if param and param.param_type:
                        all_types.append(param.param_type)
                if method.return_type:
                    all_types.append(method.return_type)

                # Check if method has contracts
                if method.requires or method.ensures:
                    if method.requires:
                        self.required_imports.add("from assertlang.runtime.contracts import check_precondition")
                    if method.ensures:
                        self.required_imports.add("from assertlang.runtime.contracts import check_postcondition")

            # Check if class has invariants
            if cls.invariants:
                self.required_imports.add("from assertlang.runtime.contracts import check_invariant")

        # Collect types from type definitions
        for type_def in module.types:
            for field in type_def.fields:
                if field and field.prop_type:
                    all_types.append(field.prop_type)

        # Get required imports
        imports = self.type_system.get_required_imports(all_types, "python")
        self.required_imports.update(imports)

    def generate_import(self, imp: IRImport) -> str:
        """
        Generate Python import statement with library mapping.

        If source language is set and library mapping exists, translates to Python equivalent.
        """
        module_name = imp.module

        # Try to translate library if source language is known
        if self.source_language and self.source_language != "python":
            translated = self.library_mapper.translate_import(
                imp.module,
                from_lang=self.source_language,
                to_lang="python"
            )
            if translated:
                module_name = translated["module"]
                # Add comment showing original library
                comment = f"  # from {self.source_language}: {imp.module}"
            else:
                comment = f"  # NOTE: No mapping for {self.source_language} library '{imp.module}'"
        else:
            comment = ""

        # Generate import statement
        if imp.items:
            # from module import item1, item2
            items = ", ".join(imp.items)
            return f"from {module_name} import {items}{comment}"
        elif imp.alias:
            # import module as alias
            return f"import {module_name} as {imp.alias}{comment}"
        else:
            # import module
            return f"import {module_name}{comment}"

    # ========================================================================
    # Type Definition Generation
    # ========================================================================

    def generate_enum(self, enum: IREnum) -> str:
        """
        Generate Python Enum class or generic enum with dataclasses.

        For generic enums like Option<T>, generates dataclass variants instead of Enum:
        - enum Option<T>: -> Union[Some[T], None_]
        - Each variant becomes a dataclass
        """
        lines = []

        # Check if this is a generic enum (has type parameters)
        if enum.generic_params:
            # Generate generic enum as Union of dataclasses
            return self.generate_generic_enum(enum)

        # Regular enum (non-generic)
        # Docstring
        if enum.doc:
            lines.append(f"class {enum.name}(Enum):")
            self.increase_indent()
            lines.append(f'{self.indent()}"""{enum.doc}"""')
        else:
            lines.append(f"class {enum.name}(Enum):")
            self.increase_indent()

        # Variants
        if not enum.variants:
            lines.append(f"{self.indent()}pass")
        else:
            for i, variant in enumerate(enum.variants):
                if variant.value is not None:
                    if isinstance(variant.value, str):
                        lines.append(f'{self.indent()}{variant.name} = "{variant.value}"')
                    else:
                        lines.append(f'{self.indent()}{variant.name} = {variant.value}')
                else:
                    # Auto-number if no value
                    lines.append(f'{self.indent()}{variant.name} = {i + 1}')

        self.decrease_indent()
        return "\n".join(lines)

    def generate_generic_enum(self, enum: IREnum) -> str:
        """
        Generate a generic enum as Union of dataclass variants.

        Example:
            enum Option<T>:
                - Some(T)
                - None

        Generates:
            @dataclass
            class Some(Generic[T]):
                value: T

            @dataclass
            class None_:
                pass

            Option = Union[Some[T], None_]

        Note: TypeVar definitions are emitted at module level, not inline.
        """
        lines = []

        # Add required imports (but don't emit TypeVars here - they're module-level)
        self.required_imports.add("from typing import TypeVar")
        self.required_imports.add("from typing import Generic")
        self.required_imports.add("from typing import Union")
        self.required_imports.add("from dataclasses import dataclass")

        # Generate dataclass for each variant
        for variant in enum.variants:
            lines.append("")
            lines.append("@dataclass")

            # Check if variant has associated types
            if variant.associated_types:
                # Variant with data: class Some(Generic[T])
                generic_params_str = ", ".join(enum.generic_params)
                lines.append(f"class {variant.name}(Generic[{generic_params_str}]):")
                self.increase_indent()

                # Generate fields for associated types
                # For unnamed tuple syntax like Some(T), create a 'value' field
                if len(variant.associated_types) == 1:
                    type_str = self.generate_type(variant.associated_types[0])
                    lines.append(f"{self.indent()}value: {type_str}")
                else:
                    # Multiple associated types become numbered fields
                    for i, assoc_type in enumerate(variant.associated_types):
                        type_str = self.generate_type(assoc_type)
                        lines.append(f"{self.indent()}field_{i}: {type_str}")

                self.decrease_indent()
            else:
                # Variant without data: class None_
                # Use trailing underscore to avoid Python keyword conflicts
                variant_name = f"{variant.name}_" if variant.name in ("None", "True", "False") else variant.name
                lines.append(f"class {variant_name}:")
                self.increase_indent()
                lines.append(f"{self.indent()}pass")
                self.decrease_indent()

        # Generate type alias as Union
        lines.append("")
        lines.append("")
        variant_names = []
        for variant in enum.variants:
            if variant.associated_types:
                # Generic variant: Some[T]
                generic_params_str = ", ".join(enum.generic_params)
                variant_names.append(f"{variant.name}[{generic_params_str}]")
            else:
                # Non-generic variant: None_
                variant_name = f"{variant.name}_" if variant.name in ("None", "True", "False") else variant.name
                variant_names.append(variant_name)

        union_str = ", ".join(variant_names)
        lines.append(f"{enum.name} = Union[{union_str}]")

        return "\n".join(lines)

    def generate_type_definition(self, type_def: IRTypeDefinition) -> str:
        """Generate Python dataclass."""
        lines = []

        # Decorator
        lines.append("@dataclass")

        # Class definition
        if type_def.doc:
            lines.append(f"class {type_def.name}:")
            self.increase_indent()
            lines.append(f'{self.indent()}"""{type_def.doc}"""')
        else:
            lines.append(f"class {type_def.name}:")
            self.increase_indent()

        # Fields
        if not type_def.fields:
            lines.append(f"{self.indent()}pass")
        else:
            for field in type_def.fields:
                field_line = f"{self.indent()}{field.name}: {self.generate_type(field.prop_type)}"
                if field.default_value:
                    field_line += f" = {self.generate_expression(field.default_value)}"
                lines.append(field_line)

        self.decrease_indent()
        return "\n".join(lines)

    # ========================================================================
    # Class Generation
    # ========================================================================

    def generate_class(self, cls: IRClass) -> str:
        """Generate Python class with optional generic type parameters."""
        lines = []

        # Track current class for 'self' type inference
        self.current_class = cls.name

        # Register class property types for safe map/array indexing
        for prop in cls.properties:
            if prop and hasattr(prop, 'prop_type'):
                self.property_types[prop.name] = prop.prop_type

        # If class has generic parameters, add TypeVar and Generic imports
        if cls.generic_params:
            self.required_imports.add("from typing import TypeVar")
            self.required_imports.add("from typing import Generic")

        # Class signature
        class_sig = f"class {cls.name}"

        # Add base classes or Generic[T]
        bases = []
        if cls.generic_params:
            # Add Generic[T, U, ...]
            generic_params_str = ", ".join(cls.generic_params)
            bases.append(f"Generic[{generic_params_str}]")
        if cls.base_classes:
            bases.extend(cls.base_classes)

        if bases:
            class_sig += f"({', '.join(bases)})"
        class_sig += ":"
        lines.append(class_sig)

        self.increase_indent()

        # Docstring
        if cls.doc:
            lines.append(f'{self.indent()}"""{cls.doc}"""')
            lines.append("")

        # Class-level properties (without default values)
        has_properties = False
        for prop in cls.properties:
            if prop and not getattr(prop, 'default_value', None):
                prop_line = f"{self.indent()}{prop.name}: {self.generate_type(prop.prop_type)}"
                lines.append(prop_line)
                has_properties = True

        if has_properties:
            lines.append("")

        # Constructor
        if cls.constructor:
            lines.append(self.generate_constructor(cls.constructor, cls.properties))
            lines.append("")

        # Methods
        for method in cls.methods:
            lines.append(self.generate_method(method))
            lines.append("")

        # If empty class, add pass
        if not cls.properties and not cls.constructor and not cls.methods:
            lines.append(f"{self.indent()}pass")

        self.decrease_indent()

        # Remove trailing empty line from class
        while lines and lines[-1] == "":
            lines.pop()

        # Clear property types (class scope ended)
        self.property_types.clear()
        # Clear current class
        self.current_class = None

        return "\n".join(lines)

    def generate_constructor(self, constructor: IRFunction, properties: List[IRProperty]) -> str:
        """Generate __init__ method."""
        lines = []

        # Signature
        params = ["self"]
        for param in constructor.params:
            param_str = f"{param.name}: {self.generate_type(param.param_type)}"
            if param.default_value:
                param_str += f" = {self.generate_expression(param.default_value)}"
            params.append(param_str)

        # Return type is None for __init__
        params_str = ", ".join(params)
        lines.append(f"{self.indent()}def __init__({params_str}) -> None:")

        self.increase_indent()

        # Docstring
        if constructor.doc:
            lines.append(f'{self.indent()}"""{constructor.doc}"""')

        # Body
        if constructor.body:
            for i, stmt in enumerate(constructor.body):
                next_stmt = constructor.body[i + 1] if i + 1 < len(constructor.body) else None
                stmt_code = self.generate_statement(stmt, next_stmt)
                if stmt_code is not None:  # Skip None (IRMap workaround)
                    lines.append(stmt_code)
        else:
            lines.append(f"{self.indent()}pass")

        self.decrease_indent()
        return "\n".join(lines)

    def generate_method(self, method: IRFunction) -> str:
        """Generate class method."""
        lines = []

        # Register parameter types for safe map/array indexing (same as functions)
        for param in method.params:
            self.variable_types[param.name] = param.param_type

        # Decorators (use direct field, fall back to metadata)
        decorators = method.decorators if hasattr(method, 'decorators') else method.metadata.get("decorators", [])
        for dec in decorators:
            lines.append(f"{self.indent()}@{dec}")

        # Static method
        if method.is_static:
            lines.append(f"{self.indent()}@staticmethod")

        # Signature
        params = [] if method.is_static else ["self"]
        for param in method.params:
            param_str = f"{param.name}: {self.generate_type(param.param_type)}"
            if param.default_value:
                param_str += f" = {self.generate_expression(param.default_value)}"
            params.append(param_str)

        params_str = ", ".join(params)

        # Async
        func_def = "async def" if method.is_async else "def"

        # Return type
        return_type = ""
        if method.return_type:
            return_type = f" -> {self.generate_type(method.return_type)}"

        lines.append(f"{self.indent()}{func_def} {method.name}({params_str}){return_type}:")

        self.increase_indent()

        # Docstring
        if method.doc:
            lines.append(f'{self.indent()}"""{method.doc}"""')

        # Body
        if method.body:
            for i, stmt in enumerate(method.body):
                next_stmt = method.body[i + 1] if i + 1 < len(method.body) else None
                stmt_code = self.generate_statement(stmt, next_stmt)
                if stmt_code is not None:  # Skip None (IRMap workaround)
                    lines.append(stmt_code)
        else:
            lines.append(f"{self.indent()}pass")

        self.decrease_indent()
        return "\n".join(lines)

    # ========================================================================
    # Function Generation
    # ========================================================================

    def generate_function(self, func: IRFunction) -> str:
        """Generate standalone function with optional generic type parameters and contract checks."""
        lines = []

        # Register parameter types for safe map/array indexing
        for param in func.params:
            self.variable_types[param.name] = param.param_type

        # If function has generic parameters, add TypeVar imports and definitions
        if func.generic_params:
            self.required_imports.add("from typing import TypeVar")

        # Decorators (use direct field, fall back to metadata)
        decorators = func.decorators if hasattr(func, 'decorators') else func.metadata.get("decorators", [])
        for dec in decorators:
            lines.append(f"@{dec}")

        # Signature
        params = []
        for param in func.params:
            param_str = f"{param.name}: {self.generate_type(param.param_type)}"
            if param.default_value:
                param_str += f" = {self.generate_expression(param.default_value)}"
            params.append(param_str)

        params_str = ", ".join(params)

        # Async
        func_def = "async def" if func.is_async else "def"

        # Return type
        return_type = ""
        if func.return_type:
            return_type = f" -> {self.generate_type(func.return_type)}"

        lines.append(f"{func_def} {func.name}({params_str}){return_type}:")

        self.increase_indent()

        # Docstring
        if func.doc:
            lines.append(f'{self.indent()}"""{func.doc}"""')

        # Generate contract checks
        preconditions, postcondition_setup, postcondition_checks = self.generate_contract_checks(func)

        # Add contract checking code if present
        if preconditions or postcondition_setup or postcondition_checks:
            # Precondition checks (at function entry)
            for check in preconditions:
                lines.append(f"{self.indent()}{check}")

            # Capture old values (before function body)
            for old_capture in postcondition_setup:
                lines.append(f"{self.indent()}{old_capture}")

            if postcondition_checks:
                # Wrap body in try/finally for postconditions
                lines.append(f"{self.indent()}__result = None")
                lines.append(f"{self.indent()}try:")
                self.increase_indent()

                # Enable return capturing mode
                self.capturing_returns = True

                # Body
                if func.body:
                    for i, stmt in enumerate(func.body):
                        next_stmt = func.body[i + 1] if i + 1 < len(func.body) else None
                        stmt_code = self.generate_statement(stmt, next_stmt)
                        if stmt_code is not None:  # Skip None (IRMap workaround)
                            lines.append(stmt_code)
                else:
                    lines.append(f"{self.indent()}pass")

                # Disable return capturing mode
                self.capturing_returns = False

                self.decrease_indent()
                lines.append(f"{self.indent()}finally:")
                self.increase_indent()

                # Postcondition checks
                for check in postcondition_checks:
                    lines.append(f"{self.indent()}{check}")

                self.decrease_indent()

                # Return the result
                lines.append(f"{self.indent()}return __result")
            else:
                # No postconditions, just body
                if func.body:
                    for i, stmt in enumerate(func.body):
                        next_stmt = func.body[i + 1] if i + 1 < len(func.body) else None
                        stmt_code = self.generate_statement(stmt, next_stmt)
                        if stmt_code is not None:  # Skip None (IRMap workaround)
                            lines.append(stmt_code)
                else:
                    lines.append(f"{self.indent()}pass")
        else:
            # No contracts, just regular body
            if func.body:
                for i, stmt in enumerate(func.body):
                    next_stmt = func.body[i + 1] if i + 1 < len(func.body) else None
                    stmt_code = self.generate_statement(stmt, next_stmt)
                    if stmt_code is not None:  # Skip None (IRMap workaround)
                        lines.append(stmt_code)
            else:
                lines.append(f"{self.indent()}pass")

        self.decrease_indent()

        # Clear variable types for this function scope
        self.variable_types.clear()

        return "\n".join(lines)

    # ========================================================================
    # Type Generation
    # ========================================================================

    def generate_type(self, ir_type: IRType) -> str:
        """Generate Python type hint from IR type."""
        return self.type_system.map_to_language(ir_type, "python")

    # ========================================================================
    # Statement Generation
    # ========================================================================

    def generate_statement(self, stmt: IRStatement, next_stmt: IRStatement = None) -> str:
        """Generate Python statement from IR."""
        if isinstance(stmt, IRAssignment):
            return self.generate_assignment(stmt, next_stmt)
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
            return self.generate_raise(stmt)
        elif isinstance(stmt, IRBreak):
            return f"{self.indent()}break"
        elif isinstance(stmt, IRContinue):
            return f"{self.indent()}continue"
        elif isinstance(stmt, IRPass):
            return f"{self.indent()}pass"
        elif isinstance(stmt, IRWith):
            return self.generate_with(stmt)
        elif isinstance(stmt, IRCall):
            # Expression statement
            return f"{self.indent()}{self.generate_expression(stmt)}"
        elif isinstance(stmt, IRMap):
            # IRMap as statement is a parser bug workaround marker - skip it
            return None  # Signal to skip this statement
        else:
            return f"{self.indent()}# Unknown statement: {type(stmt).__name__}"

    def generate_assignment(self, stmt: IRAssignment, next_stmt: IRStatement = None) -> str:
        """Generate assignment statement."""
        # Check if next statement is IRMap (parser bug workaround for class initialization)
        if next_stmt and isinstance(next_stmt, IRMap) and isinstance(stmt.value, IRIdentifier):
            # This is: let x = ClassName { field: value, ... }
            # Generate as: x = ClassName(field=value, ...)
            class_name = stmt.value.name
            kwargs = []
            for key, val_expr in next_stmt.entries.items():
                val = self.generate_expression(val_expr)
                kwargs.append(f"{key}={val}")

            target = stmt.target if isinstance(stmt.target, str) else self.generate_expression(stmt.target)

            if stmt.is_declaration and stmt.var_type and isinstance(stmt.target, str):
                type_hint = self.generate_type(stmt.var_type)
                return f"{self.indent()}{target}: {type_hint} = {class_name}({', '.join(kwargs)})"
            else:
                return f"{self.indent()}{target} = {class_name}({', '.join(kwargs)})"

        value = self.generate_expression(stmt.value)

        # Infer and track variable types for local assignments
        if isinstance(stmt.target, str):
            # Use explicit type annotation if provided
            if stmt.var_type:
                self.variable_types[stmt.target] = stmt.var_type
            else:
                # Otherwise, infer from value
                inferred_type = self._infer_expression_type(stmt.value)
                if inferred_type:
                    self.variable_types[stmt.target] = inferred_type

        # Generate target (could be variable or property access)
        if stmt.target:
            if isinstance(stmt.target, str):
                target = stmt.target
            elif isinstance(stmt.target, IRIndex):
                # Special case: Index assignment (map[key] = value or arr[i] = value)
                # Use direct bracket notation for assignment (don't use .get())
                obj = self.generate_expression(stmt.target.object)
                index = self.generate_expression(stmt.target.index)
                target = f"{obj}[{index}]"
            else:
                # Target is an expression (like property access)
                target = self.generate_expression(stmt.target)
        else:
            target = "_unknown"

        # Type annotation for declarations (only for simple variables, not attributes)
        if stmt.is_declaration and stmt.var_type and isinstance(stmt.target, str) and "." not in target:
            type_hint = self.generate_type(stmt.var_type)
            return f"{self.indent()}{target}: {type_hint} = {value}"
        else:
            return f"{self.indent()}{target} = {value}"

    def generate_if(self, stmt: IRIf) -> str:
        """Generate if statement with pattern match support."""
        lines = []

        # Check if condition is a pattern match with bindings
        bindings = []
        if isinstance(stmt.condition, IRPatternMatch):
            # Pattern match condition - extract bindings
            pattern = stmt.condition.pattern
            value = self.generate_expression(stmt.condition.value)

            if isinstance(pattern, IRCall) and pattern.args:
                # Pattern like Some(val) - bind variables
                variant_name = self.generate_expression(pattern.function)
                for i, arg in enumerate(pattern.args):
                    if isinstance(arg, IRIdentifier) and arg.name != "_":
                        # Bind arg.name to value.field
                        if len(pattern.args) == 1:
                            bindings.append((arg.name, f"{value}.value"))
                        else:
                            bindings.append((arg.name, f"{value}.field_{i}"))

        # If condition
        condition = self.generate_expression(stmt.condition)
        lines.append(f"{self.indent()}if {condition}:")

        # Then body
        self.increase_indent()

        # Add variable bindings at start of then block
        for var_name, var_value in bindings:
            lines.append(f"{self.indent()}{var_name} = {var_value}")

        if stmt.then_body:
            for i, s in enumerate(stmt.then_body):
                next_stmt = stmt.then_body[i + 1] if i + 1 < len(stmt.then_body) else None
                stmt_code = self.generate_statement(s, next_stmt)
                if stmt_code is not None:
                    lines.append(stmt_code)
        else:
            if not bindings:
                lines.append(f"{self.indent()}pass")

        self.decrease_indent()

        # Else body
        if stmt.else_body:
            lines.append(f"{self.indent()}else:")
            self.increase_indent()
            for i, s in enumerate(stmt.else_body):
                next_stmt = stmt.else_body[i + 1] if i + 1 < len(stmt.else_body) else None
                stmt_code = self.generate_statement(s, next_stmt)
                if stmt_code is not None:
                    lines.append(stmt_code)
            self.decrease_indent()

        return "\n".join(lines)

    def generate_for(self, stmt: IRFor) -> str:
        """Generate for loop."""
        lines = []

        iterable = self.generate_expression(stmt.iterable)
        lines.append(f"{self.indent()}for {stmt.iterator} in {iterable}:")

        self.increase_indent()

        # Try to infer iterator element type for better code generation
        # If iterating over array/list, iterator could be any type
        # For now, we don't track iterator types, but this is where we would

        if stmt.body:
            for i, s in enumerate(stmt.body):
                next_stmt = stmt.body[i + 1] if i + 1 < len(stmt.body) else None
                stmt_code = self.generate_statement(s, next_stmt)
                if stmt_code is not None:
                    lines.append(stmt_code)
        else:
            lines.append(f"{self.indent()}pass")
        self.decrease_indent()

        return "\n".join(lines)

    def generate_for_c_style(self, stmt: IRForCStyle) -> str:
        """
        Generate C-style for loop as Python while loop.

        for (let i = 0; i < 10; i = i + 1) { ... }
        becomes:
        i = 0
        while i < 10:
            ...
            i = i + 1
        """
        lines = []

        # Generate initialization
        init_line = self.generate_statement(stmt.init)
        lines.append(init_line)

        # Generate while loop with condition
        condition = self.generate_expression(stmt.condition)
        lines.append(f"{self.indent()}while {condition}:")

        # Generate body with increment at the end
        self.increase_indent()
        if stmt.body:
            for i, s in enumerate(stmt.body):
                next_stmt = stmt.body[i + 1] if i + 1 < len(stmt.body) else None
                stmt_code = self.generate_statement(s, next_stmt)
                if stmt_code is not None:
                    lines.append(stmt_code)

        # Add increment at end of loop body
        increment_line = self.generate_statement(stmt.increment)
        lines.append(increment_line)

        if not stmt.body:
            lines.append(f"{self.indent()}pass")

        self.decrease_indent()

        return "\n".join(lines)

    def generate_while(self, stmt: IRWhile) -> str:
        """Generate while loop."""
        lines = []

        condition = self.generate_expression(stmt.condition)
        lines.append(f"{self.indent()}while {condition}:")

        self.increase_indent()
        if stmt.body:
            for i, s in enumerate(stmt.body):
                next_stmt = stmt.body[i + 1] if i + 1 < len(stmt.body) else None
                stmt_code = self.generate_statement(s, next_stmt)
                if stmt_code is not None:
                    lines.append(stmt_code)
        else:
            lines.append(f"{self.indent()}pass")
        self.decrease_indent()

        return "\n".join(lines)

    def generate_try(self, stmt: IRTry) -> str:
        """Generate try/except statement."""
        lines = []

        # Try block
        lines.append(f"{self.indent()}try:")
        self.increase_indent()
        if stmt.try_body:
            for s in stmt.try_body:
                lines.append(self.generate_statement(s))
        else:
            lines.append(f"{self.indent()}pass")
        self.decrease_indent()

        # Except blocks
        for catch in stmt.catch_blocks:
            except_line = f"{self.indent()}except"
            if catch.exception_type:
                except_line += f" {catch.exception_type}"
                if catch.exception_var:
                    except_line += f" as {catch.exception_var}"
            except_line += ":"
            lines.append(except_line)

            self.increase_indent()
            if catch.body:
                for s in catch.body:
                    lines.append(self.generate_statement(s))
            else:
                lines.append(f"{self.indent()}pass")
            self.decrease_indent()

        # Finally block
        if stmt.finally_body:
            lines.append(f"{self.indent()}finally:")
            self.increase_indent()
            for s in stmt.finally_body:
                lines.append(self.generate_statement(s))
            self.decrease_indent()

        return "\n".join(lines)

    def generate_with(self, stmt: IRWith) -> str:
        """Generate with statement (context manager)."""
        lines = []

        # Generate: with expr as var:
        context = self.generate_expression(stmt.context_expr)
        with_line = f"{self.indent()}with {context}"

        if stmt.variable:
            with_line += f" as {stmt.variable}"

        with_line += ":"
        lines.append(with_line)

        # Body
        self.increase_indent()
        if stmt.body:
            for i, s in enumerate(stmt.body):
                next_stmt = stmt.body[i + 1] if i + 1 < len(stmt.body) else None
                stmt_code = self.generate_statement(s, next_stmt)
                if stmt_code is not None:
                    lines.append(stmt_code)
        else:
            lines.append(f"{self.indent()}pass")
        self.decrease_indent()

        return "\n".join(lines)

    def generate_return(self, stmt: IRReturn) -> str:
        """Generate return statement, capturing value if in postcondition mode."""
        if self.capturing_returns:
            # We're in a function with postconditions - capture return value
            if stmt.value:
                value = self.generate_expression(stmt.value)
                # Generate two lines: capture and return
                capture_line = f"{self.indent()}__result = {value}"
                return_line = f"{self.indent()}return __result"
                return f"{capture_line}\n{return_line}"
            else:
                # Return None
                return f"{self.indent()}__result = None\n{self.indent()}return __result"
        else:
            # Normal return generation
            if stmt.value:
                value = self.generate_expression(stmt.value)
                return f"{self.indent()}return {value}"
            else:
                return f"{self.indent()}return"

    def generate_raise(self, stmt: IRThrow) -> str:
        """Generate raise statement."""
        exception = self.generate_expression(stmt.exception)
        return f"{self.indent()}raise {exception}"

    # ========================================================================
    # Expression Generation
    # ========================================================================

    def generate_expression(self, expr: IRExpression) -> str:
        """Generate Python expression from IR."""
        if isinstance(expr, IRLiteral):
            return self.generate_literal(expr)
        elif isinstance(expr, IRIdentifier):
            # Special case: enum variant without data (None, True, False)
            if expr.name in ("None", "True", "False"):
                return f"{expr.name}_()"
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
            # Special case: .length property should use len() in Python
            if expr.property == "length":
                return f"len({obj})"

            # Special case: enum variant without data (Option.None, Result.Ok, etc.)
            if expr.property in ("None", "True", "False"):
                # Option.None → None_()
                return f"{expr.property}_()"

            # Determine if object is a map/dict (use bracket notation) or class (use dot notation)
            is_map = self._is_map_type(expr.object)

            if is_map:
                # Generate dictionary access for maps: obj["field"]
                return f'{obj}["{expr.property}"]'
            else:
                # Generate attribute access for classes: obj.field
                return f"{obj}.{expr.property}"
        elif isinstance(expr, IRIndex):
            obj = self.generate_expression(expr.object)
            index = self.generate_expression(expr.index)

            # Determine if object is a map/dict (use .get()) or array (use [index])
            is_map = False

            # Check if object is an identifier with known type (e.g., function parameter)
            if isinstance(expr.object, IRIdentifier):
                var_name = expr.object.name
                if var_name in self.variable_types:
                    var_type = self.variable_types[var_name]
                    # Check if type is "map" or "dict"
                    if var_type.name in ("map", "dict", "Dict", "dictionary"):
                        is_map = True

            # Check if object is a property access (e.g., self.users[key])
            elif isinstance(expr.object, IRPropertyAccess):
                # Check if the property is a known map type
                prop_name = expr.object.property
                if prop_name in self.property_types:
                    prop_type = self.property_types[prop_name]
                    if prop_type.name in ("map", "dict", "Dict", "dictionary"):
                        is_map = True

            # If not determined by variable type, use index type as heuristic
            if not is_map and isinstance(expr.index, IRLiteral) and expr.index.literal_type == LiteralType.STRING:
                # String key → likely map/dict access
                is_map = True

            # Generate safe map access with .get() or regular array access
            if is_map:
                return f"{obj}.get({index})"
            else:
                return f"{obj}[{index}]"
        elif isinstance(expr, IRArray):
            return self.generate_array(expr)
        elif isinstance(expr, IRMap):
            return self.generate_dict(expr)
        elif isinstance(expr, IRTernary):
            return self.generate_ternary(expr)
        elif isinstance(expr, IRLambda):
            return self.generate_lambda(expr)
        elif isinstance(expr, IRComprehension):
            return self.generate_comprehension(expr)
        elif isinstance(expr, IRPatternMatch):
            return self.generate_pattern_match(expr)
        elif isinstance(expr, IROldExpr):
            return self.generate_old_expr(expr)
        else:
            return f"<unknown: {type(expr).__name__}>"

    def generate_literal(self, lit: IRLiteral) -> str:
        """Generate Python literal."""
        if lit.literal_type == LiteralType.STRING:
            # Escape string properly - use repr for Python-safe escaping
            value = str(lit.value)
            # Escape special characters
            value = value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")
            return f'"{value}"'
        elif lit.literal_type == LiteralType.INTEGER:
            return str(lit.value)
        elif lit.literal_type == LiteralType.FLOAT:
            return str(lit.value)
        elif lit.literal_type == LiteralType.BOOLEAN:
            return "True" if lit.value else "False"
        elif lit.literal_type == LiteralType.NULL:
            return "None"
        else:
            return str(lit.value)

    def _is_map_type(self, expr: IRExpression) -> bool:
        """
        Determine if an expression evaluates to a map/dict type.

        This enables context-aware code generation:
        - Maps use bracket notation: obj["field"]
        - Classes use dot notation: obj.field

        Strategy: Be conservative - when in doubt, use bracket notation (safer for dicts).
        Only use dot notation when we're CERTAIN it's a class instance.

        Returns:
            True if expr is a map/dict, False if it's a class/object
        """
        # Check if expression has an inferred type
        expr_type = self._infer_expression_type(expr)
        if expr_type:
            # Explicitly a map/dict type
            if expr_type.name in ("map", "dict", "Dict", "dictionary"):
                return True
            # Explicitly a class type (known class name)
            if expr_type.name in self.method_return_types:
                return False
            # Other primitive types (string, int, etc.) are not maps
            if expr_type.name in ("string", "int", "float", "bool", "null", "any", "array", "list", "List"):
                return False
            # Unknown type - default to class (safer, more common)
            return False

        # Check if expression is a map literal
        if isinstance(expr, IRMap):
            return True

        # Check if expression is an identifier with known type
        if isinstance(expr, IRIdentifier):
            var_name = expr.name
            if var_name in self.variable_types:
                var_type = self.variable_types[var_name]
                if var_type.name in ("map", "dict", "Dict", "dictionary"):
                    return True
                # Known class type
                if var_type.name in self.method_return_types:
                    return False
                # Primitive types
                if var_type.name in ("string", "int", "float", "bool", "array", "list"):
                    return False
            # Unknown identifier - default to class (safer)
            # 'self' is always a class instance
            if var_name == "self":
                return False
            return False

        # Check if expression is a property access
        if isinstance(expr, IRPropertyAccess):
            # Check if accessing a property on 'self' (class property)
            if isinstance(expr.object, IRIdentifier) and expr.object.name == "self":
                # Check if property is a map type
                if expr.property in self.property_types:
                    prop_type = self.property_types[expr.property]
                    return prop_type.name in ("map", "dict", "Dict", "dictionary")
                return False  # Class properties are not maps by default

            # Otherwise, default to class (safer, more common)
            return False

        # Default: use dot notation (classes) when type is unknown
        return False

    def _infer_expression_type(self, expr: IRExpression) -> Optional[IRType]:
        """
        Infer the type of an expression for type-aware code generation.

        This is a lightweight type inference specifically for the generator.
        Used primarily to distinguish int/int division from float division.
        """
        if isinstance(expr, IRLiteral):
            # Literal types are known directly
            if expr.literal_type == LiteralType.INTEGER:
                return IRType(name="int")
            elif expr.literal_type == LiteralType.FLOAT:
                return IRType(name="float")
            elif expr.literal_type == LiteralType.STRING:
                return IRType(name="string")
            elif expr.literal_type == LiteralType.BOOLEAN:
                return IRType(name="bool")
            elif expr.literal_type == LiteralType.NULL:
                return IRType(name="null")

        elif isinstance(expr, IRIdentifier):
            # Special case: 'self' has the type of the current class
            if expr.name == "self" and self.current_class:
                return IRType(name=self.current_class)
            # Look up in variable types (from function parameters)
            return self.variable_types.get(expr.name)

        elif isinstance(expr, IRBinaryOp):
            # For binary operations, infer result type
            left_type = self._infer_expression_type(expr.left)
            right_type = self._infer_expression_type(expr.right)

            # String concatenation: if either operand is string, result is string
            if expr.op == BinaryOperator.ADD:
                if (left_type and left_type.name == "string") or (right_type and right_type.name == "string"):
                    return IRType(name="string")
                # Otherwise fall through to numeric addition

            # Arithmetic operations: if either is float, result is float
            if expr.op in [BinaryOperator.ADD, BinaryOperator.SUBTRACT, BinaryOperator.MULTIPLY, BinaryOperator.DIVIDE]:
                if (left_type and left_type.name == "float") or (right_type and right_type.name == "float"):
                    return IRType(name="float")
                elif (left_type and left_type.name == "int") and (right_type and right_type.name == "int"):
                    return IRType(name="int")
            # Floor division always returns int
            elif expr.op == BinaryOperator.FLOOR_DIVIDE:
                return IRType(name="int")

        elif isinstance(expr, IRPropertyAccess):
            # Special case: .length property returns int
            if expr.property == "length":
                return IRType(name="int")

            # Check if we're accessing a property of a map
            # If object is a map, the accessed property value could also be a map
            obj_type = self._infer_expression_type(expr.object)
            if obj_type and obj_type.name in ("map", "dict", "Dict", "dictionary"):
                # We're accessing a field of a map
                # Check if the object is a map literal with known structure
                if isinstance(expr.object, IRMap):
                    # Check the value type of the accessed field
                    if expr.property in expr.object.entries:
                        field_value = expr.object.entries[expr.property]
                        return self._infer_expression_type(field_value)
                # For non-literal maps, we conservatively assume the value is also a map
                # This ensures bracket notation propagates through nested map access
                return IRType(name="map")

        elif isinstance(expr, IRCall):
            # Special case: len() returns int
            if isinstance(expr.function, IRIdentifier) and expr.function.name == "len":
                return IRType(name="int")

            # Look up function return type
            if isinstance(expr.function, IRIdentifier):
                func_name = expr.function.name
                if func_name in self.function_return_types:
                    return self.function_return_types[func_name]

                # Check if it's a class constructor (capitalized name)
                # This is a heuristic - if a call matches a known class name, it's a constructor
                if func_name in self.method_return_types:
                    # It's a class constructor
                    return IRType(name=func_name)

            # Look up method return type
            elif isinstance(expr.function, IRPropertyAccess):
                method_name = expr.function.property
                # Try to determine the class of the object
                obj_type = self._infer_expression_type(expr.function.object)
                if obj_type and obj_type.name in self.method_return_types:
                    if method_name in self.method_return_types[obj_type.name]:
                        return self.method_return_types[obj_type.name][method_name]

        elif isinstance(expr, IRMap):
            # Map literals have type "map"
            return IRType(name="map")

        return None

    def generate_binary_op(self, expr: IRBinaryOp) -> str:
        """Generate binary operation."""
        # Special handling for division: use // for integer division
        if expr.op == BinaryOperator.DIVIDE:
            left_type = self._infer_expression_type(expr.left)
            right_type = self._infer_expression_type(expr.right)

            # If both operands are integers, use integer division (//)
            if (left_type and left_type.name == "int") and (right_type and right_type.name == "int"):
                left = self.generate_expression(expr.left)
                right = self.generate_expression(expr.right)
                return f"({left} // {right})"

        # Special handling for addition: auto-convert types for string concatenation
        if expr.op == BinaryOperator.ADD:
            left_type = self._infer_expression_type(expr.left)
            right_type = self._infer_expression_type(expr.right)

            # If one operand is string and the other is not, wrap non-string with str()
            left_is_string = left_type and left_type.name == "string"
            right_is_string = right_type and right_type.name == "string"

            if left_is_string and right_type and not right_is_string:
                # String + non-string: wrap right side with str()
                left = self.generate_expression(expr.left)
                right = self.generate_expression(expr.right)
                return f"({left} + str({right}))"
            elif right_is_string and left_type and not left_is_string:
                # Non-string + string: wrap left side with str()
                left = self.generate_expression(expr.left)
                right = self.generate_expression(expr.right)
                return f"(str({left}) + {right})"

        # Regular binary operations
        left = self.generate_expression(expr.left)
        right = self.generate_expression(expr.right)

        # Map operator
        op_map = {
            BinaryOperator.ADD: "+",
            BinaryOperator.SUBTRACT: "-",
            BinaryOperator.MULTIPLY: "*",
            BinaryOperator.DIVIDE: "/",
            BinaryOperator.FLOOR_DIVIDE: "//",
            BinaryOperator.MODULO: "%",
            BinaryOperator.POWER: "**",
            BinaryOperator.EQUAL: "==",
            BinaryOperator.NOT_EQUAL: "!=",
            BinaryOperator.LESS_THAN: "<",
            BinaryOperator.LESS_EQUAL: "<=",
            BinaryOperator.GREATER_THAN: ">",
            BinaryOperator.GREATER_EQUAL: ">=",
            BinaryOperator.AND: "and",
            BinaryOperator.OR: "or",
            BinaryOperator.BIT_AND: "&",
            BinaryOperator.BIT_OR: "|",
            BinaryOperator.BIT_XOR: "^",
            BinaryOperator.LEFT_SHIFT: "<<",
            BinaryOperator.RIGHT_SHIFT: ">>",
            BinaryOperator.IN: "in",
            BinaryOperator.NOT_IN: "not in",
            BinaryOperator.IS: "is",
            BinaryOperator.IS_NOT: "is not",
        }

        op = op_map.get(expr.op, "+")
        return f"({left} {op} {right})"

    def generate_unary_op(self, expr: IRUnaryOp) -> str:
        """Generate unary operation."""
        operand = self.generate_expression(expr.operand)

        if expr.op == UnaryOperator.NOT:
            return f"not {operand}"
        elif expr.op == UnaryOperator.NEGATE:
            return f"-{operand}"
        elif expr.op == UnaryOperator.POSITIVE:
            return f"+{operand}"
        elif expr.op == UnaryOperator.BIT_NOT:
            return f"~{operand}"
        else:
            return operand

    def generate_call(self, expr: IRCall) -> str:
        """Generate function call."""
        # STDLIB TRANSLATION: Translate stdlib calls to Python equivalents
        if isinstance(expr.function, IRPropertyAccess):
            obj = expr.function.object
            method = expr.function.property

            # str.length(x) → len(x)
            if isinstance(obj, IRIdentifier) and obj.name == "str" and method == "length":
                if len(expr.args) == 1:
                    arg = self.generate_expression(expr.args[0])
                    return f"len({arg})"

            # str.contains(s, substr) → substr in s
            if isinstance(obj, IRIdentifier) and obj.name == "str" and method == "contains":
                if len(expr.args) == 2:
                    string_arg = self.generate_expression(expr.args[0])
                    substr_arg = self.generate_expression(expr.args[1])
                    return f"({substr_arg} in {string_arg})"

        # Check if this is an enum variant constructor
        is_enum_variant = False
        if isinstance(expr.function, IRIdentifier):
            # Heuristic: uppercase first letter = enum variant
            # Known variants: Some, Ok, Err, etc.
            if expr.function.name and expr.function.name[0].isupper():
                is_enum_variant = True

        func = self.generate_expression(expr.function)

        # Special case: Convert map(lambda, iterable) to comprehension
        if isinstance(expr.function, IRIdentifier):
            # Pattern: list(map(lambda x: expr, iterable)) -> [expr for x in iterable]
            if expr.function.name == "list" and len(expr.args) == 1:
                inner = expr.args[0]
                if isinstance(inner, IRCall) and isinstance(inner.function, IRIdentifier):
                    if inner.function.name == "map" and len(inner.args) == 2:
                        lambda_expr = inner.args[0]
                        iterable_expr = inner.args[1]
                        if isinstance(lambda_expr, IRLambda) and lambda_expr.params:
                            param_name = lambda_expr.params[0].name
                            body_expr = self.generate_expression(lambda_expr.body)
                            iterable = self.generate_expression(iterable_expr)
                            return f"[{body_expr} for {param_name} in {iterable}]"

            # Pattern: map(lambda x: expr, iterable) -> (expr for x in iterable)
            # Used in generator expressions
            elif expr.function.name == "map" and len(expr.args) == 2:
                lambda_expr = expr.args[0]
                iterable_expr = expr.args[1]
                if isinstance(lambda_expr, IRLambda) and lambda_expr.params:
                    param_name = lambda_expr.params[0].name
                    body_expr = self.generate_expression(lambda_expr.body)
                    iterable = self.generate_expression(iterable_expr)
                    # Return generator expression (without list())
                    return f"({body_expr} for {param_name} in {iterable})"

        # Regular function call
        if is_enum_variant and expr.args and not expr.kwargs:
            # Enum variant constructor: Some(x) → Some(value=x)
            # Use keyword argument for single-argument variants
            if len(expr.args) == 1:
                arg_value = self.generate_expression(expr.args[0])
                return f"{func}(value={arg_value})"
            else:
                # Multiple arguments: use field_0, field_1, etc.
                kwargs_list = [f"field_{i}={self.generate_expression(arg)}" for i, arg in enumerate(expr.args)]
                return f"{func}({', '.join(kwargs_list)})"
        else:
            # Regular function call
            args = [self.generate_expression(arg) for arg in expr.args]
            kwargs = [f"{k}={self.generate_expression(v)}" for k, v in expr.kwargs.items()]

            all_args = args + kwargs
            return f"{func}({', '.join(all_args)})"

    def generate_array(self, expr: IRArray) -> str:
        """Generate list literal."""
        elements = [self.generate_expression(el) for el in expr.elements]
        return f"[{', '.join(elements)}]"

    def generate_dict(self, expr: IRMap) -> str:
        """Generate dict literal."""
        if not expr.entries:
            return "{}"

        entries = [f'"{k}": {self.generate_expression(v)}' for k, v in expr.entries.items()]
        return "{" + ", ".join(entries) + "}"

    def generate_ternary(self, expr: IRTernary) -> str:
        """Generate ternary expression (Python's if-else)."""
        true_val = self.generate_expression(expr.true_value)
        cond = self.generate_expression(expr.condition)
        false_val = self.generate_expression(expr.false_value)
        return f"{true_val} if {cond} else {false_val}"

    def generate_comprehension(self, expr: IRComprehension) -> str:
        """
        Generate Python comprehension from IR.

        Supports list, dict, set, and generator comprehensions.
        """
        iterable = self.generate_expression(expr.iterable)
        iterator = expr.iterator

        # Handle condition (filter)
        condition_str = ""
        if expr.condition:
            condition_str = f" if {self.generate_expression(expr.condition)}"

        # Generate based on comprehension type
        if expr.comprehension_type == "list":
            target = self.generate_expression(expr.target)
            return f"[{target} for {iterator} in {iterable}{condition_str}]"

        elif expr.comprehension_type == "dict":
            # For dict comprehensions, target is an IRMap with __key__ and __value__
            if isinstance(expr.target, IRMap) and "__key__" in expr.target.entries and "__value__" in expr.target.entries:
                key = self.generate_expression(expr.target.entries["__key__"])
                value = self.generate_expression(expr.target.entries["__value__"])
                return f"{{{key}: {value} for {iterator} in {iterable}{condition_str}}}"
            else:
                # Fallback: treat as list comprehension
                target = self.generate_expression(expr.target)
                return f"[{target} for {iterator} in {iterable}{condition_str}]"

        elif expr.comprehension_type == "set":
            target = self.generate_expression(expr.target)
            return f"{{{target} for {iterator} in {iterable}{condition_str}}}"

        elif expr.comprehension_type == "generator":
            target = self.generate_expression(expr.target)
            return f"({target} for {iterator} in {iterable}{condition_str})"

        else:
            # Default to list comprehension
            target = self.generate_expression(expr.target)
            return f"[{target} for {iterator} in {iterable}{condition_str}]"

    def generate_lambda(self, expr: IRLambda) -> str:
        """Generate lambda expression."""
        params = ", ".join(p.name for p in expr.params)

        if isinstance(expr.body, list):
            # Multi-statement lambda (not supported in Python)
            return f"lambda {params}: None  # Multi-statement lambda not supported"
        else:
            body = self.generate_expression(expr.body)
            return f"lambda {params}: {body}"

    def generate_pattern_match(self, expr: IRPatternMatch) -> str:
        """
        Generate pattern matching expression.

        For pattern `opt is Some(val)`, generates: isinstance(opt, Some)
        The value binding happens in the if statement generation.

        For pattern `opt is None`, generates: isinstance(opt, None_)
        """
        value = self.generate_expression(expr.value)

        # Pattern can be IRCall (Some(val)) or IRIdentifier (None)
        if isinstance(expr.pattern, IRCall):
            # Pattern like Some(val) or Ok(val)
            variant_name = self.generate_expression(expr.pattern.function)
            return f"isinstance({value}, {variant_name})"
        elif isinstance(expr.pattern, IRIdentifier):
            # Pattern like None or Some without binding
            variant_name = expr.pattern.name
            # Handle Python keyword conflicts (None → None_)
            if variant_name in ("None", "True", "False"):
                variant_name = f"{variant_name}_"
            return f"isinstance({value}, {variant_name})"
        elif isinstance(expr.pattern, IRPropertyAccess):
            # Pattern like Option.Some
            variant_name = self.generate_expression(expr.pattern)
            return f"isinstance({value}, {variant_name})"
        else:
            return f"isinstance({value}, {self.generate_expression(expr.pattern)})"

    def generate_old_expr(self, expr: IROldExpr) -> str:
        """
        Generate 'old' expression for postconditions.

        The old expression references a captured pre-state value.
        Generated code will access __old_{varname} variables.

        Example:
            old balance → __old_balance
            old this.count → __old_this_count
        """
        # Generate unique variable name for old value
        inner_expr = self.generate_expression(expr.expression)
        # Sanitize expression to create valid variable name
        var_name = inner_expr.replace(".", "_").replace("[", "_").replace("]", "").replace("(", "").replace(")", "")
        return f"__old_{var_name}"

    # ========================================================================
    # Contract Generation
    # ========================================================================

    def _has_contracts(self, func: IRFunction) -> bool:
        """Check if function has any contract clauses."""
        return bool(func.requires or func.ensures or func.effects)

    def _find_old_expressions(self, clauses: List[IRContractClause]) -> List[IRExpression]:
        """
        Find all 'old' expressions in contract clauses.

        Returns list of expressions that need to be captured before function execution.
        """
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
            # Add more expression types as needed

        for clause in clauses:
            visit_expr(clause.expression)

        return old_exprs

    def generate_contract_checks(
        self,
        func: IRFunction,
        is_method: bool = False,
        class_name: Optional[str] = None
    ) -> tuple[List[str], List[str], List[str]]:
        """
        Generate contract checking code for a function.

        Returns:
            (precondition_lines, postcondition_setup_lines, postcondition_check_lines)
        """
        precondition_lines = []
        postcondition_setup = []
        postcondition_checks = []

        # Generate precondition checks
        if func.requires:
            self.required_imports.add("from assertlang.runtime.contracts import check_precondition")

            for clause in func.requires:
                condition_expr = self.generate_expression(clause.expression)
                expr_str = self._expression_to_string(clause.expression)

                # Build context dict with parameter values
                context_items = []
                for param in func.params:
                    context_items.append(f'"{param.name}": {param.name}')

                context_str = "{" + ", ".join(context_items) + "}" if context_items else "None"

                check_call = (
                    f"check_precondition(\n"
                    f"    {condition_expr},\n"
                    f'    "{clause.name}",\n'
                    f'    "{expr_str}",\n'
                    f'    "{func.name}",\n'
                )
                if class_name:
                    check_call += f'    class_name="{class_name}",\n'
                check_call += f"    context={context_str}\n)"

                precondition_lines.append(check_call)

        # Generate postcondition checking code
        if func.ensures:
            self.required_imports.add("from assertlang.runtime.contracts import check_postcondition")

            # Find all 'old' expressions that need capturing
            old_exprs = self._find_old_expressions(func.ensures)

            # Capture old values before function body
            for old_expr in old_exprs:
                expr_code = self.generate_expression(old_expr)
                var_name = expr_code.replace(".", "_").replace("[", "_").replace("]", "").replace("(", "").replace(")", "")
                postcondition_setup.append(f"__old_{var_name} = {expr_code}")

            # Generate postcondition checks (to be inserted after function body)
            for clause in func.ensures:
                # Replace 'result' identifier with '__result' in expression
                condition_expr = self._replace_result_with_underscore(clause.expression)
                expr_str = self._expression_to_string(clause.expression)

                # Build context with result and parameters
                context_items = ['("result", __result)']
                for param in func.params:
                    context_items.append(f'("{param.name}", {param.name})')

                context_str = "dict([" + ", ".join(context_items) + "])"

                check_call = (
                    f"check_postcondition(\n"
                    f"    {condition_expr},\n"
                    f'    "{clause.name}",\n'
                    f'    "{expr_str}",\n'
                    f'    "{func.name}",\n'
                )
                if class_name:
                    check_call += f'    class_name="{class_name}",\n'
                check_call += f"    context={context_str}\n)"

                postcondition_checks.append(check_call)

        return precondition_lines, postcondition_setup, postcondition_checks

    def _replace_result_with_underscore(self, expr: IRExpression) -> str:
        """
        Replace 'result' identifier with '__result' in postcondition expressions.

        This handles the special 'result' variable in postconditions that refers
        to the function's return value.
        """
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
                BinaryOperator.EQUAL: "==",
                BinaryOperator.NOT_EQUAL: "!=",
                BinaryOperator.LESS_THAN: "<",
                BinaryOperator.LESS_EQUAL: "<=",
                BinaryOperator.GREATER_THAN: ">",
                BinaryOperator.GREATER_EQUAL: ">=",
                BinaryOperator.AND: "and",
                BinaryOperator.OR: "or",
            }
            op = op_map.get(expr.op, "+")
            return f"({left} {op} {right})"
        elif isinstance(expr, IRUnaryOp):
            operand = self._replace_result_with_underscore(expr.operand)
            if expr.op == UnaryOperator.NOT:
                return f"not {operand}"
            elif expr.op == UnaryOperator.NEGATE:
                return f"-{operand}"
            return operand
        elif isinstance(expr, IRPropertyAccess):
            obj = self._replace_result_with_underscore(expr.object)
            return f"{obj}.{expr.property}"
        elif isinstance(expr, IRCall):
            func_expr = self._replace_result_with_underscore(expr.function)
            args = [self._replace_result_with_underscore(arg) for arg in expr.args]
            return f"{func_expr}({', '.join(args)})"
        elif isinstance(expr, IROldExpr):
            # Old expression should use __old_ variable
            return self.generate_old_expr(expr)
        else:
            # For other expressions, use regular generation
            return self.generate_expression(expr)

    def _expression_to_string(self, expr: IRExpression) -> str:
        """
        Convert expression to readable string for error messages.

        This is a simplified version that produces human-readable expression strings.
        """
        if isinstance(expr, IRBinaryOp):
            left = self._expression_to_string(expr.left)
            right = self._expression_to_string(expr.right)
            op_str = expr.op.value  # Get the operator string
            return f"{left} {op_str} {right}"
        elif isinstance(expr, IRUnaryOp):
            operand = self._expression_to_string(expr.operand)
            return f"{expr.op.value} {operand}"
        elif isinstance(expr, IRLiteral):
            if expr.literal_type == LiteralType.STRING:
                return f'"{expr.value}"'
            else:
                return str(expr.value)
        elif isinstance(expr, IRIdentifier):
            return expr.name
        elif isinstance(expr, IRPropertyAccess):
            obj = self._expression_to_string(expr.object)
            return f"{obj}.{expr.property}"
        elif isinstance(expr, IRCall):
            func = self._expression_to_string(expr.function)
            args = ", ".join(self._expression_to_string(arg) for arg in expr.args)
            return f"{func}({args})"
        elif isinstance(expr, IROldExpr):
            inner = self._expression_to_string(expr.expression)
            return f"old {inner}"
        else:
            return "<expr>"


# ============================================================================
# Public API
# ============================================================================


def generate_python(module: IRModule) -> str:
    """
    Generate Python code from IR module.

    Args:
        module: IR module to convert

    Returns:
        Python source code as string

    Example:
        >>> from dsl.ir import IRModule, IRFunction, IRParameter, IRType
        >>> module = IRModule(name="example", functions=[
        ...     IRFunction(
        ...         name="greet",
        ...         params=[IRParameter(name="name", param_type=IRType(name="string"))],
        ...         return_type=IRType(name="string")
        ...     )
        ... ])
        >>> code = generate_python(module)
        >>> print(code)
    """
    generator = PythonGeneratorV2()
    return generator.generate(module)
