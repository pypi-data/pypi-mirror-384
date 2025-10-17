"""
Promptware DSL Core Module

This module contains the intermediate representation (IR) for the Promptware
universal code translation system. The IR serves as a language-agnostic bridge
between all supported programming languages.

Components:
- ir.py: IR node definitions and data structures
- validator.py: Semantic validation for IR trees
- type_system.py: Universal type system (future)
- pw_parser.py: PW DSL text → IR parser (future)
- pw_generator.py: IR → PW DSL text generator (future)
"""

from dsl.ir import (
    # Base classes
    IRNode,
    NodeType,
    SourceLocation,

    # Module-level nodes
    IRModule,
    IRImport,

    # Type nodes
    IRType,
    IRTypeDefinition,
    IREnum,
    IREnumVariant,

    # Function/class nodes
    IRFunction,
    IRParameter,
    IRClass,
    IRProperty,

    # Statement nodes
    IRIf,
    IRFor,
    IRWhile,
    IRTry,
    IRCatch,
    IRAssignment,
    IRReturn,
    IRThrow,
    IRBreak,
    IRContinue,
    IRPass,

    # Expression nodes
    IRCall,
    IRBinaryOp,
    IRUnaryOp,
    IRLiteral,
    IRIdentifier,
    IRProperty as IRPropertyAccess,
    IRIndex,
    IRLambda,
    IRArray,
    IRMap,
    IRTernary,
)

__all__ = [
    # Base classes
    "IRNode",
    "NodeType",
    "SourceLocation",

    # Module-level nodes
    "IRModule",
    "IRImport",

    # Type nodes
    "IRType",
    "IRTypeDefinition",
    "IREnum",
    "IREnumVariant",

    # Function/class nodes
    "IRFunction",
    "IRParameter",
    "IRClass",
    "IRProperty",

    # Statement nodes
    "IRIf",
    "IRFor",
    "IRWhile",
    "IRTry",
    "IRCatch",
    "IRAssignment",
    "IRReturn",
    "IRThrow",
    "IRBreak",
    "IRContinue",
    "IRPass",

    # Expression nodes
    "IRCall",
    "IRBinaryOp",
    "IRUnaryOp",
    "IRLiteral",
    "IRIdentifier",
    "IRPropertyAccess",
    "IRIndex",
    "IRLambda",
    "IRArray",
    "IRMap",
    "IRTernary",
]

__version__ = "2.0.0-alpha"
