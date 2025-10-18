"""
TypeScript Parser V3: Official TypeScript Compiler API → IR

Architecture:
1. Run typescript_ast_parser.js (TypeScript → JSON AST)
2. Parse JSON AST → IR nodes
3. Convert TypeScript types to universal IR types

Similar to go_parser_v3.py and rust_parser_v3.py
"""

import json
import subprocess
import os
from pathlib import Path
from typing import Dict, Any, List, Optional

from dsl.ir import (
    IRModule, IRClass, IRFunction, IRParameter, IRType, IRProperty,
    IRAssignment, IRIf, IRFor, IRWhile, IRSwitch, IRCase, IRTry, IRCatch, IRReturn, IRThrow,
    IRBreak, IRContinue,
    IRBinaryOp, IRIdentifier, IRLiteral, IRCall, IRArray, IRMap, IRLambda,
    LiteralType, BinaryOperator
)


class TypeScriptParserV3:
    """Parse TypeScript code using official TypeScript compiler API."""

    def __init__(self):
        self.parser_path = Path(__file__).parent / "typescript_ast_parser.js"
        self.type_mapping = {
            "number": "float",
            "string": "string",
            "boolean": "bool",
            "void": "void",
            "any": "any",
            "null": "null",
            "undefined": "null",
        }

    def parse_file(self, file_path: str) -> IRModule:
        """Parse TypeScript file → IR."""
        # Run TypeScript parser
        result = subprocess.run(
            ["node", str(self.parser_path), file_path],
            capture_output=True,
            text=True,
            check=True
        )

        # Parse JSON output
        ast_data = json.loads(result.stdout)

        # Convert to IR
        ir_module = self._convert_ast_to_ir(ast_data, file_path)
        return ir_module

    def _convert_ast_to_ir(self, ast_data: Dict[str, Any], file_path: str) -> IRModule:
        """Convert TypeScript JSON AST to IR."""
        module_name = Path(file_path).stem

        classes = []
        functions = []

        for item in ast_data.get("items", []):
            item_type = item.get("type")

            if item_type == "class":
                classes.append(self._convert_class(item))
            elif item_type == "interface":
                # For now, treat interfaces as classes with no methods
                classes.append(self._convert_interface(item))
            elif item_type == "function":
                functions.append(self._convert_function(item))

        return IRModule(
            name=module_name,
            classes=classes,
            functions=functions
        )

    def _convert_class(self, class_data: Dict[str, Any]) -> IRClass:
        """Convert TypeScript class to IR."""
        name = class_data.get("name", "Anonymous")

        # Properties
        properties = []
        for prop_data in class_data.get("properties", []):
            prop_name = prop_data.get("name")
            prop_type = self._convert_type(prop_data.get("type", "any"))
            is_optional = prop_data.get("isOptional", False)

            properties.append(IRProperty(
                name=prop_name,
                prop_type=prop_type
            ))

        # Methods
        methods = []
        for method_data in class_data.get("methods", []):
            methods.append(self._convert_method(method_data))

        # Constructor
        constructor = None
        constructor_data = class_data.get("constructor")
        if constructor_data:
            constructor = self._convert_method(constructor_data, is_constructor=True)

        return IRClass(
            name=name,
            properties=properties,
            methods=methods,
            constructor=constructor
        )

    def _convert_interface(self, interface_data: Dict[str, Any]) -> IRClass:
        """Convert TypeScript interface to IR class (no methods)."""
        name = interface_data.get("name", "Anonymous")

        properties = []
        for prop_data in interface_data.get("properties", []):
            prop_name = prop_data.get("name")
            prop_type = self._convert_type(prop_data.get("type", "any"))
            is_optional = prop_data.get("isOptional", False)

            properties.append(IRProperty(
                name=prop_name,
                prop_type=prop_type
            ))

        return IRClass(
            name=name,
            properties=properties,
            methods=[]
        )

    def _convert_function(self, func_data: Dict[str, Any]) -> IRFunction:
        """Convert TypeScript function to IR."""
        name = func_data.get("name", "anonymous")
        params = self._convert_parameters(func_data.get("params", []))
        return_type = self._convert_type(func_data.get("returnType", "void"))
        body = self._convert_body(func_data.get("body", []))
        is_async = func_data.get("isAsync", False)

        return IRFunction(
            name=name,
            params=params,
            return_type=return_type,
            body=body,
            is_async=is_async
        )

    def _convert_method(self, method_data: Dict[str, Any], is_constructor: bool = False) -> IRFunction:
        """Convert TypeScript method to IR."""
        name = method_data.get("name", "constructor" if is_constructor else "anonymous")
        params = self._convert_parameters(method_data.get("params", []))
        return_type = self._convert_type(method_data.get("returnType", "void"))
        body = self._convert_body(method_data.get("body", []))
        is_async = method_data.get("isAsync", False)
        is_static = method_data.get("isStatic", False)

        return IRFunction(
            name=name,
            params=params,
            return_type=return_type,
            body=body,
            is_async=is_async,
            is_static=is_static
        )

    def _convert_parameters(self, params_data: List[Dict[str, Any]]) -> List[IRParameter]:
        """Convert TypeScript parameters to IR."""
        params = []
        for param_data in params_data:
            param_name = param_data.get("name", "unknown")
            param_type = self._convert_type(param_data.get("type", "any"))
            is_optional = param_data.get("isOptional", False)

            params.append(IRParameter(
                name=param_name,
                param_type=param_type
            ))

        return params

    def _convert_body(self, body_data: List[Dict[str, Any]]) -> List:
        """Convert TypeScript statement list to IR."""
        body = []
        for stmt_data in body_data:
            ir_stmt = self._convert_statement(stmt_data)
            if ir_stmt:
                body.append(ir_stmt)
        return body

    def _convert_statement(self, stmt_data: Dict[str, Any]) -> Optional[Any]:
        """Convert TypeScript statement JSON to IR statement."""
        stmt_type = stmt_data.get("type")

        if stmt_type == "variable":
            target = stmt_data.get("name", "unknown")
            value_data = stmt_data.get("value")
            value = self._convert_expression(value_data) if value_data else IRLiteral(value=None, literal_type=LiteralType.NULL)
            return IRAssignment(target=target, value=value)

        elif stmt_type == "const":
            target = stmt_data.get("name", "unknown")
            value_data = stmt_data.get("value")
            value = self._convert_expression(value_data) if value_data else IRLiteral(value=None, literal_type=LiteralType.NULL)
            return IRAssignment(target=target, value=value)

        elif stmt_type == "assign":
            target = stmt_data.get("target", "unknown")
            value = self._convert_expression(stmt_data.get("value", {}))
            return IRAssignment(target=target, value=value)

        elif stmt_type == "if":
            condition = self._convert_expression(stmt_data.get("condition", {}))
            then_body = []
            for body_stmt in stmt_data.get("thenBody", []):
                ir_stmt = self._convert_statement(body_stmt)
                if ir_stmt:
                    then_body.append(ir_stmt)

            else_body = None
            if "elseBody" in stmt_data:
                else_body = []
                for body_stmt in stmt_data.get("elseBody", []):
                    ir_stmt = self._convert_statement(body_stmt)
                    if ir_stmt:
                        else_body.append(ir_stmt)

            return IRIf(condition=condition, then_body=then_body, else_body=else_body)

        elif stmt_type == "for":
            iterator = stmt_data.get("iterator", "i")
            iterable = self._convert_expression(stmt_data.get("iterable", {}))
            body = []
            for body_stmt in stmt_data.get("body", []):
                ir_stmt = self._convert_statement(body_stmt)
                if ir_stmt:
                    body.append(ir_stmt)

            return IRFor(iterator=iterator, iterable=iterable, body=body)

        elif stmt_type == "while":
            condition = self._convert_expression(stmt_data.get("condition", {}))
            body = []
            for body_stmt in stmt_data.get("body", []):
                ir_stmt = self._convert_statement(body_stmt)
                if ir_stmt:
                    body.append(ir_stmt)

            return IRWhile(condition=condition, body=body)

        elif stmt_type == "switch":
            value = self._convert_expression(stmt_data.get("value", {}))
            cases = []
            for case_data in stmt_data.get("cases", []):
                is_default = case_data.get("isDefault", False)
                case_body = []
                for body_stmt in case_data.get("body", []):
                    ir_stmt = self._convert_statement(body_stmt)
                    if ir_stmt:
                        case_body.append(ir_stmt)

                if is_default:
                    cases.append(IRCase(values=[], body=case_body, is_default=True))
                else:
                    case_values = [self._convert_expression(v) for v in case_data.get("values", [])]
                    cases.append(IRCase(values=case_values, body=case_body, is_default=False))

            return IRSwitch(value=value, cases=cases)

        elif stmt_type == "try":
            try_body = []
            for body_stmt in stmt_data.get("tryBody", []):
                ir_stmt = self._convert_statement(body_stmt)
                if ir_stmt:
                    try_body.append(ir_stmt)

            catch_blocks = []
            if "catchBody" in stmt_data and stmt_data.get("catchBody"):
                catch_var = stmt_data.get("catchVar")
                catch_body = []
                for body_stmt in stmt_data.get("catchBody", []):
                    ir_stmt = self._convert_statement(body_stmt)
                    if ir_stmt:
                        catch_body.append(ir_stmt)
                catch_blocks.append(IRCatch(exception_type=None, exception_var=catch_var, body=catch_body))

            finally_body = []
            if "finallyBody" in stmt_data and stmt_data.get("finallyBody"):
                for body_stmt in stmt_data.get("finallyBody", []):
                    ir_stmt = self._convert_statement(body_stmt)
                    if ir_stmt:
                        finally_body.append(ir_stmt)

            return IRTry(try_body=try_body, catch_blocks=catch_blocks, finally_body=finally_body)

        elif stmt_type == "return":
            value_data = stmt_data.get("value")
            value = self._convert_expression(value_data) if value_data else None
            return IRReturn(value=value)

        elif stmt_type == "throw":
            value = self._convert_expression(stmt_data.get("value", {}))
            return IRThrow(exception=value)

        elif stmt_type == "break":
            return IRBreak()

        elif stmt_type == "continue":
            return IRContinue()

        elif stmt_type == "expr":
            expr = self._convert_expression(stmt_data.get("expr", {}))
            return expr  # Expression statement

        return None

    def _convert_expression(self, expr_data: Dict[str, Any]) -> Any:
        """Convert TypeScript expression JSON to IR expression."""
        if not expr_data:
            return IRLiteral(value=None, literal_type=LiteralType.NULL)

        expr_type = expr_data.get("type")

        if expr_type == "binary":
            op = expr_data.get("op", "+")
            left = self._convert_expression(expr_data.get("left", {}))
            right = self._convert_expression(expr_data.get("right", {}))
            return IRBinaryOp(op=self._map_operator(op), left=left, right=right)

        elif expr_type == "ident":
            name = expr_data.get("name", "unknown")
            return IRIdentifier(name=name)

        elif expr_type == "literal":
            value = expr_data.get("value")
            literal_type = self._infer_literal_type(value)
            return IRLiteral(value=value, literal_type=literal_type)

        elif expr_type == "call":
            function = expr_data.get("function", "unknown")
            args = [self._convert_expression(arg) for arg in expr_data.get("args", [])]
            return IRCall(function=function, args=args)

        elif expr_type == "new":
            class_name = expr_data.get("class", "Unknown")
            args = [self._convert_expression(arg) for arg in expr_data.get("args", [])]
            # IRNew doesn't exist, use IRCall with "new ClassName"
            return IRCall(function=f"new {class_name}", args=args)

        elif expr_type == "array":
            elements = [self._convert_expression(elem) for elem in expr_data.get("elements", [])]
            return IRArray(elements=elements)

        elif expr_type == "object":
            properties = {}
            for prop in expr_data.get("properties", []):
                key = prop.get("key", "unknown")
                value = self._convert_expression(prop.get("value", {}))
                properties[key] = value
            # IRObject doesn't exist, use IRMap
            return IRMap(key_value_pairs=properties)

        elif expr_type == "arrow":
            params = expr_data.get("params", [])
            body = expr_data.get("body")

            # Arrow body can be expression or statements
            if isinstance(body, list):
                # Statements
                ir_body = []
                for stmt in body:
                    ir_stmt = self._convert_statement(stmt)
                    if ir_stmt:
                        ir_body.append(ir_stmt)
            else:
                # Single expression
                ir_body = [IRReturn(value=self._convert_expression(body))]

            # IRArrowFunction doesn't exist, use IRLambda
            return IRLambda(
                params=[IRParameter(name=p, param_type=IRType(name="any")) for p in params],
                body=ir_body
            )

        # Default: return identifier
        return IRIdentifier(name=str(expr_data))

    def _convert_type(self, type_str: str) -> IRType:
        """Convert TypeScript type to IR type."""
        # Handle array types
        if type_str.endswith("[]"):
            element_type = type_str[:-2]
            return IRType(name="array", args=[self._convert_type(element_type)])

        # Handle generic types (e.g., Array<T>, Map<K, V>)
        if "<" in type_str:
            base_type = type_str.split("<")[0]
            return IRType(name=self.type_mapping.get(base_type, base_type))

        # Map to universal type
        universal_type = self.type_mapping.get(type_str, type_str)
        return IRType(name=universal_type)

    def _map_operator(self, op: str) -> BinaryOperator:
        """Map TypeScript operator to IR operator."""
        op_mapping = {
            "+": BinaryOperator.ADD,
            "-": BinaryOperator.SUBTRACT,
            "*": BinaryOperator.MULTIPLY,
            "/": BinaryOperator.DIVIDE,
            "%": BinaryOperator.MODULO,
            "==": BinaryOperator.EQUAL,
            "===": BinaryOperator.EQUAL,  # Strict equality → EQUAL
            "!=": BinaryOperator.NOT_EQUAL,
            "!==": BinaryOperator.NOT_EQUAL,  # Strict inequality → NOT_EQUAL
            "<": BinaryOperator.LESS_THAN,
            ">": BinaryOperator.GREATER_THAN,
            "<=": BinaryOperator.LESS_EQUAL,
            ">=": BinaryOperator.GREATER_EQUAL,
            "&&": BinaryOperator.AND,
            "||": BinaryOperator.OR,
        }
        return op_mapping.get(op, BinaryOperator.ADD)

    def _infer_literal_type(self, value: Any) -> LiteralType:
        """Infer literal type from value."""
        if value is None or value == "null" or value == "undefined":
            return LiteralType.NULL
        elif value is True or value is False or value == "true" or value == "false":
            return LiteralType.BOOLEAN
        elif isinstance(value, str):
            # Try to infer numeric types
            try:
                int(value)
                return LiteralType.INTEGER
            except ValueError:
                pass
            try:
                float(value)
                return LiteralType.FLOAT
            except ValueError:
                pass
            return LiteralType.STRING
        elif isinstance(value, int):
            return LiteralType.INTEGER
        elif isinstance(value, float):
            return LiteralType.FLOAT
        else:
            return LiteralType.STRING
