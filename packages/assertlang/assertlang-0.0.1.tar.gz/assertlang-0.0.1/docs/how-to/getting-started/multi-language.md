# How to Generate Code for Multiple Languages

**Compile AssertLang contracts to Python, JavaScript, Go, Rust, and TypeScript.**

---

## What You'll Learn

- Generate contracts in 5 different languages
- Understand language-specific output
- Use generated code in each language
- Compare contract implementations

**Prerequisites**: AssertLang installed

**Time**: 15 minutes

**Difficulty**: Beginner

---

## Overview

AssertLang compiles a single `.al` contract to multiple target languages:

| Language | Command | Output | Status |
|----------|---------|--------|--------|
| **Python** | `--lang python` | `.py` | ✅ 100% |
| **JavaScript** | `--lang javascript` | `.js` | ✅ 95% |
| **Go** | `--lang go` | `.go` | ⚠️ 70% |
| **Rust** | `--lang rust` | `.rs` | ⚠️ 60% |
| **TypeScript** | `--lang typescript` | `.ts` | ⚠️ 80% |

---

## Step 1: Create a Contract

Create `user.al`:

```al
function validate_email(email: string) -> bool {
    @requires non_empty: len(email) > 0
    @requires has_at: "@" in email
    @requires has_dot: "." in email

    @ensures valid_result: result == true || result == false

    let valid = len(email) > 0 && "@" in email && "." in email;
    return valid;
}

function create_user(name: string, email: string, age: int) -> bool {
    @requires name_not_empty: len(name) > 0
    @requires email_valid: validate_email(email)
    @requires age_valid: age >= 18 && age <= 120

    @ensures created: result == true

    // User creation logic
    return true;
}
```

---

## Step 2: Generate Python

```bash
asl build user.al --lang python -o user.py
```

**Output** (`user.py`):

```python
from promptware.runtime.contracts import check_precondition, check_postcondition

def validate_email(email: str) -> bool:
    check_precondition(len(email) > 0, "non_empty", "len(email) > 0", "validate_email",
        context={"email": email, "len(email)": len(email)})
    check_precondition("@" in email, "has_at", "\"@\" in email", "validate_email",
        context={"email": email})
    check_precondition("." in email, "has_dot", "\".\" in email", "validate_email",
        context={"email": email})

    valid = len(email) > 0 and "@" in email and "." in email
    __result = valid

    check_postcondition(__result == True or __result == False, "valid_result",
        "result == true || result == false", "validate_email",
        context={"result": __result})

    return __result

def create_user(name: str, email: str, age: int) -> bool:
    check_precondition(len(name) > 0, "name_not_empty", "len(name) > 0", "create_user",
        context={"name": name, "len(name)": len(name)})
    check_precondition(validate_email(email), "email_valid", "validate_email(email)", "create_user",
        context={"email": email})
    check_precondition(age >= 18 and age <= 120, "age_valid", "age >= 18 && age <= 120", "create_user",
        context={"age": age})

    __result = True

    check_postcondition(__result == True, "created", "result == true", "create_user",
        context={"result": __result})

    return __result
```

**Use it**:
```python
from user import create_user

# Valid
success = create_user("Alice", "alice@example.com", 25)  # ✓

# Invalid
create_user("", "alice@example.com", 25)         # ✗ name_not_empty failed
create_user("Alice", "invalid-email", 25)        # ✗ email_valid failed
create_user("Alice", "alice@example.com", 15)    # ✗ age_valid failed (< 18)
```

---

## Step 3: Generate JavaScript

```bash
asl build user.al --lang javascript -o user.js
```

**Output** (`user.js`):

```javascript
const { checkPrecondition, checkPostcondition } = require('@promptware/runtime');

function validate_email(email) {
    checkPrecondition(email.length > 0, "non_empty", "len(email) > 0", "validate_email",
        { email: email, "len(email)": email.length });
    checkPrecondition(email.includes("@"), "has_at", "\"@\" in email", "validate_email",
        { email: email });
    checkPrecondition(email.includes("."), "has_dot", "\".\" in email", "validate_email",
        { email: email });

    const valid = email.length > 0 && email.includes("@") && email.includes(".");
    const __result = valid;

    checkPostcondition(__result === true || __result === false, "valid_result",
        "result == true || result == false", "validate_email",
        { result: __result });

    return __result;
}

function create_user(name, email, age) {
    checkPrecondition(name.length > 0, "name_not_empty", "len(name) > 0", "create_user",
        { name: name, "len(name)": name.length });
    checkPrecondition(validate_email(email), "email_valid", "validate_email(email)", "create_user",
        { email: email });
    checkPrecondition(age >= 18 && age <= 120, "age_valid", "age >= 18 && age <= 120", "create_user",
        { age: age });

    const __result = true;

    checkPostcondition(__result === true, "created", "result == true", "create_user",
        { result: __result });

    return __result;
}

module.exports = { validate_email, create_user };
```

**Use it**:
```javascript
const { create_user } = require('./user');

// Valid
const success = create_user("Alice", "alice@example.com", 25);  // ✓

// Invalid
create_user("", "alice@example.com", 25);        // ✗ ContractViolationError
create_user("Alice", "invalid-email", 25);       // ✗ ContractViolationError
```

---

## Step 4: Generate Go

```bash
asl build user.al --lang go -o user.go
```

**Output** (`user.go`):

```go
package main

import (
    "fmt"
    "strings"
)

func checkPrecondition(condition bool, clauseName string, expression string, functionName string) {
    if !condition {
        panic(fmt.Sprintf("Contract Violation: Precondition\n  Function: %s\n  Clause: '%s'\n  Expression: %s",
            functionName, clauseName, expression))
    }
}

func checkPostcondition(condition bool, clauseName string, expression string, functionName string) {
    if !condition {
        panic(fmt.Sprintf("Contract Violation: Postcondition\n  Function: %s\n  Clause: '%s'\n  Expression: %s",
            functionName, clauseName, expression))
    }
}

func validateEmail(email string) bool {
    checkPrecondition(len(email) > 0, "non_empty", "len(email) > 0", "validateEmail")
    checkPrecondition(strings.Contains(email, "@"), "has_at", "\"@\" in email", "validateEmail")
    checkPrecondition(strings.Contains(email, "."), "has_dot", "\".\" in email", "validateEmail")

    valid := len(email) > 0 && strings.Contains(email, "@") && strings.Contains(email, ".")
    result := valid

    checkPostcondition(result == true || result == false, "valid_result", "result == true || result == false", "validateEmail")

    return result
}

func createUser(name string, email string, age int) bool {
    checkPrecondition(len(name) > 0, "name_not_empty", "len(name) > 0", "createUser")
    checkPrecondition(validateEmail(email), "email_valid", "validateEmail(email)", "createUser")
    checkPrecondition(age >= 18 && age <= 120, "age_valid", "age >= 18 && age <= 120", "createUser")

    result := true

    checkPostcondition(result == true, "created", "result == true", "createUser")

    return result
}
```

**Use it**:
```go
package main

import "fmt"

func main() {
    // Valid
    success := createUser("Alice", "alice@example.com", 25)
    fmt.Println("User created:", success)

    // Invalid (will panic)
    // createUser("", "alice@example.com", 25)  // Panic: name_not_empty failed
}
```

---

## Step 5: Generate Rust

```bash
asl build user.al --lang rust -o user.rs
```

**Output** (`user.rs`):

```rust
fn check_precondition(condition: bool, clause_name: &str, expression: &str, function_name: &str) {
    if !condition {
        panic!(
            "Contract Violation: Precondition\n  Function: {}\n  Clause: '{}'\n  Expression: {}",
            function_name, clause_name, expression
        );
    }
}

fn check_postcondition(condition: bool, clause_name: &str, expression: &str, function_name: &str) {
    if !condition {
        panic!(
            "Contract Violation: Postcondition\n  Function: {}\n  Clause: '{}'\n  Expression: {}",
            function_name, clause_name, expression
        );
    }
}

fn validate_email(email: &str) -> bool {
    check_precondition(email.len() > 0, "non_empty", "len(email) > 0", "validate_email");
    check_precondition(email.contains("@"), "has_at", "\"@\" in email", "validate_email");
    check_precondition(email.contains("."), "has_dot", "\".\" in email", "validate_email");

    let valid = email.len() > 0 && email.contains("@") && email.contains(".");
    let result = valid;

    check_postcondition(result == true || result == false, "valid_result", "result == true || result == false", "validate_email");

    result
}

fn create_user(name: &str, email: &str, age: i32) -> bool {
    check_precondition(name.len() > 0, "name_not_empty", "len(name) > 0", "create_user");
    check_precondition(validate_email(email), "email_valid", "validate_email(email)", "create_user");
    check_precondition(age >= 18 && age <= 120, "age_valid", "age >= 18 && age <= 120", "create_user");

    let result = true;

    check_postcondition(result == true, "created", "result == true", "create_user");

    result
}
```

**Use it**:
```rust
fn main() {
    // Valid
    let success = create_user("Alice", "alice@example.com", 25);
    println!("User created: {}", success);

    // Invalid (will panic)
    // create_user("", "alice@example.com", 25);  // Panic: name_not_empty failed
}
```

---

## Step 6: Generate TypeScript

```bash
asl build user.al --lang typescript -o user.ts
```

**Output** (`user.ts`):

```typescript
import { checkPrecondition, checkPostcondition } from '@promptware/runtime';

function validate_email(email: string): boolean {
    checkPrecondition(email.length > 0, "non_empty", "len(email) > 0", "validate_email",
        { email: email, "len(email)": email.length });
    checkPrecondition(email.includes("@"), "has_at", "\"@\" in email", "validate_email",
        { email: email });
    checkPrecondition(email.includes("."), "has_dot", "\".\" in email", "validate_email",
        { email: email });

    const valid: boolean = email.length > 0 && email.includes("@") && email.includes(".");
    const __result: boolean = valid;

    checkPostcondition(__result === true || __result === false, "valid_result",
        "result == true || result == false", "validate_email",
        { result: __result });

    return __result;
}

function create_user(name: string, email: string, age: number): boolean {
    checkPrecondition(name.length > 0, "name_not_empty", "len(name) > 0", "create_user",
        { name: name, "len(name)": name.length });
    checkPrecondition(validate_email(email), "email_valid", "validate_email(email)", "create_user",
        { email: email });
    checkPrecondition(age >= 18 && age <= 120, "age_valid", "age >= 18 && age <= 120", "create_user",
        { age: age });

    const __result: boolean = true;

    checkPostcondition(__result === true, "created", "result == true", "create_user",
        { result: __result });

    return __result;
}

export { validate_email, create_user };
```

---

## Language Comparison

| Feature | Python | JavaScript | Go | Rust | TypeScript |
|---------|--------|------------|-----|------|------------|
| **Contract checks** | ✅ Full | ✅ Full | ⚠️ Basic | ⚠️ Basic | ✅ Full |
| **Error context** | ✅ Rich | ✅ Rich | ⚠️ Basic | ⚠️ Basic | ✅ Rich |
| **Type annotations** | ✅ | ❌ | ✅ | ✅ | ✅ |
| **Pattern matching** | ✅ | ✅ | ❌ | ❌ | ✅ |
| **Stdlib support** | ✅ | ✅ | ⚠️ Partial | ⚠️ Partial | ✅ |
| **Production ready** | ✅ | ✅ | ⚠️ Experimental | ⚠️ Experimental | ⚠️ Beta |

---

## Common Patterns

### Pattern 1: Generate All Languages

```bash
# Generate all at once
for lang in python javascript go rust typescript; do
    asl build user.al --lang $lang -o "user_$lang"
done
```

**Output**:
```
user_python.py
user_javascript.js
user_go.go
user_rust.rs
user_typescript.ts
```

---

### Pattern 2: Language-Specific Options

**Python with Pydantic**:
```bash
asl build user.al --lang python --format pydantic -o models.py
```

**Python with TypedDict**:
```bash
asl build user.al --lang python --format typeddict -o types.py
```

---

### Pattern 3: Validate Before Generate

```bash
# Always validate first
promptware validate user.al && \
    asl build user.al --lang python -o user.py
```

---

## What You Learned

✅ **Multi-language compilation** - One contract → 5 languages
✅ **Language-specific output** - Idiomatic code per language
✅ **Runtime contracts** - Checks embedded in all targets
✅ **Production workflow** - Validate → Generate → Test

---

## Next Steps

**Test generated code**:
- [How-To: Test Your Contracts](testing-contracts.md)

**Advanced generation**:
- [How-To: Use with Pydantic](../integration/pydantic.md)

**Learn more**:
- [CLI Commands Reference](../../reference/cli-commands.md)
- [Contract Syntax](../../reference/contract-syntax.md)

---

## Troubleshooting

**Problem**: Generated Go/Rust code doesn't compile

**Fix**: Go and Rust generators are experimental. Use Python/JavaScript for production.

---

**Problem**: Missing runtime module in JavaScript

**Fix**: Install runtime:
```bash
npm install @promptware/runtime
```

---

**Problem**: Type errors in TypeScript

**Fix**: Install type definitions:
```bash
npm install --save-dev @types/node
```

---

## See Also

- **[First Contract](first-contract.md)** - Getting started
- **[CLI Commands](../../reference/cli-commands.md)** - Build command reference
- **[Runtime API](../../reference/runtime-api.md)** - Contract runtime

---

**[← First Contract](first-contract.md)** | **[How-To Index →](../index.md)**
