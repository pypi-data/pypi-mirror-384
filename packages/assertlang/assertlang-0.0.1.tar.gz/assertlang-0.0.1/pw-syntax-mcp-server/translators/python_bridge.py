#!/usr/bin/env python3
"""
Python ⟷ PW Bridge

Translates between Python code and PW MCP trees.
"""

import sys
from pathlib import Path
from typing import Dict

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from language.python_parser_v2 import PythonParserV2
from language.python_generator_v2 import PythonGeneratorV2
from translators.ir_converter import ir_to_mcp, mcp_to_ir
from translators.semantic_normalizer import normalize_ir, denormalize_ir


def python_to_pw(python_code: str) -> Dict:
    """
    Parse Python code → PW MCP tree.

    Pipeline:
    1. Python AST → IR (language-specific)
    2. Normalize: Strip Python idioms → Pure PW IR
    3. Pure PW IR → MCP tree (universal format)

    Args:
        python_code: Python source code string

    Returns:
        PW MCP tree (JSON-serializable dict)
    """
    # Parse Python → IR
    parser = PythonParserV2()
    ir_module = parser.parse_source(python_code)

    # Normalize: Strip Python-specific patterns → Pure PW
    normalized_ir = normalize_ir(ir_module, source_lang="python")

    # Convert IR → MCP tree
    mcp_tree = ir_to_mcp(normalized_ir)

    return mcp_tree


def pw_to_python(pw_tree: Dict) -> str:
    """
    Generate Python code from PW MCP tree.

    Pipeline:
    1. MCP tree (universal) → Pure PW IR
    2. Denormalize: Apply Python idioms to Pure PW IR
    3. Python-specific IR → Python code

    Args:
        pw_tree: PW MCP tree (JSON dict)

    Returns:
        Python source code string
    """
    # Convert MCP tree → IR
    ir_module = mcp_to_ir(pw_tree)

    # Denormalize: Apply Python-specific patterns to Pure PW
    denormalized_ir = denormalize_ir(ir_module, target_lang="python")

    # Generate Python from IR
    generator = PythonGeneratorV2()
    python_code = generator.generate(denormalized_ir)

    return python_code


# Test if run directly
if __name__ == "__main__":
    # Test Python → PW → Python roundtrip
    test_code = """
def calculate(x, y):
    result = x + y
    return result * 2
"""

    print("Original Python:")
    print(test_code)

    # Python → PW
    pw_tree = python_to_pw(test_code)
    print("\nPW MCP Tree:")
    import json
    print(json.dumps(pw_tree, indent=2)[:500] + "...")

    # PW → Python
    python_code = pw_to_python(pw_tree)
    print("\nGenerated Python:")
    print(python_code)

    print("\n✅ Python bridge working!")
