#!/usr/bin/env python3
"""
PW Syntax MCP Server - Usage Demo

Shows how agents can exchange code via PW MCP trees.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from translators.python_bridge import python_to_pw, pw_to_python
from translators.go_bridge import go_to_pw, pw_to_go
import json


def demo_agent_communication():
    """
    Demonstrate two agents exchanging code via PW.

    Scenario:
    - Agent A (Python developer) writes a function
    - Agent B (Go developer) needs the same logic
    - They exchange PW MCP tree instead of source code
    """

    print("=" * 70)
    print(" DEMO: Agent-to-Agent Code Exchange via PW MCP")
    print("=" * 70)

    # Agent A: Python developer
    print("\n🤖 Agent A (Python Developer):")
    print("-" * 70)

    python_code = """
def calculate_discount(price, discount_percent):
    discount = price * (discount_percent / 100)
    final_price = price - discount
    return final_price
"""

    print("Writes Python function:")
    print(python_code)

    # Agent A converts to PW MCP tree
    print("Converting to PW MCP tree...")
    pw_tree = python_to_pw(python_code)
    print(f"✅ Created PW MCP tree ({len(json.dumps(pw_tree))} bytes)")

    # Agent A sends pw_tree to Agent B (via any transport - HTTP, message queue, etc.)
    print("\n📤 Sending PW MCP tree to Agent B...")

    # Agent B: Go developer
    print("\n🤖 Agent B (Go Developer):")
    print("-" * 70)
    print("📥 Received PW MCP tree")

    # Agent B converts to Go
    print("Generating Go code from PW MCP tree...")
    go_code = pw_to_go(pw_tree)

    print("\nGenerated Go function:")
    print(go_code)

    print("\n✅ Success! Agent B now has equivalent Go code.")
    print("\nKey Benefits:")
    print("  • No manual translation needed")
    print("  • Language-agnostic exchange format")
    print("  • Type information preserved")
    print("  • Logic semantically equivalent")


def demo_atomic_tools():
    """
    Demonstrate composing code with atomic MCP tools.
    """

    print("\n" + "=" * 70)
    print(" DEMO: Building Code with Atomic MCP Tools")
    print("=" * 70)

    from translators.ir_converter import mcp_to_ir
    from language.python_generator_v2 import PythonGeneratorV2

    print("\n🔨 Composing an IF statement using atomic tools:")
    print("-" * 70)

    # Build IF statement: if x > 10: return "big" else: return "small"
    mcp_if = {
        "tool": "pw_if",
        "params": {
            "condition": {
                "tool": "pw_binary_op",
                "params": {
                    "op": ">",
                    "left": {"tool": "pw_identifier", "params": {"name": "x"}},
                    "right": {"tool": "pw_literal", "params": {"value": 10, "literal_type": "INTEGER"}}
                }
            },
            "then_body": [
                {
                    "tool": "pw_return",
                    "params": {
                        "value": {"tool": "pw_literal", "params": {"value": "big", "literal_type": "STRING"}}
                    }
                }
            ],
            "else_body": [
                {
                    "tool": "pw_return",
                    "params": {
                        "value": {"tool": "pw_literal", "params": {"value": "small", "literal_type": "STRING"}}
                    }
                }
            ]
        }
    }

    print("Tools used:")
    print("  • pw_if (if statement)")
    print("  • pw_binary_op (comparison)")
    print("  • pw_identifier (variable reference)")
    print("  • pw_literal (literal values)")
    print("  • pw_return (return statement)")

    # Convert to IR and generate Python
    ir_node = mcp_to_ir(mcp_if)
    gen = PythonGeneratorV2()
    python_code = gen.generate_if(ir_node)

    print("\nGenerated Python code:")
    print(python_code)

    print("\n✅ Code built from atomic MCP tool calls!")


def demo_translation_pipeline():
    """
    Demonstrate the full translation pipeline.
    """

    print("\n" + "=" * 70)
    print(" DEMO: Full Translation Pipeline")
    print("=" * 70)

    print("\n📊 Pipeline: Python → IR → PW MCP → IR → Go")
    print("-" * 70)

    python_code = """
def greet(name):
    message = "Hello, " + name + "!"
    return message
"""

    print("\n1️⃣  Input Python:")
    print(python_code)

    print("2️⃣  Parse Python → IR → PW MCP tree")
    pw_tree = python_to_pw(python_code)
    print(f"   ✅ PW MCP tree created")

    print("\n3️⃣  Convert PW MCP tree → IR → Go")
    go_code = pw_to_go(pw_tree)
    print(f"   ✅ Go code generated")

    print("\n4️⃣  Output Go:")
    print(go_code)

    print("\n✅ Full pipeline complete!")
    print("\nPipeline stages:")
    print("  1. Python AST → Promptware IR")
    print("  2. IR → PW MCP Tree (JSON)")
    print("  3. PW MCP Tree → IR")
    print("  4. IR → Go AST → Go Code")


def main():
    """Run all demos."""

    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "PW SYNTAX MCP SERVER - DEMO" + " " * 25 + "║")
    print("║" + " " * 12 + "Universal Code Translation via MCP" + " " * 22 + "║")
    print("╚" + "=" * 68 + "╝")

    # Demo 1: Agent communication
    demo_agent_communication()

    # Demo 2: Atomic tools
    demo_atomic_tools()

    # Demo 3: Translation pipeline
    demo_translation_pipeline()

    print("\n" + "=" * 70)
    print(" 🎉 All demos complete!")
    print("=" * 70)
    print("\nNext steps:")
    print("  • Run 'python3 server.py' to start the MCP server")
    print("  • Connect from Claude Desktop or any MCP client")
    print("  • Use tools: translate_code, python_to_pw, pw_to_go, etc.")
    print("  • Build code with 30+ atomic syntax tools (pw_if, pw_for, etc.)")
    print("\n")


if __name__ == "__main__":
    main()
