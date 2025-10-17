#!/usr/bin/env python3
"""
Test PW Syntax MCP Server

Validates all translation bridges and atomic syntax tools.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from translators.python_bridge import python_to_pw, pw_to_python
from translators.go_bridge import go_to_pw, pw_to_go
from translators.ir_converter import ir_to_mcp, mcp_to_ir


def test_python_bridge():
    """Test Python ⟷ PW translation."""
    print("=" * 60)
    print("TEST: Python Bridge")
    print("=" * 60)

    python_code = """
def calculate(x, y):
    result = x + y
    return result * 2
"""

    print("\n1. Python → PW")
    print(f"Original Python:\n{python_code}")

    try:
        pw_tree = python_to_pw(python_code)
        print(f"✅ Parsed to PW tree ({len(str(pw_tree))} chars)")

        print("\n2. PW → Python")
        python_code_generated = pw_to_python(pw_tree)
        print(f"Generated Python:\n{python_code_generated}")
        print("✅ Python bridge working!")
        return True

    except Exception as e:
        print(f"❌ Python bridge error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_go_bridge():
    """Test Go ⟷ PW translation."""
    print("\n" + "=" * 60)
    print("TEST: Go Bridge")
    print("=" * 60)

    go_code = """
package main

func Calculate(x int, y int) int {
    result := x + y
    return result * 2
}
"""

    print("\n1. Go → PW")
    print(f"Original Go:\n{go_code}")

    try:
        pw_tree = go_to_pw(go_code)
        print(f"✅ Parsed to PW tree ({len(str(pw_tree))} chars)")

        print("\n2. PW → Go")
        go_code_generated = pw_to_go(pw_tree)
        print(f"Generated Go:\n{go_code_generated}")
        print("✅ Go bridge working!")
        return True

    except Exception as e:
        print(f"❌ Go bridge error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_cross_language():
    """Test Python → PW → Go translation."""
    print("\n" + "=" * 60)
    print("TEST: Cross-Language Translation (Python → Go)")
    print("=" * 60)

    python_code = """
def add(a, b):
    return a + b
"""

    print(f"\nOriginal Python:\n{python_code}")

    try:
        # Python → PW
        print("\n1. Python → PW tree")
        pw_tree = python_to_pw(python_code)
        print(f"✅ Parsed to PW tree")

        # PW → Go
        print("\n2. PW tree → Go")
        go_code = pw_to_go(pw_tree)
        print(f"Generated Go:\n{go_code}")
        print("✅ Cross-language translation working!")
        return True

    except Exception as e:
        print(f"❌ Cross-language error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ir_converter():
    """Test IR ⟷ MCP tree converter."""
    print("\n" + "=" * 60)
    print("TEST: IR ⟷ MCP Converter")
    print("=" * 60)

    from dsl.ir import IRFunction, IRParameter, IRType, IRReturn, IRBinaryOp, IRIdentifier

    # Create simple IR function
    ir_func = IRFunction(
        name="test_func",
        params=[
            IRParameter(name="x", param_type=IRType(name="int")),
            IRParameter(name="y", param_type=IRType(name="int"))
        ],
        body=[
            IRReturn(
                value=IRBinaryOp(
                    op="+",  # Use string operator
                    left=IRIdentifier(name="x"),
                    right=IRIdentifier(name="y")
                )
            )
        ],
        return_type=IRType(name="int"),  # Changed from 'returns' to 'return_type'
        is_async=False
    )

    print("\n1. IR → MCP tree")
    try:
        mcp_tree = ir_to_mcp(ir_func)
        print(f"✅ Converted to MCP tree")
        print(f"Tool: {mcp_tree.get('tool')}")

        print("\n2. MCP tree → IR")
        ir_restored = mcp_to_ir(mcp_tree)
        print(f"✅ Restored IR node")
        print(f"Type: {type(ir_restored).__name__}")
        print(f"Name: {ir_restored.name}")
        print("✅ IR converter working!")
        return True

    except Exception as e:
        print(f"❌ IR converter error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_atomic_tool_simulation():
    """Simulate atomic syntax tool usage."""
    print("\n" + "=" * 60)
    print("TEST: Atomic Syntax Tool Simulation")
    print("=" * 60)

    print("\nTesting atomic tool pattern:")
    print("1. MCP tool call → IR node → Code generation")

    try:
        # Simulate an atomic tool call like "pw_if"
        mcp_call = {
            "tool": "pw_if",
            "params": {
                "condition": {
                    "tool": "pw_binary_op",
                    "params": {
                        "op": ">",
                        "left": {"tool": "pw_identifier", "params": {"name": "x"}},
                        "right": {"tool": "pw_literal", "params": {"value": 0, "literal_type": "INTEGER"}}
                    }
                },
                "then_body": [
                    {
                        "tool": "pw_return",
                        "params": {
                            "value": {"tool": "pw_literal", "params": {"value": True, "literal_type": "BOOLEAN"}}
                        }
                    }
                ],
                "else_body": [
                    {
                        "tool": "pw_return",
                        "params": {
                            "value": {"tool": "pw_literal", "params": {"value": False, "literal_type": "BOOLEAN"}}
                        }
                    }
                ]
            }
        }

        print("\n  MCP tool call (pw_if):")
        print(f"    Condition: x > 0")
        print(f"    Then: return True")
        print(f"    Else: return False")

        # Convert MCP → IR
        ir_node = mcp_to_ir(mcp_call)
        print(f"\n  ✅ Converted to IR node: {type(ir_node).__name__}")

        # Generate Python code
        from language.python_generator_v2 import PythonGeneratorV2
        gen_py = PythonGeneratorV2()
        python_code = gen_py.generate_if(ir_node)
        print(f"\n  Python output:\n{python_code}")

        print("\n✅ Atomic tool simulation working!")
        return True

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("PW SYNTAX MCP SERVER - TEST SUITE")
    print("=" * 60)

    results = []

    # Test each component
    results.append(("Python Bridge", test_python_bridge()))
    results.append(("Go Bridge", test_go_bridge()))
    results.append(("Cross-Language", test_cross_language()))
    results.append(("IR Converter", test_ir_converter()))
    results.append(("Atomic Tools", test_atomic_tool_simulation()))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED! PW Syntax MCP Server is ready!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Review errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
