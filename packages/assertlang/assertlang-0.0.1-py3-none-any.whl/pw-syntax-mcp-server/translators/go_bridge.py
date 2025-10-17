#!/usr/bin/env python3
"""
Go ⟷ PW Bridge

Translates between Go code and PW MCP trees.
"""

import sys
from pathlib import Path
from typing import Dict

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from language.go_parser_v3 import GoParserV3
from language.go_generator_v2 import GoGeneratorV2
from translators.ir_converter import ir_to_mcp, mcp_to_ir
from translators.semantic_normalizer import normalize_ir, denormalize_ir
import tempfile


def go_to_pw(go_code: str) -> Dict:
    """
    Parse Go code → PW MCP tree.

    Pipeline:
    1. Go AST → IR (language-specific, has Go idioms) - using V3 parser (95% accuracy)
    2. Normalize: Strip Go idioms (error returns, stdlib) → Pure PW IR
    3. Pure PW IR → MCP tree (universal format)

    Args:
        go_code: Go source code string

    Returns:
        PW MCP tree (JSON-serializable dict)
    """
    # Parse Go → IR using V3 parser (needs file path)
    parser = GoParserV3()

    # Write to temp file for V3 parser
    with tempfile.NamedTemporaryFile(mode='w', suffix='.go', delete=False) as f:
        f.write(go_code)
        temp_path = f.name

    try:
        ir_module = parser.parse_file(temp_path)
    finally:
        import os
        os.unlink(temp_path)

    # Normalize: Strip Go-specific patterns → Pure PW
    normalized_ir = normalize_ir(ir_module, source_lang="go")

    # Convert IR → MCP tree
    mcp_tree = ir_to_mcp(normalized_ir)

    return mcp_tree


def pw_to_go(pw_tree: Dict) -> str:
    """
    Generate Go code from PW MCP tree.

    Pipeline:
    1. MCP tree (universal) → Pure PW IR
    2. Denormalize: Apply Go idioms (error returns, stdlib) to Pure PW IR
    3. Go-specific IR → Go code

    Args:
        pw_tree: PW MCP tree (JSON dict)

    Returns:
        Go source code string
    """
    # Convert MCP tree → IR
    ir_module = mcp_to_ir(pw_tree)

    # Denormalize: Apply Go-specific patterns to Pure PW
    denormalized_ir = denormalize_ir(ir_module, target_lang="go")

    # Generate Go from IR
    generator = GoGeneratorV2()
    go_code = generator.generate(denormalized_ir)

    return go_code


# Test if run directly
if __name__ == "__main__":
    # Test Go → PW → Go roundtrip
    test_code = """
package main

func Calculate(x int, y int) int {
    result := x + y
    return result * 2
}
"""

    print("Original Go:")
    print(test_code)

    # Go → PW
    pw_tree = go_to_pw(test_code)
    print("\nPW MCP Tree:")
    import json
    print(json.dumps(pw_tree, indent=2)[:500] + "...")

    # PW → Go
    go_code = pw_to_go(pw_tree)
    print("\nGenerated Go:")
    print(go_code)

    print("\n✅ Go bridge working!")
