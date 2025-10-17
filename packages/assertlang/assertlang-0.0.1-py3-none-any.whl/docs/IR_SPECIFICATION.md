# AssertLang Intermediate Representation (IR) Specification

**Version**: 2.0.0-alpha
**Last Updated**: 2025-10-04
**Status**: Foundation Complete

---

## Table of Contents

1. [Overview](#overview)
2. [Design Principles](#design-principles)
3. [Node Types](#node-types)
4. [Type System](#type-system)
5. [Expressions](#expressions)
6. [Statements](#statements)
7. [Functions and Classes](#functions-and-classes)
8. [Modules](#modules)
9. [Metadata and Source Locations](#metadata-and-source-locations)
10. [Validation](#validation)
11. [Examples](#examples)
12. [Design Decisions](#design-decisions)

---

## Overview

The AssertLang IR (Intermediate Representation) is a language-agnostic, type-safe representation of program structure. It serves as the universal bridge between all programming languages supported by AssertLang.

### Purpose

The IR enables:
- **Universal code translation**: Any language → IR → Any language
- **Semantic preservation**: Business logic and type information intact
- **Language independence**: No bias toward source or target language
- **Analyzability**: Easy to verify, optimize, and transform

### Architecture

```
┌──────────────────────────────────────────────────────────┐
│  Source Code (Python/Go/Rust/.NET/Node.js)              │
└─────────────────┬────────────────────────────────────────┘
                  │
                  ▼
┌──────────────────────────────────────────────────────────┐
│  Language-Specific Parser                                │
│  (Extracts AST, types, semantics)                       │
└─────────────────┬────────────────────────────────────────┘
                  │
                  ▼
┌──────────────────────────────────────────────────────────┐
│  PROMPTWARE IR (Language-Agnostic)                      │
│  ┌────────────────────────────────────────────────────┐ │
│  │ Modules, Functions, Classes, Types                 │ │
│  │ Control Flow (if/for/while/try)                   │ │
│  │ Expressions (calls, operations, literals)          │ │
│  │ Metadata (source location, comments)               │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────┬────────────────────────────────────────┘
                  │
                  ▼
┌──────────────────────────────────────────────────────────┐
│  Language-Specific Generator                             │
│  (Produces idiomatic code)                              │
└─────────────────┬────────────────────────────────────────┘
                  │
                  ▼
┌──────────────────────────────────────────────────────────┐
│  Target Code (Python/Go/Rust/.NET/Node.js)              │
└──────────────────────────────────────────────────────────┘
```

---

## Design Principles

The AssertLang IR follows these core principles, inspired by LLVM and MLIR:

### 1. Language Agnostic

The IR does not favor any source or target language. Python decorators, Go interfaces, Rust traits, and .NET attributes are all represented in a universal way.

### 2. Type Safe

All nodes preserve type information. This enables:
- Static type checking in IR
- Type inference for dynamic languages
- Correct type mapping across languages

### 3. SSA-Friendly (Future)

While not strictly SSA (Static Single Assignment) in v1, the IR is designed to support SSA transformation for optimization.

### 4. Metadata Rich

Every node can carry metadata:
- Source location (file, line, column)
- Comments and documentation
- Annotations and directives

### 5. Composable

IR nodes nest cleanly. A function contains statements, statements contain expressions, expressions contain subexpressions.

### 6. Validatable

The IR includes a semantic validator that catches errors before code generation:
- Type consistency
- Reference validity (variables defined before use)
- Control flow correctness (break/continue only in loops)
- Structural integrity

---

## Node Types

All IR nodes inherit from `IRNode` base class:

```python
class IRNode:
    type: NodeType          # Node type enum
    metadata: Dict[str, Any]  # Metadata (location, comments, etc.)
```

### Node Type Hierarchy

```
IRNode (base)
├── Module-Level Nodes
│   ├── IRModule
│   └── IRImport
│
├── Type Nodes
│   ├── IRType
│   ├── IRTypeDefinition
│   ├── IREnum
│   └── IREnumVariant
│
├── Function/Class Nodes
│   ├── IRFunction
│   ├── IRParameter
│   ├── IRClass
│   └── IRProperty
│
├── Statement Nodes
│   ├── IRIf
│   ├── IRFor
│   ├── IRWhile
│   ├── IRTry / IRCatch
│   ├── IRAssignment
│   ├── IRReturn
│   ├── IRThrow
│   ├── IRBreak
│   ├── IRContinue
│   └── IRPass
│
└── Expression Nodes
    ├── IRCall
    ├── IRBinaryOp
    ├── IRUnaryOp
    ├── IRLiteral
    ├── IRIdentifier
    ├── IRPropertyAccess
    ├── IRIndex
    ├── IRLambda
    ├── IRArray
    ├── IRMap
    └── IRTernary
```

---

## Type System

### IRType

`IRType` represents type references in the IR:

```python
@dataclass
class IRType(IRNode):
    name: str                          # Type name
    generic_args: List[IRType]         # Generic arguments
    is_optional: bool                  # T?
    union_types: List[IRType]          # A|B|C
```

### Primitive Types

| IR Type | Python | Go | Rust | .NET | Node.js |
|---------|--------|-----|------|------|---------|
| `string` | `str` | `string` | `String` | `string` | `string` |
| `int` | `int` | `int` | `i32` | `int` | `number` |
| `float` | `float` | `float64` | `f64` | `double` | `number` |
| `bool` | `bool` | `bool` | `bool` | `bool` | `boolean` |
| `null` | `None` | `nil` | `None` | `null` | `null` |
| `any` | `Any` | `interface{}` | `Box<dyn Any>` | `object` | `any` |

### Collection Types

| IR Type | Python | Go | Rust | .NET | Node.js |
|---------|--------|-----|------|------|---------|
| `array<T>` | `List[T]` | `[]T` | `Vec<T>` | `List<T>` | `Array<T>` |
| `map<K,V>` | `Dict[K,V]` | `map[K]V` | `HashMap<K,V>` | `Dictionary<K,V>` | `Map<K,V>` |

### Optional Types

```python
# IR
age: int?

# Maps to:
# Python: age: Optional[int]
# Go: age *int
# Rust: age: Option<i32>
# .NET: age: int?
# Node.js: age: number | null
```

### Union Types

```python
# IR
result: Success|Error

# Maps to:
# Python: result: Union[Success, Error]
# Go: result interface{} (with type assertion)
# Rust: result: Result<Success, Error>
# .NET: result: object (discriminated union)
# TypeScript: result: Success | Error
```

### Custom Types

```python
@dataclass
class IRTypeDefinition(IRNode):
    name: str
    fields: List[IRProperty]
    doc: Optional[str]
```

Example:

```python
IRTypeDefinition(
    name="User",
    fields=[
        IRProperty(name="id", prop_type=IRType(name="string")),
        IRProperty(name="email", prop_type=IRType(name="string")),
        IRProperty(name="age", prop_type=IRType(name="int", is_optional=True))
    ]
)
```

### Enums

```python
@dataclass
class IREnum(IRNode):
    name: str
    variants: List[IREnumVariant]
```

Example:

```python
IREnum(
    name="Status",
    variants=[
        IREnumVariant(name="pending"),
        IREnumVariant(name="completed"),
        IREnumVariant(name="failed")
    ]
)
```

---

## Expressions

Expressions produce values. All expressions are `IRExpression` type alias.

### Literals

```python
@dataclass
class IRLiteral(IRNode):
    value: Union[str, int, float, bool, None]
    literal_type: LiteralType  # STRING, INTEGER, FLOAT, BOOLEAN, NULL
```

Examples:

```python
IRLiteral(value="hello", literal_type=LiteralType.STRING)
IRLiteral(value=42, literal_type=LiteralType.INTEGER)
IRLiteral(value=3.14, literal_type=LiteralType.FLOAT)
IRLiteral(value=True, literal_type=LiteralType.BOOLEAN)
IRLiteral(value=None, literal_type=LiteralType.NULL)
```

### Identifiers

```python
@dataclass
class IRIdentifier(IRNode):
    name: str  # Variable/function name
```

### Binary Operations

```python
@dataclass
class IRBinaryOp(IRNode):
    op: BinaryOperator  # +, -, *, /, ==, !=, <, >, and, or, etc.
    left: IRExpression
    right: IRExpression
```

Supported operators:

- **Arithmetic**: `+`, `-`, `*`, `/`, `%`, `**`
- **Comparison**: `==`, `!=`, `<`, `<=`, `>`, `>=`
- **Logical**: `and`, `or`
- **Bitwise**: `&`, `|`, `^`, `<<`, `>>`
- **Membership**: `in`, `not in`
- **Identity**: `is`, `is not`

### Unary Operations

```python
@dataclass
class IRUnaryOp(IRNode):
    op: UnaryOperator  # not, -, +, ~
    operand: IRExpression
```

### Function Calls

```python
@dataclass
class IRCall(IRNode):
    function: IRExpression  # Usually IRIdentifier or IRPropertyAccess
    args: List[IRExpression]
    kwargs: Dict[str, IRExpression]
```

Example:

```python
# database.get_user(user_id, cached=True)
IRCall(
    function=IRPropertyAccess(
        object=IRIdentifier(name="database"),
        property="get_user"
    ),
    args=[IRIdentifier(name="user_id")],
    kwargs={"cached": IRLiteral(value=True, literal_type=LiteralType.BOOLEAN)}
)
```

### Property Access

```python
@dataclass
class IRPropertyAccess(IRNode):
    object: IRExpression
    property: str
```

Example: `user.name` → `IRPropertyAccess(object=IRIdentifier("user"), property="name")`

### Array Indexing

```python
@dataclass
class IRIndex(IRNode):
    object: IRExpression
    index: IRExpression
```

Example: `arr[0]` → `IRIndex(object=IRIdentifier("arr"), index=IRLiteral(0))`

### Collections

```python
@dataclass
class IRArray(IRNode):
    elements: List[IRExpression]

@dataclass
class IRMap(IRNode):
    entries: Dict[str, IRExpression]
```

Examples:

```python
# [1, 2, 3]
IRArray(elements=[
    IRLiteral(value=1, literal_type=LiteralType.INTEGER),
    IRLiteral(value=2, literal_type=LiteralType.INTEGER),
    IRLiteral(value=3, literal_type=LiteralType.INTEGER)
])

# {name: "John", age: 30}
IRMap(entries={
    "name": IRLiteral(value="John", literal_type=LiteralType.STRING),
    "age": IRLiteral(value=30, literal_type=LiteralType.INTEGER)
})
```

---

## Statements

Statements perform actions. All statements are `IRStatement` type alias.

### Conditional (If)

```python
@dataclass
class IRIf(IRNode):
    condition: IRExpression
    then_body: List[IRStatement]
    else_body: List[IRStatement]
```

### Loops

```python
@dataclass
class IRFor(IRNode):
    iterator: str
    iterable: IRExpression
    body: List[IRStatement]

@dataclass
class IRWhile(IRNode):
    condition: IRExpression
    body: List[IRStatement]
```

### Exception Handling

```python
@dataclass
class IRTry(IRNode):
    try_body: List[IRStatement]
    catch_blocks: List[IRCatch]
    finally_body: List[IRStatement]

@dataclass
class IRCatch(IRNode):
    exception_type: Optional[str]
    exception_var: Optional[str]
    body: List[IRStatement]
```

### Assignment

```python
@dataclass
class IRAssignment(IRNode):
    target: str
    value: IRExpression
    is_declaration: bool  # let x = ... vs x = ...
    var_type: Optional[IRType]
```

### Return, Throw, Break, Continue

```python
@dataclass
class IRReturn(IRNode):
    value: Optional[IRExpression]

@dataclass
class IRThrow(IRNode):
    exception: IRExpression

@dataclass
class IRBreak(IRNode):
    pass

@dataclass
class IRContinue(IRNode):
    pass
```

---

## Functions and Classes

### Functions

```python
@dataclass
class IRFunction(IRNode):
    name: str
    params: List[IRParameter]
    return_type: Optional[IRType]
    throws: List[str]  # Exception types
    body: List[IRStatement]
    is_async: bool
    is_static: bool
    is_private: bool
    doc: Optional[str]
```

Example:

```python
IRFunction(
    name="process_payment",
    params=[
        IRParameter(name="amount", param_type=IRType(name="float")),
        IRParameter(name="user_id", param_type=IRType(name="string"))
    ],
    return_type=IRType(name="string"),
    throws=["ValidationError", "PaymentError"],
    body=[
        # ... statements ...
        IRReturn(value=IRLiteral("success", LiteralType.STRING))
    ]
)
```

### Classes

```python
@dataclass
class IRClass(IRNode):
    name: str
    properties: List[IRProperty]
    methods: List[IRFunction]
    constructor: Optional[IRFunction]
    base_classes: List[str]
    doc: Optional[str]
```

Example:

```python
IRClass(
    name="PaymentProcessor",
    properties=[
        IRProperty(name="api_key", prop_type=IRType(name="string")),
        IRProperty(name="base_url", prop_type=IRType(name="string"))
    ],
    constructor=IRFunction(
        name="__init__",
        params=[
            IRParameter(name="api_key", param_type=IRType(name="string")),
            IRParameter(name="base_url", param_type=IRType(name="string"))
        ],
        body=[...]
    ),
    methods=[
        IRFunction(name="charge", params=[...], body=[...])
    ]
)
```

---

## Modules

### IRModule

```python
@dataclass
class IRModule(IRNode):
    name: str
    version: str
    imports: List[IRImport]
    types: List[IRTypeDefinition]
    enums: List[IREnum]
    functions: List[IRFunction]
    classes: List[IRClass]
    module_vars: List[IRAssignment]
```

### IRImport

```python
@dataclass
class IRImport(IRNode):
    module: str
    alias: Optional[str]
    items: List[str]
```

Examples:

```python
# import http_client
IRImport(module="http_client")

# import database as db
IRImport(module="database", alias="db")

# from typing import List, Dict
IRImport(module="typing", items=["List", "Dict"])
```

---

## Metadata and Source Locations

### Source Location

```python
@dataclass
class SourceLocation:
    file: Optional[str]
    line: Optional[int]
    column: Optional[int]
    end_line: Optional[int]
    end_column: Optional[int]
```

### Attaching Metadata

All IR nodes have `metadata` dict and convenience properties:

```python
func = IRFunction(name="test", body=[])
func.location = SourceLocation(file="test.py", line=10, column=5)
func.comment = "Test function"
```

---

## Validation

The IR validator checks semantic correctness:

```python
from dsl.validator import validate_ir, ValidationError

try:
    validate_ir(module)
except ValidationError as e:
    print(f"Validation failed: {e}")
```

### What the Validator Checks

1. **Structural integrity**
   - Module has a name
   - Functions/types/enums are defined
   - Required fields present

2. **Type consistency**
   - Type references are valid
   - Generic arguments correct

3. **Scope and references**
   - Variables defined before use
   - Functions defined before call

4. **Control flow**
   - `return` only inside functions
   - `break`/`continue` only inside loops
   - Try/catch structure valid

5. **Uniqueness**
   - No duplicate function/type/class names
   - No duplicate parameter/property names

---

## Examples

### Example 1: Simple Function

**Python Code**:
```python
def add(a: int, b: int) -> int:
    return a + b
```

**IR**:
```python
IRModule(
    name="example",
    functions=[
        IRFunction(
            name="add",
            params=[
                IRParameter(name="a", param_type=IRType(name="int")),
                IRParameter(name="b", param_type=IRType(name="int"))
            ],
            return_type=IRType(name="int"),
            body=[
                IRReturn(
                    value=IRBinaryOp(
                        op=BinaryOperator.ADD,
                        left=IRIdentifier(name="a"),
                        right=IRIdentifier(name="b")
                    )
                )
            ]
        )
    ]
)
```

### Example 2: Class with Method

**Python Code**:
```python
class Counter:
    def __init__(self):
        self.count = 0

    def increment(self):
        self.count = self.count + 1
        return self.count
```

**IR**:
```python
IRModule(
    name="example",
    classes=[
        IRClass(
            name="Counter",
            properties=[
                IRProperty(name="count", prop_type=IRType(name="int"))
            ],
            constructor=IRFunction(
                name="__init__",
                params=[],
                body=[
                    IRAssignment(
                        target="count",
                        value=IRLiteral(value=0, literal_type=LiteralType.INTEGER)
                    )
                ]
            ),
            methods=[
                IRFunction(
                    name="increment",
                    params=[],
                    return_type=IRType(name="int"),
                    body=[
                        IRAssignment(
                            target="count",
                            value=IRBinaryOp(
                                op=BinaryOperator.ADD,
                                left=IRPropertyAccess(
                                    object=IRIdentifier(name="self"),
                                    property="count"
                                ),
                                right=IRLiteral(value=1, literal_type=LiteralType.INTEGER)
                            ),
                            is_declaration=False
                        ),
                        IRReturn(
                            value=IRPropertyAccess(
                                object=IRIdentifier(name="self"),
                                property="count"
                            )
                        )
                    ]
                )
            ]
        )
    ]
)
```

---

## Design Decisions

### Why Not Use AST Directly?

Language-specific ASTs (Python's `ast`, Go's `go/ast`, etc.) are too language-specific. They contain:
- Language quirks and syntactic sugar
- Platform-specific details
- Inconsistent representations

The IR abstracts these away into a universal representation.

### Why Dataclasses?

- Type safety with Python type hints
- Immutability (can use `frozen=True` if needed)
- Automatic `__init__`, `__repr__`, `__eq__`
- Clean syntax
- IDE support

### Why Properties for Metadata?

Convenience. Instead of:
```python
func.metadata["location"] = SourceLocation(...)
```

We can write:
```python
func.location = SourceLocation(...)
```

### Why Not SSA Form?

SSA (Static Single Assignment) is powerful for optimization but adds complexity. For v1, we prioritize:
- Simplicity for parser/generator implementation
- Readability for debugging
- Easy transformation to SSA later if needed

### Future Extensions

Planned for future versions:
- SSA transformation pass
- Control flow graph (CFG)
- Data flow analysis
- Optimization passes
- Type inference engine
- Generic type parameters

---

## Testing

The IR implementation includes comprehensive tests (36 tests, 100% pass rate):

```bash
# Run IR tests
python -m pytest tests/test_ir.py -v
```

Test coverage includes:
- All node types
- Type system
- Expressions and statements
- Functions and classes
- Modules
- Validation (positive and negative cases)
- Metadata
- Complete IR tree construction

---

## Integration

The IR is designed to integrate with:

1. **PW DSL Parser** (`dsl/pw_parser.py`) - PW text → IR
2. **Language Parsers** (`language/*_parser_v2.py`) - Code → IR
3. **Language Generators** (`language/*_generator_v2.py`) - IR → Code
4. **Type System** (`dsl/type_system.py`) - Type inference and mapping

---

## References

1. **LLVM IR**: https://llvm.org/docs/LangRef.html
2. **MLIR**: https://mlir.llvm.org/
3. **CrossTL Paper**: https://arxiv.org/abs/2508.21256 (Universal IR for 8+ languages)
4. **AssertLang CLAUDE.md**: Complete V2 architecture and roadmap

---

**Version**: 2.0.0-alpha
**Status**: Foundation complete, ready for parser/generator implementation
**Last Updated**: 2025-10-04
**Next Steps**: Implement `dsl/pw_parser.py` and `dsl/pw_generator.py`
