# How-To: Use Pattern Matching

**Master pattern matching for destructuring, guards, and type-safe code with Option/Result.**

---

## Overview

**What you'll learn:**
- Pattern match with `is` operator
- Destructure enum variants to extract values
- Use guards for additional conditions
- Work with Option and Result types
- Write expressive, type-safe code

**Time:** 30 minutes
**Difficulty:** Advanced
**Prerequisites:** [Handle Complex Types](complex-types.md)

---

## The Problem

Handling optional values and variants often requires verbose if-else chains:

```promptware
function get_user_name(user: Option<User>) -> String
  do
    if user != None:
      # How do I extract the User from Option<User>?
      # Nested property access is messy
      ...
    else:
      return "Anonymous"
    end
  end
end
```

Problems:
- No way to extract values from variants
- Verbose null checks
- Error-prone nested conditionals
- Missing exhaustiveness checking

---

## The Solution

Pattern matching with the `is` operator:

```promptware
function get_user_name(user: Option<User>) -> String
  do
    if user is Some(u):
      return u.name  # u is extracted User
    else:
      return "Anonymous"
    end
  end
end
```

**Benefits:**
- Extract values inline
- Type-safe destructuring
- Readable code
- Works with all enum types (Option, Result, custom enums)

---

## Step 1: Basic Pattern Matching

### Pattern Matching Syntax

```promptware
if <value> is <pattern>:
  # pattern matched
else:
  # pattern didn't match
end
```

### Match Simple Variants

```promptware
enum Status:
  Active
  Inactive
  Pending
end

function describe_status(status: Status) -> String
  do
    if status is Active:
      return "User is active"
    else if status is Inactive:
      return "User is inactive"
    else:
      return "Status pending"
    end
  end
end
```

### Match with Option

```promptware
function describe_option(opt: Option<Int>) -> String
  do
    if opt is Some(value):
      # 'value' is extracted from Some(value)
      return "Got: " + String(value)
    else:
      return "Got nothing"
    end
  end
end
```

---

## Step 2: Destructuring Values

### Extract Values from Variants

```promptware
enum Result<T, E>:
  Ok(value: T)
  Err(error: E)
end

function handle_result(res: Result<Int, String>) -> String
  do
    if res is Ok(val):
      # val is the Int inside Ok
      return "Success: " + String(val)
    else if res is Err(msg):
      # msg is the String inside Err
      return "Error: " + msg
    end

    return "Unknown"
  end
end
```

### Wildcard Pattern (Ignore Value)

```promptware
function is_some(opt: Option<Int>) -> Bool
  do
    if opt is Some(_):
      # We don't need the value, just check if it's Some
      return true
    else:
      return false
    end
  end
end
```

---

## Step 3: Working with Option<T>

### Unwrap with Pattern Matching

```promptware
function unwrap_or_default(opt: Option<Int>, default: Int) -> Int
  do
    if opt is Some(val):
      return val
    else:
      return default
    end
  end
end
```

### Chain Operations

```promptware
function process_optional(opt: Option<Int>) -> Option<Int>
  do
    if opt is Some(val):
      if val > 0:
        return Some(val * 2)
      else:
        return None
      end
    else:
      return None
    end
  end
end
```

### Nested Options

```promptware
function flatten_option(nested: Option<Option<Int>>) -> Option<Int>
  do
    if nested is Some(inner):
      # inner is Option<Int>
      if inner is Some(value):
        return Some(value)
      else:
        return None
      end
    else:
      return None
    end
  end
end
```

---

## Step 4: Working with Result<T, E>

### Error Handling

```promptware
function divide(a: Int, b: Int) -> Result<Int, String>
  do
    if b == 0:
      return Err("Division by zero")
    else:
      return Ok(a / b)
    end
  end
end

function safe_divide(a: Int, b: Int) -> String
  do
    let result = divide(a, b)

    if result is Ok(value):
      return "Result: " + String(value)
    else if result is Err(error):
      return "Error: " + error
    end

    return "Unknown"
  end
end
```

### Propagate Errors

```promptware
function compute(x: Int, y: Int) -> Result<Int, String>
  do
    let result1 = divide(x, y)
    if result1 is Err(e):
      return Err(e)  # Propagate error
    end

    if result1 is Ok(val1):
      let result2 = divide(val1, 2)
      if result2 is Err(e):
        return Err(e)  # Propagate error
      end

      if result2 is Ok(val2):
        return Ok(val2)
      end
    end

    return Err("Unexpected error")
  end
end
```

---

## Step 5: Guards (Additional Conditions)

### Pattern Matching with Guards

```promptware
function classify_number(opt: Option<Int>) -> String
  do
    if opt is Some(val):
      # Guard: additional condition after pattern match
      if val > 0:
        return "Positive"
      else if val < 0:
        return "Negative"
      else:
        return "Zero"
      end
    else:
      return "No value"
    end
  end
end
```

### Multiple Guards

```promptware
function validate_age(opt: Option<Int>) -> Result<Int, String>
  do
    if opt is Some(age):
      if age < 0:
        return Err("Age cannot be negative")
      else if age > 150:
        return Err("Age too high")
      else if age < 18:
        return Err("Must be 18 or older")
      else:
        return Ok(age)
      end
    else:
      return Err("Age not provided")
    end
  end
end
```

---

## Step 6: Custom Enum Patterns

### Define Custom Enums

```promptware
enum HttpResponse:
  Success(code: Int, body: String)
  Redirect(location: String)
  ClientError(code: Int, message: String)
  ServerError(code: Int, message: String)
end
```

### Pattern Match Custom Enums

```promptware
function handle_response(response: HttpResponse) -> String
  do
    if response is Success(code, body):
      return "Success " + String(code) + ": " + body
    else if response is Redirect(loc):
      return "Redirect to: " + loc
    else if response is ClientError(code, msg):
      return "Client error " + String(code) + ": " + msg
    else if response is ServerError(code, msg):
      return "Server error " + String(code) + ": " + msg
    end

    return "Unknown response"
  end
end
```

### Nested Pattern Matching

```promptware
enum ApiResult:
  Success(data: Option<String>)
  Failure(error: String)
end

function process_api_result(result: ApiResult) -> String
  do
    if result is Success(data):
      # data is Option<String>
      if data is Some(content):
        return "Got data: " + content
      else:
        return "Success but no data"
      end
    else if result is Failure(err):
      return "API failed: " + err
    end

    return "Unknown result"
  end
end
```

---

## Step 7: Real-World Example - Order Processing

### Order State Machine with Pattern Matching

```promptware
enum OrderStatus:
  Draft(items: List<String>)
  Pending(order_id: String, items: List<String>)
  Confirmed(order_id: String, total: Float)
  Shipped(order_id: String, tracking: String)
  Delivered(order_id: String)
  Cancelled(reason: String)
end

function describe_order(status: OrderStatus) -> String
  do
    if status is Draft(items):
      return "Draft with " + String(len(items)) + " items"

    else if status is Pending(id, items):
      return "Order " + id + " pending (" + String(len(items)) + " items)"

    else if status is Confirmed(id, total):
      return "Order " + id + " confirmed: $" + String(total)

    else if status is Shipped(id, tracking):
      return "Order " + id + " shipped, tracking: " + tracking

    else if status is Delivered(id):
      return "Order " + id + " delivered"

    else if status is Cancelled(reason):
      return "Order cancelled: " + reason
    end

    return "Unknown status"
  end
end
```

### Validate State Transitions

```promptware
function can_ship(status: OrderStatus) -> Result<String, String>
  do
    if status is Confirmed(order_id, total):
      if total > 0.0:
        return Ok(order_id)
      else:
        return Err("Cannot ship order with zero total")
      end
    else if status is Cancelled(reason):
      return Err("Cannot ship cancelled order: " + reason)
    else:
      return Err("Order must be confirmed before shipping")
    end
  end
end
```

---

## Step 8: Pattern Matching Best Practices

### 1. Handle All Cases

```promptware
# Good: Handles all cases
function handle_option(opt: Option<Int>) -> String
  do
    if opt is Some(val):
      return String(val)
    else:
      return "None"  # Covers the None case
    end
  end
end

# Bad: Missing None case
function handle_option_bad(opt: Option<Int>) -> String
  do
    if opt is Some(val):
      return String(val)
    end
    # What if opt is None? No return!
  end
end
```

### 2. Use Wildcards for Ignored Values

```promptware
# Good: Explicit wildcard
function is_ok(res: Result<Int, String>) -> Bool
  do
    if res is Ok(_):
      return true
    else:
      return false
    end
  end
end

# Okay but less clear
function is_ok_verbose(res: Result<Int, String>) -> Bool
  do
    if res is Ok(val):
      # val is declared but never used
      return true
    else:
      return false
    end
  end
end
```

### 3. Extract Early, Return Early

```promptware
# Good: Extract and return early
function get_user_email(user: Option<User>) -> String
  do
    if user is Some(u):
      return u.email
    else:
      return "no-email@example.com"
    end
  end
end

# Verbose alternative
function get_user_email_verbose(user: Option<User>) -> String
  do
    let email = ""

    if user is Some(u):
      email = u.email
    else:
      email = "no-email@example.com"
    end

    return email
  end
end
```

### 4. Use Guards for Complex Conditions

```promptware
# Good: Guards make complex conditions readable
function classify_result(res: Result<Int, String>) -> String
  do
    if res is Ok(val):
      if val > 100:
        return "Large success"
      else if val > 0:
        return "Small success"
      else:
        return "Zero or negative success"
      end
    else if res is Err(msg):
      if "timeout" in msg:
        return "Timeout error"
      else:
        return "Other error"
      end
    end

    return "Unknown"
  end
end
```

---

## Step 9: Generated Code Examples

### Python Generation

**AssertLang:**
```promptware
function unwrap_option(opt: Option<Int>) -> Int
  do
    if opt is Some(val):
      return val
    else:
      return 0
    end
  end
end
```

**Generated Python:**
```python
def unwrap_option(opt: Option[int]) -> int:
    if isinstance(opt, Some):
        val = opt.value
        return val
    else:
        return 0
```

### JavaScript Generation

**Generated JavaScript:**
```javascript
function unwrapOption(opt) {
    if (opt instanceof Some) {
        const val = opt.value;
        return val;
    } else {
        return 0;
    }
}
```

---

## Comparison: Pattern Matching vs. Methods

### Using Pattern Matching

```promptware
function get_value_or_zero(opt: Option<Int>) -> Int
  do
    if opt is Some(val):
      return val
    else:
      return 0
    end
  end
end
```

### Using Option Methods

```promptware
function get_value_or_zero_method(opt: Option<Int>) -> Int
  do
    return option_unwrap_or(opt, 0)
  end
end
```

**When to use each:**
- **Pattern matching** - When you need custom logic per variant
- **Methods** - When stdlib methods (map, unwrap_or, etc.) fit your use case

---

## Common Patterns

### Safe Array Access

```promptware
function safe_get(items: List<String>, index: Int) -> Option<String>
  do
    if index >= 0 and index < len(items):
      return Some(items[index])
    else:
      return None
    end
  end
end

function get_first(items: List<String>) -> String
  do
    let first = safe_get(items, 0)

    if first is Some(item):
      return item
    else:
      return "Empty list"
    end
  end
end
```

### Chaining Computations

```promptware
function parse_int(s: String) -> Option<Int>
  # Parses string to int (simplified)
  do
    if len(s) > 0:
      return Some(42)  # Placeholder
    else:
      return None
    end
  end
end

function double_parsed(s: String) -> Option<Int>
  do
    let parsed = parse_int(s)

    if parsed is Some(val):
      return Some(val * 2)
    else:
      return None
    end
  end
end
```

### Error Recovery

```promptware
function divide_with_fallback(a: Int, b: Int, fallback: Int) -> Int
  do
    let result = divide(a, b)

    if result is Ok(val):
      return val
    else if result is Err(_):
      # Ignore error message, return fallback
      return fallback
    end

    return 0
  end
end
```

---

## Testing Pattern Matching

### Test All Branches

```python
# Python (pytest)
from mymodule import handle_result, Ok, Err

def test_handle_result_ok():
    result = Ok(value=42)
    assert handle_result(result) == "Success: 42"

def test_handle_result_err():
    result = Err(error="timeout")
    assert handle_result(result) == "Error: timeout"

def test_handle_result_guards():
    # Test with different values to exercise guards
    assert handle_result(Ok(value=0)) == "Success: 0"
    assert handle_result(Ok(value=-10)) == "Success: -10"
```

---

## Summary

**Pattern matching with `is`:**
- Matches enum variants
- Extracts values inline
- Enables guards for complex conditions
- Works with Option, Result, custom enums

**Syntax:**
```promptware
if value is Variant(extracted_value):
  # use extracted_value
else:
  # handle other cases
end
```

**Key patterns:**
- Use wildcards `_` for ignored values
- Extract early, return early
- Handle all cases (exhaustiveness)
- Combine with guards for complex logic

---

## Next Steps

- **[Handle Complex Types](complex-types.md)** - Deep dive into Option/Result
- **[Build a State Machine](state-machine.md)** - Use pattern matching for state transitions
- **[Optimize Performance](performance.md)** - Inline pattern matches for speed

---

## See Also

- **[API Reference: Pattern Matching](../../reference/contract-syntax.md#pattern-matching)** - Full syntax reference
- **[Stdlib: Option](../../reference/contract-syntax.md#option)** - Option type reference
- **[Stdlib: Result](../../reference/contract-syntax.md#result)** - Result type reference

---

**Difficulty:** Advanced
**Time:** 30 minutes
**Last Updated:** 2025-10-15
