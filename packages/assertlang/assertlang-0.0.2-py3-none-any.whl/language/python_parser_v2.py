"""
Python Parser V2: Arbitrary Python code → IR

This parser converts arbitrary Python code (not just MCP patterns) into the
universal Intermediate Representation (IR). It handles:

- Functions with type hints and without
- Classes with methods, properties, constructors
- Control flow: if, for, while, try/except
- Expressions: arithmetic, logical, function calls
- Type inference for untyped code
- Python-specific idioms (decorators, comprehensions, etc.)

Design:
- Uses Python's ast module for parsing
- Walks AST and transforms each node to IR
- Type inference engine for dynamic code
- Preserves source locations and comments
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

from dsl.ir import (
    BinaryOperator,
    IRArray,
    IRAssignment,
    IRAwait,
    IRBinaryOp,
    IRBreak,
    IRCall,
    IRCase,
    IRCatch,
    IRClass,
    IRComprehension,
    IRContinue,
    IRDecorator,
    IREnum,
    IREnumVariant,
    IRFor,
    IRFString,
    IRFunction,
    IRIdentifier,
    IRIf,
    IRImport,
    IRIndex,
    IRLambda,
    IRLiteral,
    IRMap,
    IRModule,
    IRParameter,
    IRPass,
    IRProperty,
    IRPropertyAccess,
    IRReturn,
    IRStatement,
    IRSwitch,
    IRTernary,
    IRThrow,
    IRTry,
    IRType,
    IRTypeDefinition,
    IRUnaryOp,
    IRWhile,
    IRWith,
    LiteralType,
    SourceLocation,
    UnaryOperator,
)
from dsl.type_system import TypeInfo, TypeSystem


class PythonParserV2:
    """
    Parse arbitrary Python code into IR.

    This parser handles all Python constructs and converts them to
    language-agnostic IR nodes.
    """

    def __init__(self):
        self.type_system = TypeSystem()
        self.type_context: Dict[str, TypeInfo] = {}  # Variable name -> type
        self.current_class: Optional[str] = None
        self.current_function: Optional[str] = None

    def _type_info_to_ir_type(self, type_info: TypeInfo) -> IRType:
        """
        Convert TypeInfo to IRType.

        Handles generic types like "array<int>" -> IRType(name="array", generic_args=[IRType("int")])
        """
        pw_type = type_info.pw_type

        # Parse generic types: array<int>, map<string, int>
        if "<" in pw_type and ">" in pw_type:
            # Extract base type and args
            base_name = pw_type[:pw_type.index("<")]
            args_str = pw_type[pw_type.index("<")+1:pw_type.rindex(">")]

            # Parse generic arguments (simple split by comma)
            generic_args = []
            for arg in args_str.split(","):
                arg = arg.strip()
                generic_args.append(IRType(name=arg))

            return IRType(name=base_name, generic_args=generic_args)

        # Simple type
        return IRType(name=pw_type)

    def _add_statement(self, body: List[IRStatement], stmt: Union[Optional[IRStatement], List[IRStatement]]) -> None:
        """
        Add statement(s) to body, handling both single statements and lists.

        Args:
            body: List to add to
            stmt: Single statement, list of statements, or None
        """
        if stmt is None:
            return
        if isinstance(stmt, list):
            body.extend(stmt)
        else:
            body.append(stmt)

    # ========================================================================
    # Main Entry Point
    # ========================================================================

    def parse_file(self, file_path: str) -> IRModule:
        """
        Parse a Python file into an IR module.

        Args:
            file_path: Path to Python file

        Returns:
            IRModule containing the parsed code
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()

        return self.parse_source(source, module_name=Path(file_path).stem)

    def parse_source(self, source: str, module_name: str = "module") -> IRModule:
        """
        Parse Python source code into an IR module.

        Args:
            source: Python source code
            module_name: Name for the module

        Returns:
            IRModule containing the parsed code
        """
        # Parse Python AST
        tree = ast.parse(source)

        # Extract components
        imports = []
        types = []
        enums = []
        functions = []
        classes = []
        module_vars = []

        for node in tree.body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                imports.extend(self._convert_import(node))
            elif isinstance(node, ast.ClassDef):
                # Check if it's an enum
                if self._is_enum_class(node):
                    enums.append(self._convert_enum(node))
                # Check if it's a dataclass (type definition)
                elif self._is_dataclass(node):
                    types.append(self._convert_type_definition(node))
                else:
                    classes.append(self._convert_class(node))
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions.append(self._convert_function(node))
            elif isinstance(node, ast.Assign):
                # Module-level variable (may be tuple unpacking)
                result = self._convert_assignment(node)
                if isinstance(result, list):
                    module_vars.extend(result)
                else:
                    module_vars.append(result)

        module = IRModule(
            name=module_name,
            version="1.0.0",
            imports=imports,
            types=types,
            enums=enums,
            functions=functions,
            classes=classes,
            module_vars=module_vars
        )

        return module

    # ========================================================================
    # Import Conversion
    # ========================================================================

    def _convert_import(self, node: Union[ast.Import, ast.ImportFrom]) -> List[IRImport]:
        """Convert Python import to IR import."""
        imports = []

        if isinstance(node, ast.Import):
            # import module [as alias]
            for alias in node.names:
                imports.append(IRImport(
                    module=alias.name,
                    alias=alias.asname
                ))
        elif isinstance(node, ast.ImportFrom):
            # from module import item1, item2
            if node.module:
                items = [alias.name for alias in node.names]
                imports.append(IRImport(
                    module=node.module,
                    items=items
                ))

        return imports

    # ========================================================================
    # Type Definition Conversion
    # ========================================================================

    def _is_dataclass(self, node: ast.ClassDef) -> bool:
        """Check if class is a dataclass."""
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name) and decorator.id == 'dataclass':
                return True
            if isinstance(decorator, ast.Call):
                if isinstance(decorator.func, ast.Name) and decorator.func.id == 'dataclass':
                    return True
        return False

    def _is_enum_class(self, node: ast.ClassDef) -> bool:
        """Check if class inherits from Enum."""
        for base in node.bases:
            if isinstance(base, ast.Name) and base.id in ('Enum', 'IntEnum', 'StrEnum'):
                return True
        return False

    def _convert_type_definition(self, node: ast.ClassDef) -> IRTypeDefinition:
        """Convert dataclass to IR type definition."""
        fields = []

        for item in node.body:
            if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                # Field with type annotation
                field_name = item.target.id
                field_type = self._convert_type_annotation(item.annotation)
                default_value = None
                if item.value:
                    default_value = self._convert_expression(item.value)

                fields.append(IRProperty(
                    name=field_name,
                    prop_type=field_type,
                    default_value=default_value
                ))

        return IRTypeDefinition(
            name=node.name,
            fields=fields,
            doc=ast.get_docstring(node)
        )

    def _convert_enum(self, node: ast.ClassDef) -> IREnum:
        """Convert Enum class to IR enum."""
        variants = []

        for item in node.body:
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        variant_name = target.id
                        value = None
                        if isinstance(item.value, (ast.Constant, ast.Num, ast.Str)):
                            value = self._get_constant_value(item.value)

                        variants.append(IREnumVariant(
                            name=variant_name,
                            value=value
                        ))

        return IREnum(
            name=node.name,
            variants=variants,
            doc=ast.get_docstring(node)
        )

    # ========================================================================
    # Class Conversion
    # ========================================================================

    def _convert_class(self, node: ast.ClassDef) -> IRClass:
        """Convert Python class to IR class."""
        self.current_class = node.name

        properties = []
        methods = []
        constructor = None
        base_classes = []

        # Extract base classes
        for base in node.bases:
            if isinstance(base, ast.Name):
                base_classes.append(base.id)

        # Extract properties and methods
        for item in node.body:
            if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                # Class property with type annotation
                prop_name = item.target.id
                prop_type = self._convert_type_annotation(item.annotation)
                default_value = None
                if item.value:
                    default_value = self._convert_expression(item.value)

                properties.append(IRProperty(
                    name=prop_name,
                    prop_type=prop_type,
                    default_value=default_value
                ))

            elif isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if item.name == '__init__':
                    constructor = self._convert_function(item, is_constructor=True)
                else:
                    methods.append(self._convert_function(item, is_method=True))

        # Extract properties from constructor assignments
        if constructor:
            for stmt in constructor.body:
                if isinstance(stmt, IRAssignment):
                    # Check if assignment is to self.property_name
                    if stmt.target.startswith("self."):
                        prop_name = stmt.target.replace("self.", "")

                        # Check if not already in properties list
                        if not any(p.name == prop_name for p in properties):
                            # Infer type from assignment value
                            prop_type = self._infer_expr_type_from_ir(stmt.value) if stmt.value else IRType(name='any')

                            properties.append(IRProperty(
                                name=prop_name,
                                prop_type=prop_type,
                                default_value=stmt.value
                            ))

        self.current_class = None

        return IRClass(
            name=node.name,
            properties=properties,
            methods=methods,
            constructor=constructor,
            base_classes=base_classes,
            doc=ast.get_docstring(node)
        )

    # ========================================================================
    # Function Conversion
    # ========================================================================

    def _convert_function(
        self,
        node: Union[ast.FunctionDef, ast.AsyncFunctionDef],
        is_method: bool = False,
        is_constructor: bool = False
    ) -> IRFunction:
        """Convert Python function to IR function."""
        self.current_function = node.name

        # Extract decorators
        decorators = []
        for dec in node.decorator_list:
            if isinstance(dec, ast.Name):
                # Simple decorator: @property, @staticmethod
                decorators.append(dec.id)
            elif isinstance(dec, ast.Call):
                # Decorator with args: @lru_cache(maxsize=100)
                if isinstance(dec.func, ast.Name):
                    decorators.append(dec.func.id)
                elif isinstance(dec.func, ast.Attribute):
                    # Chained decorator: @pytest.mark.skip
                    decorators.append(self._get_full_name(dec.func))
            elif isinstance(dec, ast.Attribute):
                # Attribute decorator: @abc.abstractmethod
                decorators.append(self._get_full_name(dec))

        # Extract parameters
        params = []
        for arg in node.args.args:
            # Skip 'self' and 'cls' for methods and constructors
            if (is_method or is_constructor) and arg.arg in ('self', 'cls'):
                continue

            param_type = None
            if arg.annotation:
                param_type = self._convert_type_annotation(arg.annotation)
            else:
                # Type inference for unannotated params - try to infer from usage
                param_type = self._infer_param_type_from_usage(arg.arg, node)

            # Check for default value
            default_value = None
            default_index = len(node.args.args) - len(node.args.defaults)
            arg_index = node.args.args.index(arg)
            if arg_index >= default_index:
                default_idx = arg_index - default_index
                default_value = self._convert_expression(node.args.defaults[default_idx])

            params.append(IRParameter(
                name=arg.arg,
                param_type=param_type,
                default_value=default_value
            ))

            # Update type context
            self.type_context[arg.arg] = TypeInfo(
                pw_type=param_type.name,
                confidence=1.0 if arg.annotation else 0.3,
                source="explicit" if arg.annotation else "inferred"
            )

        # Extract return type
        return_type = None
        if node.returns:
            return_type = self._convert_type_annotation(node.returns)
        else:
            # Infer return type from return statements
            return_type = self._infer_return_type(node)

        # Extract throws (from docstring or raise statements)
        throws = self._extract_throws(node)

        # Convert function body
        body = []
        for stmt in node.body:
            # Skip docstring
            if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant):
                continue
            ir_stmt = self._convert_statement(stmt)
            self._add_statement(body, ir_stmt)

        self.current_function = None

        return IRFunction(
            name=node.name,
            params=params,
            return_type=return_type,
            throws=throws,
            body=body,
            is_async=isinstance(node, ast.AsyncFunctionDef),
            is_static='staticmethod' in decorators,
            is_private=node.name.startswith('_'),
            decorators=decorators,
            doc=ast.get_docstring(node)
        )

    def _extract_throws(self, node: ast.FunctionDef) -> List[str]:
        """Extract exception types that function can throw."""
        throws = []

        for stmt in ast.walk(node):
            if isinstance(stmt, ast.Raise):
                if isinstance(stmt.exc, ast.Call):
                    if isinstance(stmt.exc.func, ast.Name):
                        exception_name = stmt.exc.func.id
                        if exception_name not in throws:
                            throws.append(exception_name)
                elif isinstance(stmt.exc, ast.Name):
                    exception_name = stmt.exc.id
                    if exception_name not in throws:
                        throws.append(exception_name)

        return throws

    def _infer_return_type(self, node: ast.FunctionDef) -> Optional[IRType]:
        """
        Infer return type from return statements in function.

        Strategy:
        1. Build local type context from assignments in function body
        2. Find all return statements
        3. Infer type of each return value (using local context)
        4. Combine types (if all same, use that; otherwise use 'any')
        """
        # Build local type context for variable lookups
        local_context = dict(self.type_context)  # Start with current context

        # Quick pass: find assignments and infer their types
        for stmt in ast.walk(node):
            if isinstance(stmt, ast.Assign):
                if stmt.targets and isinstance(stmt.targets[0], ast.Name):
                    var_name = stmt.targets[0].id
                    # Save current context, infer type, restore
                    saved_context = self.type_context
                    self.type_context = local_context
                    var_type = self._infer_expr_type(stmt.value)
                    self.type_context = saved_context

                    if var_type:
                        local_context[var_name] = TypeInfo(
                            pw_type=var_type.name,
                            confidence=0.9,
                            source='inferred'
                        )

        # Now infer return types using local context
        return_types = []
        saved_context = self.type_context
        self.type_context = local_context

        for stmt in ast.walk(node):
            if isinstance(stmt, ast.Return) and stmt.value:
                # Infer type from return value
                inferred_type = self._infer_expr_type(stmt.value)
                if inferred_type:
                    return_types.append(inferred_type)

        self.type_context = saved_context

        # No return statements or only 'return' without value
        if not return_types:
            return None

        # All return types are the same
        first_type = return_types[0]
        if all(t.name == first_type.name for t in return_types):
            return first_type

        # Mixed types - check if numeric (int + float = float)
        if all(t.name in ('int', 'float') for t in return_types):
            return IRType(name='float')

        # Mixed types - use 'any'
        return IRType(name='any')

    def _infer_expr_type_from_ir(self, expr: Any) -> IRType:
        """
        Infer type from an IR expression node.

        This is used when we have already converted AST to IR and need type information.
        """
        if isinstance(expr, IRLiteral):
            # Map literal types to IR types
            type_mapping = {
                LiteralType.NULL: 'null',
                LiteralType.BOOLEAN: 'bool',
                LiteralType.INTEGER: 'int',
                LiteralType.FLOAT: 'float',
                LiteralType.STRING: 'string',
            }
            return IRType(name=type_mapping.get(expr.literal_type, 'any'))

        elif isinstance(expr, IRArray):
            # Array type
            if expr.elements:
                # Infer element type from first element
                elem_type = self._infer_expr_type_from_ir(expr.elements[0])
                return IRType(name='array', generic_args=[elem_type])
            return IRType(name='array', generic_args=[IRType(name='any')])

        elif isinstance(expr, IRMap):
            # Map type
            if expr.entries:
                # Infer value type from first entry
                first_value = list(expr.entries.values())[0]
                value_type = self._infer_expr_type_from_ir(first_value)
                return IRType(name='map', generic_args=[IRType(name='string'), value_type])
            return IRType(name='map', generic_args=[IRType(name='string'), IRType(name='any')])

        elif isinstance(expr, IRIdentifier):
            # Look up identifier in context
            if expr.name in self.type_context:
                return IRType(name=self.type_context[expr.name].pw_type)
            return IRType(name='any')

        elif isinstance(expr, IRBinaryOp):
            # Infer from operation type
            if expr.op in (BinaryOperator.ADD, BinaryOperator.SUBTRACT, BinaryOperator.MULTIPLY,
                          BinaryOperator.DIVIDE, BinaryOperator.MODULO, BinaryOperator.POWER):
                # Arithmetic operations return numeric types
                return IRType(name='float')  # Conservative choice
            elif expr.op in (BinaryOperator.EQUAL, BinaryOperator.NOT_EQUAL, BinaryOperator.LESS_THAN,
                            BinaryOperator.LESS_EQUAL, BinaryOperator.GREATER_THAN, BinaryOperator.GREATER_EQUAL,
                            BinaryOperator.AND, BinaryOperator.OR):
                # Comparison and boolean operations return bool
                return IRType(name='bool')
            return IRType(name='any')

        elif isinstance(expr, IRCall):
            # Try to infer from function name
            if isinstance(expr.function, IRIdentifier):
                func_name = expr.function.name
                type_mapping = {
                    'str': 'string',
                    'int': 'int',
                    'float': 'float',
                    'bool': 'bool',
                    'list': 'array',
                    'dict': 'map',
                }
                if func_name in type_mapping:
                    return IRType(name=type_mapping[func_name])
            return IRType(name='any')

        elif isinstance(expr, IRTernary):
            # Try to infer from true value (assuming both branches have same type)
            return self._infer_expr_type_from_ir(expr.true_value)

        # Default: any
        return IRType(name='any')

    def _infer_expr_type(self, node: ast.expr) -> Optional[IRType]:
        """
        Infer IR type from an AST expression node.

        This is a lightweight inference for common patterns.
        """
        # Literal values
        if isinstance(node, ast.Constant):
            if node.value is None:
                return IRType(name='null')
            elif isinstance(node.value, bool):
                return IRType(name='bool')
            elif isinstance(node.value, int):
                return IRType(name='int')
            elif isinstance(node.value, float):
                return IRType(name='float')
            elif isinstance(node.value, str):
                return IRType(name='string')

        # Legacy literals (Python 3.7 and earlier)
        elif isinstance(node, ast.Num):
            if isinstance(node.n, int):
                return IRType(name='int')
            elif isinstance(node.n, float):
                return IRType(name='float')
        elif isinstance(node, ast.Str):
            return IRType(name='string')
        elif isinstance(node, ast.NameConstant):
            if node.value is None:
                return IRType(name='null')
            elif isinstance(node.value, bool):
                return IRType(name='bool')

        # Binary operations
        elif isinstance(node, ast.BinOp):
            left_type = self._infer_expr_type(node.left)
            right_type = self._infer_expr_type(node.right)

            # Arithmetic operators
            if isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod, ast.Pow)):
                # If either is float, result is float
                if left_type and left_type.name == 'float':
                    return IRType(name='float')
                if right_type and right_type.name == 'float':
                    return IRType(name='float')
                # Division always returns float
                if isinstance(node.op, ast.Div):
                    return IRType(name='float')
                # Both int = int
                if left_type and right_type and left_type.name == 'int' and right_type.name == 'int':
                    return IRType(name='int')
                # Default to float for numeric operations
                return IRType(name='float')

        # Comparison operations return bool
        elif isinstance(node, ast.Compare):
            return IRType(name='bool')

        # Boolean operations return bool
        elif isinstance(node, ast.BoolOp):
            return IRType(name='bool')

        # Lists
        elif isinstance(node, ast.List):
            if node.elts:
                # Infer element type from first element
                elem_type = self._infer_expr_type(node.elts[0])
                if elem_type:
                    return IRType(name='array', generic_args=[elem_type])
            return IRType(name='array', generic_args=[IRType(name='any')])

        # Dicts
        elif isinstance(node, ast.Dict):
            if node.keys and node.values:
                key_type = self._infer_expr_type(node.keys[0]) if node.keys[0] else IRType(name='string')
                value_type = self._infer_expr_type(node.values[0])
                if key_type and value_type:
                    return IRType(name='map', generic_args=[key_type, value_type])
            return IRType(name='map', generic_args=[IRType(name='string'), IRType(name='any')])

        # Identifiers - look up in context
        elif isinstance(node, ast.Name):
            if node.id in self.type_context:
                return IRType(name=self.type_context[node.id].pw_type)

        # Method calls - infer from method name
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                # String methods return string
                if node.func.attr in ('upper', 'lower', 'strip', 'lstrip', 'rstrip', 'replace',
                                       'split', 'join', 'format', 'capitalize', 'title', 'swapcase'):
                    return IRType(name='string')
                # Some string methods return bool
                elif node.func.attr in ('startswith', 'endswith', 'isdigit', 'isalpha', 'isalnum'):
                    return IRType(name='bool')
                # List methods that return list
                elif node.func.attr in ('append', 'extend', 'sort', 'reverse'):
                    # These modify in place, return None typically
                    return IRType(name='null')

        # Ternary expression
        elif isinstance(node, ast.IfExp):
            # Infer from both branches
            true_type = self._infer_expr_type(node.body)
            false_type = self._infer_expr_type(node.orelse)
            if true_type and false_type and true_type.name == false_type.name:
                return true_type
            # Mixed - use any
            return IRType(name='any')

        # Default: unknown
        return None

    def _infer_param_type_from_usage(self, param_name: str, func_node: ast.FunctionDef) -> IRType:
        """
        Infer parameter type from how it's used in the function body.

        Heuristics:
        1. Used in arithmetic -> numeric (int or float)
        2. Used in 'for x in param' -> param is array
        3. Property access (param.field) -> custom type
        4. String operations -> string
        """
        # Check for iteration (for x in param)
        for node in ast.walk(func_node):
            if isinstance(node, ast.For):
                if isinstance(node.iter, ast.Name) and node.iter.id == param_name:
                    # It's iterable - likely array
                    return IRType(name='array', generic_args=[IRType(name='any')])

        # Check for arithmetic usage
        for node in ast.walk(func_node):
            if isinstance(node, ast.BinOp):
                left_is_param = isinstance(node.left, ast.Name) and node.left.id == param_name
                right_is_param = isinstance(node.right, ast.Name) and node.right.id == param_name

                if left_is_param or right_is_param:
                    if isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod)):
                        # Used in arithmetic - likely numeric
                        # Default to int (can be float if we see division)
                        if isinstance(node.op, ast.Div):
                            return IRType(name='float')
                        return IRType(name='int')

        # Check for string operations BEFORE general property access
        # (param.upper(), param.split(), etc.)
        for node in ast.walk(func_node):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    # Check if it's a call on the parameter
                    obj = node.func.value
                    # Handle chained calls like param.upper().strip()
                    while isinstance(obj, ast.Call) and isinstance(obj.func, ast.Attribute):
                        obj = obj.func.value

                    if isinstance(obj, ast.Name) and obj.id == param_name:
                        # Common string methods
                        if node.func.attr in ('upper', 'lower', 'strip', 'lstrip', 'rstrip',
                                              'split', 'join', 'replace', 'startswith', 'endswith',
                                              'format', 'capitalize', 'title', 'swapcase',
                                              'isdigit', 'isalpha', 'isalnum'):
                            return IRType(name='string')
                    # Also check the immediate attribute access
                    elif isinstance(node.func.value, ast.Name) and node.func.value.id == param_name:
                        if node.func.attr in ('upper', 'lower', 'strip', 'lstrip', 'rstrip',
                                              'split', 'join', 'replace', 'startswith', 'endswith',
                                              'format', 'capitalize', 'title', 'swapcase',
                                              'isdigit', 'isalpha', 'isalnum'):
                            return IRType(name='string')

        # Check for property access (param.field) - after string methods
        # This is less specific, so check it last
        for node in ast.walk(func_node):
            if isinstance(node, ast.Attribute):
                if isinstance(node.value, ast.Name) and node.value.id == param_name:
                    # Has properties - it's a custom type
                    # For now, keep as 'any' but with better confidence
                    return IRType(name='any')

        # Default: keep as any
        return IRType(name='any')

    # ========================================================================
    # Statement Conversion
    # ========================================================================

    def _convert_statement(self, node: ast.stmt) -> Union[Optional[IRStatement], List[IRStatement]]:
        """
        Convert Python statement to IR statement.

        May return a list of statements for tuple unpacking assignments.
        """
        if isinstance(node, ast.If):
            return self._convert_if(node)
        elif isinstance(node, ast.For):
            return self._convert_for(node)
        elif isinstance(node, ast.While):
            return self._convert_while(node)
        elif isinstance(node, ast.Try):
            return self._convert_try(node)
        elif hasattr(ast, 'Match') and isinstance(node, ast.Match):
            return self._convert_match(node)
        elif isinstance(node, ast.Assign):
            return self._convert_assignment(node)
        elif isinstance(node, ast.AnnAssign):
            return self._convert_annotated_assignment(node)
        elif isinstance(node, ast.AugAssign):
            return self._convert_aug_assignment(node)
        elif isinstance(node, ast.Return):
            return self._convert_return(node)
        elif isinstance(node, ast.Raise):
            return self._convert_raise(node)
        elif isinstance(node, ast.Break):
            return IRBreak()
        elif isinstance(node, ast.Continue):
            return IRContinue()
        elif isinstance(node, ast.Pass):
            return IRPass()
        elif isinstance(node, ast.With):
            return self._convert_with(node)
        elif isinstance(node, ast.Expr):
            # Expression statement (like function call)
            expr = self._convert_expression(node.value)
            if isinstance(expr, IRCall):
                return expr

        return None

    def _convert_if(self, node: ast.If) -> IRIf:
        """Convert if statement to IR."""
        condition = self._convert_expression(node.test)

        then_body = []
        for stmt in node.body:
            ir_stmt = self._convert_statement(stmt)
            self._add_statement(then_body, ir_stmt)

        else_body = []
        for stmt in node.orelse:
            ir_stmt = self._convert_statement(stmt)
            self._add_statement(else_body, ir_stmt)

        return IRIf(
            condition=condition,
            then_body=then_body,
            else_body=else_body
        )

    def _convert_for(self, node: ast.For) -> IRFor:
        """Convert for loop to IR."""
        # Extract iterator variable
        if isinstance(node.target, ast.Name):
            iterator = node.target.id
        else:
            # Complex target (like tuple unpacking)
            iterator = "_iter"

        iterable = self._convert_expression(node.iter)

        body = []
        for stmt in node.body:
            ir_stmt = self._convert_statement(stmt)
            self._add_statement(body, ir_stmt)

        return IRFor(
            iterator=iterator,
            iterable=iterable,
            body=body
        )

    def _convert_while(self, node: ast.While) -> IRWhile:
        """Convert while loop to IR."""
        condition = self._convert_expression(node.test)

        body = []
        for stmt in node.body:
            ir_stmt = self._convert_statement(stmt)
            self._add_statement(body, ir_stmt)

        return IRWhile(
            condition=condition,
            body=body
        )

    def _convert_try(self, node: ast.Try) -> IRTry:
        """Convert try/except to IR."""
        try_body = []
        for stmt in node.body:
            ir_stmt = self._convert_statement(stmt)
            self._add_statement(try_body, ir_stmt)

        catch_blocks = []
        for handler in node.handlers:
            exception_type = None
            if handler.type:
                if isinstance(handler.type, ast.Name):
                    exception_type = handler.type.id

            exception_var = handler.name

            handler_body = []
            for stmt in handler.body:
                ir_stmt = self._convert_statement(stmt)
                self._add_statement(handler_body, ir_stmt)

            catch_blocks.append(IRCatch(
                exception_type=exception_type,
                exception_var=exception_var,
                body=handler_body
            ))

        finally_body = []
        for stmt in node.finalbody:
            ir_stmt = self._convert_statement(stmt)
            self._add_statement(finally_body, ir_stmt)

        return IRTry(
            try_body=try_body,
            catch_blocks=catch_blocks,
            finally_body=finally_body
        )

    def _convert_match(self, node) -> IRSwitch:
        """
        Convert Python 3.10+ match/case to IR switch statement.

        Example:
            match value:
                case 1:
                    return "one"
                case 2:
                    return "two"
                case _:
                    return "other"
        """
        # Subject expression (what we're matching on)
        subject = self._convert_expression(node.subject)

        cases = []
        for case in node.cases:
            # Check if this is a default case (wildcard pattern)
            is_default = False
            case_values = []

            # Pattern can be various types
            pattern = case.pattern
            if hasattr(ast, 'MatchAs') and isinstance(pattern, ast.MatchAs) and pattern.pattern is None:
                # This is the wildcard case (_)
                is_default = True
            elif hasattr(ast, 'MatchValue') and isinstance(pattern, ast.MatchValue):
                # Match a specific value
                case_values.append(self._convert_expression(pattern.value))
            elif hasattr(ast, 'MatchSingleton') and isinstance(pattern, ast.MatchSingleton):
                # Match None, True, False
                case_values.append(IRLiteral(value=pattern.value, literal_type=LiteralType.NULL if pattern.value is None else LiteralType.BOOLEAN))
            else:
                # For other patterns, treat as default
                is_default = True

            # Convert case body
            case_body = []
            for stmt in case.body:
                ir_stmt = self._convert_statement(stmt)
                self._add_statement(case_body, ir_stmt)

            cases.append(IRCase(
                values=case_values,
                body=case_body,
                is_default=is_default
            ))

        return IRSwitch(value=subject, cases=cases)

    def _convert_with(self, node: ast.With) -> IRWith:
        """
        Convert with statement (context manager) to IR.

        Example:
            with open("file.txt") as f:
                data = f.read()
        """
        # Python with can have multiple items, take the first one
        if not node.items:
            return IRWith(context_expr=IRIdentifier(name="unknown"), body=[])

        item = node.items[0]
        context_expr = self._convert_expression(item.context_expr)

        # Extract variable name from "as" clause
        variable = None
        if item.optional_vars:
            if isinstance(item.optional_vars, ast.Name):
                variable = item.optional_vars.id

        # Convert body
        body = []
        for stmt in node.body:
            ir_stmt = self._convert_statement(stmt)
            self._add_statement(body, ir_stmt)

        return IRWith(
            context_expr=context_expr,
            variable=variable,
            body=body
        )

    def _convert_assignment(self, node: ast.Assign) -> Union[IRAssignment, List[IRAssignment]]:
        """
        Convert assignment to IR.

        Returns either a single IRAssignment or a list of IRAssignments
        for tuple unpacking (e.g., cx, cy = width/2, height/2).
        """
        # Get target (first target for multiple assignment)
        target_name = ""
        if node.targets:
            target = node.targets[0]

            # Handle tuple unpacking: a, b = x, y
            if isinstance(target, ast.Tuple):
                return self._convert_tuple_assignment(node)

            if isinstance(target, ast.Name):
                target_name = target.id
            elif isinstance(target, ast.Attribute):
                # Property assignment like self.name = value
                # Convert to "self.name" string for now
                # In future, could support IRPropertyAccess as target
                obj_name = target.value.id if isinstance(target.value, ast.Name) else "self"
                target_name = f"{obj_name}.{target.attr}"

        value = self._convert_expression(node.value)

        # Infer type from value
        type_info = self.type_system.infer_from_expression(value, self.type_context)
        if target_name:  # Only update context if we have a simple name
            self.type_context[target_name] = type_info

        # Convert TypeInfo to IRType
        ir_type = self._type_info_to_ir_type(type_info)

        return IRAssignment(
            target=target_name,
            value=value,
            is_declaration=True,
            var_type=ir_type
        )

    def _convert_tuple_assignment(self, node: ast.Assign) -> List[IRAssignment]:
        """
        Convert tuple unpacking assignment to multiple IRAssignments.

        Example:
            cx, cy = width / 2, height / 2

        Becomes:
            cx = width / 2
            cy = height / 2
        """
        target = node.targets[0]
        if not isinstance(target, ast.Tuple):
            # Should never happen, but handle gracefully
            return [self._convert_assignment(node)]

        # Extract target variable names
        target_names = []
        for elt in target.elts:
            if isinstance(elt, ast.Name):
                target_names.append(elt.id)
            elif isinstance(elt, ast.Attribute):
                obj_name = elt.value.id if isinstance(elt.value, ast.Name) else "self"
                target_names.append(f"{obj_name}.{elt.attr}")
            else:
                # Unsupported target type, use empty string
                target_names.append("")

        # Extract value expressions
        values = []
        if isinstance(node.value, ast.Tuple):
            # Matching tuple: a, b = 1, 2
            for elt in node.value.elts:
                values.append(self._convert_expression(elt))
        else:
            # Single value (like unpacking a function return)
            # Create index accesses: a, b = func() -> a = func()[0], b = func()[1]
            base_value = self._convert_expression(node.value)
            for i in range(len(target_names)):
                values.append(IRIndex(
                    object=base_value,
                    index=IRLiteral(value=i, literal_type=LiteralType.INTEGER)
                ))

        # Ensure we have matching counts
        if len(target_names) != len(values):
            # Mismatch - create single assignment with tuple value
            return [IRAssignment(
                target=", ".join(target_names),
                value=self._convert_expression(node.value),
                is_declaration=True,
                var_type=IRType(name="any")
            )]

        # Create individual assignments
        assignments = []
        for target_name, value in zip(target_names, values):
            # Infer type from value
            type_info = self.type_system.infer_from_expression(value, self.type_context)
            if target_name and '.' not in target_name:
                self.type_context[target_name] = type_info

            # Convert TypeInfo to IRType
            ir_type = self._type_info_to_ir_type(type_info)

            assignments.append(IRAssignment(
                target=target_name,
                value=value,
                is_declaration=True,
                var_type=ir_type
            ))

        return assignments

    def _convert_annotated_assignment(self, node: ast.AnnAssign) -> IRAssignment:
        """Convert annotated assignment to IR."""
        target_name = ""
        if isinstance(node.target, ast.Name):
            target_name = node.target.id
        elif isinstance(node.target, ast.Attribute):
            # Property assignment like self.name: str = value
            obj_name = node.target.value.id if isinstance(node.target.value, ast.Name) else "self"
            target_name = f"{obj_name}.{node.target.attr}"

        var_type = self._convert_type_annotation(node.annotation)

        value = None
        if node.value:
            value = self._convert_expression(node.value)
        else:
            # No value, create null literal
            value = IRLiteral(value=None, literal_type=LiteralType.NULL)

        # Update type context (only for simple names)
        if target_name and '.' not in target_name:
            self.type_context[target_name] = TypeInfo(
                pw_type=var_type.name,
                confidence=1.0,
                source="explicit"
            )

        return IRAssignment(
            target=target_name,
            value=value,
            is_declaration=True,
            var_type=var_type
        )

    def _convert_aug_assignment(self, node: ast.AugAssign) -> IRAssignment:
        """Convert augmented assignment (+=, -=, etc.) to IR."""
        target_name = ""
        if isinstance(node.target, ast.Name):
            target_name = node.target.id

        # Convert to binary operation: x += 1 -> x = x + 1
        left = IRIdentifier(name=target_name)
        right = self._convert_expression(node.value)

        op = self._convert_binary_operator(node.op)
        value = IRBinaryOp(op=op, left=left, right=right)

        return IRAssignment(
            target=target_name,
            value=value,
            is_declaration=False
        )

    def _convert_return(self, node: ast.Return) -> IRReturn:
        """Convert return statement to IR."""
        value = None
        if node.value:
            value = self._convert_expression(node.value)

        return IRReturn(value=value)

    def _convert_raise(self, node: ast.Raise) -> IRThrow:
        """Convert raise statement to IR."""
        exception = self._convert_expression(node.exc)
        return IRThrow(exception=exception)

    # ========================================================================
    # Expression Conversion
    # ========================================================================

    def _convert_expression(self, node: ast.expr) -> Any:
        """Convert Python expression to IR expression."""
        if isinstance(node, ast.BinOp):
            return self._convert_binop(node)
        elif isinstance(node, ast.UnaryOp):
            return self._convert_unaryop(node)
        elif isinstance(node, ast.Compare):
            return self._convert_compare(node)
        elif isinstance(node, ast.BoolOp):
            return self._convert_boolop(node)
        elif isinstance(node, ast.Call):
            return self._convert_call(node)
        elif isinstance(node, ast.Attribute):
            return self._convert_attribute(node)
        elif isinstance(node, ast.Subscript):
            return self._convert_subscript(node)
        elif isinstance(node, ast.Name):
            return IRIdentifier(name=node.id)
        elif isinstance(node, (ast.Constant, ast.Num, ast.Str)):
            return self._convert_literal(node)
        elif isinstance(node, ast.List):
            return self._convert_list(node)
        elif isinstance(node, ast.Dict):
            return self._convert_dict(node)
        elif isinstance(node, ast.Lambda):
            return self._convert_lambda(node)
        elif isinstance(node, ast.IfExp):
            return self._convert_ternary(node)
        elif isinstance(node, ast.ListComp):
            return self._convert_list_comprehension(node)
        elif isinstance(node, ast.DictComp):
            return self._convert_dict_comprehension(node)
        elif isinstance(node, ast.SetComp):
            return self._convert_set_comprehension(node)
        elif isinstance(node, ast.GeneratorExp):
            return self._convert_generator_expression(node)
        elif isinstance(node, ast.JoinedStr):
            return self._convert_fstring(node)
        elif isinstance(node, ast.Await):
            return self._convert_await(node)
        elif isinstance(node, ast.Tuple):
            # Convert tuple to array (for return values, etc.)
            elements = [self._convert_expression(elt) for elt in node.elts]
            return IRArray(elements=elements)

        # Default: return identifier
        return IRIdentifier(name="<unknown>")

    def _convert_binop(self, node: ast.BinOp) -> IRBinaryOp:
        """Convert binary operation to IR."""
        op = self._convert_binary_operator(node.op)
        left = self._convert_expression(node.left)
        right = self._convert_expression(node.right)

        return IRBinaryOp(op=op, left=left, right=right)

    def _convert_binary_operator(self, op: ast.operator) -> BinaryOperator:
        """Convert Python operator to IR binary operator."""
        mapping = {
            ast.Add: BinaryOperator.ADD,
            ast.Sub: BinaryOperator.SUBTRACT,
            ast.Mult: BinaryOperator.MULTIPLY,
            ast.Div: BinaryOperator.DIVIDE,
            ast.Mod: BinaryOperator.MODULO,
            ast.Pow: BinaryOperator.POWER,
            ast.BitAnd: BinaryOperator.BIT_AND,
            ast.BitOr: BinaryOperator.BIT_OR,
            ast.BitXor: BinaryOperator.BIT_XOR,
            ast.LShift: BinaryOperator.LEFT_SHIFT,
            ast.RShift: BinaryOperator.RIGHT_SHIFT,
        }
        return mapping.get(type(op), BinaryOperator.ADD)

    def _convert_unaryop(self, node: ast.UnaryOp) -> IRUnaryOp:
        """Convert unary operation to IR."""
        op_mapping = {
            ast.Not: UnaryOperator.NOT,
            ast.USub: UnaryOperator.NEGATE,
            ast.UAdd: UnaryOperator.POSITIVE,
            ast.Invert: UnaryOperator.BIT_NOT,
        }
        op = op_mapping.get(type(node.op), UnaryOperator.NOT)
        operand = self._convert_expression(node.operand)

        return IRUnaryOp(op=op, operand=operand)

    def _convert_compare(self, node: ast.Compare) -> IRBinaryOp:
        """Convert comparison to IR binary operation."""
        # Handle simple comparisons (a < b)
        if len(node.ops) == 1:
            op_mapping = {
                ast.Eq: BinaryOperator.EQUAL,
                ast.NotEq: BinaryOperator.NOT_EQUAL,
                ast.Lt: BinaryOperator.LESS_THAN,
                ast.LtE: BinaryOperator.LESS_EQUAL,
                ast.Gt: BinaryOperator.GREATER_THAN,
                ast.GtE: BinaryOperator.GREATER_EQUAL,
                ast.In: BinaryOperator.IN,
                ast.NotIn: BinaryOperator.NOT_IN,
                ast.Is: BinaryOperator.IS,
                ast.IsNot: BinaryOperator.IS_NOT,
            }
            op = op_mapping.get(type(node.ops[0]), BinaryOperator.EQUAL)
            left = self._convert_expression(node.left)
            right = self._convert_expression(node.comparators[0])

            return IRBinaryOp(op=op, left=left, right=right)

        # Complex chained comparison (a < b < c)
        # Convert to: (a < b) and (b < c)
        # For now, simplify to first comparison
        return self._convert_compare(
            ast.Compare(left=node.left, ops=[node.ops[0]], comparators=[node.comparators[0]])
        )

    def _convert_boolop(self, node: ast.BoolOp) -> IRBinaryOp:
        """Convert boolean operation (and/or) to IR."""
        op = BinaryOperator.AND if isinstance(node.op, ast.And) else BinaryOperator.OR

        # Combine all values with the operator
        result = self._convert_expression(node.values[0])
        for value in node.values[1:]:
            right = self._convert_expression(value)
            result = IRBinaryOp(op=op, left=result, right=right)

        return result

    def _convert_call(self, node: ast.Call) -> IRCall:
        """Convert function call to IR."""
        function = self._convert_expression(node.func)

        args = [self._convert_expression(arg) for arg in node.args]

        kwargs = {}
        for keyword in node.keywords:
            if keyword.arg:
                kwargs[keyword.arg] = self._convert_expression(keyword.value)

        return IRCall(function=function, args=args, kwargs=kwargs)

    def _convert_attribute(self, node: ast.Attribute) -> IRPropertyAccess:
        """Convert attribute access to IR."""
        obj = self._convert_expression(node.value)
        return IRPropertyAccess(object=obj, property=node.attr)

    def _convert_subscript(self, node: ast.Subscript) -> IRIndex:
        """Convert subscript to IR."""
        obj = self._convert_expression(node.value)
        index = self._convert_expression(node.slice)
        return IRIndex(object=obj, index=index)

    def _convert_literal(self, node: Union[ast.Constant, ast.Num, ast.Str]) -> IRLiteral:
        """Convert literal value to IR."""
        if isinstance(node, ast.Constant):
            value = node.value
        elif isinstance(node, ast.Num):
            value = node.n
        elif isinstance(node, ast.Str):
            value = node.s
        else:
            value = None

        # Determine literal type
        if value is None:
            lit_type = LiteralType.NULL
        elif isinstance(value, bool):
            lit_type = LiteralType.BOOLEAN
        elif isinstance(value, int):
            lit_type = LiteralType.INTEGER
        elif isinstance(value, float):
            lit_type = LiteralType.FLOAT
        elif isinstance(value, str):
            lit_type = LiteralType.STRING
        else:
            lit_type = LiteralType.STRING

        return IRLiteral(value=value, literal_type=lit_type)

    def _convert_list(self, node: ast.List) -> IRArray:
        """Convert list to IR array."""
        elements = [self._convert_expression(elt) for elt in node.elts]
        return IRArray(elements=elements)

    def _convert_dict(self, node: ast.Dict) -> IRMap:
        """Convert dict to IR map."""
        entries = {}
        for key, value in zip(node.keys, node.values):
            if isinstance(key, (ast.Constant, ast.Str)):
                key_str = self._get_constant_value(key)
                entries[str(key_str)] = self._convert_expression(value)

        return IRMap(entries=entries)

    def _convert_lambda(self, node: ast.Lambda) -> IRLambda:
        """Convert lambda to IR."""
        params = []
        for arg in node.args.args:
            param_type = IRType(name="any")
            if arg.annotation:
                param_type = self._convert_type_annotation(arg.annotation)

            params.append(IRParameter(
                name=arg.arg,
                param_type=param_type
            ))

        # Lambda body is a single expression
        body = self._convert_expression(node.body)

        return IRLambda(params=params, body=body)

    def _convert_ternary(self, node: ast.IfExp) -> IRTernary:
        """Convert ternary expression to IR."""
        condition = self._convert_expression(node.test)
        true_value = self._convert_expression(node.body)
        false_value = self._convert_expression(node.orelse)

        return IRTernary(
            condition=condition,
            true_value=true_value,
            false_value=false_value
        )

    def _convert_list_comprehension(self, node: ast.ListComp) -> IRComprehension:
        """
        Convert list comprehension to IR.

        Example: [x*2 for x in items if x > 0] -> IRComprehension(...)
        """
        gen = node.generators[0]
        iterable = self._convert_expression(gen.iter)
        target = self._convert_expression(node.elt)
        iterator_var = gen.target.id if isinstance(gen.target, ast.Name) else "_item"

        # Handle filter condition if present
        condition = None
        if gen.ifs:
            condition = self._convert_expression(gen.ifs[0])

        return IRComprehension(
            target=target,
            iterator=iterator_var,
            iterable=iterable,
            condition=condition,
            comprehension_type="list"
        )

    def _convert_dict_comprehension(self, node: ast.DictComp) -> IRComprehension:
        """
        Convert dict comprehension to IR.

        Example: {k: v for k, v in items} -> IRComprehension with type=dict
        """
        gen = node.generators[0]
        iterable = self._convert_expression(gen.iter)

        # For dict comprehensions, target is a map with key and value
        key_expr = self._convert_expression(node.key)
        value_expr = self._convert_expression(node.value)

        # Create a map target representing the key-value pair
        target = IRMap(entries={"__key__": key_expr, "__value__": value_expr})

        iterator_var = gen.target.id if isinstance(gen.target, ast.Name) else "_item"

        # Handle filter condition if present
        condition = None
        if gen.ifs:
            condition = self._convert_expression(gen.ifs[0])

        return IRComprehension(
            target=target,
            iterator=iterator_var,
            iterable=iterable,
            condition=condition,
            comprehension_type="dict"
        )

    def _convert_set_comprehension(self, node: ast.SetComp) -> IRComprehension:
        """
        Convert set comprehension to IR.

        Example: {x*2 for x in items} -> IRComprehension with type=set
        """
        gen = node.generators[0]
        iterable = self._convert_expression(gen.iter)
        target = self._convert_expression(node.elt)
        iterator_var = gen.target.id if isinstance(gen.target, ast.Name) else "_item"

        # Handle filter condition if present
        condition = None
        if gen.ifs:
            condition = self._convert_expression(gen.ifs[0])

        return IRComprehension(
            target=target,
            iterator=iterator_var,
            iterable=iterable,
            condition=condition,
            comprehension_type="set"
        )

    def _convert_generator_expression(self, node: ast.GeneratorExp) -> IRComprehension:
        """
        Convert generator expression to IR.

        Example: (x*2 for x in items) -> IRComprehension with type=generator
        """
        gen = node.generators[0]
        iterable = self._convert_expression(gen.iter)
        target = self._convert_expression(node.elt)
        iterator_var = gen.target.id if isinstance(gen.target, ast.Name) else "_item"

        # Handle filter condition if present
        condition = None
        if gen.ifs:
            condition = self._convert_expression(gen.ifs[0])

        return IRComprehension(
            target=target,
            iterator=iterator_var,
            iterable=iterable,
            condition=condition,
            comprehension_type="generator"
        )

    def _convert_fstring(self, node: ast.JoinedStr) -> Any:
        """
        Convert f-string to IR.

        Example: f"Hello, {name}!" -> IRFString with parts ["Hello, ", name, "!"]
        Example: f"x={x:.2f}" -> IRFString with parts ["x=", IRCall(format, [x, ".2f"])]
        """
        if not node.values:
            return IRLiteral(value="", literal_type=LiteralType.STRING)

        parts = []

        for value in node.values:
            if isinstance(value, ast.Constant):
                # Static string part
                parts.append(value.value)
            elif isinstance(value, ast.FormattedValue):
                # Interpolated expression
                expr = self._convert_expression(value.value)

                # Handle format specifiers (:.2f, :03d, etc.)
                if value.format_spec:
                    # Extract format spec string
                    format_str = ""
                    if isinstance(value.format_spec, ast.JoinedStr):
                        for spec_val in value.format_spec.values:
                            if isinstance(spec_val, ast.Constant):
                                format_str += spec_val.value

                    # Store format spec as metadata in IRFString
                    # For now, we'll use a call to toFixed() for numbers
                    if format_str.endswith('f'):
                        # Extract decimal places from format like '.2f'
                        if format_str.startswith('.') and len(format_str) > 2:
                            try:
                                decimals = int(format_str[1:-1])
                                # Create a toFixed() call for JavaScript
                                expr = IRCall(
                                    function=IRPropertyAccess(
                                        object=expr,
                                        property="toFixed"
                                    ),
                                    args=[IRLiteral(value=decimals, literal_type=LiteralType.INTEGER)]
                                )
                            except ValueError:
                                pass  # Invalid format, use expr as-is

                parts.append(expr)
            else:
                # Fallback for unknown types
                parts.append("")

        return IRFString(parts=parts)

    def _convert_await(self, node: ast.Await) -> IRAwait:
        """
        Convert await expression to IR.

        Example:
            await fetch_data() -> IRAwait(expression=IRCall(...))
        """
        expression = self._convert_expression(node.value)
        return IRAwait(expression=expression)

    # ========================================================================
    # Type Annotation Conversion
    # ========================================================================

    def _convert_type_annotation(self, annotation: ast.expr) -> IRType:
        """Convert Python type annotation to IR type."""
        if isinstance(annotation, ast.Name):
            # Simple type: int, str, etc.
            return self._normalize_python_type(annotation.id)

        elif isinstance(annotation, ast.Subscript):
            # Generic type: List[int], Dict[str, int], Optional[str]
            if isinstance(annotation.value, ast.Name):
                base_type = annotation.value.id

                # Handle Optional[T] -> T?
                if base_type == 'Optional':
                    inner_type = self._convert_type_annotation(annotation.slice)
                    inner_type.is_optional = True
                    return inner_type

                # Handle Union[A, B, C]
                elif base_type == 'Union':
                    # Extract union types
                    if isinstance(annotation.slice, ast.Tuple):
                        types = [self._convert_type_annotation(t) for t in annotation.slice.elts]
                        first = types[0]
                        first.union_types = types[1:]
                        return first
                    else:
                        return self._convert_type_annotation(annotation.slice)

                # Handle List[T]
                elif base_type in ('List', 'list'):
                    inner_type = self._convert_type_annotation(annotation.slice)
                    return IRType(name="array", generic_args=[inner_type])

                # Handle Dict[K, V]
                elif base_type in ('Dict', 'dict'):
                    if isinstance(annotation.slice, ast.Tuple):
                        key_type = self._convert_type_annotation(annotation.slice.elts[0])
                        value_type = self._convert_type_annotation(annotation.slice.elts[1])
                        return IRType(name="map", generic_args=[key_type, value_type])

        elif isinstance(annotation, ast.Constant):
            # String annotation (forward reference)
            return IRType(name=str(annotation.value))

        # Default to any
        return IRType(name="any")

    def _normalize_python_type(self, type_name: str) -> IRType:
        """Normalize Python type name to IR type."""
        type_mapping = {
            'str': 'string',
            'int': 'int',
            'float': 'float',
            'bool': 'bool',
            'None': 'null',
            'Any': 'any',
            'list': 'array',
            'dict': 'map',
        }

        normalized = type_mapping.get(type_name, type_name)
        return IRType(name=normalized)

    # ========================================================================
    # Utility Methods
    # ========================================================================

    def _get_constant_value(self, node: ast.expr) -> Any:
        """Get the constant value from an AST node."""
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.Num):
            return node.n
        elif isinstance(node, ast.Str):
            return node.s
        return None

    def _get_full_name(self, node: ast.Attribute) -> str:
        """
        Get full dotted name from Attribute node.

        Example:
            abc.abstractmethod → "abc.abstractmethod"
            pytest.mark.skip → "pytest.mark.skip"
        """
        parts = []
        current = node

        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value

        if isinstance(current, ast.Name):
            parts.append(current.id)

        return ".".join(reversed(parts))


# ============================================================================
# Convenience Functions
# ============================================================================


def parse_python_file(file_path: str) -> IRModule:
    """
    Parse a Python file into IR.

    Args:
        file_path: Path to Python file

    Returns:
        IRModule containing the parsed code

    Example:
        >>> module = parse_python_file("mycode.py")
        >>> print(f"Module: {module.name}")
        >>> print(f"Functions: {len(module.functions)}")
    """
    parser = PythonParserV2()
    return parser.parse_file(file_path)


def parse_python_source(source: str, module_name: str = "module") -> IRModule:
    """
    Parse Python source code into IR.

    Args:
        source: Python source code
        module_name: Name for the module

    Returns:
        IRModule containing the parsed code

    Example:
        >>> source = '''
        ... def add(a: int, b: int) -> int:
        ...     return a + b
        ... '''
        >>> module = parse_python_source(source)
        >>> print(module.functions[0].name)  # "add"
    """
    parser = PythonParserV2()
    return parser.parse_source(source, module_name)
