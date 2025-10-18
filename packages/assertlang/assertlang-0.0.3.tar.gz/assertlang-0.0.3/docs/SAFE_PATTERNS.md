# Safe Programming Patterns in PW

This guide documents safe patterns for common operations in PW that work correctly across all 5 target languages.

---

## Array Operations

### Array Length

**PW Syntax**:
```al
function count_items(items: array) -> int {
    return items.length;
}
```

**Translation by Language**:
- **Python**: `len(items)`
- **Go**: `len(items)`
- **Rust**: `items.len()`
- **TypeScript**: `items.length`
- **C#**: `items.Count` (for List<T>)

**Usage Example**:
```al
function sum_array(numbers: array) -> int {
    let total = 0;
    let i = 0;
    while (i < numbers.length) {  // ✅ Safe in all languages
        total = total + numbers[i];
        i = i + 1;
    }
    return total;
}
```

---

## Map/Dictionary Operations

### Safe Key Existence Check

**Problem**: Direct map indexing `map[key]` can throw exceptions in some languages if the key doesn't exist.

**PW Solution**: Map indexing is automatically safe - returns `null` for missing keys.

**PW Syntax**:
```al
function has_user(users: map, username: string) -> bool {
    if (users[username] != null) {  // ✅ Safe - no exception
        return true;
    }
    return false;
}
```

**How It Works**:

PW generators detect map types and use safe access patterns:

- **Python**: `users.get(username)` - Returns `None` if missing
- **Go**: `users[username]` - Returns zero value (nil) if missing
- **Rust**: `users.get(&username).cloned()` - Returns `Option<V>`
- **TypeScript**: `users[username]` - Returns `undefined` if missing
- **C#**: `(users.ContainsKey(username) ? users[username] : null)` - Ternary check

**Generated Python**:
```python
def has_user(users: Dict, username: str) -> bool:
    if (users.get(username) != None):  # ✅ Safe
        return True
    return False
```

**Generated Rust**:
```rust
pub fn has_user(users: &HashMap<String, Box<dyn std::any::Any>>, username: String) -> bool {
    if (users.get(&username).cloned() != Box::new(())) {  // ✅ Safe
        return true;
    }
    return false;
}
```

### Map Assignment vs Reading

**Reading** (uses safe access):
```al
let value = users[username];  // Safe - returns null if missing
```

**Writing** (uses direct assignment):
```al
users[username] = "active";  // Direct assignment works
```

**Full Example**:
```al
function add_user(users: map, username: string, email: string) -> bool {
    // Safe read - check if exists
    if (users[username] != null) {
        return false;  // User already exists
    }
    
    // Direct write - add new user
    users[username] = email;
    return true;
}
```

### String Literal Keys

String literal keys are also treated as map access:

```al
function get_config(config: map) -> string {
    if (config["api_key"] != null) {  // ✅ Safe with string literal
        return config["api_key"];
    }
    return "default_key";
}
```

---

## Type Detection

PW generators use **type-aware indexing**:

1. **Map Type Detection**:
   - Check parameter types (`param: map`)
   - Check for string literal keys (`obj["key"]`)
   - Use safe access patterns

2. **Array Type Detection**:
   - Integer index → array access
   - Direct bracket notation `arr[i]`

**Example**:
```al
function demo(users: map, items: array, index: int, key: string) -> bool {
    let user = users[key];     // ✅ Map: uses .get() in Python
    let item = items[index];   // ✅ Array: uses [index] in Python
    return true;
}
```

---

## Control Flow Patterns

### C-Style For Loops

```al
for (let i = 0; i < 10; i = i + 1) {
    // Loop body
}
```

**Translation**:
- **Python**: Converts to `while` loop
- **Go**: Native `for` loop
- **Rust**: Scoped `while` loop  
- **TypeScript**: Native `for` loop
- **C#**: Native `for` loop

### For-In Loops

```al
for (item in items) {
    // Process item
}
```

Works in all 5 languages.

### While Loops with Break/Continue

```al
while (condition) {
    if (skip_this) {
        continue;  // ✅ Works in all languages
    }
    if (done) {
        break;     // ✅ Works in all languages
    }
    // Process
}
```

---

## Error Handling

### Try/Catch/Finally

```al
try {
    // Risky operation
    throw "error message";
} catch (e) {
    // Handle error
    return false;
} finally {
    // Cleanup (optional)
}
```

Works in all 5 languages.

---

## Class Patterns

### Property Assignment in Constructors

```al
class User {
    id: string;
    name: string;
    
    constructor(id: string, name: string) {
        self.id = id;      // ✅ Works in all languages
        self.name = name;
    }
}
```

---

## Common Pitfalls

### ❌ Assuming Direct Map Access is Safe

**Don't assume this**:
```al
let value = users[key];  // Will be safe in PW!
// But might throw in raw Python/Rust/C# if you write it manually
```

**In PW**: This IS safe - we generate safe code automatically.

### ❌ Using `null` in Typed Returns (Bug #4 - Not Fixed Yet)

**Currently broken**:
```al
function find_user(id: int) -> map {
    if (id < 0) {
        return null;  // ❌ Type error: expected map, got null
    }
    return {id: id};
}
```

**Workaround**:
```al
function find_user(id: int) -> map {
    if (id < 0) {
        return {};  // ✅ Return empty map instead
    }
    return {id: id};
}
```

**Future**: Optional types (`map?` or `map | null`) will fix this.

---

## Best Practices

1. **Use `.length` for arrays** - works universally
2. **Map indexing is safe** - returns null for missing keys
3. **Use `!= null` to check** - key existence or value presence
4. **Empty collections over null** - return `{}` or `[]` instead of null
5. **C-style for loops work** - use them when you need index-based iteration
6. **Try/catch uses braces** - not colons like Python

---

## Example: Complete Pattern

```al
class UserManager {
    users: map;
    
    constructor() {
        self.users = {};
    }
    
    function register(username: string, password: string) -> bool {
        // Safe key check
        if (self.users[username] != null) {
            return false;  // User exists
        }
        
        // Add user
        self.users[username] = password;
        return true;
    }
    
    function count_users() -> int {
        // Works when we add .keys() or .values() methods
        // For now, would need separate counter
        return 0;
    }
}
```

---

**Last Updated**: 2025-10-08 (v2.1.0b3)
**Bugs Fixed**: #7 (safe map access), #8 (.length translation)
