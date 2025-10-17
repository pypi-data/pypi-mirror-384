# Error Codes Reference

**Complete reference for AssertLang errors and how to fix them.**

---

## Overview

AssertLang errors fall into 4 categories:
1. **Contract Violations** - Runtime contract failures (precondition, postcondition, invariant)
2. **Parse Errors** - Syntax errors in `.pw` files
3. **Validation Errors** - Structural issues in contracts
4. **MCP Errors** - MCP server/client communication errors

---

## Quick Reference

| Error Type | When | Example |
|------------|------|---------|
| `ContractViolationError` | Runtime contract check fails | `Precondition 'positive' failed: x = -5` |
| `PWParseError` | Syntax error in `.pw` file | `Unexpected token at line 5, column 10` |
| `ValidationError` | Invalid contract structure | `Duplicate function definition: add` |
| `MCPError` | MCP communication fails | `Connection refused: localhost:3000` |

---

## Contract Violations

**Runtime errors when contract clauses fail.**

### ContractViolationError

**Type**: Runtime exception
**Raised by**: `check_precondition`, `check_postcondition`, `check_invariant`

**Fields**:
```python
class ContractViolationError(Exception):
    type: str                      # "precondition", "postcondition", or "invariant"
    clause: str                    # Clause name (e.g., "positive")
    expression: str                # Expression (e.g., "x > 0")
    message: str                   # Human-readable message
    function: Optional[str]        # Function name
    class_name: Optional[str]      # Class name (if method)
    location: Optional[str]        # Source location
    context: Dict[str, Any]        # Variable values at failure
```

---

### Precondition Violations

**When**: Function called with invalid inputs

**Error Message Format**:
```
Contract Violation: Precondition
  Function: calculate_total
  Clause: 'price_positive'
  Expression: price > 0.0
  Message: Precondition 'price_positive' violated
  Context:
    price = -10.0
```

**Example 1: Negative Value**

```python
def sqrt(x: float) -> float:
    check_precondition(x >= 0.0, "non_negative", "x >= 0.0", "sqrt", context={"x": x})
    return math.sqrt(x)

sqrt(-5)
```

**Error**:
```
Contract Violation: Precondition
  Function: sqrt
  Clause: 'non_negative'
  Expression: x >= 0.0
  Context:
    x = -5.0
```

**Fix**:
```python
# Validate before calling
if x >= 0:
    result = sqrt(x)
else:
    result = 0.0  # Or handle negative case
```

**Example 2: Empty String**

```python
def process_name(name: str) -> str:
    check_precondition(len(name) > 0, "non_empty", "len(name) > 0", "process_name",
        context={"name": name, "len(name)": len(name)})
    return name.upper()

process_name("")
```

**Error**:
```
Contract Violation: Precondition
  Function: process_name
  Clause: 'non_empty'
  Expression: len(name) > 0
  Context:
    name = ''
    len(name) = 0
```

**Fix**:
```python
# Validate input
if len(name) > 0:
    result = process_name(name)
else:
    result = "UNKNOWN"  # Default value
```

**Example 3: Array Bounds**

```python
def get_item(items: list[str], index: int) -> str:
    check_precondition(
        index >= 0 and index < len(items),
        "valid_index",
        "index >= 0 and index < len(items)",
        "get_item",
        context={"index": index, "len(items)": len(items)}
    )
    return items[index]

get_item(["a", "b"], 5)
```

**Error**:
```
Contract Violation: Precondition
  Function: get_item
  Clause: 'valid_index'
  Expression: index >= 0 and index < len(items)
  Context:
    index = 5
    len(items) = 2
```

**Fix**:
```python
# Check bounds first
if 0 <= index < len(items):
    item = get_item(items, index)
else:
    item = None  # Or raise custom exception
```

---

### Postcondition Violations

**When**: Function returns invalid result (implementation bug)

**Error Message Format**:
```
Contract Violation: Postcondition
  Function: add
  Clause: 'result_positive'
  Expression: result > 0
  Message: Postcondition 'result_positive' violated
  Context:
    result = -10
    x = 5
    y = -15
```

**Example 1: Wrong Result**

```python
def add_positive(x: int, y: int) -> int:
    check_precondition(x > 0, "x_positive", "x > 0", "add_positive", context={"x": x})
    check_precondition(y > 0, "y_positive", "y > 0", "add_positive", context={"y": y})

    result = x - y  # ❌ Bug: should be x + y

    check_postcondition(result > 0, "result_positive", "result > 0", "add_positive",
        context={"result": result, "x": x, "y": y})
    return result

add_positive(5, 10)
```

**Error**:
```
Contract Violation: Postcondition
  Function: add_positive
  Clause: 'result_positive'
  Expression: result > 0
  Context:
    result = -5
    x = 5
    y = 10
```

**Fix**:
```python
# Fix implementation
result = x + y  # ✓ Correct
```

**Example 2: Size Mismatch**

```python
def double_elements(nums: list[int]) -> list[int]:
    check_precondition(len(nums) > 0, "non_empty", "len(nums) > 0", "double_elements",
        context={"len(nums)": len(nums)})

    result = [n * 2 for n in nums]
    result.append(0)  # ❌ Bug: adds extra element

    check_postcondition(len(result) == len(nums), "same_size", "len(result) == len(nums)",
        "double_elements", context={"len(result)": len(result), "len(nums)": len(nums)})
    return result
```

**Error**:
```
Contract Violation: Postcondition
  Function: double_elements
  Clause: 'same_size'
  Expression: len(result) == len(nums)
  Context:
    len(result) = 4
    len(nums) = 3
```

**Fix**:
```python
# Remove buggy line
result = [n * 2 for n in nums]  # ✓ Correct
```

---

### Invariant Violations

**When**: Class invariant broken after method execution

**Error Message Format**:
```
Contract Violation: Invariant
  Class: BankAccount
  Clause: 'non_negative_balance'
  Expression: self.balance >= 0.0
  Message: Invariant 'non_negative_balance' violated
  Context:
    self.balance = -50.0
```

**Example 1: Negative Balance**

```python
class BankAccount:
    def __init__(self, balance: float):
        self.balance = balance
        self._check_invariants()

    def _check_invariants(self):
        check_invariant(
            self.balance >= 0.0,
            "non_negative_balance",
            "self.balance >= 0.0",
            "BankAccount",
            context={"self.balance": self.balance}
        )

    def withdraw(self, amount: float):
        self.balance -= amount  # ❌ Bug: no check
        self._check_invariants()

account = BankAccount(100.0)
account.withdraw(150.0)  # Overdraft
```

**Error**:
```
Contract Violation: Invariant
  Class: BankAccount
  Clause: 'non_negative_balance'
  Expression: self.balance >= 0.0
  Context:
    self.balance = -50.0
```

**Fix**:
```python
def withdraw(self, amount: float):
    check_precondition(amount <= self.balance, "sufficient_funds",
        "amount <= self.balance", "withdraw", class_name="BankAccount",
        context={"amount": amount, "self.balance": self.balance})
    self.balance -= amount  # ✓ Now safe
    self._check_invariants()
```

**Example 2: Size Constraint**

```python
class CircularBuffer:
    def __init__(self, capacity: int):
        self.items = []
        self.capacity = capacity
        self._check_invariants()

    def _check_invariants(self):
        check_invariant(
            len(self.items) <= self.capacity,
            "within_capacity",
            "len(self.items) <= self.capacity",
            "CircularBuffer",
            context={"len(self.items)": len(self.items), "self.capacity": self.capacity}
        )

    def add(self, item):
        self.items.append(item)  # ❌ Bug: no size check
        self._check_invariants()

buffer = CircularBuffer(capacity=3)
buffer.add("a")
buffer.add("b")
buffer.add("c")
buffer.add("d")  # Overflow
```

**Error**:
```
Contract Violation: Invariant
  Class: CircularBuffer
  Clause: 'within_capacity'
  Expression: len(self.items) <= self.capacity
  Context:
    len(self.items) = 4
    self.capacity = 3
```

**Fix**:
```python
def add(self, item):
    if len(self.items) >= self.capacity:
        self.items.pop(0)  # Remove oldest
    self.items.append(item)  # ✓ Now maintains size
    self._check_invariants()
```

---

## Parse Errors

**Syntax errors in `.pw` files.**

### PWParseError

**Type**: Compile-time exception
**Raised by**: `parse_pw()` during parsing

---

### Unexpected Token

**Message**: `Unexpected token at line X, column Y`

**Example 1: Missing Colon**

```pw
function add(x: int, y: int) -> int {
    @requires positive x > 0  // ❌ Missing colon
    return x + y;
}
```

**Error**:
```
PWParseError: [Line 2:27] Unexpected token: x
Expected ':' after clause name 'positive'
```

**Fix**:
```pw
@requires positive: x > 0  // ✓ Correct
```

**Example 2: Missing Semicolon**

```pw
function test(x: int) -> int {
    let y = x + 1  // ❌ Missing semicolon
    return y;
}
```

**Error**:
```
PWParseError: [Line 3:5] Unexpected token: return
Expected ';' or newline after statement
```

**Fix**:
```pw
let y = x + 1;  // ✓ Correct
```

**Example 3: Wrong Keyword**

```pw
function test(x: int) -> int {
    @require positive: x > 0  // ❌ Wrong keyword (should be @requires)
    return x;
}
```

**Error**:
```
PWParseError: [Line 2:6] Unknown annotation: @require
Did you mean: @requires?
```

**Fix**:
```pw
@requires positive: x > 0  // ✓ Correct
```

---

### Type Errors

**Message**: `Type mismatch` or `Unknown type`

**Example 1: Unknown Type**

```pw
function test(x: integer) -> int {  // ❌ Unknown type 'integer'
    return x;
}
```

**Error**:
```
PWParseError: [Line 1:18] Unknown type: integer
Did you mean: int?
```

**Fix**:
```pw
function test(x: int) -> int {  // ✓ Correct
    return x;
}
```

**Example 2: Generic Type Without Parameters**

```pw
function get_first(items: array) -> int {  // ❌ Missing type parameter
    return items[0];
}
```

**Error**:
```
PWParseError: [Line 1:31] Generic type 'array' requires type parameters
Expected: array<T>
```

**Fix**:
```pw
function get_first(items: array<int>) -> int {  // ✓ Correct
    return items[0];
}
```

---

## Validation Errors

**Structural issues in contracts.**

### ValidationError

**Type**: Compile-time exception
**Raised by**: `validate()` after parsing

---

### Duplicate Definitions

**Message**: `Duplicate function definition: <name>`

**Example**:
```pw
function add(x: int, y: int) -> int {
    return x + y;
}

function add(a: int, b: int) -> int {  // ❌ Duplicate
    return a + b;
}
```

**Error**:
```
ValidationError: Duplicate function definition: add
```

**Fix**:
```pw
// Rename second function
function add(x: int, y: int) -> int {
    return x + y;
}

function sum(a: int, b: int) -> int {  // ✓ Different name
    return a + b;
}
```

---

### Invalid Clauses

**Message**: `Return outside of function`

**Example**:
```pw
// ❌ Return at module level
return 42;

function test() -> int {
    return 0;
}
```

**Error**:
```
ValidationError: Return outside of function
```

**Fix**:
```pw
// ✓ Return only inside functions
function test() -> int {
    return 42;
}
```

---

### Break/Continue Outside Loop

**Message**: `Break outside of loop`

**Example**:
```pw
function test(x: int) -> int {
    if (x > 0) {
        break;  // ❌ No surrounding loop
    }
    return x;
}
```

**Error**:
```
ValidationError: Break outside of loop
```

**Fix**:
```pw
function test(x: int) -> int {
    for (let i = 0; i < 10; i = i + 1) {
        if (x > 0) {
            break;  // ✓ Inside loop
        }
    }
    return x;
}
```

---

## MCP Errors

**MCP server/client communication errors.**

### MCPError

**Base class** for all MCP errors

**Subclasses**:
- `ConnectionError` - Failed to connect
- `TimeoutError` - Request timed out
- `ServiceUnavailableError` - Service down
- `InvalidVerbError` - Verb not found
- `InvalidParamsError` - Bad parameters
- `ProtocolError` - Protocol violation

---

### ConnectionError

**When**: Cannot connect to MCP server

**Example**:
```python
from promptware.sdk import MCPClient

client = MCPClient("http://localhost:3000")
client.call_verb("user.create", {"name": "Alice"})
```

**Error**:
```
ConnectionError: Failed to connect to http://localhost:3000
  Reason: Connection refused
```

**Fixes**:
1. **Start the server**:
   ```bash
   python user-service_server.py
   ```

2. **Check the port**:
   ```python
   client = MCPClient("http://localhost:8080")  # Correct port
   ```

3. **Check the host**:
   ```python
   client = MCPClient("http://api.example.com:3000")  # Remote server
   ```

---

### TimeoutError

**When**: Request takes too long

**Example**:
```python
client = MCPClient("http://localhost:3000", timeout=5)
client.call_verb("slow_operation", {})
```

**Error**:
```
TimeoutError: Request timed out after 5 seconds
  Verb: slow_operation
```

**Fixes**:
1. **Increase timeout**:
   ```python
   client = MCPClient("http://localhost:3000", timeout=30)
   ```

2. **Optimize server-side operation**:
   - Add caching
   - Use async processing
   - Reduce computation

---

### InvalidVerbError

**When**: Requested verb doesn't exist

**Example**:
```python
client.call_verb("user.deletee", {"id": 123})  # Typo
```

**Error**:
```
InvalidVerbError: Verb not found: user.deletee
  Code: -32601
  Available verbs: user.create@v1, user.get@v1, user.update@v1, user.delete@v1
```

**Fix**:
```python
client.call_verb("user.delete", {"id": 123})  # ✓ Correct spelling
```

---

### InvalidParamsError

**When**: Wrong parameters provided

**Example**:
```python
client.call_verb("user.create", {
    "name": "Alice"
    # ❌ Missing required 'email' parameter
})
```

**Error**:
```
InvalidParamsError: Invalid parameters for verb 'user.create'
  Code: -32602
  Validation errors:
    - Missing required parameter: 'email'
```

**Fix**:
```python
client.call_verb("user.create", {
    "name": "Alice",
    "email": "alice@example.com"  # ✓ Added required param
})
```

---

## Debugging Contract Violations

### Reading Error Messages

**Full error example**:
```
Contract Violation: Precondition
  Function: BankAccount.withdraw
  Clause: 'sufficient_funds'
  Expression: amount <= self.balance
  Message: Precondition 'sufficient_funds' violated
  Context:
    amount = 150.0
    self.balance = 100.0
```

**What it tells you**:
1. **Type**: Precondition (checked before function runs)
2. **Function**: `BankAccount.withdraw` (the method that failed)
3. **Clause**: `sufficient_funds` (which contract failed)
4. **Expression**: `amount <= self.balance` (what was checked)
5. **Context**: Actual values at failure time

**How to fix**:
```python
# Before:
account.withdraw(150.0)  # ❌ Violates precondition

# After:
if amount <= account.balance:
    account.withdraw(150.0)  # ✓ Checked first
else:
    print("Insufficient funds")
```

---

### Testing with Contracts

**Verify contracts work correctly:**

```python
import pytest
from promptware.runtime.contracts import ContractViolationError

def test_sqrt_rejects_negative():
    """Test that sqrt rejects negative values."""
    with pytest.raises(ContractViolationError) as exc_info:
        sqrt(-5)

    # Verify error details
    assert exc_info.value.type == "precondition"
    assert exc_info.value.clause == "non_negative"
    assert exc_info.value.context["x"] == -5

def test_sqrt_accepts_positive():
    """Test that sqrt accepts positive values."""
    result = sqrt(4.0)  # No exception
    assert result == 2.0
```

---

### Disabling Contracts

**For production (performance-sensitive code)**:

```python
from promptware.runtime.contracts import set_validation_mode, ValidationMode

# Disable all contracts
set_validation_mode(ValidationMode.DISABLED)

# Preconditions only (recommended for production)
set_validation_mode(ValidationMode.PRECONDITIONS_ONLY)

# Full validation (development/testing)
set_validation_mode(ValidationMode.FULL)
```

**Via environment variable**:
```bash
# Disable contracts
export PROMPTWARE_DISABLE_CONTRACTS=1
python app.py

# Enable contracts (default)
unset PROMPTWARE_DISABLE_CONTRACTS
python app.py
```

---

### Coverage Tracking

**See which contracts were tested:**

```python
from promptware.runtime.contracts import get_coverage, reset_coverage

# Reset before test suite
reset_coverage()

# Run tests
test_user_creation()
test_order_processing()

# Get coverage
coverage = get_coverage()
print(coverage)
# {
#   "createUser.requires.name_not_empty": 5,
#   "createUser.requires.email_valid": 5,
#   "processOrder.requires.total_positive": 3,
#   ...
# }
```

---

## Common Patterns

### Pattern 1: Validate Before Calling

**Problem**: Function has precondition you might violate

**Solution**: Check condition before calling
```python
# Before:
result = divide(10, 0)  # ❌ Precondition violation

# After:
if denominator != 0:
    result = divide(10, denominator)  # ✓ Safe
else:
    result = 0  # Handle zero case
```

---

### Pattern 2: Try-Catch for User Input

**Problem**: User input might violate contracts

**Solution**: Catch violations, show user-friendly message
```python
try:
    order = create_order(total=user_total, discount=user_discount)
except ContractViolationError as e:
    if e.clause == "valid_discount":
        print("Error: Discount cannot exceed total")
    elif e.clause == "positive_total":
        print("Error: Total must be positive")
    else:
        print(f"Invalid order: {e.message}")
```

---

### Pattern 3: Fix Implementation Bug

**Problem**: Postcondition fails (bug in function)

**Solution**: Fix implementation, postcondition guides you
```python
def add_positive(x: int, y: int) -> int:
    check_precondition(x > 0, ...)
    check_precondition(y > 0, ...)

    result = x - y  # ❌ Bug found by postcondition

    check_postcondition(result > 0, ...)  # Fails!
    return result

# Fix:
result = x + y  # ✓ Correct
```

---

## Error Prevention Tips

1. **Read error messages carefully** - Context shows exact values
2. **Test with invalid inputs** - Verify contracts catch bad data
3. **Start with preconditions** - Validate inputs first
4. **Use coverage tracking** - Ensure all clauses tested
5. **Keep contracts simple** - Complex expressions harder to debug
6. **Name clauses clearly** - `sufficient_funds` > `check1`

---

## See Also

- **[Contract Syntax](contract-syntax.md)** - How to write contracts
- **[Runtime API](runtime-api.md)** - Contract checking functions
- **[CLI Commands](cli-commands.md)** - Validate and test commands
- **[MCP Operations](mcp-operations.md)** - MCP server errors

---

**[← CLI Commands](cli-commands.md)** | **API Reference Complete**
