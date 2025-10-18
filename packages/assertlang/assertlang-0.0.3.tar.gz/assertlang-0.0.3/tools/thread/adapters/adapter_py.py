from __future__ import annotations

from typing import Any, Dict

from tools.envelope import error, ok

VERSION = 'v1'


def handle(request: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(request, dict):
        return error('E_SCHEMA', 'request must be an object')
    tasks = request.get('tasks')
    if not isinstance(tasks, list):
        return error('E_ARGS', 'tasks must be a list')
    return ok({'results': [True for _ in tasks], 'duration_ms': 0})
