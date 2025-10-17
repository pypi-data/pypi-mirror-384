#!/usr/bin/env python3
"""
Multi-Language Code Validator

Validates generated code in ALL target languages using their native tools:
- Python: ast.parse() for syntax, mypy for types
- Go: go build for compilation
- Rust: rustc --check for compilation
- Node.js: esprima/acorn for syntax, tsc for types
- .NET: Roslyn for compilation

NO AI - uses actual compilers/parsers!
"""

import ast
import subprocess
import tempfile
import os
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """Result of code validation."""
    language: str
    valid: bool
    errors: List[Dict[str, str]]
    warnings: List[Dict[str, str]]

    def __str__(self):
        if self.valid:
            msg = f"✅ Valid {self.language}"
            if self.warnings:
                msg += f" ({len(self.warnings)} warnings)"
            return msg
        return f"❌ Invalid {self.language} ({len(self.errors)} errors)"


class MultiLanguageValidator:
    """Validate generated code in all target languages."""

    def validate_python(self, code: str, check_types: bool = False) -> ValidationResult:
        """Validate Python code using ast.parse() and optionally mypy."""
        errors = []
        warnings = []

        # Step 1: Syntax validation with ast.parse()
        try:
            ast.parse(code)
        except SyntaxError as e:
            errors.append({
                "type": "syntax_error",
                "message": str(e.msg),
                "line": e.lineno,
                "column": e.offset,
                "fix": self._suggest_python_fix(e)
            })
            return ValidationResult("Python", False, errors, warnings)

        # Step 2: Type checking with mypy (optional)
        if check_types:
            type_errors = self._check_python_types(code)
            errors.extend(type_errors)

        # Step 3: Runtime checks (imports, undefined vars)
        runtime_errors = self._check_python_runtime(code)
        warnings.extend(runtime_errors)

        return ValidationResult(
            "Python",
            len(errors) == 0,
            errors,
            warnings
        )

    def validate_go(self, code: str, package: str = "main") -> ValidationResult:
        """Validate Go code using 'go build'."""
        errors = []
        warnings = []

        # Create temporary Go file
        with tempfile.TemporaryDirectory() as tmpdir:
            go_file = Path(tmpdir) / "main.go"
            go_file.write_text(f"package {package}\n\n{code}")

            # Run go build
            result = subprocess.run(
                ["go", "build", "-o", "/dev/null", str(go_file)],
                capture_output=True,
                text=True,
                cwd=tmpdir
            )

            if result.returncode != 0:
                # Parse Go compiler errors
                for line in result.stderr.split('\n'):
                    if ':' in line:
                        parts = line.split(':', 3)
                        if len(parts) >= 4:
                            errors.append({
                                "type": "compilation_error",
                                "file": parts[0],
                                "line": parts[1],
                                "column": parts[2] if parts[2].isdigit() else None,
                                "message": parts[-1].strip(),
                                "fix": self._suggest_go_fix(parts[-1].strip())
                            })

        return ValidationResult(
            "Go",
            len(errors) == 0,
            errors,
            warnings
        )

    def validate_rust(self, code: str) -> ValidationResult:
        """Validate Rust code using 'rustc --check'."""
        errors = []
        warnings = []

        # Create temporary Rust file
        with tempfile.TemporaryDirectory() as tmpdir:
            rust_file = Path(tmpdir) / "main.rs"
            rust_file.write_text(code)

            # Run rustc --check (checks without linking)
            result = subprocess.run(
                ["rustc", "--crate-type", "lib", "--check", str(rust_file)],
                capture_output=True,
                text=True,
                cwd=tmpdir
            )

            if result.returncode != 0:
                # Parse Rust compiler errors
                for line in result.stderr.split('\n'):
                    if 'error' in line.lower():
                        errors.append({
                            "type": "compilation_error",
                            "message": line.strip(),
                            "fix": self._suggest_rust_fix(line)
                        })
                    elif 'warning' in line.lower():
                        warnings.append({
                            "type": "warning",
                            "message": line.strip()
                        })

        return ValidationResult(
            "Rust",
            len(errors) == 0,
            errors,
            warnings
        )

    def validate_nodejs(self, code: str, check_types: bool = False) -> ValidationResult:
        """Validate Node.js code using esprima/acorn and optionally tsc."""
        errors = []
        warnings = []

        # Try to import esprima for JS parsing
        try:
            import esprima
            try:
                esprima.parseScript(code)
            except esprima.Error as e:
                errors.append({
                    "type": "syntax_error",
                    "message": str(e),
                    "line": e.lineNumber if hasattr(e, 'lineNumber') else None,
                    "column": e.column if hasattr(e, 'column') else None
                })
        except ImportError:
            # Fallback: Use Node.js to check syntax
            with tempfile.TemporaryDirectory() as tmpdir:
                js_file = Path(tmpdir) / "temp.js"
                js_file.write_text(code)

                result = subprocess.run(
                    ["node", "--check", str(js_file)],
                    capture_output=True,
                    text=True
                )

                if result.returncode != 0:
                    errors.append({
                        "type": "syntax_error",
                        "message": result.stderr.strip()
                    })

        # Type checking with TypeScript (if requested)
        if check_types:
            type_errors = self._check_typescript_types(code)
            errors.extend(type_errors)

        return ValidationResult(
            "Node.js",
            len(errors) == 0,
            errors,
            warnings
        )

    def validate_dotnet(self, code: str, language: str = "csharp") -> ValidationResult:
        """Validate .NET code using Roslyn compiler."""
        errors = []
        warnings = []

        # Create temporary C# file
        with tempfile.TemporaryDirectory() as tmpdir:
            ext = "cs" if language == "csharp" else "vb"
            code_file = Path(tmpdir) / f"Temp.{ext}"
            code_file.write_text(code)

            # Run csc (C# compiler) or vbc (VB compiler)
            compiler = "csc" if language == "csharp" else "vbc"
            result = subprocess.run(
                [compiler, "/t:library", "/out:temp.dll", str(code_file)],
                capture_output=True,
                text=True,
                cwd=tmpdir
            )

            if result.returncode != 0:
                # Parse compiler errors
                for line in result.stdout.split('\n'):
                    if 'error' in line.lower():
                        errors.append({
                            "type": "compilation_error",
                            "message": line.strip()
                        })
                    elif 'warning' in line.lower():
                        warnings.append({
                            "type": "warning",
                            "message": line.strip()
                        })

        return ValidationResult(
            ".NET",
            len(errors) == 0,
            errors,
            warnings
        )

    def validate_java(self, code: str) -> ValidationResult:
        """Validate Java code using javac compiler."""
        errors = []
        warnings = []

        # Extract class name from code
        import re
        class_match = re.search(r'public\s+class\s+(\w+)', code)
        class_name = class_match.group(1) if class_match else "Main"

        # Create temporary Java file
        with tempfile.TemporaryDirectory() as tmpdir:
            java_file = Path(tmpdir) / f"{class_name}.java"
            java_file.write_text(code)

            # Run javac (Java compiler)
            result = subprocess.run(
                ["javac", str(java_file)],
                capture_output=True,
                text=True,
                cwd=tmpdir
            )

            if result.returncode != 0:
                # Parse javac error messages
                for line in result.stderr.split('\n'):
                    if '.java:' in line and 'error:' in line:
                        errors.append({
                            "type": "compilation_error",
                            "message": line.strip()
                        })
                    elif 'warning:' in line:
                        warnings.append({
                            "type": "warning",
                            "message": line.strip()
                        })

        return ValidationResult(
            "Java",
            len(errors) == 0,
            errors,
            warnings
        )

    def validate_all(self, pw_ir, generators: Dict) -> Dict[str, ValidationResult]:
        """
        Validate PW IR in ALL target languages.

        Args:
            pw_ir: The PW IR to validate
            generators: Dict of language -> generator instance
                       e.g. {"python": PythonGeneratorV2(), "go": GoGeneratorV2(), ...}

        Returns:
            Dict mapping language -> ValidationResult
        """
        results = {}

        for lang, generator in generators.items():
            # Generate code
            code = generator.generate(pw_ir)

            # Validate based on language
            if lang == "python":
                results[lang] = self.validate_python(code, check_types=True)
            elif lang == "go":
                results[lang] = self.validate_go(code)
            elif lang == "rust":
                results[lang] = self.validate_rust(code)
            elif lang == "nodejs":
                results[lang] = self.validate_nodejs(code, check_types=True)
            elif lang == "dotnet" or lang == "csharp":
                results[lang] = self.validate_dotnet(code, language="csharp")
            elif lang == "java":
                results[lang] = self.validate_java(code)

        return results

    # Helper methods for type checking
    def _check_python_types(self, code: str) -> List[Dict]:
        """Check Python types using mypy."""
        errors = []
        with tempfile.TemporaryDirectory() as tmpdir:
            py_file = Path(tmpdir) / "temp.py"
            py_file.write_text(code)

            result = subprocess.run(
                ["mypy", "--strict", str(py_file)],
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                for line in result.stdout.split('\n'):
                    if 'error:' in line:
                        errors.append({
                            "type": "type_error",
                            "message": line.strip()
                        })
        return errors

    def _check_python_runtime(self, code: str) -> List[Dict]:
        """Check for runtime issues (undefined vars, bad imports)."""
        warnings = []
        tree = ast.parse(code)

        # Check for undefined variables (simplified)
        defined_vars = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                defined_vars.add(node.id)
            elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                if node.id not in defined_vars and not node.id in dir(__builtins__):
                    warnings.append({
                        "type": "undefined_variable",
                        "message": f"Variable '{node.id}' may be undefined",
                        "line": node.lineno
                    })

        return warnings

    def _check_typescript_types(self, code: str) -> List[Dict]:
        """Check TypeScript types using tsc."""
        errors = []
        with tempfile.TemporaryDirectory() as tmpdir:
            ts_file = Path(tmpdir) / "temp.ts"
            ts_file.write_text(code)

            result = subprocess.run(
                ["tsc", "--noEmit", str(ts_file)],
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                for line in result.stdout.split('\n'):
                    if 'error' in line.lower():
                        errors.append({
                            "type": "type_error",
                            "message": line.strip()
                        })
        return errors

    # Suggestion helpers
    def _suggest_python_fix(self, error: SyntaxError) -> str:
        """Suggest fix for Python syntax error."""
        msg = error.msg.lower()
        if "invalid syntax" in msg:
            return "Check for missing colons, parentheses, or quotes"
        elif "unexpected eof" in msg:
            return "Check for unclosed brackets, parentheses, or quotes"
        elif "indentation" in msg:
            return "Check indentation - use consistent spaces or tabs"
        return "Review syntax near the error line"

    def _suggest_go_fix(self, error_msg: str) -> str:
        """Suggest fix for Go compilation error."""
        msg = error_msg.lower()
        if "undefined" in msg:
            return "Variable or function not defined - check spelling and imports"
        elif "missing" in msg:
            return "Missing required element - check Go syntax"
        elif "cannot use" in msg:
            return "Type mismatch - check variable types"
        return "Review Go syntax and types"

    def _suggest_rust_fix(self, error_msg: str) -> str:
        """Suggest fix for Rust compilation error."""
        msg = error_msg.lower()
        if "borrow" in msg:
            return "Borrow checker issue - review ownership rules"
        elif "type" in msg:
            return "Type mismatch - check type annotations"
        elif "lifetime" in msg:
            return "Lifetime issue - add lifetime annotations if needed"
        return "Review Rust syntax and ownership"


# Convenience function
def validate_generated_code(pw_ir, language: str, generator) -> ValidationResult:
    """Validate generated code in a specific language."""
    validator = MultiLanguageValidator()
    code = generator.generate(pw_ir)

    if language == "python":
        return validator.validate_python(code, check_types=True)
    elif language == "go":
        return validator.validate_go(code)
    elif language == "rust":
        return validator.validate_rust(code)
    elif language == "nodejs":
        return validator.validate_nodejs(code, check_types=True)
    elif language == "dotnet":
        return validator.validate_dotnet(code)
    else:
        raise ValueError(f"Unknown language: {language}")


if __name__ == "__main__":
    # Test multi-language validation
    from translators.pw_composer import *
    from translators.ir_converter import mcp_to_ir
    from language.python_generator_v2 import PythonGeneratorV2
    from language.go_generator_v2 import GoGeneratorV2

    print("Multi-Language Validator Test\n" + "="*70)

    # Create a simple PW function
    pw_func = pw_function(
        name="add",
        params=[
            pw_parameter("x", pw_type("int")),
            pw_parameter("y", pw_type("int"))
        ],
        return_type=pw_type("int"),
        body=[
            pw_return(
                pw_binary_op("+", pw_identifier("x"), pw_identifier("y"))
            )
        ]
    )

    pw_mod = pw_module("test", functions=[pw_func])
    ir = mcp_to_ir(pw_mod)

    # Validate in multiple languages
    validator = MultiLanguageValidator()

    generators = {
        "python": PythonGeneratorV2(),
        "go": GoGeneratorV2(),
        # "rust": RustGeneratorV2(),  # Add when available
    }

    results = validator.validate_all(ir, generators)

    print("\nValidation Results:")
    print("-" * 70)
    for lang, result in results.items():
        print(f"\n{result}")
        if result.errors:
            print("  Errors:")
            for error in result.errors:
                print(f"    ❌ {error['message']}")
        if result.warnings:
            print("  Warnings:")
            for warning in result.warnings:
                print(f"    ⚠️  {warning['message']}")
