"""
Test Python reverse parser with round-trip validation.

Tests: PW → Python → PW (should match)
"""

import tempfile
from pathlib import Path
import sys

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from language.agent_parser import parse_agent_pw
from language.mcp_server_generator import generate_python_mcp_server
from reverse_parsers.python_parser import PythonReverseParser


def normalize_pw(pw_text: str) -> dict:
    """Normalize PW for comparison (ignore whitespace, order)."""
    # Parse the PW
    agent_def = parse_agent_pw(pw_text)

    return {
        'agent': agent_def.name,
        'port': agent_def.port,
        'lang': agent_def.lang,
        'tools': sorted(agent_def.tools) if agent_def.tools else [],
        'verbs': sorted([
            {
                'name': v.verb,
                'params': sorted([
                    {'name': p['name'], 'type': p['type']}
                    for p in v.params
                ], key=lambda x: x['name']),
                'returns': sorted([
                    {'name': r['name'], 'type': r['type']}
                    for r in v.returns
                ], key=lambda x: x['name'])
            }
            for v in agent_def.exposes
        ], key=lambda x: x['name'])
    }


def test_roundtrip_minimal():
    """Test: PW → Python → PW (minimal agent)."""

    original_pw = """lang python
agent test-minimal
port 8000

expose greet@v1:
  params:
    name string
  returns:
    message string
"""

    # Forward: PW → Python
    agent_def = parse_agent_pw(original_pw)
    python_code = generate_python_mcp_server(agent_def)

    # Write to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(python_code)
        temp_file = f.name

    # Reverse: Python → PW
    parser = PythonReverseParser()
    extracted_agent = parser.parse_file(temp_file)
    reconstructed_pw = parser.to_pw_dsl(extracted_agent)

    print("\n=== MINIMAL AGENT TEST ===")
    print("\nOriginal PW:")
    print(original_pw)
    print("\nReconstructed PW:")
    print(reconstructed_pw)
    print(f"\nConfidence: {extracted_agent.confidence_score:.0%}")
    print(f"Framework: {extracted_agent.framework}")

    # Compare normalized
    original_norm = normalize_pw(original_pw)
    reconstructed_norm = normalize_pw(reconstructed_pw)

    print("\nOriginal (normalized):", original_norm)
    print("Reconstructed (normalized):", reconstructed_norm)

    # Check match
    assert original_norm['agent'] == reconstructed_norm['agent'], "Agent name mismatch"
    assert original_norm['port'] == reconstructed_norm['port'], "Port mismatch"
    assert original_norm['lang'] == reconstructed_norm['lang'], "Language mismatch"
    assert original_norm['verbs'] == reconstructed_norm['verbs'], "Verbs mismatch"

    print("\n✅ Round-trip successful!")

    # Clean up
    Path(temp_file).unlink()


def test_roundtrip_with_tools():
    """Test: PW → Python → PW (agent with tools)."""

    original_pw = """lang python
agent test-with-tools
port 8001

tools:
  - http
  - storage

expose fetch_data@v1:
  params:
    url string
  returns:
    status int
    data string

expose save_record@v1:
  params:
    key string
    value string
  returns:
    success bool
"""

    # Forward: PW → Python
    agent_def = parse_agent_pw(original_pw)
    python_code = generate_python_mcp_server(agent_def)

    # Write to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(python_code)
        temp_file = f.name

    # Reverse: Python → PW
    parser = PythonReverseParser()
    extracted_agent = parser.parse_file(temp_file)
    reconstructed_pw = parser.to_pw_dsl(extracted_agent)

    print("\n=== WITH TOOLS TEST ===")
    print("\nOriginal PW:")
    print(original_pw)
    print("\nReconstructed PW:")
    print(reconstructed_pw)
    print(f"\nConfidence: {extracted_agent.confidence_score:.0%}")
    print(f"Framework: {extracted_agent.framework}")

    # Compare
    original_norm = normalize_pw(original_pw)
    reconstructed_norm = normalize_pw(reconstructed_pw)

    assert original_norm['agent'] == reconstructed_norm['agent']
    assert original_norm['port'] == reconstructed_norm['port']
    assert original_norm['tools'] == reconstructed_norm['tools']
    assert len(original_norm['verbs']) == len(reconstructed_norm['verbs'])

    print("\n✅ Round-trip with tools successful!")

    # Clean up
    Path(temp_file).unlink()


def test_on_generated_server():
    """Test parsing an actual generated server."""

    # Use one of our generated test servers
    test_server_path = Path(__file__).parent.parent.parent / \
        "tests/bidirectional/generated/minimal-test-agent_server.py"

    if not test_server_path.exists():
        print(f"\n⚠️  Skipping: {test_server_path} not found")
        return

    parser = PythonReverseParser()
    extracted_agent = parser.parse_file(str(test_server_path))
    pw_output = parser.to_pw_dsl(extracted_agent, include_metadata=True)

    print("\n=== GENERATED SERVER TEST ===")
    print(f"\nParsing: {test_server_path.name}")
    print(f"\nExtracted PW DSL:")
    print(pw_output)
    print(f"\nConfidence: {extracted_agent.confidence_score:.0%}")
    print(f"Framework: {extracted_agent.framework}")
    print(f"Verbs found: {len(extracted_agent.verbs)}")
    print(f"Tools found: {len(extracted_agent.tools)}")

    if extracted_agent.extraction_notes:
        print(f"\nNotes:")
        for note in extracted_agent.extraction_notes:
            print(f"  - {note}")

    assert extracted_agent.confidence_score > 0.5, "Low confidence extraction"
    print("\n✅ Generated server parsing successful!")


if __name__ == "__main__":
    print("=" * 60)
    print("PYTHON REVERSE PARSER TEST SUITE")
    print("=" * 60)

    try:
        test_roundtrip_minimal()
        print("\n" + "-" * 60)

        test_roundtrip_with_tools()
        print("\n" + "-" * 60)

        test_on_generated_server()
        print("\n" + "-" * 60)

        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
