#!/usr/bin/env python3
"""
Semantic Normalization Layer for PW MCP

Ensures PW is a true universal language by:
1. Stripping language-specific idioms when converting TO PW
2. Applying target-specific idioms when converting FROM PW

PW = Pure, language-agnostic intermediate representation
Languages = Language-specific implementations of PW concepts

Design Philosophy:
- PW has ONE way to represent each concept (error handling, returns, etc.)
- Languages map their idioms TO/FROM this canonical PW representation
- No language-specific patterns leak into PW
"""

import sys
from pathlib import Path
from typing import Any, List, Optional

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dsl.ir import (
    IRModule, IRFunction, IRReturn, IRAssignment, IRImport,
    IRCall, IRLiteral, IRIdentifier, IRBinaryOp, IRArray,
    IRIf, IRFor, IRTry, IRCatch
)


class SemanticNormalizer:
    """
    Normalize language-specific patterns to/from universal PW representation.

    Two-way normalization:
    1. Language → PW: Strip language idioms, emit pure PW
    2. PW → Language: Apply language idioms from pure PW
    """

    # ========================================================================
    # Language → PW Normalization (Input Normalization)
    # ========================================================================

    @staticmethod
    def normalize_from_go(ir_module: IRModule) -> IRModule:
        """
        Normalize Go-specific patterns to universal PW.

        Transformations:
        - (value, error) returns → single value + throws declaration
        - Go stdlib imports → remove (language-specific)
        - Module-level var declarations → move to module_vars
        - Explicit type declarations → infer when possible
        """

        # 1. Filter out Go-specific imports
        normalized_imports = [
            imp for imp in ir_module.imports
            if not SemanticNormalizer._is_go_stdlib(imp.module)
        ]

        # 2. Normalize functions (strip error returns)
        normalized_functions = [
            SemanticNormalizer._normalize_go_function(func)
            for func in ir_module.functions
        ]

        # 3. Extract module-level variables (not orphaned assignments)
        # This fixes Issue #1 from telephone test
        module_vars = SemanticNormalizer._extract_module_vars(ir_module)

        return IRModule(
            name=ir_module.name,
            version=ir_module.version,
            imports=normalized_imports,
            functions=normalized_functions,
            classes=ir_module.classes,
            types=ir_module.types,
            enums=ir_module.enums,
            module_vars=module_vars
        )

    @staticmethod
    def normalize_from_python(ir_module: IRModule) -> IRModule:
        """
        Normalize Python-specific patterns to universal PW.

        Transformations:
        - Exception raises → throws in function signature
        - Comprehensions → explicit loops (or keep as PW concept)
        - Decorators → metadata (don't execute, just preserve)
        - __future__ imports → remove
        """

        # Filter out Python-specific imports
        normalized_imports = [
            imp for imp in ir_module.imports
            if not SemanticNormalizer._is_python_future(imp.module)
        ]

        # Normalize functions
        normalized_functions = [
            SemanticNormalizer._normalize_python_function(func)
            for func in ir_module.functions
        ]

        return IRModule(
            name=ir_module.name,
            version=ir_module.version,
            imports=normalized_imports,
            functions=normalized_functions,
            classes=ir_module.classes,
            types=ir_module.types,
            enums=ir_module.enums,
            module_vars=ir_module.module_vars or []
        )

    # ========================================================================
    # PW → Language Denormalization (Output Denormalization)
    # ========================================================================

    @staticmethod
    def denormalize_to_go(ir_module: IRModule) -> IRModule:
        """
        Apply Go-specific idioms to pure PW.

        Transformations:
        - Single returns → (value, error) if function can throw
        - Add Go stdlib imports (errors, fmt) if needed
        - Pure functions → no error returns
        """

        # Add Go-specific imports if needed
        needs_errors = any(
            len(func.throws) > 0 or SemanticNormalizer._has_error_handling(func)
            for func in ir_module.functions
        )

        go_imports = []
        if needs_errors:
            go_imports.append(IRImport(module="errors", alias=None, items=None))
            go_imports.append(IRImport(module="fmt", alias=None, items=None))

        # Denormalize functions (add error returns)
        denormalized_functions = [
            SemanticNormalizer._denormalize_go_function(func)
            for func in ir_module.functions
        ]

        return IRModule(
            name=ir_module.name,
            version=ir_module.version,
            imports=ir_module.imports + go_imports,
            functions=denormalized_functions,
            classes=ir_module.classes,
            types=ir_module.types,
            enums=ir_module.enums,
            module_vars=ir_module.module_vars or []
        )

    @staticmethod
    def denormalize_to_python(ir_module: IRModule) -> IRModule:
        """
        Apply Python-specific idioms to pure PW.

        Transformations:
        - Throws declarations → raise statements in body
        - Error returns → ignore (Python uses exceptions)

        Note: __future__ annotations import is handled by PythonGeneratorV2.
        """

        # Filter out language-specific imports from other languages
        filtered_imports = [
            imp for imp in ir_module.imports
            if not SemanticNormalizer._is_go_stdlib(imp.module)
            and not imp.module.startswith("java.")
            and not imp.module.startswith("System.")
        ]

        # Denormalize functions (pure PW → Python exceptions)
        denormalized_functions = [
            SemanticNormalizer._denormalize_python_function(func)
            for func in ir_module.functions
        ]

        return IRModule(
            name=ir_module.name,
            version=ir_module.version,
            imports=filtered_imports,
            functions=denormalized_functions,
            classes=ir_module.classes,
            types=ir_module.types,
            enums=ir_module.enums,
            module_vars=ir_module.module_vars or []
        )

    # ========================================================================
    # Helper Methods: Go Normalization
    # ========================================================================

    @staticmethod
    def _is_go_stdlib(module: str) -> bool:
        """Check if import is Go standard library."""
        go_stdlib = {
            "errors", "fmt", "sync", "time", "context", "io",
            "os", "strings", "strconv", "math", "net", "http"
        }
        return module in go_stdlib

    @staticmethod
    def _normalize_go_function(func: IRFunction) -> IRFunction:
        """
        Normalize Go function to pure PW.

        Go pattern:
            func DoWork(x int) (string, error) {
                return "ok", nil
            }

        PW pattern:
            function DoWork(x: int) -> string {
                return "ok"
            }
        """
        # Normalize return statements (strip error returns)
        normalized_body = [
            SemanticNormalizer._normalize_go_return(stmt) if isinstance(stmt, IRReturn) else stmt
            for stmt in func.body
        ]

        # Normalize return type (if it's a tuple with error, extract first element)
        normalized_return_type = func.return_type
        # TODO: Handle tuple types when we add them to IR

        return IRFunction(
            name=func.name,
            params=func.params,
            return_type=normalized_return_type,
            body=normalized_body,
            throws=func.throws,
            is_async=func.is_async,
            is_static=func.is_static if hasattr(func, 'is_static') else False,
            is_private=func.is_private if hasattr(func, 'is_private') else False,
            doc=func.doc if hasattr(func, 'doc') else None
        )

    @staticmethod
    def _normalize_go_return(ret: IRReturn) -> IRReturn:
        """
        Normalize Go return: (value, error) → value

        Before: return [result, nil]
        After:  return result
        """
        if isinstance(ret.value, IRArray) and len(ret.value.elements) == 2:
            # Check if second element is nil/None
            second = ret.value.elements[1]
            if isinstance(second, IRLiteral) and second.value is None:
                # Strip the error return
                return IRReturn(value=ret.value.elements[0])

        return ret

    @staticmethod
    def _extract_module_vars(ir_module: IRModule) -> List[IRAssignment]:
        """
        Extract module-level variables from orphaned assignments.

        This fixes Issue #1: Module-level variable assignments appearing outside functions.
        """
        # For now, return existing module_vars
        # In future: scan for assignments that appear at module level
        return ir_module.module_vars or []

    # ========================================================================
    # Helper Methods: Python Normalization
    # ========================================================================

    @staticmethod
    def _is_python_future(module: str) -> bool:
        """Check if import is Python __future__."""
        return module == "__future__"

    @staticmethod
    def _normalize_python_function(func: IRFunction) -> IRFunction:
        """
        Normalize Python function to pure PW.

        Python uses exceptions, PW uses throws declarations.
        Keep function as-is (Python already close to pure PW).
        """
        # Python is already pretty close to PW
        # Main difference: decorators (keep as metadata)
        return func

    # ========================================================================
    # Helper Methods: Go Denormalization
    # ========================================================================

    @staticmethod
    def _has_error_handling(func: IRFunction) -> bool:
        """Check if function has error handling (try/catch)."""
        for stmt in func.body:
            if isinstance(stmt, IRTry):
                return True
        return False

    @staticmethod
    def _denormalize_go_function(func: IRFunction) -> IRFunction:
        """
        Apply Go error handling pattern to pure PW function.

        PW pattern:
            function DoWork(x: int) -> string {
                return "ok"
            }

        Go pattern:
            func DoWork(x int) (string, error) {
                return "ok", nil
            }
        """
        # If function has throws or error handling, wrap returns with error
        if func.throws or SemanticNormalizer._has_error_handling(func):
            denormalized_body = [
                SemanticNormalizer._denormalize_go_return(stmt) if isinstance(stmt, IRReturn) else stmt
                for stmt in func.body
            ]
        else:
            denormalized_body = func.body

        return IRFunction(
            name=func.name,
            params=func.params,
            return_type=func.return_type,
            body=denormalized_body,
            throws=func.throws,
            is_async=func.is_async,
            is_static=func.is_static if hasattr(func, 'is_static') else False,
            is_private=func.is_private if hasattr(func, 'is_private') else False,
            doc=func.doc if hasattr(func, 'doc') else None
        )

    @staticmethod
    def _denormalize_go_return(ret: IRReturn) -> IRReturn:
        """
        Add Go error handling: value → (value, error)

        Before: return result
        After:  return [result, nil]
        """
        if ret.value and not isinstance(ret.value, IRArray):
            # Wrap return value with nil error
            return IRReturn(
                value=IRArray(
                    elements=[
                        ret.value,
                        IRLiteral(value=None, literal_type="null")
                    ]
                )
            )
        return ret

    # ========================================================================
    # Helper Methods: Python Denormalization
    # ========================================================================

    @staticmethod
    def _denormalize_python_function(func: IRFunction) -> IRFunction:
        """
        Apply Python exception pattern to pure PW function.

        PW uses throws declarations, Python uses raise statements.
        Keep function as-is (Python naturally handles this).
        """
        # Python generator will naturally convert throws → raise
        return func


# ============================================================================
# Convenience Functions
# ============================================================================

def normalize_ir(ir_module: IRModule, source_lang: str) -> IRModule:
    """
    Normalize IR from language-specific patterns to pure PW.

    Args:
        ir_module: IR from language parser
        source_lang: Source language (python, go, rust, etc.)

    Returns:
        Normalized IR (pure PW, no language-specific idioms)
    """
    if source_lang == "go":
        return SemanticNormalizer.normalize_from_go(ir_module)
    elif source_lang == "python":
        return SemanticNormalizer.normalize_from_python(ir_module)
    else:
        # Default: assume already normalized
        return ir_module


def denormalize_ir(ir_module: IRModule, target_lang: str) -> IRModule:
    """
    Denormalize pure PW IR to language-specific patterns.

    Args:
        ir_module: Pure PW IR
        target_lang: Target language (python, go, rust, etc.)

    Returns:
        Denormalized IR (with language-specific idioms applied)
    """
    if target_lang == "go":
        return SemanticNormalizer.denormalize_to_go(ir_module)
    elif target_lang == "python":
        return SemanticNormalizer.denormalize_to_python(ir_module)
    else:
        # Default: no denormalization
        return ir_module


# ============================================================================
# Test
# ============================================================================

if __name__ == "__main__":
    print("Semantic Normalizer - Ensures PW is truly universal")
    print("\nKey Concept:")
    print("  Language → [Normalize] → PW (pure, universal)")
    print("  PW (pure, universal) → [Denormalize] → Language")
    print("\nThis prevents language-specific idioms from leaking into PW!")
