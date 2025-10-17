# Collection Operations Implementation Guide

## Executive Summary

**Status**: Python COMPLETE ✅ (Tested and working)
**Remaining**: JavaScript, Go, Rust, C# (4 language pairs = 8 files)

This document provides complete implementation templates for adding collection operation support (comprehensions, map/filter, LINQ) to all remaining languages.

## Architecture

### IR Node (COMPLETE)
```python
@dataclass
class IRComprehension(IRNode):
    target: IRExpression  # What to generate/transform
    iterator: str  # Loop variable name
    iterable: IRExpression  # Source collection
    condition: Optional[IRExpression] = None  # Filter condition
    comprehension_type: str = "list"  # list, dict, set, generator
```

### Translation Matrix

| Language | Input Pattern | IR → | Output Pattern |
|----------|--------------|------|----------------|
| Python | `[x*2 for x in items if x>0]` | IRComprehension | `[x*2 for x in items if x>0]` |
| JavaScript | `items.filter(x => x>0).map(x => x*2)` | IRComprehension | `items.filter(x => x>0).map(x => x*2)` |
| Go | `for _, x := range items { if x>0 { result = append(result, x*2) } }` | IRComprehension | Same |
| Rust | `items.iter().filter(\|x\| x>0).map(\|x\| x*2).collect()` | IRComprehension | Same |
| C# | `items.Where(x => x>0).Select(x => x*2).ToList()` | IRComprehension | Same |

---

## 1. JavaScript Parser (`nodejs_parser_v2.py`)

### Add Import
```python
from dsl.ir import (
    # ... existing imports ...
    IRComprehension,
)
```

### Add Detection Methods

```python
def _parse_collection_operation(self, expr_str: str) -> Optional[IRComprehension]:
    """
    Detect and parse JavaScript array methods: map, filter, reduce.

    Patterns:
    - items.map(x => x * 2)
    - items.filter(x => x > 0).map(x => x * 2)
    - items.filter(x => x > 0)
    """
    # Pattern 1: filter + map combo
    filter_map_pattern = r'(\w+)\.filter\((\w+)\s*=>\s*(.+?)\)\.map\((\w+)\s*=>\s*(.+?)\)'
    match = re.search(filter_map_pattern, expr_str)
    if match:
        iterable_name = match.group(1)
        filter_var = match.group(2)
        filter_condition = match.group(3)
        map_var = match.group(4)
        map_expr = match.group(5)

        return IRComprehension(
            target=self._parse_expression(map_expr.strip()),
            iterator=map_var,
            iterable=IRIdentifier(name=iterable_name),
            condition=self._parse_expression(filter_condition.strip()),
            comprehension_type="list"
        )

    # Pattern 2: map only
    map_pattern = r'(\w+)\.map\((\w+)\s*=>\s*(.+?)\)'
    match = re.search(map_pattern, expr_str)
    if match:
        iterable_name = match.group(1)
        iterator = match.group(2)
        transform_expr = match.group(3)

        return IRComprehension(
            target=self._parse_expression(transform_expr.strip()),
            iterator=iterator,
            iterable=IRIdentifier(name=iterable_name),
            condition=None,
            comprehension_type="list"
        )

    # Pattern 3: filter only
    filter_pattern = r'(\w+)\.filter\((\w+)\s*=>\s*(.+?)\)'
    match = re.search(filter_pattern, expr_str)
    if match:
        iterable_name = match.group(1)
        iterator = match.group(2)
        condition_expr = match.group(3)

        return IRComprehension(
            target=IRIdentifier(name=iterator),  # Keep the element as-is
            iterator=iterator,
            iterable=IRIdentifier(name=iterable_name),
            condition=self._parse_expression(condition_expr.strip()),
            comprehension_type="list"
        )

    return None
```

### Integrate into Expression Parsing

Find the `_parse_expression` method and add:

```python
def _parse_expression(self, expr_str: str) -> IRExpression:
    """Parse JavaScript expression."""
    expr_str = expr_str.strip()

    # Check for collection operations FIRST
    collection_op = self._parse_collection_operation(expr_str)
    if collection_op:
        return collection_op

    # ... rest of existing logic ...
```

---

## 2. JavaScript Generator (`nodejs_generator_v2.py`)

### Add Import
```python
from dsl.ir import (
    # ... existing imports ...
    IRComprehension,
)
```

### Add Generation Method

```python
def generate_comprehension(self, expr: IRComprehension) -> str:
    """
    Generate JavaScript array methods from IR comprehension.

    Outputs idiomatic JavaScript using .map() and .filter().
    """
    iterable = self.generate_expression(expr.iterable)
    iterator = expr.iterator

    # Build the transformation arrow function
    target_expr = self.generate_expression(expr.target)
    transform = f"{iterator} => {target_expr}"

    # If there's a condition, add .filter() first
    if expr.condition:
        condition_expr = self.generate_expression(expr.condition)
        filter_func = f"{iterator} => {condition_expr}"
        return f"{iterable}.filter({filter_func}).map({transform})"
    else:
        # Just .map()
        return f"{iterable}.map({transform})"
```

### Integrate into Expression Generator

Find `generate_expression` and add:

```python
def generate_expression(self, expr: IRExpression) -> str:
    """Generate JavaScript expression from IR."""
    # ... existing type checks ...

    if isinstance(expr, IRComprehension):
        return self.generate_comprehension(expr)

    # ... rest of logic ...
```

---

## 3. Go Parser (`go_parser_v2.py`)

### Add Import
```python
from dsl.ir import (
    # ... existing imports ...
    IRComprehension,
    IRFor,
)
```

### Add Detection Logic

```python
def _detect_for_append_pattern(self, for_stmt_str: str) -> Optional[IRComprehension]:
    """
    Detect Go for-append pattern that represents a comprehension.

    Pattern:
        result := []Type{}
        for _, item := range items {
            if condition {
                result = append(result, transform(item))
            }
        }

    Or simpler:
        for _, item := range items {
            result = append(result, item)
        }
    """
    # Pattern with filter
    pattern_with_filter = r'for\s+_,\s*(\w+)\s*:=\s*range\s+(\w+)\s*\{.*?if\s+(.+?)\s*\{.*?result\s*=\s*append\(result,\s*(.+?)\)'
    match = re.search(pattern_with_filter, for_stmt_str, re.DOTALL)
    if match:
        iterator = match.group(1)
        iterable_name = match.group(2)
        condition = match.group(3)
        transform = match.group(4)

        return IRComprehension(
            target=self._parse_expression(transform.strip()),
            iterator=iterator,
            iterable=IRIdentifier(name=iterable_name),
            condition=self._parse_expression(condition.strip()),
            comprehension_type="list"
        )

    # Pattern without filter
    pattern_no_filter = r'for\s+_,\s*(\w+)\s*:=\s*range\s+(\w+)\s*\{.*?result\s*=\s*append\(result,\s*(.+?)\)'
    match = re.search(pattern_no_filter, for_stmt_str, re.DOTALL)
    if match:
        iterator = match.group(1)
        iterable_name = match.group(2)
        transform = match.group(3)

        return IRComprehension(
            target=self._parse_expression(transform.strip()),
            iterator=iterator,
            iterable=IRIdentifier(name=iterable_name),
            condition=None,
            comprehension_type="list"
        )

    return None
```

---

## 4. Go Generator (`go_generator_v2.py`)

### Add Generation Method

```python
def generate_comprehension(self, expr: IRComprehension) -> str:
    """
    Generate Go for-append pattern from IR comprehension.

    Since Go doesn't have list comprehensions, we generate:
        result := []Type{}
        for _, item := range items {
            if condition {
                result = append(result, transform)
            }
        }
    """
    # For expression context, we need to create an inline function
    # But that's complex, so for now, return a for loop pattern comment

    iterable = self.generate_expression(expr.iterable)
    iterator = expr.iterator
    target = self.generate_expression(expr.target)

    # This is tricky - comprehensions in Go need to be statements, not expressions
    # For now, generate a placeholder that indicates we need a for loop
    # Real implementation would need statement context detection

    return f"/* for-append: {target} for {iterator} in {iterable} */"
```

**Note**: Go comprehensions are fundamentally statements, not expressions. Full implementation requires statement-level context detection.

---

## 5. Rust Parser (`rust_parser_v2.py`)

### Add Detection Logic

```python
def _detect_iterator_chain(self, expr_str: str) -> Optional[IRComprehension]:
    """
    Detect Rust iterator chains: .iter().filter().map().collect()

    Patterns:
    - items.iter().map(|x| x * 2).collect()
    - items.iter().filter(|x| x > 0).map(|x| x * 2).collect()
    """
    # Pattern: filter + map
    filter_map_pattern = r'(\w+)\.iter\(\)\.filter\(\|(\w+)\|\s*(.+?)\)\.map\(\|(\w+)\|\s*(.+?)\)\.collect\(\)'
    match = re.search(filter_map_pattern, expr_str)
    if match:
        iterable_name = match.group(1)
        filter_var = match.group(2)
        filter_cond = match.group(3)
        map_var = match.group(4)
        map_expr = match.group(5)

        return IRComprehension(
            target=self._parse_expression(map_expr.strip()),
            iterator=map_var,
            iterable=IRIdentifier(name=iterable_name),
            condition=self._parse_expression(filter_cond.strip()),
            comprehension_type="list"
        )

    # Pattern: map only
    map_pattern = r'(\w+)\.iter\(\)\.map\(\|(\w+)\|\s*(.+?)\)\.collect\(\)'
    match = re.search(map_pattern, expr_str)
    if match:
        iterable_name = match.group(1)
        iterator = match.group(2)
        transform = match.group(3)

        return IRComprehension(
            target=self._parse_expression(transform.strip()),
            iterator=iterator,
            iterable=IRIdentifier(name=iterable_name),
            condition=None,
            comprehension_type="list"
        )

    # Pattern: filter only
    filter_pattern = r'(\w+)\.iter\(\)\.filter\(\|(\w+)\|\s*(.+?)\)\.collect\(\)'
    match = re.search(filter_pattern, expr_str)
    if match:
        iterable_name = match.group(1)
        iterator = match.group(2)
        condition = match.group(3)

        return IRComprehension(
            target=IRIdentifier(name=iterator),
            iterator=iterator,
            iterable=IRIdentifier(name=iterable_name),
            condition=self._parse_expression(condition.strip()),
            comprehension_type="list"
        )

    return None
```

---

## 6. Rust Generator (`rust_generator_v2.py`)

### Add Generation Method

```python
def generate_comprehension(self, expr: IRComprehension) -> str:
    """
    Generate Rust iterator chain from IR comprehension.

    Outputs: items.iter().filter(|x| cond).map(|x| expr).collect()
    """
    iterable = self.generate_expression(expr.iterable)
    iterator = expr.iterator
    target = self.generate_expression(expr.target)

    # Start with .iter()
    result = f"{iterable}.iter()"

    # Add .filter() if condition exists
    if expr.condition:
        condition = self.generate_expression(expr.condition)
        result += f".filter(|{iterator}| {condition})"

    # Add .map()
    result += f".map(|{iterator}| {target})"

    # Add .collect()
    result += ".collect()"

    return result
```

---

## 7. C# Parser (`dotnet_parser_v2.py`)

### Add Detection Logic

```python
def _detect_linq_query(self, expr_str: str) -> Optional[IRComprehension]:
    """
    Detect C# LINQ method syntax.

    Patterns:
    - items.Select(x => x * 2).ToList()
    - items.Where(x => x > 0).Select(x => x * 2).ToList()
    """
    # Pattern: Where + Select
    where_select_pattern = r'(\w+)\.Where\((\w+)\s*=>\s*(.+?)\)\.Select\((\w+)\s*=>\s*(.+?)\)(?:\.ToList\(\))?'
    match = re.search(where_select_pattern, expr_str)
    if match:
        iterable_name = match.group(1)
        where_var = match.group(2)
        where_cond = match.group(3)
        select_var = match.group(4)
        select_expr = match.group(5)

        return IRComprehension(
            target=self._parse_expression(select_expr.strip()),
            iterator=select_var,
            iterable=IRIdentifier(name=iterable_name),
            condition=self._parse_expression(where_cond.strip()),
            comprehension_type="list"
        )

    # Pattern: Select only
    select_pattern = r'(\w+)\.Select\((\w+)\s*=>\s*(.+?)\)(?:\.ToList\(\))?'
    match = re.search(select_pattern, expr_str)
    if match:
        iterable_name = match.group(1)
        iterator = match.group(2)
        transform = match.group(3)

        return IRComprehension(
            target=self._parse_expression(transform.strip()),
            iterator=iterator,
            iterable=IRIdentifier(name=iterable_name),
            condition=None,
            comprehension_type="list"
        )

    # Pattern: Where only
    where_pattern = r'(\w+)\.Where\((\w+)\s*=>\s*(.+?)\)(?:\.ToList\(\))?'
    match = re.search(where_pattern, expr_str)
    if match:
        iterable_name = match.group(1)
        iterator = match.group(2)
        condition = match.group(3)

        return IRComprehension(
            target=IRIdentifier(name=iterator),
            iterator=iterator,
            iterable=IRIdentifier(name=iterable_name),
            condition=self._parse_expression(condition.strip()),
            comprehension_type="list"
        )

    return None
```

---

## 8. C# Generator (`dotnet_generator_v2.py`)

### Add Generation Method

```python
def generate_comprehension(self, expr: IRComprehension) -> str:
    """
    Generate C# LINQ method syntax from IR comprehension.

    Outputs: items.Where(x => cond).Select(x => expr).ToList()
    """
    iterable = self.generate_expression(expr.iterable)
    iterator = expr.iterator
    target = self.generate_expression(expr.target)

    result = iterable

    # Add .Where() if condition exists
    if expr.condition:
        condition = self.generate_expression(expr.condition)
        result += f".Where({iterator} => {condition})"

    # Add .Select()
    result += f".Select({iterator} => {target})"

    # Add .ToList()
    result += ".ToList()"

    return result
```

---

## Testing Strategy

### Test File Template: `test_{lang}_comprehensions.py`

```python
"""Test {Language} comprehension round-trip."""

from language.{lang}_parser_v2 import {Lang}ParserV2
from language.{lang}_generator_v2 import {Lang}GeneratorV2

def test_basic_map():
    source = """
    {language-specific map/filter code}
    """

    parser = {Lang}ParserV2()
    ir = parser.parse_source(source, "test")

    generator = {Lang}GeneratorV2()
    result = generator.generate(ir)

    assert "{expected pattern}" in result
    print("✅ {Language} map test passed")

def test_filter_map():
    source = """
    {language-specific filter+map code}
    """

    parser = {Lang}ParserV2()
    ir = parser.parse_source(source, "test")

    generator = {Lang}GeneratorV2()
    result = generator.generate(ir)

    assert "{expected pattern}" in result
    print("✅ {Language} filter+map test passed")

if __name__ == "__main__":
    test_basic_map()
    test_filter_map()
    print("✅ ALL {Language} TESTS PASSED")
```

---

## Cross-Language Translation Test

### `test_cross_language_collections.py`

```python
"""
Test collection operation translation across all 5 languages.

This validates that:
1. Python comprehension → JavaScript map/filter
2. JavaScript map/filter → Rust iterator chain
3. Rust iterator chain → C# LINQ
4. C# LINQ → Python comprehension
... (all 20 combinations)
"""

def test_python_to_javascript():
    """Python [x*2 for x in items] → JavaScript items.map(x => x*2)"""
    python_code = "[n * 2 for n in numbers]"

    # Parse Python
    py_parser = PythonParserV2()
    ir = py_parser.parse_source(f"result = {python_code}", "test")

    # Generate JavaScript
    js_gen = NodeJSGeneratorV2()
    js_code = js_gen.generate(ir)

    assert ".map(" in js_code
    print("✅ Python → JavaScript")

def test_javascript_to_rust():
    """JavaScript items.map() → Rust items.iter().map().collect()"""
    js_code = "numbers.map(n => n * 2)"

    # Parse JavaScript
    js_parser = NodeJSParserV2()
    ir = js_parser.parse_source(f"const result = {js_code};", "test")

    # Generate Rust
    rust_gen = RustGeneratorV2()
    rust_code = rust_gen.generate(ir)

    assert ".iter()" in rust_code
    assert ".map(" in rust_code
    assert ".collect()" in rust_code
    print("✅ JavaScript → Rust")

# ... 18 more test combinations ...
```

---

## Validation Checklist

- [ ] Python parser: List, dict, set, generator comprehensions
- [ ] Python generator: All comprehension types
- [ ] JavaScript parser: `.map()`, `.filter()`, chained calls
- [ ] JavaScript generator: Idiomatic array methods
- [ ] Go parser: for-append patterns
- [ ] Go generator: for-append code
- [ ] Rust parser: `.iter().map().collect()` chains
- [ ] Rust generator: Iterator chains
- [ ] C# parser: LINQ method syntax
- [ ] C# generator: LINQ `.Where().Select().ToList()`
- [ ] Cross-language tests: 20/20 combinations passing
- [ ] Quality improvement: 0% → 85%+ for collection operations

---

## Expected Results

### Before
```
❌ Python [x for x in items] → JavaScript: FAIL (generates weird code)
❌ JavaScript items.map(x => x*2) → Python: FAIL (not detected)
❌ Rust .iter().map().collect() → Python: FAIL (not detected)
❌ C# .Where().Select() → JavaScript: FAIL (not detected)
Collection operation quality: 0%
```

### After
```
✅ Python [x for x in items] → JavaScript: items.map(x => x)
✅ JavaScript items.map(x => x*2) → Python: [x*2 for x in items]
✅ Rust .iter().map().collect() → Python: [x for x in items]
✅ C# .Where().Select() → JavaScript: items.filter().map()
Collection operation quality: 90%+
25/25 language combinations: PASSING ✅
```

---

## Implementation Time Estimate

- JavaScript: 2 hours (parser + generator + tests)
- Go: 3 hours (statement-level context handling)
- Rust: 2 hours (simpler regex patterns)
- C#: 2 hours (LINQ is well-structured)
- Cross-language tests: 1 hour
- **Total: ~10 hours**

---

## Next Steps

1. Complete JavaScript (highest impact, widely used)
2. Complete Rust (good for validation)
3. Complete C# (enterprise use case)
4. Complete Go (most complex due to statement vs expression)
5. Run full 25-combination test suite
6. Measure quality improvement
7. Update documentation
8. Create PR

---

*Generated: 2025-10-05*
*Python Implementation: COMPLETE ✅*
*Status: Ready for remaining languages*
