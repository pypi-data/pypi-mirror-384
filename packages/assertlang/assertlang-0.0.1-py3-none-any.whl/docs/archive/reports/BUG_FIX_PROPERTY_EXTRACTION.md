# Bug Fix: Constructor Property Extraction

**Date**: 2025-10-05
**Component**: Python Parser V2 (`language/python_parser_v2.py`)
**Severity**: Medium (functionality gap)
**Status**: ✅ FIXED

---

## Issue Description

### Problem
When parsing Python classes, properties defined in the constructor via `self.property = value` assignments were **not being extracted** to the IR class properties list.

### Example
```python
class UserService:
    def __init__(self, database):
        self.db = database      # Not extracted ❌
        self.cache = {}         # Not extracted ❌
```

**Current behavior**: Properties list was EMPTY
**Expected behavior**: Properties list should have `db` and `cache`

### Impact
- Generators couldn't see constructor-defined properties
- Generated code was incomplete
- Round-trip translation lost property information
- Common Python pattern (properties in __init__) was not supported

---

## Root Cause

The parser's `_convert_class()` method:
1. ✅ Correctly extracted class-level annotated properties (`name: str = "default"`)
2. ✅ Correctly parsed constructor into IR function
3. ❌ **Did NOT scan constructor body for property assignments**

The constructor body was converted to IR statements (`IRAssignment` nodes), but these assignments were never analyzed to extract properties.

---

## Solution

### Implementation

**File**: `/Users/hustlermain/HUSTLER_CONTENT/HSTLR/DEV/AssertLang/language/python_parser_v2.py`

#### 1. Added Property Extraction Logic (Lines 291-308)

After parsing the constructor, scan its body for property assignments:

```python
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
```

**Key features**:
- Scans constructor body for `IRAssignment` nodes
- Detects `self.property` pattern in assignment targets
- Infers type from assignment value
- Avoids duplicates (doesn't add if already in properties list)

#### 2. Added Type Inference from IR (Lines 483-557)

Created `_infer_expr_type_from_ir()` method to infer types from IR expressions:

```python
def _infer_expr_type_from_ir(self, expr: Any) -> IRType:
    """Infer type from an IR expression node."""

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
        # Infer array element type from first element
        if expr.elements:
            elem_type = self._infer_expr_type_from_ir(expr.elements[0])
            return IRType(name='array', generic_args=[elem_type])
        return IRType(name='array', generic_args=[IRType(name='any')])

    # ... (similar logic for IRMap, IRBinaryOp, IRCall, etc.)

    return IRType(name='any')
```

**Supports**:
- Literals (null, bool, int, float, string)
- Collections (array, map with generic types)
- Binary operations (infers numeric or bool types)
- Function calls (infers from function name)
- Ternary expressions
- Identifiers (looks up in type context)

---

## Testing

### Test Suite
Created comprehensive test suite: `/Users/hustlermain/HUSTLER_CONTENT/HSTLR/DEV/AssertLang/tests/test_constructor_property_extraction.py`

### Test Cases

#### 1. Basic Property Extraction
```python
class UserService:
    def __init__(self, database):
        self.db = database
        self.cache = {}
```
✅ Result: 2 properties extracted (db, cache)

#### 2. Type Inference
```python
class UserService:
    def __init__(self, db, cache=None):
        self.database = db
        self.cache = cache or {}
        self.count = 0
        self.active = True
        self.name = "service"
```
✅ Result: 5 properties with correct types (count=int, active=bool, name=string, etc.)

#### 3. Mixed Annotations and Constructor
```python
class UserService:
    name: str = "default"
    version: int = 1

    def __init__(self, database):
        self.db = database
        self.cache = {}
```
✅ Result: 4 properties (2 annotated + 2 from constructor)

#### 4. No Duplicates
```python
class UserService:
    db: str

    def __init__(self, database):
        self.db = database  # Same name as annotation
        self.cache = {}
```
✅ Result: 2 properties (db not duplicated, cache added)

#### 5. Classes Without Constructors
```python
class UserService:
    name: str = "default"

    def get_name(self):
        return self.name
```
✅ Result: 1 property (annotated only)

#### 6. Complex Assignments
```python
class Service:
    def __init__(self, config):
        self.config = config
        self.data = []
        self.mapping = {}
        self.enabled = True
        self.timeout = 30
        self.factor = 1.5
```
✅ Result: 6 properties with correct inferred types (array, map, bool, int, float)

#### 7. Code Generation
```python
class UserService:
    def __init__(self, database):
        self.db = database
        self.cache = {}
        self.count = 0
```
✅ Result: All properties appear in generated Python code

---

## Test Results

```bash
$ PYTHONPATH=. python3 tests/test_constructor_property_extraction.py

✅ test_basic_constructor_properties
✅ test_constructor_properties_with_types
✅ test_mixed_annotated_and_constructor_properties
✅ test_no_duplicate_properties
✅ test_class_without_constructor
✅ test_constructor_with_complex_assignments
✅ test_constructor_properties_in_generated_code

🎉 All tests passed!
```

**Success Rate**: 7/7 tests (100%)

---

## Files Changed

### Modified
1. `/Users/hustlermain/HUSTLER_CONTENT/HSTLR/DEV/AssertLang/language/python_parser_v2.py`
   - Added property extraction logic in `_convert_class()` (lines 291-308)
   - Added `_infer_expr_type_from_ir()` method (lines 483-557)
   - Total: +92 lines

### Created
1. `/Users/hustlermain/HUSTLER_CONTENT/HSTLR/DEV/AssertLang/tests/test_constructor_property_extraction.py`
   - Comprehensive test suite (157 lines)
   - 7 test cases covering all scenarios

---

## Validation

### Before Fix
```python
# Parsing this class:
class UserService:
    def __init__(self, database):
        self.db = database
        self.cache = {}

# Result:
cls.properties = []  # EMPTY ❌
```

### After Fix
```python
# Parsing the same class:
class UserService:
    def __init__(self, database):
        self.db = database
        self.cache = {}

# Result:
cls.properties = [
    IRProperty(name='db', prop_type=IRType(name='any')),
    IRProperty(name='cache', prop_type=IRType(name='map'))
]  # CORRECT ✅
```

### Generated Code Validation
```python
# Generated Python code now includes all properties:
class UserService:
    def __init__(self, database: Any) -> None:
        self.db = database
        self.cache = {}
```
✅ All properties present in generated code

---

## Impact

### Benefits
1. ✅ **Complete property extraction** - No information loss
2. ✅ **Accurate type inference** - Properties have correct types
3. ✅ **Round-trip preservation** - Properties maintained through translation
4. ✅ **Generator compatibility** - All generators can now access constructor properties
5. ✅ **Common Python patterns** - Supports standard Python class initialization

### No Breaking Changes
- Backward compatible with existing code
- All existing tests still pass
- Only adds missing functionality

---

## Future Enhancements

### Potential Improvements
1. **Better type inference** - Analyze parameter types to infer property types
2. **Setter detection** - Detect properties defined via setters
3. **Property decorators** - Support @property decorated methods
4. **Type hints** - Use parameter type hints for property types

### Related Work
- Similar logic needed for other language parsers (Node.js, Rust, .NET)
- Consider extracting common property detection patterns

---

## References

### Code Locations
- **Parser**: `/Users/hustlermain/HUSTLER_CONTENT/HSTLR/DEV/AssertLang/language/python_parser_v2.py`
- **Tests**: `/Users/hustlermain/HUSTLER_CONTENT/HSTLR/DEV/AssertLang/tests/test_constructor_property_extraction.py`
- **IR Types**: `/Users/hustlermain/HUSTLER_CONTENT/HSTLR/DEV/AssertLang/dsl/ir.py`

### Documentation
- **CURRENT_WORK.md** - Updated with bug fix details
- **CLAUDE.md** - Project roadmap (Python Parser V2 marked complete)

---

**Fix Validated**: ✅ 2025-10-05
**Next Steps**: Apply similar pattern to Node.js, Rust, .NET parsers
