# How to Test Your Contracts

**Write comprehensive tests that verify contract behavior and catch violations.**

---

## What You'll Learn

- Test contracts with pytest
- Verify preconditions are enforced
- Test postconditions and invariants
- Use contract coverage tracking
- Test contract violations

**Prerequisites**: AssertLang installed, basic pytest knowledge

**Time**: 20 minutes

**Difficulty**: Beginner

---

## Step 1: Create a Contract to Test

Create `math_utils.al`:

```al
function divide(numerator: int, denominator: int) -> float {
    @requires denominator_not_zero: denominator != 0
    @requires valid_numerator: numerator >= -1000000 && numerator <= 1000000

    @ensures result_correct: result == numerator / denominator
    @ensures finite_result: result != float('inf') && result != float('-inf')

    return numerator / denominator;
}

function factorial(n: int) -> int {
    @requires non_negative: n >= 0
    @requires reasonable_size: n <= 20

    @ensures result_positive: result > 0
    @ensures result_greater_than_input: result >= n

    if (n == 0 || n == 1) {
        return 1;
    }

    let result = 1;
    for (let i = 2; i <= n; i = i + 1) {
        result = result * i;
    }
    return result;
}
```

Generate Python:

```bash
asl build math_utils.al -o math_utils.py
```

---

## Step 2: Write Basic Tests

Create `test_math_utils.py`:

```python
import pytest
from math_utils import divide, factorial
from promptware.runtime.contracts import ContractViolationError


class TestDivide:
    """Test divide function."""

    def test_divide_valid_inputs(self):
        """Test divide with valid inputs."""
        result = divide(10, 2)
        assert result == 5.0

        result = divide(7, 3)
        assert abs(result - 2.333333) < 0.0001

        result = divide(-10, 2)
        assert result == -5.0

    def test_divide_rejects_zero_denominator(self):
        """Test divide rejects zero denominator."""
        with pytest.raises(ContractViolationError) as exc_info:
            divide(10, 0)

        # Verify error details
        assert exc_info.value.type == "precondition"
        assert exc_info.value.clause == "denominator_not_zero"
        assert exc_info.value.context["denominator"] == 0

    def test_divide_rejects_invalid_numerator(self):
        """Test divide rejects out-of-range numerator."""
        with pytest.raises(ContractViolationError) as exc_info:
            divide(2000000, 2)

        assert exc_info.value.clause == "valid_numerator"

    def test_divide_postcondition_verified(self):
        """Test divide postconditions are checked."""
        # This test verifies postconditions run
        # If postcondition fails, it will raise ContractViolationError
        result = divide(10, 3)
        # If we get here, postconditions passed
        assert result is not None


class TestFactorial:
    """Test factorial function."""

    def test_factorial_base_cases(self):
        """Test factorial base cases."""
        assert factorial(0) == 1
        assert factorial(1) == 1

    def test_factorial_valid_inputs(self):
        """Test factorial with valid inputs."""
        assert factorial(5) == 120
        assert factorial(10) == 3628800

    def test_factorial_rejects_negative(self):
        """Test factorial rejects negative inputs."""
        with pytest.raises(ContractViolationError) as exc_info:
            factorial(-1)

        assert exc_info.value.clause == "non_negative"
        assert exc_info.value.context["n"] == -1

    def test_factorial_rejects_large_input(self):
        """Test factorial rejects unreasonably large input."""
        with pytest.raises(ContractViolationError) as exc_info:
            factorial(100)

        assert exc_info.value.clause == "reasonable_size"
```

Run tests:

```bash
pytest test_math_utils.py -v
```

**Expected output**:
```
test_math_utils.py::TestDivide::test_divide_valid_inputs PASSED
test_math_utils.py::TestDivide::test_divide_rejects_zero_denominator PASSED
test_math_utils.py::TestDivide::test_divide_rejects_invalid_numerator PASSED
test_math_utils.py::TestDivide::test_divide_postcondition_verified PASSED
test_math_utils.py::TestFactorial::test_factorial_base_cases PASSED
test_math_utils.py::TestFactorial::test_factorial_valid_inputs PASSED
test_math_utils.py::TestFactorial::test_factorial_rejects_negative PASSED
test_math_utils.py::TestFactorial::test_factorial_rejects_large_input PASSED

8 passed in 0.15s
```

---

## Step 3: Test Postconditions

**Test that postconditions catch bugs:**

Create `buggy_math.al`:

```al
function absolute(x: int) -> int {
    @requires true: true

    @ensures non_negative: result >= 0
    @ensures magnitude_preserved: result == x || result == -x

    // ❌ Intentional bug
    if (x < 0) {
        return x;  // Bug: should return -x
    }
    return x;
}
```

Generate and test:

```bash
asl build buggy_math.al -o buggy_math.py
```

```python
# test_buggy_math.py
import pytest
from buggy_math import absolute
from promptware.runtime.contracts import ContractViolationError


def test_absolute_catches_bug():
    """Test that postcondition catches the implementation bug."""
    # Positive input works
    assert absolute(5) == 5

    # Negative input triggers postcondition failure
    with pytest.raises(ContractViolationError) as exc_info:
        absolute(-5)

    # Verify it's the postcondition that failed
    assert exc_info.value.type == "postcondition"
    assert exc_info.value.clause == "non_negative"
    assert exc_info.value.context["result"] == -5  # Bug exposed!
```

**Run**:
```bash
pytest test_buggy_math.py -v
```

**Output**:
```
test_buggy_math.py::test_absolute_catches_bug PASSED

Contract Violation: Postcondition
  Function: absolute
  Clause: 'non_negative'
  Expression: result >= 0
  Context:
    result = -5
```

✅ **Postcondition caught the bug!**

---

## Step 4: Test Invariants

Create `account.al`:

```al
class BankAccount {
    balance: float
    account_id: string

    @invariant non_negative_balance: this.balance >= 0.0
    @invariant valid_id: len(this.account_id) > 0

    function withdraw(amount: float) -> bool {
        @requires positive_amount: amount > 0.0
        @requires sufficient_funds: amount <= this.balance

        @ensures balance_reduced: this.balance == old(this.balance) - amount

        this.balance = this.balance - amount;
        return true;
    }
}
```

Generate and test:

```bash
asl build account.al -o account.py
```

```python
# test_account.py
import pytest
from account import BankAccount
from promptware.runtime.contracts import ContractViolationError


class TestBankAccount:
    """Test BankAccount class."""

    def test_account_creation_valid(self):
        """Test account creation with valid balance."""
        account = BankAccount(balance=100.0, account_id="ACC123")
        assert account.balance == 100.0

    def test_account_creation_invalid_balance(self):
        """Test account creation rejects negative balance."""
        with pytest.raises(ContractViolationError) as exc_info:
            BankAccount(balance=-50.0, account_id="ACC123")

        assert exc_info.value.type == "invariant"
        assert exc_info.value.clause == "non_negative_balance"

    def test_withdraw_valid(self):
        """Test withdraw with sufficient funds."""
        account = BankAccount(balance=100.0, account_id="ACC123")
        result = account.withdraw(30.0)
        assert result is True
        assert account.balance == 70.0

    def test_withdraw_insufficient_funds(self):
        """Test withdraw rejects overdraft."""
        account = BankAccount(balance=50.0, account_id="ACC123")

        with pytest.raises(ContractViolationError) as exc_info:
            account.withdraw(100.0)

        assert exc_info.value.clause == "sufficient_funds"

    def test_withdraw_maintains_invariant(self):
        """Test withdraw maintains balance invariant."""
        account = BankAccount(balance=100.0, account_id="ACC123")
        account.withdraw(50.0)
        # If we get here, invariant was maintained
        assert account.balance >= 0.0
```

---

## Step 5: Use Coverage Tracking

Track which contracts were tested:

```python
# test_with_coverage.py
import pytest
from math_utils import divide, factorial
from promptware.runtime.contracts import (
    ContractViolationError,
    get_coverage,
    reset_coverage
)


class TestWithCoverage:
    """Test with contract coverage tracking."""

    def setup_method(self):
        """Reset coverage before each test."""
        reset_coverage()

    def test_divide_coverage(self):
        """Test divide and check contract coverage."""
        # Call function with valid inputs
        divide(10, 2)
        divide(7, 3)

        # Get coverage
        coverage = get_coverage()

        # Verify preconditions were checked
        assert "divide.requires.denominator_not_zero" in coverage
        assert coverage["divide.requires.denominator_not_zero"] == 2

        assert "divide.requires.valid_numerator" in coverage
        assert coverage["divide.requires.valid_numerator"] == 2

        # Verify postconditions were checked
        assert "divide.ensures.result_correct" in coverage
        assert coverage["divide.ensures.result_correct"] == 2

    def test_factorial_coverage(self):
        """Test factorial and verify all contracts tested."""
        reset_coverage()

        # Test multiple cases
        factorial(0)
        factorial(1)
        factorial(5)

        coverage = get_coverage()

        # All preconditions checked 3 times
        assert coverage["factorial.requires.non_negative"] == 3
        assert coverage["factorial.requires.reasonable_size"] == 3

        # All postconditions checked 3 times
        assert coverage["factorial.ensures.result_positive"] == 3
        assert coverage["factorial.ensures.result_greater_than_input"] == 3

    def test_full_coverage_report(self):
        """Generate full coverage report."""
        reset_coverage()

        # Run all functions
        divide(10, 2)
        factorial(5)

        coverage = get_coverage()

        print("\n=== Contract Coverage Report ===")
        for clause, count in sorted(coverage.items()):
            print(f"{clause}: {count} executions")

        # Verify minimum coverage
        assert len(coverage) >= 8  # At least 8 contracts checked
```

**Run**:
```bash
pytest test_with_coverage.py -v -s
```

**Output**:
```
=== Contract Coverage Report ===
divide.ensures.finite_result: 1 executions
divide.ensures.result_correct: 1 executions
divide.requires.denominator_not_zero: 1 executions
divide.requires.valid_numerator: 1 executions
factorial.ensures.result_greater_than_input: 1 executions
factorial.ensures.result_positive: 1 executions
factorial.requires.non_negative: 1 executions
factorial.requires.reasonable_size: 1 executions
```

---

## Step 6: Parametrized Tests

Test multiple inputs efficiently:

```python
# test_parametrized.py
import pytest
from math_utils import divide, factorial
from promptware.runtime.contracts import ContractViolationError


class TestDivideParametrized:
    """Parametrized tests for divide."""

    @pytest.mark.parametrize("numerator,denominator,expected", [
        (10, 2, 5.0),
        (7, 3, 2.333333),
        (-10, 2, -5.0),
        (0, 5, 0.0),
        (100, 4, 25.0),
    ])
    def test_divide_valid_cases(self, numerator, denominator, expected):
        """Test divide with multiple valid inputs."""
        result = divide(numerator, denominator)
        assert abs(result - expected) < 0.0001

    @pytest.mark.parametrize("numerator,denominator", [
        (10, 0),
        (0, 0),
        (-5, 0),
    ])
    def test_divide_rejects_zero(self, numerator, denominator):
        """Test divide rejects zero denominator."""
        with pytest.raises(ContractViolationError) as exc_info:
            divide(numerator, denominator)

        assert exc_info.value.clause == "denominator_not_zero"


class TestFactorialParametrized:
    """Parametrized tests for factorial."""

    @pytest.mark.parametrize("n,expected", [
        (0, 1),
        (1, 1),
        (2, 2),
        (3, 6),
        (4, 24),
        (5, 120),
        (10, 3628800),
    ])
    def test_factorial_valid_cases(self, n, expected):
        """Test factorial with multiple valid inputs."""
        assert factorial(n) == expected

    @pytest.mark.parametrize("n", [-1, -5, -100])
    def test_factorial_rejects_negative(self, n):
        """Test factorial rejects negative inputs."""
        with pytest.raises(ContractViolationError):
            factorial(n)

    @pytest.mark.parametrize("n", [21, 50, 100])
    def test_factorial_rejects_large(self, n):
        """Test factorial rejects large inputs."""
        with pytest.raises(ContractViolationError):
            factorial(n)
```

---

## Testing Best Practices

### 1. Test Both Valid and Invalid Inputs

```python
def test_function():
    # ✓ Valid inputs (should succeed)
    result = function(valid_input)
    assert result is not None

    # ✓ Invalid inputs (should raise ContractViolationError)
    with pytest.raises(ContractViolationError):
        function(invalid_input)
```

---

### 2. Verify Contract Details

```python
def test_contract_details():
    with pytest.raises(ContractViolationError) as exc_info:
        function(bad_input)

    # Verify exact contract that failed
    assert exc_info.value.type == "precondition"
    assert exc_info.value.clause == "specific_clause_name"
    assert exc_info.value.context["param"] == expected_value
```

---

### 3. Test Edge Cases

```python
@pytest.mark.parametrize("input", [
    0,           # Zero
    1,           # Minimum valid
    999999,      # Maximum valid
    -1,          # Just below valid range
    1000000,     # Just above valid range
])
def test_edge_cases(input):
    # Test boundary conditions
    ...
```

---

### 4. Test Invariants After Each Operation

```python
def test_invariant_maintained():
    obj = MyClass(initial_state)

    # Perform operation
    obj.modify()

    # Invariant should still hold
    # (automatically checked if contracts enabled)
    assert obj.is_valid()  # Additional explicit check
```

---

## Common Testing Patterns

### Pattern 1: Fixture for Contract Setup

```python
@pytest.fixture
def account():
    """Provide a test account."""
    return BankAccount(balance=100.0, account_id="TEST123")


def test_with_fixture(account):
    """Use fixture in test."""
    account.withdraw(50.0)
    assert account.balance == 50.0
```

---

### Pattern 2: Expected Violations

```python
def test_expected_violation():
    """Test that specific violation occurs."""
    with pytest.raises(ContractViolationError) as exc:
        dangerous_function(bad_input)

    # Assert specific contract failed
    assert "expected_clause" in str(exc.value)
```

---

### Pattern 3: Contract-Specific Test Suites

```python
class TestPreconditions:
    """All precondition tests."""
    def test_precondition_1(self): ...
    def test_precondition_2(self): ...

class TestPostconditions:
    """All postcondition tests."""
    def test_postcondition_1(self): ...
    def test_postcondition_2(self): ...

class TestInvariants:
    """All invariant tests."""
    def test_invariant_1(self): ...
    def test_invariant_2(self): ...
```

---

## What You Learned

✅ **Test contracts with pytest** - Verify preconditions, postconditions, invariants
✅ **Catch violations** - Use `pytest.raises(ContractViolationError)`
✅ **Verify error details** - Check clause, type, context
✅ **Track coverage** - Use `get_coverage()` to see what was tested
✅ **Parametrized tests** - Test multiple inputs efficiently
✅ **Test postconditions catch bugs** - Verify implementation correctness

---

## Next Steps

**Test more complex contracts**:
- Test classes with invariants
- Test functions with old() values
- Test generic functions

**Advanced testing**:
- [How-To: Debug Contract Violations](debugging.md)
- [Cookbook: State Machines](../../cookbook/patterns/state-machines.md)

**Learn more**:
- [Runtime API Reference](../../reference/runtime-api.md)
- [Error Codes Reference](../../reference/error-codes.md)

---

## Troubleshooting

**Problem**: Tests pass but contracts not checked

**Fix**: Verify contracts are enabled
```python
from promptware.runtime.contracts import are_contracts_enabled
assert are_contracts_enabled()  # Should be True
```

---

**Problem**: Can't import ContractViolationError

**Fix**: Install promptware runtime
```bash
pip install promptware
```

---

**Problem**: Coverage not tracking

**Fix**: Call `reset_coverage()` before tests
```python
from promptware.runtime.contracts import reset_coverage

def setup_method(self):
    reset_coverage()
```

---

## See Also

- **[First Contract](first-contract.md)** - Getting started
- **[Runtime API](../../reference/runtime-api.md)** - Contract functions
- **[Error Codes](../../reference/error-codes.md)** - Debugging guide

---

**[← Multi-Language →](multi-language.md)** | **[How-To Index →](../index.md)**
