import json
import os
import subprocess
import sys
import threading
from pathlib import Path


def ok(data: dict) -> None:
    print(json.dumps({"ok": True, "version": "v1", "data": data}))


def err(code: str, message: str) -> None:
    print(json.dumps({"ok": False, "version": "v1", "error": {"code": code, "message": message}}))


def pump(stream, log_path: str) -> None:
    try:
        Path(log_path).parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, "ab", buffering=0) as fh:
            while True:
                chunk = stream.readline()
                if not chunk:
                    break
                if isinstance(chunk, str):
                    chunk = chunk.encode("utf-8", errors="ignore")
                fh.write(chunk)
    except Exception:
        pass


def main() -> None:
    raw = sys.stdin.read()
    try:
        req = json.loads(raw or "{}")
    except Exception as exc:  # noqa: BLE001
        err("E_JSON", str(exc))
        return

    method = req.get("method")
    if method == "apply":
        target_dir = Path(req.get("target_dir") or ".")
        files = req.get("files") or []
        try:
            writes = 0
            for spec in files:
                path = target_dir / spec["path"]
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(spec.get("content", ""), encoding="utf-8")
                mode = spec.get("mode")
                if isinstance(mode, int):
                    os.chmod(path, mode)
                writes += 1
            ok({"writes": writes, "target": str(target_dir)})
        except Exception as exc:  # noqa: BLE001
            err("E_FS", str(exc))
        return

    if method == "start":
        cmd = req.get("cmd")
        cwd = req.get("cwd") or "."
        port = int(req.get("port") or 0)
        extra_env = req.get("env") or {}
        log_path = req.get("log_path") or "run.log"
        try:
            env = os.environ.copy()
            env.update(extra_env)
            env["PORT"] = str(port)
            proc = subprocess.Popen(
                ["bash", "-lc", cmd],
                cwd=cwd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                start_new_session=True,
            )
            t1 = threading.Thread(target=pump, args=(proc.stdout, log_path), daemon=True)
            t2 = threading.Thread(target=pump, args=(proc.stderr, log_path), daemon=True)
            t1.start()
            t2.start()
            ok({"pid": proc.pid})
        except Exception as exc:  # noqa: BLE001
            err("E_RUNTIME", str(exc))
        return

    if method == "stop":
        pid = int(req.get("pid") or 0)
        try:
            if pid:
                os.kill(pid, 15)
            ok({"stopped": True})
        except Exception as exc:  # noqa: BLE001
            err("E_RUNTIME", str(exc))
        return

    if method == "health":
        import socket

        host = req.get("host") or "127.0.0.1"
        port = int(req.get("port") or 0)
        try:
            with socket.create_connection((host, port), timeout=1.0):
                ok({"ready": True})
        except Exception:  # noqa: BLE001
            ok({"ready": False})
        return

    err("E_METHOD", "unknown method")


if __name__ == "__main__":
    main()
