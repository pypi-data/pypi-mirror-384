from __future__ import annotations

import re
from typing import Any, Dict

from tools.envelope import error, ok

VERSION = 'v1'


def handle(request: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(request, dict):
        return error('E_SCHEMA', 'request must be an object')

    left = str(request.get('left', ''))
    op = request.get('op')
    right = str(request.get('right', ''))
    if not isinstance(op, str):
        return error('E_ARGS', 'op is required')

    if op == '==':
        result = left == right
    elif op == '!=':
        result = left != right
    elif op == 'regex':
        try:
            result = re.search(right, left) is not None
        except re.error as exc:
            return error('E_RUNTIME', f'regex error: {exc}')
    else:
        return error('E_ARGS', f'unsupported operator: {op}')

    return ok({'pass': result})
