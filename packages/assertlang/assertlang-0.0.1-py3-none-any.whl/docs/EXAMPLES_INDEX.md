# PW Examples Index

**Comprehensive catalog of all PW example files**

Last Updated: 2025-10-08 (v2.1.0b3)

---

## Table of Contents

- [Quick Start Examples](#quick-start-examples)
- [Language Feature Examples](#language-feature-examples)
- [Production Examples](#production-examples)
- [Bug Fix Demonstration Examples](#bug-fix-demonstration-examples)
- [Compilation Status](#compilation-status)

---

## Quick Start Examples

### hello-world.al

**Location**: `/Users/hustlermain/HUSTLER_CONTENT/HSTLR/DEV/AssertLang/examples/hello-world.pw`

**Purpose**: Minimal working example

**Features Demonstrated**:
- Basic function definition
- String return type
- Function invocation

**Compiles to**: Python, Go, Rust, TypeScript, C#

**Lines**: ~10

---

### calculator.al

**Location**: `/Users/hustlermain/HUSTLER_CONTENT/HSTLR/DEV/AssertLang/examples/calculator.pw`

**Purpose**: Basic arithmetic operations

**Features Demonstrated**:
- Multiple functions
- Integer and float types
- Arithmetic operators
- Conditional logic (if/else)
- Function composition

**Compiles to**: Python, Go, Rust, TypeScript, C#

**Lines**: ~150 (19 functions)

**Highlights**:
- `add()`, `subtract()`, `multiply()`, `divide()`
- Tax and discount calculations
- Percentage calculations
- Nested function calls

---

## Language Feature Examples

### error_handling.al ✅ NEW

**Location**: `/Users/hustlermain/HUSTLER_CONTENT/HSTLR/DEV/AssertLang/examples/error_handling.pw`

**Purpose**: Demonstrate try/catch patterns

**Features Demonstrated**:
- Try/catch blocks (Bug #3 - Fixed)
- Throw statements
- Finally blocks
- Nested error handling
- Error message concatenation

**Compiles to**: Python, Go, Rust, TypeScript, C#

**Lines**: ~60 (4 functions)

**Functions**:
1. `safe_divide()` - Basic try/catch
2. `validate_user_input()` - Multiple error conditions
3. `process_with_cleanup()` - Try/catch/finally
4. `nested_error_handling()` - Nested try/catch

**Bug Fixed**: Bug #3 - Try/catch syntax standardization (Session 23)

---

### array_and_map_basics.al ✅ NEW

**Location**: `/Users/hustlermain/HUSTLER_CONTENT/HSTLR/DEV/AssertLang/examples/array_and_map_basics.pw`

**Purpose**: Demonstrate safe collection operations

**Features Demonstrated**:
- Array creation and access
- Array `.length` property (Bug #8 - Fixed)
- Safe map indexing (Bug #7 - Fixed)
- Map creation with object literals
- String literal keys
- Null checks for missing keys

**Compiles to**: Python, Go, Rust, TypeScript, C#

**Lines**: ~56 (6 functions)

**Functions**:
1. `count_items()` - Array length
2. `sum_array()` - Array iteration with .length
3. `has_user()` - Safe map key checking
4. `add_user()` - Map insertion after existence check
5. `get_config()` - String literal keys
6. `safe_get()` - Array bounds checking

**Bugs Fixed**:
- Bug #7 - Safe map indexing (Session 26)
- Bug #8 - Array .length property (Session 25)

---

## Production Examples

### calculator_cli.al

**Location**: `/Users/hustlermain/HUSTLER_CONTENT/HSTLR/DEV/AssertLang/examples/calculator_cli.pw`

**Purpose**: Interactive calculator application

**Features Demonstrated**:
- Classes with constructors (Bug #1 - Fixed)
- Instance methods
- Property access and modification
- Arrays for history storage
- Control flow
- State management

**Compiles to**: Python, Go, Rust, TypeScript, C#

**Lines**: ~3,676 characters

**Classes**:
- `Calculator` - 6 methods (add, subtract, multiply, divide, clear, history)

**Helper Functions**: 5 utility functions

**Bug Fixed**: Bug #1 - Class compilation crash (Session 21)

---

### todo_list_manager.al

**Location**: `/Users/hustlermain/HUSTLER_CONTENT/HSTLR/DEV/AssertLang/examples/todo_list_manager.pw`

**Purpose**: Task management system

**Features Demonstrated**:
- Multiple classes
- CRUD operations
- Array operations
- Map usage
- Property assignments in constructors
- Method chaining patterns

**Compiles to**: Python, Go, Rust, TypeScript, C#

**Lines**: ~5,350 characters

**Classes**:
- `TodoItem` - 6 methods
- `TodoListManager` - 9 methods

**Helper Functions**: 2 utility functions

**Features**: Task creation, deletion, status tracking, priority handling

---

### simple_web_api.al

**Location**: `/Users/hustlermain/HUSTLER_CONTENT/HSTLR/DEV/AssertLang/examples/simple_web_api.pw`

**Purpose**: REST API patterns

**Features Demonstrated**:
- HTTP request/response classes
- User management
- API routing patterns
- Status codes
- CRUD operations
- Class composition

**Compiles to**: Python, Go, Rust, TypeScript, C#

**Lines**: ~7,535 characters

**Classes**:
- `HttpRequest`
- `HttpResponse`
- `User`
- `ApiServer`

**Route Handlers**: 9 functions (GET, POST, PUT, DELETE operations)

---

## Bug Fix Demonstration Examples

### Optional Types Examples

See `error_handling.pw` and test files for optional type demonstrations.

**Features**:
- Optional return types (`map?`, `string?`, `int?`)
- Null safety
- Optional parameters

**Bug Fixed**: Bug #4 - Optional types support (Session 27)

---

### C-Style For Loops

Available in test files and production examples.

**Features**:
- `for (let i = 0; i < 10; i = i + 1)`
- Range-based iteration
- Index-based array access

**Bug Fixed**: Bug #2 - C-style for loops (Session 24)

---

### While Loops & Break/Continue

Available in test files and `array_and_map_basics.pw`.

**Features**:
- `while (condition) { }`
- `break` statement
- `continue` statement

**Bugs Fixed**:
- Bug #5 - While loops (verified working Session 22)
- Bug #6 - Break/continue (Session 24)

---

## Compilation Status

### Successfully Compiling Examples

All examples compile to all 5 target languages:

| Example | Python | Go | Rust | TypeScript | C# | Notes |
|---------|--------|-------|------|------------|-----|-------|
| `hello-world.pw` | ✅ | ✅ | ✅ | ✅ | ✅ | Minimal example |
| `calculator.pw` | ✅ | ✅ | ✅ | ✅ | ✅ | 19 functions |
| `error_handling.pw` | ✅ | ✅ | ✅ | ✅ | ✅ | Try/catch patterns |
| `array_and_map_basics.pw` | ✅ | ✅ | ✅ | ✅ | ✅ | Safe collections |
| `calculator_cli.pw` | ✅ | ✅ | ✅ | ✅ | ✅ | Classes & state |
| `todo_list_manager.pw` | ✅ | ✅ | ✅ | ✅ | ✅ | CRUD operations |
| `simple_web_api.pw` | ✅ | ✅ | ✅ | ✅ | ✅ | REST patterns |

**Total**: 7 examples × 5 languages = **35 successful compilations**

---

## How to Compile Examples

### Compile Single Example

```bash
# Python
asl build examples/calculator.al --lang python -o calculator.py

# Go
asl build examples/calculator.al --lang go -o calculator.go

# Rust
asl build examples/calculator.al --lang rust -o calculator.rs

# TypeScript
asl build examples/calculator.al --lang typescript -o calculator.ts

# C#
asl build examples/calculator.al --lang csharp -o Calculator.cs
```

### Compile All Examples

```bash
# Test compilation of all examples
for example in examples/*.pw; do
    echo "Testing: $example"
    asl build "$example" --lang python -o /tmp/test.py
    asl build "$example" --lang go -o /tmp/test.go
    asl build "$example" --lang rust -o /tmp/test.rs
    asl build "$example" --lang typescript -o /tmp/test.ts
    asl build "$example" --lang csharp -o /tmp/test.cs
done
```

---

## Example Categories

### By Complexity

**Beginner** (< 100 lines):
- `hello-world.pw` - Minimal example
- `error_handling.pw` - Try/catch basics

**Intermediate** (100-500 lines):
- `calculator.pw` - Multiple functions
- `array_and_map_basics.pw` - Collections

**Advanced** (500+ lines):
- `calculator_cli.pw` - Classes and state
- `todo_list_manager.pw` - Multiple classes
- `simple_web_api.pw` - REST API patterns

### By Feature

**Control Flow**:
- `calculator.pw` - If/else
- `array_and_map_basics.pw` - Loops
- `error_handling.pw` - Try/catch

**Data Structures**:
- `array_and_map_basics.pw` - Arrays and maps
- `todo_list_manager.pw` - Complex data structures

**Object-Oriented**:
- `calculator_cli.pw` - Single class
- `todo_list_manager.pw` - Multiple classes
- `simple_web_api.pw` - Class composition

**Error Handling**:
- `error_handling.pw` - Try/catch/finally

---

## Testing Examples

### Verify Example Compiles

```bash
# Test single example
asl build examples/calculator.al --lang python -o /tmp/test.py && echo "✅ Python OK" || echo "❌ Python FAILED"

# Test all languages for one example
for lang in python go rust typescript csharp; do
    asl build examples/calculator.al --lang $lang -o /tmp/test.$lang && echo "✅ $lang OK" || echo "❌ $lang FAILED"
done
```

### Validate Generated Code

```bash
# Python
python /tmp/test.py

# Go (requires compilation)
go build /tmp/test.go && ./test

# Rust (requires compilation)
rustc /tmp/test.rs && ./test

# TypeScript (requires tsc)
tsc /tmp/test.ts && node /tmp/test.js

# C# (requires dotnet)
dotnet build /tmp/test.cs
```

---

## Bug-to-Example Mapping

### Bugs Fixed and Where to See Them

| Bug # | Description | Example File | Session |
|-------|-------------|--------------|---------|
| #1 | Class compilation | `calculator_cli.pw`, `todo_list_manager.pw` | 21 |
| #2 | C-style for loops | Test files | 24 |
| #3 | Try/catch syntax | `error_handling.pw` | 23 |
| #4 | Optional types | Test files, see `SAFE_PATTERNS.md` | 27 |
| #5 | While loops | Test files, `array_and_map_basics.pw` | 22 |
| #6 | Break/continue | Test files | 24 |
| #7 | Safe map indexing | `array_and_map_basics.pw` | 26 |
| #8 | Array .length | `array_and_map_basics.pw` | 25 |

---

## Additional Resources

### Documentation
- [`docs/PW_LANGUAGE_GUIDE.md`](PW_LANGUAGE_GUIDE.md) - Complete language guide
- [`docs/PW_NATIVE_SYNTAX.md`](PW_NATIVE_SYNTAX.md) - Formal syntax specification
- [`docs/SAFE_PATTERNS.md`](SAFE_PATTERNS.md) - Safe programming patterns
- [`docs/QUICK_REFERENCE.md`](QUICK_REFERENCE.md) - Quick syntax reference

### Example Files
All examples are in: `/Users/hustlermain/HUSTLER_CONTENT/HSTLR/DEV/AssertLang/examples/`

### Running Examples
See the [PW Language Guide](PW_LANGUAGE_GUIDE.md#examples) for detailed instructions on compiling and running examples.

---

**Last Updated**: 2025-10-08 (v2.1.0b3)
**Status**: All examples compile successfully to all 5 languages ✅
**Total Examples**: 7 working examples (15+ including test files)
**Total LOC**: 16,561+ characters of production PW code
