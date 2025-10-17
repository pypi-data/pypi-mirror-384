from __future__ import annotations

import time
from typing import Optional

from .codegen import generate as codegen_generate
from .models import ARTIFACT_ROOT, JobStatus, ToolJob, ensure_dirs
from .provider import get_provider
from .queue import list_jobs, update_job
from .scaffold import scaffold_tool


def _log(job: ToolJob, msg: str) -> None:
    ensure_dirs()
    log = ARTIFACT_ROOT / "logs" / f"{job.job_id}.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("a", encoding="utf-8") as f:
        f.write(msg + "\n")


def process_one(provider_name: str = "anthropic") -> Optional[ToolJob]:
    for job in list_jobs():
        if job.status != JobStatus.pending:
            continue
        job.status = JobStatus.running
        update_job(job)
        try:
            _log(job, f"scaffolding {job.tool_name} v{job.version}")
            sc = scaffold_tool(job.tool_name, job.version)
            _log(job, f"codegen adapters for {job.tool_name}")
            codegen_generate(job.tool_name)
            prov = get_provider(provider_name)
            _ = prov.generate("implement tool", {"tool": job.tool_name, "version": job.version, "schema": sc["schema"]})
            job.status = JobStatus.succeeded
            update_job(job)
            _log(job, "done")
            return job
        except Exception as ex:  # noqa: BLE001
            job.status = JobStatus.failed
            job.error = str(ex)
            update_job(job)
            _log(job, f"error: {ex}")
            return job
    return None


def run_loop(provider_name: str = "anthropic", interval_sec: int = 2) -> None:
    ensure_dirs()
    while True:
        found = process_one(provider_name)
        if not found:
            time.sleep(interval_sec)


