from __future__ import annotations

from typing import Any, Dict, List

from tools.envelope import error, ok

VERSION = 'v1'


def handle(request: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(request, dict):
        return error('E_SCHEMA', 'request must be an object')
    tasks = request.get('tasks')
    if not isinstance(tasks, list):
        return error('E_ARGS', 'tasks must be an array')
    results: List[Dict[str, Any]] = []
    for idx, task in enumerate(tasks):
        results.append({'index': idx, 'status': 'done', 'result': task})
    return ok({'results': results})
