# PW Documentation Index

**Complete guide to all PW (AssertLang) documentation**

---

## Getting Started

### For Everyone

📘 **[PW Language Guide](PW_LANGUAGE_GUIDE.md)** - **START HERE!**
- Complete instructional manual for both humans and AI agents
- Installation, quick start, examples, CLI reference
- VS Code extension setup and download links
- FAQ and troubleshooting

📋 **[Quick Reference](QUICK_REFERENCE.md)** - Cheat sheet
- Syntax at a glance
- Common commands
- Quick examples

### For Human Developers

👨‍💻 **[PW Native Syntax](PW_NATIVE_SYNTAX.md)** - Language specification
- Complete grammar and syntax rules
- Type system documentation
- Code examples
- Compilation process

### For AI Agents

🤖 **[MCP Server Documentation](../pw-syntax-mcp-server/CURRENT_WORK.md)** - Agent workflows
- How to compose PW programmatically
- MCP tool usage
- Architecture explanation
- Agent collaboration patterns

---

## Tooling

### VS Code Extension

🎨 **[VS Code Extension Guide](VS_CODE_EXTENSION.md)** - Editor integration
- Installation options (workspace, manual, marketplace)
- Syntax highlighting features
- File icons and branding
- Logo download and usage
- **Extension Status:** Currently private (workspace-only)
- **Download:** Clone repository, extension in `.vscode/extensions/pw-language/`

---

## Technical Documentation

### Architecture

🏗️ **[Architecture Overview](ARCHITECTURE.md)** - System design
- Compiler pipeline
- IR (Intermediate Representation)
- MCP JSON format
- Code generation

### Language Specification

📖 **[PW Native Syntax Spec](PW_NATIVE_SYNTAX.md)** - Formal specification
- Keywords and operators
- Type system
- Control flow
- Functions and classes
- Compilation examples

### Current Work

📝 **[Current Work](../CURRENT_WORK.md)** - Latest status
- What's completed
- What's in progress
- Test results
- Next steps

---

## Examples

### Code Examples

💻 **Working Examples:**
- [`examples/calculator.pw`](../examples/calculator.al) - Basic arithmetic functions
- [`/tmp/examples.pw`](../examples/) - Comprehensive syntax examples
- [`/tmp/user_service.pw`](../examples/) - User validation service

### Generated Code

Each example includes generated code:
- `calculator.py` - Python version
- `calculator.go` - Go version
- `calculator.rs` - Rust version
- `calculator.ts` - TypeScript version (can be generated)
- `calculator.cs` - C# version (can be generated)

---

## Installation & Setup

### Install PW Compiler

```bash
# Clone repository
git clone https://github.com/AssertLang/AssertLang.git
cd promptware

# Install dependencies
pip install -e .

# Verify installation
pw --version
```

**See:** [PW Language Guide - Installation](PW_LANGUAGE_GUIDE.md#installation)

### Install VS Code Extension

**Automatic (Workspace):**
1. Open AssertLang folder in VS Code
2. `Cmd+Shift+P` → `Developer: Reload Window`
3. Extension loads automatically!

**Manual (.vsix):**
```bash
cd .vscode/extensions/pw-language
npm install -g vsce
vsce package
code --install-extension pw-language-0.1.0.vsix
```

**See:** [VS Code Extension Guide](VS_CODE_EXTENSION.md)

---

## Quick Links

### Documentation Files

| Document | Purpose | Audience |
|----------|---------|----------|
| [PW_LANGUAGE_GUIDE.md](PW_LANGUAGE_GUIDE.md) | Complete manual | Everyone |
| [QUICK_REFERENCE.md](QUICK_REFERENCE.md) | Cheat sheet | Everyone |
| [PW_NATIVE_SYNTAX.md](PW_NATIVE_SYNTAX.md) | Language spec | Developers |
| [VS_CODE_EXTENSION.md](VS_CODE_EXTENSION.md) | Editor setup | Developers |
| [ARCHITECTURE.md](ARCHITECTURE.md) | System design | Contributors |
| [CURRENT_WORK.md](../CURRENT_WORK.md) | Latest status | Contributors |

### Key Files in Repository

| File | Description |
|------|-------------|
| `examples/calculator.pw` | Working PW example |
| `.vscode/extensions/pw-language/` | VS Code extension |
| `.vscode/extensions/pw-language/icons/pw-icon.svg` | PW logo |
| `dsl/pw_parser.py` | PW compiler/parser |
| `docs/` | All documentation |

### External Links

- **GitHub:** https://github.com/AssertLang/AssertLang
- **Issues:** https://github.com/AssertLang/AssertLang/issues
- **Discussions:** https://github.com/AssertLang/AssertLang/discussions

---

## Common Tasks

### I want to...

**Learn PW basics**
→ Read [PW Language Guide](PW_LANGUAGE_GUIDE.md)

**Write my first PW program**
→ Follow [Quick Start](PW_LANGUAGE_GUIDE.md#quick-start)

**Get syntax highlighting in VS Code**
→ See [VS Code Extension](VS_CODE_EXTENSION.md)

**Download the PW logo**
→ Get it from `.vscode/extensions/pw-language/icons/pw-icon.svg`

**Compile PW to Python/Go/Rust**
→ Use `pw build file.al --lang <language>`

**Use PW as an AI agent**
→ Read [MCP Server Docs](../pw-syntax-mcp-server/CURRENT_WORK.md)

**Understand PW syntax rules**
→ Read [PW Native Syntax](PW_NATIVE_SYNTAX.md)

**Contribute to PW**
→ See `CONTRIBUTING.md`

**Report a bug**
→ Open issue: https://github.com/AssertLang/AssertLang/issues

---

## For Different Audiences

### 👨‍💻 Human Developers

**Read:**
1. [PW Language Guide](PW_LANGUAGE_GUIDE.md) - Complete manual
2. [Quick Reference](QUICK_REFERENCE.md) - Syntax cheat sheet
3. [VS Code Extension](VS_CODE_EXTENSION.md) - Editor setup

**Then:**
- Try examples in `examples/`
- Install VS Code extension
- Write your first `.pw` file

### 🤖 AI Agents

**Read:**
1. [PW Language Guide - For AI Agents](PW_LANGUAGE_GUIDE.md#for-ai-agents)
2. [MCP Server Docs](../pw-syntax-mcp-server/CURRENT_WORK.md)

**Then:**
- Use MCP tools to compose PW
- Share PW MCP trees with other agents
- Generate target language when executing

### 🛠️ Contributors

**Read:**
1. [Architecture](ARCHITECTURE.md) - System design
2. [Current Work](../CURRENT_WORK.md) - Latest status
3. `CONTRIBUTING.md` - Contribution guidelines

**Then:**
- Check open issues
- Add features or fix bugs
- Submit pull requests

---

## Documentation Status

### ✅ Complete

- PW Language Guide (comprehensive manual)
- Quick Reference (cheat sheet)
- PW Native Syntax (language spec)
- VS Code Extension Guide
- Current Work (status updates)
- Code examples (calculator, user service)

### 🚧 In Progress

- ARCHITECTURE.md (needs update for native syntax)
- CONTRIBUTING.md (needs PW-specific guidelines)
- CLI implementation (commands specified but not built)

### 📋 Planned

- Tutorial: "Build a REST API in PW"
- Migration guides (Python → PW, Go → PW, etc.)
- Standard library documentation
- Performance benchmarks
- Best practices guide

---

## Extension Status

### VS Code Extension

**Current Status:** 🔒 **Private** (workspace-only)

**Location:** `.vscode/extensions/pw-language/`

**Installation:**
- Automatic: Open AssertLang workspace in VS Code
- Manual: Package as `.vsix` and install globally

**Features:**
- ✅ Syntax highlighting
- ✅ File icons (purple "PW" logo)
- ✅ Auto-closing brackets/quotes
- ✅ Comment toggling

**Download:**
- Clone repository: `git clone https://github.com/AssertLang/AssertLang.git`
- Extension folder: `.vscode/extensions/pw-language/`
- Logo file: `.vscode/extensions/pw-language/icons/pw-icon.svg`

**Future:** 🌐 **Public** (VS Code Marketplace)

We plan to publish to the marketplace for one-click installation!

---

## Version Information

**PW Version:** 0.1.0 (Native Language Release)

**What's Working:**
- ✅ Functions with parameters
- ✅ If/else conditionals
- ✅ Variables and assignments
- ✅ Types: int, float, string, bool
- ✅ Operators: +, -, *, /, ==, !=, <, >
- ✅ Comments: //, /* */
- ✅ Compilation to 5 languages

**What's Coming:**
- 🚧 For/while loops
- 🚧 Classes and methods
- 🚧 Arrays and maps
- 🚧 Type definitions
- 🚧 Enums
- 🚧 Try/catch
- 🚧 CLI commands

---

## Support

### Getting Help

**Questions?**
- Read the [FAQ](PW_LANGUAGE_GUIDE.md#faq)
- Check [Troubleshooting](PW_LANGUAGE_GUIDE.md#troubleshooting)

**Issues?**
- Report bugs: https://github.com/AssertLang/AssertLang/issues
- Request features: https://github.com/AssertLang/AssertLang/discussions

**Community:**
- Discord: (Coming soon!)
- Twitter: (Coming soon!)

---

## License

All documentation is licensed under [MIT License](../LICENSE).

Free to use, modify, and distribute.

---

## Credits

**Documentation by:** AssertLang Contributors

**Last Updated:** 2025-10-07

**Contributors:**
- Core team
- AI agents (Claude Code)
- Community members

---

**Start here:** [PW Language Guide](PW_LANGUAGE_GUIDE.md) 🚀

**Questions?** Open an issue: https://github.com/AssertLang/AssertLang/issues
