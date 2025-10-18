# PW Syntax Quick Reference

**Version**: 2.1.0b12
**Status**: Production Ready
**Last Updated**: 2025-10-12

A concise syntax reference for the AssertLang (PW) programming language.

---

## Table of Contents

1. [Variables](#variables)
2. [Type System](#type-system)
3. [Enums](#enums)
4. [Functions](#functions)
5. [Classes](#classes)
6. [Control Flow](#control-flow)
7. [Error Handling](#error-handling)
8. [Operators](#operators)
9. [Comments](#comments)
10. [Common Pitfalls](#common-pitfalls)

---

## Variables

### Variable Declarations

```pw
// ✅ CORRECT: Use 'let' for all variable declarations
let x: int = 42;              // Explicit type
let name = "Alice";           // Type inferred (string)
let items = [1, 2, 3];        // Type inferred (array<int>)

// ❌ ERROR: 'var' keyword does NOT exist
var x = 42;  // Error: Unexpected keyword: var
```

**Rules:**
- **Only `let` keyword** - `var` does not exist in PW
- **Type annotations are optional** - Types can be inferred
- **Variables are function-scoped** - Cannot declare at module level

### Scope Rules

```pw
// ✅ Local scope (inside functions)
function example() -> int {
    let x = 10;    // Valid
    return x;
}

// ❌ ERROR: No global variables
let GLOBAL = 42;   // Error at module level
```

### Constants Pattern

Since PW doesn't allow module-level variables, use the Constants class:

```pw
// ✅ Recommended: Constants class
class Constants {
    MAX_SIZE: int;
    API_URL: string;

    constructor() {
        self.MAX_SIZE = 100;
        self.API_URL = "https://api.example.com";
    }
}

// Usage
function main() -> int {
    let config = Constants();
    console.log(config.API_URL);
    return 0;
}
```

---

## Type System

### Primitive Types

```pw
let integer: int = 42;
let floating: float = 3.14;
let text: string = "Hello";
let flag: bool = true;
let nothing: null = null;
```

### Collection Types

```pw
// Array (ordered list)
let numbers: array<int> = [1, 2, 3];
let items = [1, 2, 3];              // Inferred as array<int>

// Map (key-value dictionary)
let user: map<string, int> = {
    "age": 30,
    "score": 100
};
let data = {"key": "value"};        // Inferred as map<string, string>

// Generic syntax
let users: array<string> = ["Alice", "Bob"];
let scores: map<string, int> = {"Alice": 95, "Bob": 87};
```

---

## Array Type Annotations

Arrays in PW use the `array<T>` syntax where `T` is the element type.

### Basic Array Syntax

```pw
// Array of integers
let numbers: array<int> = [1, 2, 3, 4, 5];

// Array of strings
let names: array<string> = ["Alice", "Bob", "Charlie"];

// Array of floats
let prices: array<float> = [9.99, 19.99, 29.99];

// Array of booleans
let flags: array<bool> = [true, false, true];

// Empty array with explicit type
let items: array<string> = [];
```

### Array Type Inference

```pw
// Type inferred from literal values
let ages = [25, 30, 35];              // Inferred as array<int>
let cities = ["NYC", "SF", "LA"];     // Inferred as array<string>

// ✅ CORRECT: Explicit type annotation (recommended for clarity)
let scores: array<int> = [95, 87, 92];

// ❌ WRONG: Cannot use [] as a type annotation
class Container {
    items: [];  // Error: Expected type identifier
}

// ✅ CORRECT: Use array<T> for type annotations
class Container {
    items: array<string>;
}
```

### Nested Array Types

```pw
// 2D array - array of arrays
let matrix: array<array<int>> = [
    [1, 2, 3],
    [4, 5, 6],
    [7, 8, 9]
];

// Array of string arrays
let groups: array<array<string>> = [
    ["Alice", "Bob"],
    ["Charlie", "David"],
    ["Eve"]
];

// 3D array
let cube: array<array<array<int>>> = [
    [[1, 2], [3, 4]],
    [[5, 6], [7, 8]]
];
```

### Arrays with Custom Types

```pw
// Array of class instances (when classes are defined)
class User {
    name: string;
    age: int;

    constructor(name: string, age: int) {
        self.name = name;
        self.age = age;
    }
}

function get_users() -> array<User> {
    let users: array<User> = [];
    // Populate array...
    return users;
}

// Array of optional values
let maybe_numbers: array<int?> = [1, null, 3, null, 5];
```

### Array Operations

```pw
// Accessing elements
let first = numbers[0];
let last = numbers[numbers.length - 1];

// Array length
let count = numbers.length;

// Iterating over arrays
for (item in numbers) {
    console.log(item);
}

for (index, value in enumerate(numbers)) {
    console.log(index, value);
}
```

### Common Array Mistakes

```pw
// ❌ WRONG: Using List instead of array
let items: List<string> = [];  // Error: List is not a PW type

// ✅ CORRECT: Use array<T>
let items: array<string> = [];

// ❌ WRONG: Using [] as type annotation
function process(data: []) -> int {  // Error: Invalid type
    return 0;
}

// ✅ CORRECT: Specify element type
function process(data: array<int>) -> int {
    return data.length;
}

// ❌ WRONG: Missing angle brackets
let values: array = [1, 2, 3];  // Error: array requires type parameter

// ✅ CORRECT: Always specify element type
let values: array<int> = [1, 2, 3];
```

---

## Map Type Annotations

Maps in PW use the `map<K, V>` syntax where `K` is the key type and `V` is the value type.

### Basic Map Syntax

```pw
// Map from string to int
let ages: map<string, int> = {
    "Alice": 30,
    "Bob": 25,
    "Charlie": 35
};

// Map from string to string
let capitals: map<string, string> = {
    "USA": "Washington DC",
    "France": "Paris",
    "Japan": "Tokyo"
};

// Map from string to float
let prices: map<string, float> = {
    "apple": 1.50,
    "banana": 0.75,
    "orange": 2.00
};

// Empty map with explicit type
let data: map<string, int> = {};
```

### Map Type Inference

```pw
// Type inferred from literal values
let scores = {"Alice": 95, "Bob": 87};  // Inferred as map<string, int>
let settings = {"enabled": true};        // Inferred as map<string, bool>

// ✅ CORRECT: Explicit type annotation (recommended)
let config: map<string, string> = {"host": "localhost", "port": "8080"};

// ❌ WRONG: Cannot use {} as a type annotation
class Event {
    payload: {};  // Error: Expected type identifier
}

// ✅ CORRECT: Use map type
class Event {
    payload: map<string, any>;
}
```

### Maps with Complex Value Types

```pw
// Map from string to array
let user_tags: map<string, array<string>> = {
    "Alice": ["admin", "developer"],
    "Bob": ["user", "tester"]
};

// Map from string to map (nested maps)
let config: map<string, map<string, int>> = {
    "database": {"port": 5432, "timeout": 30},
    "cache": {"port": 6379, "ttl": 3600}
};

// Map from int to string (non-string keys)
let status_codes: map<int, string> = {
    200: "OK",
    404: "Not Found",
    500: "Internal Server Error"
};
```

### Maps with Optional Values

```pw
// Map with optional values - values can be null
let preferences: map<string, string?> = {
    "theme": "dark",
    "language": null,  // Explicitly set to null
    "timezone": "UTC"
};

// Function returning optional map
function find_user_data(id: int) -> map<string, any>? {
    if (id < 0) {
        return null;
    }
    return {"id": id, "name": "User"};
}
```

### Map Operations

```pw
// Accessing values
let age = ages["Alice"];  // Returns value or null if key doesn't exist

// Safe access with null check
if (ages["Alice"] != null) {
    let alice_age = ages["Alice"];
}

// Setting values
ages["David"] = 28;

// Iterating over maps (when supported)
for (key in ages.keys()) {
    console.log(key, ages[key]);
}
```

### Common Map Mistakes

```pw
// ❌ WRONG: Using Dict instead of map
let data: Dict<string, int> = {};  // Error: Dict is not a PW type

// ✅ CORRECT: Use map<K, V>
let data: map<string, int> = {};

// ❌ WRONG: Using {} as type annotation
function process(data: {}) -> int {  // Error: Invalid type
    return 0;
}

// ✅ CORRECT: Specify key and value types
function process(data: map<string, any>) -> int {
    return 1;
}

// ❌ WRONG: Missing angle brackets
let values: map = {};  // Error: map requires type parameters

// ✅ CORRECT: Always specify key and value types
let values: map<string, int> = {};

// ❌ WRONG: Single type parameter
let data: map<string> = {};  // Error: map requires 2 type parameters

// ✅ CORRECT: Both key and value types
let data: map<string, int> = {};
```

---

## Generic Types

Generic types allow you to write reusable code that works with multiple types.

### Generic Type Syntax

```pw
// Option type - represents optional values
enum Option<T>:
    - Some(T)
    - None

// Result type - represents success or error
enum Result<T, E>:
    - Ok(T)
    - Err(E)

// Generic class
class Container<T> {
    value: T;

    constructor(value: T) {
        self.value = value;
    }

    function get() -> T {
        return self.value;
    }
}
```

### Using Generic Types

```pw
// Option with different types
let some_int: Option<int> = Option.Some(42);
let some_str: Option<string> = Option.Some("hello");
let none_val: Option<int> = Option.None;

// Result with different types
let ok_result: Result<int, string> = Result.Ok(100);
let err_result: Result<int, string> = Result.Err("failed");

// Generic container instances
let int_container = Container<int>(42);
let str_container = Container<string>("data");
```

### Generic Functions

```pw
// Function with generic type parameter
function first<T>(items: array<T>) -> T? {
    if (items.length > 0) {
        return items[0];
    }
    return null;
}

// Usage with different types
let first_num = first<int>([1, 2, 3]);      // Returns int?
let first_str = first<string>(["a", "b"]);  // Returns string?

// Type inference (type parameter can be omitted)
let first_value = first([10, 20, 30]);  // T inferred as int
```

### Nested Generic Types

```pw
// Array of Options
let values: array<Option<int>> = [
    Option.Some(1),
    Option.None,
    Option.Some(3)
];

// Map of Results
let responses: map<string, Result<string, int>> = {
    "api1": Result.Ok("success"),
    "api2": Result.Err(404)
};

// Option of array
let maybe_list: Option<array<string>> = Option.Some(["a", "b", "c"]);

// Result with complex types
let complex: Result<map<string, array<int>>, string> = Result.Ok({
    "scores": [95, 87, 92]
});
```

### Generic Type Constraints

```pw
// Generic function with multiple type parameters
function combine<T, U>(first: T, second: U) -> map<string, any> {
    return {
        "first": first,
        "second": second
    };
}

// Multiple generic parameters
function zip<T, U>(left: array<T>, right: array<U>) -> array<map<string, any>> {
    let result: array<map<string, any>> = [];
    // Implementation...
    return result;
}
```

### Common Generic Type Mistakes

```pw
// ❌ WRONG: Missing type parameters
let opt: Option = Option.Some(42);  // Error: Option requires type parameter

// ✅ CORRECT: Provide type parameter
let opt: Option<int> = Option.Some(42);

// ❌ WRONG: Wrong number of type parameters
let res: Result<int> = Result.Ok(42);  // Error: Result requires 2 parameters

// ✅ CORRECT: Both type parameters
let res: Result<int, string> = Result.Ok(42);

// ❌ WRONG: Mixing generic syntax styles
let items: List<int> = [];  // Error: Use array<T>, not List<T>

// ✅ CORRECT: PW native generic syntax
let items: array<int> = [];
```

### Optional Types

```pw
// Optional types can be null
let maybe_number: int? = null;
let maybe_user: map? = find_user(42);

function find_user(id: int) -> map? {
    if (id < 0) {
        return null;  // Valid for optional types
    }
    return {id: id, name: "User"};
}
```

### Type Annotations

```pw
// ✅ CORRECT: Type annotations on 'let' declarations
let x: int = 42;
let name: string = "Alice";

// ✅ CORRECT: Type inference (no annotation needed)
let count = 10;
let message = "Hello";

// ❌ ERROR: Cannot use type annotations with 'var'
var x: int = 42;  // Error: 'var' doesn't exist

// ❌ ERROR: '{}' is NOT a type annotation
class Event {
    payload: {};  // Error: Expected IDENTIFIER, got {
}

// ✅ CORRECT: Use 'map' type instead
class Event {
    payload: map;  // Generic map type
}
```

---

## Enums

**IMPORTANT:** PW uses YAML-style enum syntax (colon + dashes), NOT C-style braces.

### Basic Enum Syntax

```pw
// ✅ CORRECT: YAML-style enum
enum Status:
    - Pending
    - Active
    - Completed
    - Failed

enum Color:
    - Red
    - Green
    - Blue
```

### Enums with Associated Types

```pw
// Rust-style enum variants with data
enum Result:
    - Ok(int)
    - Error(string)

enum Option:
    - Some(string)
    - None

enum Event:
    - Click(int, int)           // x, y coordinates
    - KeyPress(string)           // key name
    - Scroll(float)              // delta
```

### What Does NOT Work

```pw
// ❌ ERROR: C-style brace syntax NOT supported
enum Status {
    QUERY,
    MUTATION
}
// Error: Expected :, got {

// ❌ ERROR: Semicolons after enum values
enum Status:
    - Pending;
    - Active;
// Error: Unexpected token

// ❌ ERROR: Enum values with assigned numbers (not yet supported)
enum Color:
    - Red = 1
    - Green = 2
// Currently not supported (planned for future)
```

### Enum Usage

```pw
// Define enum
enum OperationType:
    - QUERY
    - MUTATION
    - SUBSCRIPTION

// Use in class
class Request {
    operation: string;  // Store enum value as string

    constructor(op: string) {
        self.operation = op;
    }
}

// Create instance
function main() -> int {
    let req = Request("QUERY");
    return 0;
}
```

---

## Functions

### Basic Function Syntax

```pw
// Function with parameters and return type
function add(x: int, y: int) -> int {
    return x + y;
}

// No return type (void)
function print_message(msg: string) {
    console.log(msg);
}

// Optional return (can return null)
function find_item(id: int) -> map? {
    if (id < 0) {
        return null;
    }
    return {id: id, name: "Item"};
}
```

### Function with Throws

```pw
function divide(x: int, y: int) -> int throws DivisionError {
    if (y == 0) {
        throw DivisionError("Cannot divide by zero");
    }
    return x / y;
}
```

### Async Functions

```pw
async function fetch_data(url: string) -> string {
    let response = await http.get(url);
    return response.body;
}
```

---

## Classes

### Class Definition

```pw
class User {
    // Properties
    id: string;
    name: string;
    email: string;

    // Constructor
    constructor(id: string, name: string, email: string) {
        self.id = id;
        self.name = name;
        self.email = email;
    }

    // Method
    function greet() -> string {
        return "Hello, " + self.name;
    }

    // Method with parameters
    function set_email(new_email: string) {
        self.email = new_email;
    }
}

// Usage
let user = User("123", "Alice", "alice@example.com");
let greeting = user.greet();
```

### Class Properties

```pw
class Config {
    // Properties with types
    host: string;
    port: int;
    enabled: bool;
    options: map;
    tags: array<string>;

    constructor(host: string, port: int) {
        self.host = host;
        self.port = port;
        self.enabled = true;
        self.options = {};
        self.tags = [];
    }
}
```

---

## Control Flow

### If-Else Statements

```pw
// C-style if-else
if (x > 10) {
    console.log("Big");
} else if (x > 5) {
    console.log("Medium");
} else {
    console.log("Small");
}
```

### For Loops

```pw
// C-style for loop
for (let i = 0; i < 10; i = i + 1) {
    console.log(i);
}

// For-in loop
for (item in items) {
    console.log(item);
}

// For loop with index and value
for (index, value in enumerate(items)) {
    console.log(index, value);
}

// Range-based for loop
for (i in range(0, 10)) {
    console.log(i);
}
```

### While Loops

```pw
let count = 10;
while (count > 0) {
    console.log(count);
    count = count - 1;
}
```

### Break and Continue

```pw
for (let i = 0; i < 10; i = i + 1) {
    if (i == 5) {
        break;        // Exit loop
    }
    if (i % 2 == 0) {
        continue;     // Skip to next iteration
    }
    console.log(i);
}
```

---

## Error Handling

### Try-Catch-Finally

```pw
// Basic try-catch
try {
    let result = risky_operation();
    console.log(result);
} catch (error) {
    console.log("Error occurred");
}

// Try-catch-finally
try {
    let file = open_file("data.txt");
    process(file);
} catch (error) {
    console.log("Failed to process file");
} finally {
    cleanup();  // Always runs
}
```

### Throw Errors

```pw
function validate(value: int) throws ValidationError {
    if (value < 0) {
        throw ValidationError("Value must be positive");
    }
}
```

---

## Operators

### Arithmetic

```pw
let sum = a + b;
let diff = a - b;
let product = a * b;
let quotient = a / b;
let remainder = a % b;
let power = a ** b;
let floor_div = a // b;
```

### Comparison

```pw
let equal = a == b;
let not_equal = a != b;
let greater = a > b;
let less = a < b;
let gte = a >= b;
let lte = a <= b;
```

### Logical

```pw
// Python-style (recommended)
let and_result = a and b;
let or_result = a or b;
let not_result = not a;

// C-style (also supported)
let and_result = a && b;
let or_result = a || b;
let not_result = !a;
```

### Assignment

```pw
let x = 10;
x = x + 5;       // Regular assignment
x += 5;          // Compound assignment
x -= 3;
x *= 2;
x /= 2;
```

---

## Comments

```pw
// Single-line comment (Python/C-style)

/*
 * Multi-line comment
 * Spans multiple lines
 */

# Python-style comment (also supported)

function example() -> int {
    // Comment inside function
    let x = 42;  // Inline comment
    return x;
}
```

---

## Common Pitfalls

### ❌ Using 'var' instead of 'let'

```pw
// ❌ ERROR
var x = 42;

// ✅ CORRECT
let x = 42;
```

### ❌ C-style enum syntax

```pw
// ❌ ERROR
enum Status {
    Active,
    Inactive
}

// ✅ CORRECT
enum Status:
    - Active
    - Inactive
```

### ❌ Global variables

```pw
// ❌ ERROR
let GLOBAL_CONFIG = "production";

// ✅ CORRECT: Use Constants class
class Constants {
    ENVIRONMENT: string;
    constructor() {
        self.ENVIRONMENT = "production";
    }
}
```

### ❌ Using {} as a type

```pw
// ❌ ERROR
class Event {
    data: {};
}

// ✅ CORRECT
class Event {
    data: map;
}
```

### ❌ Type annotation with 'var'

```pw
// ❌ ERROR
var x: int = 42;

// ✅ CORRECT
let x: int = 42;
```

### ❌ Empty array literal as type

```pw
// ❌ ERROR
class Container {
    items: [];
}

// ✅ CORRECT
class Container {
    items: array<string>;  // Or array<int>, etc.
}
```

---

## Language Mapping

How PW translates to other languages:

| PW | Python | Go | Rust | TypeScript | C# |
|----|--------|----|----- |------------|-----|
| `let x: int = 5;` | `x: int = 5` | `var x int = 5` | `let x: i32 = 5;` | `const x: number = 5;` | `int x = 5;` |
| `array<int>` | `List[int]` | `[]int` | `Vec<i32>` | `number[]` | `List<int>` |
| `map<string, int>` | `Dict[str, int]` | `map[string]int` | `HashMap<String, i32>` | `Map<string, number>` | `Dictionary<string, int>` |
| `int?` | `Optional[int]` | `*int` | `Option<i32>` | `number \| null` | `int?` |

---

## Quick Checklist

Before writing PW code, remember:

- [ ] Use `let` (not `var`) for variables
- [ ] Enums use colon + dashes (not braces)
- [ ] No global variables (use Constants class)
- [ ] Type annotations are optional but recommended
- [ ] Functions need explicit return types
- [ ] Use `map` or `array<T>`, not `{}` or `[]` as types

---

## See Also

- [PW Native Syntax Specification](PW_NATIVE_SYNTAX.md) - Complete language reference
- [PW Language Guide](PW_LANGUAGE_GUIDE.md) - Detailed explanations
- [Safe Patterns](SAFE_PATTERNS.md) - Best practices
- [Examples](../examples/) - Working code samples

---

**Need Help?** Check the [bug reports](../Bugs/) for common issues or consult the full [PW DSL 2.0 Spec](PW_DSL_2.0_SPEC.md).
