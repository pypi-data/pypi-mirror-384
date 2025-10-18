from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from tools.envelope import error, ok

VERSION = 'v1'


def handle(request: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(request, dict):
        return error('E_SCHEMA', 'request must be an object')
    name = request.get('name')
    if not isinstance(name, str):
        return error('E_ARGS', 'name must be a string')
    path = Path('schemas/tools') / f"{name}.v1.json"
    if not path.exists():
        path.write_text('{"$schema":"https://json-schema.org/draft/2020-12/schema","type":"object"}', encoding='utf-8')
    return ok({'paths': [str(path)]})
