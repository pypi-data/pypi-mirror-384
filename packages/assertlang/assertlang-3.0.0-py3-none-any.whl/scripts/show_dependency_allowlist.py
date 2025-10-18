#!/usr/bin/env python3
"""Prints a human-readable summary of the dependency allowlist and optional plan view."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from daemon.deps_utils import summarise_allowlist


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, help="Optional path to a plan JSON file", default=None)
    args = parser.parse_args()

    data = summarise_allowlist(args.plan)
    print(json.dumps(data, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
