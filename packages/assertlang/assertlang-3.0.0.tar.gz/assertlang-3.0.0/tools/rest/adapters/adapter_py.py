from __future__ import annotations

from typing import Any, Dict

import requests

from tools.envelope import error, ok

VERSION = 'v1'


def handle(request: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(request, dict):
        return error('E_SCHEMA', 'request must be an object')

    base = request.get('base')
    path = request.get('path')
    if not isinstance(base, str) or not isinstance(path, str):
        return error('E_PLAN', 'base and path are required strings')

    method = request.get('method', 'GET')
    headers = request.get('headers') or {}
    params = request.get('params') or {}
    body = request.get('body')

    url = base.rstrip('/') + (path if path.startswith('/') else '/' + path)

    try:
        resp = requests.request(method, url, headers=headers, params=params, data=body, timeout=15)
    except Exception as exc:
        return error('E_NETWORK', str(exc))

    try:
        payload = resp.json()
    except ValueError:
        payload = None

    return ok({'status': resp.status_code, 'json': payload, 'text': resp.text})
