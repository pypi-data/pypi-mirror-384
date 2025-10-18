"""
.NET Parser V2 - Arbitrary C# Code to IR

This parser converts arbitrary C# code into Promptware IR, enabling universal
code translation. It handles:
- Classes and properties
- Methods and functions
- LINQ expressions (abstracted as operations)
- Async/await patterns
- Type inference and mapping

Strategy: Regex-based parsing for simplicity (no external dependencies).
For production use, consider Roslyn API via subprocess.

Design Principles:
1. Parse arbitrary C# (not just MCP servers)
2. Map C# types → IR types
3. Abstract LINQ as filter/map operations
4. Handle async/await
5. Preserve business logic
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from dsl.ir import (
    BinaryOperator,
    IRAssignment,
    IRAwait,
    IRBinaryOp,
    IRCall,
    IRClass,
    IRComprehension,
    IRFunction,
    IRIdentifier,
    IRIf,
    IRImport,
    IRLiteral,
    IRModule,
    IRParameter,
    IRProperty,
    IRPropertyAccess,
    IRReturn,
    IRType,
    IRFor,
    IRWhile,
    IRTry,
    IRCatch,
    IRThrow,
    IRArray,
    IRMap,
    LiteralType,
)
from dsl.type_system import TypeSystem


@dataclass
class ParseContext:
    """Context for parsing (track variables, types, etc.)."""

    current_class: Optional[str] = None
    current_method: Optional[str] = None
    variables: Dict[str, IRType] = None

    def __post_init__(self):
        if self.variables is None:
            self.variables = {}


class DotNetParserV2:
    """
    Parse arbitrary C# code into Promptware IR.

    Supports:
    - Classes and structs
    - Properties (auto-properties and full properties)
    - Methods and functions
    - LINQ expressions (abstracted as operations)
    - Async/await patterns
    - Control flow (if/for/while/try-catch)
    - Type inference

    Limitations:
    - Regex-based (not full C# parser)
    - Events and delegates abstracted
    - Complex generics simplified
    - No preprocessor directives
    """

    def __init__(self):
        self.type_system = TypeSystem()
        self.context = ParseContext()

    # ========================================================================
    # Main Entry Points
    # ========================================================================

    def parse_file(self, file_path: str) -> IRModule:
        """
        Parse C# file into IR module.

        Args:
            file_path: Path to .cs file

        Returns:
            IR module representation
        """
        path = Path(file_path)
        source = path.read_text()

        # Extract module name from namespace or filename
        module_name = self._extract_namespace(source) or path.stem

        return self.parse_source(source, module_name)

    def parse_source(self, source: str, module_name: str = "module") -> IRModule:
        """
        Parse C# source code into IR module.

        Args:
            source: C# source code
            module_name: Module name

        Returns:
            IR module representation
        """
        # Clean source (remove comments)
        source = self._remove_comments(source)

        # Extract components
        imports = self._extract_imports(source)
        classes = self._extract_classes(source)
        functions = self._extract_standalone_functions(source)

        return IRModule(
            name=module_name,
            version="1.0.0",
            imports=imports,
            classes=classes,
            functions=functions
        )

    # ========================================================================
    # Import Extraction
    # ========================================================================

    def _extract_imports(self, source: str) -> List[IRImport]:
        """Extract using directives as imports."""
        imports = []

        # Pattern: using System.Collections.Generic;
        # Pattern: using static System.Math;
        # Pattern: using Alias = System.Collections.Generic.List<int>;

        using_pattern = re.compile(
            r'using\s+(?:static\s+)?(?:(\w+)\s*=\s*)?([a-zA-Z0-9_.]+)\s*;'
        )

        for match in using_pattern.finditer(source):
            alias = match.group(1)  # Alias (if any)
            module_path = match.group(2)  # Full namespace/type path

            # Extract module name (last part of path)
            module_name = module_path.split('.')[-1]

            imports.append(IRImport(
                module=module_name,
                alias=alias
            ))

        return imports

    def _extract_namespace(self, source: str) -> Optional[str]:
        """Extract namespace declaration."""
        # Pattern: namespace MyApp.Services
        match = re.search(r'namespace\s+([a-zA-Z0-9_.]+)', source)
        return match.group(1) if match else None

    # ========================================================================
    # Class Extraction
    # ========================================================================

    def _extract_classes(self, source: str) -> List[IRClass]:
        """Extract all class definitions."""
        classes = []

        # Pattern: public class User { ... }
        # Pattern: public class User : BaseClass { ... }
        class_pattern = re.compile(
            r'(public|private|internal|protected)?\s*'
            r'(?:static\s+)?(?:abstract\s+)?(?:sealed\s+)?'
            r'class\s+(\w+)'
            r'(?:\s*:\s*([^{]+))?'  # Base classes
            r'\s*\{',
            re.MULTILINE
        )

        for match in class_pattern.finditer(source):
            access = match.group(1) or 'internal'
            class_name = match.group(2)
            base_classes_str = match.group(3)

            # Extract class body
            class_start = match.end()
            class_body = self._extract_block(source, class_start - 1)  # Start at {

            # Parse base classes
            base_classes = []
            if base_classes_str:
                base_classes = [b.strip() for b in base_classes_str.split(',')]

            # Update context
            old_class = self.context.current_class
            self.context.current_class = class_name

            # Extract class members
            properties = self._extract_properties(class_body)
            methods = self._extract_methods(class_body)
            constructor = self._extract_constructor(class_body, class_name)

            # Restore context
            self.context.current_class = old_class

            classes.append(IRClass(
                name=class_name,
                properties=properties,
                methods=methods,
                constructor=constructor,
                base_classes=base_classes
            ))

        return classes

    def _extract_properties(self, class_body: str) -> List[IRProperty]:
        """Extract properties from class body."""
        properties = []

        # Pattern: public string Name { get; set; }
        # Pattern: public int Age { get; private set; }
        # Pattern: private readonly string _name;

        # Auto-properties (handle complex types better)
        auto_prop_pattern = re.compile(
            r'(public|private|protected|internal)\s+'
            r'(?:static\s+)?(?:readonly\s+)?'
            r'([a-zA-Z0-9_<>,\[\]\s?]+?)\s+'  # Type (allow spaces, ?, for generics and nullables)
            r'(\w+)\s*'  # Name
            r'\{\s*get\s*;\s*(?:(?:private|protected|internal)\s+)?set\s*;\s*\}',
            re.MULTILINE
        )

        for match in auto_prop_pattern.finditer(class_body):
            access = match.group(1)
            type_str = match.group(2).strip()
            prop_name = match.group(3)

            # Parse type
            prop_type = self._parse_type(type_str)

            properties.append(IRProperty(
                name=prop_name,
                prop_type=prop_type,
                is_private=(access in ['private', 'protected'])
            ))

        # Field declarations (fallback)
        field_pattern = re.compile(
            r'(public|private|protected|internal)\s+'
            r'(?:static\s+)?(?:readonly\s+)?'
            r'([a-zA-Z0-9_<>,\[\]]+)\s+'  # Type
            r'(\w+)\s*(?:=|;)'  # Name
        )

        for match in field_pattern.finditer(class_body):
            access = match.group(1)
            type_str = match.group(2)
            field_name = match.group(3)

            # Skip if already added as property
            if any(p.name == field_name for p in properties):
                continue

            # Parse type
            field_type = self._parse_type(type_str)

            properties.append(IRProperty(
                name=field_name,
                prop_type=field_type,
                is_private=(access in ['private', 'protected'])
            ))

        return properties

    def _extract_constructor(self, class_body: str, class_name: str) -> Optional[IRFunction]:
        """Extract constructor."""
        # Pattern: public User(string name, int age) { ... }
        ctor_pattern = re.compile(
            rf'(public|private|protected|internal)\s+'
            rf'{class_name}\s*'
            r'\(([^)]*)\)\s*'
            r'(?::\s*(?:base|this)\([^)]*\)\s*)?'  # Base/this call
            r'\s*\{{',  # Allow whitespace before {
            re.MULTILINE
        )

        match = ctor_pattern.search(class_body)
        if not match:
            return None

        params_str = match.group(2)

        # Extract constructor body
        ctor_start = match.end()
        ctor_body = self._extract_block(class_body, ctor_start - 1)

        # Parse parameters
        params = self._parse_parameters(params_str)

        # Parse body
        body_stmts = self._parse_statements(ctor_body)

        return IRFunction(
            name=class_name,  # Constructor name same as class
            params=params,
            return_type=None,  # Constructors don't have return type
            body=body_stmts
        )

    def _extract_methods(self, class_body: str) -> List[IRFunction]:
        """Extract methods from class body."""
        methods = []

        # Pattern: public async Task<string> GetData(int id) { ... }
        # Pattern: public void Process() { ... }
        method_pattern = re.compile(
            r'(public|private|protected|internal)\s+'
            r'(?:static\s+)?(?:virtual\s+)?(?:override\s+)?'
            r'(async\s+)?'  # Capture async
            r'([a-zA-Z0-9_<>,\[\]\s]+?)\s+'  # Return type (allow spaces for generics)
            r'(\w+)\s*'  # Method name
            r'\(([^)]*)\)\s*'  # Parameters
            r'\{',
            re.MULTILINE
        )

        for match in method_pattern.finditer(class_body):
            access = match.group(1)
            async_keyword = match.group(2)  # "async " or None
            return_type_str = match.group(3).strip()
            method_name = match.group(4)
            params_str = match.group(5)

            # Skip properties (they look like methods)
            if match.start() > 0:
                prev_chars = class_body[max(0, match.start() - 20):match.start()]
                if '{' in prev_chars and 'get' in prev_chars:
                    continue

            # Check if async
            is_async = async_keyword is not None and 'async' in async_keyword

            # Extract method body
            method_start = match.end()
            method_body = self._extract_block(class_body, method_start - 1)

            # Parse return type
            return_type = self._parse_return_type(return_type_str, is_async)

            # Parse parameters
            params = self._parse_parameters(params_str)

            # Update context
            old_method = self.context.current_method
            self.context.current_method = method_name

            # Parse body
            body_stmts = self._parse_statements(method_body)

            # Restore context
            self.context.current_method = old_method

            methods.append(IRFunction(
                name=method_name,
                params=params,
                return_type=return_type,
                body=body_stmts,
                is_async=is_async,
                is_private=(access in ['private', 'protected'])
            ))

        return methods

    def _extract_standalone_functions(self, source: str) -> List[IRFunction]:
        """Extract standalone functions (not in classes)."""
        # For now, return empty (C# rarely has standalone functions)
        # Would need to extract from top-level statements in C# 9+
        return []

    # ========================================================================
    # Statement Parsing
    # ========================================================================

    def _parse_statements(self, body: str) -> List[Any]:
        """Parse statements in a code block."""
        statements = []

        # Remove outer braces
        body = body.strip()
        if body.startswith('{') and body.endswith('}'):
            body = body[1:-1].strip()

        # Split into lines (simplified - doesn't handle multi-line statements)
        lines = body.split('\n')

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Skip empty lines and comments
            if not line or line.startswith('//'):
                i += 1
                continue

            # Variable declaration/assignment
            if self._is_variable_declaration(line):
                stmt = self._parse_variable_declaration(line)
                if stmt:
                    statements.append(stmt)

            # Return statement
            elif line.startswith('return'):
                stmt = self._parse_return(line)
                if stmt:
                    statements.append(stmt)

            # If statement
            elif line.startswith('if'):
                # Find full if block
                if_block, consumed = self._extract_if_block('\n'.join(lines[i:]))
                stmt = self._parse_if(if_block)
                if stmt:
                    statements.append(stmt)
                i += consumed - 1

            # For loop
            elif line.startswith('for') or line.startswith('foreach'):
                for_block, consumed = self._extract_control_block('\n'.join(lines[i:]))
                stmt = self._parse_for(for_block)
                if stmt:
                    statements.append(stmt)
                i += consumed - 1

            # While loop
            elif line.startswith('while'):
                while_block, consumed = self._extract_control_block('\n'.join(lines[i:]))
                stmt = self._parse_while(while_block)
                if stmt:
                    statements.append(stmt)
                i += consumed - 1

            # Try-catch
            elif line.startswith('try'):
                try_block, consumed = self._extract_try_block('\n'.join(lines[i:]))
                stmt = self._parse_try(try_block)
                if stmt:
                    statements.append(stmt)
                i += consumed - 1

            # Throw statement
            elif line.startswith('throw'):
                stmt = self._parse_throw(line)
                if stmt:
                    statements.append(stmt)

            # Expression statement (method calls, etc.)
            else:
                # Try to parse as expression
                if ';' in line:
                    expr_str = line[:line.index(';')].strip()
                    expr = self._parse_expression(expr_str)
                    if expr:
                        statements.append(expr)

            i += 1

        return statements

    def _is_variable_declaration(self, line: str) -> bool:
        """Check if line is a variable declaration."""
        # Pattern: var x = ...
        # Pattern: string x = ...
        # Pattern: List<int> x = ...
        var_pattern = re.compile(r'^(?:var|[A-Z]\w*(?:<[^>]+>)?)\s+\w+\s*=')
        return bool(var_pattern.match(line))

    def _parse_variable_declaration(self, line: str) -> Optional[IRAssignment]:
        """Parse variable declaration."""
        # Pattern: var x = value;
        # Pattern: string name = "test";
        # Pattern: Func<int, int> name = value;
        match = re.match(
            r'(var|[a-zA-Z0-9_<>,\[\]\s]+?)\s+(\w+)\s*=\s*(.+);',
            line
        )

        if not match:
            return None

        type_str = match.group(1).strip()
        var_name = match.group(2)
        value_str = match.group(3)

        # Parse value expression
        value = self._parse_expression(value_str)

        # Parse type (if not var)
        var_type = None
        if type_str != 'var':
            var_type = self._parse_type(type_str)

        # Track variable in context
        if var_type:
            self.context.variables[var_name] = var_type

        return IRAssignment(
            target=var_name,
            value=value,
            is_declaration=True,
            var_type=var_type
        )

    def _parse_return(self, line: str) -> Optional[IRReturn]:
        """Parse return statement."""
        # Pattern: return value;
        match = re.match(r'return\s+(.+?);', line)

        if not match:
            # Empty return
            if line.strip() == 'return;':
                return IRReturn(value=None)
            return None

        value_str = match.group(1)
        value = self._parse_expression(value_str)

        return IRReturn(value=value)

    def _parse_if(self, if_block: str) -> Optional[IRIf]:
        """Parse if statement."""
        # Pattern: if (condition) { ... } else { ... }
        match = re.match(
            r'if\s*\(([^)]+)\)\s*\{(.+?)\}(?:\s*else\s*\{(.+?)\})?',
            if_block,
            re.DOTALL
        )

        if not match:
            return None

        condition_str = match.group(1)
        then_body_str = match.group(2)
        else_body_str = match.group(3)

        # Parse condition
        condition = self._parse_expression(condition_str)

        # Parse bodies
        then_body = self._parse_statements(then_body_str)
        else_body = self._parse_statements(else_body_str) if else_body_str else []

        return IRIf(
            condition=condition,
            then_body=then_body,
            else_body=else_body
        )

    def _parse_for(self, for_block: str) -> Optional[IRFor]:
        """Parse for/foreach loop."""
        # Pattern: foreach (var item in items) { ... }
        foreach_match = re.match(
            r'foreach\s*\(\s*(?:var|[a-zA-Z0-9_<>,\[\]]+)\s+(\w+)\s+in\s+(.+?)\)\s*\{(.+?)\}',
            for_block,
            re.DOTALL
        )

        if foreach_match:
            iterator = foreach_match.group(1)
            iterable_str = foreach_match.group(2)
            body_str = foreach_match.group(3)

            # Parse iterable
            iterable = self._parse_expression(iterable_str)

            # Parse body
            body = self._parse_statements(body_str)

            return IRFor(
                iterator=iterator,
                iterable=iterable,
                body=body
            )

        # Regular for loop - convert to while
        return None

    def _parse_while(self, while_block: str) -> Optional[IRWhile]:
        """Parse while loop."""
        # Pattern: while (condition) { ... }
        match = re.match(
            r'while\s*\(([^)]+)\)\s*\{(.+?)\}',
            while_block,
            re.DOTALL
        )

        if not match:
            return None

        condition_str = match.group(1)
        body_str = match.group(2)

        # Parse condition
        condition = self._parse_expression(condition_str)

        # Parse body
        body = self._parse_statements(body_str)

        return IRWhile(
            condition=condition,
            body=body
        )

    def _parse_try(self, try_block: str) -> Optional[IRTry]:
        """Parse try-catch-finally statement with support for multiple catch blocks."""
        # Extract try body
        try_match = re.match(r'try\s*\{', try_block)
        if not try_match:
            return None

        # Find try block
        try_start = try_match.end() - 1
        brace_depth = 0
        i = try_start
        while i < len(try_block):
            if try_block[i] == '{':
                brace_depth += 1
            elif try_block[i] == '}':
                brace_depth -= 1
                if brace_depth == 0:
                    try_body_str = try_block[try_start + 1:i]
                    break
            i += 1

        if brace_depth != 0:
            return None

        # Parse try body
        try_body = self._parse_statements(try_body_str)

        # Extract catch blocks (can be multiple)
        catch_blocks = []
        rest = try_block[i + 1:].lstrip()

        # Pattern for catch: catch (ExceptionType varName) { ... } or catch { ... }
        while rest.startswith('catch'):
            catch_match = re.match(r'catch\s*(?:\(([^)]+)\s+(\w+)\)|\(([^)]+)\))?\s*\{', rest)
            if not catch_match:
                break

            # Extract exception type and variable
            if catch_match.group(1):
                exception_type = catch_match.group(1).strip()
                exception_var = catch_match.group(2)
            elif catch_match.group(3):
                exception_type = catch_match.group(3).strip()
                exception_var = None
            else:
                exception_type = None
                exception_var = None

            # Find catch block body
            catch_start = catch_match.end() - 1
            brace_depth = 0
            i = catch_start
            while i < len(rest):
                if rest[i] == '{':
                    brace_depth += 1
                elif rest[i] == '}':
                    brace_depth -= 1
                    if brace_depth == 0:
                        catch_body_str = rest[catch_start + 1:i]
                        break
                i += 1

            # Parse catch body
            catch_body = self._parse_statements(catch_body_str)

            # Create IRType for exception type
            exc_type = IRType(name=exception_type) if exception_type else None

            catch_blocks.append(IRCatch(
                exception_type=exc_type,
                exception_var=exception_var,
                body=catch_body
            ))

            # Move to next potential catch or finally
            rest = rest[i + 1:].lstrip()

        # Extract finally block (optional)
        finally_body = None
        if rest.startswith('finally'):
            finally_match = re.match(r'finally\s*\{', rest)
            if finally_match:
                finally_start = finally_match.end() - 1
                brace_depth = 0
                i = finally_start
                while i < len(rest):
                    if rest[i] == '{':
                        brace_depth += 1
                    elif rest[i] == '}':
                        brace_depth -= 1
                        if brace_depth == 0:
                            finally_body_str = rest[finally_start + 1:i]
                            finally_body = self._parse_statements(finally_body_str)
                            break
                    i += 1

        return IRTry(
            try_body=try_body,
            catch_blocks=catch_blocks,
            finally_body=finally_body
        )

    def _parse_throw(self, line: str) -> Optional[IRThrow]:
        """Parse throw statement."""
        # Pattern: throw new Exception("message");
        match = re.match(r'throw\s+(.+?);', line)

        if not match:
            return None

        exception_str = match.group(1)
        exception = self._parse_expression(exception_str)

        return IRThrow(exception=exception)

    # ========================================================================
    # Expression Parsing
    # ========================================================================

    def _detect_linq_expression(self, expr_str: str) -> Optional[IRComprehension]:
        """
        Detect C# LINQ method syntax: .Where().Select().ToList()

        Patterns:
        - items.Where(x => cond).Select(x => expr).ToList()
        - items.Select(x => expr).ToList()
        - items.Where(x => cond).ToList()
        - Multiline LINQ chains
        """
        # Normalize whitespace (collapse newlines to spaces)
        normalized = ' '.join(expr_str.split())

        # Check if this looks like LINQ
        if not ('.Where(' in normalized or '.Select(' in normalized):
            return None

        # Extract the collection name
        collection_match = re.search(r'(\w+)\.(?:Where|Select)', normalized)
        if not collection_match:
            return None

        iterable_name = collection_match.group(1)

        # Check for Where
        where_var = None
        where_cond = None
        where_match = re.search(r'\.Where\((\w+)\s*=>\s*([^)]+)\)', normalized)
        if where_match:
            where_var = where_match.group(1)
            where_cond = where_match.group(2).strip()

        # Check for Select
        select_var = None
        select_expr = None
        select_match = re.search(r'\.Select\((\w+)\s*=>\s*([^)]+)\)', normalized)
        if select_match:
            select_var = select_match.group(1)
            select_expr = select_match.group(2).strip()

        # Build IRComprehension based on what we found
        if where_cond and select_expr:
            # Where + Select
            return IRComprehension(
                target=self._parse_expression(select_expr),
                iterator=select_var,
                iterable=IRIdentifier(name=iterable_name),
                condition=self._parse_expression(where_cond),
                comprehension_type="list"
            )
        elif select_expr:
            # Select only
            return IRComprehension(
                target=self._parse_expression(select_expr),
                iterator=select_var,
                iterable=IRIdentifier(name=iterable_name),
                condition=None,
                comprehension_type="list"
            )
        elif where_cond:
            # Where only (filter, no transform)
            return IRComprehension(
                target=IRIdentifier(name=where_var),
                iterator=where_var,
                iterable=IRIdentifier(name=iterable_name),
                condition=self._parse_expression(where_cond),
                comprehension_type="list"
            )

        return None

    def _parse_expression(self, expr_str: str) -> Any:
        """Parse an expression."""
        expr_str = expr_str.strip()

        if not expr_str:
            return IRLiteral(value=None, literal_type=LiteralType.NULL)

        # Literal values
        if expr_str in ['true', 'false']:
            return IRLiteral(value=(expr_str == 'true'), literal_type=LiteralType.BOOLEAN)

        if expr_str == 'null':
            return IRLiteral(value=None, literal_type=LiteralType.NULL)

        if expr_str.startswith('"') and expr_str.endswith('"'):
            return IRLiteral(value=expr_str[1:-1], literal_type=LiteralType.STRING)

        if re.match(r'^-?\d+$', expr_str):
            return IRLiteral(value=int(expr_str), literal_type=LiteralType.INTEGER)

        if re.match(r'^-?\d+\.\d+[fFdDmM]?$', expr_str):
            return IRLiteral(value=float(expr_str.rstrip('fFdDmM')), literal_type=LiteralType.FLOAT)

        # LINQ expressions (comprehensions)
        linq_result = self._detect_linq_expression(expr_str)
        if linq_result:
            return linq_result

        # Lambda expression: x => x * 2 or (x, y) => x + y
        lambda_match = re.match(r'(?:\(([^)]+)\)|(\w+))\s*=>\s*(.+)', expr_str)
        if lambda_match:
            params_str = lambda_match.group(1) or lambda_match.group(2)
            body_str = lambda_match.group(3)

            # Parse parameters
            params = []
            if params_str:
                for param in params_str.split(','):
                    param = param.strip()
                    if param:
                        params.append(IRParameter(
                            name=param,
                            param_type=IRType(name='any')
                        ))

            # Parse body (simplified - single expression)
            body_expr = self._parse_expression(body_str)

            from dsl.ir import IRLambda
            return IRLambda(
                params=params,
                body=[IRReturn(value=body_expr)]
            )

        # Dictionary initializer: new Dictionary<K, V> { {"key", val}, ... }
        # Check this BEFORE generic object initializer pattern
        dict_init_match = re.match(r'new\s+Dictionary<[^>]+>\s*\{([^}]+)\}', expr_str)
        if dict_init_match:
            entries_str = dict_init_match.group(1)
            entries = {}

            # Parse entries (each is {key, value})
            # Handle both {"key", val} and ["key"] = val syntax
            brace_pattern = r'\{([^}]+)\}'
            for entry_match in re.finditer(brace_pattern, entries_str):
                entry_content = entry_match.group(1)
                if ',' in entry_content:
                    parts = self._smart_split(entry_content, ',')
                    if len(parts) >= 2:
                        key_expr = self._parse_expression(parts[0].strip())
                        val_expr = self._parse_expression(parts[1].strip())
                        # Use string representation of key literal as dict key
                        if hasattr(key_expr, 'value'):
                            entries[str(key_expr.value)] = val_expr
                        else:
                            entries[str(key_expr)] = val_expr

            return IRMap(entries=entries)

        # Implicitly typed array: new[] { 1, 2, 3 }
        implicit_array_match = re.match(r'new\[\]\s*\{([^}]+)\}', expr_str)
        if implicit_array_match:
            content = implicit_array_match.group(1)
            elements = []
            for item in self._smart_split(content, ','):
                elements.append(self._parse_expression(item.strip()))
            return IRArray(elements=elements)

        # Collection initializer vs Object initializer
        # Check if it contains '=' for object initializer or not for collection
        new_match = re.match(r'new\s+(\w+(?:<[^>]+>)?)\s*\{([^}]+)\}', expr_str)
        if new_match:
            type_name = new_match.group(1)
            content = new_match.group(2)

            # Check if it's collection initializer (no '=' signs) or object initializer
            if '=' in content:
                # Object initializer: new Type { Prop1 = val1, Prop2 = val2 }
                kwargs = {}
                for prop_assign in self._smart_split(content, ','):
                    if '=' in prop_assign:
                        prop_name, prop_value = prop_assign.split('=', 1)
                        prop_name = prop_name.strip()
                        prop_value = prop_value.strip()
                        kwargs[prop_name] = self._parse_expression(prop_value)

                return IRCall(
                    function=IRIdentifier(name=type_name),
                    args=[],
                    kwargs=kwargs
                )
            else:
                # Collection initializer: new List<int> { 1, 2, 3 }
                elements = []
                for item in self._smart_split(content, ','):
                    elements.append(self._parse_expression(item.strip()))
                return IRArray(elements=elements)

        # Await expression: await expression (C# prefix syntax)
        if expr_str.startswith('await '):
            inner_expr_str = expr_str[6:].strip()  # Remove 'await '
            inner_expr = self._parse_expression(inner_expr_str)
            return IRAwait(expression=inner_expr)

        # Method call
        if '(' in expr_str and ')' in expr_str:
            return self._parse_call(expr_str)

        # Binary operation
        for op_str, op_enum in [
            ('==', BinaryOperator.EQUAL),
            ('!=', BinaryOperator.NOT_EQUAL),
            ('<=', BinaryOperator.LESS_EQUAL),
            ('>=', BinaryOperator.GREATER_EQUAL),
            ('<', BinaryOperator.LESS_THAN),
            ('>', BinaryOperator.GREATER_THAN),
            ('&&', BinaryOperator.AND),
            ('||', BinaryOperator.OR),
            ('+', BinaryOperator.ADD),
            ('-', BinaryOperator.SUBTRACT),
            ('*', BinaryOperator.MULTIPLY),
            ('/', BinaryOperator.DIVIDE),
        ]:
            if op_str in expr_str:
                parts = expr_str.split(op_str, 1)
                if len(parts) == 2:
                    left = self._parse_expression(parts[0].strip())
                    right = self._parse_expression(parts[1].strip())
                    return IRBinaryOp(op=op_enum, left=left, right=right)

        # Property access
        if '.' in expr_str and '(' not in expr_str:
            parts = expr_str.split('.', 1)
            obj = self._parse_expression(parts[0])
            return IRPropertyAccess(object=obj, property=parts[1])

        # LINQ expression (abstract)
        if '.Where(' in expr_str or '.Select(' in expr_str:
            return self._parse_linq(expr_str)

        # Identifier
        return IRIdentifier(name=expr_str)

    def _parse_call(self, call_str: str) -> IRCall:
        """Parse method call."""
        # Pattern: method(arg1, arg2)
        # Pattern: obj.method(arg1, arg2)

        # Find function name and args
        paren_idx = call_str.index('(')
        func_str = call_str[:paren_idx].strip()
        args_str = call_str[paren_idx+1:call_str.rindex(')')].strip()

        # Parse function (may be identifier or property access)
        function = self._parse_expression(func_str)

        # Parse arguments
        args = []
        if args_str:
            # Simple split by comma (doesn't handle nested calls)
            for arg in args_str.split(','):
                args.append(self._parse_expression(arg.strip()))

        return IRCall(function=function, args=args)

    def _parse_linq(self, linq_str: str) -> IRCall:
        """
        Parse LINQ expression and abstract as IR operations.

        Examples:
        - users.Where(u => u.Age >= 18) → filter operation
        - users.Select(u => u.Name) → map operation
        """
        # Abstract LINQ as a chain of calls
        # For now, parse as regular call
        return self._parse_call(linq_str)

    # ========================================================================
    # Type Parsing
    # ========================================================================

    def _parse_type(self, type_str: str) -> IRType:
        """
        Parse C# type string to IR type.

        Examples:
        - string → IRType("string")
        - int → IRType("int")
        - List<string> → IRType("array", generic_args=[IRType("string")])
        - Dictionary<string, int> → IRType("map", generic_args=[...])
        - int? → IRType("int", is_optional=True)
        """
        type_str = type_str.strip()

        # Handle nullable types (int?)
        if type_str.endswith('?'):
            base_type = self._parse_type(type_str[:-1])
            base_type.is_optional = True
            return base_type

        # Handle generic types
        if '<' in type_str and type_str.endswith('>'):
            bracket_idx = type_str.index('<')
            base_name = type_str[:bracket_idx]
            generic_str = type_str[bracket_idx+1:-1]

            # Parse generic arguments
            generic_args = [self._parse_type(arg.strip()) for arg in generic_str.split(',')]

            # Map common generic types
            if base_name in ['List', 'IEnumerable', 'IList', 'ICollection']:
                return IRType(name="array", generic_args=generic_args)
            elif base_name in ['Dictionary', 'IDictionary']:
                return IRType(name="map", generic_args=generic_args)
            elif base_name == 'Task':
                # Task<T> - return the inner type (async wrapper)
                return generic_args[0] if generic_args else IRType(name="any")
            else:
                # Custom generic type
                return IRType(name=base_name, generic_args=generic_args)

        # Handle array types
        if type_str.endswith('[]'):
            element_type = self._parse_type(type_str[:-2])
            return IRType(name="array", generic_args=[element_type])

        # Map primitive types
        type_map = {
            'string': 'string',
            'int': 'int',
            'Int32': 'int',
            'long': 'int',
            'Int64': 'int',
            'double': 'float',
            'Double': 'float',
            'float': 'float',
            'Single': 'float',
            'decimal': 'float',
            'Decimal': 'float',
            'bool': 'bool',
            'Boolean': 'bool',
            'object': 'any',
            'Object': 'any',
            'var': 'any',
            'void': 'null',
        }

        pw_type = type_map.get(type_str, type_str)
        return IRType(name=pw_type)

    def _parse_return_type(self, type_str: str, is_async: bool) -> Optional[IRType]:
        """Parse return type, handling async Task<T>."""
        if type_str == 'void':
            return None

        # If async and Task/Task<T>, unwrap
        if is_async:
            if type_str == 'Task':
                return None  # Task without return type
            elif type_str.startswith('Task<'):
                # Extract inner type
                inner = type_str[5:-1]
                return self._parse_type(inner)

        return self._parse_type(type_str)

    def _parse_parameters(self, params_str: str) -> List[IRParameter]:
        """Parse method parameters."""
        if not params_str.strip():
            return []

        params = []

        # Split by comma (simplified - doesn't handle complex types)
        for param in params_str.split(','):
            param = param.strip()
            if not param:
                continue

            # Pattern: int age
            # Pattern: string name = "default"
            parts = param.split()
            if len(parts) >= 2:
                type_str = ' '.join(parts[:-1])  # May include generics
                param_name = parts[-1]

                # Handle default value
                default_value = None
                if '=' in param_name:
                    param_name, default_str = param_name.split('=', 1)
                    param_name = param_name.strip()
                    default_value = self._parse_expression(default_str.strip())

                param_type = self._parse_type(type_str)

                params.append(IRParameter(
                    name=param_name,
                    param_type=param_type,
                    default_value=default_value
                ))

        return params

    # ========================================================================
    # Utility Methods
    # ========================================================================

    def _smart_split(self, text: str, delimiter: str) -> List[str]:
        """Split text by delimiter, respecting nested brackets and braces."""
        parts = []
        current = []
        depth = 0

        for char in text:
            if char in '<({[':
                depth += 1
                current.append(char)
            elif char in '>)}]':
                depth -= 1
                current.append(char)
            elif char == delimiter and depth == 0:
                parts.append(''.join(current))
                current = []
            else:
                current.append(char)

        if current:
            parts.append(''.join(current))

        return parts

    def _remove_comments(self, source: str) -> str:
        """Remove C# comments from source."""
        # Remove single-line comments
        source = re.sub(r'//.*?$', '', source, flags=re.MULTILINE)

        # Remove multi-line comments
        source = re.sub(r'/\*.*?\*/', '', source, flags=re.DOTALL)

        return source

    def _extract_block(self, source: str, start_idx: int) -> str:
        """
        Extract a balanced block starting from a { character.

        Args:
            source: Source code
            start_idx: Index of opening {

        Returns:
            Block content including braces
        """
        if start_idx >= len(source) or source[start_idx] != '{':
            return ""

        depth = 0
        i = start_idx

        while i < len(source):
            if source[i] == '{':
                depth += 1
            elif source[i] == '}':
                depth -= 1
                if depth == 0:
                    return source[start_idx:i+1]
            i += 1

        return source[start_idx:]

    def _extract_if_block(self, source: str) -> Tuple[str, int]:
        """Extract if statement including else clause."""
        # Find the if block
        match = re.match(r'if\s*\([^)]+\)\s*\{', source)
        if not match:
            return "", 0

        # Extract the then block
        then_start = match.end() - 1
        then_block = self._extract_block(source, then_start)

        # Check for else
        rest = source[then_start + len(then_block):].lstrip()
        if rest.startswith('else'):
            else_match = re.match(r'else\s*\{', rest)
            if else_match:
                else_start = else_match.end() - 1
                else_block = self._extract_block(rest, else_start)
                full_block = source[:then_start + len(then_block)] + rest[:else_start + len(else_block)]
                lines = full_block.count('\n')
                return full_block, lines + 1

        full_block = source[:then_start + len(then_block)]
        lines = full_block.count('\n')
        return full_block, lines + 1

    def _extract_control_block(self, source: str) -> Tuple[str, int]:
        """Extract control flow block (for/while)."""
        # Find the opening brace
        brace_idx = source.index('{')
        block = self._extract_block(source, brace_idx)

        full_block = source[:brace_idx + len(block)]
        lines = full_block.count('\n')
        return full_block, lines + 1

    def _extract_try_block(self, source: str) -> Tuple[str, int]:
        """Extract try-catch-finally block with support for multiple catches."""
        # Find try block
        try_match = re.match(r'try\s*\{', source)
        if not try_match:
            return "", 0

        try_start = try_match.end() - 1
        try_block = self._extract_block(source, try_start)

        end_pos = try_start + len(try_block)
        rest = source[end_pos:].lstrip()

        # Find all catch blocks (can be multiple)
        while rest.startswith('catch'):
            catch_match = re.match(r'catch\s*(?:\([^)]+\))?\s*\{', rest)
            if not catch_match:
                break

            catch_start = catch_match.end() - 1
            catch_block = self._extract_block(rest, catch_start)

            # Add the whitespace before catch and the catch block itself
            spaces_before_catch = len(source[end_pos:]) - len(rest)
            end_pos += spaces_before_catch + catch_start + len(catch_block)
            rest = source[end_pos:].lstrip()

        # Find finally block (optional)
        if rest.startswith('finally'):
            finally_match = re.match(r'finally\s*\{', rest)
            if finally_match:
                finally_start = finally_match.end() - 1
                finally_block = self._extract_block(rest, finally_start)

                # Add the whitespace before finally and the finally block itself
                spaces_before_finally = len(source[end_pos:]) - len(rest)
                end_pos += spaces_before_finally + finally_start + len(finally_block)

        full_block = source[:end_pos]
        lines = full_block.count('\n')
        return full_block, lines + 1


# ============================================================================
# Convenience Functions
# ============================================================================


def parse_csharp_file(file_path: str) -> IRModule:
    """
    Parse C# file into IR module.

    Args:
        file_path: Path to .cs file

    Returns:
        IR module representation
    """
    parser = DotNetParserV2()
    return parser.parse_file(file_path)


def parse_csharp_source(source: str, module_name: str = "module") -> IRModule:
    """
    Parse C# source code into IR module.

    Args:
        source: C# source code
        module_name: Module name

    Returns:
        IR module representation
    """
    parser = DotNetParserV2()
    return parser.parse_source(source, module_name)
