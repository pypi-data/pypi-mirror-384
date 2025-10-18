from __future__ import annotations

import time
from typing import Any, Dict

from tools.envelope import error, ok

VERSION = 'v1'


def handle(request: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(request, dict):
        return error('E_SCHEMA', 'request must be an object')
    if request.get('op') != 'sleep':
        return error('E_UNSUPPORTED', 'only sleep supported')
    ms = request.get('ms')
    if not isinstance(ms, int) or ms < 0:
        return error('E_ARGS', 'ms must be a non-negative integer')
    start = time.time()
    time.sleep(ms / 1000)
    elapsed = int((time.time() - start) * 1000)
    return ok({'elapsed_ms': elapsed})
