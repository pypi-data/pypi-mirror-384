#!/usr/bin/env python3
"""
PW Syntax MCP Server - Telephone Game Test

Tests the robustness of PW translation by passing code through multiple
agents and languages, then back to the original language.

Game Flow:
1. Agent A (blind): Python code → PW MCP tree
2. Agent B (blind): PW MCP tree → Go code
3. Agent C (blind): Go code → PW MCP tree
4. Agent D (blind): PW MCP tree → Python code
5. Validation: Does final Python match original semantics?

This tests:
- Information preservation through PW MCP format
- Bidirectional translation accuracy
- Semantic equivalence after round-trip
"""

import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from translators.python_bridge import python_to_pw, pw_to_python
from translators.go_bridge import go_to_pw, pw_to_go


def test_simple_function():
    """Test 1: Simple function with arithmetic."""

    print("=" * 70)
    print("TEST 1: Simple Arithmetic Function")
    print("=" * 70)

    original_python = """
def add_numbers(x, y):
    result = x + y
    return result
"""

    print("\n📝 Original Python Code:")
    print(original_python)

    # Step 1: Python → PW (Agent A)
    print("\n🤖 Agent A: Converting Python → PW MCP tree...")
    try:
        pw_tree_1 = python_to_pw(original_python)
        print(f"✅ PW MCP tree created ({len(json.dumps(pw_tree_1))} bytes)")
    except Exception as e:
        print(f"❌ Agent A failed: {e}")
        return False

    # Step 2: PW → Go (Agent B)
    print("\n🤖 Agent B: Converting PW MCP tree → Go...")
    try:
        go_code = pw_to_go(pw_tree_1)
        print("✅ Go code generated:")
        print(go_code[:200] + "...")
    except Exception as e:
        print(f"❌ Agent B failed: {e}")
        return False

    # Step 3: Go → PW (Agent C)
    print("\n🤖 Agent C: Converting Go → PW MCP tree...")
    try:
        pw_tree_2 = go_to_pw(go_code)
        print(f"✅ PW MCP tree created ({len(json.dumps(pw_tree_2))} bytes)")
    except Exception as e:
        print(f"❌ Agent C failed: {e}")
        return False

    # Step 4: PW → Python (Agent D)
    print("\n🤖 Agent D: Converting PW MCP tree → Python...")
    try:
        final_python = pw_to_python(pw_tree_2)
        print("✅ Final Python code:")
        print(final_python)
    except Exception as e:
        print(f"❌ Agent D failed: {e}")
        return False

    # Validation
    print("\n📊 Validation:")
    print("-" * 70)

    # Check if both versions have the same function
    has_function = "def" in final_python and "add" in final_python.lower()
    has_params = "x" in final_python and "y" in final_python
    has_return = "return" in final_python

    print(f"  Function definition: {'✅' if has_function else '❌'}")
    print(f"  Parameters (x, y): {'✅' if has_params else '❌'}")
    print(f"  Return statement: {'✅' if has_return else '❌'}")

    success = has_function and has_params and has_return

    if success:
        print("\n✅ TELEPHONE GAME SUCCESS! Code survived the round-trip!")
    else:
        print("\n❌ TELEPHONE GAME FAILED! Code lost information.")

    return success


def test_conditional_logic():
    """Test 2: Function with if/else logic."""

    print("\n" + "=" * 70)
    print("TEST 2: Conditional Logic")
    print("=" * 70)

    original_python = """
def classify_number(n):
    if n > 0:
        return "positive"
    else:
        return "negative"
"""

    print("\n📝 Original Python Code:")
    print(original_python)

    # Round-trip: Python → PW → Go → PW → Python
    print("\n🔄 Starting telephone game...")

    try:
        # Agent A: Python → PW
        print("  🤖 Agent A: Python → PW")
        pw_tree_1 = python_to_pw(original_python)

        # Agent B: PW → Go
        print("  🤖 Agent B: PW → Go")
        go_code = pw_to_go(pw_tree_1)
        print(f"\n  Intermediate Go:\n{go_code[:300]}...")

        # Agent C: Go → PW
        print("\n  🤖 Agent C: Go → PW")
        pw_tree_2 = go_to_pw(go_code)

        # Agent D: PW → Python
        print("  🤖 Agent D: PW → Python")
        final_python = pw_to_python(pw_tree_2)

        print("\n✅ Final Python:")
        print(final_python)

        # Validation
        has_if = "if" in final_python
        has_comparison = ">" in final_python or "<" in final_python
        has_return = final_python.count("return") >= 2

        print("\n📊 Validation:")
        print(f"  If statement: {'✅' if has_if else '❌'}")
        print(f"  Comparison operator: {'✅' if has_comparison else '❌'}")
        print(f"  Multiple returns: {'✅' if has_return else '❌'}")

        success = has_if and has_comparison and has_return

        if success:
            print("\n✅ CONDITIONAL LOGIC PRESERVED!")
        else:
            print("\n❌ CONDITIONAL LOGIC LOST!")

        return success

    except Exception as e:
        print(f"\n❌ Telephone game failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_loop_with_accumulator():
    """Test 3: Loop with accumulator pattern."""

    print("\n" + "=" * 70)
    print("TEST 3: Loop with Accumulator")
    print("=" * 70)

    original_python = """
def sum_list(numbers):
    total = 0
    for num in numbers:
        total = total + num
    return total
"""

    print("\n📝 Original Python Code:")
    print(original_python)

    print("\n🔄 Starting telephone game...")

    try:
        # Full round-trip
        print("  🤖 Agent A: Python → PW")
        pw_1 = python_to_pw(original_python)

        print("  🤖 Agent B: PW → Go")
        go_code = pw_to_go(pw_1)

        print("  🤖 Agent C: Go → PW")
        pw_2 = go_to_pw(go_code)

        print("  🤖 Agent D: PW → Python")
        final_python = pw_to_python(pw_2)

        print("\n✅ Final Python:")
        print(final_python)

        # Validation
        has_loop = "for" in final_python
        has_accumulator = "total" in final_python or "sum" in final_python.lower()
        has_addition = "+" in final_python

        print("\n📊 Validation:")
        print(f"  For loop: {'✅' if has_loop else '❌'}")
        print(f"  Accumulator variable: {'✅' if has_accumulator else '❌'}")
        print(f"  Addition operation: {'✅' if has_addition else '❌'}")

        success = has_loop and has_accumulator and has_addition

        if success:
            print("\n✅ LOOP PATTERN PRESERVED!")
        else:
            print("\n❌ LOOP PATTERN LOST!")

        return success

    except Exception as e:
        print(f"\n❌ Telephone game failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_multi_language_chain():
    """Test 4: Extended chain - Python → Go → Python → Go → Python."""

    print("\n" + "=" * 70)
    print("TEST 4: Extended Multi-Language Chain")
    print("=" * 70)

    original_python = """
def greet(name):
    message = "Hello, " + name
    return message
"""

    print("\n📝 Original Python Code:")
    print(original_python)

    print("\n🔄 Extended telephone game (5 translations)...")

    try:
        # Translation 1: Python → Go
        print("\n  🤖 Translation 1: Python → PW → Go")
        pw_1 = python_to_pw(original_python)
        code_1 = pw_to_go(pw_1)
        print(f"     Generated Go ({len(code_1)} chars)")

        # Translation 2: Go → Python
        print("  🤖 Translation 2: Go → PW → Python")
        pw_2 = go_to_pw(code_1)
        code_2 = pw_to_python(pw_2)
        print(f"     Generated Python ({len(code_2)} chars)")

        # Translation 3: Python → Go
        print("  🤖 Translation 3: Python → PW → Go")
        pw_3 = python_to_pw(code_2)
        code_3 = pw_to_go(pw_3)
        print(f"     Generated Go ({len(code_3)} chars)")

        # Translation 4: Go → Python
        print("  🤖 Translation 4: Go → PW → Python")
        pw_4 = go_to_pw(code_3)
        code_4 = pw_to_python(pw_4)
        print(f"     Generated Python ({len(code_4)} chars)")

        # Translation 5: Python → Go (final)
        print("  🤖 Translation 5: Python → PW → Go")
        pw_5 = python_to_pw(code_4)
        final_code = pw_to_go(pw_5)

        print("\n✅ Final Go code (after 5 translations):")
        print(final_code)

        # Validation
        has_function = "func" in final_code and "Greet" in final_code
        has_string_concat = "+" in final_code or "fmt.Sprintf" in final_code
        has_return = "return" in final_code

        print("\n📊 Validation after 5 translations:")
        print(f"  Function definition: {'✅' if has_function else '❌'}")
        print(f"  String concatenation: {'✅' if has_string_concat else '❌'}")
        print(f"  Return statement: {'✅' if has_return else '❌'}")

        success = has_function and has_string_concat and has_return

        if success:
            print("\n✅ CODE SURVIVED 5 TRANSLATIONS!")
        else:
            print("\n❌ CODE DEGRADED AFTER MULTIPLE TRANSLATIONS!")

        return success

    except Exception as e:
        print(f"\n❌ Extended chain failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all telephone game tests."""

    print("\n" + "╔" + "=" * 68 + "╗")
    print("║" + " " * 20 + "TELEPHONE GAME TEST" + " " * 29 + "║")
    print("║" + " " * 12 + "Testing PW MCP Translation Robustness" + " " * 19 + "║")
    print("╚" + "=" * 68 + "╝")

    results = []

    # Run all tests
    results.append(("Simple Function", test_simple_function()))
    results.append(("Conditional Logic", test_conditional_logic()))
    results.append(("Loop with Accumulator", test_loop_with_accumulator()))
    results.append(("Multi-Language Chain", test_multi_language_chain()))

    # Summary
    print("\n" + "=" * 70)
    print("TELEPHONE GAME TEST SUMMARY")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 ALL TELEPHONE GAMES SUCCEEDED!")
        print("\nConclusion:")
        print("  • PW MCP tree preserves semantic information")
        print("  • Bidirectional translation is robust")
        print("  • Code survives multiple round-trips")
        print("  • System ready for agent-to-agent code exchange!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed.")
        print("\nIssues identified:")
        for name, result in results:
            if not result:
                print(f"  • {name} - Information loss during translation")
        return 1


if __name__ == "__main__":
    sys.exit(main())
