"""
PW Runtime Engine
Execute PW code directly using CharCNN + MCP pipeline
"""

import sys
import json
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional, List
from dataclasses import dataclass

from dsl.pw_parser import parse_pw, PWParseError
from dsl.ir import *
from ml.inference import OperationLookup


@dataclass
class RuntimeContext:
    """Runtime execution context"""
    variables: Dict[str, Any]
    functions: Dict[str, IRFunction]
    return_value: Optional[Any] = None

    def __init__(self):
        self.variables = {}
        self.functions = {}
        self.return_value = None


class PWRuntime:
    """PW code execution engine"""

    def __init__(self, use_charcnn: bool = True):
        self.context = RuntimeContext()
        self.operation_lookup = None

        if use_charcnn:
            try:
                self.operation_lookup = OperationLookup(model_path='ml/charcnn_large.pt')
                print("✅ CharCNN loaded")
            except Exception as e:
                print(f"⚠️  CharCNN not available: {e}")
                self.operation_lookup = None

    def execute_file(self, file_path: str) -> Any:
        """Execute a PW file"""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        code = path.read_text()
        return self.execute(code, file_path)

    def execute(self, code: str, source_name: str = "<stdin>") -> Any:
        """Execute PW code"""
        try:
            # Parse code
            ir_module = parse_pw(code)

            # Register functions
            for func in ir_module.functions:
                self.context.functions[func.name] = func

            # Execute module-level variables
            for stmt in ir_module.module_vars:
                self.execute_node(stmt)

            # If there's a main function, execute it
            if 'main' in self.context.functions:
                self.execute_function(self.context.functions['main'], [])

            return self.context.return_value

        except PWParseError as e:
            print(f"Parse error in {source_name}:{e.line}:{e.column}")
            print(f"  {e}")
            raise
        except Exception as e:
            print(f"Runtime error in {source_name}: {e}")
            raise

    def execute_node(self, node: IRNode) -> Any:
        """Execute an IR node"""
        if isinstance(node, IRLiteral):
            return node.value

        elif isinstance(node, IRIdentifier):
            if node.name not in self.context.variables:
                raise NameError(f"Variable not defined: {node.name}")
            return self.context.variables[node.name]

        elif isinstance(node, IRArray):
            return [self.execute_node(item) for item in node.elements]

        elif isinstance(node, IRBinaryOp):
            left = self.execute_node(node.left)
            right = self.execute_node(node.right)
            return self.execute_binop(node.op, left, right)

        elif isinstance(node, IRUnaryOp):
            operand = self.execute_node(node.operand)
            return self.execute_unaryop(node.op, operand)

        elif isinstance(node, IRCall):
            return self.execute_call(node)

        elif isinstance(node, IRAssignment):
            value = self.execute_node(node.value)
            self.context.variables[node.target] = value
            return value

        elif isinstance(node, IRIf):
            condition = self.execute_node(node.condition)
            if condition:
                for stmt in node.then_body:
                    result = self.execute_node(stmt)
                    if self.context.return_value is not None:
                        return result
            elif node.else_body:
                for stmt in node.else_body:
                    result = self.execute_node(stmt)
                    if self.context.return_value is not None:
                        return result
            return None

        elif isinstance(node, IRWhile):
            while self.execute_node(node.condition):
                for stmt in node.body:
                    result = self.execute_node(stmt)
                    if self.context.return_value is not None:
                        return result
            return None

        elif isinstance(node, IRFor):
            iterable = self.execute_node(node.iterable)
            for item in iterable:
                self.context.variables[node.variable] = item
                for stmt in node.body:
                    result = self.execute_node(stmt)
                    if self.context.return_value is not None:
                        return result
            return None

        elif isinstance(node, IRReturn):
            self.context.return_value = self.execute_node(node.value) if node.value else None
            return self.context.return_value

        else:
            raise NotImplementedError(f"Node type not implemented: {type(node).__name__}")

    def execute_binop(self, op, left: Any, right: Any) -> Any:
        """Execute binary operation"""
        # Handle both string and enum
        op_str = op.value if hasattr(op, 'value') else op

        if op_str == '+':
            return left + right
        elif op_str == '-':
            return left - right
        elif op_str == '*':
            return left * right
        elif op_str == '/':
            return left / right
        elif op_str == '//':
            return left // right
        elif op_str == '%':
            return left % right
        elif op_str == '**':
            return left ** right
        elif op_str == '==':
            return left == right
        elif op_str == '!=':
            return left != right
        elif op_str == '<':
            return left < right
        elif op_str == '<=':
            return left <= right
        elif op_str == '>':
            return left > right
        elif op_str == '>=':
            return left >= right
        elif op_str == 'and':
            return left and right
        elif op_str == 'or':
            return left or right
        elif op_str == 'in':
            return left in right
        else:
            raise NotImplementedError(f"Binary operator not implemented: {op}")

    def execute_unaryop(self, op, operand: Any) -> Any:
        """Execute unary operation"""
        # Handle both string and enum
        op_str = op.value if hasattr(op, 'value') else op

        if op_str == '-':
            return -operand
        elif op_str == 'not':
            return not operand
        elif op_str == '+':
            return +operand
        elif op_str == '~':
            return ~operand
        else:
            raise NotImplementedError(f"Unary operator not implemented: {op}")

    def execute_call(self, node: IRCall) -> Any:
        """Execute function call"""
        # Check if it's a built-in function
        if isinstance(node.function, IRIdentifier):
            func_name = node.function.name

            # Built-in functions
            if func_name == 'print':
                args = [self.execute_node(arg) for arg in node.args]
                print(*args)
                return None

            elif func_name == 'len':
                if len(node.args) != 1:
                    raise TypeError(f"len() takes exactly 1 argument ({len(node.args)} given)")
                arg = self.execute_node(node.args[0])
                return len(arg)

            elif func_name == 'range':
                args = [self.execute_node(arg) for arg in node.args]
                return range(*args)

            elif func_name == 'str':
                if len(node.args) != 1:
                    raise TypeError(f"str() takes exactly 1 argument ({len(node.args)} given)")
                arg = self.execute_node(node.args[0])
                return str(arg)

            elif func_name == 'int':
                if len(node.args) != 1:
                    raise TypeError(f"int() takes exactly 1 argument ({len(node.args)} given)")
                arg = self.execute_node(node.args[0])
                return int(arg)

            elif func_name == 'float':
                if len(node.args) != 1:
                    raise TypeError(f"float() takes exactly 1 argument ({len(node.args)} given)")
                arg = self.execute_node(node.args[0])
                return float(arg)

            # User-defined function
            elif func_name in self.context.functions:
                return self.execute_function(self.context.functions[func_name], node.args)

            else:
                raise NameError(f"Function not defined: {func_name}")

        # Method call (e.g., str.split, file.read)
        elif isinstance(node.function, IRPropertyAccess):
            return self.execute_method_call(node)

        else:
            raise NotImplementedError(f"Call type not implemented: {type(node.function).__name__}")

    def execute_method_call(self, node: IRCall) -> Any:
        """Execute method call using CharCNN + MCP"""
        if not isinstance(node.function, IRPropertyAccess):
            raise TypeError("Expected IRPropertyAccess for method call")

        member_access = node.function
        namespace = None
        method = None

        # Get namespace and method name
        if isinstance(member_access.object, IRIdentifier):
            namespace = member_access.object.name
            method = member_access.property
        else:
            raise NotImplementedError("Complex property access not yet supported")

        operation_id = f"{namespace}.{method}"

        # Evaluate arguments
        args = [self.execute_node(arg) for arg in node.args]

        # Note: CharCNN predictions are available in node.operation_id (from parser)
        # but we don't override the namespace.method from AST since that's authoritative
        # CharCNN is useful for ambiguous cases or LSP suggestions, not runtime execution

        # Execute operation
        return self.execute_operation(operation_id, args)

    def execute_operation(self, operation_id: str, args: List[Any]) -> Any:
        """Execute operation (delegates to Python stdlib or MCP)"""
        # For now, implement common operations directly
        # In production, this would query MCP and execute generated code

        namespace, method = operation_id.split('.')

        # String operations
        if namespace == 'str':
            if method == 'split':
                if len(args) != 2:
                    raise TypeError(f"str.split() takes 2 arguments ({len(args)} given)")
                return args[0].split(args[1])
            elif method == 'upper':
                return args[0].upper()
            elif method == 'lower':
                return args[0].lower()
            elif method == 'strip':
                return args[0].strip()
            elif method == 'replace':
                return args[0].replace(args[1], args[2])
            elif method == 'join':
                return args[0].join(args[1])
            elif method == 'contains':
                return args[1] in args[0]
            elif method == 'starts_with':
                return args[0].startswith(args[1])
            elif method == 'ends_with':
                return args[0].endswith(args[1])

        # File operations
        elif namespace == 'file':
            if method == 'read':
                return Path(args[0]).read_text()
            elif method == 'write':
                Path(args[0]).write_text(args[1])
                return None
            elif method == 'exists':
                return Path(args[0]).exists()
            elif method == 'delete':
                Path(args[0]).unlink()
                return None

        # Array operations
        elif namespace == 'array':
            if method == 'push':
                args[0].append(args[1])
                return None
            elif method == 'pop':
                return args[0].pop()
            elif method == 'len':
                return len(args[0])
            elif method == 'reverse':
                args[0].reverse()
                return None
            elif method == 'sort':
                args[0].sort()
                return None
            elif method == 'contains':
                return args[1] in args[0]

        # JSON operations
        elif namespace == 'json':
            if method == 'parse':
                return json.loads(args[0])
            elif method == 'stringify':
                return json.dumps(args[0])
            elif method == 'stringify_pretty':
                return json.dumps(args[0], indent=2)

        # Math operations
        elif namespace == 'math':
            import math
            if method == 'abs':
                return abs(args[0])
            elif method == 'ceil':
                return math.ceil(args[0])
            elif method == 'floor':
                return math.floor(args[0])
            elif method == 'round':
                return round(args[0])
            elif method == 'sqrt':
                return math.sqrt(args[0])
            elif method == 'pow':
                return math.pow(args[0], args[1])
            elif method == 'max':
                return max(*args)
            elif method == 'min':
                return min(*args)

        # HTTP operations (simplified - would use requests in production)
        elif namespace == 'http':
            if method == 'get':
                import urllib.request
                with urllib.request.urlopen(args[0]) as response:
                    return response.read().decode('utf-8')
            elif method == 'get_json':
                import urllib.request
                with urllib.request.urlopen(args[0]) as response:
                    return json.loads(response.read().decode('utf-8'))

        raise NotImplementedError(f"Operation not implemented: {operation_id}")

    def execute_function(self, func: IRFunction, args: List[IRExpression]) -> Any:
        """Execute user-defined function"""
        # Evaluate arguments
        arg_values = [self.execute_node(arg) for arg in args]

        # Create new context for function
        old_vars = self.context.variables.copy()
        old_return = self.context.return_value

        # Bind arguments
        for param, value in zip(func.params, arg_values):
            self.context.variables[param.name] = value

        # Execute function body
        self.context.return_value = None
        for stmt in func.body:
            self.execute_node(stmt)

        # Get return value
        result = self.context.return_value

        # Restore context
        self.context.variables = old_vars
        self.context.return_value = old_return

        return result


def execute_pw_file(file_path: str) -> Any:
    """Convenience function to execute a PW file"""
    runtime = PWRuntime()
    return runtime.execute_file(file_path)


def execute_pw_code(code: str) -> Any:
    """Convenience function to execute PW code"""
    runtime = PWRuntime()
    return runtime.execute(code)


if __name__ == "__main__":
    # Test runtime
    if len(sys.argv) > 1:
        runtime = PWRuntime()
        runtime.execute_file(sys.argv[1])
    else:
        print("Usage: python3 dsl/runtime.py <file.al>")
