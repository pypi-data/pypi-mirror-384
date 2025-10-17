from __future__ import annotations

from typing import Any, Dict

from tools.envelope import error, ok

VERSION = 'v1'


def handle(request: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(request, dict):
        return error('E_SCHEMA', 'request must be an object')
    cases = request.get('cases')
    if not isinstance(cases, dict):
        return error('E_ARGS', 'cases must be an object')
    value = str(request.get('value', ''))
    selected = value if value in cases else 'default'
    return ok({'selected': selected})
