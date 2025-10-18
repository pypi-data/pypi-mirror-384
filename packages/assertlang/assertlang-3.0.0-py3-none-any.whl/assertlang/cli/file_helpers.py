"""File utilities for CLI commands."""

from pathlib import Path
from typing import List, Tuple
import difflib


def find_similar_files(
    target: str,
    search_dir: Path = None,
    extension: str = ".al",
    max_results: int = 5
) -> List[Path]:
    """
    Find files similar to target in search directory.

    Args:
        target: Target filename or path
        search_dir: Directory to search (defaults to current + examples/)
        extension: File extension to filter
        max_results: Maximum number of suggestions

    Returns:
        List of similar file paths
    """
    if search_dir is None:
        search_dir = Path.cwd()

    # Find all files with extension
    pw_files = []

    # Search current directory
    pw_files.extend(search_dir.glob(f"*{extension}"))

    # Search common directories
    for subdir in ["examples", "tests", "."]:
        subdir_path = search_dir / subdir
        if subdir_path.exists() and subdir_path.is_dir():
            pw_files.extend(subdir_path.rglob(f"*{extension}"))

    # Remove duplicates
    pw_files = list(set(pw_files))

    if not pw_files:
        return []

    # Get just the filenames
    file_names = [f.name for f in pw_files]

    # Find close matches
    target_name = Path(target).name
    matches = difflib.get_close_matches(
        target_name,
        file_names,
        n=max_results,
        cutoff=0.6
    )

    # Return full paths
    result = []
    for match in matches:
        for f in pw_files:
            if f.name == match:
                result.append(f)
                break

    return result[:max_results]


def check_file_writable(file_path: Path) -> Tuple[bool, str]:
    """
    Check if file path is writable.

    Args:
        file_path: Path to check

    Returns:
        Tuple of (is_writable, error_message)
        If is_writable is True, error_message will be empty string
    """
    try:
        # Check if parent directory exists and is writable
        parent = file_path.parent
        if not parent.exists():
            return False, f"Directory does not exist: {parent}"

        if not parent.is_dir():
            return False, f"Not a directory: {parent}"

        # Try to check write permission
        if not parent.stat().st_mode & 0o200:
            return False, f"No write permission: {parent}"

        return True, ""
    except Exception as e:
        return False, str(e)
