from __future__ import annotations

import json
from typing import Any, Dict

from tools.envelope import ok

VERSION = 'v1'


def handle(request: Dict[str, Any]) -> Dict[str, Any]:
    level = request.get('level', 'info').upper()
    message = request.get('message', '')
    context = request.get('context') or {}
    print(f"[{level}] {message} {json.dumps(context)}")
    return ok({'logged': True})
