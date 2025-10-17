# PW VS Code Extension

**Syntax highlighting and file icons for PW (AssertLang) language**

---

## Status

**Current: Private/Workspace Extension** 🔒

The PW VS Code extension is currently included in the AssertLang repository and loads automatically when you open the workspace. It is **not yet published** to the VS Code Marketplace.

**Future: Public Marketplace Extension** 🌐

We plan to publish to the VS Code Marketplace so anyone can install with one click!

---

## Installation Options

### Option 1: Workspace (Automatic) ✅ Recommended

**For developers working in the AssertLang repository:**

1. Clone the AssertLang repository:
   ```bash
   git clone https://github.com/AssertLang/AssertLang.git
   cd promptware
   ```

2. Open in VS Code:
   ```bash
   code .
   ```

3. Reload VS Code:
   - Press `Cmd+Shift+P` (Mac) or `Ctrl+Shift+P` (Windows/Linux)
   - Type: `Developer: Reload Window`
   - Press Enter

4. Open any `.pw` file (e.g., `examples/calculator.pw`)

**That's it!** Syntax highlighting should work automatically.

### Option 2: Manual .vsix Install

**To install globally on your machine:**

1. Navigate to the extension folder:
   ```bash
   cd .vscode/extensions/pw-language
   ```

2. Package the extension:
   ```bash
   # Install vsce if you don't have it
   npm install -g vsce

   # Package the extension
   vsce package
   ```

   This creates: `pw-language-0.1.0.vsix`

3. Install the extension:
   ```bash
   code --install-extension pw-language-0.1.0.vsix
   ```

4. Reload VS Code

### Option 3: Marketplace (Coming Soon!)

**Future installation method:**

1. Open VS Code
2. Go to Extensions (`Cmd+Shift+X` or `Ctrl+Shift+X`)
3. Search for "PW Language Support"
4. Click "Install"

---

## Features

### Syntax Highlighting ✨

Full colorization for PW syntax:

- **Keywords** (purple/blue): `function`, `if`, `else`, `return`, `let`, `const`
- **Types** (light blue): `int`, `float`, `string`, `bool`, `array`, `map`
- **Strings** (orange): `"hello"`, `'world'`
- **Numbers** (green): `42`, `3.14`
- **Comments** (green): `// comment`, `/* block comment */`
- **Operators**: `+`, `-`, `*`, `/`, `==`, `!=`, `->`, etc.

### File Icons 🎨

Purple "PW" icon next to `.pw` files in the file explorer.

**To enable:**
1. `Cmd+Shift+P` → `Preferences: File Icon Theme`
2. Select `PW Icons`

### Editor Features 🛠️

- **Auto-closing brackets**: `{`, `[`, `(`
- **Auto-closing quotes**: `"`, `'`
- **Comment toggling**: `Cmd+/` or `Ctrl+/`
- **Bracket matching**: Click `{` to highlight matching `}`
- **Code folding**: Collapse/expand function blocks

---

## Extension Files

### Location in Repository

```
.vscode/extensions/pw-language/
├── package.json                    # Extension manifest
├── language-configuration.json     # Editor configuration
├── syntaxes/
│   └── pw.tmLanguage.json         # Syntax highlighting rules
├── icons/
│   └── pw-icon.svg                # PW logo (purple square with "PW")
├── iconTheme.json                 # Icon theme definition
├── README.md                      # Extension documentation
└── SETUP.md                       # Installation guide
```

### Download

**Clone from GitHub:**

```bash
git clone https://github.com/AssertLang/AssertLang.git
cd promptware/.vscode/extensions/pw-language/
```

**Direct download** (when repo is public):

- **Full extension**: Download the entire `.vscode/extensions/pw-language/` folder
- **Logo only**: Download `.vscode/extensions/pw-language/icons/pw-icon.svg`

---

## Logo/Icon

### PW Brand Icon

**File:** `.vscode/extensions/pw-language/icons/pw-icon.svg`

**Design:**
- Purple square background (#6B46C1)
- White "PW" text
- 32x32 pixels
- SVG format (scales to any size)

**Usage:**

```html
<!-- In HTML -->
<img src="pw-icon.svg" alt="PW Logo" width="32" height="32">
```

```markdown
<!-- In Markdown -->
![PW Logo](pw-icon.svg)
```

**License:** Free to use for PW-related projects. Modify as needed!

### Custom Icons

Feel free to create your own PW icon! Replace `.vscode/extensions/pw-language/icons/pw-icon.svg` with your design.

**Requirements:**
- SVG format
- 32x32 viewBox
- File name: `pw-icon.svg`

---

## Customization

### Change Syntax Colors

The extension uses standard TextMate scopes, so colors are controlled by your VS Code theme.

**Example scopes:**
- `keyword.control.pw` - Control keywords (if, else, return)
- `keyword.other.pw` - Other keywords (function, let)
- `support.type.primitive.pw` - Primitive types (int, string)
- `string.quoted.double.pw` - Double-quoted strings
- `comment.line.double-slash.pw` - Single-line comments

**To customize colors in your theme:**

1. `Cmd+Shift+P` → `Preferences: Open Settings (JSON)`
2. Add to `editor.tokenColorCustomizations`:

```json
{
  "editor.tokenColorCustomizations": {
    "textMateRules": [
      {
        "scope": "keyword.control.al",
        "settings": {
          "foreground": "#C678DD",
          "fontStyle": "bold"
        }
      },
      {
        "scope": "support.type.primitive.al",
        "settings": {
          "foreground": "#56B6C2"
        }
      }
    ]
  }
}
```

### Add File Associations

Associate other file extensions with PW:

1. `Cmd+Shift+P` → `Preferences: Open Settings (JSON)`
2. Add:

```json
{
  "files.associations": {
    "*.promptware": "pw",
    "*.pwlang": "pw"
  }
}
```

---

## Sharing the Extension

### With Your Team

**Option 1: Share the repository**

Team members clone the repo and get the extension automatically.

**Option 2: Share the .vsix file**

1. Package the extension:
   ```bash
   cd .vscode/extensions/pw-language
   vsce package
   ```

2. Share `pw-language-0.1.0.vsix` with your team

3. Team members install:
   ```bash
   code --install-extension pw-language-0.1.0.vsix
   ```

### Public Distribution

**Publishing to VS Code Marketplace** (planned):

1. Create VS Code publisher account
2. Update `package.json` with publisher info
3. Publish:
   ```bash
   vsce publish
   ```

4. Extension appears in marketplace within minutes!

**Documentation:** https://code.visualstudio.com/api/working-with-extensions/publishing-extension

---

## Troubleshooting

### Syntax highlighting not working

**Solution 1: Reload window**
- `Cmd+Shift+P` → `Developer: Reload Window`

**Solution 2: Check language mode**
- Look in bottom-right corner of VS Code
- Should say "PW"
- If it says "Plain Text", click it and select "PW"

**Solution 3: Reinstall extension**
- Delete `.vscode/extensions/pw-language/`
- Re-clone from repository
- Reload VS Code

### No file icon appearing

**Solution: Select icon theme**
- `Cmd+Shift+P` → `Preferences: File Icon Theme`
- Select `PW Icons`

### Extension not found

**Solution: Check workspace**
- Make sure you're opening the AssertLang folder in VS Code
- The extension only loads from `.vscode/extensions/` in the workspace

### Syntax errors in .al files

**Not a VS Code issue!**
- The extension only provides highlighting, not validation
- Use the PW compiler to check syntax:
  ```bash
  pw build file.al --lang python
  ```

---

## Development

### Building from Source

```bash
cd .vscode/extensions/pw-language

# Install dependencies (none currently needed)
npm install

# Package for distribution
npm install -g vsce
vsce package

# Output: pw-language-0.1.0.vsix
```

### Testing Changes

After modifying the extension:

1. Save your changes
2. `Cmd+Shift+P` → `Developer: Reload Window`
3. Changes should be visible immediately

### Adding New Keywords

Edit `syntaxes/pw.tmLanguage.json`:

```json
{
  "keywords": {
    "patterns": [
      {
        "name": "keyword.control.al",
        "match": "\\b(if|else|for|while|your-new-keyword)\\b"
      }
    ]
  }
}
```

### Contributing

Improvements welcome!

- Better syntax highlighting
- More comprehensive language features
- Icon improvements
- Snippets
- Autocomplete

See `CONTRIBUTING.md` for guidelines.

---

## Roadmap

### Current (v0.1.0)
- ✅ Basic syntax highlighting
- ✅ File icons
- ✅ Auto-closing brackets
- ✅ Comment toggling

### Planned (v0.2.0)
- [ ] Code snippets (`func` → full function template)
- [ ] Error diagnostics (show syntax errors inline)
- [ ] Go to definition
- [ ] Find all references

### Future (v1.0.0)
- [ ] LSP server integration
- [ ] Autocomplete
- [ ] Hover documentation
- [ ] Refactoring tools
- [ ] Debugger integration

---

## Support

### Getting Help

- **Setup issues:** See `SETUP.md`
- **Language questions:** See `PW_LANGUAGE_GUIDE.md`
- **Bug reports:** https://github.com/AssertLang/AssertLang/issues
- **Feature requests:** https://github.com/AssertLang/AssertLang/discussions

### Contact

- **GitHub:** https://github.com/AssertLang/AssertLang
- **Discord:** (Coming soon!)
- **Email:** (Coming soon!)

---

## License

MIT License - Free to use, modify, and distribute.

See `LICENSE` for full text.

---

## Credits

**Created by:** AssertLang Contributors

**Built with:**
- TextMate grammars
- VS Code Extension API
- SVG icons

**Thanks to:**
- The VS Code team for excellent extension APIs
- The open source community

---

**Status Summary:**

🔒 **Current:** Private (workspace extension)
📦 **Download:** Clone from GitHub repository
🌐 **Future:** Public (VS Code Marketplace)
🎨 **Logo:** Available at `.vscode/extensions/pw-language/icons/pw-icon.svg`

---

**Last Updated:** 2025-10-07
