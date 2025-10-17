# Recipe: Non-Empty String Validation

**Problem:** Prevent empty or whitespace-only strings from entering your functions.

**Difficulty:** Beginner
**Time:** 5 minutes

---

## The Problem

Functions that process text often assume non-empty input. Empty strings cause:
- Division by zero errors (string length calculations)
- Index out of bounds (accessing first character)
- Silent failures (processing nothing)
- Poor user experience (unhelpful error messages)

---

## Solution

```al
function process_text(text: string) -> string {
    @requires non_empty: len(text) > 0
    @requires not_whitespace: len(text.strip()) > 0

    @ensures result_not_empty: len(result) > 0

    let processed = text.strip().upper();
    return processed;
}
```

**Generated Python:**
```python
from promptware.runtime.contracts import check_precondition, check_postcondition

def process_text(text: str) -> str:
    # Preconditions
    check_precondition(len(text) > 0, "non_empty",
        f"Expected non-empty string, got length {len(text)}")
    check_precondition(len(text.strip()) > 0, "not_whitespace",
        f"Expected non-whitespace string")

    # Your logic
    processed = text.strip().upper()

    # Postconditions
    check_postcondition(len(processed) > 0, "result_not_empty",
        f"Result should be non-empty, got length {len(processed)}")

    return processed
```

---

## Explanation

**Two-level check**:
1. `len(text) > 0` - Rejects empty strings (`""`)
2. `len(text.strip()) > 0` - Rejects whitespace-only (`"   "`)

**Why both?** Empty strings fail fast, whitespace-only strings show intent.

**Postcondition** ensures processing didn't produce empty output.

---

## Variations

### Minimum Length
```al
@requires min_length: len(text) >= 3
// Requires at least 3 characters
```

### Maximum Length
```al
@requires max_length: len(text) <= 280
// Twitter-style character limit
```

### Combined Min/Max
```al
@requires valid_length: len(text) >= 3 && len(text) <= 280
// Between 3 and 280 characters
```

### Pattern Matching
```al
@requires valid_format: text.matches("^[A-Za-z0-9]+$")
// Alphanumeric only
```

---

## Common Pitfalls

### ❌ Only checking `len(text) > 0`
```al
@requires non_empty: len(text) > 0
// Allows "   " (whitespace-only)
```

**Problem**: Whitespace-only strings pass, cause issues downstream.

**Fix**: Add `len(text.strip()) > 0`

---

### ❌ Stripping in precondition
```al
@requires non_empty: len(text.strip()) > 0
let processed = text.strip()  // Strips again!
```

**Problem**: Stripping twice (inefficient).

**Fix**: Check non-whitespace, strip once in function body.

---

### ❌ No postcondition
```al
function process_text(text: string) -> string {
    @requires non_empty: len(text) > 0
    // No postcondition!

    let result = "";  // Bug: returns empty!
    return result;
}
```

**Problem**: Function could return empty despite non-empty input.

**Fix**: Add `@ensures result_not_empty: len(result) > 0`

---

## Real-World Example

**User registration validation:**
```al
function validate_username(username: string) -> bool {
    @requires non_empty: len(username) > 0
    @requires not_whitespace: len(username.strip()) > 0
    @requires min_length: len(username) >= 3
    @requires max_length: len(username) <= 20
    @requires alphanumeric: username.matches("^[A-Za-z0-9_]+$")

    @ensures valid_result: result == true

    // All validation done by contracts
    return true;
}
```

**Usage:**
```python
from user_validation import validate_username

# ✓ Valid
validate_username("alice123")  # True

# ❌ Invalid (caught by contracts)
validate_username("")          # Contract: non_empty failed
validate_username("  ")        # Contract: not_whitespace failed
validate_username("ab")        # Contract: min_length failed
validate_username("a" * 30)    # Contract: max_length failed
validate_username("alice!")    # Contract: alphanumeric failed
```

---

## See Also

- **[Positive Numbers](positive-numbers.md)** - Similar pattern for numeric validation
- **[Email Validation](email-validation.md)** - Pattern matching for emails
- **[Custom Validators](custom-validators.md)** - Build reusable validators
- **[Multi-Field Constraints](multi-field-constraints.md)** - Validate related fields

---

**Next**: Try [Positive Numbers](positive-numbers.md) for numeric validation →
