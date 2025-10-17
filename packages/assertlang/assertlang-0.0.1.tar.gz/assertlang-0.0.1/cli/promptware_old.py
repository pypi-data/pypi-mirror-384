import json
import sys
from pathlib import Path

import click

from daemon.deps_utils import summarise_allowlist, trim_cache
from daemon.mcpd import MCPDaemon
from language.dsl_utils import collect_pw_files, format_text, lint_text
from language.executor import execute_pw_file
from language.parser import parse_pw
from toolbuilder.codegen import generate as codegen_generate
from toolbuilder.codegen import generate_all as codegen_generate_all
from toolbuilder.queue import enqueue, list_jobs
from toolbuilder.worker import run_loop
from tools import run_tool


def _load_prompt(arg: str) -> str:
    p = Path(arg)
    if p.suffix == ".al" and p.exists():
        prog = parse_pw(p.read_text(encoding="utf-8"))
        return prog.prompt
    return arg


@click.group()
def main() -> None:
    pass


@main.command()
@click.argument("source")
@click.option("--hold", is_flag=True, help="Keep gateway alive after success until Ctrl+C")
def run(source: str, hold: bool) -> None:
    p = Path(source)
    if p.suffix == ".al" and p.exists():
        res = execute_pw_file(str(p))
        if res.get("mode") == "interpreter":
            ok = bool(res.get("ok"))
            click.echo("✅ PASS (interpreter)" if ok else "❌ FAIL (interpreter)")
            click.echo(json.dumps(res, indent=2, sort_keys=True))
            return
        plan, start, check, report = (
            res.get("plan"),
            res.get("start"),
            res.get("check"),
            res.get("report"),
        )
        passed = bool(check and check.get("ok") and check.get("data", {}).get("pass"))
        task_id = start.get("data", {}).get("task_id") if start else None
        if passed and task_id:
            click.echo(f"✅ PASS: http://127.0.0.1:23456/apps/{task_id}/")
        else:
            click.echo("❌ FAIL")
        res["ok"] = passed
        click.echo(json.dumps(res, indent=2, sort_keys=True))
        return
    prompt = _load_prompt(source)
    d = MCPDaemon()
    d.start()
    plan = d.plan_create_v1(prompt)
    plan_data = plan.get("data", {}) if isinstance(plan, dict) else {}
    start = d.run_start_v1(plan_data)
    if not start.get("ok"):
        click.echo(json.dumps(start))
        sys.exit(1)
    task_id = start["data"]["task_id"]
    check = d.httpcheck_assert_v1(task_id, "/", 200)
    passed = bool(check.get("ok") and check.get("data", {}).get("pass"))
    report = d.report_finish_v1(task_id, verdict="pass" if passed else "fail")
    gateway_port = getattr(d, "gateway_port", None)
    host = start.get("data", {}).get("host", "127.0.0.1")
    port = start.get("data", {}).get("port")
    if passed:
        if gateway_port:
            click.echo(f"✅ PASS: http://127.0.0.1:{gateway_port}/apps/{task_id}/")
        elif port:
            click.echo(f"✅ PASS: http://{host}:{port}/")
        else:
            click.echo("✅ PASS")
    else:
        click.echo("❌ FAIL")
    click.echo(
        json.dumps({"plan": plan, "start": start, "check": check, "report": report}, indent=2)
    )

    if passed and hold:
        click.echo("Holding gateway on port 23456. Press Ctrl+C to stop.")
        try:
            import time

            while True:
                time.sleep(3600)
        except KeyboardInterrupt:
            pass


@main.command()
@click.argument("tool")
@click.argument("payload", required=False)
@click.option("--file", "payload_file", type=click.Path(exists=True), help="JSON payload file")
def tool(tool: str, payload: str | None, payload_file: str | None) -> None:  # noqa: A002
    """Run a Promptware tool directly (e.g., http)."""
    import json as _json

    data = {}
    if payload_file:
        from pathlib import Path as _P

        data = _json.loads(_P(payload_file).read_text(encoding="utf-8"))
    elif payload:
        data = _json.loads(payload)
    res = run_tool(tool, data)
    click.echo(_json.dumps(res, indent=2))


@main.group()
def tools() -> None:
    pass


@tools.command()
@click.argument("tool")
@click.option("--version", default="v1")
@click.option("--payload", default="{}")
def enqueue(tool: str, version: str, payload: str) -> None:  # noqa: A002
    data = json.loads(payload)
    job = enqueue(tool, version, data)
    click.echo(json.dumps({"ok": True, "job_id": job.job_id}))


@tools.command()
@click.option("--provider", default="anthropic")
@click.option("--interval", default=2, type=int)
def worker(provider: str, interval: int) -> None:
    run_loop(provider, interval)


@tools.command()
def status() -> None:
    jobs = list_jobs()
    click.echo(json.dumps({"ok": True, "jobs": [j.__dict__ for j in jobs]}, indent=2))


@tools.command()
@click.argument("job_id")
def logs(job_id: str) -> None:
    from toolbuilder.models import ARTIFACT_ROOT

    p = ARTIFACT_ROOT / "logs" / f"{job_id}.log"
    if p.exists():
        click.echo(p.read_text(encoding="utf-8"))
    else:
        click.echo("")


@tools.command()
@click.argument("tool")
def gen(tool: str) -> None:  # noqa: A002
    res = codegen_generate(tool)
    click.echo(json.dumps({"ok": True, "generated": res}, indent=2))


@tools.command("gen-all")
def gen_all() -> None:
    res = codegen_generate_all()
    click.echo(json.dumps({"ok": True, "generated": res}, indent=2))


@main.group()
def deps() -> None:
    """Inspect dependency policies and caches."""


@deps.command("check")
@click.option("--plan", type=click.Path(exists=True, dir_okay=False, path_type=Path))
def deps_check(plan: Path | None) -> None:
    """Show allowlisted dependencies (and merged plan view)."""
    result = summarise_allowlist(plan)
    click.echo(json.dumps(result, indent=2, sort_keys=True))


@deps.command("trim-cache")
@click.option("--default-ttl-days", default=30, show_default=True, type=int)
@click.option("--dry-run", is_flag=True, help="Report removals without deleting")
def deps_trim_cache(default_ttl_days: int, dry_run: bool) -> None:
    """Trim `.mcpd/cache` directories using allowlist TTL hints."""
    summary = trim_cache(default_ttl_days, dry_run)
    click.echo(json.dumps(summary, indent=2, sort_keys=True))


@main.group()
def dsl() -> None:
    """Promptware DSL helpers."""


@dsl.command("format")
@click.argument("paths", nargs=-1, type=click.Path())
@click.option("--check", is_flag=True, help="Only verify formatting")
def dsl_format(paths: tuple[str, ...], check: bool) -> None:
    files = collect_pw_files(paths)
    if not files:
        click.echo("No .al files found", err=True)
        sys.exit(1)
    changed = False
    for path in files:
        original = Path(path).read_text(encoding="utf-8")
        formatted = format_text(original)
        if formatted != original:
            changed = True
            if check:
                click.echo(f"Would reformat {path}")
            else:
                Path(path).write_text(formatted, encoding="utf-8")
                click.echo(f"Reformatted {path}")
    if check and changed:
        sys.exit(1)


@dsl.command("lint")
@click.argument("paths", nargs=-1, type=click.Path())
def dsl_lint(paths: tuple[str, ...]) -> None:
    files = collect_pw_files(paths)
    if not files:
        click.echo("No .al files found", err=True)
        sys.exit(1)
    warnings: list[str] = []
    for path in files:
        text = Path(path).read_text(encoding="utf-8")
        warnings.extend(lint_text(Path(path), text))
    if warnings:
        for message in warnings:
            click.echo(message)
        sys.exit(1)
    click.echo("No issues found.")


if __name__ == "__main__":
    main()
