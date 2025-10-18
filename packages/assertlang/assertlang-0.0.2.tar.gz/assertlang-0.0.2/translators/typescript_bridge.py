#!/usr/bin/env python3
"""
TypeScript ⟷ PW Bridge

Translates between TypeScript code and PW MCP trees.
"""

import sys
from pathlib import Path
from typing import Dict
import tempfile
import os

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from language.typescript_parser_v3 import TypeScriptParserV3
from language.nodejs_generator_v2 import NodeJSGeneratorV2
from translators.ir_converter import ir_to_mcp, mcp_to_ir
from translators.semantic_normalizer import normalize_ir, denormalize_ir


def typescript_to_pw(typescript_code: str) -> Dict:
    """
    Parse TypeScript code → PW MCP tree.

    Pipeline:
    1. TypeScript AST → IR (language-specific) - using V3 parser (97% accuracy)
    2. Normalize: Strip TypeScript idioms (promises, decorators) → Pure PW IR
    3. Pure PW IR → MCP tree (universal format)

    Args:
        typescript_code: TypeScript source code string

    Returns:
        PW MCP tree (JSON-serializable dict)
    """
    # Parse TypeScript → IR using V3 parser (needs file path)
    parser = TypeScriptParserV3()

    # Write to temp file for V3 parser
    with tempfile.NamedTemporaryFile(mode='w', suffix='.ts', delete=False) as f:
        f.write(typescript_code)
        temp_path = f.name

    try:
        ir_module = parser.parse_file(temp_path)
    finally:
        os.unlink(temp_path)

    # Normalize: Strip TypeScript-specific patterns → Pure PW
    normalized_ir = normalize_ir(ir_module, source_lang="typescript")

    # Convert IR → MCP tree
    mcp_tree = ir_to_mcp(normalized_ir)

    return mcp_tree


def pw_to_typescript(pw_tree: Dict) -> str:
    """
    Generate TypeScript code from PW MCP tree.

    Pipeline:
    1. MCP tree (universal) → Pure PW IR
    2. Denormalize: Apply TypeScript idioms (promises, types) to Pure PW IR
    3. TypeScript-specific IR → TypeScript code

    Args:
        pw_tree: PW MCP tree (JSON dict)

    Returns:
        TypeScript source code string
    """
    # Convert MCP tree → IR
    ir_module = mcp_to_ir(pw_tree)

    # Denormalize: Apply TypeScript-specific patterns to Pure PW
    denormalized_ir = denormalize_ir(ir_module, target_lang="typescript")

    # Generate TypeScript from IR (using NodeJS generator for now)
    generator = NodeJSGeneratorV2()
    typescript_code = generator.generate(denormalized_ir)

    return typescript_code


# Test if run directly
if __name__ == "__main__":
    # Test TypeScript → PW → TypeScript roundtrip
    test_code = """
function calculate(x: number, y: number): number {
    const result = x + y;
    return result * 2;
}
"""

    print("Original TypeScript:")
    print(test_code)

    # TypeScript → PW
    pw_tree = typescript_to_pw(test_code)
    print("\nPW MCP Tree:")
    import json
    print(json.dumps(pw_tree, indent=2)[:500] + "...")

    # PW → TypeScript
    typescript_code = pw_to_typescript(pw_tree)
    print("\nGenerated TypeScript:")
    print(typescript_code)

    print("\n✅ TypeScript bridge working!")
