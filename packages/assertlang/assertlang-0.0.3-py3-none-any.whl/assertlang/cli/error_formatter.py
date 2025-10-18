"""Rich error formatting utilities for CLI."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List
import re


@dataclass
class SourceLocation:
    """Source code location for error reporting."""
    file: Path
    line: int
    column: int
    source_line: str


def extract_location_from_error(error_msg: str) -> Optional[tuple]:
    """
    Extract line and column from error message.

    Example: "[Line 1:1] Expected declaration" -> (1, 1)

    Args:
        error_msg: Error message that may contain location

    Returns:
        Tuple of (line, column) or None if not found
    """
    match = re.search(r'\[Line (\d+):(\d+)\]', error_msg)
    if match:
        return int(match.group(1)), int(match.group(2))
    return None


def get_source_context(file_path: Path, line: int, context_lines: int = 2) -> List[str]:
    """
    Get source code lines around the error location.

    Args:
        file_path: Path to source file
        line: Line number (1-indexed)
        context_lines: Number of lines before/after to show

    Returns:
        List of formatted source lines with line numbers
    """
    try:
        lines = file_path.read_text().splitlines()

        # Calculate range
        start = max(0, line - context_lines - 1)
        end = min(len(lines), line + context_lines)

        result = []
        for i in range(start, end):
            line_num = i + 1
            prefix = ">" if line_num == line else " "
            result.append(f" {prefix} {line_num:4} | {lines[i]}")

        return result
    except Exception:
        return []


def format_parse_error(
    error: Exception,
    file_path: Optional[Path] = None,
    suggestions: Optional[List[str]] = None
) -> str:
    """
    Format parse error with source context and suggestions.

    Args:
        error: The exception that was raised
        file_path: Path to source file (if available)
        suggestions: List of helpful suggestions for fixing

    Returns:
        Formatted error string with context and suggestions
    """
    message = str(error)

    # Try to extract location from error message
    location = extract_location_from_error(message)

    parts = []
    if file_path:
        parts.append(f"[!] Parse error in {file_path}")
    else:
        parts.append("[!] Parse error")

    # Show location and context
    if location and file_path and file_path.exists():
        line, column = location
        parts.append(f"\n  Line {line}, column {column}:")

        # Get source context
        context = get_source_context(file_path, line)
        if context:
            parts.append("")
            parts.extend(context)

            # Add pointer to error location
            pointer_line = f"      {' ' * (column - 1)}^^^"
            parts.append(pointer_line)
        parts.append("")

    # Clean up error message (remove location since we show it above)
    clean_message = re.sub(r'\[Line \d+:\d+\]\s*', '', message)
    parts.append(f"  {clean_message}")

    # Add suggestions
    if suggestions:
        parts.append("\n  Suggestions:")
        for suggestion in suggestions:
            parts.append(f"    - {suggestion}")

    # Add docs link
    parts.append("\n  See: https://docs.assertlang.dev/syntax")

    return "\n".join(parts)


def get_parse_error_suggestions(error_msg: str) -> List[str]:
    """
    Get helpful suggestions based on error message.

    Args:
        error_msg: The error message to analyze

    Returns:
        List of suggestion strings
    """
    suggestions = []
    error_lower = error_msg.lower()

    if "expected declaration" in error_lower:
        suggestions.append("Try defining a function: function name(param: type) -> returntype { ... }")
        suggestions.append("Or a class: class Name { field: type; }")

    elif "expected" in error_lower and "{" in error_msg:
        suggestions.append("Check for missing or extra braces { }")

    elif "unexpected" in error_lower:
        suggestions.append("Check for typos in keywords or identifiers")

    elif ";" in error_msg and "expected" in error_lower:
        suggestions.append("Ensure statements end with semicolons")

    elif "return" in error_lower:
        suggestions.append("Check return statement syntax: return value;")

    elif "type" in error_lower:
        suggestions.append("Check type annotations: param: type")
        suggestions.append("Valid types: int, string, bool, float, any")

    return suggestions


def format_file_not_found_error(file_path: str, similar_files: List[Path]) -> str:
    """
    Format file not found error with suggestions.

    Args:
        file_path: The file that was not found
        similar_files: List of similar files that exist

    Returns:
        Formatted error message
    """
    parts = []
    parts.append("[!] Error: File not found")
    parts.append(f"\n  Path: {file_path}")
    parts.append("\n  The specified .al file does not exist.")

    if similar_files:
        parts.append("\n  Did you mean one of these?")
        for f in similar_files[:5]:  # Limit to 5 suggestions
            parts.append(f"    - {f}")

    return "\n".join(parts)
