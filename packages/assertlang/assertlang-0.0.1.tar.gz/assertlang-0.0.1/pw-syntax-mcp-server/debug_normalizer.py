#!/usr/bin/env python3
"""Debug the normalizer to see what's happening."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from translators.python_bridge import python_to_pw, pw_to_python
from translators.go_bridge import pw_to_go, go_to_pw
from translators.ir_converter import mcp_to_ir
import json

# Test case
original = '''
def greet(name):
    message = "Hello, " + name
    return message
'''

print("Original Python:")
print(original)
print()

# Step 1: Python → PW
pw1 = python_to_pw(original)
print("Step 1: Python → PW MCP tree")
print(json.dumps(pw1, indent=2)[:500] + "...")
print()

# Step 2: PW → Go
go_code = pw_to_go(pw1)
print("Step 2: PW → Go code:")
print(go_code)
print()

# Step 3: Go → PW
pw2 = go_to_pw(go_code)
print("Step 3: Go → PW MCP tree")
print(json.dumps(pw2, indent=2)[:500] + "...")
print()

# Step 4: Check the IR before Python generation
ir = mcp_to_ir(pw2)
print("Step 4: IR Module structure:")
print(f"  Module name: {ir.name}")
print(f"  Functions: {len(ir.functions)}")
print(f"  Module vars: {len(ir.module_vars) if ir.module_vars else 0}")
print(f"  Imports: {len(ir.imports)}")

if ir.module_vars:
    print("\n  Module vars found:")
    for var in ir.module_vars:
        print(f"    - {var}")

if ir.functions:
    func = ir.functions[0]
    print(f"\n  First function: {func.name}")
    print(f"    Params: {len(func.params)}")
    print(f"    Body statements: {len(func.body)}")
    for i, stmt in enumerate(func.body):
        print(f"      {i}: {type(stmt).__name__}")

print()

# Step 5: Generate Python
final = pw_to_python(pw2)
print("Step 5: Generated Python:")
print(final)
