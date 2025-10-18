from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from tools.envelope import error, ok

VERSION = 'v1'


def handle(request: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(request, dict):
        return error('E_SCHEMA', 'request must be an object')
    backend = request.get('backend', 'fs')
    if backend != 'fs':
        return error('E_UNSUPPORTED', f'unsupported backend: {backend}')
    op = request.get('op')
    params = request.get('params') or {}
    path_value = params.get('path')
    if not path_value:
        return error('E_ARGS', 'path is required')
    path = Path(path_value)
    if op == 'put':
        content = params.get('content', '')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(str(content), encoding='utf-8')
        return ok({'written': True})
    if op == 'get':
        try:
            content = path.read_text(encoding='utf-8')
        except FileNotFoundError:
            return error('E_RUNTIME', 'file not found')
        return ok({'content': content})
    if op == 'list':
        glob = params.get('glob', '*')
        items = [str(p) for p in path.glob(glob)]
        return ok({'items': items})
    if op == 'delete':
        path.unlink(missing_ok=True)
        return ok({'deleted': True})
    return error('E_ARGS', f'unsupported op: {op}')
