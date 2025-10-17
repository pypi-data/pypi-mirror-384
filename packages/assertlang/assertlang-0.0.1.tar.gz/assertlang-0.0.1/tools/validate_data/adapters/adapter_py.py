from __future__ import annotations

import json
from typing import Any, Dict

import jsonschema

from tools.envelope import error, ok

VERSION = 'v1'


def handle(request: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(request, dict):
        return error('E_SCHEMA', 'request must be an object')

    fmt = request.get('format')
    schema = request.get('schema')
    content = request.get('content')
    if fmt != 'json':
        return error('E_UNSUPPORTED', f'unsupported format: {fmt}')
    if not isinstance(schema, dict) or not isinstance(content, str):
        return error('E_ARGS', 'schema must be an object and content must be a string')

    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        return ok({'valid': False, 'issues': [f'json decode failed: {exc}']})

    try:
        jsonschema.validate(data, schema)
    except jsonschema.ValidationError as exc:
        return ok({'valid': False, 'issues': [exc.message]})
    except jsonschema.SchemaError as exc:
        return error('E_SCHEMA', f'invalid schema: {exc}')

    return ok({'valid': True, 'issues': []})
