from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from tools.envelope import error, ok

VERSION = 'v1'


def handle(request: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(request, dict):
        return error('E_SCHEMA', 'request must be an object')
    task_id = request.get('task_id')
    if not isinstance(task_id, str):
        return error('E_ARGS', 'task_id must be a string')
    base = Path('.mcpd') / task_id
    logs = []
    if base.exists():
        for p in base.rglob('*.log'):
            try:
                lines = p.read_text(encoding='utf-8').splitlines()
                logs.append({'file': str(p), 'last': lines[-1:]})
            except Exception:
                continue
    return ok({'errors': [], 'summary': '', 'logs': logs})
