from __future__ import annotations

from typing import Any, Dict

from tools.envelope import error, ok

VERSION = 'v1'


def handle(request: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(request, dict):
        return error('E_SCHEMA', 'request must be an object')

    auth_type = request.get('type')
    token = request.get('token')
    if not isinstance(auth_type, str) or not isinstance(token, str):
        return error('E_ARGS', 'type and token are required strings')

    header = request.get('header', 'Authorization') or 'Authorization'
    prefix = request.get('prefix', 'Bearer ')

    if auth_type not in {'apiKey', 'jwt'}:
        return error('E_UNSUPPORTED', f'unsupported auth type: {auth_type}')

    value = f"{prefix}{token}" if prefix else token
    return ok({'headers': {header: value}})
