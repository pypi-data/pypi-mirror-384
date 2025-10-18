#!/usr/bin/env python3
"""
DEPRECATED: This CLI has been replaced by promptware.cli

This module is deprecated and will be removed in a future version.
The new CLI is in promptware/cli.py and includes:
- Configuration management (promptware config)
- Safety features (--yes, --dry-run, --quiet)
- NO_COLOR support
- Improved UX and error handling

Use 'promptware' command instead (automatically uses promptware.cli via setup.py).

---

OLD Promptware CLI - Command-line interface for agent generation and management.

Usage:
    promptware generate <agent.al>              Generate MCP server
    promptware generate <agent.al> --lang go    Generate for specific language
    promptware run <agent.al>                   Generate and run server
    asl test <agent.al>                  Test agent definition
    promptware version                          Show version
"""

import argparse
import subprocess
import sys
from pathlib import Path

from language.agent_parser import parse_agent_pw
from language.go_server_generator import generate_go_mcp_server
from language.mcp_config_generator import (
    generate_configs_for_project,
    generate_quick_setup_instructions,
    scan_agents_in_directory,
)
from language.mcp_server_generator import generate_python_mcp_server
from language.nodejs_server_generator import generate_nodejs_mcp_server


def get_generator(lang: str):
    """Get the appropriate generator for the language."""
    generators = {
        "python": generate_python_mcp_server,
        "nodejs": generate_nodejs_mcp_server,
        "node": generate_nodejs_mcp_server,
        "js": generate_nodejs_mcp_server,
        "go": generate_go_mcp_server,
        "golang": generate_go_mcp_server,
    }

    generator = generators.get(lang.lower())
    if not generator:
        print(f"❌ Error: Unsupported language '{lang}'")
        print("   Supported: python, nodejs, go")
        sys.exit(1)

    return generator


def get_output_extension(lang: str) -> str:
    """Get file extension for the language."""
    extensions = {
        "python": ".py",
        "nodejs": ".js",
        "node": ".js",
        "js": ".js",
        "go": ".go",
        "golang": ".go",
    }
    return extensions.get(lang.lower(), ".py")


def command_generate(args):
    """Generate MCP server from .al file."""
    pw_file = Path(args.agent_file)

    if not pw_file.exists():
        print(f"❌ Error: File not found: {pw_file}")
        sys.exit(1)

    print(f"📝 Reading {pw_file}...")

    try:
        with open(pw_file, "r") as f:
            pw_code = f.read()
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        sys.exit(1)

    print("🔍 Parsing agent definition...")

    try:
        agent = parse_agent_pw(pw_code)
    except Exception as e:
        print(f"❌ Parse error: {e}")
        sys.exit(1)

    # Determine language (from args or agent definition)
    lang = args.lang or agent.lang

    print(f"🔨 Generating {lang.upper()} server...")

    try:
        generator = get_generator(lang)
        server_code = generator(agent)
    except Exception as e:
        print(f"❌ Generation error: {e}")
        sys.exit(1)

    # Determine output file
    if args.output:
        output_file = Path(args.output)
    else:
        ext = get_output_extension(lang)
        output_file = pw_file.with_name(f"{agent.name}_server{ext}")

    print(f"💾 Writing to {output_file}...")

    try:
        with open(output_file, "w") as f:
            f.write(server_code)
    except Exception as e:
        print(f"❌ Write error: {e}")
        sys.exit(1)

    print("✅ Success!")
    print(f"   Agent: {agent.name}")
    print(f"   Port: {agent.port}")
    print(f"   Verbs: {len(agent.exposes)}")
    print(f"   Output: {output_file} ({len(server_code.splitlines())} lines)")

    if lang.lower() in ["python"]:
        print(f"\n🚀 Run with: python3 {output_file}")
    elif lang.lower() in ["nodejs", "node", "js"]:
        print(f"\n🚀 Run with: node {output_file}")
    elif lang.lower() in ["go", "golang"]:
        print(f"\n🚀 Run with: go run {output_file}")


def command_run(args):
    """Generate and run MCP server."""
    # First generate
    print("=" * 60)
    print("STEP 1: Generate Server")
    print("=" * 60)
    command_generate(args)

    # Then run
    pw_file = Path(args.agent_file)

    try:
        with open(pw_file, "r") as f:
            pw_code = f.read()
        agent = parse_agent_pw(pw_code)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

    lang = args.lang or agent.lang

    if args.output:
        output_file = Path(args.output)
    else:
        ext = get_output_extension(lang)
        output_file = pw_file.with_name(f"{agent.name}_server{ext}")

    print("\n" + "=" * 60)
    print("STEP 2: Run Server")
    print("=" * 60)
    print(f"🚀 Starting {agent.name} on port {agent.port}...")
    print("   Press Ctrl+C to stop\n")

    try:
        if lang.lower() in ["python"]:
            subprocess.run(["python3", str(output_file)])
        elif lang.lower() in ["nodejs", "node", "js"]:
            subprocess.run(["node", str(output_file)])
        elif lang.lower() in ["go", "golang"]:
            subprocess.run(["go", "run", str(output_file)])
    except KeyboardInterrupt:
        print("\n\n⏹️  Server stopped")
    except Exception as e:
        print(f"\n❌ Runtime error: {e}")
        sys.exit(1)


def command_test(args):
    """Test agent definition by parsing and validating."""
    pw_file = Path(args.agent_file)

    if not pw_file.exists():
        print(f"❌ Error: File not found: {pw_file}")
        sys.exit(1)

    print(f"🧪 Testing {pw_file}...")

    try:
        with open(pw_file, "r") as f:
            pw_code = f.read()

        agent = parse_agent_pw(pw_code)

        print("✅ Parse: OK")
        print(f"   Agent: {agent.name}")
        print(f"   Lang: {agent.lang}")
        print(f"   Port: {agent.port}")
        print(f"   Verbs: {len(agent.exposes)}")

        if agent.llm:
            print(f"   AI: {agent.llm}")
        if agent.observability:
            print(
                f"   Observability: traces={agent.observability.traces}, metrics={agent.observability.metrics}"
            )
        if agent.temporal:
            print(f"   Temporal: {len(agent.workflows)} workflows")

        # Test generation
        print("\n🔨 Testing code generation...")

        lang = agent.lang
        generator = get_generator(lang)
        server_code = generator(agent)

        print(f"✅ Generation: OK ({len(server_code.splitlines())} lines)")

        print("\n✅ All tests passed!")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


def command_mcp_config(args):
    """Generate MCP configuration for editors (Cursor, Windsurf, etc)."""

    # Determine directory to scan
    if args.directory:
        project_dir = Path(args.directory)
    elif args.agent_file:
        # Single agent file
        project_dir = Path(args.agent_file).parent
    else:
        # Current directory
        project_dir = Path.cwd()

    if not project_dir.exists():
        print(f"❌ Error: Directory not found: {project_dir}")
        sys.exit(1)

    print(f"🔍 Scanning for .al agent files in {project_dir}...")

    # Scan for agents
    agent_files = scan_agents_in_directory(project_dir)

    if not agent_files:
        print(f"❌ No .al files found in {project_dir}")
        sys.exit(1)

    print(f"   Found {len(agent_files)} agent(s):")
    for pw_file, agent_name, port in agent_files:
        print(f"   • {agent_name} (port {port}) - {pw_file.name}")

    # Generate configs
    editor = args.editor.lower()

    print(f"\n🔨 Generating MCP config for {editor.title()}...")

    try:
        config_json = generate_configs_for_project(
            project_dir, editor=editor, output_dir=args.output if args.output else None
        )

        # Determine config path
        if args.output:
            config_path = Path(args.output) / "mcp.json"
        elif editor == "cursor":
            config_path = project_dir / ".cursor" / "mcp.json"
        elif editor == "windsurf":
            config_path = project_dir / ".windsurf" / "mcp.json"
        elif editor == "cline":
            config_path = project_dir / ".vscode" / "mcp.json"
        else:
            config_path = project_dir / "mcp.json"

        print(f"✅ Configuration saved to: {config_path}")
        print("\nConfiguration content:")
        print("=" * 60)
        print(config_json)
        print("=" * 60)

        # Show setup instructions
        instructions = generate_quick_setup_instructions(editor, config_path)
        print(instructions)

    except Exception as e:
        print(f"❌ Error generating config: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


def command_version(args):
    """Show version information."""
    print("Promptware v0.3.0")
    print("Agent-to-agent communication DSL")
    print("\nSupported languages:")
    print("  • Python (FastAPI) - Full support")
    print("  • Node.js (Express) - Basic MCP")
    print("  • Go (net/http) - Basic MCP")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="assertlang",
        description="Generate MCP servers from .al agent definitions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  promptware generate my_agent.al
  promptware generate my_agent.al --lang nodejs
  promptware generate my_agent.al -o custom_server.py
  promptware run my_agent.al
  asl test my_agent.al
  promptware version

For more info: https://github.com/3CH0xyz/promptware
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Generate command
    generate_parser = subparsers.add_parser("generate", help="Generate MCP server")
    generate_parser.add_argument("agent_file", help=".al agent definition file")
    generate_parser.add_argument("--lang", "-l", help="Target language (python, nodejs, go)")
    generate_parser.add_argument("--output", "-o", help="Output file path")
    generate_parser.set_defaults(func=command_generate)

    # Run command
    run_parser = subparsers.add_parser("run", help="Generate and run server")
    run_parser.add_argument("agent_file", help=".al agent definition file")
    run_parser.add_argument("--lang", "-l", help="Target language (python, nodejs, go)")
    run_parser.add_argument("--output", "-o", help="Output file path")
    run_parser.set_defaults(func=command_run)

    # Test command
    test_parser = subparsers.add_parser("test", help="Test agent definition")
    test_parser.add_argument("agent_file", help=".al agent definition file")
    test_parser.set_defaults(func=command_test)

    # MCP Config command
    mcp_parser = subparsers.add_parser("mcp-config", help="Generate MCP config for editors")
    mcp_parser.add_argument(
        "--editor",
        "-e",
        default="cursor",
        choices=["cursor", "windsurf", "cline"],
        help="Target editor (default: cursor)",
    )
    mcp_parser.add_argument(
        "--directory", "-d", help="Directory to scan for .al files (default: current)"
    )
    mcp_parser.add_argument(
        "--agent-file", "-a", help="Single .al file (alternative to --directory)"
    )
    mcp_parser.add_argument("--output", "-o", help="Output directory for config file")
    mcp_parser.set_defaults(func=command_mcp_config)

    # Version command
    version_parser = subparsers.add_parser("version", help="Show version")
    version_parser.set_defaults(func=command_version)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
