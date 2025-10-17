from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


def scaffold_tool(tool: str, version: str, spec_dir: str = "schemas/tools") -> Dict[str, Any]:
    spec_path = Path(spec_dir) / f"{tool}.v1.json"
    if not spec_path.exists():
        raise FileNotFoundError(f"schema not found for tool: {tool}")
    schema = json.loads(spec_path.read_text(encoding="utf-8"))
    out_dir = Path("tools") / tool
    out_dir.mkdir(parents=True, exist_ok=True)
    # Minimal Python adapter scaffold
    adapter_py = out_dir / "adapter.py"
    if not adapter_py.exists():
        adapter_py.write_text(
            """
from __future__ import annotations

from typing import Dict, Any


def handle(request: Dict[str, Any]) -> Dict[str, Any]:
    # TODO: implement tool logic
    return {"ok": True, "version": "v1", "data": {}}
""".lstrip(),
            encoding="utf-8",
        )
    return {"schema": schema, "adapter_path": str(adapter_py)}




