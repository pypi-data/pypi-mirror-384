#!/usr/bin/env python3
"""Trim .mcpd/cache entries based on allowlist TTL hints."""
from __future__ import annotations

import argparse
import json

from daemon.deps_utils import trim_cache


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--default-ttl-days", type=int, default=30, help="Fallback TTL when allowlist lacks cache hints")
    parser.add_argument("--dry-run", action="store_true", help="Report what would be removed without deleting")
    args = parser.parse_args()

    summary = trim_cache(args.default_ttl_days, args.dry_run)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
