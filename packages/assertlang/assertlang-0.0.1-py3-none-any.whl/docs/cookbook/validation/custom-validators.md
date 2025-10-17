# Custom Validators

**Build reusable, composable validation functions for domain-specific constraints.**

---

## Problem

Standard validations (non-empty, positive, range) don't cover domain-specific rules:
- Username format (alphanumeric, 3-20 chars, no special chars)
- Password strength (8+ chars, uppercase, lowercase, digit, symbol)
- Credit card validation (Luhn algorithm)
- ISBN validation (check digit)
- Custom business rules

**Bad approach:**
```python
# Python: Validation logic scattered everywhere
def create_user(username: str, password: str):
    # Duplicate validation in every function
    if not username or len(username) < 3 or len(username) > 20:
        raise ValueError("Invalid username")
    if len(password) < 8 or not any(c.isupper() for c in password):
        raise ValueError("Invalid password")
    # ... more validation ...
```

**Issues:**
- Code duplication
- Inconsistent validation
- Hard to test
- Not reusable

---

## Solution

Build custom validators with contracts:

```promptware
function validate_username(username: String) -> Result<String, String>
  requires:
    len(username) > 0
  do
    if len(username) < 3:
      return Err("Username too short (min 3 chars)")
    end

    if len(username) > 20:
      return Err("Username too long (max 20 chars)")
    end

    # Check alphanumeric
    if not is_alphanumeric(username):
      return Err("Username must be alphanumeric")
    end

    return Ok(username)
  end
end
```

---

## Basic Custom Validators

### Username Validator

```promptware
function is_alphanumeric(text: String) -> Bool
  requires:
    len(text) > 0
  do
    # Check if all characters are letters or digits
    # (Implementation would use regex or character checking)
    return true  # Simplified
  end
end

function validate_username(username: String) -> Result<String, String>
  requires:
    len(username) > 0
  do
    # Length check
    if len(username) < 3:
      return Err("Username must be at least 3 characters")
    end

    if len(username) > 20:
      return Err("Username must be at most 20 characters")
    end

    # Format check
    if not is_alphanumeric(username):
      return Err("Username must contain only letters and numbers")
    end

    # Reserved words check
    let reserved = ["admin", "root", "system", "null"]
    for word in reserved:
      if username == word:
        return Err("Username '" + username + "' is reserved")
      end
    end

    return Ok(username)
  end
end
```

### Password Strength Validator

```promptware
function has_uppercase(text: String) -> Bool
  do
    # Check for at least one uppercase letter
    return true  # Simplified
  end
end

function has_lowercase(text: String) -> Bool
  do
    return true  # Simplified
  end
end

function has_digit(text: String) -> Bool
  do
    return true  # Simplified
  end
end

function has_special_char(text: String) -> Bool
  do
    return true  # Simplified
  end
end

function validate_password(password: String) -> Result<String, List<String>>
  requires:
    len(password) > 0
  do
    let errors = []

    # Length check
    if len(password) < 8:
      errors = errors + ["Password must be at least 8 characters"]
    end

    if len(password) > 128:
      errors = errors + ["Password must be at most 128 characters"]
    end

    # Complexity checks
    if not has_uppercase(password):
      errors = errors + ["Password must contain at least one uppercase letter"]
    end

    if not has_lowercase(password):
      errors = errors + ["Password must contain at least one lowercase letter"]
    end

    if not has_digit(password):
      errors = errors + ["Password must contain at least one digit"]
    end

    if not has_special_char(password):
      errors = errors + ["Password must contain at least one special character"]
    end

    # Return all errors or success
    if len(errors) > 0:
      return Err(errors)
    end

    return Ok(password)
  end
end
```

---

## Composable Validators

### Combining Validators

```promptware
function validate_user_registration(
    username: String,
    password: String,
    email: String
) -> Result<Bool, List<String>>
  requires:
    len(username) > 0
    len(password) > 0
    len(email) > 0
  do
    let errors = []

    # Validate username
    let username_result = validate_username(username)
    if username_result is Err(msg):
      errors = errors + ["Username: " + msg]
    end

    # Validate password
    let password_result = validate_password(password)
    if password_result is Err(password_errors):
      for err in password_errors:
        errors = errors + ["Password: " + err]
      end
    end

    # Validate email
    let email_result = validate_email_strict(email)
    if email_result is Err(msg):
      errors = errors + ["Email: " + msg]
    end

    if len(errors) > 0:
      return Err(errors)
    end

    return Ok(true)
  end
end
```

### Validator Pipeline

```promptware
function chain_validators<T>(
    value: T,
    validators: List<function(T) -> Result<T, String>>
) -> Result<T, String>
  requires:
    len(validators) > 0
  do
    let current = value

    for validator in validators:
      let result = validator(current)
      if result is Err(msg):
        return Err(msg)
      else if result is Ok(validated):
        current = validated
      end
    end

    return Ok(current)
  end
end
```

---

## Domain-Specific Validators

### Credit Card Validation (Luhn Algorithm)

```promptware
function luhn_check(card_number: String) -> Bool
  requires:
    len(card_number) > 0
  do
    let sum = 0
    let double_digit = false
    let length = len(card_number)
    let i = length - 1

    while i >= 0:
      let digit_char = card_number[i]
      let digit = parse_digit(digit_char)

      if double_digit:
        digit = digit * 2
        if digit > 9:
          digit = digit - 9
        end
      end

      sum = sum + digit
      double_digit = not double_digit
      i = i - 1
    end

    return (sum % 10) == 0
  end
end

function validate_credit_card(card_number: String) -> Result<String, String>
  requires:
    len(card_number) > 0
  do
    # Remove spaces and dashes
    let cleaned = card_number.replace(" ", "").replace("-", "")

    # Check length (13-19 digits for most cards)
    if len(cleaned) < 13 or len(cleaned) > 19:
      return Err("Card number must be 13-19 digits")
    end

    # Check if all digits
    if not is_numeric(cleaned):
      return Err("Card number must contain only digits")
    end

    # Luhn algorithm check
    if not luhn_check(cleaned):
      return Err("Invalid card number (failed checksum)")
    end

    return Ok(cleaned)
  end
end
```

### Phone Number Validation

```promptware
function validate_phone_number(
    phone: String,
    country_code: String
) -> Result<String, String>
  requires:
    len(phone) > 0
    len(country_code) > 0
  do
    # Remove formatting
    let cleaned = phone.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")

    # US phone numbers
    if country_code == "US":
      if len(cleaned) != 10:
        return Err("US phone number must be 10 digits")
      end

      if not is_numeric(cleaned):
        return Err("Phone number must contain only digits")
      end

      # Format: (XXX) XXX-XXXX
      let formatted = "(" + cleaned.substring(0, 3) + ") " +
                      cleaned.substring(3, 6) + "-" +
                      cleaned.substring(6, 10)

      return Ok(formatted)
    end

    # Other countries...
    return Err("Country code not supported: " + country_code)
  end
end
```

---

## Real-World Examples

### User Registration System

```python
# Python (FastAPI)
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from custom_validators import (
    validate_username,
    validate_password,
    validate_email_strict,
    Err
)

app = FastAPI()

class UserRegistration(BaseModel):
    username: str
    password: str
    email: str

@app.post("/register")
def register_user(user: UserRegistration):
    """Register new user with custom validation."""

    errors = []

    # Validate username
    username_result = validate_username(user.username)
    if isinstance(username_result, Err):
        errors.append(f"Username: {username_result.error}")

    # Validate password
    password_result = validate_password(user.password)
    if isinstance(password_result, Err):
        for err in password_result.error:
            errors.append(f"Password: {err}")

    # Validate email
    email_result = validate_email_strict(user.email)
    if isinstance(email_result, Err):
        errors.append(f"Email: {email_result.error}")

    # Return errors if any
    if errors:
        raise HTTPException(
            status_code=400,
            detail={"errors": errors}
        )

    # Create user
    user_id = create_user_in_db(
        username=username_result.value,
        password_hash=hash_password(password_result.value),
        email=email_result.value
    )

    return {
        "success": True,
        "user_id": user_id,
        "username": username_result.value
    }
```

### E-Commerce Product Validation

```python
# Python
from custom_validators import *

class ProductValidator:
    @staticmethod
    def validate_product(
        name: str,
        price: float,
        sku: str,
        quantity: int
    ) -> dict:
        """Validate product data."""

        errors = []

        # Name validation
        if len(name) == 0:
            errors.append("Product name cannot be empty")
        elif len(name) > 200:
            errors.append("Product name too long (max 200 chars)")

        # Price validation
        price_result = validate_price(price, "USD")
        if isinstance(price_result, Err):
            errors.append(f"Price: {price_result.error}")

        # SKU validation (format: ABC-12345)
        sku_result = validate_sku(sku)
        if isinstance(sku_result, Err):
            errors.append(f"SKU: {sku_result.error}")

        # Quantity validation
        qty_result = validate_quantity(quantity, max_quantity=99999)
        if isinstance(qty_result, Err):
            errors.append(f"Quantity: {qty_result.error}")

        if errors:
            return {
                "valid": False,
                "errors": errors
            }

        return {
            "valid": True,
            "data": {
                "name": name,
                "price": price_result.value,
                "sku": sku_result.value,
                "quantity": qty_result.value
            }
        }

def validate_sku(sku: str) -> Result[str, str]:
    """Validate SKU format: ABC-12345"""
    if len(sku) == 0:
        return Err("SKU cannot be empty")

    if len(sku) != 9:  # ABC-12345
        return Err("SKU must be 9 characters (format: ABC-12345)")

    if sku[3] != '-':
        return Err("SKU must contain dash at position 4")

    prefix = sku[0:3]
    suffix = sku[4:9]

    if not prefix.isupper() or not prefix.isalpha():
        return Err("SKU prefix must be 3 uppercase letters")

    if not suffix.isdigit():
        return Err("SKU suffix must be 5 digits")

    return Ok(sku)
```

---

## Testing Custom Validators

```python
# Python (pytest)
import pytest
from custom_validators import *

def test_validate_username_valid():
    assert isinstance(validate_username("john"), Ok)
    assert isinstance(validate_username("user123"), Ok)
    assert isinstance(validate_username("alice"), Ok)

def test_validate_username_invalid():
    # Too short
    result = validate_username("ab")
    assert isinstance(result, Err)
    assert "too short" in result.error.lower()

    # Too long
    result = validate_username("a" * 21)
    assert isinstance(result, Err)
    assert "too long" in result.error.lower()

    # Reserved word
    result = validate_username("admin")
    assert isinstance(result, Err)
    assert "reserved" in result.error.lower()

def test_validate_password_weak():
    result = validate_password("weak")
    assert isinstance(result, Err)
    assert len(result.error) >= 3  # Multiple errors

def test_validate_password_strong():
    result = validate_password("StrongP@ss123")
    assert isinstance(result, Ok)

def test_luhn_check():
    # Valid card numbers
    assert luhn_check("4532015112830366") == True
    assert luhn_check("5425233430109903") == True

    # Invalid card numbers
    assert luhn_check("4532015112830367") == False

def test_validate_credit_card():
    # Valid
    result = validate_credit_card("4532-0151-1283-0366")
    assert isinstance(result, Ok)
    assert result.value == "4532015112830366"

    # Invalid
    result = validate_credit_card("1234")
    assert isinstance(result, Err)

def test_validate_phone_number_us():
    # Valid formats
    result = validate_phone_number("5551234567", "US")
    assert isinstance(result, Ok)
    assert result.value == "(555) 123-4567"

    result = validate_phone_number("(555) 123-4567", "US")
    assert isinstance(result, Ok)

    # Invalid
    result = validate_phone_number("123", "US")
    assert isinstance(result, Err)
```

---

## Common Pitfalls

### ❌ Validator Returns None on Success

```python
# Bad: Can't distinguish success from error
def validate_bad(value: str) -> Optional[str]:
    if is_valid(value):
        return None  # Success = None?
    return "Error message"
```

### ✅ Use Result Type

```promptware
# Good: Explicit success/error
function validate_good(value: String) -> Result<String, String>
  do
    if is_valid(value):
      return Ok(value)
    else:
      return Err("Error message")
    end
  end
end
```

### ❌ Silent Validation

```python
# Bad: Silently fixes invalid input
def clean_username(username: str) -> str:
    # Removes special chars without telling user
    return ''.join(c for c in username if c.isalnum())
```

### ✅ Explicit Validation

```promptware
# Good: Tell user what's wrong
function validate_username_strict(username: String) -> Result<String, String>
  do
    if not is_alphanumeric(username):
      return Err("Username contains invalid characters")
    end
    return Ok(username)
  end
end
```

---

## Performance Considerations

### Cache Validation Results

```python
# Python: Cache expensive validations
from functools import lru_cache

@lru_cache(maxsize=1000)
def validate_expensive(value: str) -> bool:
    # Expensive validation (regex, external API, etc.)
    return expensive_check(value)
```

### Fail Fast

```promptware
# Stop at first error for performance
function validate_fast(value: String) -> Result<String, String>
  do
    # Check cheapest validations first
    if len(value) == 0:
      return Err("Empty")  # Fast check
    end

    if len(value) > 1000:
      return Err("Too long")  # Fast check
    end

    # Expensive checks last
    if not complex_validation(value):
      return Err("Complex validation failed")
    end

    return Ok(value)
  end
end
```

---

## See Also

- [Non-Empty Strings](non-empty-strings.md) - Basic string validation
- [Email Validation](email-validation.md) - Email-specific patterns
- [Range Checking](range-checking.md) - Numeric bounds
- [Nested Validation](nested-validation.md) - Complex object validation

---

**Difficulty:** Intermediate
**Time:** 15 minutes
**Category:** Validation
**Last Updated:** 2025-10-15
