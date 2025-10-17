from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from tools.envelope import error, ok, validate_request
from tools.validator import validate_with_schema

VERSION = 'v1'

# Capability discovery: tools can advertise supported versions/features
def capabilities() -> Dict[str, Any]:
    return {
        'tool': 'api-auth',
        'versions': ['v1'],
        'features': ['validation', 'envelope', 'idempotency'],
    }


def handle(request: Dict[str, Any]) -> Dict[str, Any]:
    # Envelope + schema validation (extend with jsonschema against schema.v1.json)
    err = validate_request(request)
    if err:
        return err
    # Optional: idempotency support
    _idempotency_key = request.get('idempotency_key')
    valid, emsg = validate_with_schema(Path(__file__).parent.parent / 'api-auth' / 'schema.v1.json', request)
    if not valid:
        return error('E_SCHEMA', emsg or 'invalid request')
    try:
        # TODO: implement tool logic using request['data'] per schema
        return ok({})
    except Exception as ex:  # noqa: BLE001
        return error('E_RUNTIME', str(ex))
