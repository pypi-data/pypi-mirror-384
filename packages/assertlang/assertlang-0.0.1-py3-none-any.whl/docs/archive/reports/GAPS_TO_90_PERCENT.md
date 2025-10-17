# Gaps Preventing 90%+ Quality

**Current Quality**: 83-90%
**Target**: 90%+ (ideally 95%+)
**Gap**: ~7-10 percentage points

---

## Critical Bugs Found in Real Code

### 1. Arrow Function Syntax (Line 35) ❌ HIGH PRIORITY

**Current**:
```go
var char interface{} = (arr) => arr[rand.Intn(len(arr))]([]string{"*", "·", "✦", ".", "•"})
```

**Issue**: JavaScript arrow function syntax leaked into Go code - completely invalid

**Expected**:
```go
chars := []string{"*", "·", "✦", ".", "•"}
char := chars[rand.Intn(len(chars))]
```

**Root Cause**: Lambda parser generating JavaScript instead of Go
**Impact**: Code won't compile - **blocks 10%**

---

### 2. Type Inference Gaps - Complex Expressions

**Current**:
```go
var r interface{} = math.Sqrt((math.Pow(dx, 2) + math.Pow(dy, 2)))  // Line 28
var a interface{} = math.Atan2(dy, dx)                               // Line 29
var bright interface{} = math.Pow((math.Cos(swirl) * noise), 2)    // Line 32
```

**Issue**: Type inference fails on function call expressions

**Expected**:
```go
var r float64 = math.Sqrt((math.Pow(dx, 2) + math.Pow(dy, 2)))
var a float64 = math.Atan2(dy, dx)
var bright float64 = math.Pow((math.Cos(swirl) * noise), 2)
```

**Root Cause**: Type inference only handles literals, not call expressions
**Impact**: Type safety lost, mixed-type arithmetic fails - **blocks 5%**

---

### 3. JavaScript Method Calls Leaking Through

**Current**:
```go
t.ToFixed(2)  // Line 53 - JavaScript Number.toFixed()
```

**Issue**: JavaScript methods not translated to Go equivalents

**Expected**:
```go
fmt.Sprintf("%.2f", t)  // Go formatting
```

**Root Cause**: Method mapping incomplete for JS → Go
**Impact**: Code won't compile - **blocks 3%**

---

### 4. Ternary Operator in Statement Context

**Current**:
```go
exec.Command(...).Run(func() interface{} {
    if (os.Name == "nt") { return "cls" } else { return "clear" }
}())
```

**Issue**: Ternary translated to IIFE, but also has placeholder `...` and invalid call chain

**Expected**:
```go
var cmd string
if os.Name == "nt" {
    cmd = "cls"
} else {
    cmd = "clear"
}
exec.Command(cmd).Run()
```

**Root Cause**: Ternary in call argument needs better handling
**Impact**: Won't compile - **blocks 2%**

---

### 5. Multiline String Literals

**Current**:
```go
return strings.Join(output, "
"), nil
```

**Issue**: String literal split across lines incorrectly

**Expected**:
```go
return strings.Join(output, "\n"), nil
```

**Root Cause**: F-string/template literal parsing issue
**Impact**: Syntax error - **blocks 2%**

---

### 6. Type Errors in Arithmetic

**Current**:
```go
var swirl int = (((a * arms) + (r * 12)) - (t * 2))  // a is interface{}, not float64
var t int = 0
t = (t + 0.1)  // int + float = type error
```

**Issue**: Mixed-type arithmetic due to interface{} leakage

**Expected**:
```go
var swirl int = int(((a * float64(arms)) + (r * 12.0)) - (float64(t) * 2.0))
var t float64 = 0.0
t = (t + 0.1)
```

**Root Cause**: Type inference + type coercion missing
**Impact**: Won't compile - **blocks 3%**

---

## Summary of Gaps

| Issue | Priority | Impact | Lines of Code |
|-------|----------|--------|---------------|
| Arrow function syntax | **HIGH** | 10% | Lambda generation |
| Type inference (calls) | **HIGH** | 5% | Type inference engine |
| JS method mapping | MEDIUM | 3% | Library mapping |
| Ternary in args | MEDIUM | 2% | Expression handling |
| Multiline strings | MEDIUM | 2% | String literal parsing |
| Type coercion | MEDIUM | 3% | Type system |

**Total Estimated Impact**: **25 percentage points** (if all fixed)

**Realistic Target**: Fix top 3 issues → **+18%** → **~95-98% quality**

---

## Action Plan to Reach 90%+

### Phase 1: Fix Lambda Generation (HIGH - 10% gain)

**File**: `language/go_generator_v2.py`

**Changes**:
1. Detect lambda in assignment/expression context
2. Never generate arrow function syntax `() =>`
3. Generate proper Go anonymous function `func() { ... }`
4. OR expand to multi-line variable extraction (better)

**Test**: Lambda should become either:
```go
// Option A: Anonymous function (if truly needed)
f := func(arr []string) string { return arr[0] }

// Option B: Expanded code (preferred)
chars := []string{"*", "·", "✦", ".", "•"}
char := chars[rand.Intn(len(chars))]
```

---

### Phase 2: Extend Type Inference (HIGH - 5% gain)

**File**: `dsl/type_inference.py`

**Changes**:
1. Add `IRCall` expression type inference
2. Map function names to return types:
   - `math.Sqrt()` → `float64`
   - `math.Atan2()` → `float64`
   - `math.Pow()` → `float64`
   - `rand.Intn()` → `int`
   - `len()` → `int`
3. Propagate inferred types to assignments

**Test**: Should infer:
```go
var r float64 = math.Sqrt(...)  // Not interface{}
```

---

### Phase 3: Complete Library Mapping (MEDIUM - 3% gain)

**File**: `language/library_mapping.py`

**Changes**:
1. Add JavaScript → Go method mappings:
   - `Number.toFixed(n)` → `fmt.Sprintf("%.{n}f", val)`
   - `String.repeat(n)` → `strings.Repeat(s, n)`
   - `Array.includes(x)` → `Contains(arr, x)` (helper)

**Test**: `t.toFixed(2)` becomes `fmt.Sprintf("%.2f", t)`

---

### Phase 4: Type Coercion System (MEDIUM - 3% gain)

**File**: `dsl/type_system.py`

**Changes**:
1. Detect mixed-type arithmetic
2. Insert type conversions:
   - `interface{} * int` → `float64(...) * float64(...)`
   - `int + float` → `float64(int) + float`
3. Validate type compatibility

---

## Expected Results

| After Phase | Quality | Tests Passing |
|-------------|---------|---------------|
| Current | 83-90% | 5/6 |
| Phase 1 | 90-93% | 6/6 |
| Phase 2 | 93-95% | 6/6 |
| Phase 3 | 95-96% | 6/6 |
| Phase 4 | 96-98% | 6/6 |

**Target**: 90%+ after Phase 1+2 (should take ~2-3 hours)

---

## Testing Strategy

1. Run `test_final_validation.py` after each phase
2. Test real-world code (`test_code_original.py` → Go)
3. Validate generated Go compiles with `go build`
4. Add regression tests for each fix

---

**Next Step**: Start Phase 1 - Fix lambda generation
