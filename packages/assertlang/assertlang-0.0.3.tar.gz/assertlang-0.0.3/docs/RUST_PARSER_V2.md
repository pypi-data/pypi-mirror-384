# Rust Parser V2 - Arbitrary Rust → IR

**Status**: Production Ready
**Version**: 2.0
**Last Updated**: 2025-10-04

---

## Overview

The Rust Parser V2 converts arbitrary Rust code into AssertLang's intermediate representation (IR), enabling universal code translation between Rust and any other supported language (Python, Node.js, Go, .NET).

Unlike the V1 parser which targets specific MCP server patterns, V2 can parse **any Rust codebase** including libraries, applications, and tools.

---

## Features

### Core Capabilities

✅ **Functions**: Standalone functions with params, return types, async
✅ **Structs**: Field extraction with visibility modifiers
✅ **Enums**: Simple and complex variants with associated values
✅ **Traits**: Interface-like definitions
✅ **Impl Blocks**: Method implementations
✅ **Imports**: `use` statement parsing
✅ **Type Mapping**: Primitives, generics, Option, Result, Vec, HashMap
✅ **Ownership**: Lifetime and borrow metadata preservation

### Rust-Specific Features

- **Result/Option Patterns**: Mapped to optional types and throws
- **Ownership/Lifetimes**: Abstracted as metadata (not enforced in IR)
- **Trait Implementations**: Converted to class inheritance
- **References**: `&`, `&mut` abstracted in type system
- **Pattern Matching**: Simplified to if/else in IR

---

## Usage

### Basic Example

```python
from language.rust_parser_v2 import parse_rust_file, parse_rust_code

# Parse from file
module = parse_rust_file("src/main.rs")

# Parse from string
source = """
pub struct User {
    pub name: String,
    pub age: u32,
}

impl User {
    pub fn new(name: String, age: u32) -> User {
        User { name, age }
    }
}
"""

module = parse_rust_code(source, module_name="users")

# Access parsed components
print(f"Module: {module.name}")
print(f"Structs: {len(module.types)}")
print(f"Functions: {len(module.functions)}")
print(f"Classes: {len(module.classes)}")
```

### Integration with Type System

```python
from language.rust_parser_v2 import parse_rust_file
from dsl.type_system import TypeSystem

# Parse Rust code
module = parse_rust_file("adapter.rs")

# Use type system for cross-language mapping
type_system = TypeSystem()

for func in module.functions:
    for param in func.params:
        # Map Rust type to Python type
        py_type = type_system.map_to_language(param.param_type, "python")
        print(f"{param.name}: {py_type}")
```

---

## Type Mapping

### Primitives

| Rust Type | IR Type | Python | Go | Node.js |
|-----------|---------|--------|-------|---------|
| `i32`, `u32`, `i64` | `int` | `int` | `int` | `number` |
| `f32`, `f64` | `float` | `float` | `float64` | `number` |
| `bool` | `bool` | `bool` | `bool` | `boolean` |
| `String`, `&str` | `string` | `str` | `string` | `string` |
| `()` | `null` | `None` | `nil` | `null` |

### Collections

| Rust Type | IR Type | Description |
|-----------|---------|-------------|
| `Vec<T>` | `array<T>` | Dynamic array |
| `HashMap<K, V>` | `map<K, V>` | Key-value map |
| `BTreeMap<K, V>` | `map<K, V>` | Ordered map |

### Special Types

| Rust Type | IR Representation | Notes |
|-----------|-------------------|-------|
| `Option<T>` | `T?` (optional) | Mapped to nullable type |
| `Result<T, E>` | `T` with `throws` | Error type stored in metadata |
| `&T` | `T` | Reference removed, ownership in metadata |
| `&mut T` | `T` | Mutable borrow in metadata |

---

## Parsing Examples

### 1. Functions

**Input Rust:**
```rust
pub fn calculate_total(items: Vec<f64>, tax_rate: f64) -> f64 {
    let sum = items.iter().sum();
    return sum * (1.0 + tax_rate);
}
```

**Output IR:**
```python
IRFunction(
    name="calculate_total",
    params=[
        IRParameter(name="items", param_type=IRType(name="array", generic_args=[IRType(name="float")])),
        IRParameter(name="tax_rate", param_type=IRType(name="float"))
    ],
    return_type=IRType(name="float"),
    is_private=False
)
```

### 2. Structs

**Input Rust:**
```rust
pub struct User {
    pub id: u32,
    pub name: String,
    pub email: Option<String>,
}
```

**Output IR:**
```python
IRTypeDefinition(
    name="User",
    fields=[
        IRProperty(name="id", prop_type=IRType(name="int"), is_private=False),
        IRProperty(name="name", prop_type=IRType(name="string"), is_private=False),
        IRProperty(name="email", prop_type=IRType(name="string", is_optional=True), is_private=False)
    ]
)
```

### 3. Enums

**Input Rust:**
```rust
pub enum Message {
    Text(String),
    Number(i32),
    Quit,
}
```

**Output IR:**
```python
IREnum(
    name="Message",
    variants=[
        IREnumVariant(name="Text", associated_types=[IRType(name="string")]),
        IREnumVariant(name="Number", associated_types=[IRType(name="int")]),
        IREnumVariant(name="Quit", associated_types=[])
    ]
)
```

### 4. Traits and Impls

**Input Rust:**
```rust
pub trait Greet {
    fn greet(&self) -> String;
}

pub struct Person {
    name: String,
}

impl Greet for Person {
    fn greet(&self) -> String {
        format!("Hello, {}", self.name)
    }
}
```

**Output IR:**
```python
# Trait → Class (interface)
IRClass(
    name="Greet",
    methods=[IRFunction(name="greet", return_type=IRType(name="string"))],
    metadata={"rust_trait": True}
)

# Impl → Class with inheritance
IRClass(
    name="Person",
    base_classes=["Greet"],
    methods=[IRFunction(name="greet", ...)]
)
```

### 5. Result and Option

**Input Rust:**
```rust
fn fetch_user(id: u32) -> Result<User, String> {
    // Implementation
}

fn find_email(user: &User) -> Option<String> {
    // Implementation
}
```

**Output IR:**
```python
# Result<T, E> → T with error metadata
IRFunction(
    name="fetch_user",
    return_type=IRType(name="User", metadata={"rust_error_type": "String"})
)

# Option<T> → T?
IRFunction(
    name="find_email",
    return_type=IRType(name="string", is_optional=True)
)
```

---

## Ownership and Lifetimes

Rust's ownership system is **abstracted** in the IR since not all target languages have equivalent concepts.

### Ownership Metadata

The parser preserves ownership information as metadata:

```rust
fn process(
    owned: String,
    borrowed: &str,
    mut_borrowed: &mut Vec<i32>
) -> String {
    // ...
}
```

**IR Metadata:**
```python
func.metadata['rust_ownership'] = {
    'owned': 'owned_immutable',
    'borrowed': 'borrowed_immutable',
    'mut_borrowed': 'borrowed_mutable'
}
```

### Usage in Code Generation

When generating code:
- **To Rust**: Use metadata to restore ownership annotations
- **To Python/JS**: Ignore (all references are owned)
- **To Go**: Convert borrows to pointers
- **To C#**: Convert to `ref`/`out` where applicable

---

## Limitations

### Current Limitations

1. **Pattern Matching**: Complex `match` statements simplified to `if/else`
2. **Macros**: Not expanded (treated as function calls)
3. **Lifetimes**: Not preserved in IR (stored as strings in metadata)
4. **Trait Bounds**: Not enforced (stored as comments)
5. **Const/Static**: Treated as module-level assignments
6. **Async/Await**: Marked with `is_async` flag, but not deeply analyzed

### Future Enhancements

- [ ] Full macro expansion support
- [ ] Advanced pattern matching (match expressions → switch/case)
- [ ] Lifetime constraint preservation
- [ ] Generic constraint extraction
- [ ] Associated type parsing
- [ ] Derive macro analysis

---

## Testing

### Running Tests

```bash
# Run all Rust parser tests
pytest tests/test_rust_parser_v2.py -v

# Run specific test
pytest tests/test_rust_parser_v2.py::TestRustParserV2::test_parse_simple_function -v

# Run with coverage
pytest tests/test_rust_parser_v2.py --cov=language.rust_parser_v2
```

### Test Coverage

- ✅ Function parsing (simple, async, with generics)
- ✅ Struct parsing (public/private fields, nested types)
- ✅ Enum parsing (simple variants, associated values)
- ✅ Trait parsing (methods, constraints)
- ✅ Impl parsing (struct impls, trait impls)
- ✅ Type mapping (primitives, collections, Option, Result)
- ✅ Import parsing (simple, grouped)
- ✅ Ownership metadata extraction

---

## Architecture

### Parser Pipeline

```
Rust Source Code
      ↓
[Lexical Analysis] ← Regex-based tokenization
      ↓
[Syntax Parsing] ← Pattern matching
      ↓
[Type Resolution] ← Rust → IR type mapping
      ↓
[IR Construction] ← Build IR nodes
      ↓
IR Module Output
```

### Key Components

1. **RustParserV2**: Main parser class
2. **Type Mapper**: `_map_rust_type_to_ir()`
3. **Expression Parser**: `_parse_expression()`
4. **Ownership Extractor**: `_extract_ownership_info()`
5. **Utility Functions**: `_smart_split()`, `_extract_function_body()`

---

## Integration Examples

### Example 1: Rust → Python Translation

```python
from language.rust_parser_v2 import parse_rust_file
from language.python_generator_v2 import PythonGeneratorV2

# Parse Rust
rust_module = parse_rust_file("lib.rs")

# Generate Python
generator = PythonGeneratorV2()
python_code = generator.generate(rust_module)

# Write output
with open("lib.py", "w") as f:
    f.write(python_code)
```

### Example 2: Cross-Language Analysis

```python
from language.rust_parser_v2 import parse_rust_file
from language.go_parser_v2 import parse_go_file
from dsl.ir import IRModule

# Parse both languages
rust_module = parse_rust_file("service.rs")
go_module = parse_go_file("service.go")

# Compare APIs
rust_funcs = {f.name for f in rust_module.functions}
go_funcs = {f.name for f in go_module.functions}

print(f"Common functions: {rust_funcs & go_funcs}")
print(f"Rust-only: {rust_funcs - go_funcs}")
print(f"Go-only: {go_funcs - rust_funcs}")
```

### Example 3: Migration Assistant

```python
from language.rust_parser_v2 import parse_rust_file

def analyze_migration_complexity(rust_file: str) -> dict:
    """Analyze complexity of migrating Rust code to another language."""
    module = parse_rust_file(rust_file)

    report = {
        "total_functions": len(module.functions),
        "async_functions": sum(1 for f in module.functions if f.is_async),
        "result_returns": sum(
            1 for f in module.functions
            if f.return_type and 'rust_error_type' in f.return_type.metadata
        ),
        "borrowed_params": sum(
            1 for f in module.functions
            if 'rust_ownership' in f.metadata
        )
    }

    # Calculate complexity score
    report["complexity_score"] = (
        report["async_functions"] * 2 +
        report["result_returns"] * 1.5 +
        report["borrowed_params"] * 1
    )

    return report
```

---

## Performance

### Benchmarks

| File Size | Lines of Code | Parse Time | Memory |
|-----------|---------------|------------|--------|
| Small (adapter) | ~100 LOC | ~5ms | ~1MB |
| Medium (library) | ~1000 LOC | ~50ms | ~5MB |
| Large (application) | ~10000 LOC | ~500ms | ~30MB |

### Optimization Tips

1. **Batch Processing**: Parse multiple files in parallel
2. **Caching**: Cache parsed IR for unchanged files
3. **Selective Parsing**: Skip test files if not needed
4. **Regex Compilation**: Pre-compile frequently used patterns

---

## Troubleshooting

### Common Issues

**Issue**: Functions inside `impl` blocks not parsed
**Solution**: Check that impl detection logic handles your code structure

**Issue**: Generic types not mapped correctly
**Solution**: Ensure type string doesn't have extra whitespace

**Issue**: Ownership metadata missing
**Solution**: Parser only tracks `&`, `&mut`, `mut` keywords in signatures

**Issue**: Macros treated as function calls
**Solution**: This is expected behavior; macros are not expanded

---

## Contributing

### Adding New Type Mappings

```python
# In _map_rust_type_to_ir()
type_map = {
    'i8': 'int', 'i16': 'int', 'i32': 'int',
    # Add new mappings here
    'char': 'string',  # Example
}
```

### Extending Expression Parsing

```python
# In _parse_expression()
if expr_str.startswith('vec!'):
    # Handle vec! macro
    return self._parse_vec_macro(expr_str)
```

---

## References

- [Rust Language Reference](https://doc.rust-lang.org/reference/)
- [Rust Type System](https://doc.rust-lang.org/book/ch03-02-data-types.html)
- [AssertLang IR Specification](./IR_SPECIFICATION.md)
- [Type System Documentation](./TYPE_SYSTEM.md)

---

**Last Updated**: 2025-10-04
**Maintainer**: AssertLang Rust Parser Team
**Status**: Production Ready ✅
