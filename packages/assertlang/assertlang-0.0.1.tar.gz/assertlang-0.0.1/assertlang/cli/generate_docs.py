"""
Contract Documentation Generator

Generates markdown documentation from PW contracts.
"""

from typing import List, Optional
from dsl.pw_parser import parse_pw


class ContractDocGenerator:
    """Generates documentation from PW contracts"""

    def generate(self, file_path: str) -> str:
        """Generate markdown documentation from contract file"""
        with open(file_path, 'r') as f:
            code = f.read()

        ir = parse_pw(code)

        doc_parts = []

        # Title
        doc_parts.append(f"# {file_path} - Contract Documentation\n")

        # Services/Classes
        for cls in ir.classes:
            doc_parts.append(self._generate_service_doc(cls))

        # Functions
        for func in ir.functions:
            doc_parts.append(self._generate_function_doc(func))

        return "\n".join(doc_parts)

    def _generate_service_doc(self, cls) -> str:
        """Generate documentation for a service"""
        parts = []

        parts.append(f"## Service: {cls.name}\n")

        # Doc comment
        if hasattr(cls, 'doc_comment') and cls.doc_comment:
            parts.append(f"{cls.doc_comment}\n")

        # Contract metadata
        if hasattr(cls, 'contract_metadata') and cls.contract_metadata:
            parts.append("**Metadata:**")
            for key, value in cls.contract_metadata.items():
                parts.append(f"- {key}: `{value}`")
            parts.append("")

        # Invariants
        if hasattr(cls, 'invariants') and cls.invariants:
            parts.append("### Invariants\n")
            parts.append("Properties that always hold:\n")
            for inv in cls.invariants:
                expr_str = self._expr_to_string(inv.expression)
                parts.append(f"- **{inv.name}**: `{expr_str}`")
            parts.append("")

        # Methods
        if hasattr(cls, 'methods'):
            parts.append("### Methods\n")
            for method in cls.methods:
                parts.append(self._generate_function_doc(method, indent=True))

        return "\n".join(parts)

    def _generate_function_doc(self, func, indent: bool = False) -> str:
        """Generate documentation for a function"""
        parts = []
        prefix = "#### " if indent else "## "

        # Function signature
        param_strs = [f"{p.name}: {self._type_to_string(p.type)}" for p in func.params]
        return_str = self._type_to_string(func.return_type) if func.return_type else "void"
        signature = f"{func.name}({', '.join(param_strs)}) -> {return_str}"

        parts.append(f"{prefix}Function: {signature}\n")

        # Doc comment
        if hasattr(func, 'doc_comment') and func.doc_comment:
            parts.append(f"{func.doc_comment}\n")

        # Operation metadata
        if hasattr(func, 'operation_metadata') and func.operation_metadata:
            parts.append("**Operation Properties:**")
            for key, value in func.operation_metadata.items():
                parts.append(f"- {key}: `{value}`")
            parts.append("")

        # Parameters
        if func.params:
            parts.append("**Parameters:**\n")
            for param in func.params:
                parts.append(f"- `{param.name}` ({self._type_to_string(param.type)})")
            parts.append("")

        # Returns
        if func.return_type:
            parts.append(f"**Returns:** {self._type_to_string(func.return_type)}\n")

        # Preconditions
        if hasattr(func, 'requires') and func.requires:
            parts.append("**Preconditions:**\n")
            parts.append("The following conditions must be true when calling this function:\n")
            for req in func.requires:
                expr_str = self._expr_to_string(req.expression)
                parts.append(f"- **{req.name}**: `{expr_str}`")
            parts.append("")

        # Postconditions
        if hasattr(func, 'ensures') and func.ensures:
            parts.append("**Postconditions:**\n")
            parts.append("The following conditions are guaranteed after execution:\n")
            for ens in func.ensures:
                expr_str = self._expr_to_string(ens.expression)
                parts.append(f"- **{ens.name}**: `{expr_str}`")
            parts.append("")

        # Effects
        if hasattr(func, 'effects') and func.effects:
            parts.append("**Side Effects:**\n")
            for effect in func.effects:
                parts.append(f"- {effect}")
            parts.append("")

        parts.append("---\n")

        return "\n".join(parts)

    def _type_to_string(self, type_obj) -> str:
        """Convert IR type to string"""
        if hasattr(type_obj, 'name'):
            return type_obj.name
        return str(type_obj)

    def _expr_to_string(self, expr) -> str:
        """Convert IR expression to string - generic approach"""
        # Just use string representation for simplicity
        # This handles all IR node types generically
        if hasattr(expr, '__str__'):
            result = str(expr)
            # Clean up common patterns
            result = result.replace('IRBinaryOp(', '').replace(')', '')
            result = result.replace('IRUnaryOp(', '').replace(')', '')
            result = result.replace('IRVariable(', '').replace(')', '')
            result = result.replace('IRLiteral(', '').replace(')', '')
            return result
        return str(expr)


def generate_contract_docs(file_path: str, output_path: Optional[str] = None) -> str:
    """
    Generate contract documentation

    Args:
        file_path: Path to PW contract file
        output_path: Optional output file path (defaults to {file}.md)

    Returns:
        Generated documentation as string
    """
    generator = ContractDocGenerator()
    docs = generator.generate(file_path)

    if output_path:
        with open(output_path, 'w') as f:
            f.write(docs)
    elif not output_path:
        # Default: same name as input with .md extension
        output_path = file_path.replace('.al', '.md')
        with open(output_path, 'w') as f:
            f.write(docs)

    return docs


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m promptware.cli.generate_docs <contract.al> [output.md]")
        sys.exit(1)

    file_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None

    docs = generate_contract_docs(file_path, output_path)
    output = output_path or file_path.replace('.al', '.md')
    print(f"Documentation generated: {output}")
