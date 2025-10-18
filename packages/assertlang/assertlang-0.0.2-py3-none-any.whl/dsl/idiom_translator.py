"""
Idiom Translator - Cross-Language Pattern Conversion

This module handles translation of language-specific idioms that don't have
direct equivalents in other languages:

- Python comprehensions ↔ Go for loops
- Python context managers ↔ Go defer
- Python decorators ↔ Go middleware
- Python f-strings ↔ Go fmt.Sprintf
- Python tuple unpacking ↔ Go multiple assignment

Strategy:
- Detect idiom patterns in source IR
- Transform to equivalent pattern for target language
- Preserve semantics while adapting syntax
"""

from typing import List, Optional, Tuple
from dsl.ir import (
    IRNode,
    IRComprehension,
    IRFor,
    IRIf,
    IRAssignment,
    IRExpression,
    IRStatement,
    IRIdentifier,
    IRCall,
    IRArray,
    IRLiteral,
    IRBinaryOp,
    BinaryOperator,
    LiteralType,
)


class IdiomTranslator:
    """Translate language-specific idioms to equivalent patterns."""

    def __init__(self, source_lang: str, target_lang: str):
        """
        Initialize idiom translator.

        Args:
            source_lang: Source language (python, go, rust, node, dotnet)
            target_lang: Target language
        """
        self.source_lang = source_lang
        self.target_lang = target_lang

    # ========================================================================
    # Comprehension Translation
    # ========================================================================

    def comprehension_to_loop(self, comp: IRComprehension) -> List[IRStatement]:
        """
        Convert list/dict/set comprehension to explicit for loop.

        Python:
            result = [x * 2 for x in items if x > 0]

        Go equivalent:
            result := []int{}
            for _, x := range items {
                if x > 0 {
                    result = append(result, x * 2)
                }
            }

        Returns:
            List of statements (assignment + for loop)
        """
        statements = []

        # 1. Create result variable initialization
        if comp.comprehension_type == "list":
            # result := []Type{}
            init_value = IRArray(elements=[])
        elif comp.comprehension_type == "dict":
            # result := map[K]V{}
            from dsl.ir import IRMap
            init_value = IRMap(entries={})
        elif comp.comprehension_type == "set":
            # result := map[T]bool{}  (Go idiom for sets)
            from dsl.ir import IRMap
            init_value = IRMap(entries={})
        else:
            # Generator - treat as list for now
            init_value = IRArray(elements=[])

        # Use a unique variable name for the result
        result_var = IRIdentifier(name="_comp_result")
        statements.append(IRAssignment(
            target=result_var,
            value=init_value,
            is_declaration=True
        ))

        # 2. Build for loop body
        loop_body = []

        # Add condition if present
        if comp.condition:
            # if condition { append }
            append_stmt = self._create_append_statement(
                result_var, comp.target, comp.comprehension_type
            )
            loop_body.append(IRIf(
                condition=comp.condition,
                then_body=[append_stmt],
                else_body=[]
            ))
        else:
            # Direct append
            append_stmt = self._create_append_statement(
                result_var, comp.target, comp.comprehension_type
            )
            loop_body.append(append_stmt)

        # 3. Create for loop
        for_loop = IRFor(
            iterator=comp.iterator,
            iterable=comp.iterable,
            body=loop_body
        )
        statements.append(for_loop)

        return statements

    def _create_append_statement(
        self,
        result_var: IRIdentifier,
        target: IRExpression,
        comp_type: str
    ) -> IRStatement:
        """Create append/insert statement for comprehension result."""
        if comp_type == "list":
            # result = append(result, target)
            return IRAssignment(
                target=result_var,
                value=IRCall(
                    function=IRIdentifier(name="append"),
                    args=[result_var, target]
                )
            )
        elif comp_type == "dict":
            # result[key] = value
            # Assumes target is a map literal with __key__ and __value__
            # For now, simplify to assignment
            return IRAssignment(target=result_var, value=target)
        elif comp_type == "set":
            # result[item] = true
            return IRAssignment(target=result_var, value=target)
        else:
            # Default: append
            return IRAssignment(
                target=result_var,
                value=IRCall(
                    function=IRIdentifier(name="append"),
                    args=[result_var, target]
                )
            )

    def loop_to_comprehension(
        self,
        for_loop: IRFor,
        prev_assignment: Optional[IRAssignment] = None
    ) -> Optional[IRComprehension]:
        """
        Convert for loop back to comprehension (if it matches pattern).

        Go:
            result := []int{}
            for _, x := range items {
                if x > 0 {
                    result = append(result, x * 2)
                }
            }

        Python equivalent:
            result = [x * 2 for x in items if x > 0]

        Returns:
            IRComprehension if pattern matches, None otherwise
        """
        # Check if this looks like a comprehension pattern:
        # 1. Previous statement is empty array/map initialization
        # 2. For loop body has single if with append, or direct append

        if not prev_assignment:
            return None

        # Check if initialized with empty collection
        if not isinstance(prev_assignment.value, (IRArray,)):
            from dsl.ir import IRMap
            if not isinstance(prev_assignment.value, IRMap):
                return None

        # Empty collection check
        if isinstance(prev_assignment.value, IRArray):
            if len(prev_assignment.value.elements) > 0:
                return None
            comp_type = "list"
        else:
            comp_type = "dict"

        # Analyze loop body
        if len(for_loop.body) == 0:
            return None

        # Pattern 1: Single if statement with append
        if len(for_loop.body) == 1 and isinstance(for_loop.body[0], IRIf):
            if_stmt = for_loop.body[0]
            if len(if_stmt.then_body) == 1:
                append_stmt = if_stmt.then_body[0]
                target = self._extract_append_target(append_stmt)
                if target:
                    return IRComprehension(
                        target=target,
                        iterator=for_loop.iterator,
                        iterable=for_loop.iterable,
                        condition=if_stmt.condition,
                        comprehension_type=comp_type
                    )

        # Pattern 2: Direct append (no condition)
        if len(for_loop.body) == 1:
            append_stmt = for_loop.body[0]
            target = self._extract_append_target(append_stmt)
            if target:
                return IRComprehension(
                    target=target,
                    iterator=for_loop.iterator,
                    iterable=for_loop.iterable,
                    condition=None,
                    comprehension_type=comp_type
                )

        return None

    def _extract_append_target(self, stmt: IRStatement) -> Optional[IRExpression]:
        """Extract the target expression from an append statement."""
        if not isinstance(stmt, IRAssignment):
            return None

        # Check if value is append() call
        if not isinstance(stmt.value, IRCall):
            return None

        call = stmt.value
        if not isinstance(call.function, IRIdentifier):
            return None

        if call.function.name != "append":
            return None

        # append(result, TARGET) - return TARGET
        if len(call.args) >= 2:
            return call.args[1]

        return None

    # ========================================================================
    # Context Manager Translation
    # ========================================================================

    def with_to_defer(self, with_stmt: 'IRWith') -> List[IRStatement]:
        """
        Convert Python with statement to Go defer pattern.

        Python:
            with open("file.txt") as f:
                data = f.read()

        Go equivalent:
            f, err := os.Open("file.txt")
            if err != nil {
                return err
            }
            defer f.Close()
            data, err := f.Read()
        """
        # This is a complex transformation - placeholder for now
        # TODO: Implement full context manager translation
        return []

    # ========================================================================
    # Decorator Translation
    # ========================================================================

    def decorator_to_middleware(self, func: 'IRFunction') -> 'IRFunction':
        """
        Convert Python decorators to Go middleware pattern.

        Python:
            @cached
            @retry(3)
            def fetch_data():
                ...

        Go equivalent:
            func fetchData() {
                // Manual middleware wrapping
            }
        """
        # Placeholder for now
        # TODO: Implement decorator translation
        return func

    # ========================================================================
    # Tuple Unpacking Translation
    # ========================================================================

    def tuple_unpack_to_multi_assign(
        self,
        assignment: IRAssignment
    ) -> List[IRStatement]:
        """
        Convert Python tuple unpacking to Go multiple assignment.

        Python:
            x, y = get_coords()

        Go equivalent:
            x, y := getCoords()

        This is actually similar, but Go requires := for declaration.
        """
        # Most cases are already similar
        # Main difference is declaration syntax
        return [assignment]


# ============================================================================
# Helper Functions
# ============================================================================


def needs_idiom_translation(node: IRNode, source_lang: str, target_lang: str) -> bool:
    """Check if a node needs idiom translation between languages."""

    # Comprehensions: Python/JS → Go/Rust/C#
    if isinstance(node, IRComprehension):
        if source_lang in ["python", "node"] and target_lang in ["go", "rust", "dotnet"]:
            return True

    # For loops that look like comprehensions: Go/Rust → Python/JS
    if isinstance(node, IRFor):
        if source_lang in ["go", "rust", "dotnet"] and target_lang in ["python", "node"]:
            # Check if it's a comprehension pattern (prev statement + loop)
            # This requires context, so return True for now
            return True

    return False


def translate_idiom(
    node: IRNode,
    source_lang: str,
    target_lang: str,
    context: Optional[List[IRStatement]] = None
) -> List[IRStatement]:
    """
    Translate an idiom from source language to target language.

    Args:
        node: IR node to translate
        source_lang: Source language
        target_lang: Target language
        context: Optional surrounding statements for context

    Returns:
        List of transformed statements
    """
    translator = IdiomTranslator(source_lang, target_lang)

    if isinstance(node, IRComprehension):
        # Comprehension → Loop
        return translator.comprehension_to_loop(node)

    elif isinstance(node, IRFor):
        # Possibly Loop → Comprehension
        prev_stmt = context[-1] if context and len(context) > 0 else None
        if isinstance(prev_stmt, IRAssignment):
            comp = translator.loop_to_comprehension(node, prev_stmt)
            if comp:
                # Replace previous assignment + loop with single comprehension
                # Return marker to indicate replacement
                return [comp]  # Caller should handle removing prev statement

    # No translation needed
    return [node]
