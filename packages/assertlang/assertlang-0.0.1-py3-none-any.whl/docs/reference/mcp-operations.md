# MCP Operations Reference

**Use AssertLang via Model Context Protocol (MCP) server.**

---

## Overview

AssertLang exposes an MCP server that allows AI assistants (like Claude) to parse contracts, generate code, and validate syntax directly.

**What is MCP?**
- Model Context Protocol - standard for LLM tool integration
- Enables Claude Desktop to call AssertLang operations
- AI-native architecture for contract validation

**Status**:
- Server: ✅ Available (`promptware-mcp-server`)
- Python client: ✅ Complete
- JavaScript client: ✅ Complete
- Operations: 23 available

---

## Quick Start

### Install MCP Server

```bash
pip install promptware

# MCP server included
promptware-mcp-server --version
```

### Configure Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "promptware": {
      "command": "promptware-mcp-server",
      "args": [],
      "env": {}
    }
  }
}
```

### Use in Claude

```
User: Parse this AssertLang contract and check for errors:

function add(x: int, y: int) -> int {
    @requires positive: x > 0
    return x + y;
}

Claude: [Uses parse_pw_contract + validate_contract operations]

✓ Contract is valid
✓ 1 precondition found
✓ 0 postconditions (consider adding result validation)

Suggestion: Add postcondition to validate result
```

---

## Available Operations

### Core Operations

| Operation | Description | Input | Output |
|-----------|-------------|-------|--------|
| `parse_pw_contract` | Parse PW file to IR | PW code (string) | IR JSON |
| `validate_contract` | Check contract correctness | PW code (string) | Validation result |
| `explain_contract` | Explain contract in plain English | PW code (string) | Explanation |

### Code Generation

| Operation | Description | Input | Output |
|-----------|-------------|-------|--------|
| `generate_python` | Generate Python code | PW code (string) | Python code |
| `generate_javascript` | Generate JavaScript code | PW code (string) | JavaScript code |
| `generate_go` | Generate Go code | PW code (string) | Go code |
| `generate_rust` | Generate Rust code | PW code (string) | Rust code |
| `generate_typescript` | Generate TypeScript code | PW code (string) | TypeScript code |

### Validation

| Operation | Description | Input | Output |
|-----------|-------------|-------|--------|
| `check_syntax` | Validate PW syntax | PW code (string) | Syntax errors |
| `check_preconditions` | Verify preconditions | PW code (string) | Precondition analysis |
| `check_postconditions` | Verify postconditions | PW code (string) | Postcondition analysis |
| `check_invariants` | Verify invariants | PW code (string) | Invariant analysis |

### Testing

| Operation | Description | Input | Output |
|-----------|-------------|-------|--------|
| `run_contract_tests` | Execute test suite | PW + test code | Test results |
| `generate_test_cases` | Auto-generate tests | PW code (string) | Test code |
| `check_coverage` | Contract test coverage | PW + tests | Coverage report |

### Analysis

| Operation | Description | Input | Output |
|-----------|-------------|-------|--------|
| `analyze_complexity` | Contract complexity metrics | PW code (string) | Metrics |
| `suggest_contracts` | Suggest missing contracts | PW code (string) | Suggestions |
| `find_contract_violations` | Find potential violations | PW + usage | Violation report |

### Debugging

| Operation | Description | Input | Output |
|-----------|-------------|-------|--------|
| `explain_contract_error` | Explain contract violation | Error message | Explanation + fix |
| `debug_contract` | Debug failing contract | PW + error | Debug info |
| `trace_contract_check` | Trace contract execution | PW + input values | Execution trace |

---

## Operation Details

### parse_pw_contract

**Parse AssertLang code into Intermediate Representation (IR).**

**Request**:
```json
{
  "method": "tools/call",
  "params": {
    "name": "parse_pw_contract",
    "arguments": {
      "code": "function add(x: int, y: int) -> int { @requires positive: x > 0; return x + y; }"
    }
  }
}
```

**Response**:
```json
{
  "success": true,
  "ir": {
    "module": {
      "functions": [
        {
          "name": "add",
          "params": [
            {"name": "x", "type": "int"},
            {"name": "y", "type": "int"}
          ],
          "return_type": "int",
          "requires": [
            {"name": "positive", "expr": "x > 0"}
          ],
          "ensures": [],
          "body": [...]
        }
      ]
    }
  }
}
```

---

### validate_contract

**Validate contract correctness and completeness.**

**Request**:
```json
{
  "method": "tools/call",
  "params": {
    "name": "validate_contract",
    "arguments": {
      "code": "function divide(a: int, b: int) -> int { @requires non_zero: b != 0; return a / b; }"
    }
  }
}
```

**Response**:
```json
{
  "valid": true,
  "errors": [],
  "warnings": [
    {
      "type": "missing_postcondition",
      "message": "Consider adding postcondition to validate result",
      "suggestion": "@ensures result_correct: result == a / b"
    }
  ],
  "stats": {
    "preconditions": 1,
    "postconditions": 0,
    "invariants": 0
  }
}
```

---

### generate_python

**Generate Python code with embedded contracts.**

**Request**:
```json
{
  "method": "tools/call",
  "params": {
    "name": "generate_python",
    "arguments": {
      "code": "function add(x: int, y: int) -> int { @requires positive: x > 0; @ensures result_positive: result > 0; return x + y; }"
    }
  }
}
```

**Response**:
```json
{
  "success": true,
  "language": "python",
  "code": "from promptware.runtime.contracts import check_precondition, check_postcondition\n\ndef add(x: int, y: int) -> int:\n    check_precondition(x > 0, \"positive\", f\"Expected x > 0, got x = {x}\")\n    \n    __result = x + y\n    \n    check_postcondition(__result > 0, \"result_positive\", f\"Expected result > 0, got result = {__result}\")\n    \n    return __result\n"
}
```

---

### check_syntax

**Validate PW syntax without parsing.**

**Request**:
```json
{
  "method": "tools/call",
  "params": {
    "name": "check_syntax",
    "arguments": {
      "code": "function add(x int) -> int { return x + 1 }"
    }
  }
}
```

**Response**:
```json
{
  "valid": false,
  "errors": [
    {
      "line": 1,
      "column": 15,
      "message": "Expected ':' after parameter name",
      "suggestion": "Add type annotation: x: int"
    }
  ]
}
```

---

### explain_contract_error

**Explain a contract violation and suggest fix.**

**Request**:
```json
{
  "method": "tools/call",
  "params": {
    "name": "explain_contract_error",
    "arguments": {
      "error_message": "ContractViolationError: Precondition 'positive' failed\n  Expected: x > 0\n  Got: x = -5"
    }
  }
}
```

**Response**:
```json
{
  "explanation": "The precondition 'positive' requires that the parameter 'x' must be greater than 0. However, the function was called with x = -5, which violates this requirement.",
  "violated_contract": {
    "type": "precondition",
    "name": "positive",
    "condition": "x > 0",
    "actual_value": -5
  },
  "suggestions": [
    "Ensure x is positive before calling the function",
    "Add validation: if x > 0: call_function(x)",
    "Handle negative values separately"
  ],
  "example_fix": "# Before calling:\nif x > 0:\n    result = function(x)\nelse:\n    # Handle negative case\n    result = function(abs(x))"
}
```

---

### run_contract_tests

**Execute contract test suite.**

**Request**:
```json
{
  "method": "tools/call",
  "params": {
    "name": "run_contract_tests",
    "arguments": {
      "contract_code": "function add(x: int, y: int) -> int { @requires positive: x > 0 && y > 0; return x + y; }",
      "test_code": "import pytest\n\ndef test_valid_inputs():\n    assert add(1, 2) == 3\n\ndef test_zero_rejected():\n    with pytest.raises(ContractViolationError):\n        add(0, 1)"
    }
  }
}
```

**Response**:
```json
{
  "success": true,
  "tests_run": 2,
  "tests_passed": 2,
  "tests_failed": 0,
  "coverage": {
    "preconditions_tested": ["positive"],
    "postconditions_tested": [],
    "coverage_percent": 100.0
  },
  "results": [
    {"test": "test_valid_inputs", "status": "passed"},
    {"test": "test_zero_rejected", "status": "passed"}
  ]
}
```

---

## Integration Examples

### Claude Desktop Workflow

```
User: I have this contract but it's failing. Can you help?

function process_order(total: float, discount: float) -> float {
    @requires positive_total: total > 0.0
    @requires valid_discount: discount >= 0.0 && discount <= total

    let final = total - discount;
    return final;
}

Error: ContractViolationError: Precondition 'valid_discount' failed
  Got: discount = 150.0, total = 100.0

Claude: [Uses explain_contract_error operation]

The contract violation occurred because the discount (150.0) exceeds
the total (100.0), which violates the precondition `discount <= total`.

Suggested fix:
1. Validate discount before calling:
   if discount > total:
       discount = total  # Cap discount at total

2. Or add validation in caller:
   discount = min(discount, total)
   result = process_order(total, discount)

Would you like me to generate the fixed code?
```

---

### Python Script Integration

```python
from promptware.mcp import MCPClient

client = MCPClient()

# Parse contract
contract_code = """
function validate_email(email: string) -> bool {
    @requires non_empty: len(email) > 0
    @requires has_at: "@" in email

    @ensures valid_result: result == true || result == false

    return len(email) > 0 && "@" in email;
}
"""

# Validate
result = client.validate_contract(contract_code)
print(f"Valid: {result['valid']}")
print(f"Warnings: {result['warnings']}")

# Generate Python
python_code = client.generate_python(contract_code)
print(python_code)

# Generate JavaScript
js_code = client.generate_javascript(contract_code)
print(js_code)
```

---

### JavaScript Integration

```javascript
const { MCPClient } = require('@promptware/mcp');

const client = new MCPClient();

const contractCode = `
function add(x: int, y: int) -> int {
    @requires positive: x > 0 && y > 0
    @ensures result_positive: result > 0

    return x + y;
}
`;

// Parse and validate
const validation = await client.validateContract(contractCode);
console.log('Valid:', validation.valid);

// Generate code
const pythonCode = await client.generatePython(contractCode);
const jsCode = await client.generateJavaScript(contractCode);

console.log('Python:', pythonCode);
console.log('JavaScript:', jsCode);
```

---

## Error Handling

**All operations return structured errors:**

```json
{
  "success": false,
  "error": {
    "type": "ParseError",
    "message": "Unexpected token at line 5, column 10",
    "line": 5,
    "column": 10,
    "suggestion": "Expected ';' or newline after statement",
    "code_snippet": "    return x + y  // ← Missing semicolon"
  }
}
```

**Error Types**:
- `ParseError` - Syntax error in PW code
- `ValidationError` - Contract validation failed
- `GenerationError` - Code generation failed
- `RuntimeError` - MCP server error

---

## Performance

**Operation latency** (average):
- `parse_pw_contract`: ~10-20ms
- `validate_contract`: ~20-30ms
- `generate_python`: ~30-50ms
- `run_contract_tests`: ~100-500ms (depends on test count)

**Throughput**:
- Parse: ~100 contracts/second
- Generate: ~50 files/second
- Validate: ~80 contracts/second

---

## Configuration

### MCP Server Settings

```json
{
  "mcpServers": {
    "promptware": {
      "command": "promptware-mcp-server",
      "args": ["--debug", "--port", "3000"],
      "env": {
        "PROMPTWARE_CACHE_DIR": "/tmp/promptware",
        "PROMPTWARE_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

**Arguments**:
- `--debug` - Enable debug logging
- `--port <port>` - Custom port (default: auto)
- `--host <host>` - Bind to specific host (default: localhost)

**Environment Variables**:
- `PROMPTWARE_CACHE_DIR` - Cache directory
- `PROMPTWARE_LOG_LEVEL` - Log level (DEBUG, INFO, WARN, ERROR)
- `PROMPTWARE_MAX_FILE_SIZE` - Max PW file size (default: 1MB)

---

## See Also

- **[Contract Syntax](contract-syntax.md)** - Write PW contracts
- **[Runtime API](runtime-api.md)** - Python/JavaScript runtime
- **[CLI Commands](cli-commands.md)** - Command-line tools
- **[MCP Integration Guide](../guides/mcp/integration.md)** - Complete MCP setup guide

---

**[← Runtime API](runtime-api.md)** | **[CLI Commands →](cli-commands.md)**
