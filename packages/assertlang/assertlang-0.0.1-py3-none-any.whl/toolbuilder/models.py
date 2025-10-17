from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional


class JobStatus(str, Enum):
    pending = "pending"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"


@dataclass
class ToolJob:
    job_id: str
    tool_name: str
    version: str
    payload: Dict[str, Any]
    status: JobStatus = JobStatus.pending
    error: Optional[str] = None

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)

    @staticmethod
    def from_json(s: str) -> ToolJob:
        data = json.loads(s)
        data["status"] = JobStatus(data.get("status", JobStatus.pending))
        return ToolJob(**data)


ARTIFACT_ROOT = Path(".mcpd") / "toolbuilder"

def ensure_dirs() -> Path:
    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    (ARTIFACT_ROOT / "jobs").mkdir(parents=True, exist_ok=True)
    (ARTIFACT_ROOT / "logs").mkdir(parents=True, exist_ok=True)
    return ARTIFACT_ROOT




