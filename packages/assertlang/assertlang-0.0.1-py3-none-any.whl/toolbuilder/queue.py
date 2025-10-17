from __future__ import annotations

import secrets
from typing import List, Optional

from .models import ARTIFACT_ROOT, ToolJob, ensure_dirs


def enqueue(tool: str, version: str, payload: dict) -> ToolJob:
    ensure_dirs()
    job_id = secrets.token_hex(6)
    job = ToolJob(job_id=job_id, tool_name=tool, version=version, payload=payload)
    (ARTIFACT_ROOT / "jobs" / f"{job_id}.json").write_text(job.to_json(), encoding="utf-8")
    return job


def list_jobs() -> List[ToolJob]:
    ensure_dirs()
    jobs: List[ToolJob] = []
    for p in (ARTIFACT_ROOT / "jobs").glob("*.json"):
        try:
            jobs.append(ToolJob.from_json(p.read_text(encoding="utf-8")))
        except Exception:
            continue
    return sorted(jobs, key=lambda j: j.job_id, reverse=True)


def get_job(job_id: str) -> Optional[ToolJob]:
    p = ARTIFACT_ROOT / "jobs" / f"{job_id}.json"
    if not p.exists():
        return None
    return ToolJob.from_json(p.read_text(encoding="utf-8"))


def update_job(job: ToolJob) -> None:
    (ARTIFACT_ROOT / "jobs" / f"{job.job_id}.json").write_text(job.to_json(), encoding="utf-8")




