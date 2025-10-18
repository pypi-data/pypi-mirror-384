# Recipe: Positive Number Validation

**Problem:** Ensure numeric inputs are positive (> 0) to prevent calculation errors and invalid states.

**Difficulty:** Beginner
**Time:** 5 minutes

---

## The Problem

Functions expecting positive numbers break with:
- **Zero**: Division by zero, log(0) = undefined
- **Negative**: Invalid quantities, amounts, counts
- **Silent failures**: Wrong results instead of clear errors

Common scenarios: prices, quantities, ages, counts, durations.

---

## Solution

```al
function calculate_discount(
    original_price: float,
    discount_percent: float
) -> float {
    @requires price_positive: original_price > 0.0
    @requires valid_percent: discount_percent > 0.0 && discount_percent <= 100.0

    @ensures result_positive: result >= 0.0
    @ensures discount_applied: result <= original_price

    let discount_amount = original_price * (discount_percent / 100.0);
    let final_price = original_price - discount_amount;

    return final_price;
}
```

**Generated Python:**
```python
from promptware.runtime.contracts import check_precondition, check_postcondition

def calculate_discount(original_price: float, discount_percent: float) -> float:
    # Preconditions
    check_precondition(original_price > 0.0, "price_positive",
        f"Price must be positive, got {original_price}")
    check_precondition(
        discount_percent > 0.0 and discount_percent <= 100.0,
        "valid_percent",
        f"Discount percent must be 0-100, got {discount_percent}"
    )

    # Logic
    discount_amount = original_price * (discount_percent / 100.0)
    final_price = original_price - discount_amount

    # Postconditions
    check_postcondition(final_price >= 0.0, "result_positive",
        f"Result must be non-negative, got {final_price}")
    check_postcondition(final_price <= original_price, "discount_applied",
        f"Result must be <= original price")

    return final_price
```

---

## Explanation

**Three validation layers:**
1. `original_price > 0.0` - No zero or negative prices
2. `discount_percent > 0.0 && <= 100.0` - Valid percentage range
3. `result >= 0.0` - Final price can't be negative (catches bugs)

**Why postcondition?** Catches discount logic bugs (e.g., discount > price).

---

## Variations

### Non-Negative (Allows Zero)
```al
@requires non_negative: amount >= 0.0
// Allows 0.0 (useful for optional amounts)
```

### Strict Positive (Excludes Zero)
```al
@requires strictly_positive: amount > 0.0
// Rejects 0.0
```

### Integer Positive
```al
@requires positive_int: quantity > 0
// For counts, quantities
```

### Range Validation
```al
@requires in_range: value > 0.0 && value <= 1000.0
// Between 0 and 1000
```

### Multiple Values
```al
@requires all_positive: price > 0.0 && quantity > 0 && tax_rate >= 0.0
// Validate multiple parameters
```

---

## Common Pitfalls

### ❌ Using `>=` instead of `>`
```al
@requires positive: amount >= 0.0
// Allows 0.0 (may cause division by zero)
```

**Problem**: Zero passes, causes errors downstream.

**Fix**: Use `> 0.0` for strictly positive, document if zero allowed.

---

### ❌ No range upper bound
```al
@requires positive: price > 0.0
// Allows unrealistic values like 999999999
```

**Problem**: No sanity check on maximum.

**Fix**: Add reasonable upper bound.
```al
@requires reasonable_price: price > 0.0 && price <= 1000000.0
```

---

### ❌ Integer/float mismatch
```al
function process(count: int) -> int {
    @requires positive: count > 0.0  // ❌ Comparing int to float
```

**Fix**: Use integer literal.
```al
@requires positive: count > 0  // ✓ Integer comparison
```

---

## Real-World Example

**E-commerce order calculation:**
```al
function calculate_order_total(
    item_price: float,
    quantity: int,
    tax_rate: float
) -> float {
    @requires price_positive: item_price > 0.0
    @requires price_reasonable: item_price <= 100000.0
    @requires quantity_positive: quantity > 0
    @requires quantity_reasonable: quantity <= 1000
    @requires tax_valid: tax_rate >= 0.0 && tax_rate <= 0.5

    @ensures result_positive: result > 0.0
    @ensures includes_tax: result >= (item_price * quantity)

    let subtotal = item_price * quantity;
    let tax_amount = subtotal * tax_rate;
    let total = subtotal + tax_amount;

    return total;
}
```

**Usage:**
```python
from order_validation import calculate_order_total

# ✓ Valid
total = calculate_order_total(
    item_price=29.99,
    quantity=3,
    tax_rate=0.08
)  # Returns: 97.17

# ❌ Invalid (caught by contracts)
calculate_order_total(0.0, 3, 0.08)     # price_positive failed
calculate_order_total(29.99, 0, 0.08)   # quantity_positive failed
calculate_order_total(29.99, 3, 1.5)    # tax_valid failed (150%)
calculate_order_total(29.99, 9999, 0.08) # quantity_reasonable failed
```

---

## Testing Pattern

```python
import pytest
from order_validation import calculate_order_total

def test_valid_calculation():
    result = calculate_order_total(100.0, 2, 0.1)
    assert result == 220.0  # (100*2) + 20% tax

def test_zero_price_rejected():
    with pytest.raises(Exception, match="price_positive"):
        calculate_order_total(0.0, 2, 0.1)

def test_negative_quantity_rejected():
    with pytest.raises(Exception, match="quantity_positive"):
        calculate_order_total(100.0, -5, 0.1)

def test_invalid_tax_rate_rejected():
    with pytest.raises(Exception, match="tax_valid"):
        calculate_order_total(100.0, 2, 1.5)  # 150% tax!
```

---

## Performance Note

**Overhead**: ~1µs per contract check
**Impact**: Negligible for typical use

**Disable in production** (if needed):
```bash
export PROMPTWARE_DISABLE_CONTRACTS=1
```

Contracts still serve as documentation.

---

## See Also

- **[Non-Empty Strings](non-empty-strings.md)** - String validation patterns
- **[Array Bounds](array-bounds.md)** - Index and size validation
- **[Range Checking](range-checking.md)** - Min/max bounds
- **[Multi-Field Constraints](multi-field-constraints.md)** - Validate related fields
- **[E-commerce Orders Example](../../../examples/real_world/01_ecommerce_orders/)** - Complete working example

---

**Next**: Try [Array Bounds](array-bounds.md) for collection validation →
