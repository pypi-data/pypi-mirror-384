"""Shared utilities for dependency allowlists and cache management."""

from __future__ import annotations

import json
import os
import shutil
import time
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

CACHE_ROOT = Path(".mcpd") / "cache"
ALLOWLIST_PATH = Path("configs/dependency-allowlist.yaml")
REGISTRY_PATH = Path("data/tools_registry.json")

ALLOWLIST_KEYS = {
    "python": "requirements",
    "node": "packages",
    "nextjs": "packages",
    "go": "modules",
    "dotnet": "packages",
    "rust": "crates",
}

SAFE_KEYS = {"allow", "allowed", "values", "cache_ttl_days"}


def _load_allowlist() -> Dict[str, Any]:
    if not ALLOWLIST_PATH.exists():
        return {}
    with ALLOWLIST_PATH.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    return data if isinstance(data, dict) else {}


def _load_registry() -> Dict[str, Any]:
    if not REGISTRY_PATH.exists():
        return {}
    try:
        with REGISTRY_PATH.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _normalise(entry: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for key in ("requirements", "packages", "modules", "crates"):
        if key in entry:
            data = entry[key]
            if isinstance(data, dict):
                allowed = data.get("allow") or data.get("allowed") or data.get("values")
                if allowed is not None:
                    out[f"{key}.allow"] = allowed
                for sub_key, value in data.items():
                    if sub_key in SAFE_KEYS - {"allow", "allowed", "values"}:
                        out[f"{key}.{sub_key}"] = value
            else:
                out[f"{key}.allow"] = data
    if env := entry.get("env"):
        out["env"] = env
    for extra in ("registry", "feeds", "registries"):
        if extra in entry:
            out[extra] = entry[extra]
    for extra_key in ("cache_ttl_days", "dotnet_root", "module_name"):
        if extra_key in entry:
            out[extra_key] = entry[extra_key]
    return out


def _merge_plan_deps(plan: Dict[str, Any], registry: Dict[str, Any]) -> Dict[str, Any]:
    deps: Dict[str, Any] = {}
    for lang, cfg in (plan.get("deps") or {}).items():
        deps[lang] = cfg if isinstance(cfg, dict) else {ALLOWLIST_KEYS.get(lang, "deps"): cfg}

    tool_id = plan.get("tool")
    plan_lang = plan.get("lang")
    if tool_id and plan_lang and tool_id in registry:
        entry = registry[tool_id]
        for adapter in entry.get("adapters", []):
            if adapter.get("language") != plan_lang:
                continue
            reg_deps = adapter.get("deps") or {}
            candidate = None
            if isinstance(reg_deps, dict) and plan_lang in reg_deps:
                candidate = reg_deps.get(plan_lang)
            elif isinstance(reg_deps, dict):
                candidate = reg_deps
            if candidate is not None:
                existing = deps.get(plan_lang)
                if not existing:
                    deps[plan_lang] = candidate
                elif isinstance(existing, dict) and isinstance(candidate, dict):
                    for key, value in candidate.items():
                        existing.setdefault(key, value)
    return deps


def _allowed_values(allowlist: Dict[str, Any], lang: str) -> Optional[set[str]]:
    entry = allowlist.get(lang)
    if not isinstance(entry, dict):
        return None
    key = ALLOWLIST_KEYS.get(lang)
    if not key:
        return None
    data = entry.get(key)
    if isinstance(data, dict):
        allowed = data.get("allow") or data.get("allowed") or data.get("values")
    else:
        allowed = data
    if allowed is None:
        return None
    if isinstance(allowed, list):
        return {str(v) for v in allowed}
    return {str(allowed)}


def _plan_violations(allowlist: Dict[str, Any], plan_deps: Dict[str, Any]) -> Dict[str, list[str]]:
    violations: Dict[str, list[str]] = {}
    for lang, cfg in plan_deps.items():
        allowed = _allowed_values(allowlist, lang)
        if not allowed:
            continue
        key = ALLOWLIST_KEYS.get(lang)
        if not key:
            continue
        requested: list[str] = []
        if isinstance(cfg, dict):
            raw = cfg.get(key)
        else:
            raw = cfg
        if isinstance(raw, list):
            requested = [str(v) for v in raw]
        elif isinstance(raw, dict):
            requested = [str(v) for v in raw.get("allow", [])]
        else:
            continue
        missing = [
            item
            for item in requested
            if item not in allowed and item.split("@", 1)[0] not in allowed
        ]
        if missing:
            violations[lang] = missing
    return violations


def summarise_allowlist(plan_path: Optional[Path] = None) -> Dict[str, Any]:
    allowlist = _load_allowlist()
    summary = {
        lang: _normalise(entry) for lang, entry in allowlist.items() if isinstance(entry, dict)
    }

    output: Dict[str, Any] = {"allowlist": summary}

    if plan_path:
        with plan_path.open("r", encoding="utf-8") as fh:
            plan = json.load(fh)
        if not isinstance(plan, dict):
            raise ValueError("plan must be a JSON object")
        registry_data = _load_registry()
        if isinstance(registry_data.get("tools"), dict):
            registry_lookup = registry_data["tools"]
        else:
            registry_lookup = registry_data
        plan_deps = _merge_plan_deps(plan, registry_lookup)
        violations = _plan_violations(allowlist, plan_deps)
        output["plan"] = {
            "tool": plan.get("tool"),
            "lang": plan.get("lang"),
            "deps": plan_deps,
            "violations": violations,
        }

    return output


def _flatten_ttl(entry: Any) -> Optional[int]:
    if not isinstance(entry, dict):
        return None
    ttl = entry.get("cache_ttl_days")
    if ttl is None:
        packages = entry.get("packages")
        if isinstance(packages, dict):
            ttl = packages.get("cache_ttl_days")
    try:
        return int(ttl) if ttl is not None else None
    except (TypeError, ValueError):
        return None


def _max_age_seconds(ttl_days: Optional[int], default_days: int) -> int:
    days = ttl_days if ttl_days is not None else default_days
    return max(days, 0) * 24 * 60 * 60


def _dir_size(path: Path) -> int:
    total = 0
    for root, _, files in os.walk(path, onerror=lambda _e: None):
        for name in files:
            try:
                total += Path(root, name).stat().st_size
            except OSError:
                continue
    return total


def trim_cache(default_ttl_days: int, dry_run: bool) -> Dict[str, Any]:
    allowlist = _load_allowlist()
    now = time.time()
    summary: Dict[str, Any] = {"total_removed": 0, "entries": []}

    if not CACHE_ROOT.exists():
        return summary

    for lang_dir in CACHE_ROOT.iterdir():
        if not lang_dir.is_dir():
            continue
        ttl = _flatten_ttl(allowlist.get(lang_dir.name))
        max_age = _max_age_seconds(ttl, default_ttl_days)
        for entry in lang_dir.iterdir():
            if not entry.is_dir():
                continue
            mtime = entry.stat().st_mtime
            age = now - mtime
            entry_size = _dir_size(entry)
            record = {
                "language": lang_dir.name,
                "path": str(entry),
                "age_seconds": age,
                "size_bytes": entry_size,
                "ttl_days": ttl,
                "removed": False,
            }
            if age > max_age:
                record["removed"] = not dry_run
                if not dry_run:
                    shutil.rmtree(entry)
                    summary["total_removed"] += 1
            summary["entries"].append(record)
    return summary
