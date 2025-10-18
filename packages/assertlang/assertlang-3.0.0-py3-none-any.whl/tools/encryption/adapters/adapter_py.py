from __future__ import annotations

import hashlib
from typing import Any, Dict

from tools.envelope import error, ok

VERSION = 'v1'


def handle(request: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(request, dict):
        return error('E_SCHEMA', 'request must be an object')
    if request.get('op') != 'hash' or request.get('alg') != 'sha256':
        return error('E_UNSUPPORTED', 'only sha256 hash supported')
    data = request.get('data')
    if not isinstance(data, str):
        return error('E_ARGS', 'data must be a string')
    digest = hashlib.sha256(data.encode('utf-8')).hexdigest()
    return ok({'result': digest})
