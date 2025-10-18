# PW v2.1 Research Notes

**Date**: 2025-10-07
**Purpose**: Research to inform v2.0 → v2.1 implementation

---

## 1. Type Systems Research

### Static vs Dynamic Type Checking

**Key Finding**: PW needs **gradual typing** - static where possible, dynamic fallback

**Industry Examples**:
- **TypeScript** - Optional static typing on top of JavaScript
- **Python 3.5+** - Type hints with mypy
- **Dart** - Sound type system with inference

**PW Approach**:
```pw
// Explicit types (static check)
function add(x: int, y: int) -> int {
    return x + y;  // ✅ Type-checked
}

// Type inference (static where possible)
function compute() -> int {
    let x = 42;        // Infer: int
    let y = x + 10;    // Infer: int
    return y;          // ✅ Type-checked
}

// Dynamic fallback (when needed)
function process(data: any) -> any {
    return data.transform();  // ⚠️ Runtime check
}
```

**Implementation Strategy**:
1. **Phase 1**: Type checker validates explicit types
2. **Phase 2**: Add type inference for `let` statements
3. **Phase 3**: Add `any` type for dynamic behavior

---

### Cross-Language Type Mapping

**Research Question**: How to map PW types → 5 target languages?

**Key Findings**:

| PW Type | Python | Go | Rust | TypeScript | C# |
|---------|--------|-----|------|------------|-----|
| `int` | `int` | `int` | `i32` | `number` | `int` |
| `float` | `float` | `float64` | `f64` | `number` | `double` |
| `string` | `str` | `string` | `String` | `string` | `string` |
| `bool` | `bool` | `bool` | `bool` | `boolean` | `bool` |
| `array<T>` | `List[T]` | `[]T` | `Vec<T>` | `T[]` | `List<T>` |
| `map<K,V>` | `Dict[K,V]` | `map[K]V` | `HashMap<K,V>` | `Map<K,V>` | `Dictionary<K,V>` |
| `any` | `Any` | `interface{}` | `Box<dyn Any>` | `any` | `object` |
| `null` | `None` | `nil` | `None` | `null` | `null` |

**Edge Cases**:
- TypeScript `number` = both int and float (no distinction)
- Go `nil` only for pointers/interfaces
- Rust `None` requires `Option<T>` wrapper

**Solution**: Generate conservative code
```rust
// PW: let x: int? = null;
// Rust:
let x: Option<i32> = None;
```

---

### Type Inference Algorithms

**Research**: Hindley-Milner type inference (used in Haskell, ML, Rust)

**Key Concepts**:
1. **Constraint Generation** - Collect type constraints from expressions
2. **Unification** - Solve constraints to infer types
3. **Generalization** - Polymorphic types (defer to v2.2)

**Simple PW Implementation**:
```python
class TypeInferencer:
    def __init__(self):
        self.constraints = []
        self.type_env = {}

    def infer(self, node: IRNode) -> str:
        if isinstance(node, IRLiteral):
            if isinstance(node.value, int):
                return "int"
            elif isinstance(node.value, float):
                return "float"
            elif isinstance(node.value, str):
                return "string"
            elif isinstance(node.value, bool):
                return "bool"

        elif isinstance(node, IRBinaryOp):
            left_type = self.infer(node.left)
            right_type = self.infer(node.right)

            # Constraint: left and right must be same type
            self.constraints.append((left_type, right_type))

            if node.op in ['+', '-', '*', '/']:
                # Arithmetic: int or float
                if left_type == "float" or right_type == "float":
                    return "float"
                return "int"

            elif node.op in ['==', '!=', '<', '>', '<=', '>=']:
                # Comparison: returns bool
                return "bool"

        elif isinstance(node, IRVariable):
            # Look up in environment
            if node.name in self.type_env:
                return self.type_env[node.name]
            else:
                raise TypeError(f"Undefined variable: {node.name}")

    def unify(self):
        """Solve type constraints."""
        for (t1, t2) in self.constraints:
            if t1 != t2 and t1 != "any" and t2 != "any":
                raise TypeError(f"Type mismatch: {t1} vs {t2}")
```

**Example**:
```pw
function compute() -> int {
    let x = 10;      // Infer: int (literal)
    let y = x + 5;   // Infer: int (int + int)
    let z = y * 2;   // Infer: int (int * int)
    return z;        // Check: int matches declared int ✅
}
```

---

## 2. Loop Constructs Research

### For Loop Patterns Across Languages

**Research Question**: How do different languages implement for loops?

**Findings**:

**Python**:
```python
# For-in (most common)
for item in items:
    print(item)

# Enumerate (with index)
for i, item in enumerate(items):
    print(i, item)

# Range
for i in range(10):
    print(i)
```

**Go**:
```go
// For-range
for i, item := range items {
    fmt.Println(i, item)
}

// C-style
for i := 0; i < 10; i++ {
    fmt.Println(i)
}

// While-style
for condition {
    // ...
}
```

**Rust**:
```rust
// For-in
for item in items.iter() {
    println!("{}", item);
}

// Enumerate
for (i, item) in items.iter().enumerate() {
    println!("{} {}", i, item);
}

// Range
for i in 0..10 {
    println!("{}", i);
}
```

**TypeScript**:
```typescript
// For-of (ES6)
for (const item of items) {
    console.log(item);
}

// For-in (keys)
for (const key in obj) {
    console.log(key);
}

// Traditional
for (let i = 0; i < 10; i++) {
    console.log(i);
}

// forEach (functional)
items.forEach((item, i) => {
    console.log(i, item);
});
```

**C#**:
```csharp
// Foreach
foreach (var item in items) {
    Console.WriteLine(item);
}

// For
for (int i = 0; i < 10; i++) {
    Console.WriteLine(i);
}
```

**PW Design Decision**: Use Python-style syntax (clearest)
```pw
// For-in (most common)
for (item in items) {
    print(item);
}

// Enumerate
for (index, item in enumerate(items)) {
    print(index, item);
}

// Range
for (i in range(0, 10)) {
    print(i);
}
```

**Translation Strategy**:
```python
# dsl/pw_parser.py
def parse_for(self):
    self.expect("FOR")
    self.expect("LPAREN")

    # Check for enumerate pattern
    if self.peek_ahead(2).type == "COMMA":
        # for (i, item in ...)
        index_var = self.consume("IDENTIFIER").value
        self.expect("COMMA")
        iter_var = self.consume("IDENTIFIER").value
        self.expect("IN")
        iterable = self.parse_expression()
        has_index = True
    else:
        # for (item in ...)
        iter_var = self.consume("IDENTIFIER").value
        self.expect("IN")
        iterable = self.parse_expression()
        has_index = False
        index_var = None

    self.expect("RPAREN")
    body = self.parse_block()

    return IRFor(
        iterator=iter_var,
        iterable=iterable,
        body=body,
        index_var=index_var
    )
```

---

### While Loops & Control Flow

**Research**: While loops are simpler - all languages have similar syntax

**PW Syntax** (C-style):
```pw
while (condition) {
    // body
}

// Infinite loop
while (true) {
    if (should_exit) {
        break;
    }
}

// Skip iteration
while (condition) {
    if (skip_this) {
        continue;
    }
    process();
}
```

**Translation** (straightforward):
- Python: `while condition:`
- Go: `for condition { }`
- Rust: `while condition { }`
- TypeScript: `while (condition) { }`
- C#: `while (condition) { }`

---

## 3. Array/Collection Research

### Array Literals & Initialization

**Research Question**: How to represent arrays in PW DSL?

**Design Options**:

**Option 1: Generic Syntax** (chosen)
```pw
let numbers: array<int> = [1, 2, 3];
let names: array<string> = ["Alice", "Bob"];
```

**Option 2: Type-Specific**
```pw
let numbers: int[] = [1, 2, 3];
let names: string[] = ["Alice", "Bob"];
```

**Decision**: Use `array<T>` (clearer, consistent with `map<K,V>`)

---

### Array Methods Across Languages

**Research**: What array methods are universal?

| Method | Python | Go | Rust | TypeScript | C# |
|--------|--------|-----|------|------------|-----|
| Length | `len(arr)` | `len(arr)` | `arr.len()` | `arr.length` | `arr.Count` |
| Append | `arr.append(x)` | `append(arr, x)` | `arr.push(x)` | `arr.push(x)` | `arr.Add(x)` |
| Pop | `arr.pop()` | N/A* | `arr.pop()` | `arr.pop()` | `arr.RemoveAt(n)` |
| Filter | `filter(f, arr)` | N/A* | `arr.iter().filter(f)` | `arr.filter(f)` | `arr.Where(f)` |
| Map | `map(f, arr)` | N/A* | `arr.iter().map(f)` | `arr.map(f)` | `arr.Select(f)` |
| Index | `arr[i]` | `arr[i]` | `arr[i]` | `arr[i]` | `arr[i]` |

*Go requires manual implementation

**PW Design**:
```pw
// Built-in functions (not methods)
let length = len(numbers);
let sum = sum(numbers);

// Methods (where universal)
numbers.push(42);
numbers.pop();

// Functional (where universal)
let evens = numbers.filter(lambda x -> x % 2 == 0);
let doubled = numbers.map(lambda x -> x * 2);
```

**Translation Strategy**:
```python
# Python
numbers.append(42)
numbers.pop()
evens = list(filter(lambda x: x % 2 == 0, numbers))

# Go (manual)
numbers = append(numbers, 42)
numbers = numbers[:len(numbers)-1]  // pop
evens := []int{}
for _, x := range numbers {
    if x % 2 == 0 {
        evens = append(evens, x)
    }
}

# Rust
numbers.push(42);
numbers.pop();
let evens: Vec<i32> = numbers.iter().filter(|x| *x % 2 == 0).collect();
```

---

## 4. Class/OOP Research

### Cross-Language Class Translation

**Research Question**: How to translate classes across OOP paradigms?

**Challenge**: Python/TypeScript/C# have classes, Go has structs, Rust has structs + traits

**Design Decision**: Classes map to language idioms

**PW Class**:
```pw
class User {
    id: string;
    name: string;
    age: int;

    constructor(id: string, name: string, age: int) {
        self.id = id;
        self.name = name;
        self.age = age;
    }

    function greet() -> string {
        return "Hello, " + self.name;
    }

    function is_adult() -> bool {
        return self.age >= 18;
    }
}
```

**Python Translation**:
```python
class User:
    def __init__(self, id: str, name: str, age: int):
        self.id = id
        self.name = name
        self.age = age

    def greet(self) -> str:
        return f"Hello, {self.name}"

    def is_adult(self) -> bool:
        return self.age >= 18
```

**Go Translation**:
```go
type User struct {
    ID   string
    Name string
    Age  int
}

func NewUser(id, name string, age int) User {
    return User{
        ID:   id,
        Name: name,
        Age:  age,
    }
}

func (u User) Greet() string {
    return fmt.Sprintf("Hello, %s", u.Name)
}

func (u User) IsAdult() bool {
    return u.Age >= 18
}
```

**Rust Translation**:
```rust
struct User {
    id: String,
    name: String,
    age: i32,
}

impl User {
    fn new(id: String, name: String, age: i32) -> User {
        User { id, name, age }
    }

    fn greet(&self) -> String {
        format!("Hello, {}", self.name)
    }

    fn is_adult(&self) -> bool {
        self.age >= 18
    }
}
```

**TypeScript Translation**:
```typescript
class User {
    constructor(
        public id: string,
        public name: string,
        public age: number
    ) {}

    greet(): string {
        return `Hello, ${this.name}`;
    }

    isAdult(): boolean {
        return this.age >= 18;
    }
}
```

**C# Translation**:
```csharp
public class User {
    public string Id { get; set; }
    public string Name { get; set; }
    public int Age { get; set; }

    public User(string id, string name, int age) {
        Id = id;
        Name = name;
        Age = age;
    }

    public string Greet() {
        return $"Hello, {Name}";
    }

    public bool IsAdult() {
        return Age >= 18;
    }
}
```

**Key Insight**: All languages support this pattern, just different syntax

**Translation Complexity**:
- ✅ Properties → fields/properties
- ✅ Constructor → language-specific init
- ✅ Methods → instance methods
- ⚠️ Inheritance → defer to v2.2 (complex)
- ⚠️ Interfaces → defer to v2.2 (complex)

---

### Memory Management Considerations

**Research Question**: How to handle ownership/GC differences?

**Python/Go/TypeScript/C#**: Garbage collected (easy)
**Rust**: Ownership + borrowing (complex)

**PW Design Decision**: Generate conservative Rust code
```pw
class Data {
    value: string;

    constructor(value: string) {
        self.value = value;
    }
}

let d = Data("hello");
let d2 = d;  // What happens here?
```

**Rust Translation** (conservative):
```rust
struct Data {
    value: String,
}

impl Data {
    fn new(value: String) -> Data {
        Data { value }
    }
}

let d = Data::new("hello".to_string());
let d2 = d.clone();  // Explicit clone (safe but slower)
```

**Alternative** (advanced - defer to v2.2):
```rust
let d = Rc::new(Data::new("hello".to_string()));
let d2 = d.clone();  // Reference counted
```

---

## 5. Parser Implementation Research

### Multi-line Syntax Handling

**Research Question**: How to support multi-line function signatures/calls?

**Current Issue**:
```pw
function calculate_risk(
    account_balance: float,
    position_size: float
) -> float {
    // ERROR: Parser sees NEWLINE, expects IDENTIFIER
}
```

**Root Cause**: Lexer tokenizes line-by-line, parser expects single line

**Solution**: Context-aware lexer
```python
class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.in_parentheses = 0  # Track paren nesting

    def tokenize(self):
        tokens = []
        while self.pos < len(self.source):
            token = self.next_token()

            # Skip newlines inside parentheses
            if token.type == "NEWLINE" and self.in_parentheses > 0:
                continue

            if token.type == "LPAREN":
                self.in_parentheses += 1
            elif token.type == "RPAREN":
                self.in_parentheses -= 1

            tokens.append(token)

        return tokens
```

**Test Case**:
```pw
function multiline(
    a: int,
    b: int,
    c: int
) -> int {
    return a + b + c;
}

let result = multiline(
    1,
    2,
    3
);
```

---

### Error Recovery

**Research**: How to continue parsing after errors?

**Industry Practice**:
1. **Panic Mode** - Skip tokens until synchronization point (`;`, `}`)
2. **Error Productions** - Add grammar rules for common errors
3. **Partial AST** - Return incomplete but valid AST

**PW Approach** (simple panic mode):
```python
class Parser:
    def parse(self):
        nodes = []
        while not self.is_at_end():
            try:
                node = self.parse_statement()
                nodes.append(node)
            except ParseError as e:
                self.errors.append(e)
                self.synchronize()  # Skip to next statement

    def synchronize(self):
        """Skip tokens until synchronization point."""
        while not self.is_at_end():
            if self.previous().type == "SEMICOLON":
                return
            if self.peek().type in ["FUNCTION", "CLASS", "IF", "FOR", "WHILE"]:
                return
            self.advance()
```

**Benefit**: Parser reports ALL errors, not just first one

---

## 6. CLI Tool Research

### Industry-Standard CLI Patterns

**Research**: How do modern compilers structure CLIs?

**Examples**:
- **rustc**: `rustc main.rs -o main`
- **tsc**: `tsc main.ts --outDir dist`
- **go build**: `go build -o app main.go`
- **gcc**: `gcc main.c -o main`

**Common Patterns**:
1. Input file as positional argument
2. Output file via `-o` flag
3. Language/target via `--lang` or `--target`
4. Verbose mode via `-v` or `--verbose`
5. Help via `--help`

**PW CLI Design**:
```bash
pw build <file> [options]
  -o, --output <file>      Output file
  --lang <language>        Target language (python, go, rust, ts, cs)
  -v, --verbose            Verbose output
  --version                Show version

pw run <file>              Run PW file (compile to Python + execute)

pw compile <file>          Compile to MCP JSON
  -o, --output <file>      Output JSON file

pw format <file>           Format PW code
pw lint <file>             Lint PW code
pw repl                    Start REPL
```

**Implementation** (using Click):
```python
import click

@click.group()
@click.version_option(version='2.1.0b3')
def cli():
    """PW - Universal Programming Language"""
    pass

@cli.command()
@click.argument('file', type=click.Path(exists=True))
@click.option('--lang', default='python', type=click.Choice(['python', 'go', 'rust', 'ts', 'cs']))
@click.option('-o', '--output', type=click.Path())
@click.option('-v', '--verbose', is_flag=True)
def build(file, lang, output, verbose):
    """Compile PW to target language."""
    if verbose:
        click.echo(f"Compiling {file} to {lang}...")

    # Compile
    ir = parse_file(file)
    code = generate_code(ir, lang)

    # Output
    if output:
        Path(output).write_text(code)
        if verbose:
            click.echo(f"Written to {output}")
    else:
        click.echo(code)
```

---

## 7. Key Takeaways for Implementation

### 1. Type System
- Use gradual typing (static + inference + any)
- Simple Hindley-Milner for inference
- Conservative cross-language mapping

### 2. Loops
- Python-style for loop syntax
- Support for-in, enumerate, range
- While loops straightforward

### 3. Arrays
- Generic syntax: `array<T>`
- Built-in functions: `len()`, `sum()`
- Methods where universal: `push()`, `pop()`
- Functional where universal: `filter()`, `map()`

### 4. Classes
- Map to language idioms (struct in Go/Rust)
- Constructor → language-specific init
- Defer inheritance to v2.2
- Conservative Rust (clone by default)

### 5. Parser
- Context-aware lexer for multi-line
- Panic mode error recovery
- Better error messages with context

### 6. CLI
- Industry-standard patterns
- Click framework
- `build`, `run`, `compile` commands

---

**Research Completed**: 2025-10-07
**Next Step**: Begin Phase 1.1 - Type Validation System
