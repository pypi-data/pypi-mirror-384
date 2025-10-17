#!/usr/bin/env python3
"""
CLI tool for reverse parsing: Code → PW DSL

Usage:
    python3 reverse_parsers/cli.py <file>
    python3 reverse_parsers/cli.py <file> --output file.al
    python3 reverse_parsers/cli.py <file> --metadata
"""

import sys
import argparse
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from reverse_parsers.python_parser import PythonReverseParser
from reverse_parsers.nodejs_parser import NodeJSReverseParser
from reverse_parsers.rust_parser import RustReverseParser
from reverse_parsers.dotnet_parser import DotNetReverseParser
from reverse_parsers.go_parser import GoReverseParser


def detect_language(file_path: Path) -> str:
    """Detect language from file extension."""
    suffix = file_path.suffix.lower()
    if suffix == '.py':
        return 'python'
    elif suffix in ['.js', '.mjs', '.cjs']:
        return 'nodejs'
    elif suffix == '.rs':
        return 'rust'
    elif suffix == '.cs':
        return 'dotnet'
    elif suffix == '.go':
        return 'go'
    else:
        # Try to guess from content
        content = file_path.read_text()
        if 'using Microsoft.AspNetCore' in content or 'namespace ' in content:
            return 'dotnet'
        elif 'use warp::' in content or 'use actix_web::' in content:
            return 'rust'
        elif 'import express' in content or 'require("express")' in content:
            return 'nodejs'
        elif 'from flask import' in content or 'from fastapi import' in content:
            return 'python'
        elif 'package main' in content or 'import "net/http"' in content:
            return 'go'
    return 'unknown'


def main():
    parser = argparse.ArgumentParser(
        description='Reverse parse code to PW DSL',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Parse Python file and output PW DSL
  python3 reverse_parsers/cli.py server.py

  # Parse Rust file
  python3 reverse_parsers/cli.py main.rs

  # Save to file
  python3 reverse_parsers/cli.py server.py --output agent.al

  # Include extraction metadata
  python3 reverse_parsers/cli.py server.py --metadata

Supported languages: Python (.py), Node.js (.js), Rust (.rs), .NET/C# (.cs), Go (.go)
        """
    )

    parser.add_argument('file', help='Source file to parse')
    parser.add_argument(
        '-o', '--output',
        help='Output file (default: stdout)'
    )
    parser.add_argument(
        '-m', '--metadata',
        action='store_true',
        help='Include extraction metadata as comments'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Show detailed extraction info'
    )
    parser.add_argument(
        '-l', '--lang',
        choices=['python', 'nodejs', 'rust', 'dotnet', 'go'],
        help='Force language (auto-detect if not specified)'
    )

    args = parser.parse_args()

    # Check file exists
    file_path = Path(args.file)
    if not file_path.exists():
        print(f"Error: File not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    # Detect language
    lang = args.lang or detect_language(file_path)
    if lang == 'unknown':
        print(f"Error: Could not detect language for {args.file}", file=sys.stderr)
        print(f"Use --lang to specify: python, nodejs, rust, dotnet, or go", file=sys.stderr)
        sys.exit(1)

    # Parse the file
    print(f"Parsing {file_path.name} ({lang})...", file=sys.stderr)

    # Select appropriate parser
    if lang == 'python':
        reverse_parser = PythonReverseParser()
    elif lang == 'nodejs':
        reverse_parser = NodeJSReverseParser()
    elif lang == 'rust':
        reverse_parser = RustReverseParser()
    elif lang == 'dotnet':
        reverse_parser = DotNetReverseParser()
    elif lang == 'go':
        reverse_parser = GoReverseParser()
    else:
        print(f"Error: Unsupported language: {lang}", file=sys.stderr)
        sys.exit(1)

    try:
        extracted_agent = reverse_parser.parse_file(str(file_path))
        pw_output = reverse_parser.to_pw_dsl(
            extracted_agent,
            include_metadata=args.metadata
        )

        # Show stats if verbose
        if args.verbose:
            print("\n" + "=" * 60, file=sys.stderr)
            print("EXTRACTION STATISTICS", file=sys.stderr)
            print("=" * 60, file=sys.stderr)
            print(f"Agent name:  {extracted_agent.name}", file=sys.stderr)
            print(f"Port:        {extracted_agent.port}", file=sys.stderr)
            print(f"Framework:   {extracted_agent.framework}", file=sys.stderr)
            print(f"Confidence:  {extracted_agent.confidence_score:.0%}", file=sys.stderr)
            print(f"Verbs found: {len(extracted_agent.verbs)}", file=sys.stderr)
            print(f"Tools found: {len(extracted_agent.tools)}", file=sys.stderr)

            if extracted_agent.extraction_notes:
                print("\nNotes:", file=sys.stderr)
                for note in extracted_agent.extraction_notes:
                    print(f"  - {note}", file=sys.stderr)

            print("\n" + "=" * 60, file=sys.stderr)
            print()

        # Output PW DSL
        if args.output:
            output_path = Path(args.output)
            output_path.write_text(pw_output)
            print(f"✅ Wrote PW DSL to: {args.output}", file=sys.stderr)
        else:
            print(pw_output)

    except Exception as e:
        print(f"Error parsing file: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
