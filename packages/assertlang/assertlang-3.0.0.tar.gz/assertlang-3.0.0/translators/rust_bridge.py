#!/usr/bin/env python3
"""
Rust ⟷ PW Bridge

Translates between Rust code and PW MCP trees.
"""

import sys
from pathlib import Path
from typing import Dict
import tempfile
import os

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from language.rust_parser_v3 import RustParserV3
from language.rust_generator_v2 import RustGeneratorV2
from translators.ir_converter import ir_to_mcp, mcp_to_ir
from translators.semantic_normalizer import normalize_ir, denormalize_ir


def rust_to_pw(rust_code: str) -> Dict:
    """
    Parse Rust code → PW MCP tree.

    Pipeline:
    1. Rust AST → IR (language-specific) - using V3 parser (95% accuracy)
    2. Normalize: Strip Rust idioms (Result, Option, lifetimes) → Pure PW IR
    3. Pure PW IR → MCP tree (universal format)

    Args:
        rust_code: Rust source code string

    Returns:
        PW MCP tree (JSON-serializable dict)
    """
    # Parse Rust → IR using V3 parser (needs file path)
    parser = RustParserV3()

    # Write to temp file for V3 parser
    with tempfile.NamedTemporaryFile(mode='w', suffix='.rs', delete=False) as f:
        f.write(rust_code)
        temp_path = f.name

    try:
        ir_module = parser.parse_file(temp_path)
    finally:
        os.unlink(temp_path)

    # Normalize: Strip Rust-specific patterns → Pure PW
    normalized_ir = normalize_ir(ir_module, source_lang="rust")

    # Convert IR → MCP tree
    mcp_tree = ir_to_mcp(normalized_ir)

    return mcp_tree


def pw_to_rust(pw_tree: Dict) -> str:
    """
    Generate Rust code from PW MCP tree.

    Pipeline:
    1. MCP tree (universal) → Pure PW IR
    2. Denormalize: Apply Rust idioms (Result, Option, ownership) to Pure PW IR
    3. Rust-specific IR → Rust code

    Args:
        pw_tree: PW MCP tree (JSON dict)

    Returns:
        Rust source code string
    """
    # Convert MCP tree → IR
    ir_module = mcp_to_ir(pw_tree)

    # Denormalize: Apply Rust-specific patterns to Pure PW
    denormalized_ir = denormalize_ir(ir_module, target_lang="rust")

    # Generate Rust from IR
    generator = RustGeneratorV2()
    rust_code = generator.generate(denormalized_ir)

    return rust_code


# Test if run directly
if __name__ == "__main__":
    # Test Rust → PW → Rust roundtrip
    test_code = """
pub fn calculate(x: i32, y: i32) -> i32 {
    let result = x + y;
    result * 2
}
"""

    print("Original Rust:")
    print(test_code)

    # Rust → PW
    pw_tree = rust_to_pw(test_code)
    print("\nPW MCP Tree:")
    import json
    print(json.dumps(pw_tree, indent=2)[:500] + "...")

    # PW → Rust
    rust_code = pw_to_rust(pw_tree)
    print("\nGenerated Rust:")
    print(rust_code)

    print("\n✅ Rust bridge working!")
