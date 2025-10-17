# Development Guide

**Version**: 2.1.0b3-beta
**Last Updated**: 2025-10-07

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Development Workflow](#development-workflow)
3. [Code Organization](#code-organization)
4. [Testing](#testing)
5. [Documentation](#documentation)
6. [Git Workflow](#git-workflow)
7. [Release Process](#release-process)

---

## Getting Started

### Prerequisites

- Python 3.10+ (for main codebase)
- Node.js 18+ (for Node.js generator/parser)
- Go 1.18+ (for Go generator/parser)
- Rust 1.70+ (for Rust generator/parser)
- .NET 8+ (for C# generator/parser)

### Installation

```bash
# Clone repository
git clone https://github.com/AssertLang/AssertLang.git
cd promptware

# Install Python dependencies
pip install -e .

# Run tests to verify
python3 -m pytest tests/ -v
```

### Project Structure

```
promptware/
├── dsl/                    # Core PW language implementation
│   ├── ir.py              # IR data structures
│   ├── pw_parser.py       # PW → IR parser
│   ├── pw_generator.py    # IR → PW generator
│   ├── type_system.py     # Type system
│   └── validator.py       # IR validator
│
├── language/               # Language generators/parsers
│   ├── python_parser_v2.py
│   ├── python_generator_v2.py
│   ├── nodejs_parser_v2.py
│   ├── nodejs_generator_v2.py
│   ├── go_parser_v2.py
│   ├── go_generator_v2.py
│   ├── rust_parser_v2.py
│   ├── rust_generator_v2.py
│   ├── dotnet_parser_v2.py
│   └── dotnet_generator_v2.py
│
├── promptware/             # CLI and SDK
│   ├── cli.py             # Command-line interface
│   └── sdk.py             # Python SDK
│
├── tests/                  # Test suite
│   ├── test_*.py          # Unit tests
│   ├── integration/       # Integration tests
│   └── debug/             # Debug scripts
│
├── examples/               # Example programs
│   ├── calculator_cli.al
│   ├── todo_list_manager.al
│   └── simple_web_api.al
│
└── docs/                   # Documentation
    ├── AI_AGENT_GUIDE.md  # For AI coding agents
    ├── ARCHITECTURE.md     # System architecture
    ├── DEVELOPMENT.md      # This file
    ├── PW_DSL_2.0_SPEC.md # Language specification
    └── TYPE_SYSTEM.md      # Type system docs
```

---

## Development Workflow

### 1. Plan Your Change

Before writing code:

1. **Check existing docs**:
   ```bash
   cat Current_Work.md        # Current development status
   cat docs/ARCHITECTURE.md   # System architecture
   cat docs/PW_DSL_2.0_SPEC.md  # Language spec
   ```

2. **Check for existing issues**:
   ```bash
   gh issue list
   ```

3. **Create an issue** (if needed):
   ```bash
   gh issue create --title "Add feature X" --body "Description..."
   ```

### 2. Write Tests First (TDD)

**Why TDD?**
- Catches bugs early
- Documents expected behavior
- Ensures code quality
- Prevents regressions

**Example**:

```python
# tests/test_new_feature.py
#!/usr/bin/env python3
"""Test new feature X."""

from dsl.pw_parser import parse_pw

def test_feature_x():
    """Test that feature X works."""
    pw_code = """
function test_feature() -> int {
    return 42;
}
"""
    ir = parse_pw(pw_code)
    assert len(ir.functions) == 1
    assert ir.functions[0].name == "test_feature"
    print("✅ Feature X test passed")
    return True

if __name__ == "__main__":
    passed = test_feature_x()
    exit(0 if passed else 1)
```

**Run the test** (it should fail):
```bash
python3 tests/test_new_feature.py
# ❌ FAIL - Expected behavior not implemented
```

### 3. Implement the Feature

```python
# dsl/pw_parser.py
def parse_feature_x(self):
    """Parse feature X."""
    # Implementation here
    pass
```

**Run the test again** (it should pass):
```bash
python3 tests/test_new_feature.py
# ✅ PASS - Feature working!
```

### 4. Update Documentation

```bash
# Update relevant documentation
vim Current_Work.md        # Add to "Completed" section
vim CHANGELOG.md           # Add to "Unreleased" section
vim docs/PW_DSL_2.0_SPEC.md  # If language syntax changed
```

### 5. Commit Your Changes

```bash
# Stage changes
git add tests/test_new_feature.py dsl/pw_parser.py Current_Work.md

# Commit with descriptive message
git commit -m "feat: Add feature X (1 test passing)

- Implements feature X in parser
- Adds test coverage
- Updates documentation

Closes #123"
```

---

## Code Organization

### Adding a New Language Feature

When adding a feature to PW language:

1. **Update IR** (`dsl/ir.py`):
```python
@dataclass
class IRNewFeature(IRNode):
    """New feature node."""
    field1: str
    field2: int
```

2. **Update Parser** (`dsl/pw_parser.py`):
```python
def parse_new_feature(self) -> IRNewFeature:
    """Parse new feature from tokens."""
    # Parsing logic
    return IRNewFeature(field1=..., field2=...)
```

3. **Update ALL Generators** (`language/*_generator_v2.py`):
```python
# Python generator
def generate_new_feature(self, node: IRNewFeature) -> str:
    return f"# Python code for {node.field1}"

# Go generator
def generate_new_feature(self, node: IRNewFeature) -> str:
    return f"// Go code for {node.field1}"

# ... (Rust, TypeScript, C#)
```

4. **Write Tests**:
```python
def test_new_feature_parsing():
    """Test parsing new feature."""
    pw_code = "..."
    ir = parse_pw(pw_code)
    # Assertions

def test_new_feature_python_generation():
    """Test Python generation."""
    # Test code

def test_new_feature_go_generation():
    """Test Go generation."""
    # Test code
```

### Adding a New Target Language

1. **Create Parser** (`language/mylang_parser_v2.py`):
```python
class MyLangParserV2:
    def parse_file(self, file_path: str) -> IRModule:
        """Parse MyLang → IR."""
        pass
```

2. **Create Generator** (`language/mylang_generator_v2.py`):
```python
class MyLangGeneratorV2:
    def generate(self, ir: IRModule) -> str:
        """Generate IR → MyLang."""
        pass
```

3. **Add Type Mapping** (`dsl/type_system.py`):
```python
TYPE_MAPPINGS["mylang"] = {
    "string": "String",
    "int": "Integer",
    "float": "Float",
    "bool": "Boolean",
    "null": "Null",
    "array": "Array",
    "map": "Map",
    "any": "Any"
}
```

4. **Update CLI** (`promptware/cli.py`):
```python
build_parser.add_argument(
    '--lang',
    choices=['python', 'go', 'rust', 'typescript', 'csharp', 'mylang']
)
```

5. **Write Tests**:
```python
# tests/test_mylang_generator_v2.py
def test_mylang_function_generation():
    """Test MyLang function generation."""
    pass
```

---

## Testing

### Test Organization

```
tests/
├── Unit Tests (Parser, IR, Generators)
│   ├── test_pw_parser.py
│   ├── test_type_system.py
│   ├── test_python_generator_v2.py
│   ├── test_go_generator_v2.py
│   └── ...
│
├── Feature Tests (Specific features)
│   ├── test_type_validation.py
│   ├── test_for_loops.py
│   ├── test_while_loops.py
│   ├── test_arrays.py
│   ├── test_maps.py
│   └── test_classes.py
│
├── Integration Tests (End-to-end)
│   ├── integration/test_cross_language.py
│   ├── integration/test_real_world.py
│   └── test_round_trip.py
│
└── Debug Scripts (Development aids)
    └── debug/*.py
```

### Running Tests

```bash
# All tests
python3 -m pytest tests/ -v

# Specific test file
python3 tests/test_for_loops.py

# Specific test function
python3 -m pytest tests/test_for_loops.py::test_basic_for_loop -v

# With coverage
python3 -m pytest tests/ --cov=dsl --cov=language --cov-report=html

# Integration tests only
python3 -m pytest tests/integration/ -v

# Fast tests only (exclude slow integration tests)
python3 -m pytest tests/ -v -m "not slow"
```

### Writing Good Tests

**1. Clear Test Names**:
```python
# ✅ Good
def test_for_loop_with_enumerate_pattern():
    """Test for loop using enumerate(items) pattern."""
    pass

# ❌ Bad
def test_feature():
    """Test."""
    pass
```

**2. Arrange-Act-Assert Pattern**:
```python
def test_type_checking():
    # Arrange
    pw_code = """
function add(x: int, y: int) -> int {
    return x + y;
}
"""

    # Act
    ir = parse_pw(pw_code)

    # Assert
    assert len(ir.functions) == 1
    assert ir.functions[0].name == "add"
```

**3. Test Both Success and Failure**:
```python
def test_type_validation_success():
    """Test valid type usage."""
    pw_code = 'function f() -> int { return 42; }'
    ir = parse_pw(pw_code)
    # Should not raise

def test_type_validation_failure():
    """Test invalid type usage."""
    pw_code = 'function f() -> int { return "string"; }'
    try:
        ir = parse_pw(pw_code)
        assert False, "Should have raised type error"
    except Exception as e:
        assert "type mismatch" in str(e).lower()
```

**4. Print Progress**:
```python
def test_feature():
    """Test feature."""
    print("Testing feature...")
    # Test code
    print("✅ Feature test passed")
    return True
```

---

## Documentation

### Documentation Standards

1. **Update Current_Work.md after every significant change**
2. **Update CHANGELOG.md when adding features/fixes**
3. **Document breaking changes clearly**
4. **Include code examples in docs**
5. **Keep README.md up to date**

### Documentation Files

| File | Purpose | Update Frequency |
|------|---------|------------------|
| `README.md` | Public overview | When features change |
| `CHANGELOG.md` | Version history | Every release |
| `Current_Work.md` | Development status | Every session |
| `docs/AI_AGENT_GUIDE.md` | For AI agents | When workflow changes |
| `docs/ARCHITECTURE.md` | System design | When architecture changes |
| `docs/PW_DSL_2.0_SPEC.md` | Language spec | When syntax changes |
| `docs/TYPE_SYSTEM.md` | Type system | When types change |
| `docs/DEVELOPMENT.md` | This file | When dev process changes |

### Code Comments

```python
# ✅ Good comments (explain WHY)
# We check peek() is not empty because '' in ' \t' returns True in Python
while self.peek() and self.peek() in " \t\r":
    self.advance()

# ❌ Bad comments (explain WHAT - code is self-documenting)
# Advance while whitespace
while self.peek() and self.peek() in " \t\r":
    self.advance()
```

### Docstrings

```python
def parse_function(self) -> IRFunction:
    """Parse function definition.

    Syntax:
        function NAME(PARAMS) -> RETURN_TYPE {
            BODY
        }

    Returns:
        IRFunction with parsed name, params, return type, and body

    Raises:
        PWParseError: If syntax is invalid

    Example:
        >>> parse_function('function add(x: int, y: int) -> int { return x + y; }')
        IRFunction(name='add', params=[...], ...)
    """
    pass
```

---

## Git Workflow

### Branch Strategy

- `main` - Production-ready code
- `raw-code-parsing` - V2 universal translation system (current development)
- Feature branches - For specific features (optional)

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Adding/updating tests
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `chore`: Build/tooling changes

**Examples**:

```bash
# Feature with tests
git commit -m "feat(parser): Add while loop support (6 tests passing)

- Implements while loop parsing
- Adds type validation for while conditions
- Updates all generators

Closes #45"

# Bug fix
git commit -m "fix(parser): Prevent infinite loop on trailing whitespace

Root cause: '' in ' \t' returns True in Python
Solution: Check peek() is not empty before membership test

Fixes #123"

# Documentation
git commit -m "docs: Update AI agent guide with v2.1 features"
```

### Pull Request Process

1. **Create PR with comprehensive description**:
```bash
gh pr create --repo AssertLang/AssertLang \
  --base main --head raw-code-parsing \
  --title "feat: v2.1.0b3-beta - Production Ready" \
  --body "$(cat pr_template.md)"
```

2. **PR should include**:
   - Summary of changes
   - Test results
   - Breaking changes (if any)
   - Migration guide (if needed)
   - Screenshots/examples (if applicable)

3. **Wait for CI/CD to pass**
4. **Address review comments**
5. **Merge when approved**

---

## Release Process

### Version Numbering

Follow [Semantic Versioning](https://semver.org/):

- **MAJOR** (v3.0.0): Breaking changes
- **MINOR** (v2.1.0b3): New features (backward compatible)
- **PATCH** (v2.1.1): Bug fixes (backward compatible)
- **Beta** (v2.1.0b3-beta): Pre-release testing

### Release Checklist

#### 1. Pre-Release Testing

```bash
# Run full test suite
python3 -m pytest tests/ -v

# Run integration tests
python3 -m pytest tests/integration/ -v

# Test CLI commands
asl build examples/calculator_cli.al --lang python
asl compile examples/calculator_cli.al
promptware run examples/calculator_cli.al
```

#### 2. Update Documentation

```bash
# Update CHANGELOG.md
vim CHANGELOG.md  # Add release notes

# Update version numbers
vim setup.py  # version="2.1.0b3"
vim promptware/__init__.py  # __version__ = "2.1.0b3"

# Create release summary
vim RELEASE_SUMMARY_v2.1.0b3.md
```

#### 3. Commit and Tag

```bash
# Commit all changes
git add .
git commit -m "chore: Release v2.1.0b3

- Update CHANGELOG.md
- Update version numbers
- Add release summary"

# Create annotated tag
git tag -a v2.1.0b3 -m "AssertLang v2.1.0b3 - Production Ready

Major Features:
- Type validation system
- Control flow (for/while loops)
- Data structures (arrays/maps)
- Classes (OOP)
- CLI tools (build/compile/run)

Test Coverage: 99% (105/105 tests)
Production Confidence: 92%"

# Push to repository
git push origin raw-code-parsing
git push origin v2.1.0b3
```

#### 4. Create GitHub Release

```bash
# Create release on GitHub
gh release create v2.1.0b3 \
  --title "v2.1.0b3 - Production Ready" \
  --notes-file RELEASE_SUMMARY_v2.1.0b3.md \
  --latest
```

#### 5. Publish Package (Optional)

```bash
# Build distribution
python3 setup.py sdist bdist_wheel

# Upload to PyPI
twine upload dist/*
```

---

## Best Practices

### Code Quality

1. **Follow PEP 8** (Python style guide)
2. **Use type hints**:
```python
def parse_expression(self, tokens: List[Token]) -> IRExpression:
    pass
```

3. **Keep functions small** (< 50 lines)
4. **Avoid deep nesting** (< 4 levels)
5. **Use descriptive variable names**:
```python
# ✅ Good
user_email = "alice@example.com"

# ❌ Bad
x = "alice@example.com"
```

### Testing

1. **Test edge cases**:
   - Empty input
   - Large input
   - Invalid input
   - Boundary conditions

2. **Test error paths**:
   - Invalid syntax
   - Type mismatches
   - Missing files

3. **Test real-world scenarios**:
   - Complete programs
   - Cross-language translation
   - Round-trip conversion

### Performance

1. **Profile before optimizing**:
```python
import cProfile
cProfile.run('parse_pw(large_file)')
```

2. **Use appropriate data structures**:
   - Lists for sequences
   - Dicts for lookups
   - Sets for uniqueness

3. **Avoid premature optimization**
   - Correctness first
   - Then performance

---

## Debugging

### Common Issues

#### Parser Hangs

```bash
# Add timeout to tests
timeout 10 python3 tests/test_parser.py

# Add debug prints
print(f"Current token: {self.current()}")
print(f"Peek: {self.peek()}")
```

#### Type Errors

```bash
# Print IR structure
print(json.dumps(ir_to_dict(ir), indent=2))

# Trace type checker
print(f"Checking function: {func.name}")
print(f"Type environment: {self.type_env}")
```

#### Generation Errors

```bash
# Compare with working example
diff expected.py actual.py

# Test incrementally
python3 tests/test_python_generator_v2.py::test_simple_function -v
```

### Debug Tools

```bash
# Python debugger
python3 -m pdb tests/test_parser.py

# IPython for interactive testing
ipython
>>> from dsl.pw_parser import parse_pw
>>> ir = parse_pw("function f() {}")
>>> ir.functions[0]
```

---

## Resources

### Internal Documentation

- [Architecture](ARCHITECTURE.md) - System design
- [AI Agent Guide](AI_AGENT_GUIDE.md) - For AI coding agents
- [PW Language Spec](PW_DSL_2.0_SPEC.md) - Complete language specification
- [Type System](TYPE_SYSTEM.md) - Type system details

### External Resources

- [Python AST](https://docs.python.org/3/library/ast.html)
- [LLVM IR](https://llvm.org/docs/LangRef.html)
- [Compiler Design](https://en.wikipedia.org/wiki/Compiler)
- [Semantic Versioning](https://semver.org/)

---

## Getting Help

### For Code Issues

1. Check `Current_Work.md` for known issues
2. Search existing issues: `gh issue list`
3. Check git history: `git log --grep="keyword"`
4. Ask in discussions: `gh discussion create`

### For Architecture Questions

1. Read `docs/ARCHITECTURE.md`
2. Check example programs in `examples/`
3. Review test files for usage patterns
4. Open a discussion

### Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for:
- Code of conduct
- Pull request process
- Issue templates
- Review guidelines

---

**Last Updated**: 2025-10-07
**Version**: 2.1.0b3-beta
**Maintained By**: AssertLang Development Team
