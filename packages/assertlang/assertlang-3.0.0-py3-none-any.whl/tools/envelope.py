from __future__ import annotations

from typing import Any, Dict

DEFAULT_VERSION = "v1"


def ok(data: Dict[str, Any] | None = None, version: str = DEFAULT_VERSION) -> Dict[str, Any]:
    return {"ok": True, "version": version, "data": data or {}}


def error(code: str, message: str, details: Dict[str, Any] | None = None, version: str = DEFAULT_VERSION) -> Dict[str, Any]:
    err = {"code": code, "message": message}
    if details:
        err["details"] = details
    return {"ok": False, "version": version, "error": err}


def validate_request(req: Dict[str, Any]) -> Dict[str, Any] | None:  # placeholder schema validation
    # TODO: integrate jsonschema validation against tool schemas
    if not isinstance(req, dict):
        return error("E_SCHEMA", "request must be an object")
    return None




