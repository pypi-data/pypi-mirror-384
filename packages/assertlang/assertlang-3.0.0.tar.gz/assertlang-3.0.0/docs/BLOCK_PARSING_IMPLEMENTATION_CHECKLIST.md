# Block Parsing Implementation Checklist

**Context**: Ready to implement P1-3 fix (method body parsing)
**Estimated Time**: 1-2 hours
**Risk**: Low
**Impact**: High (fixes round-trip translation)

---

## Pre-Implementation Checklist

- [x] Research completed (`docs/BLOCK_PARSING_RESEARCH.md`)
- [x] Implementation guide created (`docs/BLOCK_PARSING_IMPLEMENTATION_EXAMPLE.md`)
- [x] `Current_Work.md` updated
- [x] Existing implementations identified (Node.js, C#, Rust parsers)
- [x] Algorithm validated (80-85% accuracy)
- [x] Edge cases documented

---

## Implementation Checklist - Go Parser

### Step 1: Copy Block Extractor Method

- [ ] Open `/Users/hustlermain/HUSTLER_CONTENT/HSTLR/DEV/AssertLang/language/go_parser_v2.py`
- [ ] Find a good location (after `_parse_expression()` method, around line 650)
- [ ] Copy `_extract_block_body()` from `nodejs_parser_v2.py:1004-1030`
- [ ] Paste into `go_parser_v2.py`
- [ ] Verify indentation is correct

**Code to add**:
```python
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
```

---

### Step 2: Add Body Parser Helper

- [ ] Add `_parse_body()` method after `_extract_block_body()`
- [ ] Handle basic statement types (return, if, for, assignment)
- [ ] Add recursion for nested control flow

**Code to add**:
```python
def _parse_body(self, lines: List[str]) -> List[IRNode]:
    """
    Parse a body (list of lines) into IR statements.

    Args:
        lines: List of code lines (body content)

    Returns:
        List of IR statement nodes
    """
    statements = []
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        # Skip empty lines and comments
        if not line or line.startswith('//'):
            i += 1
            continue

        # Parse different statement types
        if line.startswith('return'):
            stmt = self._parse_return_statement(line)
            statements.append(stmt)

        elif line.startswith('if'):
            # Recursive: parse nested if
            stmt = self._parse_if_statement(line, lines, i)
            statements.append(stmt)

        elif line.startswith('for'):
            # Recursive: parse nested for
            stmt = self._parse_for_statement(line, lines, i)
            statements.append(stmt)

        elif ':=' in line or '=' in line:
            stmt = self._parse_assignment(line)
            statements.append(stmt)

        i += 1

    return statements
```

---

### Step 3: Update `_parse_if_statement()`

- [ ] Locate `_parse_if_statement()` method (line 670-685)
- [ ] Replace the `# TODO` section with actual body extraction
- [ ] Add else clause handling

**Current code** (line 683-685):
```python
# TODO: Extract body (multi-line parsing)
# For now, return simple if
return IRIf(condition=condition_expr, then_body=[], else_body=[])
```

**Replace with**:
```python
# Extract body from full source
full_source = '\n'.join(lines)
line_start = sum(len(lines[i]) + 1 for i in range(index))  # +1 for newline
brace_pos_in_line = line.index('{')
brace_pos = line_start + brace_pos_in_line

# Extract block body (content between { and matching })
body_str = self._extract_block_body(full_source, brace_pos)

# Parse body as statements
then_body = []
if body_str.strip():
    body_lines = body_str.split('\n')
    then_body = self._parse_body(body_lines)

# TODO: Handle else clause (future enhancement)
else_body = []

return IRIf(condition=condition_expr, then_body=then_body, else_body=else_body)
```

---

### Step 4: Update `_parse_for_statement()`

- [ ] Locate `_parse_for_statement()` method (line 687-713)
- [ ] Add body extraction (similar to if statement)

**Add after line 703** (after iterator extraction):
```python
# Extract body
full_source = '\n'.join(lines)
line_start = sum(len(lines[i]) + 1 for i in range(index))
brace_pos_in_line = line.index('{')
brace_pos = line_start + brace_pos_in_line

body_str = self._extract_block_body(full_source, brace_pos)

# Parse body as statements
body = []
if body_str.strip():
    body_lines = body_str.split('\n')
    body = self._parse_body(body_lines)
```

**Replace return statement**:
```python
return IRFor(iterator=iterator, iterable=iterable_expr, body=body)
```

---

### Step 5: Write Unit Tests

- [ ] Create test file or add to existing `tests/test_go_parser_v2.py`
- [ ] Add test for simple if
- [ ] Add test for nested if
- [ ] Add test for if-else

**Test code**:
```python
def test_parse_if_with_body():
    """Test if statement with body extraction."""
    source = """
package main

func Calculate(x int) int {
    if x > 100 {
        return 100
    }
    return x
}
"""
    from language.go_parser_v2 import parse_go_source
    module = parse_go_source(source)

    func = module.functions[0]
    assert len(func.body) == 2  # IRIf + IRReturn

    if_stmt = func.body[0]
    assert isinstance(if_stmt, IRIf)
    assert len(if_stmt.then_body) == 1  # Should have IRReturn(100)

    return_stmt = if_stmt.then_body[0]
    assert isinstance(return_stmt, IRReturn)
    assert return_stmt.value.value == 100


def test_parse_nested_if():
    """Test nested if statements."""
    source = """
package main

func Process(x int) int {
    if x > 0 {
        if x > 100 {
            return 100
        }
        return x
    }
    return 0
}
"""
    from language.go_parser_v2 import parse_go_source
    module = parse_go_source(source)

    func = module.functions[0]
    outer_if = func.body[0]

    assert len(outer_if.then_body) == 2  # Nested IRIf + IRReturn

    inner_if = outer_if.then_body[0]
    assert isinstance(inner_if, IRIf)
    assert len(inner_if.then_body) == 1  # IRReturn(100)


def test_parse_for_with_body():
    """Test for loop with body extraction."""
    source = """
package main

func Sum(items []int) int {
    sum := 0
    for _, item := range items {
        sum += item
    }
    return sum
}
"""
    from language.go_parser_v2 import parse_go_source
    module = parse_go_source(source)

    func = module.functions[0]
    for_stmt = func.body[1]  # After sum := 0 assignment

    assert isinstance(for_stmt, IRFor)
    assert len(for_stmt.body) >= 1  # Should have sum += item
```

---

### Step 6: Test Implementation

- [ ] Run unit tests: `PYTHONPATH=/path/to/AssertLang python3 tests/test_go_parser_v2.py`
- [ ] Test with real Go code sample
- [ ] Verify no regression in existing tests

**Test command**:
```bash
cd /Users/hustlermain/HUSTLER_CONTENT/HSTLR/DEV/AssertLang
PYTHONPATH=. python3 tests/test_go_parser_v2.py
```

---

### Step 7: Validate Round-Trip

- [ ] Create test Go file with if/for statements
- [ ] Parse: Go → IR
- [ ] Generate: IR → Go
- [ ] Compile: Verify generated Go compiles
- [ ] Compare: Check if control flow preserved

**Test code**:
```python
# Round-trip test
source = """
package main

func Calculate(x int) int {
    if x > 100 {
        return 100
    }
    return x * 2
}
"""

# Parse
from language.go_parser_v2 import parse_go_source
module = parse_go_source(source)

# Generate
from language.go_generator_v2 import GoGeneratorV2
generator = GoGeneratorV2()
generated = generator.generate(module)

# Check
assert 'if x > 100 {' in generated
assert 'return 100' in generated
assert 'return x * 2' in generated
```

---

## Implementation Checklist - Rust Parser (Optional)

- [ ] Check if Rust parser already has `_extract_function_body()`
- [ ] Verify it works for impl blocks
- [ ] If needed, apply similar changes as Go parser
- [ ] Test with Rust code samples

---

## Post-Implementation Checklist

- [ ] All unit tests passing
- [ ] Round-trip test compiles
- [ ] No regression in existing tests
- [ ] Performance acceptable (< 15% overhead)
- [ ] Documentation updated:
  - [ ] `Current_Work.md` - Mark P1-3 as COMPLETE
  - [ ] `docs/GO_PARSER_V2.md` - Update known limitations section
- [ ] Commit changes with descriptive message
- [ ] Push to origin (backup)

**Commit message template**:
```
feat: Implement block body parsing in Go parser

- Add _extract_block_body() method (copied from Node.js parser)
- Update _parse_if_statement() to extract then/else bodies
- Update _parse_for_statement() to extract loop body
- Add _parse_body() helper for recursive statement parsing
- Add 3 unit tests (simple if, nested if, for loop)

Fixes P1-3 bug: Control flow logic now preserved in round-trip translation

Test Results:
- All existing tests still passing
- 3 new tests passing
- Round-trip Go → IR → Go compiles successfully

Accuracy: 80-85% (handles nested blocks, empty blocks)
Known limitation: Strings/comments with braces (rare, acceptable for MVP)

References:
- docs/BLOCK_PARSING_RESEARCH.md
- docs/BLOCK_PARSING_IMPLEMENTATION_EXAMPLE.md
```

---

## Success Criteria

✅ **Must Have**:
- [ ] If statements extract then_body correctly
- [ ] For statements extract loop body correctly
- [ ] Nested control flow works (if inside if)
- [ ] Round-trip test compiles (Go → IR → Go)
- [ ] No regression in existing tests

🎯 **Nice to Have**:
- [ ] Else clause handling
- [ ] While loop support
- [ ] Switch statement support

⚠️ **Known Limitations** (acceptable):
- Strings with braces: `"example { brace }"` (rare)
- Comments with braces: `// comment { brace }` (rare)
- Raw strings (Go): `` `example { brace }` `` (rare)

---

## Estimated Timeline

| Task | Time | Status |
|------|------|--------|
| Copy `_extract_block_body()` | 5 min | ☐ |
| Add `_parse_body()` helper | 15 min | ☐ |
| Update `_parse_if_statement()` | 20 min | ☐ |
| Update `_parse_for_statement()` | 15 min | ☐ |
| Write unit tests | 20 min | ☐ |
| Test implementation | 15 min | ☐ |
| Validate round-trip | 15 min | ☐ |
| Documentation updates | 10 min | ☐ |
| **TOTAL** | **1-2 hours** | ☐ |

---

## Troubleshooting

### Issue: Body extraction returns empty string

**Check**:
1. Is `start_index` pointing to `{` character?
2. Is source string complete (not truncated)?
3. Are there unmatched braces in source?

**Debug**:
```python
print(f"start_index: {start_index}")
print(f"char at start: {repr(source[start_index])}")
print(f"source preview: {repr(source[start_index:start_index+50])}")
```

---

### Issue: Nested blocks not parsed correctly

**Check**:
1. Is `_parse_body()` calling `_parse_if_statement()` recursively?
2. Are line indices calculated correctly?

**Debug**:
```python
print(f"Body lines: {body_lines}")
print(f"Parsed statements: {[type(s).__name__ for s in statements]}")
```

---

### Issue: Performance regression

**Check**:
1. Block extraction is O(n), should be fast
2. Measure parsing time before/after

**Benchmark**:
```python
import time
start = time.time()
module = parse_go_source(large_source)
elapsed = time.time() - start
print(f"Parse time: {elapsed:.3f}s")
```

---

## Next Steps After Completion

1. Mark P1-3 as COMPLETE in `Current_Work.md`
2. Update roadmap to Phase 2 bugs (P2 priority)
3. Consider state machine upgrade (Phase 2) if edge cases problematic
4. Test with more complex real-world Go code
5. Apply similar fix to other languages if needed

---

**Created**: 2025-10-06
**Status**: Ready for Implementation ✅
**Next Agent**: Implement checklist in `language/go_parser_v2.py`
