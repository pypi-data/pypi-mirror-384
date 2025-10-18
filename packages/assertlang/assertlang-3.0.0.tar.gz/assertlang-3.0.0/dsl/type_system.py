"""
Promptware Universal Type System

This module provides cross-language type mapping and type inference for the
Promptware universal code translation system. It enables seamless translation
between dynamically-typed (Python, Node.js) and statically-typed (Go, Rust, .NET)
languages.

Design Principles:
1. Conservative - Safe type mappings over optimal
2. Explicit - Clear type annotations for static languages
3. Pragmatic - Handle common cases well, document edge cases
4. Extensible - Easy to add new languages and types

Capabilities:
- Cross-language type mapping (PW ↔ Python/Node/Go/Rust/.NET)
- Type inference from literals and usage patterns
- Type compatibility checking
- Type normalization and validation
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from dsl.ir import (
    BinaryOperator,
    IRArray,
    IRAssignment,
    IRBinaryOp,
    IRCall,
    IRExpression,
    IRFunction,
    IRIdentifier,
    IRLiteral,
    IRMap,
    IRModule,
    IRNode,
    IRPropertyAccess,
    IRReturn,
    IRType,
    LiteralType,
)


# ============================================================================
# Type System Configuration
# ============================================================================


class PrimitiveType(Enum):
    """Primitive types in PW DSL."""

    STRING = "string"
    INT = "int"
    FLOAT = "float"
    BOOL = "bool"
    NULL = "null"
    ANY = "any"


class CollectionType(Enum):
    """Collection types in PW DSL."""

    ARRAY = "array"
    MAP = "map"


# ============================================================================
# Cross-Language Type Mappings
# ============================================================================


class TypeMappings:
    """
    Cross-language type mappings.

    Maps PW DSL types to language-specific types for all supported languages.
    """

    # Primitive type mappings
    PRIMITIVES: Dict[str, Dict[str, str]] = {
        "python": {
            "string": "str",
            "int": "int",
            "float": "float",
            "bool": "bool",
            "null": "None",
            "any": "Any",
        },
        "go": {
            "string": "string",
            "int": "int",
            "float": "float64",
            "bool": "bool",
            "null": "nil",
            "any": "interface{}",
        },
        "rust": {
            "string": "String",
            "int": "i32",
            "float": "f64",
            "bool": "bool",
            "null": "None",
            "any": "Box<dyn std::any::Any>",
        },
        "dotnet": {
            "string": "string",
            "int": "int",
            "float": "double",
            "bool": "bool",
            "null": "null",
            "any": "object",
        },
        "nodejs": {
            "string": "string",
            "int": "number",
            "float": "number",
            "bool": "boolean",
            "null": "null",
            "any": "any",
        },
    }

    # Collection type mappings
    COLLECTIONS: Dict[str, Dict[str, str]] = {
        "python": {
            "array": "List",
            "map": "Dict",
        },
        "go": {
            "array": "[]",
            "map": "map",
        },
        "rust": {
            "array": "Vec",
            "map": "HashMap",
        },
        "dotnet": {
            "array": "List",
            "map": "Dictionary",
        },
        "nodejs": {
            "array": "Array",
            "map": "Map",
        },
    }

    # Language-specific import requirements for types
    IMPORTS: Dict[str, Dict[str, str]] = {
        "python": {
            "List": "from typing import List",
            "Dict": "from typing import Dict",
            "Any": "from typing import Any",
            "Optional": "from typing import Optional",
            "Union": "from typing import Union",
        },
        "go": {
            "HashMap": "",  # Built-in map type
        },
        "rust": {
            "HashMap": "use std::collections::HashMap;",
            "Box": "",  # Built-in
            "Vec": "",  # Built-in
        },
        "dotnet": {
            "List": "using System.Collections.Generic;",
            "Dictionary": "using System.Collections.Generic;",
        },
        "nodejs": {
            # TypeScript types don't need imports
        },
    }


# ============================================================================
# Type System Core
# ============================================================================


@dataclass
class TypeInfo:
    """
    Rich type information for inference and validation.

    Stores not just the type, but also confidence level and source.
    """

    pw_type: str  # PW DSL type (e.g., "string", "int", "array<string>")
    confidence: float = 1.0  # 0.0 to 1.0
    source: str = "explicit"  # "explicit", "inferred", "default"
    nullable: bool = False  # Can be null/nil/None


class TypeSystem:
    """
    Universal type system for Promptware.

    Provides:
    - Cross-language type mapping
    - Type inference from literals and usage patterns
    - Type compatibility checking
    - Type normalization
    """

    def __init__(self):
        self.mappings = TypeMappings()

    # ========================================================================
    # Type Mapping (PW ↔ Languages)
    # ========================================================================

    def map_to_language(
        self, pw_type: IRType, target_lang: str, context: str = "default"
    ) -> str:
        """
        Map PW DSL type to target language type.

        Args:
            pw_type: IR type node
            target_lang: Target language (python/go/rust/dotnet/nodejs)
            context: Context hint (e.g., "generic", "optional")

        Returns:
            Language-specific type string

        Examples:
            map_to_language(IRType("string"), "go") -> "string"
            map_to_language(IRType("int", is_optional=True), "rust") -> "Option<i32>"
            map_to_language(IRType("array", generic_args=[IRType("string")]), "python") -> "List[str]"
        """
        # Handle optional types (T?)
        if pw_type.is_optional:
            base_type = self._map_base_type(pw_type.name, pw_type.generic_args, target_lang)
            return self._wrap_optional(base_type, target_lang)

        # Handle union types (A|B|C)
        if pw_type.union_types:
            types = [self._map_base_type(pw_type.name, [], target_lang)]
            types.extend(
                self._map_base_type(t.name, t.generic_args, target_lang)
                for t in pw_type.union_types
            )
            return self._wrap_union(types, target_lang)

        # Regular type mapping
        return self._map_base_type(pw_type.name, pw_type.generic_args, target_lang)

    def _map_base_type(
        self, type_name: str, generic_args: List[IRType], target_lang: str
    ) -> str:
        """Map base type (without optional/union)."""
        # Check if it's a primitive type
        if type_name in self.mappings.PRIMITIVES.get(target_lang, {}):
            return self.mappings.PRIMITIVES[target_lang][type_name]

        # Check if it's a collection type
        if type_name in self.mappings.COLLECTIONS.get(target_lang, {}):
            collection_type = self.mappings.COLLECTIONS[target_lang][type_name]

            # Add generic arguments
            if generic_args:
                mapped_args = [
                    self.map_to_language(arg, target_lang) for arg in generic_args
                ]

                if target_lang == "go":
                    # Go: []T or map[K]V
                    if type_name == "array":
                        return f"[]{mapped_args[0]}"
                    elif type_name == "map" and len(mapped_args) >= 2:
                        return f"map[{mapped_args[0]}]{mapped_args[1]}"
                elif target_lang == "rust":
                    # Rust: Vec<T> or HashMap<K, V>
                    args_str = ", ".join(mapped_args)
                    return f"{collection_type}<{args_str}>"
                else:
                    # Python/C#/TypeScript: List[T] or Dict[K, V]
                    args_str = ", ".join(mapped_args)
                    return f"{collection_type}[{args_str}]"

            return collection_type

        # Check if it's a generic type parameter (single uppercase letter or CamelCase type param)
        # Type parameters like T, E, K, V should stay as-is
        if len(type_name) == 1 and type_name.isupper():
            # Single letter type parameter (T, E, K, V)
            return type_name

        # Custom type (User, Payment, Option, Result, etc.) - handle generic args
        if generic_args:
            mapped_args = [
                self.map_to_language(arg, target_lang) for arg in generic_args
            ]
            args_str = ", ".join(mapped_args)
            # Python/TypeScript style generic: Option[T]
            if target_lang in ("python", "nodejs", "dotnet"):
                return f"{type_name}[{args_str}]"
            elif target_lang in ("rust", "go"):
                return f"{type_name}<{args_str}>"
            return f"{type_name}[{args_str}]"

        # Custom type without generics - return as-is
        return type_name

    def _wrap_optional(self, base_type: str, target_lang: str) -> str:
        """Wrap type in language-specific optional."""
        if target_lang == "python":
            return f"Optional[{base_type}]"
        elif target_lang == "go":
            # Go uses pointers for optionals
            return f"*{base_type}"
        elif target_lang == "rust":
            return f"Option<{base_type}>"
        elif target_lang == "dotnet":
            # C# nullable types
            if base_type in ["int", "double", "bool"]:
                return f"{base_type}?"
            return base_type  # Reference types already nullable
        elif target_lang == "nodejs":
            return f"{base_type} | null"
        return base_type

    def _wrap_union(self, types: List[str], target_lang: str) -> str:
        """Wrap types in language-specific union."""
        if target_lang == "python":
            return f"Union[{', '.join(types)}]"
        elif target_lang == "go":
            # Go doesn't have native unions, use interface{}
            return "interface{}"
        elif target_lang == "rust":
            # Rust enums for unions (simplified)
            return f"/* Union: {' | '.join(types)} */"
        elif target_lang == "dotnet":
            # C# doesn't have native unions, use object
            return "object"
        elif target_lang == "nodejs":
            return " | ".join(types)
        return types[0]  # Fallback to first type

    def map_from_language(
        self, lang_type: str, source_lang: str
    ) -> IRType:
        """
        Map language-specific type to PW DSL type.

        Args:
            lang_type: Language-specific type string
            source_lang: Source language (python/go/rust/dotnet/nodejs)

        Returns:
            IR type node

        Examples:
            map_from_language("str", "python") -> IRType("string")
            map_from_language("Vec<i32>", "rust") -> IRType("array", generic_args=[IRType("int")])
        """
        # Reverse lookup in primitives
        for pw_type, mapped in self.mappings.PRIMITIVES.get(source_lang, {}).items():
            if lang_type == mapped:
                return IRType(name=pw_type)

        # Handle collections with generics
        if source_lang == "python":
            if lang_type.startswith("List["):
                inner = lang_type[5:-1]
                return IRType(
                    name="array",
                    generic_args=[self.map_from_language(inner, source_lang)]
                )
            if lang_type.startswith("Dict["):
                inner = lang_type[5:-1]
                k, v = inner.split(",", 1)
                return IRType(
                    name="map",
                    generic_args=[
                        self.map_from_language(k.strip(), source_lang),
                        self.map_from_language(v.strip(), source_lang)
                    ]
                )
            if lang_type.startswith("Optional["):
                inner = lang_type[9:-1]
                inner_type = self.map_from_language(inner, source_lang)
                inner_type.is_optional = True
                return inner_type

        # Custom type - return as-is
        return IRType(name=lang_type)

    # ========================================================================
    # Type Inference
    # ========================================================================

    def infer_from_literal(self, literal: IRLiteral) -> TypeInfo:
        """
        Infer PW type from a literal value.

        Args:
            literal: IR literal node

        Returns:
            TypeInfo with inferred type

        Examples:
            infer_from_literal(IRLiteral("hello", STRING)) -> TypeInfo("string", 1.0)
            infer_from_literal(IRLiteral(42, INTEGER)) -> TypeInfo("int", 1.0)
        """
        type_map = {
            LiteralType.STRING: "string",
            LiteralType.INTEGER: "int",
            LiteralType.FLOAT: "float",
            LiteralType.BOOLEAN: "bool",
            LiteralType.NULL: "null",
        }

        pw_type = type_map.get(literal.literal_type, "any")
        return TypeInfo(
            pw_type=pw_type,
            confidence=1.0,
            source="literal",
            nullable=(literal.literal_type == LiteralType.NULL)
        )

    def infer_from_expression(
        self, expr: IRExpression, context: Dict[str, TypeInfo]
    ) -> TypeInfo:
        """
        Infer type from an expression.

        Args:
            expr: IR expression node
            context: Variable name -> TypeInfo mapping

        Returns:
            TypeInfo with inferred type
        """
        # Literal
        if isinstance(expr, IRLiteral):
            return self.infer_from_literal(expr)

        # Identifier
        if isinstance(expr, IRIdentifier):
            if expr.name in context:
                return context[expr.name]
            return TypeInfo(pw_type="any", confidence=0.0, source="unknown")

        # Binary operation
        if isinstance(expr, IRBinaryOp):
            left_type = self.infer_from_expression(expr.left, context)
            right_type = self.infer_from_expression(expr.right, context)

            # Arithmetic operators return numeric type
            if expr.op in [
                BinaryOperator.ADD,
                BinaryOperator.SUBTRACT,
                BinaryOperator.MULTIPLY,
                BinaryOperator.DIVIDE,
            ]:
                # If either is float, result is float
                if left_type.pw_type == "float" or right_type.pw_type == "float":
                    return TypeInfo(pw_type="float", confidence=0.9, source="inferred")
                return TypeInfo(pw_type="int", confidence=0.9, source="inferred")

            # Comparison operators return bool
            if expr.op in [
                BinaryOperator.EQUAL,
                BinaryOperator.NOT_EQUAL,
                BinaryOperator.LESS_THAN,
                BinaryOperator.LESS_EQUAL,
                BinaryOperator.GREATER_THAN,
                BinaryOperator.GREATER_EQUAL,
            ]:
                return TypeInfo(pw_type="bool", confidence=1.0, source="inferred")

            # Logical operators return bool
            if expr.op in [BinaryOperator.AND, BinaryOperator.OR]:
                return TypeInfo(pw_type="bool", confidence=1.0, source="inferred")

        # Property access
        if isinstance(expr, IRPropertyAccess):
            # Try to infer from object type
            obj_type = self.infer_from_expression(expr.object, context)
            # For now, return any (requires type definitions for proper inference)
            return TypeInfo(pw_type="any", confidence=0.3, source="inferred")

        # Function call
        if isinstance(expr, IRCall):
            # Return type depends on function definition
            # For now, return any
            return TypeInfo(pw_type="any", confidence=0.3, source="inferred")

        # Array
        if isinstance(expr, IRArray):
            # Infer element type from first element (if exists)
            if expr.elements:
                elem_type = self.infer_from_expression(expr.elements[0], context)
                # Check if all elements have same type
                all_same = all(
                    self.infer_from_expression(elem, context).pw_type == elem_type.pw_type
                    for elem in expr.elements
                )
                if all_same and elem_type.pw_type != "any":
                    # Homogeneous array - return array<element_type>
                    return TypeInfo(
                        pw_type=f"array<{elem_type.pw_type}>",
                        confidence=0.9,
                        source="inferred"
                    )
            # Empty array or mixed types
            return TypeInfo(pw_type="array<any>", confidence=0.5, source="inferred")

        # Map/Dictionary
        if isinstance(expr, IRMap):
            # For now, return map<string, any>
            # Could be enhanced to infer value types
            return TypeInfo(pw_type="map<string, any>", confidence=0.5, source="inferred")

        # Default
        return TypeInfo(pw_type="any", confidence=0.0, source="unknown")

    def infer_from_usage(
        self, var_name: str, function: IRFunction
    ) -> TypeInfo:
        """
        Infer variable type from its usage patterns in a function.

        Args:
            var_name: Variable name
            function: Function containing the variable

        Returns:
            TypeInfo with inferred type

        Strategy:
        1. Check assignments to the variable
        2. Check how the variable is used (method calls, operations)
        3. Combine evidence with confidence scoring
        """
        evidence: List[TypeInfo] = []
        context: Dict[str, TypeInfo] = {}

        # Build context from parameters
        for param in function.params:
            if param.param_type:
                context[param.name] = TypeInfo(
                    pw_type=param.param_type.name,
                    confidence=1.0,
                    source="explicit"
                )

        # Analyze function body
        for stmt in function.body:
            # Assignment statements
            if isinstance(stmt, IRAssignment) and stmt.target == var_name:
                type_info = self.infer_from_expression(stmt.value, context)
                evidence.append(type_info)
                context[var_name] = type_info

        # Combine evidence
        if not evidence:
            return TypeInfo(pw_type="any", confidence=0.0, source="unknown")

        # Take highest confidence type
        best = max(evidence, key=lambda t: t.confidence)
        return best

    def propagate_types(self, module: IRModule) -> Dict[str, TypeInfo]:
        """
        Propagate type information through the entire module.

        Args:
            module: IR module

        Returns:
            Mapping of variable names to their inferred types

        This performs a dataflow analysis to infer types throughout the module.
        """
        type_map: Dict[str, TypeInfo] = {}

        # First pass: collect explicit types
        for func in module.functions:
            # Parameter types
            for param in func.params:
                if param.param_type:
                    key = f"{func.name}.{param.name}"
                    type_map[key] = TypeInfo(
                        pw_type=param.param_type.name,
                        confidence=1.0,
                        source="explicit"
                    )

        # Second pass: infer types from assignments
        for func in module.functions:
            for stmt in func.body:
                if isinstance(stmt, IRAssignment):
                    context = {
                        param.name: type_map.get(f"{func.name}.{param.name}", TypeInfo("any", 0.0))
                        for param in func.params
                    }
                    type_info = self.infer_from_expression(stmt.value, context)
                    key = f"{func.name}.{stmt.target}"
                    type_map[key] = type_info

        return type_map

    # ========================================================================
    # Cross-Function Type Inference (Context-Aware)
    # ========================================================================

    def analyze_cross_function_types(self, module: IRModule) -> Dict[str, TypeInfo]:
        """
        Analyze types across function boundaries using context analysis.

        This method uses call graph and data flow analysis to infer types
        based on how values flow between functions.

        Args:
            module: IR module to analyze

        Returns:
            Mapping of fully-qualified variable names to inferred types

        Strategy:
        1. Build call graph
        2. Track data flow between functions
        3. Infer return types from usage in callers
        4. Infer parameter types from passed arguments
        5. Improve confidence scores with cross-function evidence
        """
        # Import here to avoid circular dependency
        from dsl.context_analyzer import ContextAnalyzer

        # Build context
        analyzer = ContextAnalyzer()
        analyzer.analyze_module(module)

        type_map: Dict[str, TypeInfo] = {}

        # Analyze each function
        for func in module.functions:
            # Infer return type from how it's used
            return_type = self._infer_return_type_from_usage(func, analyzer, module)
            if return_type and not func.return_type:
                type_map[f"{func.name}.__return__"] = return_type

            # Infer parameter types from call sites
            for param in func.params:
                if not param.param_type:
                    param_type = self._infer_param_type_from_calls(
                        func.name, param.name, analyzer, module
                    )
                    if param_type:
                        type_map[f"{func.name}.{param.name}"] = param_type

        return type_map

    def _infer_return_type_from_usage(
        self,
        func: IRFunction,
        analyzer: Any,  # ContextAnalyzer (Any to avoid circular import)
        module: IRModule
    ) -> Optional[TypeInfo]:
        """
        Infer return type by analyzing how return value is used in callers.

        Example:
            def get_user(id):
                return db.find(id)

            def process():
                user = get_user(42)
                print(user.name)  # <-- Infer get_user returns object with 'name'
        """
        context = analyzer.get_function_context(func.name)
        if not context:
            return None

        # Collect evidence from return statements
        return_types = []
        for return_expr in context.return_expressions:
            # Build type context from function locals
            type_context = self._build_type_context(func)
            type_info = self.infer_from_expression(return_expr, type_context)
            return_types.append(type_info)

        # Check how callers use the return value
        property_accesses = set()
        for caller_name in context.called_by:
            caller_context = analyzer.get_function_context(caller_name)
            if not caller_context:
                continue

            # Find variables that receive the return value
            # (simplified - would need more sophisticated tracking)
            # This would track: result = get_user(id); print(result.name)

        # Combine evidence
        if return_types:
            # Take most specific type with highest confidence
            best = max(return_types, key=lambda t: (t.confidence, -len(t.pw_type)))
            return best

        return None

    def _infer_param_type_from_calls(
        self,
        func_name: str,
        param_name: str,
        analyzer: Any,
        module: IRModule
    ) -> Optional[TypeInfo]:
        """
        Infer parameter type from what callers pass.

        Example:
            def process_user(user):
                print(user.name)

            def main():
                u = User("Alice")
                process_user(u)  # <-- Infer param type from User

        Args:
            func_name: Name of function
            param_name: Name of parameter
            analyzer: Context analyzer
            module: IR module

        Returns:
            TypeInfo with inferred type or None
        """
        context = analyzer.get_function_context(func_name)
        if not context:
            return None

        # Get parameter index
        param_index = None
        for i, p in enumerate(context.parameters):
            if p == param_name:
                param_index = i
                break

        if param_index is None:
            return None

        # Collect types from all call sites
        passed_types = []
        for call_site in context.calls_made:
            if param_index < len(call_site.arguments):
                arg = call_site.arguments[param_index]

                # Get caller function to build context
                caller_func = self._find_function(call_site.caller_function, module)
                if caller_func:
                    type_context = self._build_type_context(caller_func)
                    type_info = self.infer_from_expression(arg, type_context)
                    passed_types.append(type_info)

        # Also check parameter usage in function body
        usage_type = None
        if param_name in context.variable_usage:
            usage = context.variable_usage[param_name]

            # If used with property access, likely an object
            if usage.property_accesses:
                usage_type = TypeInfo(
                    pw_type="object",
                    confidence=0.6,
                    source="inferred_from_property_access"
                )

            # If used with arithmetic operators, likely numeric
            if any(op in usage.operators_used for op in ['+', '-', '*', '/']):
                usage_type = TypeInfo(
                    pw_type="int",  # Could be float
                    confidence=0.5,
                    source="inferred_from_operators"
                )

        # Combine evidence
        all_types = passed_types + ([usage_type] if usage_type else [])
        if all_types:
            # Find most common type with highest confidence
            best = max(all_types, key=lambda t: t.confidence)
            return best

        return None

    def _build_type_context(self, func: IRFunction) -> Dict[str, TypeInfo]:
        """
        Build type context for a function's local scope.

        Args:
            func: Function to analyze

        Returns:
            Mapping of variable names to their types
        """
        context = {}

        # Add parameter types
        for param in func.params:
            if param.param_type:
                context[param.name] = TypeInfo(
                    pw_type=param.param_type.name,
                    confidence=1.0,
                    source="explicit"
                )

        # Infer types from assignments
        for stmt in func.body:
            if isinstance(stmt, IRAssignment):
                type_info = self.infer_from_expression(stmt.value, context)
                context[stmt.target] = type_info

        return context

    def _find_function(self, func_name: str, module: IRModule) -> Optional[IRFunction]:
        """
        Find a function by name in the module.

        Handles both simple names and class.method names.

        Args:
            func_name: Name of function (may include class prefix)
            module: IR module

        Returns:
            IRFunction or None
        """
        # Simple function
        for func in module.functions:
            if func.name == func_name:
                return func

        # Class method
        if "." in func_name:
            class_name, method_name = func_name.split(".", 1)
            for cls in module.classes:
                if cls.name == class_name:
                    for method in cls.methods:
                        if method.name == method_name:
                            return method

        return None

    # ========================================================================
    # Type Compatibility and Validation
    # ========================================================================

    def is_compatible(self, source_type: str, target_type: str) -> bool:
        """
        Check if source type can be assigned to target type.

        Args:
            source_type: Source PW type
            target_type: Target PW type

        Returns:
            True if compatible, False otherwise

        Examples:
            is_compatible("int", "float") -> True (widening)
            is_compatible("float", "int") -> False (narrowing)
            is_compatible("string", "string") -> True
        """
        # Same type
        if source_type == target_type:
            return True

        # any is compatible with everything
        if source_type == "any" or target_type == "any":
            return True

        # null is compatible with optional types
        if source_type == "null":
            return True  # null can be assigned to anything

        # Numeric widening: int -> float
        if source_type == "int" and target_type == "float":
            return True

        # Otherwise, incompatible
        return False

    def needs_cast(self, source_type: str, target_type: str) -> bool:
        """
        Check if explicit cast is needed for type conversion.

        Args:
            source_type: Source PW type
            target_type: Target PW type

        Returns:
            True if cast needed, False otherwise
        """
        if self.is_compatible(source_type, target_type):
            return False

        # Numeric narrowing needs cast
        if source_type == "float" and target_type == "int":
            return True

        # String conversions need cast
        if source_type != "string" and target_type == "string":
            return True

        return False

    def normalize_type(self, type_str: str) -> IRType:
        """
        Normalize a type string to IR type.

        Args:
            type_str: Type string (e.g., "array<string>", "int?")

        Returns:
            IR type node

        Parses type strings with generics, optionals, and unions.
        """
        # Handle optional (T?)
        if type_str.endswith("?"):
            base = type_str[:-1]
            ir_type = self.normalize_type(base)
            ir_type.is_optional = True
            return ir_type

        # Handle union (A|B|C)
        if "|" in type_str:
            parts = type_str.split("|")
            first = self.normalize_type(parts[0].strip())
            rest = [self.normalize_type(p.strip()) for p in parts[1:]]
            first.union_types = rest
            return first

        # Handle generics (array<T>, map<K,V>)
        if "<" in type_str and type_str.endswith(">"):
            base_end = type_str.index("<")
            base = type_str[:base_end]
            args_str = type_str[base_end + 1 : -1]

            # Parse generic arguments
            args = []
            depth = 0
            current = []
            for char in args_str:
                if char == "<":
                    depth += 1
                    current.append(char)
                elif char == ">":
                    depth -= 1
                    current.append(char)
                elif char == "," and depth == 0:
                    args.append("".join(current).strip())
                    current = []
                else:
                    current.append(char)
            if current:
                args.append("".join(current).strip())

            return IRType(
                name=base,
                generic_args=[self.normalize_type(arg) for arg in args]
            )

        # Simple type
        return IRType(name=type_str)

    def get_required_imports(
        self, types: List[IRType], target_lang: str
    ) -> Set[str]:
        """
        Get required import statements for the given types.

        Args:
            types: List of IR types
            target_lang: Target language

        Returns:
            Set of import statements
        """
        imports = set()

        for ir_type in types:
            # Map to language type
            lang_type = self.map_to_language(ir_type, target_lang)

            # Check if import needed
            for type_name, import_stmt in self.mappings.IMPORTS.get(target_lang, {}).items():
                if type_name in lang_type and import_stmt:
                    imports.add(import_stmt)

        return imports


# ============================================================================
# Utility Functions
# ============================================================================


def create_type_system() -> TypeSystem:
    """Create and return a TypeSystem instance."""
    return TypeSystem()
