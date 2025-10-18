from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from tools.envelope import error, ok

VERSION = 'v1'


def handle(request: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(request, dict):
        return error('E_SCHEMA', 'request must be an object')
    artifact = request.get('artifact')
    if not isinstance(artifact, str) or not Path(artifact).exists():
        return error('E_ARGS', 'artifact missing')
    tool = request.get('tool')
    version = request.get('version')
    return ok({'url': f"https://market.local/{tool}:{version}"})
