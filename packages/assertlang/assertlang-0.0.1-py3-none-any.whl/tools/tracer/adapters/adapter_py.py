from __future__ import annotations

from typing import Any, Dict

from tools.envelope import error, ok

VERSION = 'v1'


def handle(request: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(request, dict):
        return error('E_SCHEMA', 'request must be an object')
    op = request.get('op')
    kind = request.get('kind')
    if not isinstance(op, str) or not isinstance(kind, str):
        return error('E_ARGS', 'op and kind must be strings')
    return ok({'trace_id': f"{kind}-{op}"})
