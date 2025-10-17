# Contract Syntax Best Practices Research

**Date:** 2025-10-14
**Purpose:** Design enhanced PW syntax for multi-agent contracts
**Phase:** Phase 2 - Core Contract Language

---

## Research Sources

1. **Solidity** - Smart contract language (Ethereum)
2. **Protocol Buffers** - Service contract specification (Google)
3. **Eiffel Design by Contract** - Original DbC implementation (Bertrand Meyer)

---

## Key Findings

### 1. Solidity - Smart Contracts

**Preconditions: `require()`**
- Used for input validation
- Guards against invalid user input
- Reverts transaction if condition fails
- Clear error messages required

```solidity
function transfer(address to, uint256 amount) public {
    require(to != address(0), "Invalid address");
    require(amount <= balance, "Insufficient balance");
    // ... implementation
}
```

**Invariants: `assert()`**
- Used for internal errors only
- Checks contract state invariants
- Should never fail in correct code
- Indicates programming error if triggered

```solidity
function _mint(uint256 amount) internal {
    totalSupply += amount;
    assert(totalSupply >= amount); // Overflow check (invariant)
}
```

**Postconditions: Modifiers**
- Implemented using custom modifiers
- Check state after function execution
- Can reference pre-state manually

```solidity
modifier checksInvariant() {
    _;
    assert(totalSupply == sum(allBalances)); // Postcondition check
}
```

**Key Lessons:**
- Separate preconditions (user input) from invariants (internal consistency)
- Error messages are critical for debugging
- Postconditions typically use modifiers, not built-in syntax

---

### 2. Protocol Buffers - Service Contracts

**Contract-First API Design**
- .proto files define explicit contracts
- Types, services, and methods clearly specified
- Self-documenting through required comments
- Version control for schema evolution

```proto
// User service contract
service UserService {
  // Creates a new user with validation
  rpc CreateUser(CreateUserRequest) returns (User);
}

message CreateUserRequest {
  string name = 1;    // Required: 1-100 characters
  string email = 2;   // Required: Valid email format
}
```

**Best Practices:**
1. **Documentation**: All objects must have comments
2. **Naming**: Consistent conventions (e.g., Service suffix)
3. **Structure**: Keep messages simple and purpose-built
4. **Field Numbers**: Never reuse or delete
5. **Backward Compatibility**: Design for evolution

**Key Lessons:**
- Documentation is first-class citizen
- Contracts should be strongly typed
- Versioning strategy is critical
- Comments should explain constraints, not just types

---

### 3. Eiffel Design by Contract

**The Original DbC Syntax:**

```eiffel
set_balance(new_balance: INTEGER)
    require
        non_negative: new_balance >= 0
        reasonable: new_balance < MAX_BALANCE
    do
        balance := new_balance
    ensure
        balance_set: balance = new_balance
        positive_if_was_positive:
            old balance > 0 implies balance > 0
    end
```

**Three Core Constructs:**

1. **`require` - Preconditions**
   - Obligations on the caller
   - Must be true on entry
   - Named clauses for clarity
   - Multiple conditions supported

2. **`ensure` - Postconditions**
   - Guarantees by the routine
   - Must be true on exit
   - Can reference `old` state
   - Express what changed

3. **`invariant` - Class Invariants**
   - Consistency constraints
   - Must hold after creation
   - Must be maintained by all public methods
   - Class-level properties

**The `old` Keyword:**
- Valid only in postconditions
- References value on entry
- Critical for expressing state changes

```eiffel
ensure
    increased: balance = old balance + amount
```

**Key Lessons:**
- Named clauses improve readability
- `old` keyword essential for postconditions
- Invariants apply to entire class/contract
- Clauses can have complex boolean expressions

---

## Synthesis: Best Practices for PW Contracts

### 1. Syntax Keywords

**Recommended:**
- `@requires` or `require` - Preconditions (input validation)
- `@ensures` or `ensure` - Postconditions (output guarantees)
- `@invariant` - Contract-level invariants
- `@effects` - Side effects declaration (novel, not in Eiffel)
- `old` keyword - Reference pre-state in postconditions

### 2. Named Clauses

Each condition should have a name for better error messages:

```pw
@requires name_not_empty: str.length(name) >= 1
@requires valid_email: str.contains(email, "@")
```

Benefits:
- Clear error messages ("Precondition 'name_not_empty' violated")
- Self-documenting code
- Better debugging

### 3. Contract Structure

```pw
@contract
service UserService {
    @operation(idempotent=true)
    function createUser(name: string, email: string) -> User | ValidationError {
        @requires name_valid: str.length(name) >= 1 && str.length(name) <= 100
        @requires email_valid: str.contains(email, "@") && str.contains(email, ".")

        @ensures result_has_id: result is User implies result.id > 0
        @ensures preserves_input: result is User implies result.name == name

        @effects [database.write, event.emit("user.created")]

        // Implementation
        if (str.length(name) < 1) {
            return ValidationError("name", "Name cannot be empty");
        }

        // ... rest of implementation
    }

    @invariant user_count_positive: this.userCount >= 0
    @invariant no_duplicate_emails: this.allUsers.map(u => u.email).unique()
}
```

### 4. Error Messages

**Best Practice:** Include violated clause name in error message

```
Error: Precondition 'name_valid' violated: str.length(name) >= 1 && str.length(name) <= 100
  Got: name.length = 0
  Expected: name.length >= 1
```

### 5. Documentation

**Inline with contract:**

```pw
/// Creates a new user account
///
/// Validates name (1-100 chars) and email (must contain @ and .)
/// Returns User on success, ValidationError on validation failure
///
/// @param name User's full name
/// @param email User's email address
/// @returns User object with generated ID or ValidationError
function createUser(name: string, email: string) -> User | ValidationError
```

### 6. Levels of Checking

**Three levels (from Solidity):**

1. **Preconditions (`@requires`)** - User input validation
   - Checked at runtime always
   - User-facing error messages
   - Revert with clear reason

2. **Postconditions (`@ensures`)** - Correctness guarantees
   - Checked in development/testing
   - Can be disabled in production for performance
   - Internal consistency

3. **Invariants (`@invariant`)** - State consistency
   - Checked after every public operation
   - Should never fail in correct code
   - Indicate bugs if violated

### 7. Semantic Validation

**What to validate:**

1. **Type correctness** - Already done by type system
2. **Value ranges** - Preconditions
3. **Business rules** - Preconditions + invariants
4. **State transitions** - Postconditions with `old`
5. **Side effects** - Effects declarations
6. **Return value properties** - Postconditions

### 8. Contract Metadata

Additional annotations for framework integration:

```pw
@contract(version="1.0.0", description="User management service")
service UserService {
    @operation(
        idempotent=true,
        timeout=5000,
        retries=3,
        cache_ttl=60
    )
    function getUser(id: int) -> User | NotFoundError
}
```

---

## Comparison Table

| Feature | Solidity | Protocol Buffers | Eiffel | PW Contracts |
|---------|----------|------------------|--------|--------------|
| Preconditions | `require()` | Comments | `require` | `@requires` |
| Postconditions | Modifiers | N/A | `ensure` | `@ensures` |
| Invariants | `assert()` | N/A | `invariant` | `@invariant` |
| Old state | Manual | N/A | `old` keyword | `old` keyword |
| Named clauses | No | No | Yes | Yes |
| Error messages | String param | N/A | Auto-generated | Custom |
| Documentation | Comments | Required | Comments | `///` doc comments |
| Effects | Events | N/A | N/A | `@effects` |
| Metadata | N/A | Options | N/A | `@operation()` |

---

## Implementation Recommendations

### Phase 2A: Basic Contract Syntax (Week 2, Days 1-3)

**Implement:**
1. `@requires` with named clauses
2. Basic error messages with clause names
3. Documentation comments (`///`)
4. Contract-level metadata (`@contract`)

**Example:**
```pw
@contract
function createUser(name: string, email: string) -> User | Error {
    @requires name_not_empty: str.length(name) >= 1
    @requires email_has_at: str.contains(email, "@")

    // Implementation
}
```

### Phase 2B: Advanced Contract Features (Week 2, Days 4-7)

**Implement:**
1. `@ensures` postconditions with `old` keyword
2. `@invariant` class-level constraints
3. `@effects` side effect declarations
4. Operation metadata (`@operation()`)
5. Runtime validation framework

**Example:**
```pw
@contract
service UserService {
    @invariant all_ids_positive: this.users.all(u => u.id > 0)

    @operation(idempotent=true)
    function createUser(name: string) -> User {
        @requires name_valid: str.length(name) >= 1
        @ensures id_assigned: result.id > 0
        @ensures name_preserved: result.name == name
        @ensures user_count_increased: this.userCount == old this.userCount + 1
        @effects [database.write, event.emit("user.created")]

        // Implementation
    }
}
```

### Phase 2C: Developer Experience (Week 2, concurrent)

**Implement:**
1. Helpful error messages with context
2. Contract validation CLI command
3. Contract testing framework
4. Documentation generator from contracts

---

## Success Criteria

**Phase 2 is successful when:**

1. ✅ All contracts have named preconditions (`@requires`)
2. ✅ Error messages include clause names
3. ✅ Documentation is first-class (/// comments)
4. ✅ Postconditions work with `old` keyword
5. ✅ Invariants are checked automatically
6. ✅ Effects are declared and trackable
7. ✅ CLI can validate contracts (`promptware validate contract.pw`)
8. ✅ Contracts generate useful documentation

---

## References

1. **Solidity Best Practices**: https://consensys.io/blog/solidity-best-practices-for-smart-contract-security
2. **Protocol Buffers Style Guide**: https://protobuf.dev/programming-guides/style/
3. **Eiffel Design by Contract**: https://www.eiffel.org/doc/solutions/Design_by_Contract_and_Assertions
4. **Automated Invariant Generation**: https://arxiv.org/html/2401.00650v1

---

**Next Steps:**
1. Design concrete PW syntax proposal
2. Update parser to support new syntax
3. Implement validation framework
4. Create test suite for contract validation
5. Document new syntax in language reference
