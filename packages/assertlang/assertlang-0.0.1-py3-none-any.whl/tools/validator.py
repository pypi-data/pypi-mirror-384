from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Tuple

from jsonschema import Draft202012Validator


def validate_with_schema(schema_path: Path, instance: Dict[str, Any]) -> Tuple[bool, str | None]:
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        validator = Draft202012Validator(schema)
        errors = sorted(validator.iter_errors(instance), key=lambda e: e.path)
        if errors:
            first = errors[0]
            return False, f"{list(first.path)}: {first.message}"
        return True, None
    except Exception as ex:  # noqa: BLE001
        return False, str(ex)




