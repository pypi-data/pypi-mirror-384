from __future__ import annotations

from typing import Any, Dict

from tools.envelope import ok

VERSION = 'v1'


def handle(request: Dict[str, Any]) -> Dict[str, Any]:
    return ok({'result': str(request.get('op'))})
