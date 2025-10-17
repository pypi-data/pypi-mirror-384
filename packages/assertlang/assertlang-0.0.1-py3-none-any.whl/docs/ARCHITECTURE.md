# AssertLang Architecture v2.1.0b3-beta

**Last Updated**: 2025-10-07
**Version**: 2.1.0b3-beta

---

## Overview

AssertLang is a universal programming language compiler that translates PW source code into 5 target languages through a three-layer architecture with a universal intermediate representation (IR).

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER LAYER                               │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  CLI Tool    │  │  IDE Plugin  │  │  API Server  │         │
│  │ (build/run)  │  │  (VS Code)   │  │    (MCP)     │         │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘         │
│         │                  │                  │                  │
└─────────┼──────────────────┼──────────────────┼─────────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                      LANGUAGE LAYER                              │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  PW Parser (dsl/pw_parser.py)                             │ │
│  │  • Lexer: Tokenizes PW source                             │ │
│  │  • Parser: Builds AST from tokens                         │ │
│  │  • Type Checker: Two-pass validation                      │ │
│  │  • Output: IRModule                                       │ │
│  └──────────────────────┬────────────────────────────────────┘ │
│                         │                                        │
│                         ▼                                        │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  Forward Generators                                        │ │
│  │  • python_generator_v2.py → Python 3.8+                   │ │
│  │  • nodejs_generator_v2.py → JavaScript/Node.js            │ │
│  │  • go_generator_v2.py → Go 1.18+                          │ │
│  │  • rust_generator_v2.py → Rust 2021                       │ │
│  │  • dotnet_generator_v2.py → C# / .NET 8+                  │ │
│  │  • Input: IRModule                                        │ │
│  │  • Output: Target language source code                    │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                  │
└──────────────────────────┬───────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                        IR LAYER                                  │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  Core IR (dsl/ir.py)                                       │ │
│  │  • IRModule: Top-level container                          │ │
│  │  • IRFunction: Function definitions                       │ │
│  │  • IRClass: Class definitions                             │ │
│  │  • IRStatement: Control flow (if/for/while)               │ │
│  │  • IRExpression: Operators, calls, literals               │ │
│  │  • IRType: Type information                               │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                  │
└──────────────────────────┬───────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                   TRANSLATION LAYER                              │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  Type System (dsl/type_system.py)                         │ │
│  │  • Cross-language type mapping                            │ │
│  │  • Type inference engine                                  │ │
│  │  • Type validation                                        │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  Semantic Validator (dsl/validator.py)                    │ │
│  │  • IR structure validation                                │ │
│  │  • Semantic correctness checks                            │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  Idiom Translator (dsl/idiom_translator.py)               │ │
│  │  • Language-specific pattern translation                  │ │
│  │  • Decorator ↔ Middleware mapping                         │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Compilation Pipeline

### Forward Compilation (PW → Target Language)

```
┌────────────────┐
│  PW Source     │  function add(x: int, y: int) -> int { return x + y; }
│  (.al file)    │
└────────┬───────┘
         │
         ▼
┌────────────────┐
│  Lexer         │  Tokens: [KEYWORD(function), IDENT(add), LPAREN, ...]
└────────┬───────┘
         │
         ▼
┌────────────────┐
│  Parser        │  AST: FunctionDef(name="add", params=[...], body=[...])
└────────┬───────┘
         │
         ▼
┌────────────────┐
│  Type Checker  │  Validate types, check signatures
└────────┬───────┘
         │
         ▼
┌────────────────┐
│  IR Builder    │  IRFunction(name="add", params=[...], returns=IRType("int"))
└────────┬───────┘
         │
         ▼
┌────────────────┐
│  Code          │  Python:  def add(x: int, y: int) -> int: return x + y
│  Generator     │  Go:      func add(x int, y int) int { return x + y }
│                │  Rust:    fn add(x: i32, y: i32) -> i32 { x + y }
└────────────────┘
```

### CLI Integration

```
$ asl build calculator.al --lang python -o calculator.py

┌─────────────────────────────────────────────┐
│  CLI (promptware/cli.py)                    │
│  • Parse arguments                          │
│  • Call parse_pw(source)                    │
│  • Call generator.generate(ir)              │
│  • Write output file                        │
└─────────────────────────────────────────────┘
```

---

## Core Components

### 1. PW Parser (`dsl/pw_parser.py`)

**Responsibility**: Convert PW source code into IR

**Components**:

#### Lexer
```python
class Lexer:
    """Tokenizes PW source code."""

    def tokenize(self, source: str) -> List[Token]:
        """Convert source string to list of tokens."""
        # Handles:
        # - Keywords (function, class, if, for, while, etc.)
        # - Identifiers (variable names, function names)
        # - Literals (strings, numbers, booleans)
        # - Operators (+, -, *, /, ==, !=, <, >, &&, ||)
        # - Delimiters ((, ), {, }, [, ], ;, ,, :)
        # - Whitespace and comments
```

Key features:
- **Depth tracking**: Tracks nesting of `()`, `[]`, `{}` for multi-line support
- **Whitespace handling**: Skips spaces/tabs but preserves newlines (unless nested)
- **String literals**: Handles single/double quotes with escapes
- **Number parsing**: Int and float literals
- **Operator support**: All arithmetic, comparison, logical operators

#### Parser
```python
class Parser:
    """Builds abstract syntax tree from tokens."""

    def parse(self, tokens: List[Token]) -> IRModule:
        """Parse tokens into IR module."""
        # Recursive descent parser
        # Handles:
        # - Function definitions
        # - Class definitions
        # - Statements (if, for, while, return, assignments)
        # - Expressions (binary ops, calls, indexing, properties)
```

Parsing methods:
- `parse_function()` - Function definitions
- `parse_class()` - Class definitions
- `parse_statement()` - Control flow statements
- `parse_expression()` - Expressions with precedence
- `parse_primary()` - Literals, identifiers, calls

#### Type Checker
```python
class TypeChecker:
    """Two-pass type validation."""

    def check_module(self, module: IRModule) -> None:
        """Type check entire module."""
        # Pass 1: Collect function signatures
        for func in module.functions:
            self.function_signatures[func.name] = (param_types, return_type)

        # Pass 2: Validate function bodies
        for func in module.functions:
            self.check_function(func)
```

Validation rules:
- Return type matches function signature
- Function arguments match parameter types
- Binary operations have compatible types
- Assignments respect type constraints
- Int/float compatibility (int → float allowed)

---

### 2. IR System (`dsl/ir.py`)

**Responsibility**: Universal intermediate representation

**Node Types**:

```python
# Top-level
IRModule          # File/module container
IRFunction        # Function definition
IRClass           # Class definition
IRType            # Type annotation

# Statements
IRIf              # If statement
IRFor             # For loop
IRWhile           # While loop
IRReturn          # Return statement
IRAssignment      # Variable assignment
IRExpressionStmt  # Expression as statement

# Expressions
IRBinaryOp        # Binary operations (+, -, *, /, ==, !=, <, >, &&, ||)
IRUnaryOp         # Unary operations (!, -)
IRCall            # Function calls
IRIndex           # Array/map indexing
IRProperty        # Property access (obj.prop)
IRIdentifier      # Variable references
IRLiteral         # Literal values
IRArray           # Array literals
IRMap             # Map literals

# Class components
IRProperty        # Class property
IRConstructor     # Constructor (special method)
```

**Data Flow**:

```
PW Code → Parser → IRModule → Generator → Target Code
```

Each IR node is immutable and contains:
- Node type (for pattern matching)
- Relevant fields (name, params, body, etc.)
- Metadata (line numbers for errors)

---

### 3. Type System (`dsl/type_system.py`)

**Responsibility**: Cross-language type mapping and inference

**Type Mapping**:

```python
TYPE_MAPPINGS = {
    "python": {
        "string": "str",
        "int": "int",
        "float": "float",
        "bool": "bool",
        "null": "None",
        "array": "List",
        "map": "Dict",
        "any": "Any"
    },
    "go": {
        "string": "string",
        "int": "int",
        "float": "float64",
        "bool": "bool",
        "null": "nil",
        "array": "[]",
        "map": "map",
        "any": "interface{}"
    },
    "rust": {
        "string": "String",
        "int": "i32",
        "float": "f64",
        "bool": "bool",
        "null": "None",
        "array": "Vec",
        "map": "HashMap",
        "any": "Box<dyn Any>"
    },
    # ... (TypeScript, C#)
}
```

**Type Inference**:

```python
# Infer from literal values
"hello" → string
42 → int
3.14 → float
true → bool

# Infer from operations
x + y where x: int, y: int → int
x + y where x: int, y: float → float

# Infer from function calls
add(5, 3) where add(int, int) -> int → int
```

---

### 4. Code Generators (`language/*_generator_v2.py`)

**Responsibility**: IR → Target language source code

**Common Interface**:

```python
class BaseGenerator:
    """Base class for all generators."""

    def generate(self, ir: IRModule) -> str:
        """Generate target language code from IR."""
        raise NotImplementedError

    def generate_function(self, func: IRFunction) -> str:
        """Generate function definition."""
        raise NotImplementedError

    def generate_class(self, cls: IRClass) -> str:
        """Generate class definition."""
        raise NotImplementedError

    def generate_statement(self, stmt: IRStatement) -> str:
        """Generate statement."""
        raise NotImplementedError

    def generate_expression(self, expr: IRExpression) -> str:
        """Generate expression."""
        raise NotImplementedError
```

**Python Generator Example**:

```python
class PythonGeneratorV2:
    def generate_function(self, func: IRFunction) -> str:
        # Function signature
        params = ", ".join(f"{p.name}: {self.map_type(p.type)}"
                          for p in func.params)
        returns = f" -> {self.map_type(func.returns)}" if func.returns else ""

        # Function body
        body = "\n    ".join(self.generate_statement(s) for s in func.body)

        return f"def {func.name}({params}){returns}:\n    {body}"
```

**Language-Specific Adaptations**:

| Feature | Python | Go | Rust | TypeScript | C# |
|---------|--------|-----|------|------------|-----|
| Classes | `class` | `struct + methods` | `struct + impl` | `class` | `class` |
| Arrays | `List[T]` | `[]T` | `Vec<T>` | `T[]` | `List<T>` |
| Maps | `Dict[K,V]` | `map[K]V` | `HashMap<K,V>` | `{[K]: V}` | `Dictionary<K,V>` |
| Self | `self` | `receiver` | `&self` | `this` | `this` |
| Null | `None` | `nil` | `None` | `null` | `null` |

---

### 5. CLI (`promptware/cli.py`)

**Responsibility**: User interface for compilation

**Commands**:

#### `asl build`
```bash
asl build file.al --lang python -o output.py

# Implementation:
1. Read file.al
2. Call parse_pw(source) → IR
3. Select generator based on --lang
4. Call generator.generate(IR) → code
5. Write to output.py (or stdout)
```

#### `asl compile`
```bash
asl compile file.al -o output.json

# Implementation:
1. Read file.al
2. Call parse_pw(source) → IR
3. Convert IR to MCP JSON
4. Write to output.json
```

#### `promptware run`
```bash
promptware run file.al

# Implementation:
1. Read file.al
2. Compile to Python (fastest)
3. Execute with subprocess
```

---

## Data Structures

### IRModule
```python
@dataclass
class IRModule:
    """Top-level IR node representing a PW file."""
    functions: List[IRFunction]
    classes: List[IRClass]
    imports: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
```

### IRFunction
```python
@dataclass
class IRFunction:
    """Function definition."""
    name: str
    params: List[IRParameter]
    return_type: IRType
    body: List[IRStatement]
    is_async: bool = False
    decorators: List[str] = field(default_factory=list)
```

### IRClass
```python
@dataclass
class IRClass:
    """Class definition."""
    name: str
    properties: List[IRProperty]
    methods: List[IRFunction]
    constructor: Optional[IRFunction] = None
    base_classes: List[str] = field(default_factory=list)
```

### IRFor
```python
@dataclass
class IRFor:
    """For loop."""
    iterator: str                    # Variable name
    iterable: IRExpression           # What to iterate
    body: List[IRStatement]          # Loop body
    index_var: Optional[str] = None  # For enumerate: index variable
```

### IRBinaryOp
```python
@dataclass
class IRBinaryOp:
    """Binary operation."""
    op: str           # +, -, *, /, ==, !=, <, >, &&, ||, %
    left: IRExpression
    right: IRExpression
```

---

## Error Handling

### Parse Errors

```python
class PWParseError(Exception):
    """Raised when parsing fails."""
    pass

# Example:
raise PWParseError(f"[Line {line}:{col}] Unexpected token: {token}")
```

Errors include:
- Line and column numbers
- Token that caused error
- Expected vs actual tokens
- Context (what was being parsed)

### Type Errors

```python
# Type checker collects all errors before throwing
self.errors.append(f"[Line {line}] Type mismatch: expected {expected}, got {actual}")

if self.errors:
    raise PWParseError("\n".join(self.errors))
```

### Runtime Errors (Generated Code)

Each generator wraps code in appropriate error handling:
- Python: try/except
- Go: if err != nil
- Rust: Result<T, E>
- TypeScript: try/catch
- C#: try/catch

---

## Performance Considerations

### Parser Performance

- **Linear time**: O(n) where n = source code length
- **Memory**: O(n) for token list + O(m) for IR (m = nodes)
- **Optimization**: Single-pass lexing, recursive descent parsing

### Type Checker Performance

- **Two-pass**: O(2n) ≈ O(n)
- **First pass**: Collect signatures (fast)
- **Second pass**: Validate bodies (can be parallel)

### Generator Performance

- **Linear**: O(m) where m = IR nodes
- **String building**: Uses lists + join() for efficiency
- **No optimization**: Generates readable, not optimized code

### Limits Tested

```python
# Parser stress tests (all passing)
- 500+ nesting levels
- 500+ function parameters
- 1MB+ string literals
- 10,000+ functions in one file
```

---

## Extension Points

### Adding a New Language

1. **Create generator**: `language/mylang_generator_v2.py`
```python
class MyLangGenerator:
    def generate(self, ir: IRModule) -> str:
        # Implement IR → MyLang translation
```

2. **Add type mapping**: `dsl/type_system.py`
```python
TYPE_MAPPINGS["mylang"] = {
    "string": "String",
    "int": "Integer",
    # ...
}
```

3. **Update CLI**: `promptware/cli.py`
```python
build_parser.add_argument(
    '--lang',
    choices=['python', 'go', 'rust', 'typescript', 'csharp', 'mylang']
)
```

4. **Write tests**: `tests/test_mylang_generator.py`

### Adding PW Language Feature

1. **Update spec**: `docs/PW_DSL_2.0_SPEC.md`
2. **Add IR node**: `dsl/ir.py`
3. **Update parser**: `dsl/pw_parser.py`
4. **Update all generators**: `language/*_generator_v2.py`
5. **Write tests**: `tests/test_new_feature.py`

---

## Testing Strategy

### Unit Tests
- Parser: Test each parsing method
- Type Checker: Test each validation rule
- Generators: Test each IR node type
- CLI: Test each command and flag

### Integration Tests
- Round-trip: PW → IR → PW (lossless)
- Cross-language: Python → PW → Go (semantic equivalence)
- Real-world: Full programs compile and run

### Test Organization
```
tests/
├── test_pw_parser.py          # Parser unit tests
├── test_type_system.py         # Type system tests
├── test_python_generator_v2.py # Python generator tests
├── test_go_generator_v2.py     # Go generator tests
├── integration/
│   ├── test_cross_language.py  # Cross-language tests
│   └── test_real_world.py      # Real program tests
└── fixtures/                   # Test data
```

---

## Security

### Input Validation
- Source code size limits (configurable)
- Nesting depth limits (prevent stack overflow)
- Token count limits (prevent memory exhaustion)

### Output Safety
- No arbitrary code execution during compilation
- Generated code is validated (compilable)
- No injection vulnerabilities

### File System
- Validate all file paths (prevent path traversal)
- Sandboxed file writes (only to specified output)
- No arbitrary file reads

---

## Future Architecture Improvements

### Phase V3 (Planned)
1. **Reverse Parsers V2** - Parse arbitrary code in any language → IR
2. **Optimization Passes** - IR-level optimizations
3. **Plugin System** - User-defined transformations
4. **LSP Server** - IDE integration via Language Server Protocol
5. **REPL** - Interactive PW shell

### Scalability
- Parallel type checking (per-function)
- Incremental compilation (only changed files)
- Caching (IR cache, output cache)

---

**Version**: 2.1.0b3-beta
**Status**: Production Ready
**Last Updated**: 2025-10-07
