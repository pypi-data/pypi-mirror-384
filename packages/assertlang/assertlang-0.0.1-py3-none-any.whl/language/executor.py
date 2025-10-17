from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import yaml  # type: ignore

from daemon.mcpd import MCPDaemon
from language.interpreter import ActionExecutor
from language.parser import PWProgram, parse_pw


def load_pw(path: Path) -> Dict[str, Any] | None:
    text = path.read_text(encoding="utf-8")
    try:
        data = yaml.safe_load(text)
        if isinstance(data, dict):
            return data
    except Exception:
        return None
    return None


def execute_pw_file(path: str) -> Dict[str, Any]:
    p = Path(path)
    spec = load_pw(p)
    if not spec:
        prog = parse_pw(p.read_text(encoding="utf-8"))
        if prog.plan:
            plan_payload = prog.plan
            if plan_payload.get("actions") and not plan_payload.get("files"):
                executor = ActionExecutor(plan_payload.get("tools", {}))
                responses = executor.execute(plan_payload.get("actions", []))
                plan_result = {"ok": True, "version": "v1", "data": plan_payload}
                return {
                    "ok": True,
                    "mode": "interpreter",
                    "plan": plan_result,
                    "responses": responses,
                    "events": executor.events,
                }
            return execute_plan(prog)
        return execute_prompt(prog.prompt or "")

    prompt = (
        spec.get("plan", {}).get("prompt")
        if isinstance(spec.get("plan"), dict)
        else spec.get("prompt")
    )
    lang = spec.get("run", {}).get("lang") if isinstance(spec.get("run"), dict) else spec.get("lang")
    if lang not in {None, "python", "node"}:
        lang = "python"

    d = MCPDaemon()
    d.start()
    if prompt and isinstance(prompt, str):
        plan = d.plan_create_v1(prompt, lang=lang or "python")
    else:
        plan = d.plan_create_v1("hello", lang=lang or "python")
    plan_data = plan.get("data", {}) if isinstance(plan, dict) else {}
    start = d.run_start_v1(plan_data, lang=lang or "python")
    if not start.get("ok"):
        return {"plan": plan, "start": start}
    task_id = start["data"]["task_id"]
    check = d.httpcheck_assert_v1(task_id, "/", 200)
    report = d.report_finish_v1(
        task_id,
        verdict="pass" if check.get("data", {}).get("pass") else "fail",
    )
    return {"plan": plan, "start": start, "check": check, "report": report}


def execute_prompt(prompt: str) -> Dict[str, Any]:
    d = MCPDaemon()
    d.start()
    plan = d.plan_create_v1(prompt, lang="python")
    plan_data = plan.get("data", {}) if isinstance(plan, dict) else {}
    start = d.run_start_v1(plan_data, lang="python")
    if not start.get("ok"):
        return {"plan": plan, "start": start}
    task_id = start["data"]["task_id"]
    check = d.httpcheck_assert_v1(task_id, "/", 200)
    report = d.report_finish_v1(
        task_id,
        verdict="pass" if check.get("data", {}).get("pass") else "fail",
    )
    return {"plan": plan, "start": start, "check": check, "report": report}


def execute_plan(prog: PWProgram) -> Dict[str, Any]:
    if not prog.plan:
        raise ValueError("Program has no plan to execute")
    plan_payload = prog.plan.copy()
    lang = plan_payload.get("lang", "python")
    d = MCPDaemon()
    d.start()
    plan_result = {"ok": True, "version": "v1", "data": plan_payload}
    start = d.run_start_v1(plan_payload, lang=lang)
    if not start.get("ok"):
        return {"plan": plan_result, "start": start}
    task_id = start["data"]["task_id"]
    check = d.httpcheck_assert_v1(task_id, "/", 200)
    report = d.report_finish_v1(
        task_id,
        verdict="pass" if check.get("data", {}).get("pass") else "fail",
    )
    return {"plan": plan_result, "start": start, "check": check, "report": report}

