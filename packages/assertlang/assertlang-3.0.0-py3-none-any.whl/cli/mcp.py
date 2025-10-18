import json
import shutil
import sys
import webbrowser
from pathlib import Path

import click

from cli.toolgen import toolgen as toolgen_command
from daemon.mcpd import MCPDaemon

REGISTRY_PATH = Path(__file__).resolve().parents[1] / "data" / "tools_registry.json"
if REGISTRY_PATH.exists():
    try:
        TOOL_REGISTRY = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    except Exception:  # pragma: no cover - fallback on malformed registry
        TOOL_REGISTRY = {"tools": {}}
else:
    TOOL_REGISTRY = {"tools": {}}


@click.group()
def main() -> None:
    pass


main.add_command(toolgen_command, name="toolgen")


@main.command("tools")
def list_tools() -> None:
    click.echo(
        json.dumps({"ok": True, "version": "v1", "data": TOOL_REGISTRY.get("tools", {})}, indent=2)
    )


@main.command()
@click.argument("prompt")
@click.option("--hold", is_flag=True, help="Keep gateway alive after success until Ctrl+C")
@click.option(
    "--lang",
    type=click.Choice(["python", "node", "nextjs", "go", "rust", "java", ".net", "cpp"]),
    default="python",
    help="Language runner to use",
)
def run(prompt: str, hold: bool, lang: str) -> None:
    d = MCPDaemon()
    d.start()
    plan = d.plan_create_v1(prompt, lang=lang)
    plan_data = plan.get("data", {}) if isinstance(plan, dict) else {}
    start = d.run_start_v1(plan_data, lang=lang)
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
        finally:
            # Try to stop the task process and free routing
            try:
                d.stop_task(task_id)
            except Exception:
                pass


@main.command()
def list() -> None:  # noqa: A003 - intentional name per spec
    root = Path(".mcpd")
    items = []
    if root.exists():
        for p in root.iterdir():
            if p.is_dir():
                items.append(p.name)
    click.echo(json.dumps({"ok": True, "version": "v1", "data": {"tasks": items}}))


@main.command()
@click.argument("task_id")
def kill(task_id: str) -> None:
    d = MCPDaemon()
    d.start()
    d.stop_task(task_id)
    click.echo(json.dumps({"ok": True, "version": "v1", "data": {"killed": task_id}}))


@main.command()
@click.argument("task_id")
def open(task_id: str) -> None:  # noqa: A003
    url = f"http://127.0.0.1:23456/apps/{task_id}/"
    webbrowser.open(url)
    click.echo(json.dumps({"ok": True, "version": "v1", "data": {"url": url}}))


@main.command()
@click.argument("task_id")
@click.argument("dest")
def export(task_id: str, dest: str) -> None:
    src = Path(".mcpd") / task_id / "source"
    if not src.exists():
        click.echo(
            json.dumps(
                {
                    "ok": False,
                    "version": "v1",
                    "error": {"code": "E_ARGS", "message": "unknown task_id"},
                }
            )
        )
        sys.exit(1)
    dest_path = Path(dest)
    dest_path.mkdir(parents=True, exist_ok=True)
    for p in src.rglob("*"):
        if p.is_file():
            rel = p.relative_to(src)
            out = dest_path / rel
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, out)
    click.echo(
        json.dumps(
            {"ok": True, "version": "v1", "data": {"exported": task_id, "dest": str(dest_path)}}
        )
    )


if __name__ == "__main__":
    main()
