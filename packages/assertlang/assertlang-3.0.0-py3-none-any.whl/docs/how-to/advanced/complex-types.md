# How-To: Handle Complex Types

**Master Option<T>, Result<T, E>, generics, and advanced type patterns for robust code.**

---

## Overview

**What you'll learn:**
- Use Option<T> for null safety
- Handle errors with Result<T, E>
- Work with generic type parameters
- Chain operations for elegant code
- Build custom generic types

**Time:** 40 minutes
**Difficulty:** Advanced
**Prerequisites:** [Use Pattern Matching](pattern-matching.md)

---

## The Problem

Traditional null/error handling is error-prone:

```python
# Python: Null checks everywhere
def get_user_email(user_id):
    user = find_user(user_id)  # Returns None if not found
    if user is None:
        return "no-email@example.com"
    if user.email is None:
        return "no-email@example.com"
    return user.email

# What if we forget a null check? NullPointerException!
```

**Problems:**
- Easy to forget null checks
- No compile-time guarantees
- Error handling with exceptions is implicit
- Type system doesn't help

---

## The Solution

Use explicit types that encode optionality and errors:

```promptware
function get_user_email(user_id: Int) -> String
  do
    let user = find_user(user_id)  # Returns Option<User>

    if user is Some(u):
      if u.email is Some(email):
        return email
      else:
        return "no-email@example.com"
      end
    else:
      return "no-email@example.com"
    end
  end
end
```

**Benefits:**
- Null safety enforced by type system
- Explicit error handling
- Chainable operations
- Works across all languages (Python, JS, Rust, Go)

---

## Step 1: Option<T> Basics

### What is Option<T>?

Option represents a value that might or might not exist:

```promptware
enum Option<T>:
  Some(value: T)  # Has a value
  None            # No value
end
```

**Use cases:**
- Functions that might not find a result (search, lookup)
- Optional configuration values
- Nullable fields

### Creating Options

```promptware
# Using constructors
let some_value = Some(42)           # Option<Int> with value
let no_value = None                 # Option<Int> without value

# Using stdlib functions
let val1 = option_some(42)          # Some(42)
let val2 = option_none()            # None
```

### Pattern Matching on Option

```promptware
function describe(opt: Option<Int>) -> String
  do
    if opt is Some(value):
      return "Got: " + String(value)
    else:
      return "Got nothing"
    end
  end
end
```

---

## Step 2: Option<T> Methods

### map - Transform Values

```promptware
# Apply function to value inside Some, or pass through None
let num = Some(5)
let doubled = option_map(num, fn(x) -> x * 2)  # Some(10)

let empty = None
let result = option_map(empty, fn(x) -> x * 2)  # None
```

**Signature:**
```promptware
function option_map<T, U>(opt: Option<T>, fn: function(T) -> U) -> Option<U>
```

### and_then - Chain Operations (flatMap)

```promptware
function safe_divide(a: Int, b: Int) -> Option<Int>
  do
    if b == 0:
      return None
    else:
      return Some(a / b)
    end
  end
end

let num = Some(10)
let result = option_and_then(num, fn(x) -> safe_divide(x, 2))  # Some(5)
let bad = option_and_then(num, fn(x) -> safe_divide(x, 0))     # None
```

**Signature:**
```promptware
function option_and_then<T, U>(
    opt: Option<T>,
    fn: function(T) -> Option<U>
) -> Option<U>
```

### unwrap_or - Provide Default

```promptware
let num = Some(42)
let value = option_unwrap_or(num, 0)  # 42

let empty = None
let value2 = option_unwrap_or(empty, 0)  # 0
```

### unwrap_or_else - Lazy Default

```promptware
# Function is only called if None
let num = Some(42)
let value = option_unwrap_or_else(num, fn() -> expensive_default())  # 42, fn not called

let empty = None
let value2 = option_unwrap_or_else(empty, fn() -> expensive_default())  # Calls fn
```

### is_some / is_none - Check Presence

```promptware
let num = Some(42)
let has_value = option_is_some(num)  # true
let is_empty = option_is_none(num)   # false

let empty = None
let has_value2 = option_is_some(empty)  # false
let is_empty2 = option_is_none(empty)   # true
```

### match - Pattern Match with Functions

```promptware
let num = Some(42)
let msg = option_match(
    num,
    fn(x) -> "Got: " + String(x),  # Called if Some
    fn() -> "Got nothing"           # Called if None
)  # "Got: 42"
```

---

## Step 3: Result<T, E> Basics

### What is Result<T, E>?

Result represents success or failure with typed errors:

```promptware
enum Result<T, E>:
  Ok(value: T)    # Success with value
  Err(error: E)   # Failure with error
end
```

**Use cases:**
- Operations that can fail (parsing, file I/O, network requests)
- Validation with typed errors
- Error propagation without exceptions

### Creating Results

```promptware
# Using constructors
let success = Ok(42)                # Result<Int, String>
let failure = Err("failed")         # Result<Int, String>

# Using stdlib functions
let val1 = result_ok(42)            # Ok(42)
let val2 = result_err("error")      # Err("error")
```

### Pattern Matching on Result

```promptware
function handle_result(res: Result<Int, String>) -> String
  do
    if res is Ok(value):
      return "Success: " + String(value)
    else if res is Err(error):
      return "Error: " + error
    end

    return "Unknown"
  end
end
```

---

## Step 4: Result<T, E> Methods

### map - Transform Success Value

```promptware
let success = Ok(5)
let doubled = result_map(success, fn(x) -> x * 2)  # Ok(10)

let failure = Err("error")
let result = result_map(failure, fn(x) -> x * 2)   # Err("error")
```

### map_err - Transform Error

```promptware
let success = Ok(42)
let result = result_map_err(success, fn(e) -> "Error: " + e)  # Ok(42)

let failure = Err("bad")
let mapped = result_map_err(failure, fn(e) -> "Error: " + e)  # Err("Error: bad")
```

### and_then - Chain Failable Operations

```promptware
function safe_divide(a: Int, b: Int) -> Result<Int, String>
  do
    if b == 0:
      return Err("division by zero")
    else:
      return Ok(a / b)
    end
  end
end

let num = Ok(10)
let result = result_and_then(num, fn(x) -> safe_divide(x, 2))  # Ok(5)
let bad = result_and_then(num, fn(x) -> safe_divide(x, 0))     # Err("division by zero")
```

### unwrap_or - Extract or Default

```promptware
let success = Ok(42)
let value = result_unwrap_or(success, 0)  # 42

let failure = Err("error")
let value2 = result_unwrap_or(failure, 0)  # 0
```

### is_ok / is_err - Check Result

```promptware
let success = Ok(42)
let is_success = result_is_ok(success)  # true
let is_error = result_is_err(success)   # false

let failure = Err("error")
let is_success2 = result_is_ok(failure)  # false
let is_error2 = result_is_err(failure)   # true
```

### match - Pattern Match with Functions

```promptware
let success = Ok(42)
let msg = result_match(
    success,
    fn(x) -> "Success: " + String(x),  # Called if Ok
    fn(e) -> "Error: " + e              # Called if Err
)  # "Success: 42"
```

---

## Step 5: Generic Type Parameters

### Defining Generic Functions

```promptware
function identity<T>(value: T) -> T
  do
    return value
  end
end

# Works with any type
let num = identity(42)        # T = Int
let text = identity("hello")  # T = String
```

### Multiple Type Parameters

```promptware
function pair<A, B>(first: A, second: B) -> List<Any>
  do
    return [first, second]
  end
end

let result = pair(42, "hello")  # A = Int, B = String
```

### Constrained Generics

```promptware
function max<T>(a: T, b: T) -> T
  requires:
    a == a  # T must support equality
  do
    if a > b:
      return a
    else:
      return b
    end
  end
end
```

---

## Step 6: Nested Types

### Option<Option<T>>

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

### List<Option<T>>

```promptware
function filter_some(items: List<Option<Int>>) -> List<Int>
  do
    let result = []
    for item in items:
      if item is Some(val):
        result = result + [val]
      end
    end
    return result
  end
end

# Usage
let items = [Some(1), None, Some(3), None, Some(5)]
let filtered = filter_some(items)  # [1, 3, 5]
```

### Result<Option<T>, E>

```promptware
function parse_optional_int(s: String) -> Result<Option<Int>, String>
  do
    if len(s) == 0:
      return Ok(None)  # Empty string is valid, no value
    else if s == "invalid":
      return Err("Parse error")  # Invalid input
    else:
      return Ok(Some(42))  # Simplified parsing
    end
  end
end
```

---

## Step 7: Real-World Patterns

### Safe Parsing

```promptware
function parse_int(s: String) -> Option<Int>
  do
    # Simplified: real implementation would parse string
    if len(s) > 0 and s != "invalid":
      return Some(42)  # Placeholder
    else:
      return None
    end
  end
end

function parse_and_double(s: String) -> Option<Int>
  do
    let parsed = parse_int(s)
    return option_map(parsed, fn(x) -> x * 2)
  end
end
```

### Chaining Computations

```promptware
function safe_sqrt(x: Float) -> Result<Float, String>
  do
    if x < 0.0:
      return Err("Cannot take sqrt of negative")
    else:
      return Ok(x ** 0.5)  # Square root
    end
  end
end

function safe_log(x: Float) -> Result<Float, String>
  do
    if x <= 0.0:
      return Err("Cannot take log of non-positive")
    else:
      return Ok(x)  # Simplified: would use log function
    end
  end
end

function compute_log_sqrt(x: Float) -> Result<Float, String>
  do
    # Chain: sqrt, then log
    let sqrt_result = safe_sqrt(x)
    return result_and_then(sqrt_result, fn(val) -> safe_log(val))
  end
end
```

### Error Recovery

```promptware
function divide_with_fallback(a: Int, b: Int, fallback: Int) -> Int
  do
    let result = safe_divide(a, b)
    return result_unwrap_or(result, fallback)
  end
end

# Usage
let val1 = divide_with_fallback(10, 2, 0)  # 5
let val2 = divide_with_fallback(10, 0, 99) # 99 (fallback)
```

### Collecting Results

```promptware
function divide_many(nums: List<Int>, divisor: Int) -> List<Result<Int, String>>
  do
    let results = []
    for num in nums:
      let result = safe_divide(num, divisor)
      results = results + [result]
    end
    return results
  end
end

# Usage
let results = divide_many([10, 20, 30], 2)  # [Ok(5), Ok(10), Ok(15)]
let bad = divide_many([10, 20, 30], 0)      # [Err(...), Err(...), Err(...)]
```

---

## Step 8: Custom Generic Types

### Define Generic Data Structures

```promptware
type Box<T>:
  value: T
end

function box_new<T>(value: T) -> Box<T>
  do
    return Box(value=value)
  end
end

function box_map<T, U>(box: Box<T>, fn: function(T) -> U) -> Box<U>
  do
    return Box(value=fn(box.value))
  end
end
```

### Generic Containers

```promptware
type Container<T>:
  items: List<T>
  count: Int
end

function container_new<T>() -> Container<T>
  do
    return Container(items=[], count=0)
  end
end

function container_add<T>(c: Container<T>, item: T) -> Container<T>
  do
    return Container(
      items=c.items + [item],
      count=c.count + 1
    )
  end
end

function container_map<T, U>(
    c: Container<T>,
    fn: function(T) -> U
) -> Container<U>
  do
    let new_items = []
    for item in c.items:
      new_items = new_items + [fn(item)]
    end
    return Container(items=new_items, count=c.count)
  end
end
```

---

## Step 9: Type Inference

### Automatic Type Inference

```promptware
# Type inferred from literal
let num = Some(42)  # Option<Int>
let text = Some("hello")  # Option<String>

# Type inferred from function return
function get_user(id: Int) -> Option<User>:
  # ...
end

let user = get_user(123)  # Type is Option<User>
```

### Explicit Type Annotations

```promptware
# When inference isn't enough
let empty: Option<Int> = None  # Explicit type needed for None

function identity<T>(value: T) -> T:
  do
    return value
  end
end

let result: Option<String> = identity(Some("hello"))
```

---

## Step 10: Performance Considerations

### Avoid Unnecessary Allocations

```promptware
# Good: Direct return
function get_value(opt: Option<Int>) -> Int
  do
    if opt is Some(val):
      return val
    else:
      return 0
    end
  end
end

# Slower: Creates intermediate Option
function get_value_slow(opt: Option<Int>) -> Int
  do
    let mapped = option_map(opt, fn(x) -> x)
    return option_unwrap_or(mapped, 0)
  end
end
```

### Inline Pattern Matching

```promptware
# Fast: Direct pattern match
function process(opt: Option<Int>) -> Int
  do
    if opt is Some(val):
      return val * 2
    else:
      return 0
    end
  end
end

# Slower: Function call overhead
function process_slow(opt: Option<Int>) -> Int
  do
    return option_unwrap_or(option_map(opt, fn(x) -> x * 2), 0)
  end
end
```

---

## Summary

**Option<T>:**
- Represents optional values (Some or None)
- Methods: map, and_then, unwrap_or, is_some, is_none, match
- Use for: nullability, search results, optional fields

**Result<T, E>:**
- Represents success (Ok) or failure (Err) with typed errors
- Methods: map, map_err, and_then, unwrap_or, is_ok, is_err, match
- Use for: error handling, validation, failable operations

**Generic Types:**
- Define functions/types that work with any type: `<T>`
- Multiple parameters: `<T, U>`, `<T, E>`
- Nested types: `Option<Option<T>>`, `List<Result<T, E>>`

**Best Practices:**
- Use Option instead of null checks
- Use Result instead of throwing exceptions
- Chain operations with map/and_then
- Provide defaults with unwrap_or
- Pattern match for control flow

---

## Next Steps

- **[Use Pattern Matching](pattern-matching.md)** - Advanced pattern matching techniques
- **[Build a State Machine](state-machine.md)** - Use Option/Result in state machines
- **[Optimize Performance](performance.md)** - Inline and optimize type operations
- **[Deploy to Production](../../deployment/production.md)** - Disable runtime checks

---

## See Also

- **[Stdlib Reference: Option](../../reference/contract-syntax.md#option)** - Complete Option API
- **[Stdlib Reference: Result](../../reference/contract-syntax.md#result)** - Complete Result API
- **[API Reference: Generics](../../reference/contract-syntax.md#generics)** - Generic type parameters

---

**Difficulty:** Advanced
**Time:** 40 minutes
**Last Updated:** 2025-10-15
