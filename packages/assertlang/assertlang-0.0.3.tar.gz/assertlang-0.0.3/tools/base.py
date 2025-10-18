from __future__ import annotations

import json
from importlib import import_module
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import jsonschema
except Exception:  # noqa: BLE001
    jsonschema = None


def _load_schema(name: str) -> Dict[str, Any]:
    path = Path("schemas/tools") / f"{name}.v1.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _validate(name: str, payload: Dict[str, Any]) -> None:
    if jsonschema is None:
        return
    schema = _load_schema(name)
    jsonschema.validate(payload, schema)


def run_tool(name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    _validate(name, payload)
    generated = _run_generated_adapter(name, payload)
    if generated is not None:
        return generated
    return {"ok": False, "version": "v1", "error": {"code": "E_TOOL", "message": f"unknown tool {name}"}}


def _run_generated_adapter(name: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    safe_name = name.replace('-', '_')
    module_name = f"tools.{safe_name}.adapters.adapter_py"
    try:
        module = import_module(module_name)
    except ModuleNotFoundError:
        return None
    handle = getattr(module, "handle", None)
    if handle is None:
        return None
    return handle(payload)
