"""
Node.js Parser V2: Arbitrary JavaScript/TypeScript → IR

Parses arbitrary JavaScript and TypeScript code into Promptware IR.
Supports:
- Functions (regular, arrow, async)
- Classes (properties, methods, constructor)
- TypeScript type annotations
- ES6+ features (destructuring, arrow functions, etc.)
- Async/await patterns
- Modules (import/export)

Strategy:
- Regex-based parsing (no external dependencies)
- TypeScript type extraction
- Type inference for JavaScript
- AST-like transformation to IR
"""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from dsl.ir import (
    BinaryOperator,
    IRArray,
    IRAssignment,
    IRAwait,
    IRBinaryOp,
    IRCall,
    IRCatch,
    IRClass,
    IRComprehension,
    IRExpression,
    IRFunction,
    IRIdentifier,
    IRIf,
    IRImport,
    IRLiteral,
    IRMap,
    IRModule,
    IRParameter,
    IRProperty,
    IRPropertyAccess,
    IRReturn,
    IRStatement,
    IRThrow,
    IRTry,
    IRType,
    IRUnaryOp,
    IRWhile,
    LiteralType,
    SourceLocation,
    UnaryOperator,
)
from dsl.type_system import TypeSystem


class NodeJSParserV2:
    """Parse arbitrary JavaScript/TypeScript code → IR."""

    def __init__(self):
        self.type_system = TypeSystem()
        self.current_file: Optional[str] = None
        self.source_lines: List[str] = []

    # ========================================================================
    # Main Entry Points
    # ========================================================================

    def parse_file(self, file_path: str) -> IRModule:
        """
        Parse JavaScript/TypeScript file → IR module.

        Args:
            file_path: Path to .js or .ts file

        Returns:
            IR module representation
        """
        self.current_file = file_path
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()

        self.source_lines = source.split('\n')
        return self.parse_source(source, Path(file_path).stem)

    def parse_source(self, source: str, module_name: str = "module") -> IRModule:
        """
        Parse JavaScript/TypeScript source code → IR module.

        Args:
            source: JavaScript/TypeScript source code
            module_name: Module name

        Returns:
            IR module representation
        """
        # Remove comments (preserve for later metadata extraction)
        source_no_comments = self._remove_comments(source)

        # Extract components
        imports = self._extract_imports(source_no_comments)
        functions = self._extract_functions(source_no_comments)
        classes = self._extract_classes(source_no_comments)

        return IRModule(
            name=module_name,
            version="1.0.0",
            imports=imports,
            functions=functions,
            classes=classes,
        )

    # ========================================================================
    # Import Extraction
    # ========================================================================

    def _extract_imports(self, source: str) -> List[IRImport]:
        """Extract import/require statements."""
        imports = []

        # Match: import { a, b } from 'module'
        pattern1 = r"import\s+\{([^}]+)\}\s+from\s+['\"]([^'\"]+)['\"]"
        for match in re.finditer(pattern1, source):
            items_str = match.group(1)
            module = match.group(2)
            items = [item.strip() for item in items_str.split(',')]
            imports.append(IRImport(module=module, items=items))

        # Match: import module from 'module'
        pattern2 = r"import\s+(\w+)\s+from\s+['\"]([^'\"]+)['\"]"
        for match in re.finditer(pattern2, source):
            alias = match.group(1)
            module = match.group(2)
            imports.append(IRImport(module=module, alias=alias))

        # Match: const module = require('module')
        pattern3 = r"const\s+(\w+)\s+=\s+require\(['\"]([^'\"]+)['\"]\)"
        for match in re.finditer(pattern3, source):
            alias = match.group(1)
            module = match.group(2)
            imports.append(IRImport(module=module, alias=alias))

        return imports

    # ========================================================================
    # Function Extraction
    # ========================================================================

    def _extract_functions(self, source: str) -> List[IRFunction]:
        """Extract all function definitions."""
        functions = []

        # Pattern 1: Regular function declarations
        # function name(params) { ... }
        # async function name(params): ReturnType { ... }
        pattern1 = r'(async\s+)?function\s+(\w+)\s*\(([^)]*)\)(?:\s*:\s*([^{]+))?\s*\{'
        for match in re.finditer(pattern1, source):
            is_async = bool(match.group(1))
            name = match.group(2)
            params_str = match.group(3)
            return_type_str = match.group(4)

            # Extract function body
            body_start = match.end()
            body = self._extract_block_body(source, body_start - 1)

            # Parse parameters
            params = self._parse_parameters(params_str)

            # Parse return type
            return_type = None
            if return_type_str:
                return_type = self._parse_type(return_type_str.strip())

            # Parse body statements
            body_stmts = self._parse_statements(body)

            func = IRFunction(
                name=name,
                params=params,
                return_type=return_type,
                body=body_stmts,
                is_async=is_async,
            )
            functions.append(func)

        # Pattern 2: Arrow functions assigned to const/let/var
        # const name = (params) => expr
        # const name = async (params): ReturnType => { ... }
        pattern2 = r'(?:const|let|var)\s+(\w+)\s*=\s*(async\s+)?\(([^)]*)\)(?:\s*:\s*([^=]+))?\s*=>\s*'
        for match in re.finditer(pattern2, source):
            name = match.group(1)
            is_async = bool(match.group(2))
            params_str = match.group(3)
            return_type_str = match.group(4)

            # Check if arrow function has body block or single expression
            after_arrow = source[match.end():]
            if after_arrow.strip().startswith('{'):
                # Block body
                body_start = match.end() + after_arrow.index('{')
                body = self._extract_block_body(source, body_start)
                body_stmts = self._parse_statements(body)
            else:
                # Single expression - extract until semicolon or newline
                expr_match = re.match(r'([^;\n]+)', after_arrow)
                if expr_match:
                    expr_str = expr_match.group(1).strip()
                    expr = self._parse_expression(expr_str)
                    body_stmts = [IRReturn(value=expr)]
                else:
                    body_stmts = []

            # Parse parameters
            params = self._parse_parameters(params_str)

            # Parse return type
            return_type = None
            if return_type_str:
                return_type = self._parse_type(return_type_str.strip())

            func = IRFunction(
                name=name,
                params=params,
                return_type=return_type,
                body=body_stmts,
                is_async=is_async,
            )
            functions.append(func)

        return functions

    # ========================================================================
    # Class Extraction
    # ========================================================================

    def _extract_classes(self, source: str) -> List[IRClass]:
        """Extract all class definitions."""
        classes = []

        # Pattern: class Name { ... }
        pattern = r'class\s+(\w+)(?:\s+extends\s+(\w+))?\s*\{'
        for match in re.finditer(pattern, source):
            name = match.group(1)
            base_class = match.group(2)

            # Extract class body
            body_start = match.end() - 1
            body = self._extract_block_body(source, body_start)

            # Parse properties and methods
            properties = self._extract_class_properties(body)
            methods = self._extract_class_methods(body)
            constructor = self._extract_constructor(body)

            cls = IRClass(
                name=name,
                properties=properties,
                methods=methods,
                constructor=constructor,
                base_classes=[base_class] if base_class else [],
            )
            classes.append(cls)

        return classes

    def _extract_class_properties(self, class_body: str) -> List[IRProperty]:
        """Extract class property declarations."""
        properties = []

        # TypeScript property declarations: [visibility] name: type;
        # Matches: name: type; or private/public/protected name: type;
        pattern = r'^\s*(?:private|public|protected|readonly)?\s*(\w+)\s*:\s*([^;=]+);'
        for match in re.finditer(pattern, class_body, re.MULTILINE):
            name = match.group(1)
            type_str = match.group(2).strip()

            # Skip if it looks like a method (has parentheses)
            if '(' in type_str:
                continue

            prop_type = self._parse_type(type_str)
            properties.append(IRProperty(name=name, prop_type=prop_type))

        return properties

    def _extract_class_methods(self, class_body: str) -> List[IRFunction]:
        """Extract class methods."""
        methods = []

        # Pattern: methodName(params): ReturnType { ... }
        # Skip constructor (handled separately)
        pattern = r'^\s*(async\s+)?(\w+)\s*\(([^)]*)\)(?:\s*:\s*([^{]+))?\s*\{'
        for match in re.finditer(pattern, class_body, re.MULTILINE):
            is_async = bool(match.group(1))
            name = match.group(2)

            # Skip constructor
            if name == 'constructor':
                continue

            params_str = match.group(3)
            return_type_str = match.group(4)

            # Extract method body (relative to class_body)
            method_start = match.start()
            method_source = class_body[method_start:]
            body_start = method_source.index('{')
            body = self._extract_block_body(method_source, body_start)

            # Parse parameters
            params = self._parse_parameters(params_str)

            # Parse return type
            return_type = None
            if return_type_str:
                return_type = self._parse_type(return_type_str.strip())

            # Parse body statements
            body_stmts = self._parse_statements(body)

            method = IRFunction(
                name=name,
                params=params,
                return_type=return_type,
                body=body_stmts,
                is_async=is_async,
            )
            methods.append(method)

        return methods

    def _extract_constructor(self, class_body: str) -> Optional[IRFunction]:
        """Extract class constructor."""
        # Pattern: constructor(params) { ... }
        pattern = r'constructor\s*\(([^)]*)\)\s*\{'
        match = re.search(pattern, class_body)
        if not match:
            return None

        params_str = match.group(1)

        # Extract constructor body
        body_start = match.end() - 1
        body = self._extract_block_body(class_body, body_start)

        # Parse parameters
        params = self._parse_parameters(params_str)

        # Parse body statements
        body_stmts = self._parse_statements(body)

        return IRFunction(
            name="constructor",
            params=params,
            return_type=None,
            body=body_stmts,
        )

    # ========================================================================
    # Parameter Parsing
    # ========================================================================

    def _parse_parameters(self, params_str: str) -> List[IRParameter]:
        """Parse function parameters from parameter list string."""
        if not params_str.strip():
            return []

        parameters = []
        # Split by comma (but be careful with nested generics)
        param_parts = self._split_by_comma(params_str)

        for part in param_parts:
            part = part.strip()
            if not part:
                continue

            # Parse: name: type = default
            # Or: name = default
            # Or: name: type
            # Or: name

            # Check for default value
            default_value = None
            if '=' in part:
                param_part, default_part = part.split('=', 1)
                param_part = param_part.strip()
                default_value = self._parse_expression(default_part.strip())
            else:
                param_part = part

            # Check for type annotation
            if ':' in param_part:
                name, type_str = param_part.split(':', 1)
                name = name.strip()
                param_type = self._parse_type(type_str.strip())
            else:
                name = param_part.strip()
                # Type inference from default value
                if default_value and isinstance(default_value, IRLiteral):
                    type_info = self.type_system.infer_from_literal(default_value)
                    param_type = IRType(name=type_info.pw_type)
                else:
                    param_type = IRType(name="any")

            parameters.append(
                IRParameter(
                    name=name,
                    param_type=param_type,
                    default_value=default_value,
                )
            )

        return parameters

    # ========================================================================
    # Statement Parsing
    # ========================================================================

    def _parse_statements(self, body: str) -> List[IRStatement]:
        """Parse function body into list of IR statements."""
        statements = []
        lines = body.split('\n')

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Skip empty lines and comments
            if not line or line.startswith('//'):
                i += 1
                continue

            # Variable assignment: const/let/var name = value OR const name: type = value
            if re.match(r'(const|let|var)\s+\w+(?:\s*:\s*[^=]+)?\s*=', line):
                stmt = self._parse_assignment(line)
                if stmt:
                    statements.append(stmt)
                i += 1
                continue

            # Re-assignment without declaration: name = value
            if re.match(r'\w+\s*=', line) and not line.startswith('return'):
                stmt = self._parse_reassignment(line)
                if stmt:
                    statements.append(stmt)
                i += 1
                continue

            # If statement
            if line.startswith('if'):
                stmt, lines_consumed = self._parse_if_statement('\n'.join(lines[i:]))
                if stmt:
                    statements.append(stmt)
                i += lines_consumed
                continue

            # While loop
            if line.startswith('while'):
                stmt, lines_consumed = self._parse_while_statement('\n'.join(lines[i:]))
                if stmt:
                    statements.append(stmt)
                i += lines_consumed
                continue

            # Try/catch/finally statement
            if line.startswith('try'):
                stmt, lines_consumed = self._parse_try_statement('\n'.join(lines[i:]))
                if stmt:
                    statements.append(stmt)
                i += lines_consumed
                continue

            # Throw statement
            if line.startswith('throw'):
                stmt = self._parse_throw(line)
                if stmt:
                    statements.append(stmt)
                i += 1
                continue

            # Return statement (may be multiline)
            if line.startswith('return'):
                # Check if return has a multiline object literal
                if '{' in line and '}' not in line:
                    # Multiline return - collect all lines until closing brace
                    full_return = [line]
                    i += 1
                    brace_depth = line.count('{') - line.count('}')
                    while i < len(lines) and brace_depth > 0:
                        next_line = lines[i]
                        full_return.append(next_line)
                        brace_depth += next_line.count('{') - next_line.count('}')
                        i += 1
                    stmt = self._parse_return('\n'.join(full_return))
                else:
                    stmt = self._parse_return(line)
                    i += 1
                if stmt:
                    statements.append(stmt)
                continue

            # Expression statement (function call, etc.)
            if ';' in line or not line.endswith(('{', '}')):
                expr = self._parse_expression(line.rstrip(';'))
                if expr and isinstance(expr, IRCall):
                    statements.append(expr)
                i += 1
                continue

            i += 1

        return statements

    def _parse_assignment(self, line: str) -> Optional[IRAssignment]:
        """Parse variable assignment statement."""
        # Pattern: const/let/var name = value OR const name: type = value
        match = re.match(r'(const|let|var)\s+(\w+)(?:\s*:\s*([^=]+))?\s*=\s*(.+);?$', line)
        if not match:
            return None

        name = match.group(2)
        # Group 3 is optional type annotation (we ignore it for now)
        value_str = match.group(4).rstrip(';')

        value = self._parse_expression(value_str)

        return IRAssignment(
            target=name,
            value=value,
            is_declaration=True,
        )

    def _parse_reassignment(self, line: str) -> Optional[IRAssignment]:
        """Parse variable re-assignment statement (without declaration)."""
        # Pattern: name = value
        match = re.match(r'(\w+)\s*=\s*(.+);?$', line)
        if not match:
            return None

        name = match.group(1)
        value_str = match.group(2).rstrip(';')

        value = self._parse_expression(value_str)

        return IRAssignment(
            target=name,
            value=value,
            is_declaration=False,
        )

    def _parse_if_statement(self, source: str) -> Tuple[Optional[IRIf], int]:
        """Parse if statement. Returns (statement, lines_consumed)."""
        # Pattern: if (condition) { ... } (allow leading whitespace)
        match = re.match(r'\s*if\s*\(([^)]+)\)\s*\{', source)
        if not match:
            return None, 1

        condition_str = match.group(1)
        condition = self._parse_expression(condition_str)

        # Extract if body
        body_start = match.end() - 1
        then_body_str = self._extract_block_body(source, body_start)
        then_body = self._parse_statements(then_body_str)

        # Check for else clause
        after_if = source[body_start + len(then_body_str) + 2:].lstrip()
        else_body = []
        lines_consumed = len(source[:body_start + len(then_body_str) + 2].split('\n'))

        if after_if.startswith('else'):
            if after_if[4:].lstrip().startswith('{'):
                # else { ... }
                else_start = after_if.index('{')
                else_body_str = self._extract_block_body(after_if, else_start)
                else_body = self._parse_statements(else_body_str)
                lines_consumed += len(else_body_str.split('\n'))

        return IRIf(condition=condition, then_body=then_body, else_body=else_body), lines_consumed

    def _parse_while_statement(self, source: str) -> Tuple[Optional[IRWhile], int]:
        """Parse while statement. Returns (statement, lines_consumed)."""
        # Pattern: while (condition) { ... } (allow leading whitespace)
        match = re.match(r'\s*while\s*\(([^)]+)\)\s*\{', source)
        if not match:
            return None, 1

        condition_str = match.group(1)
        condition = self._parse_expression(condition_str)

        # Extract while body
        body_start = match.end() - 1
        body_str = self._extract_block_body(source, body_start)
        body = self._parse_statements(body_str)

        lines_consumed = len(source[:body_start + len(body_str) + 2].split('\n'))

        return IRWhile(condition=condition, body=body), lines_consumed

    def _parse_try_statement(self, source: str) -> Tuple[Optional[IRTry], int]:
        """
        Parse try/catch/finally statement.

        Handles:
        - try { ... } catch (e) { ... }
        - try { ... } catch (e) { ... } finally { ... }
        - try { ... } finally { ... }

        Returns: (IRTry statement, lines_consumed)
        """
        # Pattern: try { ... }
        match = re.match(r'\s*try\s*\{', source)
        if not match:
            return None, 1

        # Extract try body
        try_start = match.end() - 1
        try_body_str = self._extract_block_body(source, try_start)
        try_body = self._parse_statements(try_body_str)

        # Track position after try block
        current_pos = try_start + len(try_body_str) + 2  # +2 for {}
        catch_blocks = []
        finally_body = []

        # Look for catch blocks
        remaining = source[current_pos:].lstrip()
        while remaining.startswith('catch'):
            # Pattern: catch (exception_var) { ... }
            catch_match = re.match(r'catch\s*\(([^)]+)\)\s*\{', remaining)
            if not catch_match:
                break

            exception_var = catch_match.group(1).strip()
            exception_type = None  # JavaScript doesn't have typed catch

            # Extract catch body
            catch_start = catch_match.end() - 1
            catch_body_str = self._extract_block_body(remaining, catch_start)
            catch_body = self._parse_statements(catch_body_str)

            catch_blocks.append(IRCatch(
                exception_type=exception_type,
                exception_var=exception_var,
                body=catch_body
            ))

            # Move position forward
            consumed = catch_start + len(catch_body_str) + 2
            current_pos += len(remaining[:consumed])
            remaining = source[current_pos:].lstrip()

        # Look for finally block
        if remaining.startswith('finally'):
            finally_match = re.match(r'finally\s*\{', remaining)
            if finally_match:
                finally_start = finally_match.end() - 1
                finally_body_str = self._extract_block_body(remaining, finally_start)
                finally_body = self._parse_statements(finally_body_str)

                # Update position
                current_pos += len(remaining[:finally_start + len(finally_body_str) + 2])

        # Calculate total lines consumed
        lines_consumed = len(source[:current_pos].split('\n'))

        return IRTry(
            try_body=try_body,
            catch_blocks=catch_blocks,
            finally_body=finally_body
        ), lines_consumed

    def _parse_return(self, line: str) -> Optional[IRReturn]:
        """Parse return statement (may be multiline)."""
        # Pattern: return value; (handle multiline)
        # Remove 'return' keyword and semicolon
        line = line.strip()
        if not line.startswith('return'):
            return IRReturn(value=None)

        value_str = line[6:].strip()  # Remove 'return'
        value_str = value_str.rstrip(';').strip()

        if not value_str:
            return IRReturn(value=None)

        value = self._parse_expression(value_str)
        return IRReturn(value=value)

    def _parse_throw(self, line: str) -> Optional[IRThrow]:
        """Parse throw statement."""
        # Pattern: throw expression;
        match = re.match(r'throw\s+(.*);?$', line)
        if not match:
            return None

        exception_str = match.group(1).rstrip(';')
        if not exception_str:
            return None

        exception = self._parse_expression(exception_str)
        return IRThrow(exception=exception)

    # ========================================================================
    # Collection Operations Parsing
    # ========================================================================

    def _parse_array_method_chain(self, expr_str: str) -> Optional[IRComprehension]:
        """
        Parse JavaScript array methods (.map, .filter) into IRComprehension.

        Patterns:
        - items.filter(x => x > 0)
        - items.map(x => x * 2)
        - items.filter(x => x > 0).map(x => x * 2)

        Returns:
            IRComprehension if detected, None otherwise
        """
        # Pattern 1: filter + map (most specific - check first)
        # items.filter(x => x > 0).map(x => x * 2)
        filter_map_pattern = r'(\w+)\.filter\((\w+)\s*=>\s*(.+?)\)\.map\((\w+)\s*=>\s*(.+?)\)'
        match = re.search(filter_map_pattern, expr_str)
        if match:
            iterable_name = match.group(1)
            filter_var = match.group(2)
            filter_condition = match.group(3).strip()
            map_var = match.group(4)
            map_expr = match.group(5).strip()

            return IRComprehension(
                target=self._parse_expression(map_expr),
                iterator=map_var,
                iterable=IRIdentifier(name=iterable_name),
                condition=self._parse_expression(filter_condition),
                comprehension_type="list"
            )

        # Pattern 2: map only
        # items.map(x => x * 2)
        map_pattern = r'(\w+)\.map\((\w+)\s*=>\s*(.+?)\)'
        match = re.search(map_pattern, expr_str)
        if match:
            iterable_name = match.group(1)
            iterator = match.group(2)
            transform_expr = match.group(3).strip()

            return IRComprehension(
                target=self._parse_expression(transform_expr),
                iterator=iterator,
                iterable=IRIdentifier(name=iterable_name),
                condition=None,
                comprehension_type="list"
            )

        # Pattern 3: filter only
        # items.filter(x => x > 0)
        filter_pattern = r'(\w+)\.filter\((\w+)\s*=>\s*(.+?)\)'
        match = re.search(filter_pattern, expr_str)
        if match:
            iterable_name = match.group(1)
            iterator = match.group(2)
            condition_expr = match.group(3).strip()

            return IRComprehension(
                target=IRIdentifier(name=iterator),  # Keep element as-is
                iterator=iterator,
                iterable=IRIdentifier(name=iterable_name),
                condition=self._parse_expression(condition_expr),
                comprehension_type="list"
            )

        return None

    # ========================================================================
    # Expression Parsing
    # ========================================================================

    def _parse_expression(self, expr_str: str) -> IRExpression:
        """Parse expression string into IR expression node."""
        expr_str = expr_str.strip()

        if not expr_str:
            return IRLiteral(value=None, literal_type=LiteralType.NULL)

        # Check for array method chains (collection operations)
        array_method = self._parse_array_method_chain(expr_str)
        if array_method:
            return array_method

        # Await expression: await expr
        if expr_str.startswith('await '):
            inner_expr_str = expr_str[6:].strip()
            inner_expr = self._parse_expression(inner_expr_str)
            return IRAwait(expression=inner_expr)

        # Unary operators: !x, -x, +x, ~x
        for op_char, op_enum in [
            ('!', UnaryOperator.NOT),
            ('-', UnaryOperator.NEGATE),
            ('+', UnaryOperator.POSITIVE),
            ('~', UnaryOperator.BIT_NOT),
        ]:
            if expr_str.startswith(op_char) and len(expr_str) > 1:
                # Make sure it's not a negative number literal
                if op_char == '-' and expr_str[1:].strip().replace('.', '', 1).isdigit():
                    break  # Let number literal handle it
                operand_str = expr_str[1:].strip()
                operand = self._parse_expression(operand_str)
                return IRUnaryOp(op=op_enum, operand=operand)

        # Literal: string
        if (expr_str.startswith('"') and expr_str.endswith('"')) or \
           (expr_str.startswith("'") and expr_str.endswith("'")):
            value = expr_str[1:-1]
            return IRLiteral(value=value, literal_type=LiteralType.STRING)

        # Literal: template string
        if expr_str.startswith('`') and expr_str.endswith('`'):
            value = expr_str[1:-1]
            return IRLiteral(value=value, literal_type=LiteralType.STRING)

        # Literal: number
        if re.match(r'^-?\d+$', expr_str):
            return IRLiteral(value=int(expr_str), literal_type=LiteralType.INTEGER)
        if re.match(r'^-?\d+\.\d+$', expr_str):
            return IRLiteral(value=float(expr_str), literal_type=LiteralType.FLOAT)

        # Literal: boolean
        if expr_str == 'true':
            return IRLiteral(value=True, literal_type=LiteralType.BOOLEAN)
        if expr_str == 'false':
            return IRLiteral(value=False, literal_type=LiteralType.BOOLEAN)

        # Literal: null/undefined
        if expr_str in ['null', 'undefined']:
            return IRLiteral(value=None, literal_type=LiteralType.NULL)

        # Array literal: [...]
        if expr_str.startswith('[') and expr_str.endswith(']'):
            return self._parse_array_literal(expr_str)

        # Object literal: {...}
        if expr_str.startswith('{') and expr_str.endswith('}'):
            return self._parse_object_literal(expr_str)

        # Function call: func(args)
        if '(' in expr_str and expr_str.endswith(')'):
            return self._parse_function_call(expr_str)

        # Binary operation: a + b, x === y, etc.
        for op_pattern, op_enum in [
            (r'\+', BinaryOperator.ADD),
            (r'-', BinaryOperator.SUBTRACT),
            (r'\*', BinaryOperator.MULTIPLY),
            (r'/', BinaryOperator.DIVIDE),
            (r'===', BinaryOperator.EQUAL),
            (r'!==', BinaryOperator.NOT_EQUAL),
            (r'==', BinaryOperator.EQUAL),
            (r'!=', BinaryOperator.NOT_EQUAL),
            (r'<=', BinaryOperator.LESS_EQUAL),
            (r'>=', BinaryOperator.GREATER_EQUAL),
            (r'<', BinaryOperator.LESS_THAN),
            (r'>', BinaryOperator.GREATER_THAN),
            (r'&&', BinaryOperator.AND),
            (r'\|\|', BinaryOperator.OR),
        ]:
            if re.search(rf'\s+{op_pattern}\s+', expr_str):
                return self._parse_binary_op(expr_str, op_pattern, op_enum)

        # Collection operation: array.filter().map(), etc.
        if '.filter(' in expr_str or '.map(' in expr_str:
            comp = self._parse_array_method_chain(expr_str)
            if comp:
                return comp

        # Property access: obj.prop
        if '.' in expr_str and '(' not in expr_str.split('.')[0]:
            parts = expr_str.split('.')
            obj = IRIdentifier(name=parts[0])
            for prop in parts[1:]:
                obj = IRPropertyAccess(object=obj, property=prop)
            return obj

        # Identifier
        if re.match(r'^[a-zA-Z_$][a-zA-Z0-9_$]*$', expr_str):
            return IRIdentifier(name=expr_str)

        # Default: return as identifier
        return IRIdentifier(name=expr_str)

    def _parse_array_literal(self, expr_str: str) -> IRArray:
        """Parse array literal: [1, 2, 3]"""
        inner = expr_str[1:-1].strip()
        if not inner:
            return IRArray(elements=[])

        elements = []
        for item in self._split_by_comma(inner):
            elements.append(self._parse_expression(item.strip()))

        return IRArray(elements=elements)

    def _parse_object_literal(self, expr_str: str) -> IRMap:
        """Parse object literal: {a: 1, b: 2}"""
        inner = expr_str[1:-1].strip()
        if not inner:
            return IRMap(entries={})

        entries = {}
        for item in self._split_by_comma(inner):
            item = item.strip()
            if ':' not in item:
                continue

            key, value = item.split(':', 1)
            key = key.strip()
            # Remove quotes from key if present
            if (key.startswith('"') and key.endswith('"')) or \
               (key.startswith("'") and key.endswith("'")):
                key = key[1:-1]

            entries[key] = self._parse_expression(value.strip())

        return IRMap(entries=entries)

    def _parse_function_call(self, expr_str: str) -> IRCall:
        """Parse function call: func(arg1, arg2) or new Func(args)"""
        paren_idx = expr_str.index('(')
        func_name = expr_str[:paren_idx].strip()
        args_str = expr_str[paren_idx + 1:-1].strip()

        # Handle 'new' keyword (constructor calls)
        if func_name.startswith('new '):
            func_name = func_name[4:].strip()  # Remove 'new ' prefix

        # Parse function (could be identifier or property access)
        function = self._parse_expression(func_name) if func_name else IRIdentifier(name="unknown")

        # Parse arguments
        args = []
        if args_str:
            for arg in self._split_by_comma(args_str):
                args.append(self._parse_expression(arg.strip()))

        return IRCall(function=function, args=args)

    def _parse_binary_op(self, expr_str: str, op_pattern: str, op_enum: BinaryOperator) -> IRBinaryOp:
        """Parse binary operation."""
        parts = re.split(rf'\s+{op_pattern}\s+', expr_str, 1)
        if len(parts) != 2:
            return IRIdentifier(name=expr_str)

        left = self._parse_expression(parts[0].strip())
        right = self._parse_expression(parts[1].strip())

        return IRBinaryOp(op=op_enum, left=left, right=right)

    # ========================================================================
    # Type Parsing
    # ========================================================================

    def _parse_type(self, type_str: str) -> IRType:
        """Parse TypeScript type annotation into IR type."""
        type_str = type_str.strip()

        # Handle Promise<T>
        if type_str.startswith('Promise<') and type_str.endswith('>'):
            inner = type_str[8:-1]
            inner_type = self._parse_type(inner)
            # For now, just return the inner type
            # In full implementation, we might have async return types
            return inner_type

        # Handle Array<T> or T[]
        if type_str.startswith('Array<') and type_str.endswith('>'):
            inner = type_str[6:-1]
            return IRType(name="array", generic_args=[self._parse_type(inner)])
        if type_str.endswith('[]'):
            inner = type_str[:-2]
            return IRType(name="array", generic_args=[self._parse_type(inner)])

        # Normalize TypeScript types to PW types
        type_map = {
            'string': 'string',
            'number': 'int',  # Could be float, but int is more common
            'boolean': 'bool',
            'any': 'any',
            'void': 'null',
            'null': 'null',
            'undefined': 'null',
        }

        pw_type = type_map.get(type_str.lower(), type_str)
        return IRType(name=pw_type)

    # ========================================================================
    # Utility Functions
    # ========================================================================

    def _extract_block_body(self, source: str, start_index: int) -> str:
        """
        Extract the body of a block (between { and matching }).

        Args:
            source: Source code
            start_index: Index of opening '{'

        Returns:
            Body text (without enclosing braces)
        """
        if start_index >= len(source) or source[start_index] != '{':
            return ""

        depth = 0
        i = start_index

        while i < len(source):
            if source[i] == '{':
                depth += 1
            elif source[i] == '}':
                depth -= 1
                if depth == 0:
                    return source[start_index + 1:i]
            i += 1

        return source[start_index + 1:]

    def _split_by_comma(self, text: str) -> List[str]:
        """
        Split text by comma, respecting nesting (parens, brackets, braces).

        Args:
            text: Text to split

        Returns:
            List of parts
        """
        parts = []
        current = []
        depth = 0

        for char in text:
            if char in '({[<':
                depth += 1
                current.append(char)
            elif char in ')}]>':
                depth -= 1
                current.append(char)
            elif char == ',' and depth == 0:
                parts.append(''.join(current))
                current = []
            else:
                current.append(char)

        if current:
            parts.append(''.join(current))

        return parts

    def _remove_comments(self, source: str) -> str:
        """Remove JavaScript comments from source."""
        # Remove single-line comments
        source = re.sub(r'//.*$', '', source, flags=re.MULTILINE)

        # Remove multi-line comments
        source = re.sub(r'/\*.*?\*/', '', source, flags=re.DOTALL)

        return source
