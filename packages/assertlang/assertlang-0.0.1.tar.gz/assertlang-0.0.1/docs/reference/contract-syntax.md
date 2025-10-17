# Contract Syntax Reference

**Complete reference for AssertLang contract language.**

---

## Quick Reference

| Feature | Syntax | Example |
|---------|--------|---------|
| Precondition | `@requires name: expr` | `@requires positive: x > 0` |
| Postcondition | `@ensures name: expr` | `@ensures valid: result > 0` |
| Invariant | `@invariant name: expr` | `@invariant size_ok: len(items) <= capacity` |
| Old value | `old(variable)` | `@ensures increased: result > old(x)` |
| Function | `function name(params) -> type { }` | `function add(x: int, y: int) -> int { }` |
| Type annotation | `param: type` | `count: int`, `name: string` |

---

## Table of Contents

1. [Preconditions (@requires)](#preconditions-requires)
2. [Postconditions (@ensures)](#postconditions-ensures)
3. [Invariants (@invariant)](#invariants-invariant)
4. [Old Values (old())](#old-values-old)
5. [Types](#types)
6. [Functions](#functions)
7. [Classes](#classes)
8. [Expressions](#expressions)
9. [Operators](#operators)
10. [Built-in Functions](#built-in-functions)

---

## Preconditions (@requires)

**What**: Conditions that must be true **before** function execution.

**Syntax**:
```pw
@requires clause_name: boolean_expression
```

**Rules**:
- Can have multiple preconditions
- Checked in order of declaration
- Must use only parameters and constants
- Cannot reference `result` or local variables

**Examples**:

### Single Precondition
```pw
function sqrt(x: float) -> float {
    @requires non_negative: x >= 0.0

    // ... implementation
}
```

### Multiple Preconditions
```pw
function divide(a: float, b: float) -> float {
    @requires b_not_zero: b != 0.0
    @requires finite_inputs: is_finite(a) && is_finite(b)

    return a / b;
}
```

### Complex Conditions
```pw
function process_order(order: Order, user: User) -> bool {
    @requires valid_order: order.id > 0 && len(order.items) > 0
    @requires verified_user: user.verified == true
    @requires sufficient_balance: user.balance >= order.total
    @requires valid_shipping: len(order.shipping_address) > 0

    // ... implementation
}
```

**Common Patterns**:
- `x > 0` - Positive numbers
- `len(s) > 0` - Non-empty collections
- `x >= 0 && x <= 100` - Range checking
- `state == "valid"` - State validation
- `param != null` - Null checking

---

## Postconditions (@ensures)

**What**: Conditions that must be true **after** function execution.

**Syntax**:
```pw
@ensures clause_name: boolean_expression
```

**Rules**:
- Can have multiple postconditions
- Checked after function returns
- Can reference `result`, parameters, and `old()` values
- Cannot modify state (pure boolean expressions)

**Special Variables**:
- `result` - The return value of the function

**Examples**:

### Result Validation
```pw
function absolute(x: int) -> int {
    @requires true: true

    @ensures non_negative: result >= 0
    @ensures preserves_magnitude: result == x || result == -x

    if (x < 0) {
        return -x;
    }
    return x;
}
```

### Old Value Comparison
```pw
function increment(x: int) -> int {
    @requires positive: x > 0

    @ensures incremented: result == old(x) + 1
    @ensures still_positive: result > 0

    return x + 1;
}
```

### State Verification
```pw
function add_item(items: array<string>, item: string) -> array<string> {
    @requires non_empty_item: len(item) > 0
    @requires space_available: len(items) < 1000

    @ensures item_added: len(result) == len(old(items)) + 1
    @ensures contains_item: item in result
    @ensures size_increased: len(result) > len(old(items))

    items.push(item);
    return items;
}
```

**Common Patterns**:
- `result > 0` - Positive result
- `result == old(x) + 1` - Incremented value
- `len(result) == len(input)` - Size preservation
- `result >= old(value)` - Monotonic increase
- `result != null` - Non-null return

---

## Invariants (@invariant)

**What**: Conditions that must **always** be true for a class/object.

**Syntax**:
```pw
@invariant clause_name: boolean_expression
```

**Rules**:
- Defined at class level
- Checked after constructor and after every method
- Can reference class fields/properties
- Cannot reference method parameters or local variables

**Examples**:

### Class Invariants
```pw
class BankAccount {
    balance: float
    account_id: string

    @invariant non_negative_balance: this.balance >= 0.0
    @invariant valid_id: len(this.account_id) > 0

    function withdraw(amount: float) -> bool {
        @requires positive_amount: amount > 0.0
        @requires sufficient_funds: amount <= this.balance

        @ensures balance_reduced: this.balance == old(this.balance) - amount

        this.balance = this.balance - amount;
        return true;
    }
}
```

### Multiple Invariants
```pw
class CircularBuffer<T> {
    items: array<T>
    capacity: int
    size: int

    @invariant capacity_positive: this.capacity > 0
    @invariant size_in_range: this.size >= 0 && this.size <= this.capacity
    @invariant array_sized: len(this.items) == this.capacity
    @invariant never_overflow: this.size <= len(this.items)

    // ... methods
}
```

**Common Patterns**:
- `balance >= 0` - Non-negative balance
- `size <= capacity` - Size limits
- `len(items) == capacity` - Fixed capacity
- `state in valid_states` - Valid state
- `count >= 0` - Non-negative counters

---

## Old Values (old())

**What**: Reference parameter/field values from **before** function execution.

**Syntax**:
```pw
old(variable_name)
```

**Where Allowed**:
- ✓ Postconditions (`@ensures`)
- ✗ Preconditions (`@requires`)
- ✗ Function body

**Examples**:

### Compare Before/After
```pw
function increment_counter(counter: int) -> int {
    @requires non_negative: counter >= 0

    @ensures incremented: result == old(counter) + 1
    @ensures increased: result > old(counter)

    return counter + 1;
}
```

### State Changes
```pw
function mark_as_paid(order: Order) -> Order {
    @requires pending: order.status == "pending"

    @ensures status_changed: result.status == "paid"
    @ensures status_was_pending: old(order.status) == "pending"
    @ensures amount_unchanged: result.amount == old(order.amount)

    order.status = "paid";
    return order;
}
```

### Array Modifications
```pw
function add_element(arr: array<int>, elem: int) -> array<int> {
    @requires valid_elem: elem > 0

    @ensures size_increased: len(result) == len(old(arr)) + 1
    @ensures element_added: elem in result
    @ensures original_preserved: all_elements_from(result, old(arr))

    arr.push(elem);
    return arr;
}
```

**Rules**:
- Can only use `old()` in postconditions
- Can nest: `old(obj.field.property)`
- Captures value at function entry
- Deep copy for objects/arrays

---

## Types

**Primitive Types**:
```pw
int          // 32-bit signed integer
float        // 64-bit floating point
string       // UTF-8 string
bool         // true or false
```

**Generic Types**:
```pw
array<T>             // Array of T
Option<T>            // Optional value (Some(T) or None)
Result<T, E>         // Success (Ok(T)) or Error (Err(E))
Map<K, V>            // Key-value map
Set<T>               // Unique values set
```

**Union Types**:
```pw
string | int         // Either string or int
Option<string>       // Some(string) or None
Result<int, Error>   // Ok(int) or Err(Error)
```

**Function Types**:
```pw
function(int, int) -> int        // Function taking 2 ints, returning int
function(string) -> bool         // Predicate function
```

**Custom Types**:
```pw
class User {
    name: string
    age: int
}

type UserId = int
type Email = string
```

---

## Functions

**Syntax**:
```pw
function name<GenericParams>(params) -> ReturnType {
    @requires precondition_name: boolean_expr
    @ensures postcondition_name: boolean_expr

    // body
    return value;
}
```

**Examples**:

### Basic Function
```pw
function add(x: int, y: int) -> int {
    @requires true: true
    @ensures sum_correct: result == x + y

    return x + y;
}
```

### Generic Function
```pw
function first<T>(items: array<T>) -> Option<T> {
    @requires non_empty: len(items) > 0

    @ensures has_value: result != None
    @ensures correct_element: result == Some(items[0])

    return Some(items[0]);
}
```

### Void Function
```pw
function log_message(msg: string) -> void {
    @requires non_empty: len(msg) > 0

    print(msg);
}
```

### Multiple Returns (Tuple)
```pw
function divide_with_remainder(a: int, b: int) -> (int, int) {
    @requires b_not_zero: b != 0

    @ensures quotient_correct: result.0 == a / b
    @ensures remainder_correct: result.1 == a % b

    let quotient = a / b;
    let remainder = a % b;
    return (quotient, remainder);
}
```

---

## Classes

**Syntax**:
```pw
class ClassName<GenericParams> {
    field1: Type
    field2: Type

    @invariant name: boolean_expr

    function method_name(params) -> ReturnType {
        // method body
    }
}
```

**Example**:
```pw
class Stack<T> {
    items: array<T>
    capacity: int

    @invariant valid_capacity: this.capacity > 0
    @invariant within_capacity: len(this.items) <= this.capacity
    @invariant non_negative_size: len(this.items) >= 0

    function push(item: T) -> bool {
        @requires not_full: len(this.items) < this.capacity

        @ensures item_added: len(this.items) == old(len(this.items)) + 1
        @ensures top_is_item: this.peek() == item

        this.items.push(item);
        return true;
    }

    function pop() -> Option<T> {
        @requires not_empty: len(this.items) > 0

        @ensures size_decreased: len(this.items) == old(len(this.items)) - 1
        @ensures returns_value: result != None

        return this.items.pop();
    }

    function peek() -> T {
        @requires not_empty: len(this.items) > 0

        @ensures correct_element: result == this.items[len(this.items) - 1]

        return this.items[len(this.items) - 1];
    }
}
```

---

## Expressions

**Boolean Expressions** (for contracts):
```pw
x > 0                           // Comparison
len(s) > 0                      // Function call
x >= 0 && x <= 100             // Logical AND
state == "valid" || state == "pending"  // Logical OR
!(x < 0)                        // Logical NOT
value in [1, 2, 3]             // Membership
```

**Arithmetic**:
```pw
x + y                           // Addition
x - y                           // Subtraction
x * y                           // Multiplication
x / y                           // Division
x % y                           // Modulo
x ** y                          // Exponentiation
```

**Comparison**:
```pw
x == y                          // Equality
x != y                          // Inequality
x > y                           // Greater than
x >= y                          // Greater or equal
x < y                           // Less than
x <= y                          // Less or equal
```

**Logical**:
```pw
a && b                          // AND
a || b                          // OR
!a                              // NOT
```

---

## Operators

**Precedence** (highest to lowest):
1. `()` - Parentheses
2. `**` - Exponentiation
3. `!`, `-` (unary) - Logical NOT, Negation
4. `*`, `/`, `%` - Multiplication, Division, Modulo
5. `+`, `-` - Addition, Subtraction
6. `<`, `<=`, `>`, `>=` - Comparison
7. `==`, `!=` - Equality
8. `&&` - Logical AND
9. `||` - Logical OR

**Examples**:
```pw
x + y * z       // Same as: x + (y * z)
a && b || c     // Same as: (a && b) || c
!x && y         // Same as: (!x) && y
```

---

## Built-in Functions

**String Functions**:
```pw
len(s: string) -> int          // String length
s.strip() -> string            // Remove whitespace
s.upper() -> string            // Uppercase
s.lower() -> string            // Lowercase
s.contains(sub: string) -> bool // Substring check
```

**Array Functions**:
```pw
len(arr: array<T>) -> int      // Array length
arr.push(item: T) -> void      // Add element
arr.pop() -> Option<T>         // Remove last
arr[index: int] -> T           // Index access
```

**Math Functions**:
```pw
abs(x: int) -> int             // Absolute value
min(x: int, y: int) -> int     // Minimum
max(x: int, y: int) -> int     // Maximum
```

**Type Checking**:
```pw
is_some(opt: Option<T>) -> bool     // Has value
is_none(opt: Option<T>) -> bool     // No value
is_ok(res: Result<T,E>) -> bool     // Success
is_err(res: Result<T,E>) -> bool    // Error
```

---

## Complete Example

```pw
class BankAccount {
    balance: float
    account_id: string
    owner: string

    @invariant positive_balance: this.balance >= 0.0
    @invariant valid_id: len(this.account_id) > 0
    @invariant has_owner: len(this.owner) > 0

    function deposit(amount: float) -> Result<float, string> {
        @requires positive_amount: amount > 0.0
        @requires reasonable_amount: amount <= 1000000.0

        @ensures balance_increased: this.balance == old(this.balance) + amount
        @ensures returns_new_balance: is_ok(result) && result.unwrap() == this.balance

        this.balance = this.balance + amount;
        return Ok(this.balance);
    }

    function withdraw(amount: float) -> Result<float, string> {
        @requires positive_amount: amount > 0.0
        @requires sufficient_funds: amount <= this.balance

        @ensures balance_decreased: this.balance == old(this.balance) - amount
        @ensures non_negative_result: this.balance >= 0.0
        @ensures returns_new_balance: is_ok(result) && result.unwrap() == this.balance

        this.balance = this.balance - amount;
        return Ok(this.balance);
    }

    function transfer(to: BankAccount, amount: float) -> Result<bool, string> {
        @requires positive_amount: amount > 0.0
        @requires sufficient_funds: amount <= this.balance
        @requires different_account: to.account_id != this.account_id

        @ensures from_decreased: this.balance == old(this.balance) - amount
        @ensures to_increased: to.balance == old(to.balance) + amount
        @ensures total_preserved: this.balance + to.balance == old(this.balance) + old(to.balance)

        this.balance = this.balance - amount;
        to.balance = to.balance + amount;
        return Ok(true);
    }
}
```

---

## See Also

- **[Runtime API](runtime-api.md)** - Python/JavaScript runtime functions
- **[CLI Commands](cli-commands.md)** - Command-line tools
- **[MCP Operations](mcp-operations.md)** - MCP server operations
- **[Error Codes](error-codes.md)** - Contract violation errors
- **[Quickstart](../../QUICKSTART.md)** - Get started in 5 minutes

---

**Complete Reference** | **[Next: Runtime API →](runtime-api.md)**
