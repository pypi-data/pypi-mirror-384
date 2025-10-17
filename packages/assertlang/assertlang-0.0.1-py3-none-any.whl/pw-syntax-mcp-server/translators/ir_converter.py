#!/usr/bin/env python3
"""
IR ⟷ MCP Tree Converter

Converts between Promptware IR (Python dataclasses) and MCP trees (JSON-serializable dicts).
This allows IR nodes to be sent as MCP tool parameters and returned as MCP tool results.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dsl.ir import (
    IRModule, IRFunction, IRParameter, IRClass, IRProperty,
    IRStatement, IRExpression, IRAssignment, IRReturn, IRThrow, IRIf, IRFor, IRForCStyle, IRWhile,
    IRTry, IRCatch, IRBreak, IRContinue, IRCall, IRBinaryOp, IRUnaryOp, IRLiteral, IRIdentifier,
    IRPropertyAccess, IRIndex, IRLambda, IRArray, IRMap, IRTernary,
    IRType, IRImport, IRTypeDefinition, IREnum, IREnumVariant,
    BinaryOperator, UnaryOperator, LiteralType,
)


def ir_to_mcp(node: Any) -> Dict[str, Any]:
    """
    Convert IR node to MCP tree (JSON-serializable dict).

    Args:
        node: Any IR node (IRModule, IRFunction, IRExpression, etc.)

    Returns:
        Dict representing the node as MCP tool call
    """
    if node is None:
        return None

    # Module
    if isinstance(node, IRModule):
        return {
            "tool": "pw_module",
            "params": {
                "name": node.name,
                "version": node.version,
                "imports": [ir_to_mcp(imp) for imp in node.imports],
                "functions": [ir_to_mcp(func) for func in node.functions],
                "classes": [ir_to_mcp(cls) for cls in node.classes],
                "types": [ir_to_mcp(t) for t in node.types],
                "enums": [ir_to_mcp(e) for e in node.enums],
                "module_vars": [ir_to_mcp(v) for v in node.module_vars],
            }
        }

    # Import
    elif isinstance(node, IRImport):
        return {
            "tool": "pw_import",
            "params": {
                "module": node.module,
                "alias": node.alias,
                "items": node.items,
            }
        }

    # Function
    elif isinstance(node, IRFunction):
        return {
            "tool": "pw_function",
            "params": {
                "name": node.name,
                "params": [ir_to_mcp(p) for p in node.params],
                "return_type": ir_to_mcp(node.return_type) if node.return_type else None,
                "body": [ir_to_mcp(stmt) for stmt in node.body],
                "is_async": node.is_async,
                "is_static": node.is_static if hasattr(node, 'is_static') else False,
                "is_private": node.is_private if hasattr(node, 'is_private') else False,
                "throws": node.throws or [],
                "doc": node.doc if hasattr(node, 'doc') else None,
            }
        }

    # Parameter
    elif isinstance(node, IRParameter):
        return {
            "tool": "pw_parameter",
            "params": {
                "name": node.name,
                "param_type": ir_to_mcp(node.param_type) if node.param_type else None,
                "default_value": ir_to_mcp(node.default_value) if node.default_value else None,
                "is_variadic": node.is_variadic,
            }
        }

    # Class
    elif isinstance(node, IRClass):
        return {
            "tool": "pw_class",
            "params": {
                "name": node.name,
                "base_classes": node.base_classes or [],
                "properties": [ir_to_mcp(p) for p in node.properties],
                "methods": [ir_to_mcp(m) for m in node.methods],
                "constructor": ir_to_mcp(node.constructor) if node.constructor else None,
            }
        }

    # Property
    elif isinstance(node, IRProperty):
        return {
            "tool": "pw_property",
            "params": {
                "name": node.name,
                "prop_type": ir_to_mcp(node.prop_type),
                "default_value": ir_to_mcp(node.default_value) if node.default_value else None,
            }
        }

    # Statements
    elif isinstance(node, IRAssignment):
        return {
            "tool": "pw_assignment",
            "params": {
                "target": node.target if isinstance(node.target, str) else ir_to_mcp(node.target),
                "value": ir_to_mcp(node.value),
                "var_type": ir_to_mcp(node.var_type) if node.var_type else None,
                "is_declaration": node.is_declaration,
            }
        }

    elif isinstance(node, IRReturn):
        return {
            "tool": "pw_return",
            "params": {
                "value": ir_to_mcp(node.value) if node.value else None,
            }
        }

    elif isinstance(node, IRThrow):
        return {
            "tool": "pw_throw",
            "params": {
                "exception": ir_to_mcp(node.exception),
            }
        }

    elif isinstance(node, IRBreak):
        return {
            "tool": "pw_break",
            "params": {}
        }

    elif isinstance(node, IRContinue):
        return {
            "tool": "pw_continue",
            "params": {}
        }

    elif isinstance(node, IRIf):
        return {
            "tool": "pw_if",
            "params": {
                "condition": ir_to_mcp(node.condition),
                "then_body": [ir_to_mcp(stmt) for stmt in node.then_body],
                "else_body": [ir_to_mcp(stmt) for stmt in node.else_body] if node.else_body else None,
            }
        }

    elif isinstance(node, IRForCStyle):
        return {
            "tool": "pw_for_c_style",
            "params": {
                "init": ir_to_mcp(node.init),
                "condition": ir_to_mcp(node.condition),
                "increment": ir_to_mcp(node.increment),
                "body": [ir_to_mcp(stmt) for stmt in node.body],
            }
        }

    elif isinstance(node, IRFor):
        return {
            "tool": "pw_for",
            "params": {
                "iterator": node.iterator,
                "iterable": ir_to_mcp(node.iterable),
                "body": [ir_to_mcp(stmt) for stmt in node.body],
            }
        }

    elif isinstance(node, IRWhile):
        return {
            "tool": "pw_while",
            "params": {
                "condition": ir_to_mcp(node.condition),
                "body": [ir_to_mcp(stmt) for stmt in node.body],
            }
        }

    elif isinstance(node, IRTry):
        return {
            "tool": "pw_try",
            "params": {
                "body": [ir_to_mcp(stmt) for stmt in node.try_body],
                "catch_clauses": [ir_to_mcp(c) for c in node.catch_blocks],
                "finally_body": [ir_to_mcp(stmt) for stmt in node.finally_body] if node.finally_body else None,
            }
        }

    elif isinstance(node, IRCatch):
        return {
            "tool": "pw_catch",
            "params": {
                "exception_type": node.exception_type,
                "variable": node.exception_var,
                "body": [ir_to_mcp(stmt) for stmt in node.body],
            }
        }

    # Expressions
    elif isinstance(node, IRCall):
        return {
            "tool": "pw_call",
            "params": {
                "function": ir_to_mcp(node.function),
                "args": [ir_to_mcp(arg) for arg in node.args],
                "kwargs": {k: ir_to_mcp(v) for k, v in node.kwargs.items()} if node.kwargs else {},
            }
        }

    elif isinstance(node, IRBinaryOp):
        return {
            "tool": "pw_binary_op",
            "params": {
                "op": node.op.value if hasattr(node.op, 'value') else node.op,
                "left": ir_to_mcp(node.left),
                "right": ir_to_mcp(node.right),
            }
        }

    elif isinstance(node, IRUnaryOp):
        return {
            "tool": "pw_unary_op",
            "params": {
                "op": node.op.value if hasattr(node.op, 'value') else node.op,
                "operand": ir_to_mcp(node.operand),
            }
        }

    elif isinstance(node, IRLiteral):
        return {
            "tool": "pw_literal",
            "params": {
                "value": node.value,
                "literal_type": node.literal_type.value if hasattr(node.literal_type, 'value') else node.literal_type,
            }
        }

    elif isinstance(node, IRIdentifier):
        return {
            "tool": "pw_identifier",
            "params": {
                "name": node.name,
            }
        }

    elif isinstance(node, IRPropertyAccess):
        return {
            "tool": "pw_property_access",
            "params": {
                "object": ir_to_mcp(node.object),
                "property": node.property,
            }
        }

    elif isinstance(node, IRIndex):
        return {
            "tool": "pw_index",
            "params": {
                "object": ir_to_mcp(node.object),
                "index": ir_to_mcp(node.index),
            }
        }

    elif isinstance(node, IRLambda):
        return {
            "tool": "pw_lambda",
            "params": {
                "params": [ir_to_mcp(p) for p in node.params],
                "body": ir_to_mcp(node.body) if not isinstance(node.body, list) else [ir_to_mcp(s) for s in node.body],
                "return_type": ir_to_mcp(node.return_type) if node.return_type else None,
            }
        }

    elif isinstance(node, IRArray):
        return {
            "tool": "pw_array",
            "params": {
                "elements": [ir_to_mcp(elem) for elem in node.elements],
                "element_type": ir_to_mcp(node.element_type) if hasattr(node, 'element_type') and node.element_type else None,
            }
        }

    elif isinstance(node, IRMap):
        return {
            "tool": "pw_map",
            "params": {
                "entries": {str(k): ir_to_mcp(v) for k, v in node.entries.items()},
                "key_type": ir_to_mcp(node.key_type) if hasattr(node, 'key_type') and node.key_type else None,
                "value_type": ir_to_mcp(node.value_type) if hasattr(node, 'value_type') and node.value_type else None,
            }
        }

    elif isinstance(node, IRTernary):
        return {
            "tool": "pw_ternary",
            "params": {
                "condition": ir_to_mcp(node.condition),
                "true_value": ir_to_mcp(node.true_value),
                "false_value": ir_to_mcp(node.false_value),
            }
        }

    # Types
    elif isinstance(node, IRType):
        return {
            "tool": "pw_type",
            "params": {
                "name": node.name,
                "generic_args": [ir_to_mcp(arg) for arg in node.generic_args] if node.generic_args else [],
                "is_optional": node.is_optional,
            }
        }

    elif isinstance(node, IRTypeDefinition):
        return {
            "tool": "pw_type_definition",
            "params": {
                "name": node.name,
                "fields": [{"name": f.name, "type": ir_to_mcp(f.field_type)} for f in node.fields],
            }
        }

    elif isinstance(node, IREnum):
        return {
            "tool": "pw_enum",
            "params": {
                "name": node.name,
                "variants": [ir_to_mcp(v) for v in node.variants],
            }
        }

    elif isinstance(node, IREnumVariant):
        return {
            "tool": "pw_enum_variant",
            "params": {
                "name": node.name,
                "value": node.value,
            }
        }

    else:
        # Fallback for unknown types
        return {"tool": "unknown", "params": {"type": str(type(node)), "value": str(node)}}


def mcp_to_ir(mcp_tree: Dict[str, Any]) -> Any:
    """
    Convert MCP tree (JSON dict) back to IR node.

    Args:
        mcp_tree: Dict with "tool" and "params" keys

    Returns:
        Corresponding IR node instance
    """
    if not mcp_tree or not isinstance(mcp_tree, dict):
        return None

    tool = mcp_tree.get("tool")
    params = mcp_tree.get("params", {})

    # Module
    if tool == "pw_module":
        return IRModule(
            name=params["name"],
            version=params.get("version", "1.0.0"),
            imports=[mcp_to_ir(imp) for imp in params.get("imports", [])],
            functions=[mcp_to_ir(func) for func in params.get("functions", [])],
            classes=[mcp_to_ir(cls) for cls in params.get("classes", [])],
            types=[mcp_to_ir(t) for t in params.get("types", [])],
            enums=[mcp_to_ir(e) for e in params.get("enums", [])],
            module_vars=[mcp_to_ir(v) for v in params.get("module_vars", [])],
        )

    # Import
    elif tool == "pw_import":
        return IRImport(
            module=params["module"],
            alias=params.get("alias"),
            items=params.get("items"),
        )

    # Function
    elif tool == "pw_function":
        return IRFunction(
            name=params["name"],
            params=[mcp_to_ir(p) for p in params.get("params", [])],
            return_type=mcp_to_ir(params["return_type"]) if params.get("return_type") else None,
            body=[mcp_to_ir(stmt) for stmt in params.get("body", [])],
            is_async=params.get("is_async", False),
            is_static=params.get("is_static", False),
            is_private=params.get("is_private", False),
            throws=params.get("throws", []),
            doc=params.get("doc"),
        )

    # Parameter
    elif tool == "pw_parameter":
        return IRParameter(
            name=params["name"],
            param_type=mcp_to_ir(params["param_type"]) if params.get("param_type") else None,
            default_value=mcp_to_ir(params["default_value"]) if params.get("default_value") else None,
            is_variadic=params.get("is_variadic", False),
        )

    # Class
    elif tool == "pw_class":
        return IRClass(
            name=params["name"],
            base_classes=params.get("base_classes", []),
            properties=[mcp_to_ir(prop) for prop in params.get("properties", [])],
            methods=[mcp_to_ir(method) for method in params.get("methods", [])],
            constructor=mcp_to_ir(params["constructor"]) if params.get("constructor") else None,
        )

    # Property
    elif tool == "pw_property":
        return IRProperty(
            name=params["name"],
            prop_type=mcp_to_ir(params["prop_type"]) if params.get("prop_type") else None,
            default_value=mcp_to_ir(params["default_value"]) if params.get("default_value") else None,
        )

    # Statements
    elif tool == "pw_assignment":
        return IRAssignment(
            target=params["target"] if isinstance(params["target"], str) else mcp_to_ir(params["target"]),
            value=mcp_to_ir(params["value"]),
            var_type=mcp_to_ir(params["var_type"]) if params.get("var_type") else None,
            is_declaration=params.get("is_declaration", True),
        )

    elif tool == "pw_return":
        return IRReturn(
            value=mcp_to_ir(params["value"]) if params.get("value") else None,
        )

    elif tool == "pw_if":
        return IRIf(
            condition=mcp_to_ir(params["condition"]),
            then_body=[mcp_to_ir(stmt) for stmt in params.get("then_body", [])],
            else_body=[mcp_to_ir(stmt) for stmt in params.get("else_body", [])] if params.get("else_body") else None,
        )

    elif tool == "pw_for_c_style":
        return IRForCStyle(
            init=mcp_to_ir(params["init"]),
            condition=mcp_to_ir(params["condition"]),
            increment=mcp_to_ir(params["increment"]),
            body=[mcp_to_ir(stmt) for stmt in params.get("body", [])],
        )

    elif tool == "pw_for":
        return IRFor(
            iterator=params["iterator"],
            iterable=mcp_to_ir(params["iterable"]),
            body=[mcp_to_ir(stmt) for stmt in params.get("body", [])],
        )

    elif tool == "pw_while":
        return IRWhile(
            condition=mcp_to_ir(params["condition"]),
            body=[mcp_to_ir(stmt) for stmt in params.get("body", [])],
        )

    elif tool == "pw_try":
        return IRTry(
            try_body=[mcp_to_ir(stmt) for stmt in params.get("body", [])],
            catch_blocks=[mcp_to_ir(c) for c in params.get("catch_clauses", [])],
            finally_body=[mcp_to_ir(stmt) for stmt in params.get("finally_body", [])] if params.get("finally_body") else [],
        )

    elif tool == "pw_catch":
        return IRCatch(
            exception_type=params.get("exception_type"),
            exception_var=params.get("variable"),
            body=[mcp_to_ir(stmt) for stmt in params.get("body", [])],
        )

    elif tool == "pw_throw":
        return IRThrow(
            exception=mcp_to_ir(params["exception"]),
        )

    elif tool == "pw_break":
        return IRBreak()

    elif tool == "pw_continue":
        return IRContinue()

    # Expressions
    elif tool == "pw_call":
        return IRCall(
            function=mcp_to_ir(params["function"]),
            args=[mcp_to_ir(arg) for arg in params.get("args", [])],
            kwargs={k: mcp_to_ir(v) for k, v in params.get("kwargs", {}).items()},
        )

    elif tool == "pw_binary_op":
        return IRBinaryOp(
            op=BinaryOperator(params["op"]),
            left=mcp_to_ir(params["left"]),
            right=mcp_to_ir(params["right"]),
        )

    elif tool == "pw_unary_op":
        return IRUnaryOp(
            op=UnaryOperator(params["op"]),
            operand=mcp_to_ir(params["operand"]),
        )

    elif tool == "pw_literal":
        # Handle literal_type - if it's uppercase, convert to lowercase for enum
        lit_type = params["literal_type"]
        if isinstance(lit_type, str):
            lit_type = lit_type.lower()
        return IRLiteral(
            value=params["value"],
            literal_type=LiteralType(lit_type),
        )

    elif tool == "pw_identifier":
        return IRIdentifier(name=params["name"])

    elif tool == "pw_property_access":
        return IRPropertyAccess(
            object=mcp_to_ir(params["object"]),
            property=params["property"],
        )

    elif tool == "pw_index":
        return IRIndex(
            object=mcp_to_ir(params["object"]),
            index=mcp_to_ir(params["index"]),
        )

    elif tool == "pw_array":
        return IRArray(elements=[mcp_to_ir(elem) for elem in params.get("elements", [])])

    elif tool == "pw_map":
        return IRMap(entries={k: mcp_to_ir(v) for k, v in params.get("entries", {}).items()})

    elif tool == "pw_ternary":
        return IRTernary(
            condition=mcp_to_ir(params["condition"]),
            true_value=mcp_to_ir(params["true_value"]),
            false_value=mcp_to_ir(params["false_value"]),
        )

    # Types
    elif tool == "pw_type":
        return IRType(
            name=params["name"],
            generic_args=[mcp_to_ir(arg) for arg in params.get("generic_args", [])],
            is_optional=params.get("is_optional", False),
        )

    else:
        return None


# Test if run directly
if __name__ == "__main__":
    # Test roundtrip
    test_ir = IRFunction(
        name="test",
        params=[IRParameter(name="x", param_type=IRType(name="int"))],
        return_type=IRType(name="int"),
        body=[
            IRReturn(value=IRBinaryOp(
                op=BinaryOperator.MULTIPLY,
                left=IRIdentifier(name="x"),
                right=IRLiteral(value=2, literal_type=LiteralType.INTEGER)
            ))
        ],
        is_async=False,
        decorators=[],
        throws=[],
    )

    # Convert to MCP
    mcp_tree = ir_to_mcp(test_ir)
    print("MCP Tree:")
    import json
    print(json.dumps(mcp_tree, indent=2))

    # Convert back to IR
    ir_restored = mcp_to_ir(mcp_tree)
    print("\nRestored IR:")
    print(ir_restored)

    print("\n✅ Roundtrip successful!")
