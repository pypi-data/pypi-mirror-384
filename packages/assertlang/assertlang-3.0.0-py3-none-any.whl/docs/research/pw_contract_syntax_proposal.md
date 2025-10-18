# PW Contract Syntax Proposal

**Date:** 2025-10-14
**Status:** Design Phase
**Target:** Phase 2 implementation (Week 2)

---

## Overview

This document specifies the enhanced PW syntax for multi-agent contracts, incorporating best practices from Solidity, Protocol Buffers, and Eiffel Design by Contract.

---

## 1. Contract Declaration

### Syntax

```pw
@contract(version="1.0.0", description="Optional description")
service ServiceName {
    // Service-level invariants
    @invariant invariant_name: boolean_expression

    // Operations (functions)
    function operationName(...) -> ReturnType { ... }
}
```

### Example

```pw
@contract(version="1.0.0", description="User management service")
service UserService {
    @invariant no_duplicate_ids: users.map(u => u.id).unique()
    @invariant positive_user_count: users.length >= 0

    function createUser(name: string, email: string) -> User | ValidationError {
        // ...
    }
}
```

---

## 2. Preconditions (`@requires`)

### Syntax

```pw
@requires clause_name: boolean_expression
@requires another_clause: boolean_expression
```

### Features

- **Named clauses**: Each clause has a name for error reporting
- **Multiple clauses**: Can have multiple `@requires` per function
- **Boolean expressions**: Any expression evaluating to boolean

### Example

```pw
function createUser(name: string, email: string) -> User | ValidationError {
    @requires name_not_empty: str.length(name) >= 1
    @requires name_max_length: str.length(name) <= 100
    @requires email_format: str.contains(email, "@") && str.contains(email, ".")

    // Implementation
}
```

### Error Messages

When a precondition fails:

```
ContractViolation: Precondition 'name_not_empty' failed
  Function: UserService.createUser
  Clause: str.length(name) >= 1
  Got: name.length = 0
  Expected: name.length >= 1
```

---

## 3. Postconditions (`@ensures`)

### Syntax

```pw
@ensures clause_name: boolean_expression
@ensures another_clause: boolean_expression_with_old
```

### The `old` Keyword

References the value of an expression **before** the function executed:

```pw
@ensures balance_increased: balance == old balance + amount
```

### Example

```pw
function createUser(name: string, email: string) -> User | ValidationError {
    @requires name_not_empty: str.length(name) >= 1

    @ensures result_has_id: result is User implies result.id > 0
    @ensures name_preserved: result is User implies result.name == name
    @ensures user_count_increased: this.users.length == old this.users.length + 1

    // Implementation
}
```

### When to Use

- Verify return value properties
- Check state changes
- Validate side effects occurred
- Express guarantees to caller

---

## 4. Invariants (`@invariant`)

### Contract-Level Invariants

Applied to entire service/class:

```pw
@contract
service UserService {
    @invariant all_ids_positive: users.all(u => u.id > 0)
    @invariant no_duplicates: users.map(u => u.email).unique()

    // ... functions
}
```

### Checking Strategy

**When checked:**
- After contract creation/initialization
- After every public function execution
- Automatically by runtime

**Failure behavior:**
- Indicates programming bug (should never fail in correct code)
- More severe than precondition failure
- Logs error with full context

---

## 5. Effects Declaration (`@effects`)

### Syntax

```pw
@effects [effect1, effect2, effect3]
```

### Effect Types

```pw
@effects [
    database.write,                    // Database modification
    database.read,                     // Database query
    network.http(url),                // Network call
    event.emit("event_name"),         // Event emission
    file.write(path),                 // File system write
    cache.invalidate(key)             // Cache modification
]
```

### Example

```pw
function createUser(name: string, email: string) -> User {
    @requires name_not_empty: str.length(name) >= 1

    @effects [
        database.write,
        event.emit("user.created"),
        cache.invalidate("user_list")
    ]

    // Implementation
}
```

### Use Cases

1. **Documentation**: Explicitly declare side effects
2. **Testing**: Mock these effects in tests
3. **Framework Integration**: Frameworks can intercept effects
4. **Coordination**: Other agents know what changed

---

## 6. Operation Metadata (`@operation`)

### Syntax

```pw
@operation(key=value, key2=value2)
function name(...) -> ReturnType
```

### Supported Metadata

```pw
@operation(
    idempotent=true,          // Safe to retry
    timeout=5000,             // Timeout in milliseconds
    retries=3,                // Number of retry attempts
    cache_ttl=60,            // Cache time-to-live (seconds)
    rate_limit=100,          // Max calls per minute
    authentication=true       // Requires authentication
)
```

### Example

```pw
@operation(idempotent=true, timeout=5000, retries=3)
function createUser(name: string, email: string) -> User {
    // Safe to retry, 5s timeout, up to 3 retries
}

@operation(cache_ttl=60, rate_limit=1000)
function getUser(id: int) -> User | NotFoundError {
    // Cache for 60s, max 1000 calls/min
}
```

---

## 7. Documentation Comments

### Syntax

Use `///` for documentation (similar to Rust/C#):

```pw
/// Creates a new user account with validation
///
/// This function validates the name and email, generates a unique ID,
/// and persists the user to the database.
///
/// @param name User's full name (1-100 characters)
/// @param email Valid email address (must contain @ and .)
/// @returns User object with assigned ID, or ValidationError on failure
///
/// @example
///   let user = createUser("Alice Smith", "alice@example.com");
///   if (user is User) {
///     print("Created user with ID: " + user.id);
///   }
function createUser(name: string, email: string) -> User | ValidationError {
    @requires name_length: str.length(name) >= 1 && str.length(name) <= 100
    @requires email_format: str.contains(email, "@")

    // Implementation
}
```

### Documentation Tags

- `@param name description` - Parameter documentation
- `@returns description` - Return value documentation
- `@throws ErrorType description` - Possible errors
- `@example code` - Usage example
- `@see OtherFunction` - Related functions

---

## 8. Complete Example

```pw
@contract(
    version="1.0.0",
    description="User management service for multi-agent coordination",
    author="AssertLang Contributors"
)
service UserService {
    // Service-level invariants
    @invariant all_ids_positive: users.all(u => u.id > 0)
    @invariant no_duplicate_emails: users.map(u => u.email).unique()
    @invariant user_count_matches: users.length == this.userCount

    /// Creates a new user account
    ///
    /// Validates input, generates ID, and persists to database.
    ///
    /// @param name User's full name (1-100 characters)
    /// @param email Valid email address
    /// @returns User object or ValidationError
    @operation(idempotent=false, timeout=5000)
    function createUser(name: string, email: string) -> User | ValidationError {
        // Preconditions (input validation)
        @requires name_not_empty: str.length(name) >= 1
        @requires name_max_length: str.length(name) <= 100
        @requires email_has_at: str.contains(email, "@")
        @requires email_has_dot: str.contains(email, ".")
        @requires no_duplicate_email: !users.any(u => u.email == email)

        // Postconditions (output guarantees)
        @ensures id_positive: result is User implies result.id > 0
        @ensures name_preserved: result is User implies result.name == name
        @ensures email_preserved: result is User implies result.email == email
        @ensures user_added: result is User implies
            this.users.length == old this.users.length + 1
        @ensures count_incremented: result is User implies
            this.userCount == old this.userCount + 1

        // Side effects declaration
        @effects [
            database.write,
            event.emit("user.created"),
            cache.invalidate("user_list")
        ]

        // Implementation
        if (str.length(name) < 1) {
            return ValidationError {
                field: "name",
                message: "Name cannot be empty"
            };
        }

        if (str.length(name) > 100) {
            return ValidationError {
                field: "name",
                message: "Name too long (max 100 characters)"
            };
        }

        if (!str.contains(email, "@") || !str.contains(email, ".")) {
            return ValidationError {
                field: "email",
                message: "Invalid email format"
            };
        }

        // Check for duplicate
        for (user in users) {
            if (user.email == email) {
                return ValidationError {
                    field: "email",
                    message: "Email already exists"
                };
            }
        }

        // Generate ID (deterministic for demo)
        let id = str.length(name) + str.length(email);
        let timestamp = timestamp();

        // Create user
        let user = User {
            id: id,
            name: name,
            email: email,
            created_at: timestamp
        };

        // Persist (side effect)
        users.push(user);
        this.userCount = this.userCount + 1;

        return user;
    }

    /// Retrieves user by ID
    ///
    /// @param id User ID to lookup
    /// @returns User object or NotFoundError
    @operation(idempotent=true, cache_ttl=60)
    function getUser(id: int) -> User | NotFoundError {
        @requires id_positive: id > 0

        @ensures found_has_matching_id: result is User implies result.id == id

        @effects [database.read]

        for (user in users) {
            if (user.id == id) {
                return user;
            }
        }

        return NotFoundError {
            resource: "user",
            id: id
        };
    }

    /// Validates email format
    ///
    /// @param email Email to validate
    /// @returns true if valid, false otherwise
    @operation(idempotent=true, cache_ttl=300)
    function isValidEmail(email: string) -> bool {
        @requires email_not_empty: str.length(email) > 0

        @ensures consistent: result == (
            str.contains(email, "@") && str.contains(email, ".")
        )

        @effects []  // Pure function, no side effects

        if (!str.contains(email, "@")) {
            return false;
        }

        if (!str.contains(email, ".")) {
            return false;
        }

        return true;
    }
}
```

---

## 9. Validation Modes

### Development Mode

All checks enabled:
- Preconditions: ✅ Checked
- Postconditions: ✅ Checked
- Invariants: ✅ Checked
- Effects: ✅ Tracked

### Production Mode

Optimized for performance:
- Preconditions: ✅ Checked (user-facing validation)
- Postconditions: ⚠️ Optional (can disable for performance)
- Invariants: ⚠️ Optional (should never fail, can disable)
- Effects: ⚠️ Logging only

### Test Mode

Maximum validation:
- Preconditions: ✅ Checked
- Postconditions: ✅ Checked
- Invariants: ✅ Checked
- Effects: ✅ Mocked/verified
- Coverage: ✅ Track which clauses were tested

---

## 10. CLI Commands

### Validate Contract

```bash
promptware validate contract.al

# Output:
✓ Syntax valid
✓ All preconditions have names
✓ All invariants are well-formed
✓ No circular dependencies
✓ Documentation complete
✗ Warning: Function 'createUser' has no postconditions
```

### Test Contract

```bash
asl test contract.al --mode=development

# Output:
Testing UserService.createUser
  ✓ Precondition 'name_not_empty' (2 test cases)
  ✓ Precondition 'email_has_at' (2 test cases)
  ✓ Postcondition 'id_positive' (1 test case)
  ✓ Invariant 'all_ids_positive' (maintained)

Coverage: 5/5 clauses tested (100%)
```

### Generate Documentation

```bash
promptware docs contract.al -o docs/

# Generates:
# docs/UserService.md - Full API documentation
# docs/UserService.html - HTML version
# docs/contracts.json - Machine-readable spec
```

---

## 11. Implementation Phases

### Phase 2A: Parser & Basic Validation (Days 1-3)

**Tasks:**
1. Update parser to recognize `@requires`, `@ensures`, `@invariant`, `@effects`
2. Parse named clauses (name: expression)
3. Parse documentation comments (`///`)
4. Add contract metadata parsing (`@contract`, `@operation`)
5. Basic syntax validation

**Agent:** stdlib-engineer

### Phase 2B: Runtime Validation (Days 4-5)

**Tasks:**
1. Implement precondition checking at function entry
2. Implement postcondition checking at function exit
3. Implement invariant checking after public operations
4. Handle `old` keyword in postconditions
5. Generate helpful error messages

**Agent:** runtime-engineer

### Phase 2C: Testing & Tooling (Days 6-7)

**Tasks:**
1. Build contract testing framework
2. Implement `promptware validate` command
3. Implement `asl test` command
4. Track coverage of contract clauses
5. Generate test reports

**Agent:** qa-engineer

---

## 12. Backward Compatibility

### Existing PW Code

All existing PW code continues to work:

```pw
// Old style (still valid)
function createUser(name: string) -> User {
    if (str.length(name) < 1) {
        return error("Name required");
    }
    // ...
}
```

### New Style

New contracts use enhanced syntax:

```pw
// New style (opt-in)
@contract
function createUser(name: string) -> User {
    @requires name_not_empty: str.length(name) >= 1
    // ...
}
```

### Migration Path

1. Existing code works without changes
2. Add `@requires` incrementally
3. Add `@ensures` for critical functions
4. Add `@invariant` for services
5. Full contract syntax for new code

---

## 13. Success Metrics

**Phase 2 is complete when:**

1. ✅ Parser supports all new syntax
2. ✅ Runtime validates preconditions
3. ✅ Runtime validates postconditions (with `old`)
4. ✅ Runtime validates invariants
5. ✅ Effects are declared and tracked
6. ✅ Error messages include clause names
7. ✅ `promptware validate` command works
8. ✅ `asl test` command works
9. ✅ Documentation generator works
10. ✅ All tests pass (100% coverage)

---

## 14. Examples for Testing

### Minimal Contract

```pw
@contract
function add(a: int, b: int) -> int {
    @ensures result_correct: result == a + b
    return a + b;
}
```

### Contract with Failure Cases

```pw
@contract
function divide(a: int, b: int) -> int {
    @requires non_zero: b != 0
    @ensures result_correct: result * b == a
    return a / b;
}
```

### Stateful Contract

```pw
@contract
service Counter {
    @invariant non_negative: this.count >= 0

    @operation(idempotent=false)
    function increment() -> int {
        @ensures increased: result == old this.count + 1
        @ensures state_updated: this.count == result
        @effects [state.write]

        this.count = this.count + 1;
        return this.count;
    }
}
```

---

## Next Steps

1. **stdlib-engineer**: Implement parser for new syntax
2. **runtime-engineer**: Build validation runtime
3. **qa-engineer**: Create testing framework
4. **Lead Agent**: Review and integrate implementations

---

**Status:** Design complete, ready for implementation
**Target Completion:** End of Week 2 (Phase 2)
