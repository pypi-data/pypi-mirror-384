# How to Write Your First Contract

**Create and validate your first AssertLang contract in 10 minutes.**

---

## What You'll Learn

- Write a function with preconditions and postconditions
- Validate contract syntax
- Generate Python code with contracts
- Test the generated code

**Prerequisites**: AssertLang installed (`pip install promptware`)

**Time**: 10 minutes

**Difficulty**: Beginner

---

## Step 1: Create Your Contract File

Create a file called `calculator.al`:

```al
function add(x: int, y: int) -> int {
    @requires x_positive: x > 0
    @requires y_positive: y > 0

    @ensures result_positive: result > 0
    @ensures sum_correct: result == x + y

    return x + y;
}

function subtract(x: int, y: int) -> int {
    @requires x_greater: x > y

    @ensures result_positive: result > 0
    @ensures diff_correct: result == x - y

    return x - y;
}
```

**What this does**:
- `add`: Requires both inputs positive, ensures result positive and correct
- `subtract`: Requires x > y (no negative results), ensures result positive

---

## Step 2: Validate the Contract

Check syntax and structure:

```bash
promptware validate calculator.al
```

**Expected output**:
```
🔍 Validating calculator.pw...
✓ Syntax valid
```

**If you get errors**:
- Check for typos (`:` after clause names, `;` after statements)
- Verify brackets match (`{` and `}`)
- Ensure contract annotations start with `@`

---

## Step 3: Generate Python Code

Compile to Python:

```bash
asl build calculator.al -o calculator.py
```

**Expected output**:
```
✓ Compiled calculator.al → calculator.py
```

**View generated code**:

```bash
cat calculator.py
```

**Output** (formatted):
```python
from promptware.runtime.contracts import check_precondition, check_postcondition

def add(x: int, y: int) -> int:
    # Preconditions
    check_precondition(
        x > 0,
        "x_positive",
        "x > 0",
        "add",
        context={"x": x}
    )
    check_precondition(
        y > 0,
        "y_positive",
        "y > 0",
        "add",
        context={"y": y}
    )

    # Implementation
    __result = x + y

    # Postconditions
    check_postcondition(
        __result > 0,
        "result_positive",
        "result > 0",
        "add",
        context={"result": __result}
    )
    check_postcondition(
        __result == x + y,
        "sum_correct",
        "result == x + y",
        "add",
        context={"result": __result, "x": x, "y": y}
    )

    return __result

def subtract(x: int, y: int) -> int:
    # Similar structure...
    check_precondition(x > y, "x_greater", "x > y", "subtract", context={"x": x, "y": y})

    __result = x - y

    check_postcondition(__result > 0, "result_positive", "result > 0", "subtract", context={"result": __result})
    check_postcondition(__result == x - y, "diff_correct", "result == x - y", "subtract", context={"result": __result, "x": x, "y": y})

    return __result
```

---

## Step 4: Test the Generated Code

Create `test_calculator.py`:

```python
from calculator import add, subtract
from promptware.runtime.contracts import ContractViolationError
import pytest

def test_add_valid():
    """Test add with valid inputs."""
    result = add(5, 3)
    assert result == 8

def test_add_rejects_negative():
    """Test add rejects negative inputs."""
    with pytest.raises(ContractViolationError) as exc:
        add(-5, 3)

    assert exc.value.clause == "x_positive"
    assert exc.value.type == "precondition"

def test_subtract_valid():
    """Test subtract with valid inputs."""
    result = subtract(10, 3)
    assert result == 7

def test_subtract_rejects_invalid():
    """Test subtract rejects x <= y."""
    with pytest.raises(ContractViolationError) as exc:
        subtract(3, 10)

    assert exc.value.clause == "x_greater"
```

**Run tests**:

```bash
pytest test_calculator.py -v
```

**Expected output**:
```
test_calculator.py::test_add_valid PASSED
test_calculator.py::test_add_rejects_negative PASSED
test_calculator.py::test_subtract_valid PASSED
test_calculator.py::test_subtract_rejects_invalid PASSED

4 passed in 0.12s
```

---

## Step 5: Try It Interactively

Open Python REPL:

```python
from calculator import add, subtract

# Valid calls
print(add(5, 3))        # Output: 8
print(subtract(10, 3))  # Output: 7

# Invalid calls (will raise ContractViolationError)
add(-5, 3)              # Error: Precondition 'x_positive' failed
subtract(3, 10)         # Error: Precondition 'x_greater' failed
add(0, 0)               # Error: Precondition 'x_positive' failed (0 not > 0)
```

**Example error**:
```
Contract Violation: Precondition
  Function: add
  Clause: 'x_positive'
  Expression: x > 0
  Context:
    x = -5
```

---

## What You Learned

✅ **Write contracts** - Use `@requires` and `@ensures`
✅ **Validate syntax** - Use `promptware validate`
✅ **Generate code** - Use `asl build`
✅ **Test contracts** - Verify violations are caught

---

## Next Steps

**Add more contracts**:
```al
function multiply(x: int, y: int) -> int {
    @requires x_positive: x > 0
    @requires y_positive: y > 0

    @ensures result_greater_than_inputs: result >= x && result >= y

    return x * y;
}
```

**Try other languages**:
```bash
# JavaScript
asl build calculator.al --lang javascript -o calculator.js

# Go
asl build calculator.al --lang go -o calculator.go

# Rust
asl build calculator.al --lang rust -o calculator.rs
```

**Learn more patterns**:
- [Cookbook: Positive Numbers](../../cookbook/validation/positive-numbers.md)
- [Cookbook: Array Bounds](../../cookbook/validation/array-bounds.md)
- [How-To: Generate Code for Multiple Languages](multi-language.md)

---

## Troubleshooting

**Problem**: `promptware: command not found`

**Fix**: Install AssertLang
```bash
pip install promptware
```

---

**Problem**: `ModuleNotFoundError: No module named 'promptware'`

**Fix**: Ensure promptware is installed in your Python environment
```bash
python -m pip install promptware
```

---

**Problem**: Validation fails with "Unexpected token"

**Fix**: Check syntax:
- Colon after clause name: `@requires positive: x > 0` (not `@requires positive x > 0`)
- Semicolon after statements: `return x + y;` (not `return x + y`)
- Matching brackets: `{ ... }`

---

**Problem**: Generated code raises `NameError`

**Fix**: Import runtime module
```python
# At top of file
from promptware.runtime.contracts import check_precondition, check_postcondition
```

---

## See Also

- **[Quickstart Guide](../../../QUICKSTART.md)** - 5-minute overview
- **[Contract Syntax Reference](../../reference/contract-syntax.md)** - Complete syntax
- **[Runtime API](../../reference/runtime-api.md)** - Contract checking functions
- **[Error Codes](../../reference/error-codes.md)** - Debugging violations

---

**[← How-To Index](../index.md)** | **[Generate Multi-Language →](multi-language.md)**
