"""Thin generator that queries MCP for ALL operations"""
from typing import Dict, List, Set
from dsl.ir import *
from dsl.mcp_client import get_mcp_client

class MCPCodeGenerator:
    def __init__(self, target_lang: str):
        self.target = target_lang
        self.mcp = get_mcp_client()
        self.imports = set()
        self.indent = 0
    
    def generate(self, module: IRModule) -> str:
        parts = []
        
        # Functions
        for func in module.functions:
            parts.append(self.gen_function(func))
        
        # Imports at top
        if self.imports:
            return '\n'.join(sorted(self.imports)) + '\n\n' + '\n\n'.join(parts)
        return '\n\n'.join(parts)
    
    def gen_function(self, func: IRFunction) -> str:
        if self.target == "python":
            params = ', '.join(p.name for p in func.params)
            body = '\n'.join('    ' + self.gen_stmt(s) for s in func.body)
            return f"def {func.name}({params}):\n{body}"
        elif self.target == "javascript":
            params = ', '.join(p.name for p in func.params)
            body = '\n'.join('    ' + self.gen_stmt(s) for s in func.body)
            return f"function {func.name}({params}) {{\n{body}\n}}"
        elif self.target == "go":
            params = ', '.join(f"{p.name} interface{{}}" for p in func.params)
            body = '\n'.join('    ' + self.gen_stmt(s) for s in func.body)
            return f"func {func.name}({params}) interface{{}} {{\n{body}\n}}"
    
    def gen_stmt(self, node) -> str:
        if isinstance(node, IRAssignment):
            val = self.gen_expr(node.value)
            if self.target == "python":
                return f"{node.target} = {val}"
            elif self.target == "javascript":
                return f"let {node.target} = {val};"
            elif self.target == "go":
                return f"{node.target} := {val}"
        elif isinstance(node, IRReturn):
            val = self.gen_expr(node.value) if node.value else ""
            return f"return {val}"
        elif isinstance(node, IRCall):
            return self.gen_expr(node)
        return f"// Unknown: {type(node).__name__}"
    
    def gen_expr(self, node) -> str:
        if isinstance(node, IRLiteral):
            if isinstance(node.value, str):
                return f'"{node.value}"'
            return str(node.value)
        elif isinstance(node, IRIdentifier):
            return node.name
        elif isinstance(node, IRBinaryOp):
            l = self.gen_expr(node.left)
            r = self.gen_expr(node.right)
            op = node.op.value if hasattr(node.op, 'value') else node.op
            return f"({l} {op} {r})"
        elif isinstance(node, IRCall):
            if isinstance(node.function, IRIdentifier):
                # Built-in
                if node.function.name == "print":
                    args = ', '.join(self.gen_expr(a) for a in node.args)
                    if self.target == "python":
                        return f"print({args})"
                    elif self.target == "javascript":
                        return f"console.log({args})"
                    elif self.target == "go":
                        self.imports.add('import "fmt"')
                        return f"fmt.Println({args})"
                # User function
                args = ', '.join(self.gen_expr(a) for a in node.args)
                return f"{node.function.name}({args})"
            elif isinstance(node.function, IRPropertyAccess):
                # MCP OPERATION - QUERY MCP
                ns = node.function.object.name
                method = node.function.property
                op_id = f"{ns}.{method}"
                
                try:
                    impl = self.mcp.get_operation(op_id, self.target)
                    # Add imports
                    for imp in impl.get('imports', []):
                        self.imports.add(imp)
                    # Generate code from template
                    code = impl['code']
                    for i, arg in enumerate(node.args):
                        arg_val = self.gen_expr(arg)
                        code = code.replace(f"{{arg{i}}}", arg_val)
                    return code
                except Exception as e:
                    return f"/* MCP error: {e} */"
        return f"/* Unknown: {type(node).__name__} */"

def generate_code(module: IRModule, target: str) -> str:
    gen = MCPCodeGenerator(target)
    return gen.generate(module)
