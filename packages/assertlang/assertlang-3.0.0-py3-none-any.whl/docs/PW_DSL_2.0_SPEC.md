# PW DSL 2.0 Language Specification

**Version**: 2.0.0-alpha
**Last Updated**: 2025-10-04
**Status**: Draft

---

## Table of Contents

1. [Introduction](#introduction)
2. [Lexical Structure](#lexical-structure)
3. [Grammar (BNF)](#grammar-bnf)
4. [Language Constructs](#language-constructs)
5. [Type System](#type-system)
6. [Expressions](#expressions)
7. [Statements](#statements)
8. [Semantic Rules](#semantic-rules)
9. [Error Conditions](#error-conditions)
10. [Examples](#examples)

---

## 1. Introduction

PW DSL 2.0 is a universal intermediate representation language designed to bridge arbitrary code across multiple programming languages. It extends PW DSL 1.0 (MCP-focused) to support general-purpose programming constructs including functions, classes, control flow, and complex expressions.

### Design Principles

1. **Readable** - Clear, Python-like syntax
2. **Consistent** - Uniform structure across constructs
3. **Extensible** - Easy to add new features
4. **Unambiguous** - One way to express each concept
5. **Language-Agnostic** - No bias toward any source/target language

### Key Features

- Module system with imports
- Custom type definitions (structs, enums)
- Functions with type annotations
- Classes with properties and methods
- Control flow (if/for/while/try-catch)
- Rich expression syntax
- Error handling primitives

---

## 2. Lexical Structure

### 2.1 Tokens

**Keywords**:
```
module      version     import      from        as
type        enum        function    class       constructor
params      returns     throws      body        properties
method      let         if          else        elif
for         in          while       try         catch
finally     throw       return      break       continue
pass        null        true        false       and
or          not         async       await
```

**Operators**:
```
Arithmetic: +  -  *  /  %  **  //
Comparison: ==  !=  <  >  <=  >=
Logical:    and  or  not
Bitwise:    &  |  ^  ~  <<  >>
Assignment: =  +=  -= *=  /=
Member:     .  ::
Index:      [  ]
Call:       (  )
```

**Delimiters**:
```
:  ,  ;  {  }  [  ]  (  )
```

**Literals**:
```
Integer:    42  -10  0xFF  0b1010  0o77
Float:      3.14  -0.5  1.23e-4
String:     "hello"  'world'  """multiline"""
Boolean:    true  false
Null:       null
```

**Identifiers**:
- Must start with letter or underscore: `[a-zA-Z_]`
- Followed by letters, digits, underscores: `[a-zA-Z0-9_]*`
- Examples: `user_id`, `ProcessPayment`, `_private`

**Comments**:
```pw
# Single-line comment

"""
Multi-line comment
or documentation string
"""
```

### 2.2 Indentation

PW DSL 2.0 uses **indentation** to denote block structure (like Python):
- Indentation must be **2 spaces per level** (no tabs)
- Inconsistent indentation is a syntax error
- Blocks end when indentation decreases

---

## 3. Grammar (BNF)

### 3.1 Program Structure

```bnf
<program>        ::= <module_decl>? <import_list>? <declaration_list>

<module_decl>    ::= "module" <identifier> <newline>
                     "version" <version_string> <newline>

<import_list>    ::= <import_stmt>+

<import_stmt>    ::= "import" <identifier> <newline>
                   | "import" <identifier> "from" <identifier> <newline>
                   | "import" <identifier> "as" <identifier> <newline>

<declaration_list> ::= <declaration>+

<declaration>    ::= <type_def>
                   | <enum_def>
                   | <function_def>
                   | <class_def>
```

### 3.2 Type Definitions

```bnf
<type_def>       ::= "type" <identifier> ":" <newline>
                     <indent> <field_list> <dedent>

<field_list>     ::= <field>+

<field>          ::= <identifier> <type_annotation> <newline>

<type_annotation> ::= <type_expr> <optional_marker>?

<type_expr>      ::= <primitive_type>
                   | <identifier>
                   | "array" "<" <type_expr> ">"
                   | "map" "<" <type_expr> "," <type_expr> ">"
                   | <type_expr> "|" <type_expr>  # Union type

<optional_marker> ::= "?"

<primitive_type> ::= "string" | "int" | "float" | "bool" | "null" | "any"
```

### 3.3 Enum Definitions

```bnf
<enum_def>       ::= "enum" <identifier> ":" <newline>
                     <indent> <variant_list> <dedent>

<variant_list>   ::= <variant>+

<variant>        ::= "-" <identifier> <newline>
                   | "-" <identifier> "(" <field_list> ")" <newline>
```

### 3.4 Function Definitions

```bnf
<function_def>   ::= <async_marker>? "function" <identifier> ":" <newline>
                     <indent>
                       <params_block>?
                       <returns_block>?
                       <throws_block>?
                       <body_block>
                     <dedent>

<async_marker>   ::= "async"

<params_block>   ::= "params:" <newline>
                     <indent> <param_list> <dedent>

<param_list>     ::= <param>+

<param>          ::= <identifier> <type_annotation> <default_value>? <newline>

<default_value>  ::= "=" <literal>

<returns_block>  ::= "returns:" <newline>
                     <indent> <return_field_list> <dedent>

<return_field_list> ::= <identifier> <type_annotation> <newline>+

<throws_block>   ::= "throws:" <newline>
                     <indent> <exception_list> <dedent>

<exception_list> ::= "-" <identifier> <newline>+

<body_block>     ::= "body:" <newline>
                     <indent> <statement_list> <dedent>

<statement_list> ::= <statement>+
```

### 3.5 Class Definitions

```bnf
<class_def>      ::= "class" <identifier> <inheritance>? ":" <newline>
                     <indent>
                       <properties_block>?
                       <constructor_block>?
                       <method_list>?
                     <dedent>

<inheritance>    ::= ":" <identifier> ("," <identifier>)*

<properties_block> ::= "properties:" <newline>
                       <indent> <property_list> <dedent>

<property_list>  ::= <property>+

<property>       ::= <identifier> <type_annotation> <default_value>? <newline>

<constructor_block> ::= "constructor:" <newline>
                        <indent>
                          <params_block>?
                          <body_block>
                        <dedent>

<method_list>    ::= <method>+

<method>         ::= "method" <identifier> ":" <newline>
                     <indent>
                       <params_block>?
                       <returns_block>?
                       <throws_block>?
                       <body_block>
                     <dedent>
```

### 3.6 Statements

```bnf
<statement>      ::= <assignment>
                   | <if_stmt>
                   | <for_stmt>
                   | <while_stmt>
                   | <try_stmt>
                   | <return_stmt>
                   | <throw_stmt>
                   | <break_stmt>
                   | <continue_stmt>
                   | <pass_stmt>
                   | <expression_stmt>

<assignment>     ::= "let" <identifier> "=" <expression> <newline>
                   | <identifier> "=" <expression> <newline>
                   | <identifier> <compound_op> <expression> <newline>

<compound_op>    ::= "+=" | "-=" | "*=" | "/="

<if_stmt>        ::= "if" <expression> ":" <newline>
                     <indent> <statement_list> <dedent>
                     <elif_clause>*
                     <else_clause>?

<elif_clause>    ::= "elif" <expression> ":" <newline>
                     <indent> <statement_list> <dedent>

<else_clause>    ::= "else:" <newline>
                     <indent> <statement_list> <dedent>

<for_stmt>       ::= "for" <identifier> "in" <expression> ":" <newline>
                     <indent> <statement_list> <dedent>

<while_stmt>     ::= "while" <expression> ":" <newline>
                     <indent> <statement_list> <dedent>

<try_stmt>       ::= "try:" <newline>
                     <indent> <statement_list> <dedent>
                     <catch_clause>+
                     <finally_clause>?

<catch_clause>   ::= "catch" <identifier> <identifier>? ":" <newline>
                     <indent> <statement_list> <dedent>

<finally_clause> ::= "finally:" <newline>
                     <indent> <statement_list> <dedent>

<return_stmt>    ::= "return" <expression>? <newline>

<throw_stmt>     ::= "throw" <expression> <newline>

<break_stmt>     ::= "break" <newline>

<continue_stmt>  ::= "continue" <newline>

<pass_stmt>      ::= "pass" <newline>

<expression_stmt> ::= <expression> <newline>
```

### 3.7 Expressions

```bnf
<expression>     ::= <ternary_expr>

<ternary_expr>   ::= <logical_or> ("if" <logical_or> "else" <logical_or>)?

<logical_or>     ::= <logical_and> ("or" <logical_and>)*

<logical_and>    ::= <logical_not> ("and" <logical_not>)*

<logical_not>    ::= "not"? <comparison>

<comparison>     ::= <bitwise_or> (<comp_op> <bitwise_or>)*

<comp_op>        ::= "==" | "!=" | "<" | ">" | "<=" | ">="

<bitwise_or>     ::= <bitwise_xor> ("|" <bitwise_xor>)*

<bitwise_xor>    ::= <bitwise_and> ("^" <bitwise_and>)*

<bitwise_and>    ::= <shift> ("&" <shift>)*

<shift>          ::= <addition> (("<<" | ">>") <addition>)*

<addition>       ::= <multiplication> (("+" | "-") <multiplication>)*

<multiplication> ::= <unary> (("*" | "/" | "%" | "//" | "**") <unary>)*

<unary>          ::= ("-" | "+" | "~")? <postfix>

<postfix>        ::= <primary> <postfix_op>*

<postfix_op>     ::= <call>
                   | <index>
                   | <member_access>

<call>           ::= "(" <arg_list>? ")"

<arg_list>       ::= <argument> ("," <argument>)*

<argument>       ::= <expression>
                   | <identifier> ":" <expression>  # Named argument

<index>          ::= "[" <expression> "]"

<member_access>  ::= "." <identifier>

<primary>        ::= <literal>
                   | <identifier>
                   | <lambda>
                   | <array_literal>
                   | <map_literal>
                   | <await_expr>
                   | "(" <expression> ")"

<lambda>         ::= "lambda" <param_list>? ":" <expression>

<array_literal>  ::= "[" <expr_list>? "]"

<expr_list>      ::= <expression> ("," <expression>)*

<map_literal>    ::= "{" <map_entry_list>? "}"

<map_entry_list> ::= <map_entry> ("," <map_entry>)*

<map_entry>      ::= <identifier> ":" <expression>
                   | <string> ":" <expression>

<await_expr>     ::= "await" <expression>

<literal>        ::= <integer>
                   | <float>
                   | <string>
                   | <boolean>
                   | "null"
```

---

## 4. Language Constructs

### 4.1 Module Declaration

Declares the module name and version.

```pw
module payment_processor
version 1.0.0
```

**Rules**:
- Module declaration is optional (defaults to "main" v1.0.0)
- Version follows semantic versioning (major.minor.patch)

### 4.2 Imports

Import external modules or specific items.

```pw
import http_client
import database from storage
import json as JSON
```

**Forms**:
- `import <module>` - Import entire module
- `import <module> from <package>` - Import module from package
- `import <module> as <alias>` - Import with alias

### 4.3 Type Definitions

Define custom struct-like types.

```pw
type User:
  id string
  name string
  email string
  age int?
  metadata map<string, any>
```

**Features**:
- Optional fields with `?` suffix
- Nested types allowed
- Generic types: `array<T>`, `map<K, V>`

### 4.4 Enum Definitions

Define enumeration types.

```pw
enum Status:
  - pending
  - processing
  - completed
  - failed

enum Result:
  - ok(value any)
  - error(message string, code int)
```

**Features**:
- Simple variants (no data)
- Tuple variants (with typed data)

### 4.5 Function Definitions

Define standalone functions.

```pw
function process_payment:
  params:
    amount float
    user_id string
    options map<string, any>?
  returns:
    status Status
    transaction_id string
  throws:
    - ValidationError
    - PaymentError
  body:
    let user = database.get_user(user_id)
    if user == null:
      throw ValidationError("User not found")

    let result = charge_card(amount)
    return {
      status: Status.completed,
      transaction_id: result.id
    }
```

**Features**:
- Typed parameters with optional defaults
- Multiple return values (tuple destructuring)
- Explicit exception declarations
- `async` functions supported

### 4.6 Class Definitions

Define classes with properties and methods.

```pw
class PaymentProcessor:
  properties:
    api_key string
    base_url string
    retry_count int = 3

  constructor:
    params:
      api_key string
      base_url string = "https://api.example.com"
    body:
      self.api_key = api_key
      self.base_url = base_url

  method charge:
    params:
      amount float
    returns:
      transaction_id string
    throws:
      - PaymentError
    body:
      let response = http_client.post(
        self.base_url + "/charge",
        {amount: amount, key: self.api_key}
      )

      if response.status != 200:
        throw PaymentError("Charge failed")

      return response.data.transaction_id

  method refund:
    params:
      transaction_id string
    returns:
      success bool
    body:
      # Implementation here
      pass
```

**Features**:
- Properties with optional default values
- Constructor with initialization
- Instance methods with `self` reference
- Inheritance support (future)

---

## 5. Type System

### 5.1 Primitive Types

```
string   - Text data (UTF-8)
int      - Integer numbers (platform-dependent size)
float    - Floating-point numbers (64-bit)
bool     - Boolean (true/false)
null     - Null/None/nil value
any      - Dynamic type (for type inference)
```

### 5.2 Collection Types

```
array<T>        - Ordered list of elements
map<K, V>       - Key-value dictionary
set<T>          - Unique element collection (future)
```

### 5.3 Type Modifiers

```
T?              - Optional type (nullable)
T | U           - Union type (either T or U)
readonly T      - Immutable type (future)
```

### 5.4 Type Annotations

All identifiers can have type annotations:

```pw
let name string = "Alice"
let age int = 30
let scores array<int> = [95, 87, 92]
let user User = get_user("123")
```

---

## 6. Expressions

### 6.1 Literal Expressions

```pw
# Integers
42
-10
0xFF      # Hex
0b1010    # Binary
0o77      # Octal

# Floats
3.14
-0.5
1.23e-4   # Scientific

# Strings
"hello"
'world'
"""
multi
line
"""

# Boolean
true
false

# Null
null
```

### 6.2 Arithmetic Expressions

```pw
a + b         # Addition
a - b         # Subtraction
a * b         # Multiplication
a / b         # Division
a % b         # Modulo
a ** b        # Exponentiation
a // b        # Floor division
```

### 6.3 Comparison Expressions

```pw
a == b        # Equal
a != b        # Not equal
a < b         # Less than
a > b         # Greater than
a <= b        # Less or equal
a >= b        # Greater or equal
```

### 6.4 Logical Expressions

```pw
a and b       # Logical AND
a or b        # Logical OR
not a         # Logical NOT
```

### 6.5 Bitwise Expressions

```pw
a & b         # Bitwise AND
a | b         # Bitwise OR
a ^ b         # Bitwise XOR
~a            # Bitwise NOT
a << n        # Left shift
a >> n        # Right shift
```

### 6.6 Member Access

```pw
object.property        # Dot notation
object.method()        # Method call
object["key"]          # Index notation
object[0]              # Array index
```

### 6.7 Function Calls

```pw
func(arg1, arg2)              # Positional args
func(name: value)             # Named args
func(arg1, name: value)       # Mixed
```

### 6.8 Array/Map Literals

```pw
# Arrays
[1, 2, 3]
["a", "b", "c"]
[user1, user2, user3]

# Maps (object literals)
{name: "Alice", age: 30}
{id: user.id, email: user.email}
{"key1": value1, "key2": value2}
```

### 6.9 Lambda Expressions

```pw
lambda x: x * 2
lambda x, y: x + y
lambda: 42
```

### 6.10 Ternary Expressions

```pw
value if condition else default
x if x > 0 else 0
```

### 6.11 Await Expressions

```pw
await async_function()
let result = await fetch_data()
```

---

## 7. Statements

### 7.1 Variable Assignment

```pw
let x = 10                    # Declaration with inference
let y int = 20                # Declaration with type
x = 30                        # Reassignment
x += 5                        # Compound assignment
```

### 7.2 If Statements

```pw
if condition:
  # body

if x > 0:
  # positive
elif x < 0:
  # negative
else:
  # zero
```

### 7.3 For Loops

```pw
for item in collection:
  # body

for user in users:
  print(user.name)

for i in range(10):
  # 0..9
```

### 7.4 While Loops

```pw
while condition:
  # body

while x > 0:
  x = x - 1
```

### 7.5 Try-Catch

```pw
try:
  risky_operation()
catch ValidationError e:
  handle_validation(e)
catch PaymentError e:
  handle_payment(e)
catch Error e:
  handle_generic(e)
finally:
  cleanup()
```

### 7.6 Return/Throw

```pw
return value
return {status: "ok", data: result}
throw ValidationError("Invalid input")
```

### 7.7 Break/Continue/Pass

```pw
for item in items:
  if item.skip:
    continue
  if item.stop:
    break
  process(item)

# Placeholder
function not_implemented:
  body:
    pass
```

---

## 8. Semantic Rules

### 8.1 Variable Scope

- **Module scope**: Top-level variables/functions
- **Function scope**: Variables declared in function body
- **Block scope**: Variables in if/for/while blocks
- **Closure**: Lambdas capture enclosing scope

### 8.2 Name Resolution

1. Check local scope (innermost block)
2. Check enclosing function scope
3. Check class scope (if in method)
4. Check module scope
5. Check imported modules
6. Error if not found

### 8.3 Type Checking

- **Inference**: Types inferred from literals/expressions
- **Annotation**: Explicit types override inference
- **Coercion**: No implicit type conversion
- **Validation**: Type mismatches are errors

### 8.4 Control Flow

- **Reachability**: All code paths must be reachable
- **Returns**: Functions with return type must return in all paths
- **Breaks**: Only allowed in loops
- **Continues**: Only allowed in loops

### 8.5 Error Handling

- **Throws**: Declared exceptions must be documented
- **Propagation**: Uncaught exceptions propagate to caller
- **Finally**: Always executes (even with return/throw)

---

## 9. Error Conditions

### 9.1 Syntax Errors

```
E_SYNTAX_INDENT       - Inconsistent indentation
E_SYNTAX_KEYWORD      - Invalid keyword usage
E_SYNTAX_EXPR         - Malformed expression
E_SYNTAX_STMT         - Malformed statement
E_SYNTAX_TYPE         - Invalid type annotation
E_SYNTAX_EOF          - Unexpected end of file
```

### 9.2 Semantic Errors

```
E_SEMANTIC_UNDEFINED  - Undefined variable/function
E_SEMANTIC_REDEFINED  - Variable redefinition
E_SEMANTIC_TYPE       - Type mismatch
E_SEMANTIC_RETURN     - Missing return statement
E_SEMANTIC_BREAK      - Break outside loop
E_SEMANTIC_CONTINUE   - Continue outside loop
```

### 9.3 Runtime Errors (for interpreter)

```
E_RUNTIME_NULL        - Null pointer dereference
E_RUNTIME_INDEX       - Index out of bounds
E_RUNTIME_KEY         - Key not found
E_RUNTIME_CAST        - Invalid type cast
E_RUNTIME_THROW       - Uncaught exception
```

---

## 10. Examples

### 10.1 Simple Function

```pw
module math_utils
version 1.0.0

function factorial:
  params:
    n int
  returns:
    result int
  body:
    if n <= 1:
      return 1
    return n * factorial(n - 1)
```

### 10.2 Class with Methods

```pw
class BankAccount:
  properties:
    balance float = 0.0
    owner string

  constructor:
    params:
      owner string
      initial_balance float = 0.0
    body:
      self.owner = owner
      self.balance = initial_balance

  method deposit:
    params:
      amount float
    returns:
      new_balance float
    throws:
      - ValueError
    body:
      if amount <= 0:
        throw ValueError("Amount must be positive")
      self.balance += amount
      return self.balance

  method withdraw:
    params:
      amount float
    returns:
      new_balance float
    throws:
      - ValueError
      - InsufficientFunds
    body:
      if amount <= 0:
        throw ValueError("Amount must be positive")
      if amount > self.balance:
        throw InsufficientFunds("Insufficient balance")
      self.balance -= amount
      return self.balance
```

### 10.3 Error Handling

```pw
function safe_divide:
  params:
    a float
    b float
  returns:
    result float | null
  body:
    try:
      if b == 0:
        throw DivisionByZero("Cannot divide by zero")
      return a / b
    catch DivisionByZero e:
      print("Error: " + e.message)
      return null
```

### 10.4 Async Function

```pw
async function fetch_user:
  params:
    user_id string
  returns:
    user User | null
  throws:
    - NetworkError
  body:
    try:
      let response = await http_client.get("/users/" + user_id)
      if response.status == 200:
        return response.data
      return null
    catch NetworkError e:
      print("Network error: " + e.message)
      throw e
```

### 10.5 Complex Data Processing

```pw
module data_processor
version 2.0.0

import json
import database from storage

type ProcessResult:
  success bool
  processed_count int
  errors array<string>

function process_batch:
  params:
    items array<map<string, any>>
    config map<string, any>?
  returns:
    result ProcessResult
  throws:
    - ValidationError
  body:
    let errors array<string> = []
    let count int = 0

    for item in items:
      try:
        validate_item(item)
        let transformed = transform(item, config)
        database.save(transformed)
        count += 1
      catch ValidationError e:
        errors.append(e.message)
      catch DatabaseError e:
        errors.append("DB error: " + e.message)

    return {
      success: count > 0,
      processed_count: count,
      errors: errors
    }

function validate_item:
  params:
    item map<string, any>
  throws:
    - ValidationError
  body:
    if not item.has("id"):
      throw ValidationError("Missing id field")
    if not item.has("type"):
      throw ValidationError("Missing type field")
    pass

function transform:
  params:
    item map<string, any>
    config map<string, any>?
  returns:
    transformed map<string, any>
  body:
    let result map<string, any> = {}
    result["id"] = item["id"]
    result["type"] = item["type"]

    if config != null and config.has("normalize"):
      result["normalized"] = true

    return result
```

---

## Appendix A: Reserved Keywords

```
and         any         array       as          async
await       bool        body        break       catch
class       constructor continue    elif        else
enum        false       finally     float       for
from        function    if          import      in
int         lambda      let         map         method
module      not         null        or          params
pass        properties  return      returns     self
string      throw       throws      true        try
type        version     while
```

---

## Appendix B: Operator Precedence

From highest to lowest:

1. Member access (`.`), indexing (`[]`), call (`()`)
2. Unary (`-`, `+`, `~`, `not`)
3. Exponentiation (`**`)
4. Multiplication (`*`, `/`, `%`, `//`)
5. Addition (`+`, `-`)
6. Bitwise shift (`<<`, `>>`)
7. Bitwise AND (`&`)
8. Bitwise XOR (`^`)
9. Bitwise OR (`|`)
10. Comparison (`==`, `!=`, `<`, `>`, `<=`, `>=`)
11. Logical NOT (`not`)
12. Logical AND (`and`)
13. Logical OR (`or`)
14. Ternary (`if-else`)
15. Assignment (`=`, `+=`, etc.)

---

## Appendix C: Compatibility Notes

### V1 → V2 Migration

PW DSL 2.0 is **mostly backward compatible** with V1:

**Breaking Changes**:
- `expose` directive removed (use `function` instead)
- `@v1` version suffix removed (use module version)
- MCP-specific directives deprecated

**Migration Path**:
```pw
# V1 (deprecated)
expose get_user@v1:
  params:
    user_id string
  returns:
    user User

# V2 (current)
function get_user:
  params:
    user_id string
  returns:
    user User
```

---

## Appendix D: Future Extensions

Planned for future versions:

- **Generics**: `function map<T, U>(items array<T>, f lambda T -> U)`
- **Decorators**: `@cached`, `@validate`, etc.
- **Pattern Matching**: `match value: case pattern: ...`
- **Traits/Interfaces**: `interface Serializable: method serialize()`
- **Macros**: Compile-time code generation
- **Modules as packages**: Nested module hierarchy

---

**End of Specification**
