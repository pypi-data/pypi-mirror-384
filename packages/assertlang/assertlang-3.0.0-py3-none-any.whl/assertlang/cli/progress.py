"""Progress indicators and timing utilities for CLI commands."""

import time
import sys
from contextlib import contextmanager
from typing import Optional


@contextmanager
def timed_step(description: str, verbose: bool = True, quiet: bool = False):
    """
    Context manager for timed operations with progress output.

    Usage:
        with timed_step("Loading model", verbose=args.verbose, quiet=args.quiet):
            load_model()

    Args:
        description: Description of the operation
        verbose: Whether to show detailed output
        quiet: Whether to suppress all output

    Yields:
        None
    """
    if not quiet:
        if verbose:
            print(f"[*] {description}...", file=sys.stderr, flush=True)

    start = time.time()
    try:
        yield
    finally:
        elapsed = time.time() - start
        if not quiet and verbose:
            print(f"[+] {description} ({elapsed:.1f}s)", file=sys.stderr, flush=True)


def show_progress(message: str, quiet: bool = False):
    """
    Show a progress message.

    Args:
        message: Progress message to display
        quiet: Whether to suppress output
    """
    if not quiet:
        print(f"[*] {message}...", file=sys.stderr, flush=True)


def show_completion(message: str, elapsed: Optional[float] = None, quiet: bool = False):
    """
    Show completion message with optional timing.

    Args:
        message: Completion message to display
        elapsed: Optional elapsed time in seconds
        quiet: Whether to suppress output
    """
    if not quiet:
        if elapsed is not None:
            print(f"[+] {message} ({elapsed:.1f}s)", file=sys.stderr, flush=True)
        else:
            print(f"[+] {message}", file=sys.stderr, flush=True)
