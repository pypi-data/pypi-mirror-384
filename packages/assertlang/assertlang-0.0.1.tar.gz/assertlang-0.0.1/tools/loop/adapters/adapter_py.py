from __future__ import annotations

from typing import Any, Dict

from tools.envelope import error, ok

VERSION = 'v1'


def handle(request: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(request, dict):
        return error('E_SCHEMA', 'request must be an object')
    items = request.get('items')
    if not isinstance(items, list):
        return error('E_ARGS', 'items must be a list')
    return ok({'iterations': len(items)})
