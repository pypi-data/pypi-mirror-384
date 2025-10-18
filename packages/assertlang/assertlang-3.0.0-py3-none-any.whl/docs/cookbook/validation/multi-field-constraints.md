# Multi-Field Constraints

**Validate rules that span multiple fields - relationships between field values.**

---

## Problem

Many validation rules involve relationships between fields:
- Start date must be before end date
- Min value must be less than max value
- Password and confirmation password must match
- Total equals sum of line items
- At least one contact method required (email or phone)

**Bad approach:**
```python
# Python: Validation scattered across code
def create_event(start_date: str, end_date: str):
    # Validate start_date
    if not is_valid_date(start_date):
        raise ValueError("Invalid start date")

    # Validate end_date
    if not is_valid_date(end_date):
        raise ValueError("Invalid end date")

    # Missing: start < end check!
    # This bug allows end_date before start_date
```

**Issues:**
- Easy to miss cross-field rules
- Validation logic spread across codebase
- Inconsistent enforcement
- Hard to test all combinations

---

## Solution

Use contracts for explicit multi-field constraints:

```promptware
type Event:
  name: String
  start_date: String
  end_date: String
end

function create_event(event: Event) -> Result<Event, String>
  requires:
    len(event.name) > 0
    len(event.start_date) > 0
    len(event.end_date) > 0
  ensures:
    result.start_date <= result.end_date if result is Ok
  do
    # Validate individual fields
    if len(event.name) == 0:
      return Err("Name required")
    end

    # Validate multi-field constraint: start < end
    if event.start_date > event.end_date:
      return Err("Start date must be before end date")
    end

    return Ok(event)
  end
end
```

---

## Basic Multi-Field Patterns

### Date Range Validation

```promptware
function validate_date_range(
    start_date: String,
    end_date: String
) -> Result<Bool, String>
  requires:
    len(start_date) > 0
    len(end_date) > 0
  do
    # Ensure start <= end
    if start_date > end_date:
      return Err("Start date (" + start_date + ") must be before or equal to end date (" + end_date + ")")
    end

    return Ok(true)
  end
end
```

### Min/Max Validation

```promptware
type RangeFilter:
  min_value: Int
  max_value: Int
end

function validate_range_filter(filter: RangeFilter) -> Result<RangeFilter, String>
  do
    if filter.min_value > filter.max_value:
      return Err("Min value (" + String(filter.min_value) + ") cannot exceed max value (" + String(filter.max_value) + ")")
    end

    return Ok(filter)
  end
end
```

### Password Confirmation

```promptware
function validate_password_match(
    password: String,
    password_confirm: String
) -> Result<String, String>
  requires:
    len(password) > 0
    len(password_confirm) > 0
  do
    if password != password_confirm:
      return Err("Passwords do not match")
    end

    return Ok(password)
  end
end
```

---

## Sum/Total Validation

### Order Total Matches Line Items

```promptware
type LineItem:
  product_id: String
  quantity: Int
  unit_price: Float
end

type Order:
  items: List<LineItem>
  subtotal: Float
  tax: Float
  total: Float
end

function calculate_subtotal(items: List<LineItem>) -> Float
  do
    let sum = 0.0
    for item in items:
      sum = sum + (Float(item.quantity) * item.unit_price)
    end
    return sum
  end
end

function validate_order_totals(order: Order) -> Result<Order, List<String>>
  do
    let errors = []

    # Calculate expected subtotal
    let expected_subtotal = calculate_subtotal(order.items)

    # Validate subtotal
    if order.subtotal != expected_subtotal:
      errors = errors + ["Subtotal mismatch: expected " + String(expected_subtotal) + ", got " + String(order.subtotal)]
    end

    # Validate tax (must be non-negative)
    if order.tax < 0.0:
      errors = errors + ["Tax cannot be negative"]
    end

    # Validate total = subtotal + tax
    let expected_total = order.subtotal + order.tax

    if order.total != expected_total:
      errors = errors + ["Total mismatch: expected " + String(expected_total) + ", got " + String(order.total)]
    end

    if len(errors) > 0:
      return Err(errors)
    end

    return Ok(order)
  end
end
```

---

## At-Least-One Constraints

### Contact Information Required

```promptware
type ContactInfo:
  email: Option<String>
  phone: Option<String>
  address: Option<String>
end

function validate_contact_info(contact: ContactInfo) -> Result<ContactInfo, String>
  do
    # At least one contact method required
    let has_email = contact.email is Some
    let has_phone = contact.phone is Some
    let has_address = contact.address is Some

    if not has_email and not has_phone and not has_address:
      return Err("At least one contact method required (email, phone, or address)")
    end

    # If email provided, validate format
    if contact.email is Some(email):
      if not ("@" in email):
        return Err("Invalid email format")
      end
    end

    # If phone provided, validate format
    if contact.phone is Some(phone):
      if len(phone) != 10:
        return Err("Phone must be 10 digits")
      end
    end

    return Ok(contact)
  end
end
```

---

## Mutually Exclusive Fields

### Payment Method Selection

```promptware
type Payment:
  card_number: Option<String>
  paypal_email: Option<String>
  bank_account: Option<String>
end

function validate_payment_method(payment: Payment) -> Result<Payment, String>
  do
    let has_card = payment.card_number is Some
    let has_paypal = payment.paypal_email is Some
    let has_bank = payment.bank_account is Some

    # Exactly one payment method required
    let methods_count = 0
    if has_card:
      methods_count = methods_count + 1
    end
    if has_paypal:
      methods_count = methods_count + 1
    end
    if has_bank:
      methods_count = methods_count + 1
    end

    if methods_count == 0:
      return Err("Payment method required")
    end

    if methods_count > 1:
      return Err("Only one payment method allowed")
    end

    return Ok(payment)
  end
end
```

---

## Conditional Multi-Field Constraints

### Discount Limits

```promptware
type Order:
  subtotal: Float
  discount_type: String  # "percentage" | "fixed"
  discount_value: Float
  final_total: Float
end

function validate_order_discount(order: Order) -> Result<Order, List<String>>
  requires:
    order.subtotal >= 0.0
  do
    let errors = []

    # Calculate expected discount
    let discount_amount = 0.0

    if order.discount_type == "percentage":
      if order.discount_value < 0.0 or order.discount_value > 100.0:
        errors = errors + ["Percentage discount must be 0-100"]
      end

      discount_amount = order.subtotal * (order.discount_value / 100.0)
    else if order.discount_type == "fixed":
      if order.discount_value > order.subtotal:
        errors = errors + ["Fixed discount cannot exceed subtotal"]
      end

      discount_amount = order.discount_value
    end

    # Validate final total
    let expected_total = order.subtotal - discount_amount

    if order.final_total != expected_total:
      errors = errors + ["Final total mismatch: expected " + String(expected_total) + ", got " + String(order.final_total)]
    end

    if len(errors) > 0:
      return Err(errors)
    end

    return Ok(order)
  end
end
```

---

## Real-World Examples

### Event Scheduling

```python
# Python (FastAPI)
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from multi_field_validation import validate_date_range, Err

app = FastAPI()

class EventRequest(BaseModel):
    name: str
    start_date: str
    end_date: str
    location: str

@app.post("/events")
def create_event(event: EventRequest):
    """Create event with date range validation."""

    # Validate date range (multi-field constraint)
    date_result = validate_date_range(event.start_date, event.end_date)

    if isinstance(date_result, Err):
        raise HTTPException(
            status_code=400,
            detail={"error": date_result.error}
        )

    # Create event
    event_id = save_event_to_db(event)

    return {
        "success": True,
        "event_id": event_id
    }
```

### Price Range Filter

```python
# Python
from multi_field_validation import validate_range_filter, Err

def search_products(min_price: float, max_price: float):
    """Search products with price range validation."""

    # Create range filter
    filter_obj = RangeFilter(
        min_value=int(min_price * 100),  # Convert to cents
        max_value=int(max_price * 100)
    )

    # Validate multi-field constraint: min <= max
    result = validate_range_filter(filter_obj)

    if isinstance(result, Err):
        return {
            "success": False,
            "error": result.error
        }

    # Search database
    products = db_search_products(
        min_price=filter_obj.min_value,
        max_price=filter_obj.max_value
    )

    return {
        "success": True,
        "products": products
    }
```

### User Registration

```python
# Python
from multi_field_validation import validate_password_match, validate_contact_info, Err

def register_user(
    username: str,
    password: str,
    password_confirm: str,
    email: str = None,
    phone: str = None
) -> dict:
    """Register user with multi-field validation."""

    errors = []

    # Password match validation
    password_result = validate_password_match(password, password_confirm)
    if isinstance(password_result, Err):
        errors.append(password_result.error)

    # Contact info validation (at least one required)
    contact = ContactInfo(
        email=Some(email) if email else None_(),
        phone=Some(phone) if phone else None_(),
        address=None_()
    )

    contact_result = validate_contact_info(contact)
    if isinstance(contact_result, Err):
        errors.append(contact_result.error)

    if errors:
        return {
            "success": False,
            "errors": errors
        }

    # Create user
    user_id = create_user_in_db(username, password_result.value, contact_result.value)

    return {
        "success": True,
        "user_id": user_id
    }
```

---

## Common Pitfalls

### ❌ Forgetting Cross-Field Checks

```python
# Bad: Validates fields individually but not their relationship
def create_event_bad(start: str, end: str):
    if not is_valid_date(start):
        raise ValueError("Invalid start date")
    if not is_valid_date(end):
        raise ValueError("Invalid end date")
    # Missing: start < end check!
    return Event(start, end)
```

### ✅ Validate Relationships

```promptware
# Good: Explicit cross-field validation
function create_event_good(start: String, end: String) -> Result<Event, String>
  do
    # Individual validation
    if not is_valid_date(start):
      return Err("Invalid start date")
    end

    if not is_valid_date(end):
      return Err("Invalid end date")
    end

    # Multi-field constraint
    if start > end:
      return Err("Start date must be before end date")
    end

    return Ok(Event(start, end))
  end
end
```

### ❌ Weak At-Least-One Checks

```python
# Bad: Doesn't actually check if at least one is provided
def validate_contact_bad(email: str, phone: str):
    # Both could be empty strings!
    return True
```

### ✅ Strong At-Least-One

```promptware
# Good: Verify at least one has value
function validate_contact_good(
    email: Option<String>,
    phone: Option<String>
) -> Result<Bool, String>
  do
    if email is None and phone is None:
      return Err("At least one contact method required")
    end

    return Ok(true)
  end
end
```

---

## Testing

```python
# Python (pytest)
import pytest
from multi_field_validation import *

def test_date_range_valid():
    result = validate_date_range("2025-01-01", "2025-12-31")
    assert isinstance(result, Ok)

def test_date_range_invalid():
    result = validate_date_range("2025-12-31", "2025-01-01")
    assert isinstance(result, Err)
    assert "before" in result.error.lower()

def test_range_filter_valid():
    filter = RangeFilter(min_value=10, max_value=100)
    result = validate_range_filter(filter)
    assert isinstance(result, Ok)

def test_range_filter_invalid():
    filter = RangeFilter(min_value=100, max_value=10)
    result = validate_range_filter(filter)
    assert isinstance(result, Err)
    assert "min" in result.error.lower() and "max" in result.error.lower()

def test_password_match_valid():
    result = validate_password_match("password123", "password123")
    assert isinstance(result, Ok)

def test_password_match_invalid():
    result = validate_password_match("password123", "different")
    assert isinstance(result, Err)
    assert "match" in result.error.lower()

def test_order_totals_valid():
    order = Order(
        items=[
            LineItem("PROD-1", 2, 10.00),
            LineItem("PROD-2", 1, 20.00)
        ],
        subtotal=40.00,
        tax=4.00,
        total=44.00
    )

    result = validate_order_totals(order)
    assert isinstance(result, Ok)

def test_order_totals_invalid_subtotal():
    order = Order(
        items=[
            LineItem("PROD-1", 2, 10.00)
        ],
        subtotal=100.00,  # Wrong!
        tax=10.00,
        total=110.00
    )

    result = validate_order_totals(order)
    assert isinstance(result, Err)
    assert any("subtotal" in err.lower() for err in result.error)

def test_contact_info_at_least_one():
    # Valid: has email
    contact = ContactInfo(
        email=Some("user@example.com"),
        phone=None_(),
        address=None_()
    )
    assert isinstance(validate_contact_info(contact), Ok)

    # Invalid: no contact method
    contact = ContactInfo(
        email=None_(),
        phone=None_(),
        address=None_()
    )
    assert isinstance(validate_contact_info(contact), Err)

def test_payment_method_mutually_exclusive():
    # Valid: exactly one method
    payment = Payment(
        card_number=Some("1234567890123456"),
        paypal_email=None_(),
        bank_account=None_()
    )
    assert isinstance(validate_payment_method(payment), Ok)

    # Invalid: multiple methods
    payment = Payment(
        card_number=Some("1234567890123456"),
        paypal_email=Some("user@paypal.com"),
        bank_account=None_()
    )
    result = validate_payment_method(payment)
    assert isinstance(result, Err)
    assert "one" in result.error.lower()
```

---

## Performance Considerations

### Short-Circuit Evaluation

```promptware
# Check cheapest constraints first
function validate_fast(start: String, end: String) -> Result<Bool, String>
  do
    # Quick length check first
    if len(start) != 10 or len(end) != 10:
      return Err("Invalid date format")  # Fast fail
    end

    # More expensive date parsing and comparison
    if start > end:
      return Err("Start must be before end")
    end

    return Ok(true)
  end
end
```

---

## See Also

- [Conditional Validation](conditional-validation.md) - Field-dependent validation
- [Nested Validation](nested-validation.md) - Complex object validation
- [Custom Validators](custom-validators.md) - Build reusable validators
- [Range Checking](range-checking.md) - Numeric bounds

---

**Difficulty:** Intermediate
**Time:** 10 minutes
**Category:** Validation
**Last Updated:** 2025-10-15
