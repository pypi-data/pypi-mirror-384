"""
Generate MCP server configurations for editors (Cursor, Windsurf, etc).

Editors like Cursor and Windsurf have built-in MCP client support.
This module generates config files so editors can connect to Promptware agents.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class MCPServerConfig:
    """MCP server configuration for an agent."""
    name: str
    command: str
    args: List[str]
    env: Optional[Dict[str, str]] = None


def generate_cursor_config(agents: List[MCPServerConfig], output_path: Optional[Path] = None) -> str:
    """
    Generate Cursor MCP configuration.

    Cursor expects a .cursor/mcp.json file with server definitions.
    """
    config = {
        "mcpServers": {}
    }

    for agent in agents:
        server_config = {
            "command": agent.command,
            "args": agent.args
        }

        if agent.env:
            server_config["env"] = agent.env

        config["mcpServers"][agent.name] = server_config

    json_config = json.dumps(config, indent=2)

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json_config)

    return json_config


def generate_windsurf_config(agents: List[MCPServerConfig], output_path: Optional[Path] = None) -> str:
    """
    Generate Windsurf MCP configuration.

    Windsurf uses similar config format to Cursor.
    """
    # Windsurf uses same format as Cursor
    return generate_cursor_config(agents, output_path)


def generate_cline_config(agents: List[MCPServerConfig], output_path: Optional[Path] = None) -> str:
    """
    Generate Cline (VSCode extension) MCP configuration.

    Cline expects MCP servers in VSCode settings.
    """
    config = {
        "cline.mcpServers": {}
    }

    for agent in agents:
        server_config = {
            "command": agent.command,
            "args": agent.args
        }

        if agent.env:
            server_config["env"] = agent.env

        config["cline.mcpServers"][agent.name] = server_config

    json_config = json.dumps(config, indent=2)

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json_config)

    return json_config


def scan_agents_in_directory(directory: Path) -> List[tuple[Path, str, int]]:
    """
    Scan directory for .al agent files.

    Returns: List of (pw_file_path, agent_name, port)
    """
    from language.agent_parser import parse_agent_pw

    agents = []

    for pw_file in directory.rglob("*.al"):
        try:
            pw_code = pw_file.read_text()
            agent = parse_agent_pw(pw_code)
            agents.append((pw_file, agent.name, agent.port))
        except Exception as e:
            print(f"Warning: Failed to parse {pw_file}: {e}")

    return agents


def generate_agent_mcp_config(
    pw_file: Path,
    agent_name: str,
    port: int,
    use_python: bool = True
) -> MCPServerConfig:
    """
    Generate MCP config for a single agent.

    Args:
        pw_file: Path to .al file
        agent_name: Name of the agent
        port: Port the agent runs on
        use_python: If True, use Python server. Otherwise use generated server.

    Returns:
        MCPServerConfig for the agent
    """
    import sys

    if use_python:
        # Use Python directly to run the CLI (works without promptware in PATH)
        # Find cli/main.py relative to pw_file
        project_root = pw_file.parent
        while not (project_root / "cli" / "main.py").exists():
            if project_root.parent == project_root:
                # Reached root, use current approach
                break
            project_root = project_root.parent

        cli_path = project_root / "cli" / "main.py"
        stdio_server_path = project_root / "language" / "mcp_stdio_server.py"

        if cli_path.exists() and stdio_server_path.exists():
            # Use native stdio MCP server
            # Communicates directly via MCP protocol over stdin/stdout
            return MCPServerConfig(
                name=agent_name,
                command=sys.executable,  # Current Python interpreter
                args=[str(stdio_server_path.absolute()), str(pw_file.absolute())],
                env={"PYTHONPATH": str(project_root.absolute())}
            )
        else:
            # Fallback to promptware command
            return MCPServerConfig(
                name=agent_name,
                command="assertlang",
                args=["run", str(pw_file.absolute())]
            )
    else:
        # Use generated server file
        server_file = pw_file.with_name(f"{agent_name}_server.py")
        return MCPServerConfig(
            name=agent_name,
            command=sys.executable,
            args=[str(server_file.absolute())]
        )


def generate_configs_for_project(
    project_dir: Path,
    editor: str = "cursor",
    output_dir: Optional[Path] = None
) -> str:
    """
    Generate MCP configs for all agents in a project.

    Args:
        project_dir: Directory containing .al files
        editor: Editor type (cursor, windsurf, cline)
        output_dir: Where to write config (defaults to project_dir/.cursor or similar)

    Returns:
        Generated configuration as JSON string
    """
    # Scan for agents
    agent_files = scan_agents_in_directory(project_dir)

    if not agent_files:
        raise ValueError(f"No .al files found in {project_dir}")

    # Generate configs
    mcp_configs = []
    for pw_file, agent_name, port in agent_files:
        config = generate_agent_mcp_config(pw_file, agent_name, port)
        mcp_configs.append(config)

    # Determine output path
    if output_dir is None:
        if editor == "cursor":
            output_dir = project_dir / ".cursor"
        elif editor == "windsurf":
            output_dir = project_dir / ".windsurf"
        elif editor == "cline":
            output_dir = project_dir / ".vscode"
    else:
        # Ensure output_dir is a Path object
        output_dir = Path(output_dir)

    output_file = output_dir / "mcp.json"

    # Generate appropriate config
    if editor in ["cursor", "windsurf"]:
        config_json = generate_cursor_config(mcp_configs, output_file)
    elif editor == "cline":
        config_json = generate_cline_config(mcp_configs, output_file)
    else:
        raise ValueError(f"Unknown editor: {editor}")

    return config_json


def generate_quick_setup_instructions(editor: str, config_path: Path) -> str:
    """Generate setup instructions for the user."""

    if editor == "cursor":
        return f"""
✅ Cursor MCP Configuration Generated

Configuration saved to: {config_path}

Setup Steps:
1. Open Cursor
2. Open Settings (Cmd+, or Ctrl+,)
3. Search for "MCP"
4. Click "Edit in settings.json"
5. The config at {config_path} will be used automatically

Or manually add:
1. Copy the content from {config_path}
2. Paste into your Cursor settings

Your Promptware agents are now available in Cursor!
Use them via the MCP menu or chat interface.
"""

    elif editor == "windsurf":
        return f"""
✅ Windsurf MCP Configuration Generated

Configuration saved to: {config_path}

Setup Steps:
1. Open Windsurf
2. Go to Settings → Extensions → MCP
3. The config at {config_path} will be loaded automatically

Your Promptware agents are now available in Windsurf!
"""

    elif editor == "cline":
        return f"""
✅ Cline (VSCode) MCP Configuration Generated

Configuration saved to: {config_path}

Setup Steps:
1. Open VSCode
2. Install the Cline extension if not installed
3. Open Settings (Cmd+, or Ctrl+,)
4. Search for "Cline MCP"
5. The config at {config_path} will be used

Your Promptware agents are now available in Cline!
"""

    return f"Configuration generated at: {config_path}"