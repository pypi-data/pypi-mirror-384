# How-To: Debug Contract Violations

**Learn how to read error messages, identify violations, and fix them quickly.**

---

## Overview

**What you'll learn:**
- Read contract violation error messages
- Identify precondition vs postcondition failures
- Fix common contract violations
- Use debugging workflow effectively

**Time:** 15 minutes
**Difficulty:** Beginner
**Prerequisites:** [Write Your First Contract](first-contract.md)

---

## The Problem

You've written a contract, but when you run your code, it throws a `ContractViolation` error. The error message is long and confusing. You're not sure what went wrong or how to fix it.

---

## The Solution

AssertLang provides detailed error messages that tell you exactly:
1. **What contract** was violated
2. **Which condition** failed (precondition, postcondition, type)
3. **What values** caused the failure
4. **Where to look** (file, line number)

Let's debug a real contract violation step by step.

---

## Step 1: Understanding Error Messages

### Anatomy of a Violation Error

```
ContractViolation: Postcondition failed in divide()
  Contract: divide(a: Int, b: Int) -> Int
  Condition: b != 0
  Failed with: b = 0
  Location: calculator.py:15

  Stack trace:
    File "calculator.py", line 15, in divide
      result = a / b
```

**Key parts:**
1. **Violation type** - `Postcondition failed` (or `Precondition failed`, `Type mismatch`)
2. **Function name** - `divide()`
3. **Failed condition** - `b != 0`
4. **Actual values** - `b = 0`
5. **Location** - `calculator.py:15`

---

## Step 2: Common Violation Types

### Precondition Violations

**What:** Input validation failed before function runs.

**Example:**

```promptware
function calculate_discount(price: Float, discount_percent: Float) -> Float
  requires:
    price > 0.0
    discount_percent >= 0.0
    discount_percent <= 100.0
  ensures:
    result >= 0.0
    result <= price
  do
    return price * (1.0 - discount_percent / 100.0)
  end
end
```

**Error:**

```
ContractViolation: Precondition failed in calculate_discount()
  Contract: calculate_discount(price: Float, discount_percent: Float) -> Float
  Condition: price > 0.0
  Failed with: price = -10.5
  Location: pricing.py:8
```

**Fix:** Validate input before calling:

```python
# Python
price = max(0.0, user_input)  # Ensure positive
discount = calculate_discount(price, 20.0)
```

---

### Postcondition Violations

**What:** Function returned invalid value (bug in implementation).

**Example:**

```promptware
function calculate_age(birth_year: Int) -> Int
  requires:
    birth_year > 1900
    birth_year <= 2025
  ensures:
    result >= 0
    result <= 150
  do
    return birth_year - 2025  # BUG: Should be 2025 - birth_year
  end
end
```

**Error:**

```
ContractViolation: Postcondition failed in calculate_age()
  Contract: calculate_age(birth_year: Int) -> Int
  Condition: result >= 0
  Failed with: result = -25 (birth_year = 2000)
  Location: age_calculator.py:12

  Expected: result >= 0
  Actual: result = -25
```

**Fix:** Correct the implementation:

```promptware
function calculate_age(birth_year: Int) -> Int
  requires:
    birth_year > 1900
    birth_year <= 2025
  ensures:
    result >= 0
    result <= 150
  do
    return 2025 - birth_year  # Fixed
  end
end
```

---

### Type Violations

**What:** Wrong type passed to function.

**Example:**

```promptware
function format_price(amount: Float) -> String
  requires:
    amount >= 0.0
  do
    return "$" + String(amount)
  end
end
```

**Error:**

```
ContractViolation: Type mismatch in format_price()
  Contract: format_price(amount: Float) -> String
  Expected: amount: Float
  Got: amount: String = "10.50"
  Location: formatter.py:5
```

**Fix:** Convert type before calling:

```python
# Python
price_str = "10.50"
price = float(price_str)  # Convert to float
formatted = format_price(price)
```

---

## Step 3: Debugging Workflow

### 1. Read the Error Message

Focus on these parts:
- **Condition** - What failed?
- **Failed with** - What values caused it?
- **Location** - Where did it happen?

### 2. Check Preconditions First

Most violations are precondition failures (bad input).

**Quick check:**
```python
# Add debug logging before contract calls
print(f"Calling divide({a}, {b})")  # See actual values
result = divide(a, b)
```

### 3. Verify Postconditions

If preconditions pass but postconditions fail, there's a bug in your implementation.

**Quick check:**
```python
# Add assertion before returning
result = a / b
assert result >= 0, f"Expected positive, got {result}"
return result
```

### 4. Test with Known Values

Isolate the problem with simple inputs:

```python
# Test with obvious values
assert divide(10, 2) == 5  # Should work
assert divide(10, 0)  # Should fail with clear error
```

---

## Step 4: Fixing Common Issues

### Issue: "Array index out of bounds"

**Contract:**
```promptware
function get_item(items: List<String>, index: Int) -> String
  requires:
    index >= 0
    index < len(items)
  do
    return items[index]
  end
end
```

**Error:**
```
ContractViolation: Precondition failed in get_item()
  Condition: index < len(items)
  Failed with: index = 5, len(items) = 3
```

**Fix:**
```python
# Python: Validate before calling
if 0 <= index < len(items):
    item = get_item(items, index)
else:
    item = None  # Or handle error
```

---

### Issue: "Null/None value passed"

**Contract:**
```promptware
function process_user(user: User) -> String
  requires:
    user != null
  do
    return user.name
  end
end
```

**Error:**
```
ContractViolation: Precondition failed in process_user()
  Condition: user != null
  Failed with: user = None
```

**Fix with Option type:**
```promptware
function process_user(user: Option<User>) -> String
  do
    return match user:
      case Some(u): u.name
      case None: "Anonymous"
    end
  end
end
```

---

### Issue: "Empty collection"

**Contract:**
```promptware
function get_first(items: List<Int>) -> Int
  requires:
    len(items) > 0
  do
    return items[0]
  end
end
```

**Error:**
```
ContractViolation: Precondition failed in get_first()
  Condition: len(items) > 0
  Failed with: len(items) = 0
```

**Fix with Result type:**
```promptware
function get_first(items: List<Int>) -> Result<Int, String>
  do
    if len(items) > 0:
      return Ok(items[0])
    else:
      return Err("Empty list")
    end
  end
end
```

---

## Step 5: Debugging Tools

### Enable Detailed Errors

Set environment variable for verbose output:

```bash
# Bash
export PW_DEBUG=1
python your_script.py
```

**Output:**
```
ContractViolation: Postcondition failed in calculate_discount()
  Contract: calculate_discount(price: Float, discount_percent: Float) -> Float
  Condition: result >= 0.0
  Failed with: result = -5.0

  Input values:
    price = 100.0
    discount_percent = 105.0

  Output value:
    result = -5.0

  Stack trace:
    File "pricing.py", line 15, in calculate_discount
      return price * (1.0 - discount_percent / 100.0)
    File "checkout.py", line 42, in apply_discount
      discounted = calculate_discount(item.price, coupon.percent)
```

---

### Use Test Suite

Write tests that check boundaries:

```python
# Python (pytest)
import pytest
from mymodule import divide

def test_divide_valid():
    assert divide(10, 2) == 5
    assert divide(7, 2) == 3  # Integer division

def test_divide_by_zero():
    with pytest.raises(ContractViolation) as exc:
        divide(10, 0)

    assert "b != 0" in str(exc.value)
    assert "b = 0" in str(exc.value)

def test_divide_negative():
    # If contract requires positive inputs
    with pytest.raises(ContractViolation):
        divide(-10, 2)
```

---

### Use Runtime Assertions

Add temporary assertions to narrow down issues:

```python
# Python
def process_orders(orders):
    assert len(orders) > 0, f"Empty orders list"

    for order in orders:
        assert order is not None, f"Null order in list"
        assert order.amount >= 0, f"Negative amount: {order.amount}"

        # Contract call
        result = process_order(order)
```

---

## Step 6: Prevention Strategies

### 1. Write Tests First

```python
# Python (pytest)
def test_calculate_discount_boundaries():
    # Test limits
    assert calculate_discount(100.0, 0.0) == 100.0    # No discount
    assert calculate_discount(100.0, 100.0) == 0.0    # Full discount
    assert calculate_discount(50.0, 50.0) == 25.0     # Half off

    # Test violations
    with pytest.raises(ContractViolation):
        calculate_discount(-10.0, 20.0)  # Negative price

    with pytest.raises(ContractViolation):
        calculate_discount(100.0, 150.0)  # Invalid percent
```

### 2. Use Defensive Programming

```python
# Python
def apply_coupon(price, coupon_code):
    # Validate before contract call
    if price <= 0:
        raise ValueError(f"Invalid price: {price}")

    discount = get_discount_percent(coupon_code)
    if not (0 <= discount <= 100):
        raise ValueError(f"Invalid discount: {discount}")

    # Now safe to call contract
    return calculate_discount(price, discount)
```

### 3. Use Type Hints

```python
# Python
from typing import List, Optional

def process_items(items: List[str], index: int) -> Optional[str]:
    """Mypy will catch type errors before runtime."""
    if 0 <= index < len(items):
        return get_item(items, index)  # Contract call
    return None
```

---

## Real-World Example

### Scenario: E-commerce Cart

**Contract:**
```promptware
function apply_bulk_discount(
    items: List<CartItem>,
    min_quantity: Int
) -> Float
  requires:
    len(items) > 0
    min_quantity > 0
    forall item in items: item.quantity > 0
    forall item in items: item.price >= 0.0
  ensures:
    result >= 0.0
  do
    total_quantity = sum(item.quantity for item in items)
    total_price = sum(item.price * item.quantity for item in items)

    if total_quantity >= min_quantity:
      return total_price * 0.9  # 10% off
    else:
      return total_price
    end
  end
end
```

**Error:**
```
ContractViolation: Precondition failed in apply_bulk_discount()
  Condition: forall item in items: item.price >= 0.0
  Failed with: items[2].price = -5.0
  Location: cart.py:23
```

**Debug:**
```python
# Python
def checkout(cart):
    # Add debug logging
    for i, item in enumerate(cart.items):
        print(f"Item {i}: price={item.price}, qty={item.quantity}")

    # Found the issue: Item 2 has negative price
    # >>> Item 2: price=-5.0, qty=2
```

**Fix:**
```python
# Python
def add_to_cart(item):
    # Validate when adding items
    if item.price < 0:
        raise ValueError(f"Invalid price for {item.name}: {item.price}")

    if item.quantity <= 0:
        raise ValueError(f"Invalid quantity for {item.name}: {item.quantity}")

    cart.items.append(item)
```

---

## Summary

**Debugging workflow:**
1. **Read error message** - Focus on condition, values, location
2. **Check preconditions** - Most failures are bad inputs
3. **Verify postconditions** - Implementation bugs if preconditions pass
4. **Test with simple values** - Isolate the problem
5. **Fix at the source** - Validate inputs early

**Prevention:**
- Write tests for boundaries
- Use defensive programming
- Enable type checking
- Add debug logging during development

**Tools:**
- `PW_DEBUG=1` for verbose errors
- `pytest` for systematic testing
- Type hints for static analysis
- Runtime assertions for debugging

---

## Next Steps

- **[Test Your Contracts](testing-contracts.md)** - Write comprehensive tests
- **[Handle Complex Types](../../advanced/complex-types.md)** - Use Option/Result for error handling
- **[Monitor Contract Violations](../../deployment/monitoring.md)** - Track violations in production

---

## See Also

- **[Error Codes Reference](../../reference/error-codes.md)** - Complete error catalog
- **[Cookbook: State Machines](../../cookbook/patterns/state-machines.md)** - Debug state transitions
- **[API Reference: Runtime](../../reference/runtime-api.md)** - Runtime exception handling

---

**Difficulty:** Beginner
**Time:** 15 minutes
**Last Updated:** 2025-10-15
