#!/usr/bin/env python3
"""Placeholder CLI for future pwfmt/pwlint functionality."""
import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Verify formatting without rewriting")
    parser.add_argument("paths", nargs="*", help="Files or directories to format")
    parser.parse_args()
    print("pwfmt placeholder: no-op")


if __name__ == "__main__":
    main()
