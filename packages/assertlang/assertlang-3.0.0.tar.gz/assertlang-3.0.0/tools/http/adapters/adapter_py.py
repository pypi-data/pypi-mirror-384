from __future__ import annotations

from typing import Any, Dict

import requests

from tools.envelope import error, ok

VERSION = 'v1'


def handle(request: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(request, dict):
        return error('E_SCHEMA', 'request must be a JSON object')
    method = request.get('method', 'GET')
    url = request.get('url')
    if not url:
        return error('E_ARGS', 'url is required')
    headers = request.get('headers') or {}
    body = request.get('body')
    timeout = float(request.get('timeout_sec', 30))
    try:
        resp = requests.request(method, url, headers=headers, data=body, timeout=timeout)
    except Exception as exc:
        return error('E_NETWORK', str(exc))
    return ok({'status': resp.status_code, 'headers': dict(resp.headers), 'body': resp.text})
