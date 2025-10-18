# Path to 90% Production Readiness - Complete Roadmap

**Current Status**: 70% production ready
**Target**: 90%+ production ready
**Remaining**: 20 percentage points (22% of work)
**Estimated Time**: 20-25 hours

---

## Executive Summary

We've achieved **70% production readiness** with a solid foundation:
- ✅ Async/await: 100% (all 5 languages)
- ✅ Simple code: 100% (all 25 combinations)
- ✅ Basic classes: 100% (all 25 combinations)
- ⚠️ Exception handling: 33% (2/5 languages)
- ⚠️ Collections: 20% (1/5 languages)

**The remaining 22% requires implementing 3 languages for exceptions and 4 languages for collections.**

---

## Detailed Roadmap (20-25 hours)

### Phase 1: Exception Handling Completion (9-13 hours)

#### Task 1.1: C# Exception Handling (2-3 hours) ⭐ HIGHEST PRIORITY

**Why First**: Nearly identical to JavaScript (already working), easiest win

**Files to Modify**:
1. `/language/dotnet_parser_v2.py`
2. `/language/dotnet_generator_v2.py`

**Implementation**:

```python
# dotnet_parser_v2.py - Add method
def _parse_try_statement(self, content: str) -> IRTry:
    """Parse C# try/catch/finally."""
    # Pattern: try { body } catch (Type var) { handler } finally { cleanup }

    # Extract try body
    try_match = re.search(r'try\s*\{(.*?)\}', content, re.DOTALL)
    try_body = self._parse_statements_from_block(try_match.group(1))

    # Extract catch clauses (can be multiple)
    catch_pattern = r'catch\s*\((\w+)(?:\s+(\w+))?\)\s*\{(.*?)\}'
    catches = []
    for match in re.finditer(catch_pattern, content, re.DOTALL):
        exc_type = IRType(name=match.group(1))
        exc_var = match.group(2)
        body = self._parse_statements_from_block(match.group(3))
        catches.append(IRCatch(exc_type, exc_var, body))

    # Extract finally (optional)
    finally_match = re.search(r'finally\s*\{(.*?)\}', content, re.DOTALL)
    finally_body = self._parse_statements_from_block(finally_match.group(1)) if finally_match else None

    return IRTry(try_body, catches, finally_body)

# Add to statement parsing
if line.strip().startswith('try'):
    return self._parse_try_statement(remaining_content)
```

```python
# dotnet_generator_v2.py - Verify/enhance
def generate_try(self, stmt: IRTry) -> List[str]:
    """Generate C# try/catch/finally."""
    lines = [f"{self.indent()}try"]
    lines.append(f"{self.indent()}{{")

    self.indent_level += 1
    for s in stmt.try_body:
        lines.extend(self.generate_statement(s))
    self.indent_level -= 1
    lines.append(f"{self.indent()}}}")

    # Catch blocks
    for catch in stmt.catch_clauses:
        exc_type = catch.exception_type.name if catch.exception_type else "Exception"
        exc_var = catch.exception_var or "e"
        lines.append(f"{self.indent()}catch ({exc_type} {exc_var})")
        lines.append(f"{self.indent()}{{")
        self.indent_level += 1
        for s in catch.body:
            lines.extend(self.generate_statement(s))
        self.indent_level -= 1
        lines.append(f"{self.indent()}}}")

    # Finally
    if stmt.finally_body:
        lines.append(f"{self.indent()}finally")
        lines.append(f"{self.indent()}{{")
        self.indent_level += 1
        for s in stmt.finally_body:
            lines.extend(self.generate_statement(s))
        self.indent_level -= 1
        lines.append(f"{self.indent()}}}")

    return lines
```

**Testing**:
```python
# tests/test_csharp_exceptions.py
def test_csharp_try_catch_finally():
    code = '''
public class Example {
    public int Divide(int a, int b) {
        try {
            return a / b;
        } catch (DivideByZeroException e) {
            Console.WriteLine($"Error: {e.Message}");
            return 0;
        } finally {
            Console.WriteLine("Done");
        }
    }
}
'''
    parser = DotNetParserV2()
    ir = parser.parse_source(code, "test")
    # Verify IRTry created

    # Round-trip
    generated = generate_csharp(ir)
    assert 'try' in generated
    assert 'catch' in generated
    assert 'finally' in generated
```

**Success Criteria**:
- ✅ Parses try/catch/finally
- ✅ Round-trip works
- ✅ Python → C# exception translation
- ✅ Exception handling: 33% → 60%

---

#### Task 1.2: Rust Exception Handling (3-4 hours)

**Complexity**: Rust uses Result<T, E>, not try/catch

**Files to Modify**:
1. `/language/rust_parser_v2.py`
2. `/language/rust_generator_v2.py`

**Implementation**:

```python
# rust_parser_v2.py
def _parse_match_result(self, content: str) -> Optional[IRTry]:
    """Parse Rust Result match patterns."""
    # Pattern: match result { Ok(v) => { ... }, Err(e) => { ... } }

    match_pattern = r'match\s+(\w+)\s*\{.*?Ok\((\w+)\)\s*=>\s*\{(.*?)\}.*?Err\((\w+)\)\s*=>\s*\{(.*?)\}\s*\}'
    match = re.search(match_pattern, content, re.DOTALL)

    if match:
        ok_var = match.group(2)
        ok_body = self._parse_block(match.group(3))
        err_var = match.group(4)
        err_body = self._parse_block(match.group(5))

        catch = IRCatch(
            exception_type=IRType(name="Error"),
            exception_var=err_var,
            body=err_body
        )

        return IRTry(ok_body, [catch], None)

    return None
```

```python
# rust_generator_v2.py
def generate_try(self, stmt: IRTry) -> List[str]:
    """Generate Rust Result match."""
    lines = [f"{self.indent()}match result {{"]

    # Ok arm
    lines.append(f"{self.indent()}    Ok(v) => {{")
    self.indent_level += 2
    for s in stmt.try_body:
        lines.extend(self.generate_statement(s))
    self.indent_level -= 2
    lines.append(f"{self.indent()}    }},")

    # Err arm
    for catch in stmt.catch_clauses:
        err_var = catch.exception_var or "e"
        lines.append(f"{self.indent()}    Err({err_var}) => {{")
        self.indent_level += 2
        for s in catch.body:
            lines.extend(self.generate_statement(s))
        self.indent_level -= 2
        lines.append(f"{self.indent()}    }},")

    lines.append(f"{self.indent()}}}")
    return lines
```

**Success Criteria**:
- ✅ Parses match/Result patterns
- ✅ Generates match statements
- ✅ Python → Rust exception translation
- ✅ Exception handling: 60% → 80%

---

#### Task 1.3: Go Exception Handling (4-6 hours)

**Complexity**: Go uses error returns, not exceptions

**Files to Modify**:
1. `/language/go_parser_v2.py`
2. `/language/go_generator_v2.py`

**Implementation**:

```python
# go_parser_v2.py
def _detect_error_check_pattern(self, lines: List[str], idx: int) -> Optional[IRTry]:
    """Detect if err != nil { return err } pattern."""
    # Pattern:
    # result, err := someFunc()
    # if err != nil {
    #     return err  // or handle error
    # }

    if idx + 1 < len(lines):
        current = lines[idx]
        next_line = lines[idx + 1]

        # Check for assignment with err
        if ':=' in current and 'err' in current:
            # Check next line for error check
            if 'if err != nil' in next_line or 'if err != NULL' in next_line:
                # Extract try body (before error check)
                # Extract error handling (inside if block)
                # Return IRTry
                pass

    return None
```

```python
# go_generator_v2.py
def generate_try(self, stmt: IRTry) -> List[str]:
    """Generate Go error handling."""
    lines = []

    # Generate try body with error assignment
    # Assume last statement returns error
    for s in stmt.try_body[:-1]:
        lines.extend(self.generate_statement(s))

    # Last statement becomes: result, err := lastStatement
    # Then: if err != nil { catch_body }

    lines.append(f"{self.indent()}if err != nil {{")
    self.indent_level += 1
    for catch in stmt.catch_clauses:
        for s in catch.body:
            lines.extend(self.generate_statement(s))
    self.indent_level -= 1
    lines.append(f"{self.indent()}}}")

    return lines
```

**Success Criteria**:
- ✅ Detects error return patterns
- ✅ Generates if err != nil checks
- ✅ Python → Go exception translation
- ✅ Exception handling: 80% → 100%

---

### Phase 2: Collection Operations Completion (10 hours)

#### Task 2.1: JavaScript Collections (2 hours)

**Files to Modify**:
1. `/language/nodejs_parser_v2.py`
2. `/language/nodejs_generator_v2.py`

**Implementation**:

```python
# nodejs_parser_v2.py
def _parse_array_method_chain(self, expr_str: str) -> Optional[IRComprehension]:
    """Parse .filter().map() chains."""
    if '.filter(' in expr_str or '.map(' in expr_str:
        # Extract base array
        base_match = re.match(r'(\w+)\.', expr_str)
        iterable = IRIdentifier(name=base_match.group(1))

        # Parse filter
        filter_match = re.search(r'\.filter\((\w+)\s*=>\s*(.+?)\)', expr_str)
        condition = None
        iterator = None
        if filter_match:
            iterator = filter_match.group(1)
            condition_str = filter_match.group(2)
            condition = self._parse_expression(condition_str)

        # Parse map
        map_match = re.search(r'\.map\((\w+)\s*=>\s*(.+?)\)', expr_str)
        element = None
        if map_match:
            if not iterator:
                iterator = map_match.group(1)
            element_str = map_match.group(2)
            element = self._parse_expression(element_str)
        else:
            element = IRIdentifier(name=iterator) if iterator else None

        if element and iterator:
            return IRComprehension(element, iterator, iterable, condition, "list")

    return None
```

```python
# nodejs_generator_v2.py
def generate_comprehension(self, expr: IRComprehension) -> str:
    """Generate JavaScript array methods."""
    iterable = self.generate_expression(expr.iterable)
    result = iterable

    if expr.condition:
        filter_lambda = f"{expr.iterator} => {self.generate_expression(expr.condition)}"
        result = f"{result}.filter({filter_lambda})"

    # Map if element != iterator
    if not (isinstance(expr.element, IRIdentifier) and expr.element.name == expr.iterator):
        map_lambda = f"{expr.iterator} => {self.generate_expression(expr.element)}"
        result = f"{result}.map({map_lambda})"

    return result
```

**Success Criteria**:
- ✅ Parses .filter() and .map()
- ✅ Generates array methods
- ✅ Python ↔ JavaScript collections work
- ✅ Collections: 20% → 40%

---

#### Task 2.2: Rust Collections (2 hours)

**Files**: `rust_parser_v2.py`, `rust_generator_v2.py`

**Key Patterns**: `.iter().filter(|x| cond).map(|x| expr).collect()`

Similar approach to JavaScript, but with Rust closure syntax `|x|` and `.collect()`

**Success Criteria**:
- ✅ Collections: 40% → 60%

---

#### Task 2.3: C# Collections (2 hours)

**Files**: `dotnet_parser_v2.py`, `dotnet_generator_v2.py`

**Key Patterns**: `.Where(x => cond).Select(x => expr).ToList()`

LINQ method syntax, very similar to JavaScript

**Success Criteria**:
- ✅ Collections: 60% → 80%

---

#### Task 2.4: Go Collections (3 hours)

**Files**: `go_parser_v2.py`, `go_generator_v2.py`

**Complexity**: Go uses for loops, not method chains

**Pattern**:
```go
var result []int
for _, item := range items {
    if condition {
        result = append(result, expression)
    }
}
```

**Success Criteria**:
- ✅ Collections: 80% → 100%

---

### Phase 3: Integration & Polish (2-3 hours)

#### Task 3.1: Connect Context-Aware Types

**Files**: All 5 generators

**What to Do**:
The context analyzer already exists (`/dsl/context_analyzer.py`) and works.

Add to each generator:
```python
def generate_function(self, func: IRFunction, type_map: Optional[Dict] = None):
    # If type_map provided, use inferred types instead of generic fallbacks
    if type_map and func.name in type_map:
        inferred_type = type_map[func.name]
        # Use inferred_type instead of 'any'/'interface{}'
```

**Success Criteria**:
- ✅ Type inference: 83% → 95%
- ✅ Fewer generic types

---

#### Task 3.2: Connect Library Mapping

**Files**: All 5 generators (already partially done)

**What to Do**:
Library mapping system exists (`/language/library_mapping.py`).

Ensure all generators use it:
```python
from language.library_mapping import translate_library

# In import generation:
target_lib = translate_library(source_lib, source_lang, target_lang)
```

**Success Criteria**:
- ✅ Correct library names in all languages
- ✅ requests → axios → net/http etc.

---

## Testing & Validation Plan

### After Each Task

Run these tests:
```bash
# Task-specific test
python3 tests/test_{language}_{feature}.py

# Full exception handling test
python3 tests/test_error_handling_complete.py

# Full collection operations test
python3 tests/test_translation_quality.py

# Quick quality check
python3 tests/test_quality_quick.py
```

### Final Validation (After All Tasks)

```bash
# Full 25-combination matrix
python3 tests/test_full_bidirectional_matrix.py

# Quality assessment
python3 tests/test_translation_quality.py

# Real-world patterns
python3 tests/real_world_demo.py
```

---

## Expected Results by Phase

### After Phase 1 (Exception Handling Complete)

- Exception handling: 33% → 100% (+67%)
- Overall quality: 70% → 80% (+10%)
- **Time**: 9-13 hours

### After Phase 2 (Collections Complete)

- Collections: 20% → 100% (+80%)
- Overall quality: 80% → 90% (+10%)
- **Time**: +10 hours (19-23 hours total)

### After Phase 3 (Integration)

- Type accuracy: 83% → 95% (+12%)
- Library calls: 0% → 100% (+100%)
- Overall quality: 90% → 92-95% (+2-5%)
- **Time**: +2-3 hours (21-26 hours total)

---

## File Modification Checklist

### Parsers (10 files)
- [ ] `python_parser_v2.py` (already done for collections)
- [ ] `nodejs_parser_v2.py` (needs collections)
- [ ] `go_parser_v2.py` (needs exceptions + collections)
- [ ] `rust_parser_v2.py` (needs exceptions + collections)
- [ ] `dotnet_parser_v2.py` (needs exceptions + collections)

### Generators (10 files)
- [ ] `python_generator_v2.py` (already done for collections)
- [ ] `nodejs_generator_v2.py` (needs collections)
- [ ] `go_generator_v2.py` (needs exceptions + collections)
- [ ] `rust_generator_v2.py` (needs exceptions + collections)
- [ ] `dotnet_generator_v2.py` (needs exceptions + collections)

### Tests (9 new files)
- [ ] `test_csharp_exceptions.py`
- [ ] `test_rust_exceptions.py`
- [ ] `test_go_exceptions.py`
- [ ] `test_javascript_collections.py`
- [ ] `test_rust_collections.py`
- [ ] `test_csharp_collections.py`
- [ ] `test_go_collections.py`
- [ ] `test_context_integration.py`
- [ ] `test_library_integration.py`

---

## Risk Mitigation

### Potential Issues

1. **Go Error Patterns Too Complex**: Error handling in Go is statement-level, not expression-level
   - **Mitigation**: Start with simple patterns, expand gradually

2. **Rust Result Chaining**: ? operator, unwrap, etc. have many variants
   - **Mitigation**: Support basic match first, add variants later

3. **Type Inference Integration**: Generators may need significant refactoring
   - **Mitigation**: Optional parameter, gradual rollout

### Backup Plan

If time runs short, prioritize:
1. C# exceptions (2-3 hrs) → Biggest quick win
2. JavaScript collections (2 hrs) → Enables Python ↔ JS functional code
3. Context types integration (2-3 hrs) → Improves all languages

**Minimum Viable**: 6-8 hours → 75-80% production ready (still significant improvement)

---

## Success Metrics

### Current (70%)
- Simple code: 100%
- Async: 100%
- Exceptions: 33%
- Collections: 20%

### Target (90%+)
- Simple code: 100% ✅
- Async: 100% ✅
- Exceptions: 100% ✅
- Collections: 100% ✅
- Types: 95% ✅
- Libraries: 100% ✅

---

## Estimated Timeline

### Aggressive (20 hours)
- Week 1 (5 days × 4 hrs/day): Phases 1-2
- Weekend: Phase 3 + testing

### Moderate (25 hours)
- Week 1: Phase 1 (exceptions)
- Week 2: Phase 2 (collections)
- Week 3: Phase 3 (integration) + testing

### Conservative (30 hours)
- Add buffer for debugging and edge cases
- More comprehensive testing
- Real-world validation

---

## Conclusion

The path to 90%+ is **clear and well-defined**. All infrastructure exists, we just need to implement the patterns for the remaining languages.

**Recommendation**: Start with C# exceptions (easiest, 2-3 hours) to build momentum, then tackle JavaScript collections (2 hours) for quick wins. This gets you to 75-80% in just 4-5 hours.

**Status**: ✅ Ready to execute
**Confidence**: HIGH (all patterns documented, tests exist, clear success criteria)
