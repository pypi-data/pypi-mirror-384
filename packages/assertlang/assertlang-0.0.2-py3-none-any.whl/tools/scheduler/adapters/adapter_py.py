from __future__ import annotations

from typing import Any, Dict

from tools.envelope import error, ok

VERSION = 'v1'


def handle(request: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(request, dict):
        return error('E_SCHEMA', 'request must be an object')
    job = request.get('job')
    if not isinstance(job, str):
        return error('E_ARGS', 'job must be a string')
    return ok({'scheduled': True, 'id': f'sch-{job}'})
