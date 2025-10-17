#!/usr/bin/env python3
"""
C# ⟷ PW Bridge

Translates between C# code and PW MCP trees.
"""

import sys
from pathlib import Path
from typing import Dict
import tempfile
import os

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from language.csharp_parser_v3 import CSharpParserV3
from language.dotnet_generator_v2 import DotNetGeneratorV2
from translators.ir_converter import ir_to_mcp, mcp_to_ir
from translators.semantic_normalizer import normalize_ir, denormalize_ir


def csharp_to_pw(csharp_code: str) -> Dict:
    """
    Parse C# code → PW MCP tree.

    Pipeline:
    1. C# AST → IR (language-specific) - using V3 parser (97% accuracy)
    2. Normalize: Strip C# idioms (LINQ, async/await, properties) → Pure PW IR
    3. Pure PW IR → MCP tree (universal format)

    Args:
        csharp_code: C# source code string

    Returns:
        PW MCP tree (JSON-serializable dict)
    """
    # Parse C# → IR using V3 parser (needs file path)
    parser = CSharpParserV3()

    # Write to temp file for V3 parser
    with tempfile.NamedTemporaryFile(mode='w', suffix='.cs', delete=False) as f:
        f.write(csharp_code)
        temp_path = f.name

    try:
        ir_module = parser.parse_file(temp_path)
    finally:
        os.unlink(temp_path)

    # Normalize: Strip C#-specific patterns → Pure PW
    normalized_ir = normalize_ir(ir_module, source_lang="csharp")

    # Convert IR → MCP tree
    mcp_tree = ir_to_mcp(normalized_ir)

    return mcp_tree


def pw_to_csharp(pw_tree: Dict) -> str:
    """
    Generate C# code from PW MCP tree.

    Pipeline:
    1. MCP tree (universal) → Pure PW IR
    2. Denormalize: Apply C# idioms (properties, LINQ, async/await) to Pure PW IR
    3. C#-specific IR → C# code

    Args:
        pw_tree: PW MCP tree (JSON dict)

    Returns:
        C# source code string
    """
    # Convert MCP tree → IR
    ir_module = mcp_to_ir(pw_tree)

    # Denormalize: Apply C#-specific patterns to Pure PW
    denormalized_ir = denormalize_ir(ir_module, target_lang="csharp")

    # Generate C# from IR
    generator = DotNetGeneratorV2()
    csharp_code = generator.generate(denormalized_ir)

    return csharp_code


# Test if run directly
if __name__ == "__main__":
    # Test C# → PW → C# roundtrip
    test_code = """
public class Calculator {
    public int Calculate(int x, int y) {
        int result = x + y;
        return result * 2;
    }
}
"""

    print("Original C#:")
    print(test_code)

    # C# → PW
    pw_tree = csharp_to_pw(test_code)
    print("\nPW MCP Tree:")
    import json
    print(json.dumps(pw_tree, indent=2)[:500] + "...")

    # PW → C#
    csharp_code = pw_to_csharp(pw_tree)
    print("\nGenerated C#:")
    print(csharp_code)

    print("\n✅ C# bridge working!")
