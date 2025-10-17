from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from tools.envelope import error, ok

VERSION = 'v1'


def handle(request: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(request, dict):
        return error('E_SCHEMA', 'request must be an object')
    target = request.get('target')
    if target not in {'stdout', 'file'}:
        return error('E_ARGS', 'target must be stdout or file')
    content = request.get('content', '')
    if target == 'stdout':
        print(str(content))
        return ok({'written': True})
    path = request.get('path')
    if not isinstance(path, str) or not path:
        return error('E_ARGS', 'path is required for file target')
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(str(content), encoding='utf-8')
    return ok({'written': True, 'path': str(file_path)})
