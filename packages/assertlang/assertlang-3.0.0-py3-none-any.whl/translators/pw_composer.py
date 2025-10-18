#!/usr/bin/env python3
"""
PW MCP Composer - Build PW code via MCP tool calls

This is the CORRECT way to create PW code - by composing MCP tool calls,
NOT by parsing raw language code.

Agents speak PW natively by calling these composition functions.
"""

import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


# ============================================================================
# PW MCP Composition Helpers
# ============================================================================

def pw_literal(value: Any, literal_type: str) -> Dict:
    """Create a PW literal value."""
    return {
        "tool": "pw_literal",
        "params": {
            "value": value,
            "literal_type": literal_type
        }
    }


def pw_identifier(name: str) -> Dict:
    """Create a PW identifier (variable reference)."""
    return {
        "tool": "pw_identifier",
        "params": {"name": name}
    }


def pw_binary_op(op: str, left: Dict, right: Dict) -> Dict:
    """Create a PW binary operation."""
    return {
        "tool": "pw_binary_op",
        "params": {
            "op": op,
            "left": left,
            "right": right
        }
    }


def pw_call(function: str, args: List[Dict], kwargs: Optional[Dict] = None) -> Dict:
    """Create a PW function call."""
    return {
        "tool": "pw_call",
        "params": {
            "function": function,
            "args": args,
            "kwargs": kwargs or {}
        }
    }


def pw_assignment(target: str, value: Dict, var_type: Optional[Dict] = None) -> Dict:
    """Create a PW assignment statement."""
    return {
        "tool": "pw_assignment",
        "params": {
            "target": target,
            "value": value,
            "var_type": var_type
        }
    }


def pw_return(value: Dict) -> Dict:
    """Create a PW return statement."""
    return {
        "tool": "pw_return",
        "params": {"value": value}
    }


def pw_if(condition: Dict, then_body: List[Dict], else_body: Optional[List[Dict]] = None) -> Dict:
    """Create a PW if statement."""
    return {
        "tool": "pw_if",
        "params": {
            "condition": condition,
            "then_body": then_body,
            "else_body": else_body
        }
    }


def pw_for(iterator: str, iterable: Dict, body: List[Dict]) -> Dict:
    """Create a PW for loop."""
    return {
        "tool": "pw_for",
        "params": {
            "iterator": iterator,
            "iterable": iterable,
            "body": body
        }
    }


def pw_while(condition: Dict, body: List[Dict]) -> Dict:
    """Create a PW while loop."""
    return {
        "tool": "pw_while",
        "params": {
            "condition": condition,
            "body": body
        }
    }


def pw_parameter(name: str, param_type: Optional[Dict] = None, default: Optional[Dict] = None) -> Dict:
    """Create a PW function parameter."""
    return {
        "tool": "pw_parameter",
        "params": {
            "name": name,
            "param_type": param_type,
            "default": default
        }
    }


def pw_type(name: str, generic_args: Optional[List[Dict]] = None) -> Dict:
    """Create a PW type reference."""
    return {
        "tool": "pw_type",
        "params": {
            "name": name,
            "generic_args": generic_args or []
        }
    }


def pw_function(name: str, params: List[Dict], body: List[Dict],
                return_type: Optional[Dict] = None,
                throws: Optional[List[str]] = None,
                is_async: bool = False) -> Dict:
    """Create a PW function definition."""
    return {
        "tool": "pw_function",
        "params": {
            "name": name,
            "params": params,
            "body": body,
            "return_type": return_type,
            "throws": throws or [],
            "is_async": is_async
        }
    }


def pw_module(name: str,
              functions: Optional[List[Dict]] = None,
              classes: Optional[List[Dict]] = None,
              imports: Optional[List[Dict]] = None,
              version: str = "1.0.0") -> Dict:
    """Create a PW module."""
    return {
        "tool": "pw_module",
        "params": {
            "name": name,
            "version": version,
            "imports": imports or [],
            "functions": functions or [],
            "classes": classes or [],
            "types": [],
            "enums": [],
            "module_vars": []
        }
    }


def pw_import(module: str, alias: Optional[str] = None, items: Optional[List[str]] = None) -> Dict:
    """Create a PW import statement."""
    return {
        "tool": "pw_import",
        "params": {
            "module": module,
            "alias": alias,
            "items": items
        }
    }


# ============================================================================
# Example: Compose PW Code Programmatically
# ============================================================================

def compose_add_function() -> Dict:
    """
    Compose a simple add function in PW.

    Equivalent to:
        function add(x: int, y: int) -> int:
            return x + y
    """
    return pw_function(
        name="add",
        params=[
            pw_parameter("x", pw_type("int")),
            pw_parameter("y", pw_type("int"))
        ],
        return_type=pw_type("int"),
        body=[
            pw_return(
                pw_binary_op(
                    "+",
                    pw_identifier("x"),
                    pw_identifier("y")
                )
            )
        ]
    )


def compose_greet_function() -> Dict:
    """
    Compose a greeting function in PW.

    Equivalent to:
        function greet(name: string) -> string:
            message = "Hello, " + name
            return message
    """
    return pw_function(
        name="greet",
        params=[
            pw_parameter("name", pw_type("string"))
        ],
        return_type=pw_type("string"),
        body=[
            pw_assignment(
                "message",
                pw_binary_op(
                    "+",
                    pw_literal("Hello, ", "string"),
                    pw_identifier("name")
                ),
                pw_type("string")
            ),
            pw_return(pw_identifier("message"))
        ]
    )


def compose_classify_number() -> Dict:
    """
    Compose a function with conditional logic.

    Equivalent to:
        function classify_number(n: int) -> string:
            if n > 0:
                return "positive"
            else:
                return "negative"
    """
    return pw_function(
        name="classify_number",
        params=[
            pw_parameter("n", pw_type("int"))
        ],
        return_type=pw_type("string"),
        body=[
            pw_if(
                condition=pw_binary_op(
                    ">",
                    pw_identifier("n"),
                    pw_literal(0, "integer")
                ),
                then_body=[
                    pw_return(pw_literal("positive", "string"))
                ],
                else_body=[
                    pw_return(pw_literal("negative", "string"))
                ]
            )
        ]
    )


def compose_sum_list() -> Dict:
    """
    Compose a function with a loop.

    Equivalent to:
        function sum_list(numbers: array<int>) -> int:
            total = 0
            for num in numbers:
                total = total + num
            return total
    """
    return pw_function(
        name="sum_list",
        params=[
            pw_parameter("numbers", pw_type("array", [pw_type("int")]))
        ],
        return_type=pw_type("int"),
        body=[
            pw_assignment(
                "total",
                pw_literal(0, "integer"),
                pw_type("int")
            ),
            pw_for(
                iterator="num",
                iterable=pw_identifier("numbers"),
                body=[
                    pw_assignment(
                        "total",
                        pw_binary_op(
                            "+",
                            pw_identifier("total"),
                            pw_identifier("num")
                        )
                    )
                ]
            ),
            pw_return(pw_identifier("total"))
        ]
    )


def compose_calculator_module() -> Dict:
    """
    Compose a complete PW module with multiple functions.

    This is what agents would create and share!
    """
    return pw_module(
        name="calculator",
        version="1.0.0",
        functions=[
            compose_add_function(),
            compose_greet_function(),
            compose_classify_number(),
            compose_sum_list()
        ]
    )


# ============================================================================
# Test
# ============================================================================

if __name__ == "__main__":
    import json

    print("=" * 70)
    print("PW MCP Composer - Building PW Code Programmatically")
    print("=" * 70)

    # Compose a simple function
    print("\n1. Simple Add Function:")
    add_func = compose_add_function()
    print(json.dumps(add_func, indent=2)[:300] + "...")

    # Compose a function with assignment
    print("\n2. Greet Function (with assignment):")
    greet_func = compose_greet_function()
    print(json.dumps(greet_func, indent=2)[:300] + "...")

    # Compose a function with conditional
    print("\n3. Classify Number (with if/else):")
    classify_func = compose_classify_number()
    print(json.dumps(classify_func, indent=2)[:300] + "...")

    # Compose a complete module
    print("\n4. Complete Calculator Module:")
    module = compose_calculator_module()
    print(f"Module: {module['params']['name']}")
    print(f"Functions: {len(module['params']['functions'])}")
    print("  - add")
    print("  - greet")
    print("  - classify_number")
    print("  - sum_list")

    print("\n" + "=" * 70)
    print("✅ PW MCP Composition Working!")
    print("=" * 70)
    print("\nAgents can now compose PW code by calling these functions,")
    print("without ever writing raw Python/Go/Rust code!")
