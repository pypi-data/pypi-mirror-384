#!/usr/bin/env python3
"""
PW Syntax MCP Server

Universal code translation via atomic, composable MCP tools.
Exposes 30+ syntax tools plus high-level translation services.
"""

import asyncio
import sys
from pathlib import Path
from typing import Any, Dict, List

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# MCP imports
import mcp.server.stdio
import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions

# Translation bridges
from translators.python_bridge import python_to_pw, pw_to_python
from translators.go_bridge import go_to_pw, pw_to_go
from translators.rust_bridge import rust_to_pw, pw_to_rust
from translators.typescript_bridge import typescript_to_pw, pw_to_typescript
from translators.csharp_bridge import csharp_to_pw, pw_to_csharp
from translators.ir_converter import ir_to_mcp, mcp_to_ir

# Initialize MCP server
app = Server("pw-syntax")

# ============================================================================
# High-Level Translation Tools
# ============================================================================

@app.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """
    List all available PW Syntax MCP tools.
    """
    tools = [
        # ====================================================================
        # High-Level Translation Tools
        # ====================================================================
        types.Tool(
            name="translate_code",
            description="Translate code from one language to another via PW",
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Source code to translate"},
                    "from_lang": {"type": "string", "description": "Source language (python, go)"},
                    "to_lang": {"type": "string", "description": "Target language (python, go)"},
                },
                "required": ["code", "from_lang", "to_lang"],
            },
        ),
        types.Tool(
            name="python_to_pw",
            description="Parse Python code into PW MCP tree",
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Python source code"},
                },
                "required": ["code"],
            },
        ),
        types.Tool(
            name="go_to_pw",
            description="Parse Go code into PW MCP tree",
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Go source code"},
                },
                "required": ["code"],
            },
        ),
        types.Tool(
            name="pw_to_python",
            description="Generate Python code from PW MCP tree",
            inputSchema={
                "type": "object",
                "properties": {
                    "tree": {"type": "object", "description": "PW MCP tree"},
                },
                "required": ["tree"],
            },
        ),
        types.Tool(
            name="pw_to_go",
            description="Generate Go code from PW MCP tree",
            inputSchema={
                "type": "object",
                "properties": {
                    "tree": {"type": "object", "description": "PW MCP tree"},
                },
                "required": ["tree"],
            },
        ),
        types.Tool(
            name="rust_to_pw",
            description="Parse Rust code into PW MCP tree",
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Rust source code"},
                },
                "required": ["code"],
            },
        ),
        types.Tool(
            name="pw_to_rust",
            description="Generate Rust code from PW MCP tree",
            inputSchema={
                "type": "object",
                "properties": {
                    "tree": {"type": "object", "description": "PW MCP tree"},
                },
                "required": ["tree"],
            },
        ),
        types.Tool(
            name="typescript_to_pw",
            description="Parse TypeScript code into PW MCP tree",
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "TypeScript source code"},
                },
                "required": ["code"],
            },
        ),
        types.Tool(
            name="pw_to_typescript",
            description="Generate TypeScript code from PW MCP tree",
            inputSchema={
                "type": "object",
                "properties": {
                    "tree": {"type": "object", "description": "PW MCP tree"},
                },
                "required": ["tree"],
            },
        ),
        types.Tool(
            name="csharp_to_pw",
            description="Parse C# code into PW MCP tree",
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "C# source code"},
                },
                "required": ["code"],
            },
        ),
        types.Tool(
            name="pw_to_csharp",
            description="Generate C# code from PW MCP tree",
            inputSchema={
                "type": "object",
                "properties": {
                    "tree": {"type": "object", "description": "PW MCP tree"},
                },
                "required": ["tree"],
            },
        ),

        # ====================================================================
        # Atomic Syntax Tools (76 tools)
        # ====================================================================

        # Module-Level (2)
        types.Tool(
            name="pw_module",
            description="Define module/file structure",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "version": {"type": "string"},
                    "imports": {"type": "array", "items": {"type": "object"}},
                    "functions": {"type": "array", "items": {"type": "object"}},
                    "classes": {"type": "array", "items": {"type": "object"}},
                    "target_lang": {"type": "string", "enum": ["python", "go", "rust", "typescript", "csharp"]},
                },
                "required": ["name", "target_lang"],
            },
        ),
        types.Tool(
            name="pw_import",
            description="Import dependencies",
            inputSchema={
                "type": "object",
                "properties": {
                    "module": {"type": "string"},
                    "alias": {"type": "string"},
                    "items": {"type": "array", "items": {"type": "string"}},
                    "target_lang": {"type": "string", "enum": ["python", "go", "rust", "typescript", "csharp"]},
                },
                "required": ["module", "target_lang"],
            },
        ),

        # Functions (4)
        types.Tool(
            name="pw_function",
            description="Define function",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "params": {"type": "array", "items": {"type": "object"}},
                    "returns": {"type": "object"},
                    "body": {"type": "array", "items": {"type": "object"}},
                    "is_async": {"type": "boolean"},
                    "target_lang": {"type": "string", "enum": ["python", "go", "rust", "typescript", "csharp"]},
                },
                "required": ["name", "target_lang"],
            },
        ),
        types.Tool(
            name="pw_parameter",
            description="Function parameter",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "param_type": {"type": "object"},
                    "default": {"type": "object"},
                    "target_lang": {"type": "string", "enum": ["python", "go", "rust", "typescript", "csharp"]},
                },
                "required": ["name", "target_lang"],
            },
        ),
        types.Tool(
            name="pw_class",
            description="Define class/struct",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "properties": {"type": "array", "items": {"type": "object"}},
                    "methods": {"type": "array", "items": {"type": "object"}},
                    "target_lang": {"type": "string", "enum": ["python", "go", "rust", "typescript", "csharp"]},
                },
                "required": ["name", "target_lang"],
            },
        ),
        types.Tool(
            name="pw_property",
            description="Class property/field",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "prop_type": {"type": "object"},
                    "default": {"type": "object"},
                    "target_lang": {"type": "string", "enum": ["python", "go", "rust", "typescript", "csharp"]},
                },
                "required": ["name", "target_lang"],
            },
        ),

        # Control Flow (10)
        types.Tool(
            name="pw_if",
            description="If statement",
            inputSchema={
                "type": "object",
                "properties": {
                    "condition": {"type": "object"},
                    "then_body": {"type": "array", "items": {"type": "object"}},
                    "else_body": {"type": "array", "items": {"type": "object"}},
                    "target_lang": {"type": "string", "enum": ["python", "go", "rust", "typescript", "csharp"]},
                },
                "required": ["condition", "then_body", "target_lang"],
            },
        ),
        types.Tool(
            name="pw_for",
            description="For loop",
            inputSchema={
                "type": "object",
                "properties": {
                    "iterator": {"type": "string"},
                    "iterable": {"type": "object"},
                    "body": {"type": "array", "items": {"type": "object"}},
                    "target_lang": {"type": "string", "enum": ["python", "go", "rust", "typescript", "csharp"]},
                },
                "required": ["iterator", "iterable", "body", "target_lang"],
            },
        ),
        types.Tool(
            name="pw_while",
            description="While loop",
            inputSchema={
                "type": "object",
                "properties": {
                    "condition": {"type": "object"},
                    "body": {"type": "array", "items": {"type": "object"}},
                    "target_lang": {"type": "string", "enum": ["python", "go", "rust", "typescript", "csharp"]},
                },
                "required": ["condition", "body", "target_lang"],
            },
        ),
        types.Tool(
            name="pw_assignment",
            description="Variable assignment",
            inputSchema={
                "type": "object",
                "properties": {
                    "target": {"type": "string"},
                    "value": {"type": "object"},
                    "var_type": {"type": "object"},
                    "target_lang": {"type": "string", "enum": ["python", "go", "rust", "typescript", "csharp"]},
                },
                "required": ["target", "value", "target_lang"],
            },
        ),
        types.Tool(
            name="pw_return",
            description="Return statement",
            inputSchema={
                "type": "object",
                "properties": {
                    "value": {"type": "object"},
                    "target_lang": {"type": "string", "enum": ["python", "go", "rust", "typescript", "csharp"]},
                },
                "required": ["target_lang"],
            },
        ),
        types.Tool(
            name="pw_break",
            description="Break statement",
            inputSchema={
                "type": "object",
                "properties": {
                    "target_lang": {"type": "string", "enum": ["python", "go", "rust", "typescript", "csharp"]},
                },
                "required": ["target_lang"],
            },
        ),
        types.Tool(
            name="pw_continue",
            description="Continue statement",
            inputSchema={
                "type": "object",
                "properties": {
                    "target_lang": {"type": "string", "enum": ["python", "go", "rust", "typescript", "csharp"]},
                },
                "required": ["target_lang"],
            },
        ),
        types.Tool(
            name="pw_try",
            description="Try/except block",
            inputSchema={
                "type": "object",
                "properties": {
                    "body": {"type": "array", "items": {"type": "object"}},
                    "handlers": {"type": "array", "items": {"type": "object"}},
                    "finally_body": {"type": "array", "items": {"type": "object"}},
                    "target_lang": {"type": "string", "enum": ["python", "go", "rust", "typescript", "csharp"]},
                },
                "required": ["body", "target_lang"],
            },
        ),
        types.Tool(
            name="pw_catch",
            description="Exception handler",
            inputSchema={
                "type": "object",
                "properties": {
                    "exception_type": {"type": "string"},
                    "var_name": {"type": "string"},
                    "body": {"type": "array", "items": {"type": "object"}},
                    "target_lang": {"type": "string", "enum": ["python", "go", "rust", "typescript", "csharp"]},
                },
                "required": ["body", "target_lang"],
            },
        ),
        types.Tool(
            name="pw_throw",
            description="Throw/raise exception",
            inputSchema={
                "type": "object",
                "properties": {
                    "exception": {"type": "object"},
                    "target_lang": {"type": "string", "enum": ["python", "go", "rust", "typescript", "csharp"]},
                },
                "required": ["exception", "target_lang"],
            },
        ),
        types.Tool(
            name="pw_switch",
            description="Switch/match statement",
            inputSchema={
                "type": "object",
                "properties": {
                    "value": {"type": "object", "description": "Expression to match against"},
                    "cases": {"type": "array", "items": {"type": "object"}, "description": "Array of case clauses"},
                    "target_lang": {"type": "string", "enum": ["python", "go", "rust", "typescript", "csharp"]},
                },
                "required": ["value", "cases", "target_lang"],
            },
        ),
        types.Tool(
            name="pw_case",
            description="Case clause for switch/match",
            inputSchema={
                "type": "object",
                "properties": {
                    "values": {"type": "array", "items": {"type": "object"}, "description": "Values to match (empty for default)"},
                    "body": {"type": "array", "items": {"type": "object"}, "description": "Statements to execute"},
                    "is_default": {"type": "boolean", "description": "Whether this is the default case"},
                    "target_lang": {"type": "string", "enum": ["python", "go", "rust", "typescript", "csharp"]},
                },
                "required": ["body", "target_lang"],
            },
        ),

        # Expressions (14)
        types.Tool(
            name="pw_call",
            description="Function call",
            inputSchema={
                "type": "object",
                "properties": {
                    "function": {"type": "string"},
                    "args": {"type": "array", "items": {"type": "object"}},
                    "kwargs": {"type": "object"},
                    "target_lang": {"type": "string", "enum": ["python", "go", "rust", "typescript", "csharp"]},
                },
                "required": ["function", "target_lang"],
            },
        ),
        types.Tool(
            name="pw_binary_op",
            description="Binary operation (+, -, *, /, ==, !=, etc.)",
            inputSchema={
                "type": "object",
                "properties": {
                    "op": {"type": "string"},
                    "left": {"type": "object"},
                    "right": {"type": "object"},
                    "target_lang": {"type": "string", "enum": ["python", "go", "rust", "typescript", "csharp"]},
                },
                "required": ["op", "left", "right", "target_lang"],
            },
        ),
        types.Tool(
            name="pw_unary_op",
            description="Unary operation (not, -, +, ~)",
            inputSchema={
                "type": "object",
                "properties": {
                    "op": {"type": "string"},
                    "operand": {"type": "object"},
                    "target_lang": {"type": "string", "enum": ["python", "go", "rust", "typescript", "csharp"]},
                },
                "required": ["op", "operand", "target_lang"],
            },
        ),
        types.Tool(
            name="pw_literal",
            description="Literal value (string, int, float, bool, null)",
            inputSchema={
                "type": "object",
                "properties": {
                    "value": {},
                    "literal_type": {"type": "string", "enum": ["STRING", "INTEGER", "FLOAT", "BOOLEAN", "NULL"]},
                    "target_lang": {"type": "string", "enum": ["python", "go", "rust", "typescript", "csharp"]},
                },
                "required": ["value", "literal_type", "target_lang"],
            },
        ),
        types.Tool(
            name="pw_identifier",
            description="Variable reference",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "target_lang": {"type": "string", "enum": ["python", "go", "rust", "typescript", "csharp"]},
                },
                "required": ["name", "target_lang"],
            },
        ),
        types.Tool(
            name="pw_property_access",
            description="Object.property access",
            inputSchema={
                "type": "object",
                "properties": {
                    "object": {"type": "object"},
                    "property": {"type": "string"},
                    "target_lang": {"type": "string", "enum": ["python", "go", "rust", "typescript", "csharp"]},
                },
                "required": ["object", "property", "target_lang"],
            },
        ),
        types.Tool(
            name="pw_index",
            description="Array[index] access",
            inputSchema={
                "type": "object",
                "properties": {
                    "array": {"type": "object"},
                    "index": {"type": "object"},
                    "target_lang": {"type": "string", "enum": ["python", "go", "rust", "typescript", "csharp"]},
                },
                "required": ["array", "index", "target_lang"],
            },
        ),
        types.Tool(
            name="pw_array",
            description="Array literal [1, 2, 3]",
            inputSchema={
                "type": "object",
                "properties": {
                    "elements": {"type": "array", "items": {"type": "object"}},
                    "target_lang": {"type": "string", "enum": ["python", "go", "rust", "typescript", "csharp"]},
                },
                "required": ["elements", "target_lang"],
            },
        ),
        types.Tool(
            name="pw_map",
            description="Map/dict literal {key: value}",
            inputSchema={
                "type": "object",
                "properties": {
                    "pairs": {"type": "array", "items": {"type": "object"}},
                    "target_lang": {"type": "string", "enum": ["python", "go", "rust", "typescript", "csharp"]},
                },
                "required": ["pairs", "target_lang"],
            },
        ),
        types.Tool(
            name="pw_lambda",
            description="Lambda/anonymous function",
            inputSchema={
                "type": "object",
                "properties": {
                    "params": {"type": "array", "items": {"type": "string"}},
                    "body": {"type": "object"},
                    "target_lang": {"type": "string", "enum": ["python", "go", "rust", "typescript", "csharp"]},
                },
                "required": ["params", "body", "target_lang"],
            },
        ),
        types.Tool(
            name="pw_ternary",
            description="Ternary operator (condition ? true : false)",
            inputSchema={
                "type": "object",
                "properties": {
                    "condition": {"type": "object"},
                    "true_value": {"type": "object"},
                    "false_value": {"type": "object"},
                    "target_lang": {"type": "string", "enum": ["python", "go", "rust", "typescript", "csharp"]},
                },
                "required": ["condition", "true_value", "false_value", "target_lang"],
            },
        ),
        types.Tool(
            name="pw_comprehension",
            description="List/dict comprehension",
            inputSchema={
                "type": "object",
                "properties": {
                    "element": {"type": "object"},
                    "iterator": {"type": "string"},
                    "iterable": {"type": "object"},
                    "condition": {"type": "object"},
                    "is_dict": {"type": "boolean"},
                    "target_lang": {"type": "string", "enum": ["python", "go", "rust", "typescript", "csharp"]},
                },
                "required": ["element", "iterator", "iterable", "target_lang"],
            },
        ),
        types.Tool(
            name="pw_fstring",
            description="F-string/template literal",
            inputSchema={
                "type": "object",
                "properties": {
                    "parts": {"type": "array"},
                    "target_lang": {"type": "string", "enum": ["python", "go", "rust", "typescript", "csharp"]},
                },
                "required": ["parts", "target_lang"],
            },
        ),
        types.Tool(
            name="pw_slice",
            description="Array slice [start:end]",
            inputSchema={
                "type": "object",
                "properties": {
                    "array": {"type": "object"},
                    "start": {"type": "object"},
                    "end": {"type": "object"},
                    "step": {"type": "object"},
                    "target_lang": {"type": "string", "enum": ["python", "go", "rust", "typescript", "csharp"]},
                },
                "required": ["array", "target_lang"],
            },
        ),
    ]

    return tools


@app.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """
    Handle MCP tool calls.
    """
    if not arguments:
        arguments = {}

    # ========================================================================
    # High-Level Translation
    # ========================================================================

    if name == "translate_code":
        code = arguments.get("code", "")
        from_lang = arguments.get("from_lang", "").lower()
        to_lang = arguments.get("to_lang", "").lower()

        try:
            # Step 1: Source → PW
            if from_lang == "python":
                pw_tree = python_to_pw(code)
            elif from_lang == "go":
                pw_tree = go_to_pw(code)
            elif from_lang == "rust":
                pw_tree = rust_to_pw(code)
            elif from_lang == "typescript":
                pw_tree = typescript_to_pw(code)
            elif from_lang == "csharp" or from_lang == "c#":
                pw_tree = csharp_to_pw(code)
            else:
                return [types.TextContent(
                    type="text",
                    text=f"❌ Unsupported source language: {from_lang}. Supported: python, go, rust, typescript, csharp"
                )]

            # Step 2: PW → Target
            if to_lang == "python":
                result_code = pw_to_python(pw_tree)
            elif to_lang == "go":
                result_code = pw_to_go(pw_tree)
            elif to_lang == "rust":
                result_code = pw_to_rust(pw_tree)
            elif to_lang == "typescript":
                result_code = pw_to_typescript(pw_tree)
            elif to_lang == "csharp" or to_lang == "c#":
                result_code = pw_to_csharp(pw_tree)
            else:
                return [types.TextContent(
                    type="text",
                    text=f"❌ Unsupported target language: {to_lang}. Supported: python, go, rust, typescript, csharp"
                )]

            return [types.TextContent(
                type="text",
                text=f"✅ Translated {from_lang} → {to_lang}:\n\n```{to_lang}\n{result_code}\n```"
            )]

        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"❌ Translation error: {str(e)}"
            )]

    # ========================================================================
    # Language → PW Parsers
    # ========================================================================

    elif name == "python_to_pw":
        code = arguments.get("code", "")
        try:
            pw_tree = python_to_pw(code)
            import json
            return [types.TextContent(
                type="text",
                text=f"✅ Python → PW tree:\n\n```json\n{json.dumps(pw_tree, indent=2)}\n```"
            )]
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"❌ Parse error: {str(e)}"
            )]

    elif name == "go_to_pw":
        code = arguments.get("code", "")
        try:
            pw_tree = go_to_pw(code)
            import json
            return [types.TextContent(
                type="text",
                text=f"✅ Go → PW tree:\n\n```json\n{json.dumps(pw_tree, indent=2)}\n```"
            )]
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"❌ Parse error: {str(e)}"
            )]

    elif name == "rust_to_pw":
        code = arguments.get("code", "")
        try:
            pw_tree = rust_to_pw(code)
            import json
            return [types.TextContent(
                type="text",
                text=f"✅ Rust → PW tree:\n\n```json\n{json.dumps(pw_tree, indent=2)}\n```"
            )]
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"❌ Parse error: {str(e)}"
            )]

    elif name == "typescript_to_pw":
        code = arguments.get("code", "")
        try:
            pw_tree = typescript_to_pw(code)
            import json
            return [types.TextContent(
                type="text",
                text=f"✅ TypeScript → PW tree:\n\n```json\n{json.dumps(pw_tree, indent=2)}\n```"
            )]
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"❌ Parse error: {str(e)}"
            )]

    elif name == "csharp_to_pw":
        code = arguments.get("code", "")
        try:
            pw_tree = csharp_to_pw(code)
            import json
            return [types.TextContent(
                type="text",
                text=f"✅ C# → PW tree:\n\n```json\n{json.dumps(pw_tree, indent=2)}\n```"
            )]
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"❌ Parse error: {str(e)}"
            )]

    # ========================================================================
    # PW → Language Generators
    # ========================================================================

    elif name == "pw_to_python":
        tree = arguments.get("tree", {})
        try:
            python_code = pw_to_python(tree)
            return [types.TextContent(
                type="text",
                text=f"✅ PW → Python:\n\n```python\n{python_code}\n```"
            )]
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"❌ Generation error: {str(e)}"
            )]

    elif name == "pw_to_go":
        tree = arguments.get("tree", {})
        try:
            go_code = pw_to_go(tree)
            return [types.TextContent(
                type="text",
                text=f"✅ PW → Go:\n\n```go\n{go_code}\n```"
            )]
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"❌ Generation error: {str(e)}"
            )]

    elif name == "pw_to_rust":
        tree = arguments.get("tree", {})
        try:
            rust_code = pw_to_rust(tree)
            return [types.TextContent(
                type="text",
                text=f"✅ PW → Rust:\n\n```rust\n{rust_code}\n```"
            )]
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"❌ Generation error: {str(e)}"
            )]

    elif name == "pw_to_typescript":
        tree = arguments.get("tree", {})
        try:
            typescript_code = pw_to_typescript(tree)
            return [types.TextContent(
                type="text",
                text=f"✅ PW → TypeScript:\n\n```typescript\n{typescript_code}\n```"
            )]
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"❌ Generation error: {str(e)}"
            )]

    elif name == "pw_to_csharp":
        tree = arguments.get("tree", {})
        try:
            csharp_code = pw_to_csharp(tree)
            return [types.TextContent(
                type="text",
                text=f"✅ PW → C#:\n\n```csharp\n{csharp_code}\n```"
            )]
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"❌ Generation error: {str(e)}"
            )]

    # ========================================================================
    # Atomic Syntax Tools
    # ========================================================================

    elif name.startswith("pw_"):
        # All atomic syntax tools follow the same pattern:
        # 1. Extract target_lang from arguments
        # 2. Convert arguments to IR node via mcp_to_ir
        # 3. Generate code in target language

        target_lang = arguments.get("target_lang", "python").lower()

        try:
            # Create MCP tree from tool call
            mcp_tree = {
                "tool": name,
                "params": {k: v for k, v in arguments.items() if k != "target_lang"}
            }

            # Convert to IR
            ir_node = mcp_to_ir(mcp_tree)

            # Generate code in target language
            if target_lang == "python":
                from language.python_generator_v2 import PythonGeneratorV2
                generator = PythonGeneratorV2()
                code = generator._generate_node(ir_node)
            elif target_lang == "go":
                from language.go_generator_v2 import GoGeneratorV2
                generator = GoGeneratorV2()
                code = generator._generate_node(ir_node)
            elif target_lang == "rust":
                from language.rust_generator_v2 import RustGeneratorV2
                generator = RustGeneratorV2()
                code = generator._generate_node(ir_node)
            elif target_lang == "typescript":
                from language.nodejs_generator_v2 import NodeJSGeneratorV2
                generator = NodeJSGeneratorV2()
                code = generator._generate_node(ir_node)
            elif target_lang == "csharp" or target_lang == "c#":
                from language.dotnet_generator_v2 import DotNetGeneratorV2
                generator = DotNetGeneratorV2()
                code = generator._generate_node(ir_node)
            else:
                return [types.TextContent(
                    type="text",
                    text=f"❌ Unsupported target language: {target_lang}. Supported: python, go, rust, typescript, csharp"
                )]

            return [types.TextContent(
                type="text",
                text=f"✅ Generated {target_lang} code from {name}:\n\n```{target_lang}\n{code}\n```"
            )]

        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"❌ Error generating code from {name}: {str(e)}"
            )]

    # ========================================================================
    # Unknown Tool
    # ========================================================================

    else:
        return [types.TextContent(
            type="text",
            text=f"❌ Unknown tool: {name}"
        )]


# ============================================================================
# Server Entry Point
# ============================================================================

async def main():
    """Run the MCP server."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="pw-syntax",
                server_version="0.1.0",
                capabilities=app.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
