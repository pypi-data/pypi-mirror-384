"""
Pydantic/TypedDict Generator: IR → Python Type Classes

Generates type classes from PW type definitions for use in:
- CrewAI agent coordination (Pydantic)
- LangGraph state machines (TypedDict)
- FastAPI endpoints (Pydantic)
- Data validation (Pydantic)
- Type-safe agent-to-agent communication

Design:
- IRTypeDefinition → Pydantic BaseModel or TypedDict
- IRType → Python type hints
- Mode selection: "pydantic" or "typeddict"
- Clean, idiomatic Python code
"""

from __future__ import annotations

from typing import Set, Literal

from dsl.ir import (
    IRModule,
    IRType,
    IRTypeDefinition,
    IRClass,
    IREnum,
    IREnumVariant,
)


class PydanticGenerator:
    """Generate Pydantic BaseModel or TypedDict classes from IR."""

    def __init__(self, mode: Literal["pydantic", "typeddict"] = "pydantic"):
        """
        Initialize generator.

        Args:
            mode: Output mode - "pydantic" for Pydantic models, "typeddict" for TypedDict
        """
        self.mode = mode
        self.required_imports: Set[str] = set()

    def generate(self, module: IRModule) -> str:
        """
        Generate Pydantic models from IR module.

        Args:
            module: IR module containing type definitions

        Returns:
            Python code with Pydantic models
        """
        self.required_imports.clear()
        lines = []

        # Always import Pydantic
        lines.append("from __future__ import annotations")
        lines.append("")
        lines.append("from pydantic import BaseModel, Field")
        lines.append("from typing import Optional, List, Dict, Any")
        lines.append("")

        # Module docstring
        if module.metadata.get("doc"):
            lines.append(f'"""{module.metadata["doc"]}"""')
            lines.append("")

        # Generate enums first (if needed)
        for enum in module.enums:
            lines.append(self.generate_enum(enum))
            lines.append("")
            lines.append("")

        # Generate type definitions as Pydantic models
        for type_def in module.types:
            lines.append(self.generate_pydantic_model_from_typedef(type_def))
            lines.append("")
            lines.append("")

        # Generate classes as Pydantic models
        for cls in module.classes:
            lines.append(self.generate_pydantic_model_from_class(cls))
            lines.append("")
            lines.append("")

        # Clean up excessive blank lines
        result = "\n".join(lines)
        while "\n\n\n\n" in result:
            result = result.replace("\n\n\n\n", "\n\n\n")

        return result.rstrip() + "\n"

    def generate_pydantic_model_from_typedef(self, type_def: IRTypeDefinition) -> str:
        """Generate Pydantic BaseModel from type definition."""
        lines = []

        # Class docstring
        if type_def.doc:
            lines.append(f'"""{type_def.doc}"""')

        # Class definition
        lines.append(f"class {type_def.name}(BaseModel):")

        # Handle generic types (e.g., Option<T>)
        if type_def.generic_params:
            # For now, we'll skip complex generics - focus on concrete types
            lines.append("    # Generic type - implement as needed")
            lines.append("    pass")
            return "\n".join(lines)

        # Fields
        if not type_def.fields:
            lines.append("    pass")
        else:
            for field in type_def.fields:
                field_type = self.generate_type_hint(field.field_type)

                # Add Field() for documentation/validation
                if field.doc:
                    lines.append(f'    {field.name}: {field_type} = Field(description="{field.doc}")')
                else:
                    lines.append(f"    {field.name}: {field_type}")

        return "\n".join(lines)

    def generate_pydantic_model_from_class(self, cls: IRClass) -> str:
        """Generate Pydantic BaseModel from class definition."""
        lines = []

        # Class docstring
        if cls.doc:
            lines.append(f'"""{cls.doc}"""')

        # Class definition
        lines.append(f"class {cls.name}(BaseModel):")

        # Properties become Pydantic fields
        if not cls.properties:
            lines.append("    pass")
        else:
            for prop in cls.properties:
                if prop and hasattr(prop, 'prop_type') and hasattr(prop, 'name'):
                    field_type = self.generate_type_hint(prop.prop_type)

                    # Add Field() for documentation/validation
                    if hasattr(prop, 'doc') and prop.doc:
                        lines.append(f'    {prop.name}: {field_type} = Field(description="{prop.doc}")')
                    else:
                        lines.append(f"    {prop.name}: {field_type}")

        return "\n".join(lines)

    def generate_type_hint(self, ir_type: IRType) -> str:
        """Generate Python type hint compatible with Pydantic."""
        # Map PW types to Python types
        type_map = {
            'int': 'int',
            'float': 'float',
            'string': 'str',
            'str': 'str',
            'bool': 'bool',
            'void': 'None',
            'any': 'Any',
            'null': 'None',
        }

        base_type = ir_type.name.lower()

        # Handle built-in types
        if base_type in type_map:
            return type_map[base_type]

        # Handle generic types
        if ir_type.generic_args:
            # list<T> → List[T]
            if base_type in ('list', 'array'):
                inner = self.generate_type_hint(ir_type.generic_args[0])
                return f"List[{inner}]"

            # map<K, V> → Dict[K, V]
            if base_type in ('map', 'dict'):
                if len(ir_type.generic_args) >= 2:
                    key_type = self.generate_type_hint(ir_type.generic_args[0])
                    val_type = self.generate_type_hint(ir_type.generic_args[1])
                    return f"Dict[{key_type}, {val_type}]"
                else:
                    return "Dict[str, Any]"

            # Option<T> → Optional[T]
            if base_type == 'option':
                inner = self.generate_type_hint(ir_type.generic_args[0])
                return f"Optional[{inner}]"

            # Result<T, E> → Union[T, E] or custom type
            if base_type == 'result':
                # For now, just use Any - this needs better handling
                return "Any"  # TODO: Better Result<T,E> handling

            # Generic with args but unknown base → treat as custom generic
            args = ", ".join(self.generate_type_hint(arg) for arg in ir_type.generic_args)
            return f"{ir_type.name}[{args}]"

        # Custom types (user-defined classes/types)
        return ir_type.name

    def generate_enum(self, enum: IREnum) -> str:
        """Generate Python Enum from IR enum."""
        lines = []

        # For Pydantic, we'll use Python's Enum
        self.required_imports.add("from enum import Enum")

        if enum.doc:
            lines.append(f'"""{enum.doc}"""')

        # Simple enum (non-generic)
        if not enum.generic_params:
            lines.append(f"class {enum.name}(str, Enum):")

            if not enum.variants:
                lines.append("    pass")
            else:
                for variant in enum.variants:
                    if variant.value is not None:
                        if isinstance(variant.value, str):
                            lines.append(f'    {variant.name} = "{variant.value}"')
                        else:
                            lines.append(f"    {variant.name} = {variant.value}")
                    else:
                        lines.append(f'    {variant.name} = "{variant.name}"')

            return "\n".join(lines)

        # Generic enum (like Option<T>) - more complex
        # For now, skip - would need union types or custom implementation
        lines.append(f"# Generic enum {enum.name} - implement as needed")
        lines.append("# Consider using Union types or custom Pydantic validators")
        return "\n".join(lines)


# ============================================================================
# Public API
# ============================================================================


def generate_pydantic(module: IRModule) -> str:
    """
    Generate Pydantic models from IR module.

    Args:
        module: IR module to convert

    Returns:
        Python code with Pydantic BaseModel classes
    """
    generator = PydanticGenerator(mode="pydantic")
    return generator.generate(module)


def generate_typeddict(module: IRModule) -> str:
    """
    Generate TypedDict classes from IR module for LangGraph.

    Args:
        module: IR module to convert

    Returns:
        Python code with TypedDict classes
    """
    lines = []

    # Imports for TypedDict
    lines.append("from __future__ import annotations")
    lines.append("")
    lines.append("from typing import TypedDict, Optional, List, Dict, Any")
    lines.append("")

    # Module docstring
    if module.metadata.get("doc"):
        lines.append(f'"""{module.metadata["doc"]}"""')
        lines.append("")

    # Helper for type hints (reuse from PydanticGenerator)
    gen = PydanticGenerator(mode="typeddict")

    # Generate TypedDict from type definitions
    for type_def in module.types:
        if type_def.doc:
            lines.append(f'"""{type_def.doc}"""')

        lines.append(f"class {type_def.name}(TypedDict):")

        if type_def.generic_params:
            lines.append("    # Generic type - implement as needed")
            lines.append("    pass")
        elif not type_def.fields:
            lines.append("    pass")
        else:
            for field in type_def.fields:
                field_type = gen.generate_type_hint(field.field_type)
                lines.append(f"    {field.name}: {field_type}")

        lines.append("")
        lines.append("")

    # Generate TypedDict from classes
    for cls in module.classes:
        if cls.doc:
            lines.append(f'"""{cls.doc}"""')

        lines.append(f"class {cls.name}(TypedDict):")

        if not cls.properties:
            lines.append("    pass")
        else:
            for prop in cls.properties:
                if prop and hasattr(prop, 'prop_type') and hasattr(prop, 'name'):
                    field_type = gen.generate_type_hint(prop.prop_type)
                    lines.append(f"    {prop.name}: {field_type}")

        lines.append("")
        lines.append("")

    # Clean up excessive blank lines
    result = "\n".join(lines)
    while "\n\n\n\n" in result:
        result = result.replace("\n\n\n\n", "\n\n\n")

    return result.rstrip() + "\n"
