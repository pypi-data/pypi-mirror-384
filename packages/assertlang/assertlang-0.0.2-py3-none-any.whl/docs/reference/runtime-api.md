# Runtime API Reference

**API reference for contract checking at runtime (Python & JavaScript).**

---

## Overview

When AssertLang generates code, it embeds runtime contract checks. This document describes the runtime API available in generated code.

**Languages**:
- Python (100% complete)
- JavaScript (95% complete)
- Go (70% complete)
- Rust (60% complete)

---

## Python Runtime API

### Module: `promptware.runtime.contracts`

**Import**:
```python
from promptware.runtime.contracts import (
    check_precondition,
    check_postcondition,
    check_invariant,
    ContractViolationError,
    disable_contracts,
    enable_contracts,
    are_contracts_enabled
)
```

---

### check_precondition()

**Check a precondition (before function execution).**

**Signature**:
```python
def check_precondition(
    condition: bool,
    clause_name: str,
    message: str = None,
    **context
) -> None
```

**Parameters**:
- `condition` - Boolean expression to check
- `clause_name` - Name of the contract clause
- `message` - Optional custom error message
- `**context` - Optional context variables for error message

**Raises**:
- `ContractViolationError` if condition is `False`

**Example**:
```python
def sqrt(x: float) -> float:
    check_precondition(
        x >= 0.0,
        "non_negative",
        f"Expected non-negative value, got {x}"
    )

    return math.sqrt(x)
```

---

### check_postcondition()

**Check a postcondition (after function returns).**

**Signature**:
```python
def check_postcondition(
    condition: bool,
    clause_name: str,
    message: str = None,
    **context
) -> None
```

**Parameters**:
- `condition` - Boolean expression to check
- `clause_name` - Name of the contract clause
- `message` - Optional custom error message
- `**context` - Optional context for debugging

**Raises**:
- `ContractViolationError` if condition is `False`

**Example**:
```python
def absolute(x: int) -> int:
    result = abs(x)

    check_postcondition(
        result >= 0,
        "non_negative",
        f"Result must be non-negative, got {result}"
    )

    return result
```

---

### check_invariant()

**Check a class invariant.**

**Signature**:
```python
def check_invariant(
    condition: bool,
    clause_name: str,
    class_name: str = None,
    message: str = None
) -> None
```

**Parameters**:
- `condition` - Boolean expression to check
- `clause_name` - Name of the invariant
- `class_name` - Optional class name
- `message` - Optional error message

**Raises**:
- `ContractViolationError` if condition is `False`

**Example**:
```python
class BankAccount:
    def __init__(self, balance: float):
        self.balance = balance
        self._check_invariants()

    def _check_invariants(self):
        check_invariant(
            self.balance >= 0.0,
            "non_negative_balance",
            class_name="BankAccount"
        )

    def withdraw(self, amount: float):
        self.balance -= amount
        self._check_invariants()  # Check after modification
```

---

### ContractViolationError

**Exception raised when contract fails.**

**Attributes**:
```python
class ContractViolationError(Exception):
    clause_name: str      # Name of failed clause
    clause_type: str      # "precondition" | "postcondition" | "invariant"
    message: str          # Error message
    context: dict         # Additional context
```

**Example**:
```python
try:
    result = divide(10, 0)
except ContractViolationError as e:
    print(f"Contract '{e.clause_name}' failed: {e.message}")
    # Output: Contract 'divisor_not_zero' failed: Expected b != 0, got b = 0
```

---

### disable_contracts()

**Disable contract checking globally.**

**Signature**:
```python
def disable_contracts() -> None
```

**Use Case**: Production environments where performance is critical.

**Example**:
```python
import os
from promptware.runtime.contracts import disable_contracts

if os.getenv("PROMPTWARE_DISABLE_CONTRACTS") == "1":
    disable_contracts()

# Contracts now disabled - functions run without checks
result = divide(10, 0)  # No contract check!
```

---

### enable_contracts()

**Enable contract checking globally.**

**Signature**:
```python
def enable_contracts() -> None
```

**Example**:
```python
from promptware.runtime.contracts import enable_contracts

# Re-enable contracts (enabled by default)
enable_contracts()
```

---

### are_contracts_enabled()

**Check if contracts are currently enabled.**

**Signature**:
```python
def are_contracts_enabled() -> bool
```

**Returns**: `True` if enabled, `False` if disabled

**Example**:
```python
from promptware.runtime.contracts import are_contracts_enabled

if are_contracts_enabled():
    print("Contracts active - validation enabled")
else:
    print("Contracts disabled - no validation")
```

---

## JavaScript Runtime API

### Module: `@promptware/runtime`

**Import**:
```javascript
const {
    checkPrecondition,
    checkPostcondition,
    checkInvariant,
    ContractViolationError,
    disableContracts,
    enableContracts,
    areContractsEnabled
} = require('@promptware/runtime');
```

---

### checkPrecondition()

**Check a precondition.**

**Signature**:
```typescript
function checkPrecondition(
    condition: boolean,
    clauseName: string,
    message?: string,
    context?: Record<string, any>
): void
```

**Example**:
```javascript
function sqrt(x) {
    checkPrecondition(
        x >= 0.0,
        'non_negative',
        `Expected non-negative value, got ${x}`
    );

    return Math.sqrt(x);
}
```

---

### checkPostcondition()

**Check a postcondition.**

**Signature**:
```typescript
function checkPostcondition(
    condition: boolean,
    clauseName: string,
    message?: string,
    context?: Record<string, any>
): void
```

**Example**:
```javascript
function absolute(x) {
    const result = Math.abs(x);

    checkPostcondition(
        result >= 0,
        'non_negative',
        `Result must be non-negative, got ${result}`
    );

    return result;
}
```

---

### checkInvariant()

**Check a class invariant.**

**Signature**:
```typescript
function checkInvariant(
    condition: boolean,
    clauseName: string,
    className?: string,
    message?: string
): void
```

**Example**:
```javascript
class BankAccount {
    constructor(balance) {
        this.balance = balance;
        this._checkInvariants();
    }

    _checkInvariants() {
        checkInvariant(
            this.balance >= 0.0,
            'non_negative_balance',
            'BankAccount'
        );
    }

    withdraw(amount) {
        this.balance -= amount;
        this._checkInvariants();
    }
}
```

---

### ContractViolationError

**Error thrown when contract fails.**

**Properties**:
```typescript
class ContractViolationError extends Error {
    clauseName: string;
    clauseType: 'precondition' | 'postcondition' | 'invariant';
    context: Record<string, any>;
}
```

**Example**:
```javascript
try {
    const result = divide(10, 0);
} catch (error) {
    if (error instanceof ContractViolationError) {
        console.log(`Contract '${error.clauseName}' failed: ${error.message}`);
    }
}
```

---

### disableContracts()

**Disable contract checking.**

**Signature**:
```typescript
function disableContracts(): void
```

**Example**:
```javascript
const { disableContracts } = require('@promptware/runtime');

if (process.env.PROMPTWARE_DISABLE_CONTRACTS === '1') {
    disableContracts();
}
```

---

### enableContracts()

**Enable contract checking.**

**Signature**:
```typescript
function enableContracts(): void
```

---

### areContractsEnabled()

**Check if contracts are enabled.**

**Signature**:
```typescript
function areContractsEnabled(): boolean
```

**Returns**: `true` if enabled, `false` if disabled

---

## Environment Variables

**Control contract checking via environment variables:**

| Variable | Values | Effect |
|----------|--------|--------|
| `PROMPTWARE_DISABLE_CONTRACTS` | `1` or `true` | Disable all contract checks |
| `PROMPTWARE_DEBUG_CONTRACTS` | `1` or `true` | Enable verbose contract debugging |
| `PROMPTWARE_STRICT_MODE` | `1` or `true` | Fail fast on first contract violation |

**Example**:
```bash
# Disable contracts in production
export PROMPTWARE_DISABLE_CONTRACTS=1
python main.py

# Enable debug mode in development
export PROMPTWARE_DEBUG_CONTRACTS=1
node server.js
```

---

## Generated Code Patterns

### Function with Contracts

**PW Source**:
```pw
function add(x: int, y: int) -> int {
    @requires x_positive: x > 0
    @requires y_positive: y > 0

    @ensures result_positive: result > 0
    @ensures sum_correct: result == x + y

    return x + y;
}
```

**Generated Python**:
```python
from promptware.runtime.contracts import check_precondition, check_postcondition

def add(x: int, y: int) -> int:
    # Preconditions
    check_precondition(x > 0, "x_positive", f"Expected x > 0, got x = {x}")
    check_precondition(y > 0, "y_positive", f"Expected y > 0, got y = {y}")

    # Implementation
    __result = x + y

    # Postconditions
    check_postcondition(__result > 0, "result_positive",
        f"Expected result > 0, got result = {__result}")
    check_postcondition(__result == x + y, "sum_correct",
        f"Expected result == x + y, got result = {__result}, x + y = {x + y}")

    return __result
```

---

### Class with Invariants

**PW Source**:
```pw
class Counter {
    count: int

    @invariant non_negative: this.count >= 0

    function increment() -> int {
        @ensures increased: this.count > old(this.count)

        this.count = this.count + 1;
        return this.count;
    }
}
```

**Generated Python**:
```python
from promptware.runtime.contracts import check_invariant, check_postcondition

class Counter:
    def __init__(self):
        self.count = 0
        self._check_invariants()

    def _check_invariants(self):
        check_invariant(
            self.count >= 0,
            "non_negative",
            "Counter"
        )

    def increment(self) -> int:
        __old_count = self.count

        self.count = self.count + 1

        check_postcondition(
            self.count > __old_count,
            "increased"
        )

        self._check_invariants()
        return self.count
```

---

## Performance

**Overhead**:
- Precondition check: ~1-2µs
- Postcondition check: ~1-2µs
- Invariant check: ~2-3µs

**Total impact**: Negligible for most applications (< 0.1% of execution time)

**When to disable**:
- Tight loops (millions of iterations)
- Real-time systems (< 1ms latency requirements)
- After thorough testing (contracts served purpose)

**Best practice**: Keep enabled in development, optionally disable in production.

---

## Error Messages

**Contract violations provide detailed error messages:**

```python
ContractViolationError: Precondition 'non_negative' failed
  Expected: x >= 0
  Got: x = -5

  Function: sqrt(x: float) -> float
  File: math_utils.py, line 15

  Context:
    x = -5

  Suggestion: Ensure x is non-negative before calling sqrt()

  Learn more: https://docs.assertlang.dev/reference/error-codes#non-negative
```

---

## Testing with Contracts

**Contract violations can be tested:**

```python
import pytest
from promptware.runtime.contracts import ContractViolationError

def test_sqrt_rejects_negative():
    with pytest.raises(ContractViolationError) as exc_info:
        sqrt(-5)

    assert exc_info.value.clause_name == "non_negative"
    assert "negative" in str(exc_info.value).lower()

def test_sqrt_accepts_positive():
    result = sqrt(4.0)
    assert result == 2.0  # No contract violation
```

---

## See Also

- **[Contract Syntax](contract-syntax.md)** - Write contracts in PW
- **[CLI Commands](cli-commands.md)** - Generate code from contracts
- **[MCP Operations](mcp-operations.md)** - Use via MCP server
- **[Error Codes](error-codes.md)** - All contract error types

---

**[← Contract Syntax](contract-syntax.md)** | **[MCP Operations →](mcp-operations.md)**
