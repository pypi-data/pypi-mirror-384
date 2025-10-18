# How to Create Demo GIF for AssertLang

## Tools Needed

1. **Terminalizer** (Recommended):
   ```bash
   npm install -g terminalizer
   ```

2. **Or asciinema + agg**:
   ```bash
   brew install asciinema
   cargo install --git https://github.com/asciinema/agg
   ```

---

## Demo Script

This script creates a ~30 second demo showing the full workflow.

### Recording with Terminalizer

```bash
cd /Users/hustlermain/HUSTLER_CONTENT/HSTLR/DEV/AssertLang

# Start recording
terminalizer record demo --skip-sharing

# Run these commands in the recording:
```

### Commands to Run (copy-paste these one by one):

```bash
# Show version
promptware --version

# Create a simple PW file
cat > calculator.al << 'EOF'
// Universal calculator in PW
function add(x: int, y: int) -> int {
    return x + y;
}

function multiply(x: int, y: int) -> int {
    return x * y;
}

function calculate_tax(price: float, rate: float) -> float {
    let tax = price * rate;
    return price + tax;
}
EOF

# Show the PW file
cat calculator.al

# Compile to Python
asl build calculator.al --lang python -o calculator.py

# Show Python output (first 10 lines)
head -20 calculator.py

# Compile to Go
asl build calculator.al --lang go -o calculator.go

# Show Go output (first 10 lines)
head -20 calculator.go

# Compile to Rust
asl build calculator.al --lang rust -o calculator.rs

# Show file sizes
ls -lh calculator.*

# Clean up
rm calculator.*
```

### Stop Recording

Press `Ctrl+D` to stop recording.

### Generate GIF

```bash
terminalizer render demo -o docs/images/promptware-demo.gif
```

---

## Alternative: asciinema + agg

```bash
# Record
asciinema rec demo.cast

# Run the same commands above

# Convert to GIF
agg demo.cast docs/images/promptware-demo.gif
```

---

## Configuration (Optional)

Create `.terminalizer/config.yml`:

```yaml
command: zsh
cols: 120
rows: 30
repeat: 0
quality: 100
frameDelay: auto
maxIdleTime: 2000
theme:
  background: "#0d1117"
  foreground: "#c9d1d9"
  cursor: "#58a6ff"
```

---

## Final Output

The GIF should show:
1. `promptware --version` → shows version
2. Create `calculator.pw` → shows code
3. Compile to Python → shows output
4. Compile to Go → shows output
5. Compile to Rust → shows output
6. `ls -lh` → shows all 3 files created

**Duration**: ~30 seconds
**Size**: <2MB
**FPS**: 10-15

---

## Quick Manual Alternative (Screenshot)

If you can't create a GIF, take screenshots of:

1. VSCode showing `calculator.pw` with syntax highlighting
2. Terminal showing successful compilation
3. Side-by-side Python/Go/Rust output

Save as:
- `docs/images/vscode-syntax.png`
- `docs/images/terminal-compile.png`
- `docs/images/code-comparison.png`

Then use in README like:

```markdown
![AssertLang in VSCode](docs/images/vscode-syntax.png)
![Compilation Success](docs/images/terminal-compile.png)
```
