# Conditional Validation

**Validate fields based on the values of other fields - context-dependent constraints.**

---

## Problem

Field validation often depends on other fields:
- If payment method is "credit card", require card number
- If shipping method is "express", require delivery date
- If user type is "business", require company name
- If discount type is "percentage", validate 0-100 range
- If age < 18, require parent consent

**Bad approach:**
```python
# Python: Scattered conditional logic
def validate_payment(payment: dict):
    if payment.get('method') == 'credit_card':
        if not payment.get('card_number'):
            raise ValueError("Card number required")
    # Validation logic scattered everywhere
```

**Issues:**
- Logic duplication
- Easy to miss conditions
- Hard to test all paths
- Inconsistent validation

---

## Solution

Use contracts for declarative conditional validation:

```promptware
type Payment:
  method: String  # "credit_card" | "paypal" | "bank_transfer"
  card_number: Option<String>
  paypal_email: Option<String>
  bank_account: Option<String>
end

function validate_payment(payment: Payment) -> Result<Payment, String>
  do
    if payment.method == "credit_card":
      if payment.card_number is None:
        return Err("Credit card payment requires card number")
      end
    else if payment.method == "paypal":
      if payment.paypal_email is None:
        return Err("PayPal payment requires email")
      end
    else if payment.method == "bank_transfer":
      if payment.bank_account is None:
        return Err("Bank transfer requires account number")
      end
    end

    return Ok(payment)
  end
end
```

---

## Basic Conditional Patterns

### If-Then Validation

```promptware
type ShippingInfo:
  method: String
  address: Option<String>
  express_delivery_date: Option<String>
end

function validate_shipping(shipping: ShippingInfo) -> Result<ShippingInfo, String>
  do
    # If express shipping, require delivery date
    if shipping.method == "express":
      if shipping.express_delivery_date is None:
        return Err("Express shipping requires delivery date")
      end
    end

    # If home delivery, require address
    if shipping.method == "home_delivery" or shipping.method == "express":
      if shipping.address is None:
        return Err("Home delivery requires address")
      end
    end

    return Ok(shipping)
  end
end
```

### Age-Dependent Validation

```promptware
type UserRegistration:
  name: String
  age: Int
  parent_email: Option<String>
  accept_terms: Bool
end

function validate_registration(user: UserRegistration) -> Result<UserRegistration, List<String>>
  do
    let errors = []

    # Basic validation
    if len(user.name) == 0:
      errors = errors + ["Name required"]
    end

    if user.age < 0 or user.age > 150:
      errors = errors + ["Invalid age"]
    end

    # Conditional: If under 18, require parent email
    if user.age < 18:
      if user.parent_email is None:
        errors = errors + ["Users under 18 require parent email"]
      else if user.parent_email is Some(email):
        if not ("@" in email):
          errors = errors + ["Invalid parent email"]
        end
      end
    end

    # All users must accept terms
    if not user.accept_terms:
      errors = errors + ["Must accept terms and conditions"]
    end

    if len(errors) > 0:
      return Err(errors)
    end

    return Ok(user)
  end
end
```

---

## Business Rule Conditionals

### Discount Type Validation

```promptware
type Discount:
  discount_type: String  # "percentage" | "fixed_amount"
  value: Float
  max_discount: Option<Float>
end

function validate_discount(discount: Discount, order_total: Float) -> Result<Discount, String>
  requires:
    order_total >= 0.0
  do
    # Percentage discount: must be 0-100
    if discount.discount_type == "percentage":
      if discount.value < 0.0 or discount.value > 100.0:
        return Err("Percentage discount must be 0-100")
      end

      # If max discount specified, validate it
      if discount.max_discount is Some(max_val):
        if max_val <= 0.0:
          return Err("Max discount must be positive")
        end
      end
    end

    # Fixed amount discount: cannot exceed order total
    if discount.discount_type == "fixed_amount":
      if discount.value < 0.0:
        return Err("Fixed discount cannot be negative")
      end

      if discount.value > order_total:
        return Err("Fixed discount cannot exceed order total")
      end
    end

    return Ok(discount)
  end
end
```

### Account Type Validation

```promptware
type Account:
  account_type: String  # "personal" | "business"
  name: String
  company_name: Option<String>
  tax_id: Option<String>
end

function validate_account(account: Account) -> Result<Account, List<String>>
  do
    let errors = []

    if len(account.name) == 0:
      errors = errors + ["Name required"]
    end

    # Business accounts require company name and tax ID
    if account.account_type == "business":
      if account.company_name is None:
        errors = errors + ["Business account requires company name"]
      else if account.company_name is Some(company):
        if len(company) == 0:
          errors = errors + ["Company name cannot be empty"]
        end
      end

      if account.tax_id is None:
        errors = errors + ["Business account requires tax ID"]
      else if account.tax_id is Some(tax):
        if len(tax) != 9:
          errors = errors + ["Tax ID must be 9 digits"]
        end
      end
    end

    # Personal accounts should not have company fields
    if account.account_type == "personal":
      if account.company_name is Some:
        errors = errors + ["Personal account should not have company name"]
      end
    end

    if len(errors) > 0:
      return Err(errors)
    end

    return Ok(account)
  end
end
```

---

## Multi-Condition Validation

### Complex Dependencies

```promptware
type EmployeeForm:
  employee_type: String  # "full_time" | "part_time" | "contractor"
  salary: Option<Float>
  hourly_rate: Option<Float>
  benefits_eligible: Bool
  contract_end_date: Option<String>
end

function validate_employee(emp: EmployeeForm) -> Result<EmployeeForm, List<String>>
  do
    let errors = []

    # Full-time: require salary, eligible for benefits
    if emp.employee_type == "full_time":
      if emp.salary is None:
        errors = errors + ["Full-time employees require salary"]
      end

      if not emp.benefits_eligible:
        errors = errors + ["Full-time employees must be benefits eligible"]
      end

      # Should not have hourly rate or contract end date
      if emp.hourly_rate is Some:
        errors = errors + ["Full-time employees use salary, not hourly rate"]
      end
    end

    # Part-time: require hourly rate, optional benefits
    if emp.employee_type == "part_time":
      if emp.hourly_rate is None:
        errors = errors + ["Part-time employees require hourly rate"]
      end

      # Should not have salary
      if emp.salary is Some:
        errors = errors + ["Part-time employees use hourly rate, not salary"]
      end
    end

    # Contractor: require hourly rate and contract end date, no benefits
    if emp.employee_type == "contractor":
      if emp.hourly_rate is None:
        errors = errors + ["Contractors require hourly rate"]
      end

      if emp.contract_end_date is None:
        errors = errors + ["Contractors require contract end date"]
      end

      if emp.benefits_eligible:
        errors = errors + ["Contractors are not eligible for benefits"]
      end
    end

    if len(errors) > 0:
      return Err(errors)
    end

    return Ok(emp)
  end
end
```

---

## Real-World Examples

### E-Commerce Checkout

```python
# Python (FastAPI)
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from conditional_validation import validate_payment, validate_shipping, Err

app = FastAPI()

class PaymentModel(BaseModel):
    method: str
    card_number: Optional[str] = None
    paypal_email: Optional[str] = None
    bank_account: Optional[str] = None

class ShippingModel(BaseModel):
    method: str
    address: Optional[str] = None
    express_delivery_date: Optional[str] = None

class CheckoutRequest(BaseModel):
    payment: PaymentModel
    shipping: ShippingModel

@app.post("/checkout")
def checkout(request: CheckoutRequest):
    """Process checkout with conditional validation."""

    # Validate payment (conditional based on method)
    payment_result = validate_payment(to_pw_payment(request.payment))
    if isinstance(payment_result, Err):
        raise HTTPException(
            status_code=400,
            detail={"field": "payment", "error": payment_result.error}
        )

    # Validate shipping (conditional based on method)
    shipping_result = validate_shipping(to_pw_shipping(request.shipping))
    if isinstance(shipping_result, Err):
        raise HTTPException(
            status_code=400,
            detail={"field": "shipping", "error": shipping_result.error}
        )

    # Process checkout
    order_id = process_order(payment_result.value, shipping_result.value)

    return {
        "success": True,
        "order_id": order_id
    }
```

### User Profile Form

```python
# Python
from conditional_validation import validate_account, Err

def update_user_profile(user_id: str, profile_data: dict) -> dict:
    """Update user profile with conditional validation."""

    account = Account(
        account_type=profile_data['account_type'],
        name=profile_data['name'],
        company_name=profile_data.get('company_name'),
        tax_id=profile_data.get('tax_id')
    )

    # Validate account (business accounts have extra requirements)
    result = validate_account(account)

    if isinstance(result, Err):
        return {
            "success": False,
            "errors": result.error
        }

    # Update database
    update_user_in_db(user_id, result.value)

    return {
        "success": True,
        "user_id": user_id
    }
```

---

## Common Pitfalls

### ❌ Missing Conditions

```python
# Bad: Forgot to handle "contractor" case
def validate_bad(emp: Employee) -> bool:
    if emp.type == "full_time":
        return emp.salary is not None
    if emp.type == "part_time":
        return emp.hourly_rate is not None
    # Missing: contractor validation!
    return True
```

### ✅ Handle All Cases

```promptware
# Good: Explicit handling of all cases
function validate_good(emp: Employee) -> Result<Employee, String>
  do
    if emp.employee_type == "full_time":
      if emp.salary is None:
        return Err("Full-time requires salary")
      end
    else if emp.employee_type == "part_time":
      if emp.hourly_rate is None:
        return Err("Part-time requires hourly rate")
      end
    else if emp.employee_type == "contractor":
      if emp.hourly_rate is None or emp.contract_end_date is None:
        return Err("Contractor requires hourly rate and end date")
      end
    else:
      return Err("Unknown employee type: " + emp.employee_type)
    end

    return Ok(emp)
  end
end
```

### ❌ Inconsistent Validation

```python
# Bad: Validation differs between create and update
def create_user(data):
    if data['type'] == 'business':
        if 'tax_id' not in data:
            raise ValueError("Tax ID required")

def update_user(data):
    # Missing business account validation!
    if 'name' not in data:
        raise ValueError("Name required")
```

### ✅ Shared Validation

```promptware
# Good: Same validation for create and update
function validate_account(account: Account) -> Result<Account, List<String>>
  do
    # Shared validation logic used by both create and update
    let errors = []

    if account.account_type == "business":
      if account.tax_id is None:
        errors = errors + ["Business account requires tax ID"]
      end
    end

    # ... more shared validation ...

    if len(errors) > 0:
      return Err(errors)
    end

    return Ok(account)
  end
end
```

---

## Testing

```python
# Python (pytest)
import pytest
from conditional_validation import *

def test_payment_credit_card_valid():
    payment = Payment(
        method="credit_card",
        card_number=Some("4532015112830366"),
        paypal_email=None_(),
        bank_account=None_()
    )

    result = validate_payment(payment)
    assert isinstance(result, Ok)

def test_payment_credit_card_missing_number():
    payment = Payment(
        method="credit_card",
        card_number=None_(),
        paypal_email=None_(),
        bank_account=None_()
    )

    result = validate_payment(payment)
    assert isinstance(result, Err)
    assert "card number" in result.error.lower()

def test_registration_under_18_requires_parent():
    user = UserRegistration(
        name="Teen User",
        age=15,
        parent_email=None_(),
        accept_terms=True
    )

    result = validate_registration(user)
    assert isinstance(result, Err)
    assert any("parent email" in err.lower() for err in result.error)

def test_registration_under_18_with_parent():
    user = UserRegistration(
        name="Teen User",
        age=15,
        parent_email=Some("parent@example.com"),
        accept_terms=True
    )

    result = validate_registration(user)
    assert isinstance(result, Ok)

def test_business_account_requires_company():
    account = Account(
        account_type="business",
        name="John Doe",
        company_name=None_(),
        tax_id=Some("123456789")
    )

    result = validate_account(account)
    assert isinstance(result, Err)
    assert any("company name" in err.lower() for err in result.error)

def test_personal_account_no_company():
    account = Account(
        account_type="personal",
        name="John Doe",
        company_name=None_(),
        tax_id=None_()
    )

    result = validate_account(account)
    assert isinstance(result, Ok)
```

---

## See Also

- [Multi-Field Constraints](multi-field-constraints.md) - Cross-field validation
- [Nested Validation](nested-validation.md) - Complex object validation
- [Custom Validators](custom-validators.md) - Build reusable validators
- [Enum Validation](enum-validation.md) - Validate discrete values

---

**Difficulty:** Intermediate
**Time:** 10 minutes
**Category:** Validation
**Last Updated:** 2025-10-15
