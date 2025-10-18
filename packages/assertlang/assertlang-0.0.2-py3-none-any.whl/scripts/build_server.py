#!/usr/bin/env python3
"""
Universal build system for compile-time languages (Go, C#, Rust).

Copies tool adapter source files into generated server project
and compiles everything together.
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List


class ServerBuilder:
    """Builds MCP servers for compile-time languages."""

    def __init__(self, project_dir: Path, promptware_root: Path):
        self.project_dir = project_dir
        self.promptware_root = promptware_root
        self.tools_dir = promptware_root / "tools"

    def detect_language(self) -> str:
        """Detect language from project files."""
        if (self.project_dir / "go.mod").exists():
            return "go"
        elif (self.project_dir / "Cargo.toml").exists():
            return "rust"
        elif list(self.project_dir.glob("*.csproj")):
            return "dotnet"
        else:
            raise ValueError("Could not detect language (no go.mod, Cargo.toml, or .csproj found)")

    def copy_tool_adapters(self, tools: List[str], language: str):
        """Copy tool adapter source files into project."""

        # Create tools directory in project
        project_tools_dir = self.project_dir / "tools"
        project_tools_dir.mkdir(exist_ok=True)

        # Extension mapping
        extensions = {
            "go": "adapter_go.go",
            "rust": "adapter_rust.rs",
            "dotnet": "Adapter.cs"
        }

        adapter_file = extensions.get(language)
        if not adapter_file:
            raise ValueError(f"Unsupported language: {language}")

        copied_count = 0

        for tool_name in tools:
            # Find tool adapter
            tool_dirs = [
                self.tools_dir / tool_name,
                self.tools_dir / tool_name.replace("_", "-")
            ]

            for tool_dir in tool_dirs:
                adapter_path = tool_dir / "adapters" / adapter_file
                if adapter_path.exists():
                    # Create tool directory in project
                    dest_dir = project_tools_dir / tool_name / "adapters"
                    dest_dir.mkdir(parents=True, exist_ok=True)

                    # Copy adapter file with language-specific transformations
                    dest_file = dest_dir / adapter_file

                    if language == "go":
                        # Fix package declaration for Go (package main -> package adapters)
                        content = adapter_path.read_text()
                        content = content.replace("package main", "package adapters", 1)
                        dest_file.write_text(content)
                    elif language == "dotnet":
                        # Wrap in namespace for C#
                        content = adapter_path.read_text()
                        namespace_name = tool_name.replace("-", "_").title() + "Adapter"
                        wrapped = f"namespace {namespace_name};\n\n{content}"
                        dest_file.write_text(wrapped)
                    elif language == "rust":
                        # Create module file structure for Rust
                        # Rust needs: src/tool_name/mod.rs
                        rust_mod_dir = self.project_dir / "src" / tool_name.replace("-", "_")
                        rust_mod_dir.mkdir(parents=True, exist_ok=True)
                        rust_mod_file = rust_mod_dir / "mod.rs"
                        shutil.copy2(adapter_path, rust_mod_file)
                    else:
                        shutil.copy2(adapter_path, dest_file)

                    print(f"  ✓ Copied {tool_name}")
                    copied_count += 1
                    break

        print(f"\nCopied {copied_count}/{len(tools)} tool adapters")
        return copied_count

    def build_go(self) -> bool:
        """Build Go server."""
        print("\n🔨 Building Go server...")

        # Update go.mod to include tools directory
        go_mod_path = self.project_dir / "go.mod"
        if go_mod_path.exists():
            # Add replace directives for local tool packages
            # For now, just run go mod tidy
            result = subprocess.run(
                ["go", "mod", "tidy"],
                cwd=self.project_dir,
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                print(f"  ✗ go mod tidy failed: {result.stderr}")

        # Build the server
        result = subprocess.run(
            ["go", "build", "-o", "server", "."],
            cwd=self.project_dir,
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print(f"  ✓ Build successful: {self.project_dir / 'server'}")
            return True
        else:
            print(f"  ✗ Build failed:\n{result.stderr}")
            return False

    def build_dotnet(self) -> bool:
        """Build .NET server."""
        print("\n🔨 Building .NET server...")

        result = subprocess.run(
            ["dotnet", "build", "-c", "Release"],
            cwd=self.project_dir,
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print("  ✓ Build successful")
            return True
        else:
            print(f"  ✗ Build failed:\n{result.stderr}")
            return False

    def build_rust(self) -> bool:
        """Build Rust server."""
        print("\n🔨 Building Rust server...")

        # Build in the project directory to avoid parent Cargo.toml conflicts
        result = subprocess.run(
            ["cargo", "build", "--release"],
            cwd=str(self.project_dir.absolute()),
            capture_output=True,
            text=True,
            env={**subprocess.os.environ, "CARGO_TARGET_DIR": str(self.project_dir.absolute() / "target")}
        )

        if result.returncode == 0:
            print(f"  ✓ Build successful: {self.project_dir / 'target/release'}")
            return True
        else:
            print(f"  ✗ Build failed:\n{result.stderr}")
            return False

    def build(self, tools: List[str]) -> bool:
        """Build the server project."""
        language = self.detect_language()
        print(f"📦 Detected language: {language}")

        # Copy tool adapters
        print(f"\n📂 Copying {len(tools)} tool adapters...")
        self.copy_tool_adapters(tools, language)

        # Build based on language
        if language == "go":
            return self.build_go()
        elif language == "dotnet":
            return self.build_dotnet()
        elif language == "rust":
            return self.build_rust()
        else:
            print(f"✗ Unsupported language: {language}")
            return False


def main():
    parser = argparse.ArgumentParser(description="Build MCP server for compile-time languages")
    parser.add_argument("project_dir", type=Path, help="Server project directory")
    parser.add_argument("--tools", nargs="+", required=True, help="List of tools to include")
    parser.add_argument("--promptware-root", type=Path, help="Promptware root directory")

    args = parser.parse_args()

    # Default promptware root to script's parent directory
    if args.promptware_root is None:
        args.promptware_root = Path(__file__).parent.parent

    if not args.project_dir.exists():
        print(f"✗ Project directory not found: {args.project_dir}")
        sys.exit(1)

    builder = ServerBuilder(args.project_dir, args.promptware_root)

    print("=" * 60)
    print("Promptware Server Builder")
    print("=" * 60)

    success = builder.build(args.tools)

    if success:
        print("\n" + "=" * 60)
        print("✅ Build completed successfully!")
        print("=" * 60)
        sys.exit(0)
    else:
        print("\n" + "=" * 60)
        print("❌ Build failed")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()
