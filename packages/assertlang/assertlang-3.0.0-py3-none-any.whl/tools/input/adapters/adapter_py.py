from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from tools.envelope import error, ok

VERSION = 'v1'


def handle(request: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(request, dict):
        return error('E_SCHEMA', 'request must be an object')
    if request.get('source') != 'file':
        return error('E_UNSUPPORTED', 'only file source supported')
    path = request.get('path')
    if not isinstance(path, str):
        return error('E_ARGS', 'path must be a string')
    encoding = request.get('encoding', 'utf-8')
    try:
        content = Path(path).read_text(encoding=encoding)
    except FileNotFoundError:
        return error('E_RUNTIME', 'file not found')
    return ok({'content': content})
