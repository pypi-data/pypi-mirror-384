# Result<T,E> API Reference

**Package**: `stdlib.core`
**Version**: v0.1.0-alpha
**Status**: BLOCKED - Awaiting parser generic support

---

## Overview

`Result<T,E>` represents the result of an operation that can succeed (`Ok(value)`) with a value of type `T`, or fail (`Err(error)`) with an error of type `E`. This type eliminates exceptions by making errors explicit in the type system.

## Motivation

**Problem**: Exceptions can be thrown anywhere, making error handling implicit and easy to forget:

```python
# Python - easy to forget error handling
def divide(a, b):
    return a / b  # ❌ Throws ZeroDivisionError

result = divide(10, 0)  # Crash!
```

**Solution**: `Result<T,E>` makes errors explicit and forces you to handle them:

```pw
# AssertLang - compiler enforces error handling
function divide(a: int, b: int) -> Result<int, string>:
    if b == 0:
        return result_err("division by zero")
    else:
        return result_ok(a / b)

let result = divide(10, 0)
let value = result_unwrap_or(result, 0)  // ✅ Must handle error
```

---

## Type Definition

```pw
enum Result<T, E>:
    - Ok(value: T)      // Success with value of type T
    - Err(error: E)     // Failure with error of type E
```

### Variants

| Variant | Description | Example |
|---------|-------------|---------|
| `Ok(value)` | Operation succeeded | `result_ok(42)` → `Ok(42)` |
| `Err(error)` | Operation failed | `result_err("timeout")` → `Err("timeout")` |

---

## Constructors

### result_ok

```pw
function result_ok<T, E>(value: T) -> Result<T, E>
```

Create a `Result` representing success.

**Parameters:**
- `value: T` - The success value

**Returns:**
- `Result<T, E>` - `Ok(value)`

**Example:**
```pw
let success = result_ok(42)               // Ok(42)
let user = result_ok(User{name: "Alice"}) // Ok(User{...})
```

---

### result_err

```pw
function result_err<T, E>(error: E) -> Result<T, E>
```

Create a `Result` representing failure.

**Parameters:**
- `error: E` - The error value

**Returns:**
- `Result<T, E>` - `Err(error)`

**Example:**
```pw
let failure = result_err("file not found")     // Err("file not found")
let timeout = result_err(ErrorCode.Timeout)    // Err(ErrorCode.Timeout)
```

---

## Transformation Methods

### result_map

```pw
function result_map<T, E, U>(res: Result<T, E>, fn: function(T) -> U) -> Result<U, E>
```

Transform the `Ok` value by applying a function. If `res` is `Err`, returns the error unchanged.

**Parameters:**
- `res: Result<T, E>` - The Result to map over
- `fn: function(T) -> U` - Function to apply to the Ok value

**Returns:**
- `Result<U, E>` - `Ok(fn(value))` if `res` is `Ok(value)`, otherwise the original `Err`

**Example:**
```pw
let success = result_ok(5)
let doubled = result_map(success, fn(x) -> x * 2)
// doubled is Ok(10)

let failure = result_err("error")
let result = result_map(failure, fn(x) -> x * 2)
// result is Err("error") (function not called)
```

**Use Cases:**
- Converting types: `result_map(read_result, fn(text) -> parse_json(text))`
- Applying transformations: `result_map(fetch_result, fn(data) -> data.process())`

---

### result_map_err

```pw
function result_map_err<T, E, F>(res: Result<T, E>, fn: function(E) -> F) -> Result<T, F>
```

Transform the `Err` value by applying a function. If `res` is `Ok`, returns the value unchanged.

**Parameters:**
- `res: Result<T, E>` - The Result to map over
- `fn: function(E) -> F` - Function to apply to the Err value

**Returns:**
- `Result<T, F>` - The original `Ok` if success, otherwise `Err(fn(error))`

**Example:**
```pw
let failure = result_err("timeout")
let enhanced = result_map_err(failure, fn(e) -> "Enhanced: " + e)
// enhanced is Err("Enhanced: timeout")

let success = result_ok(42)
let result = result_map_err(success, fn(e) -> "Enhanced: " + e)
// result is Ok(42) (function not called)
```

**Use Cases:**
- Adding context: `result_map_err(res, fn(e) -> "File error: " + e)`
- Converting error types: `result_map_err(res, fn(e) -> ErrorCode.from_string(e))`

---

### result_and_then

```pw
function result_and_then<T, E, U>(
    res: Result<T, E>,
    fn: function(T) -> Result<U, E>
) -> Result<U, E>
```

Chain operations that return `Result`. Returns the first `Err` encountered (short-circuits).

**Parameters:**
- `res: Result<T, E>` - The Result to chain from
- `fn: function(T) -> Result<U, E>` - Function that returns a Result

**Returns:**
- `Result<U, E>` - The result of `fn` if `res` is `Ok`, otherwise the original `Err`

**Example:**
```pw
function parse_int(s: string) -> Result<int, string>:
    // Simplified - actual impl would parse
    if s == "42":
        return result_ok(42)
    else:
        return result_err("invalid number")

function validate_positive(n: int) -> Result<int, string>:
    if n > 0:
        return result_ok(n)
    else:
        return result_err("must be positive")

let input = result_ok("42")
let result = result_and_then(
    result_and_then(input, parse_int),
    validate_positive
)
// result is Ok(42)

let bad_input = result_ok("-5")
let result2 = result_and_then(
    result_and_then(bad_input, parse_int),
    validate_positive
)
// result2 is Err("must be positive") - chain stops at first error
```

**Use Cases:**
- Multi-step validation
- Sequential fallible operations
- Pipeline processing with error propagation

---

## Unwrapping Methods

### result_unwrap_or

```pw
function result_unwrap_or<T, E>(res: Result<T, E>, default: T) -> T
```

Extract the `Ok` value, or return a default if `Err`.

**Parameters:**
- `res: Result<T, E>` - The Result to unwrap
- `default: T` - Value to return if `res` is `Err`

**Returns:**
- `T` - The value from `Ok`, or `default`

**Example:**
```pw
let success = result_ok(42)
let value = result_unwrap_or(success, 0)  // 42

let failure = result_err("error")
let value2 = result_unwrap_or(failure, 0)  // 0
```

**Use Cases:**
- Providing fallback values
- Graceful degradation: `let data = result_unwrap_or(fetch_data(), cached_data)`

---

## Predicate Methods

### result_is_ok

```pw
function result_is_ok<T, E>(res: Result<T, E>) -> bool
```

Check if the `Result` is `Ok`.

**Parameters:**
- `res: Result<T, E>` - The Result to check

**Returns:**
- `bool` - `true` if `Ok`, `false` if `Err`

**Example:**
```pw
let success = result_ok(42)
let is_success = result_is_ok(success)  // true

let failure = result_err("error")
let is_success2 = result_is_ok(failure)  // false
```

---

### result_is_err

```pw
function result_is_err<T, E>(res: Result<T, E>) -> bool
```

Check if the `Result` is `Err`.

**Parameters:**
- `res: Result<T, E>` - The Result to check

**Returns:**
- `bool` - `true` if `Err`, `false` if `Ok`

**Example:**
```pw
let success = result_ok(42)
let is_error = result_is_err(success)  // false

let failure = result_err("error")
let is_error2 = result_is_err(failure)  // true
```

---

## Pattern Matching

### result_match

```pw
function result_match<T, E, U>(
    res: Result<T, E>,
    ok_fn: function(T) -> U,
    err_fn: function(E) -> U
) -> U
```

Pattern match on `Result`, calling the appropriate function.

**Parameters:**
- `res: Result<T, E>` - The Result to match
- `ok_fn: function(T) -> U` - Function to call if `Ok` (receives the value)
- `err_fn: function(E) -> U` - Function to call if `Err` (receives the error)

**Returns:**
- `U` - The result of the called function

**Example:**
```pw
let success = result_ok(42)
let message = result_match(
    success,
    fn(x) -> "Success: " + str(x),
    fn(e) -> "Error: " + e
)
// message is "Success: 42"

let failure = result_err("timeout")
let message2 = result_match(
    failure,
    fn(x) -> "Success: " + str(x),
    fn(e) -> "Error: " + e
)
// message2 is "Error: timeout"
```

---

## Common Patterns

### Chaining Fallible Operations

```pw
function read_and_process_file(path: string) -> Result<Data, string>:
    let content = read_file(path)  // Returns Result<string, string>
    let parsed = result_and_then(content, parse_json)  // Result<Json, string>
    let validated = result_and_then(parsed, validate_schema)  // Result<Data, string>
    return validated

// Usage
let data_result = read_and_process_file("config.json")
let data = result_match(
    data_result,
    fn(d) -> d,  // Use data
    fn(e) -> {
        log("Error: " + e)
        return default_data()
    }
)
```

### Error Recovery with map_err

```pw
function fetch_with_retry(url: string) -> Result<Response, string>:
    let attempt1 = http_get(url)
    if result_is_ok(attempt1):
        return attempt1

    // Add context to error
    let attempt2 = http_get(url)
    return result_map_err(attempt2, fn(e) -> "Retry failed: " + e)
```

### Converting Errors

```pw
enum HttpError:
    - Timeout
    - NotFound
    - ServerError(code: int)

function fetch_user(id: int) -> Result<User, HttpError>:
    let response = http_get("/api/users/" + str(id))

    return result_map_err(
        response,
        fn(err_str) -> {
            if err_str == "timeout":
                return HttpError.Timeout
            else if err_str == "404":
                return HttpError.NotFound
            else:
                return HttpError.ServerError(500)
        }
    )
```

---

## Real-World Examples

### File I/O

```pw
function load_config(path: string) -> Result<Config, string>:
    let content = file.read(path)
    if result_is_err(content):
        return result_map_err(content, fn(e) -> "Cannot read file: " + e)

    let parsed = result_and_then(content, json.parse)
    if result_is_err(parsed):
        return result_map_err(parsed, fn(e) -> "Invalid JSON: " + e)

    return parsed
```

### HTTP Request with Typed Errors

```pw
enum ApiError:
    - NetworkError(message: string)
    - AuthError
    - RateLimitExceeded
    - ServerError(code: int)

function fetch_data(token: string) -> Result<Data, ApiError>:
    if token == "":
        return result_err(ApiError.AuthError)

    let response = http_get("/api/data", {auth: token})

    return result_match(
        response,
        fn(resp) -> {
            if resp.status == 200:
                return result_ok(resp.body)
            else if resp.status == 401:
                return result_err(ApiError.AuthError)
            else if resp.status == 429:
                return result_err(ApiError.RateLimitExceeded)
            else:
                return result_err(ApiError.ServerError(resp.status))
        },
        fn(err) -> result_err(ApiError.NetworkError(err))
    )
```

### Parsing with Multiple Validations

```pw
function parse_age(input: string) -> Result<int, string>:
    let parsed = int.parse(input)
    if result_is_err(parsed):
        return result_err("Not a number")

    return result_and_then(parsed, fn(age) -> {
        if age < 0:
            return result_err("Age cannot be negative")
        else if age > 150:
            return result_err("Age too high")
        else:
            return result_ok(age)
    })
```

---

## Anti-Patterns

### ❌ DON'T: Use exceptions instead of Result

```pw
// Bad - throws exception
function divide(a: int, b: int) -> int:
    if b == 0:
        throw "division by zero"  // ❌ Exception
    return a / b
```

```pw
// Good - returns Result
function divide(a: int, b: int) -> Result<int, string>:
    if b == 0:
        return result_err("division by zero")  // ✅ Explicit
    return result_ok(a / b)
```

### ❌ DON'T: Ignore errors silently

```pw
// Bad - error information lost
let value = result_unwrap_or(risky_operation(), default_value)
// ❌ No way to know if operation failed
```

```pw
// Good - handle errors explicitly
let result = risky_operation()
let value = result_match(
    result,
    fn(v) -> v,
    fn(e) -> {
        log("Operation failed: " + e)  // ✅ Log error
        return default_value
    }
)
```

### ❌ DON'T: Use string errors for typed errors

```pw
// Bad - loses type information
function fetch() -> Result<Data, string>:
    return result_err("timeout")  // ❌ Just a string
```

```pw
// Good - use typed errors
enum FetchError:
    - Timeout
    - NetworkError(reason: string)
    - ParseError

function fetch() -> Result<Data, FetchError>:
    return result_err(FetchError.Timeout)  // ✅ Type-safe
```

---

## Cross-Language Mapping

| PW | Python | Rust | Go | TypeScript | C# |
|----|--------|------|----|-----------|----|
| `Result<T, E>` | `Union[Ok[T], Err[E]]` | `Result<T, E>` | `(T, error)` | Custom type | Custom type |
| `Ok(42)` | `Ok(42)` | `Ok(42)` | `42, nil` | `{ ok: 42 }` | `Ok<int>(42)` |
| `Err("msg")` | `Err("msg")` | `Err("msg")` | `nil, err` | `{ err: "msg" }` | `Err<string>("msg")` |

---

## Performance Considerations

- **Zero-cost in Rust**: Compiles to native `Result<T, E>`
- **No exceptions**: No stack unwinding overhead
- **Explicit control flow**: All error paths visible to optimizer

---

## See Also

- [Option<T>](./Option.md) - For optional values without errors
- [stdlib README](./README.md) - Overview of the standard library
- [PW_NATIVE_SYNTAX.md](../PW_NATIVE_SYNTAX.md) - Language syntax reference

---

**Last Updated**: 2025-10-12
**Status**: API specification complete, awaiting parser generic support
