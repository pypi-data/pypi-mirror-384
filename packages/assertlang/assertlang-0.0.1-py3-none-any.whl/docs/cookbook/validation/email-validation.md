# Email Validation

**Validate email addresses with contracts to ensure data quality.**

---

## Problem

You need to validate email addresses across your application:
- User registration forms
- Contact information
- Email campaign recipients
- API endpoints accepting emails

**Bad approach:**
```python
# Python: No validation
def send_email(email: str):
    # Sends to invalid emails
    # Crashes on malformed input
    smtp.send(email, message)
```

**Issues:**
- Invalid emails accepted
- Bounced messages
- Database filled with junk
- No consistent validation

---

## Solution

Use contracts to enforce email format:

```promptware
function send_email(email: String) -> Bool
  requires:
    len(email) > 0
    "@" in email
    len(email) <= 255
    not email.startswith("@")
    not email.endswith("@")
  do
    # Send email implementation
    return true
  end
end
```

---

## Basic Email Validation

### Simple Check

```promptware
function is_valid_email(email: String) -> Bool
  do
    return (
      len(email) > 0 and
      "@" in email and
      len(email) <= 255 and
      not email.startswith("@") and
      not email.endswith("@")
    )
  end
end
```

**Generated Python:**
```python
def is_valid_email(email: str) -> bool:
    return (
        len(email) > 0 and
        "@" in email and
        len(email) <= 255 and
        not email.startswith("@") and
        not email.endswith("@")
    )
```

### With Contracts

```promptware
function validate_email(email: String) -> Result<String, String>
  requires:
    len(email) > 0
  do
    if not ("@" in email):
      return Err("Email must contain @")
    end

    if email.startswith("@") or email.endswith("@"):
      return Err("Email cannot start or end with @")
    end

    if len(email) > 255:
      return Err("Email too long (max 255 chars)")
    end

    return Ok(email)
  end
end
```

---

## Advanced Email Validation

### RFC 5322 Basic Compliance

```promptware
function validate_email_strict(email: String) -> Result<String, String>
  requires:
    len(email) > 0
  do
    # Split into local and domain parts
    if not ("@" in email):
      return Err("Missing @ symbol")
    end

    let parts = email.split("@")
    if len(parts) != 2:
      return Err("Email must have exactly one @ symbol")
    end

    let local = parts[0]
    let domain = parts[1]

    # Validate local part (before @)
    if len(local) == 0:
      return Err("Local part cannot be empty")
    end

    if len(local) > 64:
      return Err("Local part too long (max 64 chars)")
    end

    if local.startswith(".") or local.endswith("."):
      return Err("Local part cannot start or end with .")
    end

    # Validate domain part (after @)
    if len(domain) == 0:
      return Err("Domain cannot be empty")
    end

    if len(domain) > 255:
      return Err("Domain too long (max 255 chars)")
    end

    if not ("." in domain):
      return Err("Domain must contain at least one .")
    end

    if domain.startswith(".") or domain.endswith("."):
      return Err("Domain cannot start or end with .")
    end

    return Ok(email)
  end
end
```

---

## Domain-Specific Validation

### Corporate Email Only

```promptware
function validate_corporate_email(
    email: String,
    allowed_domains: List<String>
) -> Result<String, String>
  requires:
    len(email) > 0
    len(allowed_domains) > 0
  do
    # Basic validation first
    let basic = validate_email_strict(email)
    if basic is Err(msg):
      return Err(msg)
    end

    # Extract domain
    let parts = email.split("@")
    let domain = parts[1]

    # Check if domain is allowed
    let domain_allowed = false
    for allowed in allowed_domains:
      if domain == allowed:
        domain_allowed = true
      end
    end

    if not domain_allowed:
      return Err("Email domain not allowed: " + domain)
    end

    return Ok(email)
  end
end
```

**Usage:**
```python
# Python
allowed = ["company.com", "subsidiary.com"]
result = validate_corporate_email("user@company.com", allowed)

if result.is_ok():
    email = result.unwrap()
else:
    error = result.unwrap_err()
    print(f"Validation failed: {error}")
```

---

## Batch Email Validation

### Validate Multiple Emails

```promptware
function validate_emails(emails: List<String>) -> Result<List<String>, String>
  requires:
    len(emails) > 0
    len(emails) <= 1000  # Batch size limit
  do
    let valid_emails = []
    let errors = []

    for email in emails:
      let result = validate_email_strict(email)
      if result is Ok(validated):
        valid_emails = valid_emails + [validated]
      else if result is Err(msg):
        errors = errors + [email + ": " + msg]
      end
    end

    if len(errors) > 0:
      return Err("Validation errors: " + String(len(errors)))
    end

    return Ok(valid_emails)
  end
end
```

---

## Integration Examples

### FastAPI Endpoint

```python
# Python (FastAPI)
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from email_validation import validate_email_strict, Ok, Err

app = FastAPI()

class UserRegistration(BaseModel):
    name: str
    email: str

@app.post("/register")
def register_user(user: UserRegistration):
    # Validate email with contract
    result = validate_email_strict(user.email)

    if isinstance(result, Err):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid email: {result.error}"
        )

    # Email is valid
    validated_email = result.value
    # ... create user ...

    return {"message": "User registered", "email": validated_email}
```

### Django Form

```python
# Python (Django)
from django import forms
from email_validation import validate_email_strict, Err

class ContactForm(forms.Form):
    name = forms.CharField(max_length=100)
    email = forms.CharField(max_length=255)

    def clean_email(self):
        email = self.cleaned_data['email']

        # Validate with contract
        result = validate_email_strict(email)

        if isinstance(result, Err):
            raise forms.ValidationError(result.error)

        return result.value
```

---

## Common Pitfalls

### ❌ Too Strict

```promptware
# Don't reject valid international domains
function validate_email_bad(email: String) -> Bool
  requires:
    email.endswith(".com")  # Too strict! Rejects .org, .net, .io, etc.
  do
    return true
  end
end
```

### ❌ Regex in Contracts

```promptware
# Don't use complex regex in contracts
function validate_email_regex(email: String) -> Bool
  requires:
    # This is too complex for contracts
    email.matches("^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$")
  do
    return true
  end
end
```

**Better:** Use simple checks in contracts, regex in implementation.

### ✅ Good Pattern

```promptware
function validate_email_good(email: String) -> Result<String, String>
  requires:
    len(email) > 0
    len(email) <= 255
  do
    # Use simple checks
    if not ("@" in email):
      return Err("Invalid email format")
    end

    # More complex validation in body
    # (regex can go here if needed)

    return Ok(email)
  end
end
```

---

## Variations

### Case Insensitive

```promptware
function normalize_email(email: String) -> String
  requires:
    len(email) > 0
  ensures:
    len(result) > 0
  do
    # Convert to lowercase for consistency
    return email.lower()
  end
end

function validate_email_normalized(email: String) -> Result<String, String>
  do
    let normalized = normalize_email(email)
    return validate_email_strict(normalized)
  end
end
```

### With Suggestions

```promptware
function validate_with_suggestions(email: String) -> Result<String, List<String>>
  do
    let result = validate_email_strict(email)

    if result is Err(msg):
      let suggestions = []

      # Common typos
      if not ("@" in email):
        suggestions = suggestions + ["Did you forget the @ symbol?"]
      end

      if email.endswith("@gmail") or email.endswith("@yahoo"):
        suggestions = suggestions + ["Did you mean " + email + ".com?"]
      end

      return Err(suggestions)
    end

    return Ok(result.value)
  end
end
```

---

## Testing

### Unit Tests

```python
# Python (pytest)
import pytest
from email_validation import validate_email_strict, Ok, Err

def test_valid_emails():
    valid = [
        "user@example.com",
        "test.user@company.co.uk",
        "admin+tag@domain.org",
    ]

    for email in valid:
        result = validate_email_strict(email)
        assert isinstance(result, Ok), f"Failed for {email}"

def test_invalid_emails():
    invalid = [
        "",                      # Empty
        "no-at-symbol",         # Missing @
        "@example.com",         # Missing local
        "user@",                # Missing domain
        "user@@example.com",    # Double @
        "user@domain",          # Missing TLD
        "a" * 256,              # Too long
    ]

    for email in invalid:
        result = validate_email_strict(email)
        assert isinstance(result, Err), f"Should fail for {email}"

def test_domain_validation():
    result = validate_corporate_email(
        "user@company.com",
        ["company.com", "subsidiary.com"]
    )
    assert isinstance(result, Ok)

    result = validate_corporate_email(
        "user@gmail.com",
        ["company.com"]
    )
    assert isinstance(result, Err)
```

---

## See Also

- [Non-Empty Strings](non-empty-strings.md) - Basic string validation
- [Custom Validators](custom-validators.md) - Build your own validators
- [FastAPI Endpoints](../framework-integration/fastapi-endpoints.md) - API validation

---

**Difficulty:** Beginner
**Time:** 10 minutes
**Category:** Validation
**Last Updated:** 2025-10-15
