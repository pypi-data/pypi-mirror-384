"""
Rust Parser V2: Arbitrary Rust code → Promptware IR

This parser converts arbitrary Rust code into the Promptware intermediate
representation (IR), enabling universal code translation between Rust and
any other supported language.

Key Features:
- Parse functions, structs, enums, traits, and impls
- Handle ownership and lifetimes (abstracted as metadata)
- Extract type information from Rust syntax
- Handle Result/Option patterns
- Support common Rust idioms

Strategy:
- Regex-based parsing (no external dependencies)
- Pattern matching for Rust-specific constructs
- Type mapping: Rust types → IR types
- Ownership/lifetime preservation as metadata
"""

import re
from dataclasses import dataclass
from typing import List, Dict, Optional, Any, Set, Tuple

from dsl.ir import (
    IRModule,
    IRImport,
    IRFunction,
    IRParameter,
    IRType,
    IRClass,
    IRProperty,
    IREnum,
    IREnumVariant,
    IRTypeDefinition,
    IRAssignment,
    IRAwait,
    IRReturn,
    IRIf,
    IRFor,
    IRWhile,
    IRTry,
    IRCatch,
    IRThrow,
    IRCall,
    IRIdentifier,
    IRLiteral,
    IRBinaryOp,
    IRPropertyAccess,
    IRArray,
    IRMap,
    IRComprehension,
    BinaryOperator,
    LiteralType,
    SourceLocation,
)


class RustParserV2:
    """Parse arbitrary Rust code into Promptware IR."""

    def __init__(self):
        self.current_file: Optional[str] = None
        self.source_lines: List[str] = []

    # ========================================================================
    # Main Parsing Entry Points
    # ========================================================================

    def parse_file(self, file_path: str) -> IRModule:
        """
        Parse a Rust source file into IR.

        Args:
            file_path: Path to .rs file

        Returns:
            IRModule containing all extracted definitions
        """
        self.current_file = file_path

        with open(file_path, 'r') as f:
            source = f.read()

        # Extract module name from file path
        module_name = self._extract_module_name(file_path)

        return self.parse_source(source, module_name)

    def parse_source(self, source: str, module_name: str = "module") -> IRModule:
        """
        Parse Rust source code into IR.

        Args:
            source: Rust source code string
            module_name: Name for the module (default: "module")

        Returns:
            IRModule containing all extracted definitions
        """
        self.source_lines = source.split('\n')

        # Create IR module
        module = IRModule(name=module_name, version="1.0.0")

        # Parse imports
        module.imports = self._parse_imports(source)

        # Parse type definitions (structs)
        struct_defs = self._parse_structs(source)

        # Parse enums
        module.enums = self._parse_enums(source)

        # Parse standalone functions
        module.functions = self._parse_functions(source)

        # Parse traits and impls (convert to classes)
        impl_classes = self._parse_traits_and_impls(source)

        # CRITICAL: Merge struct definitions with impl blocks
        # This is the reverse operation - generator creates struct + impl from IRClass
        module.classes = self._merge_structs_with_impls(struct_defs, impl_classes)
        module.types = []  # Structs are now part of classes

        return module

    # ========================================================================
    # Import Parsing
    # ========================================================================

    def _parse_imports(self, source: str) -> List[IRImport]:
        """Parse use statements."""
        imports = []

        # Pattern: use path::to::module;
        # Pattern: use path::to::{Item1, Item2};
        use_pattern = r'use\s+([\w:]+)(?:::\{([^}]+)\})?;'

        for match in re.finditer(use_pattern, source):
            module_path = match.group(1)
            items_str = match.group(2)

            if items_str:
                # use std::collections::{HashMap, HashSet};
                items = [item.strip() for item in items_str.split(',')]
                imports.append(IRImport(
                    module=module_path,
                    items=items
                ))
            else:
                # use std::collections::HashMap;
                parts = module_path.split('::')
                if len(parts) > 1:
                    module = '::'.join(parts[:-1])
                    item = parts[-1]
                    imports.append(IRImport(
                        module=module,
                        items=[item]
                    ))
                else:
                    imports.append(IRImport(module=module_path))

        return imports

    # ========================================================================
    # Struct Parsing
    # ========================================================================

    def _parse_structs(self, source: str) -> List[IRTypeDefinition]:
        """Parse struct definitions."""
        structs = []

        # Pattern: struct Name { ... }
        # Handles doc comments: /// Description
        struct_pattern = r'(?:///\s*(.+)\n\s*)?pub\s+struct\s+(\w+)\s*\{([^}]+)\}'

        for match in re.finditer(struct_pattern, source, re.MULTILINE | re.DOTALL):
            doc_comment = match.group(1)
            struct_name = match.group(2)
            fields_str = match.group(3)

            # Parse fields
            fields = self._parse_struct_fields(fields_str)

            struct_def = IRTypeDefinition(
                name=struct_name,
                fields=fields,
                doc=doc_comment
            )

            structs.append(struct_def)

        return structs

    def _parse_struct_fields(self, fields_str: str) -> List[IRProperty]:
        """Parse struct field definitions."""
        fields = []

        # Pattern: pub field_name: Type,
        # Pattern: field_name: Type,
        field_pattern = r'(?:pub\s+)?(\w+)\s*:\s*([^,\n]+)'

        for match in re.finditer(field_pattern, fields_str):
            field_name = match.group(1)
            field_type_str = match.group(2).strip().rstrip(',')

            # Map Rust type to IR type
            field_type = self._map_rust_type_to_ir(field_type_str)

            fields.append(IRProperty(
                name=field_name,
                prop_type=field_type,
                is_private=not match.group(0).startswith('pub')
            ))

        return fields

    # ========================================================================
    # Enum Parsing
    # ========================================================================

    def _parse_enums(self, source: str) -> List[IREnum]:
        """Parse enum definitions."""
        enums = []

        # Pattern: enum Name { ... }
        enum_pattern = r'(?:///\s*(.+)\n\s*)?pub\s+enum\s+(\w+)\s*\{([^}]+)\}'

        for match in re.finditer(enum_pattern, source, re.MULTILINE | re.DOTALL):
            doc_comment = match.group(1)
            enum_name = match.group(2)
            variants_str = match.group(3)

            # Parse variants
            variants = self._parse_enum_variants(variants_str)

            enum_def = IREnum(
                name=enum_name,
                variants=variants,
                doc=doc_comment
            )

            enums.append(enum_def)

        return enums

    def _parse_enum_variants(self, variants_str: str) -> List[IREnumVariant]:
        """Parse enum variant definitions."""
        variants = []

        # Pattern: VariantName,
        # Pattern: VariantName(Type),
        # Pattern: VariantName { field: Type },
        variant_pattern = r'(\w+)(?:\(([^)]+)\))?(?:\s*\{[^}]+\})?,?'

        for match in re.finditer(variant_pattern, variants_str):
            variant_name = match.group(1)
            associated_type_str = match.group(2)

            associated_types = []
            if associated_type_str:
                # Parse associated types
                for type_str in associated_type_str.split(','):
                    ir_type = self._map_rust_type_to_ir(type_str.strip())
                    associated_types.append(ir_type)

            variants.append(IREnumVariant(
                name=variant_name,
                associated_types=associated_types
            ))

        return variants

    # ========================================================================
    # Function Parsing
    # ========================================================================

    def _parse_functions(self, source: str) -> List[IRFunction]:
        """Parse standalone function definitions."""
        functions = []

        # Pattern: fn name(...) -> ReturnType { ... }
        # Pattern: pub fn name(...) { ... }
        # Pattern: async fn name(...) { ... }
        fn_pattern = r'(?:///\s*(.+)\n\s*)?(?:pub\s+)?(?:async\s+)?fn\s+(\w+)\s*\(([^)]*)\)(?:\s*->\s*([^{]+))?\s*\{'

        for match in re.finditer(fn_pattern, source, re.MULTILINE):
            doc_comment = match.group(1)
            fn_name = match.group(2)
            params_str = match.group(3)
            return_type_str = match.group(4)

            # Skip trait methods (handled separately)
            if self._is_inside_trait_or_impl(source, match.start()):
                continue

            # Parse parameters
            params = self._parse_function_params(params_str)

            # Parse return type
            return_type = None
            if return_type_str:
                return_type = self._map_rust_type_to_ir(return_type_str.strip())

            # Extract function body
            body_start = match.end()
            body = self._extract_function_body(source, body_start - 1)

            # Parse body statements (simplified)
            body_stmts = self._parse_function_body(body)

            # Check if async
            is_async = 'async' in match.group(0)

            # Check if public
            is_private = 'pub' not in match.group(0)

            func = IRFunction(
                name=fn_name,
                params=params,
                return_type=return_type,
                body=body_stmts,
                is_async=is_async,
                is_private=is_private,
                doc=doc_comment
            )

            # Store ownership metadata
            func.metadata['rust_ownership'] = self._extract_ownership_info(params_str)

            functions.append(func)

        return functions

    def _parse_function_params(self, params_str: str) -> List[IRParameter]:
        """Parse function parameters."""
        params = []

        if not params_str.strip():
            return params

        # Split by comma, but respect nested generics
        param_strs = self._smart_split(params_str, ',')

        for param_str in param_strs:
            param_str = param_str.strip()
            if not param_str:
                continue

            # Pattern: name: Type
            # Pattern: mut name: Type
            # Pattern: &self
            # Pattern: &mut self

            if param_str in ['self', '&self', '&mut self', 'mut self']:
                # Self parameter - skip for now (handled by class methods)
                continue

            # Remove 'mut' keyword
            param_str = param_str.replace('mut ', '')

            # Split on ':'
            parts = param_str.split(':', 1)
            if len(parts) != 2:
                continue

            param_name = parts[0].strip().lstrip('&')
            param_type_str = parts[1].strip()

            # Map to IR type
            param_type = self._map_rust_type_to_ir(param_type_str)

            params.append(IRParameter(
                name=param_name,
                param_type=param_type
            ))

        return params

    def _parse_function_body(self, body: str) -> List:
        """Parse function body into IR statements."""
        statements = []

        # Remove leading/trailing whitespace
        body = body.strip()
        if not body:
            return statements

        # Split into lines for statement parsing
        lines = body.split('\n')

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Skip empty lines and comments
            if not line or line.startswith('//'):
                i += 1
                continue

            # Parse statement
            stmt, lines_consumed = self._parse_rust_statement(line, lines, i)
            if stmt:
                statements.append(stmt)
                i += lines_consumed
            else:
                i += 1

        return statements

    def _parse_rust_statement(self, line: str, lines: List[str], index: int) -> tuple[Optional, int]:
        """Parse a single Rust statement. Returns (statement, lines_consumed)."""

        # Return statement
        if line.startswith('return '):
            return_match = re.match(r'return\s+([^;]+);', line)
            if return_match:
                expr_str = return_match.group(1).strip()
                expr = self._parse_expression(expr_str)
                return IRReturn(value=expr), 1

        # If statement
        if line.startswith('if '):
            stmt, lines_consumed = self._parse_rust_if_statement(line, lines, index)
            return stmt, lines_consumed

        # For loop
        if line.startswith('for '):
            stmt, lines_consumed = self._parse_rust_for_statement(line, lines, index)
            return stmt, lines_consumed

        # Let binding
        let_match = re.match(r'let\s+(?:mut\s+)?(\w+)\s*=\s*([^;]+);', line)
        if let_match:
            var_name = let_match.group(1)
            value_str = let_match.group(2).strip()
            value_expr = self._parse_expression(value_str)
            return IRAssignment(target=var_name, value=value_expr, is_declaration=True), 1

        # Method call (map.insert, vec.push, etc.)
        if '.' in line and '(' in line:
            call_match = re.match(r'(.+);', line)
            if call_match:
                expr_str = call_match.group(1).strip()
                expr = self._parse_expression(expr_str)
                if isinstance(expr, IRCall):
                    return expr, 1

        return None, 1

    def _extract_rust_block_body(self, lines: List[str], start_index: int) -> tuple[str, int]:
        """
        Extract the body of a block starting from line with opening '{'.
        Returns (body_text, lines_consumed).
        """
        # Reconstruct source from lines
        source = '\n'.join(lines[start_index:])

        # Find opening brace
        brace_idx = source.find('{')
        if brace_idx == -1:
            return "", 0

        # Track brace depth
        depth = 0
        i = brace_idx

        while i < len(source):
            if source[i] == '{':
                depth += 1
            elif source[i] == '}':
                depth -= 1
                if depth == 0:
                    # Extract body (between braces)
                    body = source[brace_idx + 1:i]

                    # Count lines consumed
                    consumed_text = source[:i + 1]
                    lines_consumed = consumed_text.count('\n') + 1

                    return body.strip(), lines_consumed
            i += 1

        # Unclosed block - return what we have
        return source[brace_idx + 1:].strip(), len(lines) - start_index

    def _parse_rust_if_statement(self, line: str, lines: List[str], index: int) -> tuple[IRIf, int]:
        """Parse Rust if statement. Returns (statement, lines_consumed)."""
        # Extract condition: if condition {
        condition_match = re.match(r'if\s+(.+?)\s*\{', line)
        if not condition_match:
            condition_str = line[3:].strip()
            condition_expr = self._parse_expression(condition_str)
            return IRIf(condition=condition_expr, then_body=[], else_body=[]), 1

        condition_str = condition_match.group(1)
        condition_expr = self._parse_expression(condition_str)

        # Extract then body
        then_body_str, lines_consumed = self._extract_rust_block_body(lines, index)
        then_body = self._parse_function_body(then_body_str) if then_body_str else []

        # TODO: Handle else/else if
        return IRIf(condition=condition_expr, then_body=then_body, else_body=[]), lines_consumed

    def _parse_rust_for_statement(self, line: str, lines: List[str], index: int) -> tuple[IRFor, int]:
        """Parse Rust for loop. Returns (statement, lines_consumed)."""
        # Handle: for item in items {
        for_match = re.match(r'for\s+(\w+)\s+in\s+(.+?)\s*\{', line)
        if for_match:
            iterator = for_match.group(1)
            iterable_str = for_match.group(2)
            iterable_expr = self._parse_expression(iterable_str)

            # Extract loop body
            body_str, lines_consumed = self._extract_rust_block_body(lines, index)
            body = self._parse_function_body(body_str) if body_str else []

            return IRFor(iterator=iterator, iterable=iterable_expr, body=body), lines_consumed

        # Fallback
        return IRFor(iterator='item', iterable=IRIdentifier(name='iter'), body=[]), 1

    # ========================================================================
    # Trait and Impl Parsing
    # ========================================================================

    def _parse_traits_and_impls(self, source: str) -> List[IRClass]:
        """Parse trait definitions and impl blocks as classes."""
        classes = []

        # Parse traits as interfaces
        trait_pattern = r'(?:///\s*(.+)\n\s*)?pub\s+trait\s+(\w+)\s*\{([^}]+)\}'

        for match in re.finditer(trait_pattern, source, re.MULTILINE | re.DOTALL):
            doc_comment = match.group(1)
            trait_name = match.group(2)
            trait_body = match.group(3)

            # Parse trait methods
            methods = self._parse_trait_methods(trait_body)

            # Create class representation of trait
            trait_class = IRClass(
                name=trait_name,
                methods=methods,
                doc=doc_comment
            )
            trait_class.metadata['rust_trait'] = True

            classes.append(trait_class)

        # Parse impl blocks - use a simpler pattern then extract body manually
        impl_start_pattern = r'impl\s+(?:(\w+)\s+for\s+)?(\w+)\s*\{'

        for match in re.finditer(impl_start_pattern, source):
            trait_name = match.group(1)
            type_name = match.group(2)

            # Extract impl body by matching braces
            body_start = match.end() - 1  # Position of opening brace
            impl_body = self._extract_function_body(source, body_start)

            # Parse impl methods
            methods = self._parse_impl_methods(impl_body, source, match.start())

            if not methods:
                continue

            # Find or create class for this type
            existing_class = next(
                (c for c in classes if c.name == type_name),
                None
            )

            if existing_class:
                existing_class.methods.extend(methods)
            else:
                impl_class = IRClass(
                    name=type_name,
                    methods=methods
                )
                if trait_name:
                    impl_class.base_classes = [trait_name]
                classes.append(impl_class)

        return classes

    def _merge_structs_with_impls(
        self,
        struct_defs: List,
        impl_classes: List[IRClass]
    ) -> List[IRClass]:
        """
        Merge struct definitions with their impl blocks into complete IRClass.

        This is the REVERSE operation of the generator:
        - Generator: IRClass → struct + impl
        - Parser: struct + impl → IRClass

        Args:
            struct_defs: List of IRTypeDefinition from structs
            impl_classes: List of IRClass from impl blocks

        Returns:
            Merged list of IRClass with both properties (from struct) and methods (from impl)
        """
        merged_classes = []

        # Create a dict of impl classes by name for fast lookup
        impl_dict = {cls.name: cls for cls in impl_classes}

        # Process each struct
        for struct_def in struct_defs:
            struct_name = struct_def.name

            # Get corresponding impl (if any)
            impl_class = impl_dict.get(struct_name)

            if impl_class:
                # Merge: struct fields + impl methods
                # Convert struct fields to properties
                properties = []
                for field in struct_def.fields:
                    prop = IRProperty(
                        name=field.name,
                        prop_type=field.prop_type,
                        is_private=False,  # Rust uses pub keyword
                        is_readonly=False,
                    )
                    properties.append(prop)

                # Create merged class
                merged_class = IRClass(
                    name=struct_name,
                    properties=properties,
                    methods=impl_class.methods,
                    constructor=None,  # Rust uses new() pattern
                    doc=struct_def.doc,
                )

                merged_classes.append(merged_class)

                # Remove from impl_dict so we don't process it again
                del impl_dict[struct_name]
            else:
                # Struct without impl - still create class with just properties
                properties = []
                for field in struct_def.fields:
                    prop = IRProperty(
                        name=field.name,
                        prop_type=field.prop_type,
                        is_private=False,
                        is_readonly=False,
                    )
                    properties.append(prop)

                merged_class = IRClass(
                    name=struct_name,
                    properties=properties,
                    methods=[],
                    doc=struct_def.doc,
                )

                merged_classes.append(merged_class)

        # Add any remaining impl blocks that didn't have a struct
        # (e.g., trait implementations for external types)
        for impl_class in impl_dict.values():
            merged_classes.append(impl_class)

        return merged_classes

    def _parse_trait_methods(self, trait_body: str) -> List[IRFunction]:
        """Parse method signatures in trait definition."""
        methods = []

        # Pattern: fn method_name(...) -> ReturnType;
        method_pattern = r'fn\s+(\w+)\s*\(([^)]*)\)(?:\s*->\s*([^;]+))?;'

        for match in re.finditer(method_pattern, trait_body):
            method_name = match.group(1)
            params_str = match.group(2)
            return_type_str = match.group(3)

            params = self._parse_function_params(params_str)

            return_type = None
            if return_type_str:
                return_type = self._map_rust_type_to_ir(return_type_str.strip())

            methods.append(IRFunction(
                name=method_name,
                params=params,
                return_type=return_type,
                body=[]  # Trait methods have no body
            ))

        return methods

    def _parse_impl_methods(self, impl_body: str, full_source: str, impl_start: int) -> List[IRFunction]:
        """Parse method implementations in impl block."""
        methods = []

        # Pattern: fn method_name(...) -> ReturnType { ... }
        # More flexible pattern to catch methods with &self, &mut self, etc.
        method_pattern = r'(?:pub\s+)?(?:async\s+)?fn\s+(\w+)\s*\(([^)]*)\)(?:\s*->\s*([^{]+))?\s*\{'

        for match in re.finditer(method_pattern, impl_body, re.MULTILINE):
            method_name = match.group(1)
            params_str = match.group(2)
            return_type_str = match.group(3)

            params = self._parse_function_params(params_str)

            return_type = None
            if return_type_str:
                return_type = self._map_rust_type_to_ir(return_type_str.strip())

            # Extract method body
            body_start = match.end()
            # Find this position in full source
            full_body_start = impl_start + impl_body[:body_start].count('\n')
            body = self._extract_function_body(impl_body, body_start - 1)

            body_stmts = self._parse_function_body(body)

            is_async = 'async' in match.group(0)
            is_private = 'pub' not in match.group(0)

            methods.append(IRFunction(
                name=method_name,
                params=params,
                return_type=return_type,
                body=body_stmts,
                is_async=is_async,
                is_private=is_private
            ))

        return methods

    # ========================================================================
    # Type Mapping
    # ========================================================================

    def _map_rust_type_to_ir(self, rust_type: str) -> IRType:
        """
        Map Rust type to IR type.

        Handles:
        - Primitives: i32, u32, f64, bool, String, str
        - References: &str, &mut T
        - Option<T> → T? (optional)
        - Result<T, E> → T with throws metadata
        - Vec<T> → array<T>
        - HashMap<K, V> → map<K, V>
        - Custom types
        """
        rust_type = rust_type.strip()

        # Remove reference markers
        rust_type = rust_type.lstrip('&').replace('mut ', '')

        # Handle Option<T> - make it optional
        if rust_type.startswith('Option<'):
            inner = rust_type[7:-1].strip()
            inner_type = self._map_rust_type_to_ir(inner)
            inner_type.is_optional = True
            return inner_type

        # Handle Result<T, E> - unwrap to T, store E in metadata
        if rust_type.startswith('Result<'):
            inner = rust_type[7:-1].strip()
            # Split by comma (handle nested generics)
            parts = self._smart_split(inner, ',')
            if parts:
                ok_type = self._map_rust_type_to_ir(parts[0].strip())
                # Store error type in metadata
                if len(parts) > 1:
                    ok_type.metadata['rust_error_type'] = parts[1].strip()
                return ok_type

        # Handle Vec<T>
        if rust_type.startswith('Vec<'):
            inner = rust_type[4:-1].strip()
            inner_type = self._map_rust_type_to_ir(inner)
            return IRType(name='array', generic_args=[inner_type])

        # Handle HashMap<K, V>
        if rust_type.startswith('HashMap<') or rust_type.startswith('BTreeMap<'):
            start_idx = rust_type.index('<')
            inner = rust_type[start_idx+1:-1].strip()
            parts = self._smart_split(inner, ',')
            if len(parts) >= 2:
                key_type = self._map_rust_type_to_ir(parts[0].strip())
                val_type = self._map_rust_type_to_ir(parts[1].strip())
                return IRType(name='map', generic_args=[key_type, val_type])

        # Map primitive types
        type_map = {
            'i8': 'int', 'i16': 'int', 'i32': 'int', 'i64': 'int', 'i128': 'int',
            'u8': 'int', 'u16': 'int', 'u32': 'int', 'u64': 'int', 'u128': 'int',
            'isize': 'int', 'usize': 'int',
            'f32': 'float', 'f64': 'float',
            'bool': 'bool',
            'String': 'string', 'str': 'string',
            '()': 'null',  # Unit type
        }

        if rust_type in type_map:
            return IRType(name=type_map[rust_type])

        # Custom type - return as-is
        return IRType(name=rust_type)

    # ========================================================================
    # Iterator Chain Detection (Collection Operations)
    # ========================================================================

    def _extract_closure_body(self, text: str, start_pos: int) -> str:
        """Extract closure body handling nested parens, handling |var| body syntax."""
        depth = 0
        i = start_pos
        while i < len(text):
            if text[i] == '|' and depth == 0:
                # Found closing pipe
                return text[start_pos:i].strip()
            elif text[i] == '(':
                depth += 1
            elif text[i] == ')':
                if depth == 0:
                    # End of closure - this happens with .map(|x| expr).collect()
                    return text[start_pos:i].strip()
                depth -= 1
            i += 1
        return text[start_pos:].strip()

    def _detect_iterator_chain(self, expr_str: str) -> Optional[IRComprehension]:
        """
        Detect Rust iterator chains: .iter().filter().map().collect()

        Patterns:
        - items.iter().map(|x| x * 2).collect()
        - items.iter().filter(|x| x > 0).map(|x| x * 2).collect()
        - items.into_iter().filter(...).map(...).collect()
        """
        # Normalize whitespace (including newlines) to single spaces for pattern matching
        normalized = ' '.join(expr_str.split())

        # Check if this looks like an iterator chain
        if '.iter()' not in normalized and '.into_iter()' not in normalized:
            return None

        # Extract the iterable name
        iter_match = re.search(r'(\w+)\.(?:iter|into_iter)\(\)', normalized)
        if not iter_match:
            return None

        iterable_name = iter_match.group(1)

        # Check for filter
        filter_var = None
        filter_cond = None
        filter_match = re.search(r'\.filter\(\|(\w+)\|\s*', normalized)
        if filter_match:
            filter_var = filter_match.group(1)
            body_start = filter_match.end()
            filter_cond = self._extract_closure_body(normalized, body_start)

        # Check for map
        map_var = None
        map_expr = None
        map_match = re.search(r'\.map\(\|(\w+)\|\s*', normalized)
        if map_match:
            map_var = map_match.group(1)
            body_start = map_match.end()
            map_expr = self._extract_closure_body(normalized, body_start)

        # Must have .collect()
        if '.collect()' not in normalized:
            return None

        # Build IRComprehension based on what we found
        if filter_cond and map_expr:
            # filter + map
            return IRComprehension(
                target=self._parse_expression(map_expr),
                iterator=map_var,
                iterable=IRIdentifier(name=iterable_name),
                condition=self._parse_expression(filter_cond),
                comprehension_type="list"
            )
        elif map_expr:
            # map only
            return IRComprehension(
                target=self._parse_expression(map_expr),
                iterator=map_var,
                iterable=IRIdentifier(name=iterable_name),
                condition=None,
                comprehension_type="list"
            )
        elif filter_cond:
            # filter only
            return IRComprehension(
                target=IRIdentifier(name=filter_var),
                iterator=filter_var,
                iterable=IRIdentifier(name=iterable_name),
                condition=self._parse_expression(filter_cond),
                comprehension_type="list"
            )

        return None

    # ========================================================================
    # Expression Parsing (Simplified)
    # ========================================================================

    def _parse_expression(self, expr_str: str):
        """Parse expression string into IR expression (simplified)."""
        expr_str = expr_str.strip()

        # Check for iterator chains first (before other patterns)
        iterator_chain = self._detect_iterator_chain(expr_str)
        if iterator_chain:
            return iterator_chain

        # Literal strings
        if expr_str.startswith('"') and expr_str.endswith('"'):
            return IRLiteral(
                value=expr_str[1:-1],
                literal_type=LiteralType.STRING
            )

        # Literal numbers
        if expr_str.isdigit():
            return IRLiteral(
                value=int(expr_str),
                literal_type=LiteralType.INTEGER
            )

        if re.match(r'^-?\d+\.\d+$', expr_str):
            return IRLiteral(
                value=float(expr_str),
                literal_type=LiteralType.FLOAT
            )

        # Booleans
        if expr_str in ['true', 'false']:
            return IRLiteral(
                value=expr_str == 'true',
                literal_type=LiteralType.BOOLEAN
            )

        # Vec literal: vec![1, 2, 3]
        vec_match = re.match(r'vec!\[([^\]]*)\]', expr_str)
        if vec_match:
            elements = []
            elements_str = vec_match.group(1)
            if elements_str.strip():
                for elem in self._smart_split(elements_str, ','):
                    elements.append(self._parse_expression(elem.strip()))
            return IRArray(elements=elements)

        # Array literal: [1, 2, 3]
        array_match = re.match(r'\[([^\]]*)\]', expr_str)
        if array_match:
            elements = []
            elements_str = array_match.group(1)
            if elements_str.strip():
                for elem in self._smart_split(elements_str, ','):
                    elements.append(self._parse_expression(elem.strip()))
            return IRArray(elements=elements)

        # Struct literal: User { id: 1, name: "Alice" }
        struct_match = re.match(r'(\w+)\s*\{([^}]*)\}', expr_str)
        if struct_match:
            type_name = struct_match.group(1)
            fields_str = struct_match.group(2)

            kwargs = {}
            if fields_str.strip():
                # Parse field assignments
                for field_assign in self._smart_split(fields_str, ','):
                    if ':' in field_assign:
                        field_name, field_value = field_assign.split(':', 1)
                        field_name = field_name.strip()
                        field_value = field_value.strip()
                        kwargs[field_name] = self._parse_expression(field_value)

            return IRCall(
                function=IRIdentifier(name=type_name),
                args=[],
                kwargs=kwargs
            )

        # Closure/Lambda: |x| x * 2
        lambda_match = re.match(r'\|([^|]*)\|\s*(.+)', expr_str)
        if lambda_match:
            params_str = lambda_match.group(1)
            body_str = lambda_match.group(2)

            # Parse parameters
            params = []
            if params_str.strip():
                for param in self._smart_split(params_str, ','):
                    param = param.strip()
                    if param:
                        # Simple parameter (no type annotation in closures usually)
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

        # Await expression: expr.await (Rust postfix syntax)
        if '.await' in expr_str:
            # Split on .await and parse the expression before it
            base_expr_str = expr_str.replace('.await', '').strip()
            base_expr = self._parse_expression(base_expr_str)
            return IRAwait(expression=base_expr)

        # Function calls
        if '(' in expr_str and expr_str.endswith(')'):
            paren_idx = expr_str.index('(')
            func_name = expr_str[:paren_idx].strip()
            args_str = expr_str[paren_idx+1:-1].strip()

            # Parse arguments
            args = []
            if args_str:
                for arg_str in self._smart_split(args_str, ','):
                    args.append(self._parse_expression(arg_str.strip()))

            return IRCall(
                function=IRIdentifier(name=func_name),
                args=args
            )

        # Default: identifier
        return IRIdentifier(name=expr_str)

    # ========================================================================
    # Utility Methods
    # ========================================================================

    def _extract_module_name(self, file_path: str) -> str:
        """Extract module name from file path."""
        import os
        basename = os.path.basename(file_path)
        return basename.replace('.rs', '').replace('-', '_')

    def _extract_function_body(self, source: str, brace_start: int) -> str:
        """Extract function body by matching braces."""
        depth = 0
        i = brace_start

        while i < len(source):
            if source[i] == '{':
                depth += 1
            elif source[i] == '}':
                depth -= 1
                if depth == 0:
                    return source[brace_start+1:i]
            i += 1

        return source[brace_start+1:]

    def _is_inside_trait_or_impl(self, source: str, pos: int) -> bool:
        """Check if position is inside a trait or impl block."""
        # Look backward for 'trait' or 'impl' keyword
        before = source[:pos]

        # Count braces to see if we're inside a block
        trait_matches = list(re.finditer(r'\btrait\s+\w+\s*\{', before))
        impl_matches = list(re.finditer(r'\bimpl\s+(?:\w+\s+for\s+)?\w+\s*\{', before))

        for match in trait_matches + impl_matches:
            block_start = match.end() - 1
            # Check if we're inside this block
            depth = 0
            for i in range(block_start, pos):
                if source[i] == '{':
                    depth += 1
                elif source[i] == '}':
                    depth -= 1
                    if depth == 0:
                        break
            if depth > 0:
                return True

        return False

    def _smart_split(self, text: str, delimiter: str) -> List[str]:
        """Split text by delimiter, respecting nested brackets."""
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

    def _extract_ownership_info(self, params_str: str) -> Dict[str, str]:
        """Extract ownership information from parameters."""
        ownership_info = {}

        # Look for &, &mut, mut patterns
        for param in params_str.split(','):
            param = param.strip()
            if not param:
                continue

            if '&mut' in param:
                ownership_info[param.split(':')[0].strip()] = 'borrowed_mutable'
            elif '&' in param:
                ownership_info[param.split(':')[0].strip()] = 'borrowed_immutable'
            elif 'mut' in param:
                ownership_info[param.split(':')[0].strip()] = 'owned_mutable'
            else:
                ownership_info[param.split(':')[0].strip()] = 'owned_immutable'

        return ownership_info


# ============================================================================
# Convenience Functions
# ============================================================================


def parse_rust_file(file_path: str) -> IRModule:
    """
    Parse a Rust file into IR.

    Args:
        file_path: Path to .rs file

    Returns:
        IRModule
    """
    parser = RustParserV2()
    return parser.parse_file(file_path)


def parse_rust_code(source_code: str, module_name: str = "module") -> IRModule:
    """
    Parse Rust source code string into IR.

    Args:
        source_code: Rust source code
        module_name: Name for the module

    Returns:
        IRModule
    """
    import tempfile
    import os

    # Write to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.rs', delete=False) as f:
        f.write(source_code)
        temp_path = f.name

    try:
        parser = RustParserV2()
        module = parser.parse_file(temp_path)
        module.name = module_name
        return module
    finally:
        os.unlink(temp_path)
