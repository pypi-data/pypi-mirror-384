from __future__ import annotations

import json
from typing import Any, Dict

import yaml

from tools.envelope import error, ok

VERSION = 'v1'


def handle(request: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(request, dict):
        return error('E_SCHEMA', 'request must be an object')
    source = request.get('from')
    target = request.get('to')
    content = request.get('content', '')
    if source not in {'json', 'yaml'} or target not in {'json', 'yaml'}:
        return error('E_ARGS', "from/to must be 'json' or 'yaml'")
    try:
        if source == 'json':
            data = json.loads(str(content))
        else:
            data = yaml.safe_load(str(content))
    except Exception as exc:  # noqa: BLE001
        return error('E_RUNTIME', str(exc))

    try:
        if target == 'json':
            converted = json.dumps(data, indent=2)
        else:
            converted = yaml.safe_dump(data, sort_keys=False)
    except Exception as exc:  # noqa: BLE001
        return error('E_RUNTIME', str(exc))

    return ok({'content': converted})
