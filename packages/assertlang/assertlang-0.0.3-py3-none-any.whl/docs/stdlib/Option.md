# Option<T> API Reference

**Package**: `stdlib.core`
**Version**: v0.1.0-alpha
**Status**: BLOCKED - Awaiting parser generic support

---

## Overview

`Option<T>` represents an optional value - either `Some(value)` containing a value of type `T`, or `None` representing no value. This type eliminates null pointer exceptions by making optional values explicit in the type system.

## Motivation

**Problem**: In many languages, `null` or `undefined` can appear anywhere, leading to runtime errors:

```python
# Python - can throw AttributeError
user = find_user(user_id)
name = user.name  # ❌ Crashes if user is None
```

**Solution**: `Option<T>` makes optionality explicit and forces you to handle both cases:

```pw
# AssertLang - compiler enforces handling
let user_opt = find_user(user_id)  // Returns Option<User>
let name = option_match(
    user_opt,
    fn(user) -> user.name,  // ✅ Only called if user exists
    fn() -> "Unknown"       // ✅ Fallback if no user
)
```

---

## Type Definition

```pw
enum Option<T>:
    - Some(value: T)   // Contains a value of type T
    - None             // Contains no value
```

### Variants

| Variant | Description | Example |
|---------|-------------|---------|
| `Some(value)` | Contains a value | `option_some(42)` → `Some(42)` |
| `None` | Contains no value | `option_none()` → `None` |

---

## Constructors

### option_some

```pw
function option_some<T>(value: T) -> Option<T>
```

Create an `Option` containing a value.

**Parameters:**
- `value: T` - The value to wrap

**Returns:**
- `Option<T>` - `Some(value)`

**Example:**
```pw
let num = option_some(42)        // Some(42)
let text = option_some("hello")  // Some("hello")
let user = option_some(User{name: "Alice", age: 30})  // Some(User{...})
```

---

### option_none

```pw
function option_none<T>() -> Option<T>
```

Create an empty `Option`.

**Parameters:** None

**Returns:**
- `Option<T>` - `None`

**Example:**
```pw
let nothing = option_none()  // None
```

---

## Transformation Methods

### option_map

```pw
function option_map<T, U>(opt: Option<T>, fn: function(T) -> U) -> Option<U>
```

Transform the value inside `Some` by applying a function. If `opt` is `None`, returns `None` without calling `fn`.

**Parameters:**
- `opt: Option<T>` - The Option to map over
- `fn: function(T) -> U` - Function to apply to the value

**Returns:**
- `Option<U>` - `Some(fn(value))` if `opt` is `Some(value)`, otherwise `None`

**Example:**
```pw
let num = option_some(5)
let doubled = option_map(num, fn(x) -> x * 2)
// doubled is Some(10)

let empty = option_none()
let result = option_map(empty, fn(x) -> x * 2)
// result is None (function not called)
```

**Use Cases:**
- Converting types: `option_map(age_opt, fn(age) -> str(age))`
- Applying transformations: `option_map(price_opt, fn(p) -> p * 1.1)`  // Add 10% tax
- Extracting fields: `option_map(user_opt, fn(u) -> u.email)`

---

### option_and_then

```pw
function option_and_then<T, U>(opt: Option<T>, fn: function(T) -> Option<U>) -> Option<U>
```

Chain operations that return `Option` (also known as flatMap). Returns `None` if either the input is `None` or the function returns `None`.

**Parameters:**
- `opt: Option<T>` - The Option to chain from
- `fn: function(T) -> Option<U>` - Function that returns an Option

**Returns:**
- `Option<U>` - The result of `fn` if `opt` is `Some`, otherwise `None`

**Example:**
```pw
function safe_divide(a: int, b: int) -> Option<int>:
    if b == 0:
        return option_none()
    else:
        return option_some(a / b)

let num = option_some(10)
let result = option_and_then(num, fn(x) -> safe_divide(x, 2))
// result is Some(5)

let bad = option_and_then(num, fn(x) -> safe_divide(x, 0))
// bad is None (function returned None)
```

**Use Cases:**
- Validation chains: `option_and_then(input, validate_email)`
- Dependent lookups: `option_and_then(user_id_opt, find_user)`
- Parsing sequences: `option_and_then(json_opt, parse_config)`

**Difference from `map`:**
- `map`: Transform value, wraps result in `Some`
- `and_then`: Function already returns `Option`, no double-wrapping

---

## Unwrapping Methods

### option_unwrap_or

```pw
function option_unwrap_or<T>(opt: Option<T>, default: T) -> T
```

Extract the value from `Some`, or return a default if `None`.

**Parameters:**
- `opt: Option<T>` - The Option to unwrap
- `default: T` - Value to return if `opt` is `None`

**Returns:**
- `T` - The value from `Some`, or `default`

**Example:**
```pw
let num = option_some(42)
let value = option_unwrap_or(num, 0)  // 42

let empty = option_none()
let value2 = option_unwrap_or(empty, 0)  // 0
```

**Use Cases:**
- Config with defaults: `let port = option_unwrap_or(config_port, 8080)`
- Fallback values: `let timeout = option_unwrap_or(custom_timeout, 30)`

---

### option_unwrap_or_else

```pw
function option_unwrap_or_else<T>(opt: Option<T>, fn: function() -> T) -> T
```

Extract the value from `Some`, or compute a default lazily. The function `fn` is only called if `opt` is `None`.

**Parameters:**
- `opt: Option<T>` - The Option to unwrap
- `fn: function() -> T` - Function to compute default value

**Returns:**
- `T` - The value from `Some`, or the result of `fn()`

**Example:**
```pw
let num = option_some(42)
let value = option_unwrap_or_else(num, fn() -> expensive_computation())
// value is 42 (function not called)

let empty = option_none()
let value2 = option_unwrap_or_else(empty, fn() -> expensive_computation())
// value2 is result of expensive_computation() (function called once)
```

**When to use instead of `unwrap_or`:**
- Default is expensive to compute
- Default requires I/O or network access
- You want to avoid unnecessary work

---

## Predicate Methods

### option_is_some

```pw
function option_is_some<T>(opt: Option<T>) -> bool
```

Check if the `Option` contains a value.

**Parameters:**
- `opt: Option<T>` - The Option to check

**Returns:**
- `bool` - `true` if `Some`, `false` if `None`

**Example:**
```pw
let num = option_some(42)
let has_value = option_is_some(num)  // true

let empty = option_none()
let has_value2 = option_is_some(empty)  // false
```

---

### option_is_none

```pw
function option_is_none<T>(opt: Option<T>) -> bool
```

Check if the `Option` is empty.

**Parameters:**
- `opt: Option<T>` - The Option to check

**Returns:**
- `bool` - `true` if `None`, `false` if `Some`

**Example:**
```pw
let num = option_some(42)
let is_empty = option_is_none(num)  // false

let empty = option_none()
let is_empty2 = option_is_none(empty)  // true
```

---

## Pattern Matching

### option_match

```pw
function option_match<T, U>(
    opt: Option<T>,
    some_fn: function(T) -> U,
    none_fn: function() -> U
) -> U
```

Pattern match on `Option`, calling the appropriate function based on the variant.

**Parameters:**
- `opt: Option<T>` - The Option to match
- `some_fn: function(T) -> U` - Function to call if `Some` (receives the value)
- `none_fn: function() -> U` - Function to call if `None`

**Returns:**
- `U` - The result of the called function

**Example:**
```pw
let num = option_some(42)
let message = option_match(
    num,
    fn(x) -> "Got: " + str(x),
    fn() -> "Got nothing"
)
// message is "Got: 42"

let empty = option_none()
let message2 = option_match(
    empty,
    fn(x) -> "Got: " + str(x),
    fn() -> "Got nothing"
)
// message2 is "Got nothing"
```

**Use Cases:**
- Converting to different types based on presence
- Logging or side effects
- Complex branching logic

---

## Common Patterns

### Chaining Operations

```pw
// Start with Option
let user_id = option_some(42)

// Chain transformations
let user_name = option_unwrap_or(
    option_map(
        option_and_then(user_id, find_user),
        fn(user) -> user.name
    ),
    "Unknown"
)
```

### Early Return Simulation

```pw
function process_user(user_id_opt: Option<int>) -> string:
    // Extract or return early
    let user_id = option_unwrap_or(user_id_opt, -1)
    if user_id == -1:
        return "No user ID provided"

    // Continue processing...
    let user = find_user(user_id)
    return option_match(
        user,
        fn(u) -> "Hello, " + u.name,
        fn() -> "User not found"
    )
```

### Filtering with Options

```pw
// Get all users who have ages
let users_with_ages = []
for user in all_users:
    if option_is_some(user.age):
        let age_value = option_unwrap_or(user.age, 0)
        users_with_ages.append({name: user.name, age: age_value})
```

---

## Anti-Patterns

### ❌ DON'T: Use null instead of Option

```pw
// Bad - defeats the purpose
function find_user(id: int) -> User?:
    if id < 0:
        return null  // ❌ Still allows null
    return User{id: id}
```

```pw
// Good - use Option
function find_user(id: int) -> Option<User>:
    if id < 0:
        return option_none()  // ✅ Explicit
    return option_some(User{id: id})
```

### ❌ DON'T: Unwrap without checking (if unwrap existed)

```pw
// Bad - would panic on None
let value = opt.unwrap()  // ❌ DON'T DO THIS (not even available)
```

```pw
// Good - always handle both cases
let value = option_unwrap_or(opt, default_value)  // ✅ Safe
let value2 = option_match(opt, some_fn, none_fn)  // ✅ Explicit
```

### ❌ DON'T: Excessive nesting

```pw
// Bad - hard to read
let result = option_map(
    option_and_then(
        option_map(opt1, fn1),
        fn2
    ),
    fn3
)
```

```pw
// Good - intermediate variables
let step1 = option_map(opt1, fn1)
let step2 = option_and_then(step1, fn2)
let result = option_map(step2, fn3)
```

---

## Cross-Language Mapping

| PW | Python | Rust | Go | TypeScript | C# |
|----|--------|------|----|-----------|----|
| `Option<T>` | `Optional[T]` | `Option<T>` | `*T` | `T \| null` | `T?` |
| `Some(42)` | `Some(42)` | `Some(42)` | `&value` | `42` | `42` |
| `None` | `None` | `None` | `nil` | `null` | `null` |

---

## Performance Considerations

- **Zero-cost abstraction**: When targeting Rust, compiles to native `Option<T>`
- **No runtime overhead**: Pattern matching compiles to efficient branches
- **Memory**: Single pointer overhead compared to nullable references

---

## See Also

- [Result<T,E>](./Result.md) - For operations that can fail with typed errors
- [stdlib README](./README.md) - Overview of the standard library
- [PW_NATIVE_SYNTAX.md](../PW_NATIVE_SYNTAX.md) - Language syntax reference

---

**Last Updated**: 2025-10-12
**Status**: API specification complete, awaiting parser generic support
