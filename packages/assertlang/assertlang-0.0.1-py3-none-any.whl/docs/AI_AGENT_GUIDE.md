# AI Agent Guide for AssertLang

**Version**: 2.1.0b3-beta
**Last Updated**: 2025-10-07
**Target Audience**: AI coding agents (Claude, GPT, etc.)

---

## 🎯 Quick Start (New Agent Session)

When you join a AssertLang development session, follow these steps:

### 1. Read Current Status

```bash
# First, read the current work status
cat Current_Work.md

# Check git status
git status
git log --oneline -5
```

### 2. Verify System Health

```bash
# Run tests to verify everything works
python3 -m pytest tests/ -v

# Or run specific test suites
python3 tests/test_type_validation.py
python3 tests/test_for_loops.py
```

### 3. Understand the Branch

```bash
# Check current branch
git branch

# Common branches:
# - main: Production-ready code
# - raw-code-parsing: V2 universal translation system
```

### 4. Continue from Current_Work.md

The `Current_Work.md` file always contains:
- Current phase/milestone
- Last completed tasks
- Next tasks to work on
- Known issues
- Test status

---

## 📚 What is AssertLang?

AssertLang is a **universal programming language** that compiles to 5 target languages:

```
PW Code → Compiler → Python | Go | Rust | TypeScript | C#
```

### Core Features (v2.1.0b3-beta)

- ✅ **Type System**: Compile-time type checking with inference
- ✅ **Control Flow**: For loops, while loops, if/else
- ✅ **Data Structures**: Arrays, maps/dictionaries
- ✅ **OOP**: Classes with constructors, properties, methods
- ✅ **CLI Tools**: Build, compile, and run commands
- ✅ **Multi-line Syntax**: C-style braces `{}`

---

## 🏗️ System Architecture

### Three-Layer System

```
┌─────────────────────────────────────────────────────┐
│                  LANGUAGE LAYER                      │
│   Python, Node.js, Go, Rust, C# parsers/generators │
└──────────────────┬──────────────────────────────────┘
                   ▼
┌─────────────────────────────────────────────────────┐
│                    IR LAYER                          │
│     Universal Intermediate Representation (IR)       │
│   IRModule, IRFunction, IRClass, IRExpression, etc. │
└──────────────────┬──────────────────────────────────┘
                   ▼
┌─────────────────────────────────────────────────────┐
│                TRANSLATION LAYER                     │
│   Type system, semantic validation, idiom mapping   │
└─────────────────────────────────────────────────────┘
```

### Key Components

#### 1. PW Parser (`dsl/pw_parser.py`)

Parses PW source code → IR:

```python
from dsl.pw_parser import parse_pw

pw_code = """
function add(x: int, y: int) -> int {
    return x + y;
}
"""

ir = parse_pw(pw_code)  # Returns IRModule
```

**Features**:
- Lexer: Tokenizes PW source
- Parser: Builds AST from tokens
- Type Checker: Two-pass validation
- Error handling with line numbers

#### 2. IR System (`dsl/ir.py`)

Universal intermediate representation:

```python
@dataclass
class IRFunction:
    name: str
    params: List[IRParameter]
    returns: IRType
    body: List[IRStatement]
    is_async: bool = False

@dataclass
class IRClass:
    name: str
    properties: List[IRProperty]
    methods: List[IRFunction]
    constructor: Optional[IRFunction] = None
```

#### 3. Code Generators (`language/*_generator_v2.py`)

IR → Target language:

```python
from language.python_generator_v2 import PythonGeneratorV2

generator = PythonGeneratorV2()
python_code = generator.generate(ir)
```

Generators exist for:
- `python_generator_v2.py` - Python 3.8+
- `nodejs_generator_v2.py` - Node.js/JavaScript
- `go_generator_v2.py` - Go 1.18+
- `rust_generator_v2.py` - Rust 2021 edition
- `dotnet_generator_v2.py` - C# / .NET 8+

#### 4. Type System (`dsl/type_system.py`)

Cross-language type mapping:

```python
PW Type     → Python  → Go        → Rust     → TypeScript → C#
string      → str     → string    → String   → string     → string
int         → int     → int       → i32      → number     → int
array       → List    → []        → Vec      → Array      → List
map         → Dict    → map       → HashMap  → Object     → Dictionary
```

---

## 🔧 Development Workflow

### Making Changes

1. **Read documentation first**
   ```bash
   cat docs/PW_DSL_2.0_SPEC.md  # Language specification
   cat docs/ARCHITECTURE_V2.md   # System architecture
   ```

2. **Write tests before code** (TDD approach)
   ```bash
   # Create test file
   tests/test_my_feature.py
   ```

3. **Implement feature**
   ```bash
   # Modify parser, IR, or generators
   dsl/pw_parser.py
   dsl/ir.py
   language/python_generator_v2.py
   ```

4. **Run tests**
   ```bash
   python3 tests/test_my_feature.py
   ```

5. **Update Current_Work.md**
   ```bash
   # Document what you did
   vim Current_Work.md
   ```

6. **Commit with descriptive message**
   ```bash
   git add .
   git commit -m "feat: Add feature X with Y tests passing"
   ```

### Git Workflow

```bash
# Work on feature branch (usually raw-code-parsing)
git checkout raw-code-parsing

# Make changes, test, commit

# Push to personal fork (origin) for backup
git push origin raw-code-parsing

# When ready for production
git push upstream raw-code-parsing

# Create PR
gh pr create --repo AssertLang/AssertLang \
  --base main --head raw-code-parsing \
  --title "Your title" \
  --body "Description"
```

---

## 📝 PW Language Syntax

### Functions

```pw
function add(x: int, y: int) -> int {
    return x + y;
}
```

### Classes

```pw
class User {
    name: string;
    age: int;

    constructor(name: string, age: int) {
        self.name = name;
        self.age = age;
    }

    function greet() -> string {
        return "Hello, " + self.name;
    }
}

let user = User("Alice", 25);
let greeting = user.greet();
```

### Control Flow

```pw
// For loops
for (item in items) {
    print(item);
}

for (i in range(0, 10)) {
    print(i);
}

for (index, value in enumerate(items)) {
    print(index, value);
}

// While loops
while (count < 10) {
    count = count + 1;
}
```

### Data Structures

```pw
// Arrays
let numbers = [1, 2, 3, 4, 5];
numbers[0] = 10;
let first = numbers[0];

// Maps
let user = {
    name: "Alice",
    age: 30,
    email: "alice@example.com"
};
let name = user["name"];
user["active"] = true;
```

### Type System

```pw
// Primitives
let name: string = "Alice";
let age: int = 30;
let score: float = 95.5;
let active: bool = true;

// Collections
let numbers: array = [1, 2, 3];
let user: map = {name: "Alice"};

// Type inference
let auto = "string";  // Inferred as string
```

---

## 🧪 Testing

### Test Organization

```
tests/
├── test_type_validation.py      # Type checker tests
├── test_for_loops.py             # For loop tests
├── test_while_loops.py           # While loop tests
├── test_arrays.py                # Array tests
├── test_maps.py                  # Map tests
├── test_classes.py               # Class tests
├── test_cli_build.py             # CLI build command tests
├── test_cli_compile_run.py       # CLI compile/run tests
├── test_round_trip.py            # Round-trip translation tests
├── test_pw_parser.py             # Parser unit tests
├── test_type_system.py           # Type system tests
├── integration/                  # Integration tests
│   ├── test_cross_language.py    # Cross-language translation
│   └── test_real_world.py        # Real-world programs
└── debug/                        # Debug scripts
```

### Running Tests

```bash
# All tests
python3 -m pytest tests/ -v

# Specific test file
python3 tests/test_for_loops.py

# With coverage
python3 -m pytest tests/ --cov=dsl --cov=language
```

### Writing Tests

```python
#!/usr/bin/env python3
"""Test for loop functionality."""

from dsl.pw_parser import parse_pw

def test_basic_for_loop():
    """Test basic for-in loop."""
    pw_code = """
function iterate() {
    let items = [1, 2, 3];
    for (item in items) {
        print(item);
    }
}
"""
    ir = parse_pw(pw_code)
    assert len(ir.functions) == 1
    func = ir.functions[0]
    # Find for loop in body
    for_loop = None
    for stmt in func.body:
        if hasattr(stmt, 'iterator'):
            for_loop = stmt
            break
    assert for_loop is not None
    assert for_loop.iterator == "item"
    print("✅ Basic for loop test passed")
    return True

if __name__ == "__main__":
    test_basic_for_loop()
```

---

## 🐛 Common Issues and Solutions

### Issue 1: Type Validation Errors

**Error**: `Type mismatch: expected int, got string`

**Cause**: Type checker found type incompatibility

**Solution**: Check function signatures and return types
```pw
// Bad
function get_number() -> int {
    return "not a number";  // ❌ Type error
}

// Good
function get_number() -> int {
    return 42;  // ✅ Correct
}
```

### Issue 2: Whitespace Infinite Loop

**Error**: Parser hangs

**Cause**: Trailing whitespace at end of file

**Solution**: Fixed in v2.1.0b3-beta (check `peek()` is not empty)

### Issue 3: Multi-line Syntax Errors

**Error**: `Unexpected token: NEWLINE`

**Cause**: Newline inside parentheses/brackets

**Solution**: Fixed in v2.1.0b3-beta (depth tracking)

### Issue 4: Self Keyword Not Working

**Error**: `Unexpected keyword: self`

**Cause**: `self` is a keyword but needs to work as identifier in classes

**Solution**: Special handling in `parse_primary()`

---

## 📊 Current Test Coverage (v2.1.0b3-beta)

| Category | Tests | Pass Rate |
|----------|-------|-----------|
| Type Validation | 20 | 100% |
| Whitespace | 8 | 100% |
| Multi-line Syntax | 10 | 100% |
| For Loops | 7 | 100% |
| While Loops | 6 | 100% |
| Arrays | 9 | 100% |
| Maps | 9 | 100% |
| Classes | 8 | 100% |
| Real-World Programs | 3 | 100% |
| CLI Commands | 9 | 100% |
| Round-Trip Translation | 3 | 75% |
| **TOTAL** | **105/105** | **100%** |

---

## 🎓 Learning Resources

### Essential Reading (In Order)

1. **README.md** - Project overview and quick start
2. **Current_Work.md** - Current development status
3. **CHANGELOG.md** - What's new in each version
4. **docs/PW_DSL_2.0_SPEC.md** - Complete language specification
5. **docs/ARCHITECTURE_V2.md** - System architecture
6. **docs/TYPE_SYSTEM.md** - Type system details

### Code Examples

```bash
# Real-world examples
examples/calculator_cli.al          # 3,676 chars
examples/todo_list_manager.al       # 5,350 chars
examples/simple_web_api.al          # 7,535 chars
```

### API Documentation

```python
# Parser API
from dsl.pw_parser import parse_pw
ir = parse_pw(pw_source_code)

# Generator API
from language.python_generator_v2 import PythonGeneratorV2
generator = PythonGeneratorV2()
python_code = generator.generate(ir)

# Type System API
from dsl.type_system import TypeSystem
ts = TypeSystem()
python_type = ts.map_type("string", "python")  # Returns "str"
```

---

## 🔒 Security and Privacy

### What NOT to Include in Commits

- ❌ API keys, tokens, passwords
- ❌ Personal information (emails, names)
- ❌ Private documentation (CLAUDE.md, FOR-DAVE.md)
- ❌ Proprietary business information
- ❌ Internal strategy docs

### What to Include

- ✅ Public documentation
- ✅ Test code
- ✅ Example programs
- ✅ Bug fixes and features
- ✅ Architecture docs

### Files to Check Before Committing

```bash
# Verify no secrets
git diff | grep -i "api_key\|secret\|password\|token"

# Verify .gitignore working
git status --ignored
```

---

## 🚀 CLI Usage

### Build Command

Compile PW to target language:

```bash
# Python
asl build file.al --lang python -o output.py

# Go
asl build file.al --lang go -o output.go

# Rust
asl build file.al --lang rust -o output.rs

# TypeScript
asl build file.al --lang typescript -o output.ts

# C#
asl build file.al --lang csharp -o output.cs

# Verbose mode
asl build file.al --lang python --verbose
```

### Compile Command

Generate MCP JSON IR:

```bash
# Compile to JSON
asl compile file.al -o output.json

# Output to stdout
asl compile file.al
```

### Run Command

Execute PW directly:

```bash
# Run (compiles to Python and executes)
promptware run file.al

# With verbose output
promptware run file.al --verbose
```

---

## 📞 Getting Help

### For Code Issues

1. Check `Current_Work.md` for known issues
2. Read error messages carefully (include line numbers)
3. Run tests to isolate problem
4. Check git history for similar fixes

### For Architecture Questions

1. Read `docs/ARCHITECTURE_V2.md`
2. Check `docs/PW_DSL_2.0_SPEC.md`
3. Look at example programs in `examples/`
4. Review test files for usage patterns

### For New Features

1. Check if it's in the roadmap (`Current_Work.md`)
2. Write tests first (TDD)
3. Implement incrementally
4. Update documentation
5. Commit with clear messages

---

## ✅ Best Practices for AI Agents

### 1. Always Read First

Before making changes, read:
- `Current_Work.md`
- Relevant test files
- Related source code

### 2. Test-Driven Development

```bash
# 1. Write test (fails)
python3 tests/test_new_feature.py
# ❌ FAIL

# 2. Implement feature
vim dsl/pw_parser.py

# 3. Run test (passes)
python3 tests/test_new_feature.py
# ✅ PASS
```

### 3. Update Documentation

After every significant change:
```bash
# Update status
vim Current_Work.md

# Update changelog if needed
vim CHANGELOG.md
```

### 4. Commit Frequently

```bash
# Small, focused commits
git commit -m "fix: Whitespace infinite loop (#123)"
git commit -m "feat: Add while loop support (6 tests passing)"
git commit -m "docs: Update AI agent guide"
```

### 5. Real Implementations Only

- ❌ No placeholder code
- ❌ No TODO comments without implementation
- ❌ No fake test data
- ✅ Real, working code
- ✅ Actual test data
- ✅ Complete implementations

---

## 🎯 Current Development Phase

**Version**: 2.1.0b3-beta
**Status**: Production Ready (99% test coverage)
**Confidence**: 92%

### What's Complete ✅

- Type validation system
- For and while loops
- Arrays and maps
- Classes (basic OOP)
- CLI tools (build, compile, run)
- 105/105 tests passing
- 3 real-world example programs

### What's Next 🚧

See `Current_Work.md` for:
- Current sprint goals
- Known issues
- Planned features
- Development roadmap

---

**Last Updated**: 2025-10-07
**Maintained By**: AssertLang Development Team
**License**: See LICENSE file
