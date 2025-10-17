# How to Set Up MCP Server

**Expose AssertLang contracts via Model Context Protocol for Claude Desktop and other AI tools.**

---

## What You'll Learn

- Install and configure MCP server
- Connect Claude Desktop to AssertLang
- Use AssertLang operations from Claude
- Test MCP integration

**Prerequisites**:
- AssertLang installed
- Claude Desktop (for testing)

**Time**: 20 minutes

**Difficulty**: Intermediate

---

## What is MCP?

**Model Context Protocol (MCP)** is an open standard for connecting AI assistants to external tools and data sources.

**Why use MCP with AssertLang?**
- **AI-native** - Claude can parse, validate, and generate contracts directly
- **No REST API needed** - Standard protocol, no custom endpoints
- **Real-time validation** - AI gets instant feedback on contract syntax
- **Multi-language generation** - AI can generate code in any target language

---

## Architecture

```
┌─────────────────┐
│  Claude Desktop │
│                 │
│  "Parse this    │
│   contract..."  │
└────────┬────────┘
         │ MCP Protocol
         │ (stdio/JSON-RPC)
         ▼
┌─────────────────┐
│ AssertLang MCP  │
│    Server       │
│                 │
│  23 Operations  │
│  - parse        │
│  - validate     │
│  - generate     │
│  - explain      │
└─────────────────┘
```

---

## Step 1: Verify Installation

Check that MCP server is installed:

```bash
promptware-mcp-server --version
```

**Expected output**:
```
AssertLang MCP Server 2.2.0
```

**If not found**:
```bash
pip install --upgrade promptware
```

---

## Step 2: Configure Claude Desktop

**Locate config file**:

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

**Edit config** (create if doesn't exist):

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

**With custom settings**:

```json
{
  "mcpServers": {
    "promptware": {
      "command": "promptware-mcp-server",
      "args": ["--debug"],
      "env": {
        "PROMPTWARE_CACHE_DIR": "/tmp/promptware",
        "PROMPTWARE_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

---

## Step 3: Restart Claude Desktop

1. Quit Claude Desktop completely
2. Restart Claude Desktop
3. Wait for MCP server to initialize (~5 seconds)

**Verify connection**:

In Claude chat, type:
```
List available AssertLang operations
```

Claude should respond with 23 available operations.

---

## Step 4: Test Basic Operations

### Test 1: Parse Contract

**Prompt Claude**:
```
Parse this AssertLang contract:

function add(x: int, y: int) -> int {
    @requires positive: x > 0 && y > 0
    @ensures result_positive: result > 0
    return x + y;
}
```

**Claude will**:
1. Call `parse_pw_contract` operation
2. Show parsed IR structure
3. Report success/failure

**Expected response**:
```
✓ Contract parsed successfully

IR Structure:
- Function: add
  - Parameters: x (int), y (int)
  - Return type: int
  - Preconditions: 1 (positive)
  - Postconditions: 1 (result_positive)
  - Body: return statement
```

---

### Test 2: Validate Contract

**Prompt Claude**:
```
Validate this contract and check for issues:

function divide(a: int, b: int) -> int {
    @requires non_zero: b != 0
    return a / b;
}
```

**Claude will**:
1. Call `validate_contract` operation
2. Check syntax and structure
3. Report warnings/suggestions

**Expected response**:
```
✓ Contract is valid

Warnings:
- Missing postcondition: Consider adding result validation
  Suggestion: @ensures result_correct: result == a / b

Contract stats:
- Preconditions: 1
- Postconditions: 0
- Invariants: 0
```

---

### Test 3: Generate Code

**Prompt Claude**:
```
Generate Python code with contracts for:

function sqrt(x: float) -> float {
    @requires non_negative: x >= 0.0
    @ensures non_negative_result: result >= 0.0
    return x ** 0.5;
}
```

**Claude will**:
1. Call `generate_python` operation
2. Return Python code with embedded contracts

**Expected response**:
```python
from promptware.runtime.contracts import check_precondition, check_postcondition

def sqrt(x: float) -> float:
    check_precondition(x >= 0.0, "non_negative", "x >= 0.0", "sqrt",
        context={"x": x})

    __result = x ** 0.5

    check_postcondition(__result >= 0.0, "non_negative_result",
        "result >= 0.0", "sqrt", context={"result": __result})

    return __result
```

---

## Step 5: Advanced Usage

### Multi-Language Generation

**Prompt**:
```
Generate this contract in Python, JavaScript, and Go:

function validate_email(email: string) -> bool {
    @requires non_empty: len(email) > 0
    @requires has_at: "@" in email
    return true;
}
```

**Claude will**:
1. Call `generate_python`
2. Call `generate_javascript`
3. Call `generate_go`
4. Present all three versions

---

### Explain Contract Errors

**Prompt**:
```
Explain this contract error:

ContractViolationError: Precondition 'positive' failed
  Expected: x > 0
  Got: x = -5
```

**Claude will**:
1. Call `explain_contract_error`
2. Provide explanation and fix

**Expected response**:
```
The precondition 'positive' requires that parameter 'x' must be greater
than 0. However, the function was called with x = -5, which violates this
requirement.

Suggestions:
1. Ensure x is positive before calling the function
2. Add validation: if x > 0: call_function(x)
3. Handle negative values separately

Example fix:
if x > 0:
    result = function(x)
else:
    result = function(abs(x))  # Use absolute value
```

---

### Generate Test Cases

**Prompt**:
```
Generate test cases for this contract:

function calculate_discount(price: float, percent: float) -> float {
    @requires price_positive: price > 0.0
    @requires valid_percent: percent >= 0.0 && percent <= 100.0
    @ensures result_non_negative: result >= 0.0
    @ensures result_less_than_price: result <= price
    return price * (percent / 100.0);
}
```

**Claude will**:
1. Call `generate_test_cases`
2. Return pytest-compatible tests

---

## Available MCP Operations

### Core Operations (3)
- `parse_pw_contract` - Parse PW → IR JSON
- `validate_contract` - Check correctness
- `explain_contract` - Plain English explanation

### Code Generation (5)
- `generate_python` - Generate Python code
- `generate_javascript` - Generate JavaScript code
- `generate_go` - Generate Go code
- `generate_rust` - Generate Rust code
- `generate_typescript` - Generate TypeScript code

### Validation (4)
- `check_syntax` - Validate PW syntax
- `check_preconditions` - Verify preconditions
- `check_postconditions` - Verify postconditions
- `check_invariants` - Verify invariants

### Testing (3)
- `run_contract_tests` - Execute test suite
- `generate_test_cases` - Auto-generate tests
- `check_coverage` - Contract test coverage

### Analysis (3)
- `analyze_complexity` - Complexity metrics
- `suggest_contracts` - Suggest missing contracts
- `find_contract_violations` - Find violations

### Debugging (3)
- `explain_contract_error` - Explain error + fix
- `debug_contract` - Debug failing contract
- `trace_contract_check` - Trace execution

---

## Configuration Options

**Server arguments** (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "promptware": {
      "command": "promptware-mcp-server",
      "args": [
        "--debug",           // Enable debug logging
        "--port", "3000",    // Custom port
        "--host", "localhost"  // Bind to specific host
      ],
      "env": {
        "PROMPTWARE_CACHE_DIR": "/tmp/promptware",
        "PROMPTWARE_LOG_LEVEL": "DEBUG",
        "PROMPTWARE_MAX_FILE_SIZE": "5242880"  // 5MB max
      }
    }
  }
}
```

---

## Troubleshooting

### Problem: Claude says "AssertLang operations not available"

**Fixes**:
1. **Verify config location**:
   ```bash
   # macOS
   cat ~/Library/Application\ Support/Claude/claude_desktop_config.json
   ```

2. **Check JSON syntax** (no trailing commas):
   ```json
   {
     "mcpServers": {
       "promptware": {
         "command": "promptware-mcp-server"
       }
     }
   }
   ```

3. **Restart Claude Desktop completely** (Quit → Reopen)

4. **Verify MCP server installed**:
   ```bash
   which promptware-mcp-server
   ```

---

### Problem: MCP server crashes on startup

**Fixes**:
1. **Check logs** (stderr output in Claude Desktop console)

2. **Test server manually**:
   ```bash
   promptware-mcp-server --debug
   ```

3. **Reinstall**:
   ```bash
   pip uninstall promptware
   pip install promptware
   ```

---

### Problem: Operations timeout

**Fixes**:
1. **Increase timeout** in config:
   ```json
   {
     "args": ["--timeout", "60"]
   }
   ```

2. **Simplify contracts** (smaller files parse faster)

3. **Clear cache**:
   ```bash
   rm -rf /tmp/promptware/*
   ```

---

## Integration Examples

### Example 1: Contract Review Workflow

**Prompt**:
```
Review this contract for completeness and suggest improvements:

function transfer_funds(from_account: int, to_account: int, amount: float) -> bool {
    @requires amount_positive: amount > 0.0
    return true;
}
```

**Claude will**:
1. Parse contract
2. Validate structure
3. Analyze completeness
4. Suggest additional contracts

---

### Example 2: Multi-Language Export

**Prompt**:
```
I need this contract in Python and JavaScript with full runtime checks:

function validate_age(age: int) -> bool {
    @requires valid_range: age >= 0 && age <= 120
    return true;
}
```

**Claude will**:
1. Generate Python version
2. Generate JavaScript version
3. Include runtime imports
4. Show usage examples

---

### Example 3: Debug Assistance

**Prompt**:
```
My contract is failing with this error. What's wrong and how do I fix it?

Contract Violation: Postcondition
  Clause: 'result_positive'
  Expression: result > 0
  Got: result = -10
```

**Claude will**:
1. Explain the error
2. Identify the bug
3. Suggest fixes
4. Show corrected code

---

## What You Learned

✅ **MCP setup** - Configure Claude Desktop for AssertLang
✅ **23 operations** - Parse, validate, generate, debug contracts
✅ **AI integration** - Use Claude as contract assistant
✅ **Multi-language** - Generate code in 5 languages via AI

---

## Next Steps

**Advanced MCP usage**:
- Use MCP from Python scripts (not just Claude Desktop)
- Build custom MCP clients
- Integrate with CI/CD

**Related guides**:
- [How-To: Integrate with CrewAI](crewai.md)
- [How-To: Integrate with LangGraph](langgraph.md)

**Learn more**:
- [MCP Operations Reference](../../reference/mcp-operations.md)
- [Contract Syntax](../../reference/contract-syntax.md)

---

## See Also

- **[MCP Operations Reference](../../reference/mcp-operations.md)** - All 23 operations
- **[Runtime API](../../reference/runtime-api.md)** - Contract runtime
- **[CLI Commands](../../reference/cli-commands.md)** - Command-line tools

---

**[← How-To Index](../index.md)** | **[Integrate with CrewAI →](crewai.md)**
