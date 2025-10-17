"""
PW DSL 2.0 Parser

Converts PW DSL 2.0 text into IR (Intermediate Representation).

Architecture:
1. Lexer: Tokenize input text
2. Parser: Build IR tree from tokens
3. Semantic Analyzer: Validate and enrich IR

The parser is hand-written (recursive descent) for maximum control
and clear error messages.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

from dsl.ir import (
    BinaryOperator,
    IRArray,
    IRAssignment,
    IRBinaryOp,
    IRBreak,
    IRCall,
    IRCatch,
    IRClass,
    IRContractAnnotation,
    IRContractClause,
    IRContinue,
    IREnum,
    IREnumVariant,
    IRExpression,
    IRFor,
    IRForCStyle,
    IRFunction,
    IRIdentifier,
    IRIf,
    IRImport,
    IRIndex,
    IRLambda,
    IRLiteral,
    IRMap,
    IRModule,
    IROldExpr,
    IRParameter,
    IRPass,
    IRPatternMatch,
    IRProperty,
    IRPropertyAccess,
    IRReturn,
    IRSlice,
    IRStatement,
    IRTernary,
    IRThrow,
    IRTry,
    IRType,
    IRTypeDefinition,
    IRUnaryOp,
    IRWhile,
    LiteralType,
    SourceLocation,
    UnaryOperator,
)

# Optional CharCNN integration for operation lookup
try:
    from ml.inference import lookup_operation
    CHARCNN_AVAILABLE = True
except ImportError:
    CHARCNN_AVAILABLE = False
    lookup_operation = None


# ============================================================================
# Error Handling
# ============================================================================


class PWParseError(Exception):
    """Parse error with location information."""

    def __init__(self, message: str, line: int = 0, column: int = 0):
        self.message = message
        self.line = line
        self.column = column
        super().__init__(f"[Line {line}:{column}] {message}")


# ============================================================================
# Lexer (Tokenization)
# ============================================================================


class TokenType(Enum):
    """Token types for lexical analysis."""

    # Literals
    INTEGER = "INTEGER"
    FLOAT = "FLOAT"
    STRING = "STRING"
    BOOLEAN = "BOOLEAN"
    NULL = "NULL"

    # Identifiers and keywords
    IDENTIFIER = "IDENTIFIER"
    KEYWORD = "KEYWORD"

    # Operators
    PLUS = "+"
    MINUS = "-"
    STAR = "*"
    SLASH = "/"
    PERCENT = "%"
    POWER = "**"
    FLOOR_DIV = "//"

    EQ = "=="
    NE = "!="
    LT = "<"
    LE = "<="
    GT = ">"
    GE = ">="

    AND = "and"
    OR = "or"
    NOT = "not"
    IS = "is"  # Pattern matching operator

    # C-style logical operators
    LOGICAL_AND = "&&"
    LOGICAL_OR = "||"
    LOGICAL_NOT = "!"  # C-style NOT operator

    BIT_AND = "&"
    BIT_OR = "|"
    BIT_XOR = "^"
    BIT_NOT = "~"
    LSHIFT = "<<"
    RSHIFT = ">>"

    ASSIGN = "="
    PLUS_ASSIGN = "+="
    MINUS_ASSIGN = "-="
    STAR_ASSIGN = "*="
    SLASH_ASSIGN = "/="

    # Delimiters
    LPAREN = "("
    RPAREN = ")"
    LBRACKET = "["
    RBRACKET = "]"
    LBRACE = "{"
    RBRACE = "}"
    COLON = ":"
    COMMA = ","
    DOT = "."
    QUESTION = "?"
    PIPE = "|"
    ARROW = "->"
    SEMICOLON = ";"
    AT = "@"  # For contract annotations

    # Special
    NEWLINE = "NEWLINE"
    INDENT = "INDENT"
    DEDENT = "DEDENT"
    EOF = "EOF"
    DOC_COMMENT = "DOC_COMMENT"  # /// style documentation comments


# PW DSL 2.0 keywords
KEYWORDS = {
    "module", "version", "import", "from", "as",
    "type", "enum", "function", "class", "constructor",
    "params", "returns", "throws", "body", "properties", "method",
    "let", "if", "else", "elif", "for", "in", "while",
    "try", "catch", "finally", "throw", "return",
    "break", "continue", "pass",
    "null", "true", "false",
    "and", "or", "not", "is",
    "async", "await", "lambda", "self",
    # Contract-related keywords
    "old", "service",  # 'old' for postconditions, 'service' as alias for 'class'
}


@dataclass
class Token:
    """A lexical token."""

    type: TokenType
    value: Any
    line: int
    column: int

    def __repr__(self) -> str:
        return f"Token({self.type.value}, {self.value!r}, {self.line}:{self.column})"


class Lexer:
    """Tokenize PW DSL 2.0 source code."""

    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.line = 1
        self.column = 1
        self.tokens: List[Token] = []
        self.indent_stack = [0]
        self.paren_depth = 0  # Track ( ) [ ] { } nesting for multi-line support

    def error(self, msg: str) -> PWParseError:
        return PWParseError(msg, self.line, self.column)

    def peek(self, offset: int = 0) -> str:
        """Peek ahead at character."""
        pos = self.pos + offset
        return self.text[pos] if pos < len(self.text) else ""

    def advance(self) -> str:
        """Consume and return current character."""
        if self.pos >= len(self.text):
            return ""
        char = self.text[self.pos]
        self.pos += 1
        if char == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return char

    def skip_whitespace(self) -> None:
        """Skip spaces, tabs, and carriage returns (but not newlines)."""
        while self.peek() and self.peek() in " \t\r":
            self.advance()

    def skip_comment(self) -> None:
        """
        Skip comments.
        Supports:
        - Python-style: # comment
        - C-style single-line: // comment
        - C-style multi-line: /* comment */

        NOTE: /// doc comments are handled separately in read_doc_comment()
        """
        # Python-style comment
        if self.peek() == "#":
            while self.peek() and self.peek() != "\n":
                self.advance()
        # C-style single-line comment (but NOT ///)
        elif self.peek() == "/" and self.peek(1) == "/" and self.peek(2) != "/":
            self.advance()  # /
            self.advance()  # /
            while self.peek() and self.peek() != "\n":
                self.advance()
        # C-style multi-line comment
        elif self.peek() == "/" and self.peek(1) == "*":
            self.advance()  # /
            self.advance()  # *
            while self.peek():
                if self.peek() == "*" and self.peek(1) == "/":
                    self.advance()  # *
                    self.advance()  # /
                    break
                self.advance()

    def read_doc_comment(self) -> str:
        """
        Read /// style documentation comment.
        Returns the comment content without the ///.
        """
        line, col = self.line, self.column
        comment_lines = []

        # Read consecutive /// lines
        while self.peek() == "/" and self.peek(1) == "/" and self.peek(2) == "/":
            self.advance()  # /
            self.advance()  # /
            self.advance()  # /

            # Skip optional space after ///
            if self.peek() == " ":
                self.advance()

            # Read line content
            line_content = ""
            while self.peek() and self.peek() != "\n":
                line_content += self.advance()

            comment_lines.append(line_content)

            # Consume newline
            if self.peek() == "\n":
                self.advance()

            # Skip whitespace/indentation on next line
            while self.peek() == " ":
                self.advance()

        return "\n".join(comment_lines)

    def read_string(self) -> str:
        """Read string literal."""
        quote = self.advance()  # Opening quote
        value = ""

        # Check for triple-quoted string
        if self.peek() == quote and self.peek(1) == quote:
            self.advance()  # Second quote
            self.advance()  # Third quote
            # Read until triple quote
            while True:
                if not self.peek():
                    raise self.error("Unterminated string")
                if self.peek() == quote and self.peek(1) == quote and self.peek(2) == quote:
                    self.advance()
                    self.advance()
                    self.advance()
                    break
                value += self.advance()
        else:
            # Single or double quoted
            while self.peek() and self.peek() != quote:
                if self.peek() == "\\":
                    self.advance()
                    escape = self.advance()
                    escapes = {"n": "\n", "t": "\t", "r": "\r", "\\": "\\", quote: quote}
                    value += escapes.get(escape, escape)
                else:
                    value += self.advance()
            if not self.peek():
                raise self.error("Unterminated string")
            self.advance()  # Closing quote

        return value

    def read_number(self) -> Token:
        """Read numeric literal."""
        line, col = self.line, self.column
        num_str = ""

        # Handle hex, binary, octal
        # Check peek(1) is not empty before checking 'in' operator (empty string matches any string)
        if self.peek() == "0" and self.peek(1) and self.peek(1) in "xXbBoO":
            num_str += self.advance()  # 0
            num_str += self.advance()  # x/b/o
            if num_str[1] in "xX":
                while self.peek() in "0123456789abcdefABCDEF_":
                    if self.peek() != "_":
                        num_str += self.advance()
                    else:
                        self.advance()
                return Token(TokenType.INTEGER, int(num_str, 16), line, col)
            elif num_str[1] in "bB":
                while self.peek() in "01_":
                    if self.peek() != "_":
                        num_str += self.advance()
                    else:
                        self.advance()
                return Token(TokenType.INTEGER, int(num_str, 2), line, col)
            elif num_str[1] in "oO":
                while self.peek() in "01234567_":
                    if self.peek() != "_":
                        num_str += self.advance()
                    else:
                        self.advance()
                return Token(TokenType.INTEGER, int(num_str, 8), line, col)

        # Regular decimal number
        while self.peek().isdigit() or self.peek() == "_":
            if self.peek() != "_":
                num_str += self.advance()
            else:
                self.advance()

        # Check for float
        if self.peek() == "." and self.peek(1).isdigit():
            num_str += self.advance()  # .
            while self.peek().isdigit() or self.peek() == "_":
                if self.peek() != "_":
                    num_str += self.advance()
                else:
                    self.advance()

        # Check for scientific notation
        if self.peek() in "eE":
            num_str += self.advance()
            if self.peek() in "+-":
                num_str += self.advance()
            while self.peek().isdigit():
                num_str += self.advance()

        # Determine type
        if "." in num_str or "e" in num_str or "E" in num_str:
            return Token(TokenType.FLOAT, float(num_str), line, col)
        else:
            return Token(TokenType.INTEGER, int(num_str), line, col)

    def read_identifier(self) -> Token:
        """Read identifier or keyword."""
        line, col = self.line, self.column
        ident = ""

        while self.peek() and (self.peek().isalnum() or self.peek() == "_"):
            ident += self.advance()

        # Check if keyword
        if ident in KEYWORDS:
            if ident in ("true", "false"):
                return Token(TokenType.BOOLEAN, ident == "true", line, col)
            elif ident == "null":
                return Token(TokenType.NULL, None, line, col)
            elif ident in ("and", "or", "not", "is"):
                # Logical operators as keywords
                if ident == "and":
                    return Token(TokenType.AND, ident, line, col)
                elif ident == "or":
                    return Token(TokenType.OR, ident, line, col)
                elif ident == "not":
                    return Token(TokenType.NOT, ident, line, col)
                elif ident == "is":
                    return Token(TokenType.IS, ident, line, col)
            else:
                return Token(TokenType.KEYWORD, ident, line, col)
        else:
            return Token(TokenType.IDENTIFIER, ident, line, col)

    def tokenize(self) -> List[Token]:
        """Tokenize the entire input."""
        # Handle indentation at start of each line
        line_start = True

        while self.pos < len(self.text):
            # Handle line start (indentation)
            if line_start:
                indent = 0
                while self.peek() == " ":
                    self.advance()
                    indent += 1

                # Check indentation change BEFORE skipping blank lines
                # This ensures DEDENT tokens are emitted even for blank lines
                if indent < self.indent_stack[-1]:
                    while self.indent_stack and indent < self.indent_stack[-1]:
                        self.indent_stack.pop()
                        self.tokens.append(Token(TokenType.DEDENT, None, self.line, self.column))
                    if indent != self.indent_stack[-1]:
                        raise self.error(f"Inconsistent indentation")

                # Skip blank lines and comments (AFTER checking indentation)
                if self.peek() in "\n#" or (self.peek() == "/" and self.peek(1) in "/*"):
                    if self.peek() == "#" or (self.peek() == "/" and self.peek(1) in "/*"):
                        self.skip_comment()
                    if self.peek() == "\n":
                        self.advance()
                    continue

                # Check for INDENT (only for non-blank lines)
                if indent > self.indent_stack[-1]:
                    self.indent_stack.append(indent)
                    self.tokens.append(Token(TokenType.INDENT, None, self.line, self.column))

                line_start = False

            # Skip inline whitespace
            self.skip_whitespace()

            # Documentation comments: ///
            three_char = self.peek() + self.peek(1) + self.peek(2)
            if three_char == "///":
                # Read doc comment
                doc_content = self.read_doc_comment()
                self.tokens.append(Token(TokenType.DOC_COMMENT, doc_content, self.line, self.column))
                continue

            # Two-character operators - but check for comment context first
            # Special handling for // : it's a comment if not in an expression context
            # Expression context: after identifier, number, closing paren/bracket/brace
            two_char = self.peek() + self.peek(1)

            # For //, check if we're in expression context
            if two_char == "//":
                # Check if previous token suggests we're in an expression
                in_expression = False
                if self.tokens:
                    last_token = self.tokens[-1]
                    # After these tokens, // is an operator (not comment)
                    expression_tokens = {
                        TokenType.IDENTIFIER, TokenType.INTEGER, TokenType.FLOAT,
                        TokenType.RPAREN, TokenType.RBRACKET, TokenType.STRING,
                    }
                    # Only treat as floor division if:
                    # 1. Previous token is an expression token
                    # 2. Previous token is on the SAME line (not a new line)
                    if (last_token.type in expression_tokens and
                        last_token.line == self.line):
                        in_expression = True

                if in_expression:
                    # Tokenize as FLOOR_DIV operator
                    line, col = self.line, self.column
                    self.advance()
                    self.advance()
                    self.tokens.append(Token(TokenType.FLOOR_DIV, "//", line, col))
                    continue
                else:
                    # Treat as comment
                    self.skip_comment()
                    continue

            # Other two-character operators
            if two_char in ("**", "==", "!=", "<=", ">=", "<<", ">>", "+=", "-=", "*=", "/=", "->", "&&", "||"):
                line, col = self.line, self.column
                self.advance()
                self.advance()
                type_map = {
                    "**": TokenType.POWER,
                    "==": TokenType.EQ, "!=": TokenType.NE,
                    "<=": TokenType.LE, ">=": TokenType.GE,
                    "<<": TokenType.LSHIFT, ">>": TokenType.RSHIFT,
                    "+=": TokenType.PLUS_ASSIGN, "-=": TokenType.MINUS_ASSIGN,
                    "*=": TokenType.STAR_ASSIGN, "/=": TokenType.SLASH_ASSIGN,
                    "->": TokenType.ARROW,
                    "&&": TokenType.LOGICAL_AND, "||": TokenType.LOGICAL_OR,
                }
                self.tokens.append(Token(type_map[two_char], two_char, line, col))
                continue

            # Skip comments (#, /*, but // is handled above)
            if self.peek() == "#" or (self.peek() == "/" and self.peek(1) == "*"):
                self.skip_comment()
                continue

            # Newline
            if self.peek() == "\n":
                if self.paren_depth > 0:
                    # Inside parentheses - skip newline (allows multi-line syntax)
                    self.advance()
                    continue

                # Check if previous token was a binary operator (line continuation)
                if self.tokens:
                    last_token = self.tokens[-1]
                    continuation_ops = {
                        TokenType.PLUS, TokenType.MINUS, TokenType.STAR, TokenType.SLASH,
                        TokenType.PERCENT, TokenType.POWER, TokenType.FLOOR_DIV,
                        TokenType.EQ, TokenType.NE,  # Comparison: == !=
                        # NOTE: LT/GT/LE/GE removed - they're used in generics (array<T>) and shouldn't continue lines
                        TokenType.AND, TokenType.OR, TokenType.LOGICAL_AND, TokenType.LOGICAL_OR,
                        TokenType.BIT_AND, TokenType.BIT_OR, TokenType.BIT_XOR,
                        TokenType.LSHIFT, TokenType.RSHIFT,
                        TokenType.COMMA,  # Allow multi-line argument lists
                    }
                    if last_token.type in continuation_ops:
                        # Line continues - skip newline
                        self.advance()
                        continue

                # Outside parentheses - emit NEWLINE token
                self.tokens.append(Token(TokenType.NEWLINE, "\n", self.line, self.column))
                self.advance()
                line_start = True
                continue

            # End of file
            if not self.peek():
                break

            line, col = self.line, self.column

            # String literals
            if self.peek() in "\"'":
                value = self.read_string()
                self.tokens.append(Token(TokenType.STRING, value, line, col))
                continue

            # Numbers
            if self.peek().isdigit():
                self.tokens.append(self.read_number())
                continue

            # Identifiers and keywords
            if self.peek().isalpha() or self.peek() == "_":
                self.tokens.append(self.read_identifier())
                continue

            # Single-character operators/delimiters
            char = self.peek()
            char_map = {
                "+": TokenType.PLUS, "-": TokenType.MINUS,
                "*": TokenType.STAR, "/": TokenType.SLASH,
                "%": TokenType.PERCENT,
                "=": TokenType.ASSIGN,
                "!": TokenType.LOGICAL_NOT,  # C-style NOT operator
                "<": TokenType.LT, ">": TokenType.GT,
                "&": TokenType.BIT_AND, "|": TokenType.BIT_OR,
                "^": TokenType.BIT_XOR, "~": TokenType.BIT_NOT,
                "(": TokenType.LPAREN, ")": TokenType.RPAREN,
                "[": TokenType.LBRACKET, "]": TokenType.RBRACKET,
                "{": TokenType.LBRACE, "}": TokenType.RBRACE,
                ":": TokenType.COLON, ",": TokenType.COMMA,
                ".": TokenType.DOT, "?": TokenType.QUESTION,
                ";": TokenType.SEMICOLON,
                "@": TokenType.AT,  # For contract annotations
            }
            if char in char_map:
                # Track parenthesis, bracket, and brace depth for multi-line support
                if char in "([{":
                    self.paren_depth += 1
                elif char in ")]}":
                    self.paren_depth -= 1
                self.advance()
                self.tokens.append(Token(char_map[char], char, line, col))
                continue

            raise self.error(f"Unexpected character: {char!r}")

        # Emit trailing dedents
        while len(self.indent_stack) > 1:
            self.indent_stack.pop()
            self.tokens.append(Token(TokenType.DEDENT, None, self.line, self.column))

        # Emit EOF
        self.tokens.append(Token(TokenType.EOF, None, self.line, self.column))

        return self.tokens


# ============================================================================
# Parser (Syntax Analysis)
# ============================================================================


class Parser:
    """Parse PW DSL 2.0 tokens into IR."""

    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def error(self, msg: str) -> PWParseError:
        tok = self.current()
        return PWParseError(msg, tok.line, tok.column)

    def current(self) -> Token:
        """Get current token."""
        return self.tokens[self.pos] if self.pos < len(self.tokens) else self.tokens[-1]

    def peek(self, offset: int = 1) -> Token:
        """Peek ahead at token."""
        pos = self.pos + offset
        return self.tokens[pos] if pos < len(self.tokens) else self.tokens[-1]

    def advance(self) -> Token:
        """Consume and return current token."""
        tok = self.current()
        if tok.type != TokenType.EOF:
            self.pos += 1
        return tok

    def expect(self, token_type: TokenType) -> Token:
        """Expect specific token type and consume it."""
        tok = self.current()
        if tok.type != token_type:
            raise self.error(f"Expected {token_type.value}, got {tok.type.value}")
        return self.advance()

    def match(self, *token_types: TokenType) -> bool:
        """Check if current token matches any of the given types."""
        return self.current().type in token_types

    def skip_newlines(self) -> None:
        """Skip newline tokens. Does NOT skip DEDENT (it marks end of blocks)."""
        while self.match(TokenType.NEWLINE):
            self.advance()

    def _is_fn_lambda(self) -> bool:
        """
        Look ahead to check if 'fn(...)' is a lambda or function call.
        Returns True if there's a -> after the closing paren (lambda), False otherwise (call).

        Assumes current token is 'fn' identifier.
        """
        # Start from current position + 2 (skip 'fn' and '(')
        pos = self.pos + 2
        paren_depth = 1

        # Scan to find matching ')'
        while pos < len(self.tokens) and paren_depth > 0:
            tok = self.tokens[pos]
            if tok.type == TokenType.LPAREN:
                paren_depth += 1
            elif tok.type == TokenType.RPAREN:
                paren_depth -= 1
            pos += 1

        # Check if next token after ')' is '->'
        if pos < len(self.tokens):
            return self.tokens[pos].type == TokenType.ARROW
        return False

    def _reconstruct_operation_code(self, expr: IRExpression) -> str:
        """
        Reconstruct PW code string from IRExpression for CharCNN lookup.

        This converts an IR node back to approximate PW syntax for operation identification.

        Example:
            IRPropertyAccess(IRIdentifier("file"), "read") → "file.read"
            IRIdentifier("print") → "print"
        """
        if isinstance(expr, IRIdentifier):
            return expr.name
        elif isinstance(expr, IRPropertyAccess):
            obj_code = self._reconstruct_operation_code(expr.object)
            return f"{obj_code}.{expr.property}"
        else:
            # For other expressions, return empty (won't match operations)
            return ""

    def consume_statement_terminator(self) -> None:
        """
        Consume optional statement terminator.
        Accepts semicolon, newline, or nothing if followed by closing brace.
        This enables both Python-style (newlines) and C-style (semicolons) syntax.
        """
        if self.match(TokenType.SEMICOLON, TokenType.NEWLINE):
            self.advance()
        # If next token is RBRACE, statement can end without terminator

    # ========================================================================
    # Top-level parsing
    # ========================================================================

    def parse(self) -> IRModule:
        """Parse entire module."""
        self.skip_newlines()

        name = "main"
        version = "1.0.0"
        imports: List[IRImport] = []
        types: List[IRTypeDefinition] = []
        enums: List[IREnum] = []
        functions: List[IRFunction] = []
        classes: List[IRClass] = []

        # Parse module declaration (optional)
        if self.match(TokenType.KEYWORD) and self.current().value == "module":
            self.advance()
            name = self.expect(TokenType.IDENTIFIER).value
            self.expect(TokenType.NEWLINE)
            self.skip_newlines()

        # Parse version (optional)
        if self.match(TokenType.KEYWORD) and self.current().value == "version":
            self.advance()
            if self.match(TokenType.STRING):
                version = self.advance().value
            elif self.match(TokenType.FLOAT):
                # Handle float as version (e.g., 1.0)
                version = str(self.advance().value)
                # Check if there's more (e.g., 1.0.0 parsed as 1.0 + . + 0)
                if self.match(TokenType.DOT):
                    self.advance()
                    version += "." + str(self.expect(TokenType.INTEGER).value)
            elif self.match(TokenType.INTEGER):
                # Integer version like 1 or parse 1.0.0
                version_parts = [str(self.advance().value)]
                while self.match(TokenType.DOT):
                    self.advance()
                    version_parts.append(str(self.expect(TokenType.INTEGER).value))
                version = ".".join(version_parts)
            else:
                raise self.error("Expected version number or string")
            self.expect(TokenType.NEWLINE)
            self.skip_newlines()

        # Parse declarations
        while not self.match(TokenType.EOF):
            self.skip_newlines()  # Skip blank lines between declarations
            if self.match(TokenType.EOF):
                break
            if self.match(TokenType.KEYWORD):
                keyword = self.current().value
                if keyword == "import":
                    imports.append(self.parse_import())
                elif keyword == "type":
                    types.append(self.parse_type_definition())
                elif keyword == "enum":
                    enums.append(self.parse_enum())
                elif keyword == "function" or keyword == "async":
                    functions.append(self.parse_function())
                elif keyword == "class":
                    classes.append(self.parse_class())
                else:
                    raise self.error(f"Unexpected keyword: {keyword}")
            else:
                raise self.error(f"Expected declaration, got {self.current().type.value}")

        return IRModule(
            name=name,
            version=version,
            imports=imports,
            types=types,
            enums=enums,
            functions=functions,
            classes=classes,
        )

    def parse_import(self) -> IRImport:
        """Parse import statement with support for dotted paths (e.g., import x.y.z)."""
        self.expect(TokenType.KEYWORD)  # "import"

        # Parse module path: identifier (DOT identifier)*
        # Support dotted paths like: stdlib.core, x.y.z
        module_parts = [self.expect(TokenType.IDENTIFIER).value]
        while self.match(TokenType.DOT):
            self.advance()  # consume DOT
            module_parts.append(self.expect(TokenType.IDENTIFIER).value)
        module = ".".join(module_parts)

        alias = None
        items = []

        if self.match(TokenType.KEYWORD):
            if self.current().value == "from":
                # import X from Y
                self.advance()
                package = self.expect(TokenType.IDENTIFIER).value
                module, alias = package, module
            elif self.current().value == "as":
                # import X as Y
                self.advance()
                alias = self.expect(TokenType.IDENTIFIER).value

        # Import statement can end with NEWLINE or EOF
        if not self.match(TokenType.EOF):
            self.expect(TokenType.NEWLINE)
            self.skip_newlines()

        return IRImport(module=module, alias=alias, items=items)

    def parse_type_definition(self) -> IRTypeDefinition:
        """Parse type definition."""
        self.expect(TokenType.KEYWORD)  # "type"
        name = self.expect(TokenType.IDENTIFIER).value
        self.expect(TokenType.COLON)
        self.expect(TokenType.NEWLINE)
        self.expect(TokenType.INDENT)

        fields = []
        while not self.match(TokenType.DEDENT):
            self.skip_newlines()
            if self.match(TokenType.DEDENT):
                break

            field_name = self.expect(TokenType.IDENTIFIER).value
            field_type = self.parse_type()
            default_value = None

            if self.match(TokenType.ASSIGN):
                self.advance()
                default_value = self.parse_expression()

            fields.append(IRProperty(
                name=field_name,
                prop_type=field_type,
                default_value=default_value,
            ))
            self.expect(TokenType.NEWLINE)

        self.expect(TokenType.DEDENT)
        return IRTypeDefinition(name=name, fields=fields)

    def parse_enum(self) -> IREnum:
        """Parse enum definition with optional generic parameters."""
        self.expect(TokenType.KEYWORD)  # "enum"
        name = self.expect(TokenType.IDENTIFIER).value

        # Parse generic parameters: <T> or <T, E>
        generic_params = []
        if self.match(TokenType.LT):
            self.advance()  # consume '<'
            generic_params.append(self.expect(TokenType.IDENTIFIER).value)
            while self.match(TokenType.COMMA):
                self.advance()  # consume ','
                generic_params.append(self.expect(TokenType.IDENTIFIER).value)
            self.expect(TokenType.GT)  # consume '>'

        self.expect(TokenType.COLON)
        self.expect(TokenType.NEWLINE)
        self.expect(TokenType.INDENT)

        variants = []
        while not self.match(TokenType.DEDENT):
            self.skip_newlines()
            if self.match(TokenType.DEDENT):
                break

            self.expect(TokenType.MINUS)  # "-"
            variant_name = self.expect(TokenType.IDENTIFIER).value

            # Check for associated types (UNNAMED tuple syntax: Some(T), not Some(value: T))
            associated_types = []
            if self.match(TokenType.LPAREN):
                self.advance()
                while not self.match(TokenType.RPAREN):
                    # Check if this looks like named syntax (identifier followed by colon)
                    # If so, skip the name and just parse the type
                    if self.match(TokenType.IDENTIFIER) and self.peek().type == TokenType.COLON:
                        # Named syntax: Some(value: T) - skip name, parse type
                        self.advance()  # consume identifier
                        self.expect(TokenType.COLON)  # consume colon
                    # Parse the type
                    associated_types.append(self.parse_type())
                    if self.match(TokenType.COMMA):
                        self.advance()
                self.expect(TokenType.RPAREN)

            variants.append(IREnumVariant(
                name=variant_name,
                associated_types=associated_types,
            ))
            self.expect(TokenType.NEWLINE)

        self.expect(TokenType.DEDENT)
        return IREnum(name=name, generic_params=generic_params, variants=variants)

    # ========================================================================
    # Contract Annotation Parsing
    # ========================================================================

    def parse_contract_annotations(self) -> Tuple[Optional[str], List[IRContractClause], Dict[str, Any]]:
        """
        Parse contract annotations before a function or class.

        Returns:
            - doc_comment: Documentation string (from /// comments)
            - operation_annotations: List of @operation, @contract metadata
            - metadata: Combined metadata dict

        Handles:
            /// doc comments
            @contract(version="1.0.0")
            @operation(idempotent=true)
        """
        doc_comment = None
        metadata = {}

        # Parse doc comments (///)
        while self.match(TokenType.DOC_COMMENT):
            comment = self.advance().value
            if doc_comment is None:
                doc_comment = comment
            else:
                doc_comment += "\n" + comment
            self.skip_newlines()

        # Parse @ annotations (@contract, @operation)
        while self.match(TokenType.AT):
            self.advance()  # consume '@'
            annotation_name = self.expect(TokenType.IDENTIFIER).value

            if annotation_name in ("contract", "operation"):
                # Parse metadata: @contract(key=value, key2=value2)
                if self.match(TokenType.LPAREN):
                    self.advance()  # consume '('
                    while not self.match(TokenType.RPAREN):
                        key = self.expect(TokenType.IDENTIFIER).value
                        self.expect(TokenType.ASSIGN)  # consume '='

                        # Parse value (string, boolean, number)
                        if self.match(TokenType.STRING):
                            value = self.advance().value
                        elif self.match(TokenType.BOOLEAN):
                            value = self.advance().value
                        elif self.match(TokenType.INTEGER):
                            value = self.advance().value
                        elif self.match(TokenType.FLOAT):
                            value = self.advance().value
                        else:
                            raise self.error(f"Expected value for annotation key '{key}'")

                        metadata[key] = value

                        if self.match(TokenType.COMMA):
                            self.advance()
                    self.expect(TokenType.RPAREN)

            self.skip_newlines()

        return doc_comment, metadata

    def parse_contract_clause(self) -> IRContractClause:
        """
        Parse a contract clause (@requires, @ensures, @invariant).

        Syntax: @requires clause_name: boolean_expression
        """
        self.expect(TokenType.AT)  # consume '@'
        clause_type = self.expect(TokenType.IDENTIFIER).value

        if clause_type not in ("requires", "ensures", "invariant"):
            raise self.error(f"Expected 'requires', 'ensures', or 'invariant', got '{clause_type}'")

        # Parse clause name
        clause_name = self.expect(TokenType.IDENTIFIER).value
        self.expect(TokenType.COLON)  # consume ':'

        # Parse boolean expression
        expression = self.parse_expression()

        return IRContractClause(
            clause_type=clause_type,
            name=clause_name,
            expression=expression
        )

    def parse_effects_annotation(self) -> List[str]:
        """
        Parse @effects annotation.

        Syntax: @effects [effect1, effect2, effect3]
        """
        self.expect(TokenType.AT)  # consume '@'
        effects_keyword = self.expect(TokenType.IDENTIFIER).value
        if effects_keyword != "effects":
            raise self.error(f"Expected 'effects', got '{effects_keyword}'")

        self.expect(TokenType.LBRACKET)  # consume '['

        effects = []
        while not self.match(TokenType.RBRACKET):
            # Parse effect as dot-separated identifier: database.write, event.emit("name")
            # For simplicity, parse as string or property access
            if self.match(TokenType.STRING):
                effects.append(self.advance().value)
            elif self.match(TokenType.IDENTIFIER):
                # Parse identifier chain: database.write
                effect_parts = [self.advance().value]
                while self.match(TokenType.DOT):
                    self.advance()
                    effect_parts.append(self.expect(TokenType.IDENTIFIER).value)
                effects.append(".".join(effect_parts))
            else:
                raise self.error("Expected effect identifier or string")

            if self.match(TokenType.COMMA):
                self.advance()

        self.expect(TokenType.RBRACKET)  # consume ']'

        return effects

    def parse_function(self) -> IRFunction:
        """
        Parse C-style function definition with optional generic parameters.

        Syntax: function name<T>(param1: type1, param2: type2) -> return_type throws Error { body }
        """
        is_async = False
        if self.match(TokenType.KEYWORD) and self.current().value == "async":
            is_async = True
            self.advance()

        self.expect(TokenType.KEYWORD)  # "function"
        name = self.expect(TokenType.IDENTIFIER).value

        # Parse generic parameters: <T> or <T, U>
        generic_params = []
        if self.match(TokenType.LT):
            self.advance()  # consume '<'
            generic_params.append(self.expect(TokenType.IDENTIFIER).value)
            while self.match(TokenType.COMMA):
                self.advance()  # consume ','
                generic_params.append(self.expect(TokenType.IDENTIFIER).value)
            self.expect(TokenType.GT)  # consume '>'

        # Parse parameters: (x: int, y: int)
        self.expect(TokenType.LPAREN)
        params = []

        if not self.match(TokenType.RPAREN):
            while True:
                param_name = self.expect(TokenType.IDENTIFIER).value

                # Type annotation
                param_type = None
                if self.match(TokenType.COLON):
                    self.advance()  # consume ':'
                    param_type = self.parse_type()

                # Default value
                default_value = None
                if self.match(TokenType.ASSIGN):
                    self.advance()  # consume '='
                    default_value = self.parse_expression()

                params.append(IRParameter(
                    name=param_name,
                    param_type=param_type,
                    default_value=default_value,
                    is_variadic=False,
                ))

                if self.match(TokenType.COMMA):
                    self.advance()  # consume ','
                else:
                    break

        self.expect(TokenType.RPAREN)

        # Parse return type: -> int
        return_type = None
        if self.match(TokenType.ARROW):
            self.advance()  # consume '->'
            return_type = self.parse_type()

        # Parse throws: throws Error1, Error2
        throws = []
        if self.match(TokenType.KEYWORD) and self.current().value == "throws":
            self.advance()  # consume 'throws'
            while True:
                throws.append(self.expect(TokenType.IDENTIFIER).value)
                if self.match(TokenType.COMMA):
                    self.advance()
                else:
                    break

        # Parse contract clauses and effects
        requires = []
        ensures = []
        effects = []

        # Parse body: { statements } (C-style) or : INDENT statements DEDENT (Python-style)
        if self.match(TokenType.LBRACE):
            # C-style: { ... }
            self.advance()
            self.skip_newlines()

            # Parse contract clauses at the beginning of function body
            while self.match(TokenType.AT):
                peek_ahead = self.peek()
                if peek_ahead.type == TokenType.IDENTIFIER:
                    clause_type = peek_ahead.value
                    if clause_type == "requires":
                        requires.append(self.parse_contract_clause())
                    elif clause_type == "ensures":
                        ensures.append(self.parse_contract_clause())
                    elif clause_type == "effects":
                        effects = self.parse_effects_annotation()
                    else:
                        break  # Not a contract clause
                else:
                    break
                self.skip_newlines()

            body = []
            while not self.match(TokenType.RBRACE):
                self.skip_newlines()
                if self.match(TokenType.RBRACE):
                    break

                stmt = self.parse_statement()
                if stmt:
                    body.append(stmt)

                # Optional semicolon
                if self.match(TokenType.SEMICOLON):
                    self.advance()

                self.skip_newlines()

            self.expect(TokenType.RBRACE)
        elif self.match(TokenType.COLON):
            # Python-style: : INDENT ... DEDENT
            self.advance()
            self.expect(TokenType.NEWLINE)
            self.expect(TokenType.INDENT)

            # Parse contract clauses at the beginning of function body
            while self.match(TokenType.AT):
                peek_ahead = self.peek()
                if peek_ahead.type == TokenType.IDENTIFIER:
                    clause_type = peek_ahead.value
                    if clause_type == "requires":
                        requires.append(self.parse_contract_clause())
                    elif clause_type == "ensures":
                        ensures.append(self.parse_contract_clause())
                    elif clause_type == "effects":
                        effects = self.parse_effects_annotation()
                    else:
                        break  # Not a contract clause
                else:
                    break
                self.skip_newlines()

            body = self.parse_statement_list()
            self.expect(TokenType.DEDENT)
        else:
            raise self.error("Expected '{' or ':' to start function body")

        return IRFunction(
            name=name,
            generic_params=generic_params,
            params=params,
            return_type=return_type,
            throws=throws,
            body=body,
            is_async=is_async,
            requires=requires,
            ensures=ensures,
            effects=effects,
        )

    def parse_class(self) -> IRClass:
        """
        Parse class definition with optional generic parameters.
        Supports both C-style ({}) and Python-style (:) syntax.

        Syntax:
            # C-style
            class User {
                id: string;
                name: string;

                constructor(id: string, name: string) {
                    self.id = id;
                    self.name = name;
                }

                function greet() -> string {
                    return "Hello";
                }
            }

            # Python-style (simple - properties only)
            class List<T>:
                items: array<T>
        """
        self.expect(TokenType.KEYWORD)  # "class"
        name = self.expect(TokenType.IDENTIFIER).value

        # Parse generic parameters: <T> or <K, V>
        generic_params = []
        if self.match(TokenType.LT):
            self.advance()  # consume '<'
            generic_params.append(self.expect(TokenType.IDENTIFIER).value)
            while self.match(TokenType.COMMA):
                self.advance()  # consume ','
                generic_params.append(self.expect(TokenType.IDENTIFIER).value)
            self.expect(TokenType.GT)  # consume '>'

        # Check for Python-style or C-style syntax
        if self.match(TokenType.COLON):
            # Python-style: class Name<T>: INDENT properties DEDENT
            self.advance()  # consume ':'
            self.expect(TokenType.NEWLINE)
            self.expect(TokenType.INDENT)

            properties = []
            # Parse properties (simple style - just name: type declarations)
            while not self.match(TokenType.DEDENT):
                self.skip_newlines()  # Skip blank lines
                if self.match(TokenType.DEDENT):
                    break

                # Skip docstrings (triple-quoted strings in class body)
                if self.match(TokenType.STRING):
                    self.advance()  # consume docstring
                    if self.match(TokenType.NEWLINE):
                        self.advance()
                    continue

                # Property: name: type
                if self.match(TokenType.IDENTIFIER):
                    prop_name = self.advance().value
                    self.expect(TokenType.COLON)
                    prop_type = self.parse_type()

                    # Consume NEWLINE if present (may not be there before DEDENT)
                    if self.match(TokenType.NEWLINE):
                        self.advance()

                    properties.append(IRProperty(
                        name=prop_name,
                        prop_type=prop_type
                    ))

            self.expect(TokenType.DEDENT)

            return IRClass(
                name=name,
                generic_params=generic_params,
                properties=properties,
                methods=[],
                constructor=None
            )

        # C-style: class Name<T> { ... }
        self.expect(TokenType.LBRACE)  # "{"

        properties = []
        constructor = None
        methods = []

        # Parse class body
        while not self.match(TokenType.RBRACE):
            self.skip_newlines()
            if self.match(TokenType.RBRACE):
                break

            # Check for constructor or function (method)
            if self.match(TokenType.KEYWORD):
                keyword = self.current().value

                if keyword == "constructor":
                    # Parse constructor
                    self.advance()
                    self.expect(TokenType.LPAREN)

                    # Parse parameters
                    params = []
                    while not self.match(TokenType.RPAREN):
                        # Allow both identifiers and keywords as parameter names
                        if self.match(TokenType.IDENTIFIER):
                            param_name = self.advance().value
                        elif self.match(TokenType.KEYWORD):
                            param_name = self.advance().value
                        else:
                            raise self.error("Expected parameter name")

                        self.expect(TokenType.COLON)
                        param_type = self.parse_type()
                        params.append(IRParameter(name=param_name, param_type=param_type))

                        if self.match(TokenType.COMMA):
                            self.advance()
                        elif not self.match(TokenType.RPAREN):
                            raise self.error("Expected ',' or ')' in constructor parameters")

                    self.expect(TokenType.RPAREN)
                    self.expect(TokenType.LBRACE)

                    # Parse body
                    body = self.parse_statement_list()

                    self.expect(TokenType.RBRACE)

                    constructor = IRFunction(
                        name="__init__",
                        params=params,
                        body=body,
                        return_type=IRType(name="void")
                    )

                elif keyword == "function":
                    # Parse method (same as regular function)
                    method = self.parse_function()
                    methods.append(method)

                # Check if keyword is followed by colon (property with keyword name)
                elif self.peek().type == TokenType.COLON:
                    # This is a property with a keyword as its name
                    # (e.g., method: string, body: map, type: string)
                    prop_name = self.advance().value  # consume keyword as property name
                    self.expect(TokenType.COLON)
                    prop_type = self.parse_type()
                    self.consume_statement_terminator()

                    properties.append(IRProperty(
                        name=prop_name,
                        prop_type=prop_type
                    ))

                else:
                    raise self.error(f"Unexpected keyword in class body: {keyword}")

            # Check for property declaration (identifier)
            elif self.match(TokenType.IDENTIFIER):
                # Property: name: type;
                prop_name = self.advance().value
                self.expect(TokenType.COLON)
                prop_type = self.parse_type()
                self.consume_statement_terminator()

                properties.append(IRProperty(
                    name=prop_name,
                    prop_type=prop_type
                ))

            else:
                raise self.error("Expected property, constructor, or method in class body")

        self.expect(TokenType.RBRACE)  # Close class

        return IRClass(
            name=name,
            generic_params=generic_params,
            properties=properties,
            methods=methods,
            constructor=constructor
        )

    def parse_class_old_style(self) -> IRClass:
        """Parse class definition (old YAML-style - deprecated)."""
        self.expect(TokenType.KEYWORD)  # "class"
        name = self.expect(TokenType.IDENTIFIER).value

        base_classes = []
        if self.match(TokenType.COLON) and self.peek().type == TokenType.IDENTIFIER:
            # Inheritance: class Foo: Bar, Baz
            self.advance()  # :
            base_classes.append(self.expect(TokenType.IDENTIFIER).value)
            while self.match(TokenType.COMMA):
                self.advance()
                base_classes.append(self.expect(TokenType.IDENTIFIER).value)

        self.expect(TokenType.COLON)
        self.expect(TokenType.NEWLINE)
        self.expect(TokenType.INDENT)

        properties = []
        constructor = None
        methods = []

        # Parse class blocks (old YAML style)
        while not self.match(TokenType.DEDENT):
            self.skip_newlines()
            if self.match(TokenType.DEDENT):
                break

            if not self.match(TokenType.KEYWORD):
                raise self.error("Expected class member (properties/constructor/method)")

            keyword = self.current().value

            if keyword == "properties":
                self.advance()
                self.expect(TokenType.COLON)
                self.expect(TokenType.NEWLINE)
                self.expect(TokenType.INDENT)
                properties = self.parse_properties()
                self.expect(TokenType.DEDENT)

            elif keyword == "constructor":
                self.advance()
                self.expect(TokenType.COLON)
                self.expect(TokenType.NEWLINE)
                self.expect(TokenType.INDENT)

                params = []
                body = []

                while not self.match(TokenType.DEDENT):
                    self.skip_newlines()
                    if self.match(TokenType.DEDENT):
                        break

                    kw = self.current().value
                    if kw == "params":
                        self.advance()
                        self.expect(TokenType.COLON)
                        self.expect(TokenType.NEWLINE)
                        self.expect(TokenType.INDENT)
                        params = self.parse_parameters()
                        self.expect(TokenType.DEDENT)
                    elif kw == "body":
                        self.advance()
                        self.expect(TokenType.COLON)
                        self.expect(TokenType.NEWLINE)
                        self.expect(TokenType.INDENT)
                        body = self.parse_statement_list()
                        self.expect(TokenType.DEDENT)

                constructor = IRFunction(
                    name="__init__",
                    params=params,
                    body=body,
                )
                self.expect(TokenType.DEDENT)

            elif keyword == "method":
                self.advance()
                method_name = self.expect(TokenType.IDENTIFIER).value
                self.expect(TokenType.COLON)
                self.expect(TokenType.NEWLINE)
                self.expect(TokenType.INDENT)

                params = []
                return_type = None
                throws = []
                body = []

                while not self.match(TokenType.DEDENT):
                    self.skip_newlines()
                    if self.match(TokenType.DEDENT):
                        break

                    kw = self.current().value
                    if kw == "params":
                        self.advance()
                        self.expect(TokenType.COLON)
                        self.expect(TokenType.NEWLINE)
                        self.expect(TokenType.INDENT)
                        params = self.parse_parameters()
                        self.expect(TokenType.DEDENT)
                    elif kw == "returns":
                        self.advance()
                        self.expect(TokenType.COLON)
                        self.expect(TokenType.NEWLINE)
                        self.expect(TokenType.INDENT)
                        # Simplified: take first return type
                        field_name = self.expect(TokenType.IDENTIFIER).value
                        return_type = self.parse_type()
                        self.expect(TokenType.NEWLINE)
                        self.expect(TokenType.DEDENT)
                    elif kw == "throws":
                        self.advance()
                        self.expect(TokenType.COLON)
                        self.expect(TokenType.NEWLINE)
                        self.expect(TokenType.INDENT)
                        while not self.match(TokenType.DEDENT):
                            self.skip_newlines()
                            if self.match(TokenType.DEDENT):
                                break
                            self.expect(TokenType.MINUS)
                            throws.append(self.expect(TokenType.IDENTIFIER).value)
                            self.expect(TokenType.NEWLINE)
                        self.expect(TokenType.DEDENT)
                    elif kw == "body":
                        self.advance()
                        self.expect(TokenType.COLON)
                        self.expect(TokenType.NEWLINE)
                        self.expect(TokenType.INDENT)
                        body = self.parse_statement_list()
                        self.expect(TokenType.DEDENT)

                methods.append(IRFunction(
                    name=method_name,
                    params=params,
                    return_type=return_type,
                    throws=throws,
                    body=body,
                ))
                self.expect(TokenType.DEDENT)

        self.expect(TokenType.DEDENT)

        return IRClass(
            name=name,
            base_classes=base_classes,
            properties=properties,
            constructor=constructor,
            methods=methods,
        )

    # ========================================================================
    # Helper parsers
    # ========================================================================

    def parse_function_type(self) -> IRType:
        """
        Parse function type: function(T, U) -> R

        This represents a function signature as a type, used in parameters like:
        fn: function(T) -> U
        """
        self.expect(TokenType.KEYWORD)  # consume "function"
        self.expect(TokenType.LPAREN)

        # Parse parameter types
        param_types = []
        while not self.match(TokenType.RPAREN):
            param_types.append(self.parse_type())
            if self.match(TokenType.COMMA):
                self.advance()
            elif not self.match(TokenType.RPAREN):
                raise self.error("Expected ',' or ')' in function type")

        self.expect(TokenType.RPAREN)

        # Parse return type
        return_type = None
        if self.match(TokenType.ARROW):
            self.advance()
            return_type = self.parse_type()

        # Represent function type as IRType with special name
        # We'll store param types in generic_args and return type in metadata
        func_type = IRType(name="function", generic_args=param_types)
        if return_type:
            func_type.metadata["return_type"] = return_type

        return func_type

    def parse_type(self) -> IRType:
        """Parse type annotation."""
        # Check for function type: function(T, U) -> R
        if self.match(TokenType.KEYWORD) and self.current().value == "function":
            return self.parse_function_type()

        name = self.expect(TokenType.IDENTIFIER).value

        # Generic types
        generic_args = []
        if self.match(TokenType.LT):
            self.advance()
            generic_args.append(self.parse_type())
            while self.match(TokenType.COMMA):
                self.advance()
                generic_args.append(self.parse_type())

            # Handle nested generics: >> should be split into > >
            if self.match(TokenType.RSHIFT):
                # We hit >> when expecting >
                # Split it: consume the token as if it were >, and inject another > for next parse
                self.advance()  # consume >>
                # Inject a GT token back into the stream
                gt_token = Token(TokenType.GT, ">", self.current().line, self.current().column)
                self.tokens.insert(self.pos, gt_token)
            else:
                self.expect(TokenType.GT)

        # Union types
        union_types = []
        while self.match(TokenType.BIT_OR):  # | operator
            self.advance()
            union_types.append(self.parse_type())

        # Optional marker
        is_optional = False
        if self.match(TokenType.QUESTION):
            self.advance()
            is_optional = True

        return IRType(
            name=name,
            generic_args=generic_args,
            union_types=union_types,
            is_optional=is_optional,
        )

    def parse_parameters(self) -> List[IRParameter]:
        """Parse function parameters."""
        params = []
        while not self.match(TokenType.DEDENT):
            self.skip_newlines()
            if self.match(TokenType.DEDENT):
                break

            param_name = self.expect(TokenType.IDENTIFIER).value
            param_type = self.parse_type()

            default_value = None
            if self.match(TokenType.ASSIGN):
                self.advance()
                default_value = self.parse_expression()

            params.append(IRParameter(
                name=param_name,
                param_type=param_type,
                default_value=default_value,
            ))
            self.expect(TokenType.NEWLINE)

        return params

    def parse_properties(self) -> List[IRProperty]:
        """Parse class properties."""
        properties = []
        while not self.match(TokenType.DEDENT):
            self.skip_newlines()
            if self.match(TokenType.DEDENT):
                break

            prop_name = self.expect(TokenType.IDENTIFIER).value
            prop_type = self.parse_type()

            default_value = None
            if self.match(TokenType.ASSIGN):
                self.advance()
                default_value = self.parse_expression()

            properties.append(IRProperty(
                name=prop_name,
                prop_type=prop_type,
                default_value=default_value,
            ))
            self.expect(TokenType.NEWLINE)

        return properties

    # ========================================================================
    # Statement parsing
    # ========================================================================

    def parse_statement_list(self) -> List[IRStatement]:
        """Parse a list of statements (stops at DEDENT, RBRACE, or EOF)."""
        statements = []
        while not self.match(TokenType.DEDENT, TokenType.RBRACE, TokenType.EOF):
            self.skip_newlines()
            if self.match(TokenType.DEDENT, TokenType.RBRACE, TokenType.EOF):
                break
            statements.append(self.parse_statement())
        return statements

    def parse_statement(self) -> IRStatement:
        """Parse a single statement."""
        if self.match(TokenType.KEYWORD):
            keyword = self.current().value

            if keyword == "let":
                return self.parse_assignment(is_declaration=True)
            elif keyword == "if":
                return self.parse_if()
            elif keyword == "for":
                return self.parse_for()
            elif keyword == "while":
                return self.parse_while()
            elif keyword == "try":
                return self.parse_try()
            elif keyword == "return":
                return self.parse_return()
            elif keyword == "throw":
                return self.parse_throw()
            elif keyword == "break":
                self.advance()
                self.consume_statement_terminator()
                return IRBreak()
            elif keyword == "continue":
                self.advance()
                self.consume_statement_terminator()
                return IRContinue()
            elif keyword == "pass":
                self.advance()
                self.consume_statement_terminator()
                return IRPass()

        # Check for assignment (simple or indexed/property)
        # Save current position to potentially parse as assignment
        saved_pos = self.pos

        # Try to parse as assignment target (identifier or self keyword)
        if self.match(TokenType.IDENTIFIER) or (self.match(TokenType.KEYWORD) and self.current().value == "self"):
            # Could be assignment - parse the left side
            target_expr = self.parse_postfix()

            # Check if followed by assignment operator
            if self.match(TokenType.ASSIGN, TokenType.PLUS_ASSIGN, TokenType.MINUS_ASSIGN,
                         TokenType.STAR_ASSIGN, TokenType.SLASH_ASSIGN):
                return self.parse_assignment(is_declaration=False, target_expr=target_expr)
            else:
                # Not an assignment, it's an expression statement
                # Continue parsing the rest of the expression
                expr = target_expr
                # Check if there are more operators (binary, ternary, etc.)
                if not self.match(TokenType.NEWLINE, TokenType.SEMICOLON, TokenType.RBRACE, TokenType.EOF):
                    # Reset and parse as full expression
                    self.pos = saved_pos
                    expr = self.parse_expression()
                self.consume_statement_terminator()
                return expr

        # Expression statement (not starting with identifier)
        expr = self.parse_expression()
        self.consume_statement_terminator()
        return expr  # Will be wrapped as IRCall if it's a function call

    def parse_assignment(self, is_declaration: bool, target_expr=None) -> IRAssignment:
        """
        Parse assignment statement.

        Can handle:
        - let x = value (declaration)
        - x = value (simple assignment)
        - arr[0] = value (indexed assignment)
        - obj.prop = value (property assignment)
        """
        if is_declaration:
            self.expect(TokenType.KEYWORD)  # "let"
            target = self.expect(TokenType.IDENTIFIER).value
            target_expr = IRIdentifier(name=target)
        elif target_expr is None:
            # Parse target expression (could be identifier, index, or property access)
            target_expr = self.parse_postfix()

        # Extract simple name for target if it's an identifier
        if isinstance(target_expr, IRIdentifier):
            target = target_expr.name
        else:
            # For indexed/property assignments, use the expression itself
            target = target_expr

        # Optional type annotation
        var_type = None

        operator = "="
        if self.match(TokenType.ASSIGN):
            self.advance()
        elif self.match(TokenType.PLUS_ASSIGN):
            operator = "+="
            self.advance()
        elif self.match(TokenType.MINUS_ASSIGN):
            operator = "-="
            self.advance()
        elif self.match(TokenType.STAR_ASSIGN):
            operator = "*="
            self.advance()
        elif self.match(TokenType.SLASH_ASSIGN):
            operator = "/="
            self.advance()

        value = self.parse_expression()
        self.consume_statement_terminator()

        return IRAssignment(
            target=target,
            value=value,
            is_declaration=is_declaration,
            var_type=var_type,
        )

    def parse_if(self) -> IRIf:
        """
        Parse if statement.
        Supports both styles:
        - C-style: if (condition) { body }
        - Python-style: if condition: INDENT body DEDENT
        """
        self.expect(TokenType.KEYWORD)  # "if"

        # Parse condition (with or without parentheses)
        has_parens = False
        if self.match(TokenType.LPAREN):
            self.advance()
            has_parens = True

        condition = self.parse_expression()

        if has_parens:
            self.expect(TokenType.RPAREN)

        # Parse body: either { ... } or : INDENT ... DEDENT
        if self.match(TokenType.LBRACE):
            # C-style: if (cond) { body }
            self.advance()
            self.skip_newlines()
            then_body = []
            while not self.match(TokenType.RBRACE):
                self.skip_newlines()
                if self.match(TokenType.RBRACE):
                    break
                stmt = self.parse_statement()
                if stmt:
                    then_body.append(stmt)
                if self.match(TokenType.SEMICOLON):
                    self.advance()
                self.skip_newlines()
            self.expect(TokenType.RBRACE)
        else:
            # Python-style: if cond: INDENT body DEDENT
            self.expect(TokenType.COLON)
            self.expect(TokenType.NEWLINE)
            self.expect(TokenType.INDENT)
            then_body = self.parse_statement_list()
            self.expect(TokenType.DEDENT)

        # Parse else/elif
        # Skip only NEWLINES, NOT DEDENTS (DEDENT marks end of function body in Python-style)
        while self.match(TokenType.NEWLINE):
            self.advance()
        else_body = []
        if self.match(TokenType.KEYWORD) and self.current().value == "else":
            self.advance()

            # Check for "else if"
            if self.match(TokenType.KEYWORD) and self.current().value == "if":
                # else if -> treat as nested if
                else_body = [self.parse_if()]
            else:
                # Regular else block
                if self.match(TokenType.LBRACE):
                    # C-style: else { body }
                    self.advance()
                    self.skip_newlines()
                    while not self.match(TokenType.RBRACE):
                        self.skip_newlines()
                        if self.match(TokenType.RBRACE):
                            break
                        stmt = self.parse_statement()
                        if stmt:
                            else_body.append(stmt)
                        if self.match(TokenType.SEMICOLON):
                            self.advance()
                        self.skip_newlines()
                    self.expect(TokenType.RBRACE)
                else:
                    # Python-style: else: INDENT body DEDENT
                    self.expect(TokenType.COLON)
                    self.expect(TokenType.NEWLINE)
                    self.expect(TokenType.INDENT)
                    else_body = self.parse_statement_list()
                    self.expect(TokenType.DEDENT)

        return IRIf(condition=condition, then_body=then_body, else_body=else_body)

    def parse_for(self):
        """
        Parse for loop - detects and delegates to appropriate parser.

        Syntax:
            # C-style (requires parentheses)
            for (item in items) { body }              # for-in loop
            for (let i = 0; i < 10; i = i + 1) { }    # C-style loop

            # Python-style (no parentheses)
            for item in items:                        # for-in loop
                body
        """
        self.expect(TokenType.KEYWORD)  # "for"

        # Check for C-style (with parentheses) or Python-style (without)
        has_parens = self.match(TokenType.LPAREN)

        if has_parens:
            self.advance()  # consume '('

            # Peek ahead to determine loop type
            # C-style: starts with "let"
            # for-in: starts with identifier
            if self.match(TokenType.KEYWORD) and self.current().value == "let":
                return self.parse_for_c_style()
            else:
                return self.parse_for_in(has_parens=True)
        else:
            # Python-style: for item in items:
            return self.parse_for_in(has_parens=False)

    def parse_for_in(self, has_parens: bool = True) -> IRFor:
        """
        Parse for-in loop.

        Syntax:
            # C-style (has_parens=True)
            for (item in items) { body }
            for (i in range(0, 10)) { body }
            for (index, value in enumerate(items)) { body }

            # Python-style (has_parens=False)
            for item in items:
                body
        """
        # Parse iterator(s) - could be single or tuple (for enumerate)
        iterator = self.expect(TokenType.IDENTIFIER).value
        index_var = None

        # Check for comma (enumerate pattern: index, value)
        if self.match(TokenType.COMMA):
            self.advance()
            index_var = iterator
            iterator = self.expect(TokenType.IDENTIFIER).value

        # Expect "in" keyword (could be KEYWORD or identifier "in")
        if not self.match(TokenType.KEYWORD) and not (self.match(TokenType.IDENTIFIER) and self.current().value == "in"):
            raise self.error(f"Expected 'in' keyword in for loop, got {self.current().type.value}: {self.current().value}")
        if self.current().value != "in":
            raise self.error(f"Expected 'in' keyword in for loop, got: {self.current().value}")
        self.advance()

        # Parse iterable expression
        iterable = self.parse_expression()

        # Parse body - different syntax based on has_parens
        if has_parens:
            # C-style: for (item in items) { body }
            self.expect(TokenType.RPAREN)   # ")"
            self.expect(TokenType.LBRACE)   # "{"
            body = self.parse_statement_list()
            self.expect(TokenType.RBRACE)   # "}"
        else:
            # Python-style: for item in items: INDENT body DEDENT
            self.expect(TokenType.COLON)    # ":"
            self.expect(TokenType.NEWLINE)
            self.expect(TokenType.INDENT)
            body = self.parse_statement_list()
            self.expect(TokenType.DEDENT)

        # Create IRFor with optional index_var
        for_node = IRFor(iterator=iterator, iterable=iterable, body=body)
        if index_var:
            # Store index_var in metadata for enumerate support
            for_node.index_var = index_var

        return for_node

    def parse_for_c_style(self) -> IRForCStyle:
        """
        Parse C-style for loop.

        Syntax:
            for (let i = 0; i < 10; i = i + 1) { body }
        """
        # Parse initialization: let i = 0
        self.expect(TokenType.KEYWORD)  # "let"
        var_name = self.expect(TokenType.IDENTIFIER).value
        self.expect(TokenType.ASSIGN)
        init_value = self.parse_expression()
        init = IRAssignment(target=var_name, value=init_value, is_declaration=True)

        # Parse condition: i < 10
        self.expect(TokenType.SEMICOLON)
        condition = self.parse_expression()

        # Parse increment: i = i + 1
        self.expect(TokenType.SEMICOLON)
        increment_target_name = self.expect(TokenType.IDENTIFIER).value
        increment_target = IRIdentifier(name=increment_target_name)

        # Parse assignment operator
        operator = "="
        if self.match(TokenType.ASSIGN):
            self.advance()
        elif self.match(TokenType.PLUS_ASSIGN):
            operator = "+="
            self.advance()
        elif self.match(TokenType.MINUS_ASSIGN):
            operator = "-="
            self.advance()
        elif self.match(TokenType.STAR_ASSIGN):
            operator = "*="
            self.advance()
        elif self.match(TokenType.SLASH_ASSIGN):
            operator = "/="
            self.advance()
        else:
            raise self.error("Expected assignment operator in for loop increment")

        increment_value = self.parse_expression()
        increment = IRAssignment(target=increment_target_name, value=increment_value, is_declaration=False)

        self.expect(TokenType.RPAREN)   # ")"
        self.expect(TokenType.LBRACE)   # "{"

        # Parse body
        body = self.parse_statement_list()

        self.expect(TokenType.RBRACE)   # "}"

        return IRForCStyle(init=init, condition=condition, increment=increment, body=body)

    def parse_while(self) -> IRWhile:
        """
        Parse while loop (C-style syntax).

        Syntax:
            while (condition) { body }
        """
        self.expect(TokenType.KEYWORD)  # "while"
        self.expect(TokenType.LPAREN)   # "("
        condition = self.parse_expression()
        self.expect(TokenType.RPAREN)   # ")"
        self.expect(TokenType.LBRACE)   # "{"
        body = self.parse_statement_list()
        self.expect(TokenType.RBRACE)   # "}"

        return IRWhile(condition=condition, body=body)

    def parse_try(self) -> IRTry:
        """
        Parse try-catch statement with C-style brace syntax.

        Syntax:
            try {
                // try body
            } catch (error_var) {
                // catch body
            } finally {
                // finally body
            }
        """
        self.expect(TokenType.KEYWORD)  # "try"
        self.expect(TokenType.LBRACE)   # "{"
        try_body = self.parse_statement_list()
        self.expect(TokenType.RBRACE)   # "}"

        catch_blocks = []
        while self.match(TokenType.KEYWORD) and self.current().value == "catch":
            self.advance()
            exception_type = None
            exception_var = None

            # Parse catch parameter: (error_var) or (ExceptionType error_var)
            if self.match(TokenType.LPAREN):
                self.advance()

                # Check if we have type annotation or just variable
                if self.match(TokenType.IDENTIFIER):
                    first_identifier = self.advance().value

                    # If another identifier follows, first is type, second is variable
                    if self.match(TokenType.IDENTIFIER):
                        exception_type = first_identifier
                        exception_var = self.advance().value
                    else:
                        # Just a variable name
                        exception_var = first_identifier

                self.expect(TokenType.RPAREN)

            self.expect(TokenType.LBRACE)   # "{"
            catch_body = self.parse_statement_list()
            self.expect(TokenType.RBRACE)   # "}"

            catch_blocks.append(IRCatch(
                exception_type=exception_type,
                exception_var=exception_var,
                body=catch_body,
            ))

        finally_body = []
        if self.match(TokenType.KEYWORD) and self.current().value == "finally":
            self.advance()
            self.expect(TokenType.LBRACE)   # "{"
            finally_body = self.parse_statement_list()
            self.expect(TokenType.RBRACE)   # "}"

        return IRTry(try_body=try_body, catch_blocks=catch_blocks, finally_body=finally_body)

    def parse_return(self) -> IRReturn:
        """Parse return statement."""
        self.expect(TokenType.KEYWORD)  # "return"
        value = None
        if not self.match(TokenType.NEWLINE, TokenType.SEMICOLON, TokenType.RBRACE):
            value = self.parse_expression()
        self.consume_statement_terminator()
        return IRReturn(value=value)

    def parse_throw(self) -> IRThrow:
        """Parse throw statement."""
        self.expect(TokenType.KEYWORD)  # "throw"
        exception = self.parse_expression()
        self.consume_statement_terminator()
        return IRThrow(exception=exception)

    # ========================================================================
    # Expression parsing (precedence climbing)
    # ========================================================================

    def parse_expression(self) -> IRExpression:
        """Parse expression with precedence."""
        return self.parse_ternary()

    def parse_ternary(self) -> IRExpression:
        """Parse ternary expression: x if cond else y"""
        expr = self.parse_logical_or()

        if self.match(TokenType.KEYWORD) and self.current().value == "if":
            # Save position in case this isn't a complete ternary expression
            saved_pos = self.pos
            self.advance()  # consume 'if'
            condition = self.parse_logical_or()
            if self.match(TokenType.KEYWORD) and self.current().value == "else":
                self.advance()
                false_value = self.parse_logical_or()
                return IRTernary(
                    condition=condition,
                    true_value=expr,
                    false_value=false_value,
                )
            else:
                # No 'else' found - this is not a ternary expression
                # Restore position to before 'if' and return original expression
                self.pos = saved_pos

        return expr

    def parse_logical_or(self) -> IRExpression:
        """Parse logical OR."""
        left = self.parse_logical_and()

        while self.match(TokenType.OR) or self.match(TokenType.LOGICAL_OR):
            op = self.advance().value
            right = self.parse_logical_and()
            left = IRBinaryOp(op=BinaryOperator.OR, left=left, right=right)

        return left

    def parse_logical_and(self) -> IRExpression:
        """Parse logical AND."""
        left = self.parse_logical_not()

        while self.match(TokenType.AND) or self.match(TokenType.LOGICAL_AND):
            op = self.advance().value
            right = self.parse_logical_not()
            left = IRBinaryOp(op=BinaryOperator.AND, left=left, right=right)

        return left

    def parse_logical_not(self) -> IRExpression:
        """Parse logical NOT."""
        if self.match(TokenType.NOT):
            self.advance()
            operand = self.parse_comparison()
            return IRUnaryOp(op=UnaryOperator.NOT, operand=operand)

        return self.parse_comparison()

    def parse_comparison(self) -> IRExpression:
        """Parse comparison operators, pattern matching, and membership tests."""
        left = self.parse_bitwise_or()

        while (self.match(TokenType.EQ, TokenType.NE, TokenType.LT, TokenType.LE, TokenType.GT, TokenType.GE, TokenType.IS) or
               (self.match(TokenType.KEYWORD) and self.current().value == "in")):
            tok = self.advance()

            # Handle pattern matching ('is' operator)
            if tok.type == TokenType.IS:
                # Parse pattern (right side of 'is')
                pattern = self.parse_pattern()
                return IRPatternMatch(value=left, pattern=pattern)

            # Handle membership test ('in' operator)
            if tok.value == "in":
                right = self.parse_bitwise_or()
                left = IRBinaryOp(op=BinaryOperator.IN, left=left, right=right)
                continue

            # Handle regular comparison operators
            op_map = {
                "==": BinaryOperator.EQUAL,
                "!=": BinaryOperator.NOT_EQUAL,
                "<": BinaryOperator.LESS_THAN,
                "<=": BinaryOperator.LESS_EQUAL,
                ">": BinaryOperator.GREATER_THAN,
                ">=": BinaryOperator.GREATER_EQUAL,
            }
            op = op_map[tok.value]
            right = self.parse_bitwise_or()
            left = IRBinaryOp(op=op, left=left, right=right)

        return left

    def parse_pattern(self) -> IRExpression:
        """
        Parse a pattern for pattern matching.

        Patterns can be:
        - Simple identifier: None
        - Enum variant: Some(val)
        - Enum variant with wildcard: Some(_)
        - Qualified variant: Option.Some(val)

        Returns an IR expression representing the pattern.
        """
        # Start with an identifier (enum variant name)
        if not self.match(TokenType.IDENTIFIER):
            raise self.error("Expected identifier in pattern")

        name = self.advance().value
        pattern = IRIdentifier(name=name)

        # Check for property access (e.g., Option.Some)
        if self.match(TokenType.DOT):
            self.advance()
            if not self.match(TokenType.IDENTIFIER):
                raise self.error("Expected identifier after '.' in pattern")
            property = self.advance().value
            pattern = IRPropertyAccess(object=pattern, property=property)

        # Check for pattern with captures: Some(val) or Some(_)
        if self.match(TokenType.LPAREN):
            self.advance()  # consume '('
            args = []

            while not self.match(TokenType.RPAREN):
                # Parse capture variable or wildcard
                if self.match(TokenType.IDENTIFIER):
                    capture = self.advance().value
                    args.append(IRIdentifier(name=capture))
                else:
                    raise self.error("Expected identifier or '_' in pattern capture")

                if self.match(TokenType.COMMA):
                    self.advance()
                elif not self.match(TokenType.RPAREN):
                    raise self.error("Expected ',' or ')' in pattern")

            self.expect(TokenType.RPAREN)  # consume ')'

            # Create IRCall representing the pattern with captures
            pattern = IRCall(function=pattern, args=args)

        return pattern

    def parse_bitwise_or(self) -> IRExpression:
        """Parse bitwise OR."""
        left = self.parse_bitwise_xor()

        while self.match(TokenType.BIT_OR):
            self.advance()
            right = self.parse_bitwise_xor()
            left = IRBinaryOp(op=BinaryOperator.BIT_OR, left=left, right=right)

        return left

    def parse_bitwise_xor(self) -> IRExpression:
        """Parse bitwise XOR."""
        left = self.parse_bitwise_and()

        while self.match(TokenType.BIT_XOR):
            self.advance()
            right = self.parse_bitwise_and()
            left = IRBinaryOp(op=BinaryOperator.BIT_XOR, left=left, right=right)

        return left

    def parse_bitwise_and(self) -> IRExpression:
        """Parse bitwise AND."""
        left = self.parse_shift()

        while self.match(TokenType.BIT_AND):
            self.advance()
            right = self.parse_shift()
            left = IRBinaryOp(op=BinaryOperator.BIT_AND, left=left, right=right)

        return left

    def parse_shift(self) -> IRExpression:
        """Parse shift operators."""
        left = self.parse_addition()

        while self.match(TokenType.LSHIFT, TokenType.RSHIFT):
            tok = self.advance()
            op = BinaryOperator.LEFT_SHIFT if tok.type == TokenType.LSHIFT else BinaryOperator.RIGHT_SHIFT
            right = self.parse_addition()
            left = IRBinaryOp(op=op, left=left, right=right)

        return left

    def parse_addition(self) -> IRExpression:
        """Parse addition and subtraction."""
        left = self.parse_multiplication()

        while self.match(TokenType.PLUS, TokenType.MINUS):
            tok = self.advance()
            op = BinaryOperator.ADD if tok.type == TokenType.PLUS else BinaryOperator.SUBTRACT
            right = self.parse_multiplication()
            left = IRBinaryOp(op=op, left=left, right=right)

        return left

    def parse_multiplication(self) -> IRExpression:
        """Parse multiplication, division, modulo, floor division."""
        left = self.parse_unary()

        while self.match(TokenType.STAR, TokenType.SLASH, TokenType.PERCENT, TokenType.POWER, TokenType.FLOOR_DIV):
            tok = self.advance()
            op_map = {
                "*": BinaryOperator.MULTIPLY,
                "/": BinaryOperator.DIVIDE,
                "%": BinaryOperator.MODULO,
                "**": BinaryOperator.POWER,
                "//": BinaryOperator.FLOOR_DIVIDE,
            }
            op = op_map[tok.value]
            right = self.parse_unary()
            left = IRBinaryOp(op=op, left=left, right=right)

        return left

    def parse_unary(self) -> IRExpression:
        """Parse unary operators."""
        if self.match(TokenType.MINUS, TokenType.PLUS, TokenType.BIT_NOT, TokenType.LOGICAL_NOT):
            tok = self.advance()
            op_map = {
                "-": UnaryOperator.NEGATE,
                "+": UnaryOperator.POSITIVE,
                "~": UnaryOperator.BIT_NOT,
                "!": UnaryOperator.NOT,  # C-style NOT operator
            }
            op = op_map[tok.value]
            operand = self.parse_unary()
            return IRUnaryOp(op=op, operand=operand)

        return self.parse_postfix()

    def parse_postfix(self) -> IRExpression:
        """Parse postfix operators (call, index, member access)."""
        expr = self.parse_primary()

        while True:
            if self.match(TokenType.LPAREN):
                # Function call
                self.advance()
                args = []
                kwargs = {}

                while not self.match(TokenType.RPAREN):
                    if self.match(TokenType.IDENTIFIER) and self.peek().type == TokenType.COLON:
                        # Named argument
                        name = self.advance().value
                        self.expect(TokenType.COLON)
                        value = self.parse_expression()
                        kwargs[name] = value
                    else:
                        # Positional argument
                        args.append(self.parse_expression())

                    if self.match(TokenType.COMMA):
                        self.advance()
                    elif not self.match(TokenType.RPAREN):
                        raise self.error("Expected ',' or ')' in function call")

                self.expect(TokenType.RPAREN)

                # Use CharCNN to predict operation_id
                operation_id = None
                operation_confidence = None
                if CHARCNN_AVAILABLE:
                    try:
                        # Reconstruct operation code (e.g., "file.read")
                        op_code = self._reconstruct_operation_code(expr)
                        if op_code:
                            # Get top prediction from CharCNN
                            predictions = lookup_operation(op_code, top_k=1)
                            if predictions:
                                operation_id, operation_confidence = predictions[0]
                    except Exception:
                        # Silently ignore CharCNN errors (don't break parsing)
                        pass

                expr = IRCall(
                    function=expr,
                    args=args,
                    kwargs=kwargs,
                    operation_id=operation_id,
                    operation_confidence=operation_confidence
                )

            elif self.match(TokenType.LBRACKET):
                # Array/map indexing or slice notation
                self.advance()

                # Check for slice notation by looking ahead for ':'
                # Slice patterns: [:], [start:], [:stop], [start:stop], [start:stop:step]
                start = None
                stop = None
                step = None
                is_slice = False

                # Check if first character is ':' (start is omitted)
                if self.match(TokenType.COLON):
                    is_slice = True
                    self.advance()  # consume ':'
                    # Parse stop if present
                    if not self.match(TokenType.RBRACKET) and not self.match(TokenType.COLON):
                        stop = self.parse_addition()  # Use parse_addition to avoid recursion
                    # Check for step
                    if self.match(TokenType.COLON):
                        self.advance()
                        if not self.match(TokenType.RBRACKET):
                            step = self.parse_addition()
                else:
                    # Parse first expression (could be index or start of slice)
                    first_expr = self.parse_addition()

                    # Check if it's a slice (has ':')
                    if self.match(TokenType.COLON):
                        is_slice = True
                        start = first_expr
                        self.advance()  # consume ':'
                        # Parse stop if present
                        if not self.match(TokenType.RBRACKET) and not self.match(TokenType.COLON):
                            stop = self.parse_addition()
                        # Check for step
                        if self.match(TokenType.COLON):
                            self.advance()
                            if not self.match(TokenType.RBRACKET):
                                step = self.parse_addition()
                    else:
                        # Simple indexing
                        self.expect(TokenType.RBRACKET)
                        expr = IRIndex(object=expr, index=first_expr)
                        continue

                # Create slice node
                self.expect(TokenType.RBRACKET)
                expr = IRSlice(object=expr, start=start, stop=stop, step=step)

            elif self.match(TokenType.DOT):
                # Member access
                self.advance()
                # Allow both identifiers and keywords as property names
                if self.match(TokenType.IDENTIFIER):
                    property = self.advance().value
                elif self.match(TokenType.KEYWORD):
                    property = self.advance().value
                else:
                    raise self.error("Expected property name")
                expr = IRPropertyAccess(object=expr, property=property)

            else:
                break

        return expr

    def parse_primary(self) -> IRExpression:
        """Parse primary expressions."""
        # Old keyword for postconditions: old expr
        if self.match(TokenType.KEYWORD) and self.current().value == "old":
            self.advance()  # consume 'old'
            expr = self.parse_primary()  # Parse the expression to reference in pre-state
            return IROldExpr(expression=expr)

        # Literals
        if self.match(TokenType.INTEGER):
            value = self.advance().value
            return IRLiteral(value=value, literal_type=LiteralType.INTEGER)

        if self.match(TokenType.FLOAT):
            value = self.advance().value
            return IRLiteral(value=value, literal_type=LiteralType.FLOAT)

        if self.match(TokenType.STRING):
            value = self.advance().value
            return IRLiteral(value=value, literal_type=LiteralType.STRING)

        if self.match(TokenType.BOOLEAN):
            value = self.advance().value
            return IRLiteral(value=value, literal_type=LiteralType.BOOLEAN)

        if self.match(TokenType.NULL):
            self.advance()
            return IRLiteral(value=None, literal_type=LiteralType.NULL)

        # Lambda (fn-style): fn(x) -> expr or fn(x, y) -> expr
        # Check BEFORE general identifier to avoid parsing as function call
        # Must look ahead to confirm there's a -> after params to distinguish from fn(item) calls
        if (self.match(TokenType.IDENTIFIER) and self.current().value == "fn" and
            self.peek().type == TokenType.LPAREN and self._is_fn_lambda()):
            self.advance()  # consume 'fn'
            self.expect(TokenType.LPAREN)
            params = []
            # Parse parameters
            while not self.match(TokenType.RPAREN):
                param_name = self.expect(TokenType.IDENTIFIER).value
                params.append(IRParameter(name=param_name, param_type=IRType(name="any")))
                if self.match(TokenType.COMMA):
                    self.advance()
                elif not self.match(TokenType.RPAREN):
                    raise self.error("Expected ',' or ')' in lambda parameters")

            self.expect(TokenType.RPAREN)
            self.expect(TokenType.ARROW)  # '->'
            body = self.parse_expression()
            return IRLambda(params=params, body=body)

        # Keywords that can be used as identifiers
        # Special cases like 'self', 'method', 'body', etc.
        if self.match(TokenType.KEYWORD):
            keyword_value = self.current().value
            # Only allow keywords that don't have syntactic meaning in this context
            # (exclude control flow keywords that must be keywords)
            control_keywords = {
                'if', 'else', 'elif', 'for', 'while', 'try', 'catch', 'finally',
                'return', 'throw', 'break', 'continue', 'pass', 'let',
                'function', 'class', 'constructor', 'enum', 'import', 'from', 'as',
                'async', 'await', 'lambda', 'module', 'version'
            }
            if keyword_value not in control_keywords:
                # Allow keywords like 'self', 'method', 'body', 'type', 'name', etc. as identifiers
                self.advance()
                return IRIdentifier(name=keyword_value)

        # Identifier
        if self.match(TokenType.IDENTIFIER):
            name = self.advance().value
            return IRIdentifier(name=name)

        # Parenthesized expression
        if self.match(TokenType.LPAREN):
            self.advance()
            expr = self.parse_expression()
            self.expect(TokenType.RPAREN)
            return expr

        # Array literal
        if self.match(TokenType.LBRACKET):
            self.advance()
            elements = []
            while not self.match(TokenType.RBRACKET):
                elements.append(self.parse_expression())
                if self.match(TokenType.COMMA):
                    self.advance()
                elif not self.match(TokenType.RBRACKET):
                    raise self.error("Expected ',' or ']' in array literal")
            self.expect(TokenType.RBRACKET)
            return IRArray(elements=elements)

        # Map literal
        if self.match(TokenType.LBRACE):
            self.advance()
            entries = {}
            while not self.match(TokenType.RBRACE):
                # Key can be identifier or string
                if self.match(TokenType.IDENTIFIER):
                    key = self.advance().value
                elif self.match(TokenType.STRING):
                    key = self.advance().value
                else:
                    raise self.error("Expected identifier or string as map key")

                self.expect(TokenType.COLON)
                value = self.parse_expression()
                entries[key] = value

                if self.match(TokenType.COMMA):
                    self.advance()
                elif not self.match(TokenType.RBRACE):
                    raise self.error("Expected ',' or '}' in map literal")

            self.expect(TokenType.RBRACE)
            return IRMap(entries=entries)

        # Lambda (Python-style): lambda x: expr
        if self.match(TokenType.KEYWORD) and self.current().value == "lambda":
            self.advance()
            params = []
            # Parse parameters
            if self.match(TokenType.IDENTIFIER):
                param_name = self.advance().value
                params.append(IRParameter(name=param_name, param_type=IRType(name="any")))
                while self.match(TokenType.COMMA):
                    self.advance()
                    param_name = self.expect(TokenType.IDENTIFIER).value
                    params.append(IRParameter(name=param_name, param_type=IRType(name="any")))

            self.expect(TokenType.COLON)
            body = self.parse_expression()
            return IRLambda(params=params, body=body)

        # Lambda (fn-style): fn(x) -> expr or fn(x, y) -> expr
        if self.match(TokenType.IDENTIFIER) and self.current().value == "fn" and self.peek().type == TokenType.LPAREN:
            self.advance()  # consume 'fn'
            self.expect(TokenType.LPAREN)
            params = []
            # Parse parameters
            while not self.match(TokenType.RPAREN):
                param_name = self.expect(TokenType.IDENTIFIER).value
                params.append(IRParameter(name=param_name, param_type=IRType(name="any")))
                if self.match(TokenType.COMMA):
                    self.advance()
                elif not self.match(TokenType.RPAREN):
                    raise self.error("Expected ',' or ')' in lambda parameters")

            self.expect(TokenType.RPAREN)
            self.expect(TokenType.ARROW)  # '->'
            body = self.parse_expression()
            return IRLambda(params=params, body=body)

        # Await expression
        if self.match(TokenType.KEYWORD) and self.current().value == "await":
            self.advance()
            expr = self.parse_expression()
            # Note: IR doesn't have IRAwait yet, wrap in metadata
            # For now, create a call-like structure
            return expr

        raise self.error(f"Unexpected token in expression: {self.current().type.value}")


# ============================================================================
# Public API
# ============================================================================


class TypeChecker:
    """Type checker for PW IR."""

    def __init__(self):
        self.type_env: Dict[str, str] = {}  # Variable name -> type
        self.function_signatures: Dict[str, Tuple[List[str], str]] = {}  # name -> (param_types, return_type)
        self.errors: List[str] = []

    def check_module(self, module: IRModule) -> None:
        """Type check entire module."""
        # First pass: collect function signatures
        for func in module.functions:
            param_types = [self._extract_type_name(p.param_type) for p in func.params]
            return_type = self._extract_type_name(func.return_type)
            self.function_signatures[func.name] = (param_types, return_type)

        # Second pass: type check each function
        for func in module.functions:
            self.check_function(func)

        # If any errors, raise
        if self.errors:
            raise PWParseError("\n".join(self.errors))

    def _extract_type_name(self, type_obj) -> str:
        """Extract type name from IRType or string."""
        if isinstance(type_obj, str):
            return type_obj
        elif hasattr(type_obj, 'name'):
            return type_obj.name
        else:
            return str(type_obj)

    def check_function(self, func: IRFunction) -> None:
        """Type check a function."""
        # Clear variable env for new function
        self.type_env = {}

        # Add parameters to environment
        for param in func.params:
            param_type = self._extract_type_name(param.param_type)
            self.type_env[param.name] = param_type

        # Check function has return type (keep as IRType object)
        if not func.return_type:
            self.errors.append(f"Function '{func.name}' missing return type annotation")
            return

        # Type check body with IRType object
        for stmt in func.body:
            self.check_statement(stmt, func.return_type)

    def check_statement(self, stmt: IRStatement, expected_return_type: Union[str, IRType]) -> None:
        """Type check a statement."""
        if isinstance(stmt, IRReturn):
            if stmt.value:
                actual_type = self.infer_type(stmt.value)
                if not self.types_compatible(actual_type, expected_return_type):
                    # Format expected type for error message
                    expected_str = str(expected_return_type) if isinstance(expected_return_type, IRType) else expected_return_type
                    self.errors.append(
                        f"Return type mismatch: expected {expected_str}, got {actual_type}"
                    )
        elif isinstance(stmt, IRAssignment):
            # Infer type from value
            value_type = self.infer_type(stmt.value)
            # Only track type if target is a simple identifier (string)
            if isinstance(stmt.target, str):
                self.type_env[stmt.target] = value_type
            # For indexed/property assignments, we don't track in type_env
            # (would need more sophisticated tracking)
        elif isinstance(stmt, IRIf):
            # Check condition is boolean (or can be used as bool)
            cond_type = self.infer_type(stmt.condition)
            # For now, accept any type as condition

            # Check then branch
            for s in stmt.then_body:
                self.check_statement(s, expected_return_type)

            # Check else branch
            if stmt.else_body:
                for s in stmt.else_body:
                    self.check_statement(s, expected_return_type)

    def infer_type(self, expr: IRExpression) -> str:
        """Infer the type of an expression."""
        if isinstance(expr, IRLiteral):
            if expr.literal_type == LiteralType.INTEGER:
                return "int"
            elif expr.literal_type == LiteralType.FLOAT:
                return "float"
            elif expr.literal_type == LiteralType.STRING:
                return "string"
            elif expr.literal_type == LiteralType.BOOLEAN:
                return "bool"
            elif expr.literal_type == LiteralType.NULL:
                return "null"
            else:
                return "any"

        elif isinstance(expr, IRIdentifier):
            # Look up in environment
            if expr.name in self.type_env:
                return self.type_env[expr.name]
            else:
                # Unknown variable - could be error or any
                return "any"

        elif isinstance(expr, IRBinaryOp):
            left_type = self.infer_type(expr.left)
            right_type = self.infer_type(expr.right)

            # Arithmetic operators
            if expr.op in [BinaryOperator.ADD, BinaryOperator.SUBTRACT,
                          BinaryOperator.MULTIPLY, BinaryOperator.DIVIDE]:
                # Special case: string concatenation
                if expr.op == BinaryOperator.ADD and (left_type == "string" or right_type == "string"):
                    return "string"

                # Type check: operands should be compatible
                if left_type != right_type and left_type != "any" and right_type != "any":
                    # Check int/float compatibility
                    if not ((left_type in ["int", "float"] and right_type in ["int", "float"])):
                        self.errors.append(
                            f"Binary operation type mismatch: {left_type} {expr.op.value} {right_type}"
                        )

                # Return type
                if left_type == "float" or right_type == "float":
                    return "float"
                return left_type if left_type != "any" else right_type

            # Comparison operators
            elif expr.op in [BinaryOperator.EQUAL, BinaryOperator.NOT_EQUAL,
                           BinaryOperator.LESS_THAN, BinaryOperator.GREATER_THAN,
                           BinaryOperator.LESS_EQUAL, BinaryOperator.GREATER_EQUAL]:
                return "bool"

            # Logical operators
            elif expr.op in [BinaryOperator.AND, BinaryOperator.OR]:
                return "bool"

            else:
                return "any"

        elif isinstance(expr, IRCall):
            # Extract function name
            func_name = None
            if isinstance(expr.function, IRIdentifier):
                func_name = expr.function.name
            elif isinstance(expr.function, str):
                func_name = expr.function

            # Look up function signature
            if func_name and func_name in self.function_signatures:
                param_types, return_type = self.function_signatures[func_name]

                # Check argument count
                if len(expr.args) != len(param_types):
                    self.errors.append(
                        f"Function '{func_name}' expects {len(param_types)} arguments, got {len(expr.args)}"
                    )

                # Check argument types
                for i, (arg, expected_type) in enumerate(zip(expr.args, param_types)):
                    actual_type = self.infer_type(arg)
                    if not self.types_compatible(actual_type, expected_type):
                        self.errors.append(
                            f"Argument {i+1} to '{func_name}': expected {expected_type}, got {actual_type}"
                        )

                return return_type
            else:
                # Unknown function - assume any
                return "any"

        else:
            return "any"

    def types_compatible(self, actual: Union[str, IRType], expected: Union[str, IRType]) -> bool:
        """
        Check if actual type is compatible with expected type.

        Supports both string type names and IRType objects.
        Handles optional types (T?) - null is always compatible with optional types.
        """
        # Convert to IRType objects if needed
        if isinstance(actual, str):
            actual_type = IRType(name=actual, is_optional=False)
        else:
            actual_type = actual

        if isinstance(expected, str):
            expected_type = IRType(name=expected, is_optional=False)
        else:
            expected_type = expected

        # Special case: If expected is optional (T?), null is always valid
        if expected_type.is_optional and actual_type.name == "null":
            return True

        # Compare base type names
        actual_name = actual_type.name
        expected_name = expected_type.name

        if actual_name == expected_name:
            return True
        if actual_name == "any" or expected_name == "any":
            return True
        # Int is compatible with float
        if actual_name == "int" and expected_name == "float":
            return True
        # Void is special
        if expected_name == "void":
            return True
        return False


def parse_pw(text: str) -> IRModule:
    """
    Parse PW DSL 2.0 text into IR.

    Args:
        text: PW DSL 2.0 source code

    Returns:
        IRModule: Root IR node

    Raises:
        PWParseError: If parsing fails
    """
    # Lexical analysis
    lexer = Lexer(text)
    tokens = lexer.tokenize()

    # Syntax analysis
    parser = Parser(tokens)
    ir = parser.parse()

    # Type checking
    type_checker = TypeChecker()
    type_checker.check_module(ir)

    return ir
