"""
Promptware Intermediate Representation (IR)

This module defines the complete IR node structure for the Promptware universal
code translation system. The IR is language-agnostic and designed following
LLVM IR principles.

Design Principles:
1. Language-agnostic - No bias toward any source or target language
2. Type-safe - All nodes preserve type information
3. Metadata-rich - Source locations, comments, and annotations
4. Composable - Nodes nest cleanly into larger structures
5. Validatable - Easy to verify semantic correctness

The IR supports:
- Modules, imports, and namespaces
- Functions, classes, and methods
- Control flow (if/for/while/try-catch)
- Expressions (arithmetic, logical, function calls)
- Type definitions (primitives, collections, custom types)
- Error handling (throws, try/catch)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union


# ============================================================================
# Enumerations
# ============================================================================


class NodeType(Enum):
    """Enumeration of all IR node types."""

    # Module-level
    MODULE = "module"
    IMPORT = "import"

    # Types
    TYPE = "type"
    TYPE_DEFINITION = "type_definition"
    ENUM = "enum"
    ENUM_VARIANT = "enum_variant"

    # Functions and classes
    FUNCTION = "function"
    PARAMETER = "parameter"
    CLASS = "class"
    PROPERTY = "property"

    # Statements
    IF = "if"
    FOR = "for"
    FOR_C_STYLE = "for_c_style"
    WHILE = "while"
    SWITCH = "switch"
    CASE = "case"
    TRY = "try"
    CATCH = "catch"
    ASSIGNMENT = "assignment"
    RETURN = "return"
    THROW = "throw"
    BREAK = "break"
    CONTINUE = "continue"
    PASS = "pass"
    WITH = "with"
    DEFER = "defer"
    DESTRUCTURE = "destructure"

    # Go-specific statements
    SELECT = "select"
    GOROUTINE = "goroutine"
    CHANNEL = "channel"

    # Expressions
    CALL = "call"
    BINARY_OP = "binary_op"
    UNARY_OP = "unary_op"
    LITERAL = "literal"
    IDENTIFIER = "identifier"
    PROPERTY_ACCESS = "property_access"
    INDEX = "index"
    LAMBDA = "lambda"
    ARRAY = "array"
    MAP = "map"
    TERNARY = "ternary"
    COMPREHENSION = "comprehension"
    FSTRING = "fstring"
    SLICE = "slice"
    SPREAD = "spread"
    AWAIT = "await"
    DECORATOR = "decorator"
    PATTERN_MATCH = "pattern_match"
    OLD_EXPR = "old_expr"  # For `old` keyword in postconditions

    # Contract annotations
    CONTRACT_CLAUSE = "contract_clause"  # @requires, @ensures, @invariant
    CONTRACT_ANNOTATION = "contract_annotation"  # @contract, @operation


class BinaryOperator(Enum):
    """Binary operators."""

    # Arithmetic
    ADD = "+"
    SUBTRACT = "-"
    MULTIPLY = "*"
    DIVIDE = "/"
    MODULO = "%"
    POWER = "**"
    FLOOR_DIVIDE = "//"

    # Comparison
    EQUAL = "=="
    NOT_EQUAL = "!="
    LESS_THAN = "<"
    LESS_EQUAL = "<="
    GREATER_THAN = ">"
    GREATER_EQUAL = ">="

    # Logical
    AND = "and"
    OR = "or"

    # Bitwise
    BIT_AND = "&"
    BIT_OR = "|"
    BIT_XOR = "^"
    LEFT_SHIFT = "<<"
    RIGHT_SHIFT = ">>"

    # Other
    IN = "in"
    NOT_IN = "not in"
    IS = "is"
    IS_NOT = "is not"


class UnaryOperator(Enum):
    """Unary operators."""

    NOT = "not"
    NEGATE = "-"
    POSITIVE = "+"
    BIT_NOT = "~"


class LiteralType(Enum):
    """Types of literal values."""

    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    NULL = "null"


# ============================================================================
# Base Classes
# ============================================================================


@dataclass
class SourceLocation:
    """Source location information for IR nodes."""

    file: Optional[str] = None
    line: Optional[int] = None
    column: Optional[int] = None
    end_line: Optional[int] = None
    end_column: Optional[int] = None

    def __repr__(self) -> str:
        if self.file and self.line:
            return f"{self.file}:{self.line}:{self.column or 0}"
        elif self.line:
            return f"line {self.line}:{self.column or 0}"
        return "unknown location"


class IRNode:
    """
    Base class for all IR nodes.

    All IR nodes include:
    - type: The node type enum
    - metadata: Arbitrary metadata (source location, comments, etc.)

    Note: This is not a dataclass itself to avoid field ordering issues in subclasses.
    """

    def __init__(self, type: NodeType, metadata: Optional[Dict[str, Any]] = None):
        self.type = type
        self.metadata = metadata if metadata is not None else {}

    @property
    def location(self) -> Optional[SourceLocation]:
        """Get source location from metadata."""
        return self.metadata.get("location")

    @location.setter
    def location(self, value: SourceLocation) -> None:
        """Set source location in metadata."""
        self.metadata["location"] = value

    @property
    def comment(self) -> Optional[str]:
        """Get comment from metadata."""
        return self.metadata.get("comment")

    @comment.setter
    def comment(self, value: str) -> None:
        """Set comment in metadata."""
        self.metadata["comment"] = value


# ============================================================================
# Module-Level Nodes
# ============================================================================


@dataclass
class IRImport(IRNode):
    """
    Import statement.

    Examples:
        import http_client
        import database from storage
        from typing import List, Dict
    """

    module: str  # Module name (e.g., "http_client")
    alias: Optional[str] = None  # Import alias (e.g., "import x as y")
    items: List[str] = field(default_factory=list)  # Specific items (e.g., "from x import a, b")

    def __post_init__(self) -> None:
        super().__init__(type=NodeType.IMPORT)


@dataclass
class IRModule(IRNode):
    """
    Top-level module/file representation.

    A module contains:
    - Imports
    - Type definitions
    - Functions
    - Classes
    - Module-level variables (as assignments)
    """

    name: str
    version: str = "1.0.0"
    imports: List[IRImport] = field(default_factory=list)
    types: List[IRTypeDefinition] = field(default_factory=list)
    enums: List[IREnum] = field(default_factory=list)
    functions: List[IRFunction] = field(default_factory=list)
    classes: List[IRClass] = field(default_factory=list)
    module_vars: List[IRAssignment] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.type = NodeType.MODULE
        super().__init__(type=NodeType.MODULE)


# ============================================================================
# Type Nodes
# ============================================================================


@dataclass
class IRType(IRNode):
    """
    Type reference.

    Represents a type in the IR. Can be:
    - Primitive: "string", "int", "float", "bool", "null", "any"
    - Collection: "array<T>", "map<K,V>"
    - Custom: "User", "Payment"
    - Optional: "T?"
    - Union: "A|B|C"
    """

    name: str  # Type name
    generic_args: List[IRType] = field(default_factory=list)  # Generic arguments
    is_optional: bool = False  # T?
    union_types: List[IRType] = field(default_factory=list)  # A|B|C

    def __post_init__(self) -> None:
        self.type = NodeType.TYPE
        super().__init__(type=NodeType.TYPE)

    def __str__(self) -> str:
        """String representation of type."""
        result = self.name

        # Add generic arguments
        if self.generic_args:
            args = ", ".join(str(arg) for arg in self.generic_args)
            result = f"{result}<{args}>"

        # Add union types
        if self.union_types:
            types = "|".join(str(t) for t in [self] + self.union_types)
            result = types

        # Add optional marker
        if self.is_optional:
            result = f"{result}?"

        return result


@dataclass
class IRTypeDefinition(IRNode):
    """
    Type definition (struct/class-like type).

    Example:
        type User:
          id: string
          name: string
          age: int?
    """

    name: str
    fields: List[IRProperty] = field(default_factory=list)
    doc: Optional[str] = None

    def __post_init__(self) -> None:
        self.type = NodeType.TYPE_DEFINITION
        super().__init__(type=NodeType.TYPE_DEFINITION)


@dataclass
class IREnumVariant(IRNode):
    """
    Enum variant.

    Example:
        - pending
        - completed(string)  # With associated value
    """

    name: str
    value: Optional[Union[str, int]] = None
    associated_types: List[IRType] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.type = NodeType.ENUM_VARIANT
        super().__init__(type=NodeType.ENUM_VARIANT)


@dataclass
class IREnum(IRNode):
    """
    Enumeration definition.

    Example:
        enum Status:
          - pending
          - completed
          - failed

        enum Option<T>:
          - Some(value: T)
          - None
    """

    name: str
    generic_params: List[str] = field(default_factory=list)  # Generic type parameters
    variants: List[IREnumVariant] = field(default_factory=list)
    doc: Optional[str] = None

    def __post_init__(self) -> None:
        self.type = NodeType.ENUM
        super().__init__(type=NodeType.ENUM)


# ============================================================================
# Function and Class Nodes
# ============================================================================


@dataclass
class IRParameter(IRNode):
    """
    Function parameter.

    Example:
        amount: float
        user_id: string
        options: map<string, any>?
    """

    name: str
    param_type: IRType
    default_value: Optional[IRExpression] = None
    is_variadic: bool = False  # *args or **kwargs

    def __post_init__(self) -> None:
        self.type = NodeType.PARAMETER
        super().__init__(type=NodeType.PARAMETER)


@dataclass
class IRFunction(IRNode):
    """
    Function definition.

    Example:
        function process_payment:
          params:
            amount: float
            user_id: string
          returns:
            status: string
          throws:
            - ValidationError
          body:
            # statements

        function option_map<T, U>(opt: Option<T>, fn: function(T) -> U) -> Option<U>:
          # body

        # With contract annotations:
        @operation(idempotent=true)
        function createUser(name: string) -> User {
          @requires name_not_empty: str.length(name) >= 1
          @ensures id_positive: result.id > 0
          @effects [database.write, event.emit("user.created")]
          // body
        }
    """

    name: str
    generic_params: List[str] = field(default_factory=list)  # Generic type parameters
    params: List[IRParameter] = field(default_factory=list)
    return_type: Optional[IRType] = None
    throws: List[str] = field(default_factory=list)
    body: List[IRStatement] = field(default_factory=list)
    is_async: bool = False
    is_static: bool = False
    is_private: bool = False
    decorators: List[Union[str, 'IRDecorator']] = field(default_factory=list)
    doc: Optional[str] = None

    # Contract annotations
    requires: List['IRContractClause'] = field(default_factory=list)  # Preconditions
    ensures: List['IRContractClause'] = field(default_factory=list)  # Postconditions
    effects: List[str] = field(default_factory=list)  # Side effects
    operation_metadata: Dict[str, Any] = field(default_factory=dict)  # @operation metadata

    def __post_init__(self) -> None:
        self.type = NodeType.FUNCTION
        super().__init__(type=NodeType.FUNCTION)


@dataclass
class IRProperty(IRNode):
    """
    Class property.

    Example:
        api_key: string
        base_url: string
    """

    name: str
    prop_type: IRType
    default_value: Optional[IRExpression] = None
    is_private: bool = False
    is_readonly: bool = False

    def __post_init__(self) -> None:
        self.type = NodeType.PROPERTY
        super().__init__(type=NodeType.PROPERTY)


@dataclass
class IRClass(IRNode):
    """
    Class definition.

    Example:
        class PaymentProcessor:
          properties:
            api_key: string
            base_url: string
          constructor:
            params:
              api_key: string
            body:
              self.api_key = api_key
          methods:
            - function charge: ...

        class List<T>:
          items: array<T>

        # With contract annotations:
        @contract(version="1.0.0")
        service UserService {
          @invariant count_non_negative: this.userCount >= 0
          // ... methods
        }
    """

    name: str
    generic_params: List[str] = field(default_factory=list)  # Generic type parameters
    properties: List[IRProperty] = field(default_factory=list)
    methods: List[IRFunction] = field(default_factory=list)
    constructor: Optional[IRFunction] = None
    base_classes: List[str] = field(default_factory=list)
    doc: Optional[str] = None

    # Contract annotations
    invariants: List['IRContractClause'] = field(default_factory=list)  # Class invariants
    contract_metadata: Dict[str, Any] = field(default_factory=dict)  # @contract metadata

    def __post_init__(self) -> None:
        self.type = NodeType.CLASS
        super().__init__(type=NodeType.CLASS)


# ============================================================================
# Statement Nodes
# ============================================================================


@dataclass
class IRIf(IRNode):
    """
    If statement.

    Example:
        if user == null:
          throw ValidationError("Not found")
        else:
          return user
    """

    condition: IRExpression
    then_body: List[IRStatement] = field(default_factory=list)
    else_body: List[IRStatement] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.type = NodeType.IF
        super().__init__(type=NodeType.IF)


@dataclass
class IRFor(IRNode):
    """
    For loop.

    Examples:
        for (item in items) { process(item) }
        for (i in range(0, 10)) { print(i) }
        for (index, value in enumerate(items)) { print(index, value) }
    """

    iterator: str  # Variable name (or value variable for enumerate)
    iterable: IRExpression
    body: List[IRStatement] = field(default_factory=list)
    index_var: Optional[str] = None  # For enumerate pattern: (index, value)

    def __post_init__(self) -> None:
        self.type = NodeType.FOR
        super().__init__(type=NodeType.FOR)


@dataclass
class IRForCStyle(IRNode):
    """
    C-style for loop.

    Example:
        for (let i = 0; i < 10; i = i + 1) {
            print(i)
        }
    """

    init: IRStatement  # Initialization statement (usually IRAssignment)
    condition: IRExpression  # Loop condition
    increment: IRStatement  # Increment statement (usually IRAssignment)
    body: List[IRStatement] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.type = NodeType.FOR_C_STYLE
        super().__init__(type=NodeType.FOR_C_STYLE)


@dataclass
class IRWhile(IRNode):
    """
    While loop.

    Example:
        while count > 0:
          count = count - 1
    """

    condition: IRExpression
    body: List[IRStatement] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.type = NodeType.WHILE
        super().__init__(type=NodeType.WHILE)


@dataclass
class IRCase(IRNode):
    """
    Case clause in switch statement.

    Example:
        case 1:
          print("one")
        case 2, 3:
          print("two or three")
        default:
          print("other")
    """

    values: List[IRExpression] = field(default_factory=list)  # Empty for default case
    body: List[IRStatement] = field(default_factory=list)
    is_default: bool = False

    def __post_init__(self) -> None:
        self.type = NodeType.CASE
        super().__init__(type=NodeType.CASE)


@dataclass
class IRSwitch(IRNode):
    """
    Switch/match statement.

    Example (C#/TypeScript):
        switch (value) {
          case 1:
            return "one";
          case 2:
            return "two";
          default:
            return "other";
        }

    Example (Python match):
        match value:
          case 1:
            return "one"
          case 2:
            return "two"
          case _:
            return "other"
    """

    value: IRExpression  # Value to switch on
    cases: List[IRCase] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.type = NodeType.SWITCH
        super().__init__(type=NodeType.SWITCH)


@dataclass
class IRCatch(IRNode):
    """
    Catch block in try/catch.

    Example:
        catch ValidationError as e:
          log(e)
    """

    exception_type: Optional[str] = None  # None = catch all
    exception_var: Optional[str] = None  # Variable to bind exception
    body: List[IRStatement] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.type = NodeType.CATCH
        super().__init__(type=NodeType.CATCH)


@dataclass
class IRTry(IRNode):
    """
    Try/catch statement.

    Example:
        try:
          risky_operation()
        catch NetworkError as e:
          log(e)
        catch:
          log("Unknown error")
    """

    try_body: List[IRStatement] = field(default_factory=list)
    catch_blocks: List[IRCatch] = field(default_factory=list)
    finally_body: List[IRStatement] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.type = NodeType.TRY
        super().__init__(type=NodeType.TRY)


@dataclass
class IRAssignment(IRNode):
    """
    Variable assignment.

    Example:
        let user = database.get_user(user_id)
        count = count + 1
    """

    target: str  # Variable name
    value: IRExpression
    is_declaration: bool = True  # let x = ... vs x = ...
    var_type: Optional[IRType] = None  # Explicit type annotation

    def __post_init__(self) -> None:
        self.type = NodeType.ASSIGNMENT
        super().__init__(type=NodeType.ASSIGNMENT)


@dataclass
class IRReturn(IRNode):
    """
    Return statement.

    Example:
        return {status: "ok", data: result}
    """

    value: Optional[IRExpression] = None

    def __post_init__(self) -> None:
        self.type = NodeType.RETURN
        super().__init__(type=NodeType.RETURN)


@dataclass
class IRThrow(IRNode):
    """
    Throw/raise statement.

    Example:
        throw ValidationError("Invalid input")
    """

    exception: IRExpression  # Usually an IRCall or IRIdentifier

    def __post_init__(self) -> None:
        self.type = NodeType.THROW
        super().__init__(type=NodeType.THROW)


@dataclass
class IRBreak(IRNode):
    """Break statement in loops."""

    def __post_init__(self) -> None:
        self.type = NodeType.BREAK
        super().__init__(type=NodeType.BREAK)


@dataclass
class IRContinue(IRNode):
    """Continue statement in loops."""

    def __post_init__(self) -> None:
        self.type = NodeType.CONTINUE
        super().__init__(type=NodeType.CONTINUE)


@dataclass
class IRPass(IRNode):
    """Pass/noop statement."""

    def __post_init__(self) -> None:
        self.type = NodeType.PASS
        super().__init__(type=NodeType.PASS)


# ============================================================================
# Expression Nodes
# ============================================================================


@dataclass
class IRCall(IRNode):
    """
    Function call.

    Example:
        database.get_user(user_id)
        process(x, y, z=10)
    """

    function: IRExpression  # Usually IRIdentifier or IRPropertyAccess
    args: List[IRExpression] = field(default_factory=list)
    kwargs: Dict[str, IRExpression] = field(default_factory=dict)
    operation_id: Optional[str] = None  # CharCNN-predicted operation (e.g., "file.read")
    operation_confidence: Optional[float] = None  # Confidence score from CharCNN

    def __post_init__(self) -> None:
        self.type = NodeType.CALL
        super().__init__(type=NodeType.CALL)


@dataclass
class IRBinaryOp(IRNode):
    """
    Binary operation.

    Example:
        a + b
        x == y
        count > 0
    """

    op: BinaryOperator
    left: IRExpression
    right: IRExpression

    def __post_init__(self) -> None:
        self.type = NodeType.BINARY_OP
        super().__init__(type=NodeType.BINARY_OP)


@dataclass
class IRUnaryOp(IRNode):
    """
    Unary operation.

    Example:
        not x
        -count
    """

    op: UnaryOperator
    operand: IRExpression

    def __post_init__(self) -> None:
        self.type = NodeType.UNARY_OP
        super().__init__(type=NodeType.UNARY_OP)


@dataclass
class IRLiteral(IRNode):
    """
    Literal value.

    Example:
        "hello"
        42
        3.14
        true
        null
    """

    value: Union[str, int, float, bool, None]
    literal_type: LiteralType

    def __post_init__(self) -> None:
        self.type = NodeType.LITERAL
        super().__init__(type=NodeType.LITERAL)


@dataclass
class IRIdentifier(IRNode):
    """
    Variable/function identifier.

    Example:
        user
        database
        result
    """

    name: str

    def __post_init__(self) -> None:
        self.type = NodeType.IDENTIFIER
        super().__init__(type=NodeType.IDENTIFIER)


@dataclass
class IRPropertyAccess(IRNode):
    """
    Property access.

    Example:
        user.name
        obj.field.nested
    """

    object: IRExpression
    property: str

    def __post_init__(self) -> None:
        self.type = NodeType.PROPERTY_ACCESS
        super().__init__(type=NodeType.PROPERTY_ACCESS)


@dataclass
class IRIndex(IRNode):
    """
    Array/map indexing.

    Example:
        arr[0]
        map["key"]
    """

    object: IRExpression
    index: IRExpression

    def __post_init__(self) -> None:
        self.type = NodeType.INDEX
        super().__init__(type=NodeType.INDEX)


@dataclass
class IRLambda(IRNode):
    """
    Lambda/anonymous function.

    Example:
        lambda x: x + 1
        (x, y) => x + y
    """

    params: List[IRParameter] = field(default_factory=list)
    body: Union[IRExpression, List[IRStatement]] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.type = NodeType.LAMBDA
        super().__init__(type=NodeType.LAMBDA)


@dataclass
class IRArray(IRNode):
    """
    Array literal.

    Example:
        [1, 2, 3]
        ["a", "b", "c"]
    """

    elements: List[IRExpression] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.type = NodeType.ARRAY
        super().__init__(type=NodeType.ARRAY)


@dataclass
class IRMap(IRNode):
    """
    Map/object literal.

    Example:
        {name: "John", age: 30}
        {"key": "value", "count": 42}
    """

    entries: Dict[str, IRExpression] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.type = NodeType.MAP
        super().__init__(type=NodeType.MAP)


@dataclass
class IRTernary(IRNode):
    """
    Ternary conditional expression.

    Example:
        x if condition else y
        condition ? x : y
    """

    condition: IRExpression
    true_value: IRExpression
    false_value: IRExpression

    def __post_init__(self) -> None:
        self.type = NodeType.TERNARY
        super().__init__(type=NodeType.TERNARY)


@dataclass
class IRComprehension(IRNode):
    """
    List/Dict/Set comprehension.

    Example:
        [x * 2 for x in items]
        {k: v for k, v in pairs}
        {item.id for item in items}
    """

    target: IRExpression  # The expression to build
    iterator: str  # Variable name
    iterable: IRExpression
    condition: Optional[IRExpression] = None  # if clause
    comprehension_type: str = "list"  # list, dict, set, generator

    def __post_init__(self) -> None:
        self.type = NodeType.COMPREHENSION
        super().__init__(type=NodeType.COMPREHENSION)


@dataclass
class IRFString(IRNode):
    """
    F-string / template literal.

    Example:
        f"Hello {name}, you are {age} years old"
        `Hello ${name}, you are ${age} years old`
    """

    parts: List[Union[str, IRExpression]] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.type = NodeType.FSTRING
        super().__init__(type=NodeType.FSTRING)


@dataclass
class IRWith(IRNode):
    """
    Context manager / using statement.

    Example (Python):
        with open("file.txt") as f:
            data = f.read()

    Example (C#):
        using (var file = File.Open("file.txt"))
        {
            var data = file.ReadAll();
        }
    """

    context_expr: IRExpression  # The resource to manage
    variable: Optional[str] = None  # Variable to bind (as clause)
    body: List[IRStatement] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.type = NodeType.WITH
        super().__init__(type=NodeType.WITH)


@dataclass
class IRDecorator(IRNode):
    """
    Decorator / attribute.

    Example (Python):
        @staticmethod
        @property
        @cache

    Example (C#):
        [Obsolete]
        [Serializable]
    """

    name: str
    args: List[IRExpression] = field(default_factory=list)
    kwargs: Dict[str, IRExpression] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.type = NodeType.DECORATOR
        super().__init__(type=NodeType.DECORATOR)


@dataclass
class IRSlice(IRNode):
    """
    Slice notation.

    Example:
        items[1:5]
        items[:3]
        items[-2:]
        items[::2]
    """

    object: IRExpression
    start: Optional[IRExpression] = None
    stop: Optional[IRExpression] = None
    step: Optional[IRExpression] = None

    def __post_init__(self) -> None:
        self.type = NodeType.SLICE
        super().__init__(type=NodeType.SLICE)


@dataclass
class IRDestructure(IRNode):
    """
    Destructuring assignment.

    Example (JS):
        const {name, email} = user;
        const [first, second] = items;

    Example (Python):
        name, email = user.name, user.email
    """

    pattern: Union[List[str], Dict[str, str]]  # Variables to extract
    value: IRExpression
    destructure_type: str = "object"  # object or array

    def __post_init__(self) -> None:
        self.type = NodeType.DESTRUCTURE
        super().__init__(type=NodeType.DESTRUCTURE)


@dataclass
class IRSpread(IRNode):
    """
    Spread operator.

    Example:
        [...arr1, ...arr2]
        {...obj1, ...obj2}
    """

    value: IRExpression
    spread_type: str = "array"  # array or object

    def __post_init__(self) -> None:
        self.type = NodeType.SPREAD
        super().__init__(type=NodeType.SPREAD)


@dataclass
class IRDefer(IRNode):
    """
    Defer statement (Go).

    Example:
        defer file.Close()
    """

    call: IRExpression  # Usually IRCall

    def __post_init__(self) -> None:
        self.type = NodeType.DEFER
        super().__init__(type=NodeType.DEFER)


@dataclass
class IRChannel(IRNode):
    """
    Channel operation (Go).

    Example:
        ch <- value  // send
        value := <-ch  // receive
    """

    channel: IRExpression
    value: Optional[IRExpression] = None  # None for receive
    operation: str = "send"  # send or receive

    def __post_init__(self) -> None:
        self.type = NodeType.CHANNEL
        super().__init__(type=NodeType.CHANNEL)


@dataclass
class IRSelect(IRNode):
    """
    Select statement (Go).

    Example:
        select {
        case v := <-ch1:
            process(v)
        case ch2 <- value:
            log("sent")
        default:
            log("nothing")
        }
    """

    cases: List[Dict[str, Any]] = field(default_factory=list)
    # Each case: {"channel_op": IRChannel, "body": List[IRStatement]}
    default_body: List[IRStatement] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.type = NodeType.SELECT
        super().__init__(type=NodeType.SELECT)


@dataclass
class IRGoroutine(IRNode):
    """
    Goroutine (Go async execution).

    Example:
        go processData(item)
    """

    call: IRExpression  # Usually IRCall or IRLambda

    def __post_init__(self) -> None:
        self.type = NodeType.GOROUTINE
        super().__init__(type=NodeType.GOROUTINE)


@dataclass
class IRAwait(IRNode):
    """
    Await expression.

    Example:
        await fetchData()
        await promise
    """

    expression: IRExpression

    def __post_init__(self) -> None:
        self.type = NodeType.AWAIT
        super().__init__(type=NodeType.AWAIT)


@dataclass
class IRPatternMatch(IRNode):
    """
    Pattern matching expression using 'is' operator.

    Example:
        opt is Some(val)  // Matches Some variant and binds val
        opt is None       // Matches None variant
        res is Ok(_)      // Matches Ok variant, ignores value
        res is Err(e)     // Matches Err variant and binds e
    """

    value: IRExpression  # The value being matched (left side)
    pattern: IRExpression  # The pattern (right side) - usually IRCall or IRIdentifier
    # pattern can be:
    # - IRIdentifier("None") for simple enum variants
    # - IRCall(IRIdentifier("Some"), [IRIdentifier("val")]) for variants with capture
    # - IRPropertyAccess(IRIdentifier("Option"), "Some") for qualified variants

    def __post_init__(self) -> None:
        self.type = NodeType.PATTERN_MATCH
        super().__init__(type=NodeType.PATTERN_MATCH)


@dataclass
class IROldExpr(IRNode):
    """
    Old expression for referencing pre-state in postconditions.

    Example:
        @ensures increased: balance == old balance + amount
        @ensures preserved: result.name == old name
    """

    expression: IRExpression  # The expression to evaluate in pre-state

    def __post_init__(self) -> None:
        self.type = NodeType.OLD_EXPR
        super().__init__(type=NodeType.OLD_EXPR)


# ============================================================================
# Contract Annotation Nodes
# ============================================================================


@dataclass
class IRContractClause(IRNode):
    """
    Contract clause (precondition, postcondition, or invariant).

    Example:
        @requires name_not_empty: str.length(name) >= 1
        @ensures result_positive: result > 0
        @invariant count_non_negative: this.count >= 0
    """

    clause_type: str  # "requires", "ensures", or "invariant"
    name: str  # Clause name (e.g., "name_not_empty")
    expression: IRExpression  # Boolean expression

    def __post_init__(self) -> None:
        self.type = NodeType.CONTRACT_CLAUSE
        super().__init__(type=NodeType.CONTRACT_CLAUSE)


@dataclass
class IRContractAnnotation(IRNode):
    """
    Contract metadata annotation (@contract, @operation, @effects).

    Example:
        @contract(version="1.0.0", description="User service")
        @operation(idempotent=true, timeout=5000)
        @effects [database.write, event.emit("user.created")]
    """

    annotation_type: str  # "contract", "operation", or "effects"
    metadata: Dict[str, Any] = field(default_factory=dict)  # Key-value metadata
    effects: List[str] = field(default_factory=list)  # For @effects

    def __post_init__(self) -> None:
        self.type = NodeType.CONTRACT_ANNOTATION
        super().__init__(type=NodeType.CONTRACT_ANNOTATION)


# ============================================================================
# Type Aliases
# ============================================================================

# Union type for all expression nodes
IRExpression = Union[
    IRCall,
    IRBinaryOp,
    IRUnaryOp,
    IRLiteral,
    IRIdentifier,
    IRPropertyAccess,
    IRIndex,
    IRLambda,
    IRArray,
    IRMap,
    IRTernary,
    IRComprehension,
    IRFString,
    IRSlice,
    IRSpread,
    IRAwait,
    IRPatternMatch,
    IROldExpr,
]

# Union type for all statement nodes
IRStatement = Union[
    IRIf,
    IRFor,
    IRWhile,
    IRSwitch,
    IRTry,
    IRAssignment,
    IRReturn,
    IRThrow,
    IRBreak,
    IRContinue,
    IRPass,
    IRWith,
    IRDefer,
    IRDestructure,
    IRSelect,
    IRGoroutine,
    IRChannel,
    IRCall,  # Expression statements
]
