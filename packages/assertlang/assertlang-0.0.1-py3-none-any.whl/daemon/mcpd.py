import hashlib
import html
import json
import os
import random
import secrets
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml

# Import DSL parser
try:
    from language.parser import parse_pw
except ImportError:
    parse_pw = None  # Fallback if not available

from .deps_utils import trim_cache

ALLOWLIST_KEYS = {
    "python": "requirements",
    "node": "packages",
    "nextjs": "packages",
    "go": "modules",
    "dotnet": "packages",
    "rust": "crates",
}

from .gateway import Gateway


class DependencyError(RuntimeError):
    """Raised when dependency preparation fails."""


class DependencyPolicyError(DependencyError):
    """Raised when requested dependencies violate allowlists."""


ARTIFACT_ROOT = Path(".mcpd")
CACHE_ROOT = ARTIFACT_ROOT / "cache"
DEFAULT_SOCKET_DIR = (
    Path("/run/mcpd/sock")
    if sys.platform != "win32"
    else Path(tempfile.gettempdir(), "mcpd", "sock")
)


@lru_cache(maxsize=1)
def _load_tool_registry() -> Dict[str, Dict[str, Any]]:
    registry_path = Path("data/tools_registry.json")
    if not registry_path.exists():
        return {}
    try:
        with registry_path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
    except Exception:
        return {}
    tools = data.get("tools")
    return tools if isinstance(tools, dict) else {}


@lru_cache(maxsize=1)
def _load_dependency_allowlist() -> Dict[str, Dict[str, Any]]:
    allowlist_path = Path("configs/dependency-allowlist.yaml")
    if not allowlist_path.exists():
        return {}
    try:
        with allowlist_path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


@dataclass
class Task:
    task_id: str
    dir: Path
    socket_path: Path
    pid: Optional[int] = None
    port: Optional[int] = None
    events: List[Dict[str, Any]] = field(default_factory=list)


class MCPDaemon:
    def __init__(self) -> None:
        self.gateway = Gateway()
        self.tasks: Dict[str, Task] = {}
        self.run_socket_dir: Path = DEFAULT_SOCKET_DIR
        self._tool_registry = _load_tool_registry()
        self._dependency_allowlist = _load_dependency_allowlist()
        self._leases: Dict[int, float] = {}
        self.gateway_port: Optional[int] = None
        self.gateway_available: bool = False

    def ensure_dirs(self) -> None:
        ARTIFACT_ROOT.mkdir(exist_ok=True)
        CACHE_ROOT.mkdir(parents=True, exist_ok=True)
        # Ensure socket dir, with fallback to /tmp if /run is not writable.
        try:
            self.run_socket_dir.mkdir(parents=True, exist_ok=True)
        except OSError:
            fallback = Path(tempfile.gettempdir()) / "mcpd" / "sock"
            fallback.mkdir(parents=True, exist_ok=True)
            self.run_socket_dir = fallback

    def start(self) -> None:
        self.ensure_dirs()
        self._trim_dependency_cache()
        self.gateway.start()
        self.gateway_available = self.gateway.is_available
        self.gateway_port = self.gateway.bound_port if self.gateway_available else None

    def _enforce_allowlist(self, lang: str, values: list[str]) -> None:
        if not values:
            return
        allow = self._dependency_allowlist.get(lang)
        if not allow:
            return
        key = ALLOWLIST_KEYS.get(lang)
        if not key:
            return
        entry = allow.get(key)
        if isinstance(entry, dict):
            allowed_values = entry.get("allow") or entry.get("allowed") or entry.get("values")
        else:
            allowed_values = entry
        if isinstance(allowed_values, str):
            allowed_values = [allowed_values]
        if not allowed_values:
            raise DependencyPolicyError(f"no allowlist entries defined for {lang}")
        missing: list[str] = []
        for value in values:
            if value in allowed_values:
                continue
            base = value.split("@", 1)[0]
            if base in allowed_values:
                continue
            missing.append(value)
        if missing:
            raise DependencyPolicyError(
                f"dependencies not allowed for {lang}: {', '.join(missing)}"
            )

    def _allowlist_env(self, lang: str) -> dict[str, str]:
        allow = self._dependency_allowlist.get(lang)
        env = allow.get("env") if isinstance(allow, dict) else None
        if not isinstance(env, dict):
            return {}
        return {str(k): str(v) for k, v in env.items() if v is not None}

    def _cache_key(self, lang: str, values: list[str], extras: Optional[list[str]] = None) -> str:
        payload = [lang]
        payload.extend(sorted(str(v) for v in values if v))
        if extras:
            payload.extend(str(v) for v in extras if v)
        digest = hashlib.sha256("|".join(payload).encode("utf-8")).hexdigest()
        return digest[:16]

    def _shared_cache_dir(
        self, lang: str, values: list[str], extras: Optional[list[str]] = None
    ) -> Path:
        key = self._cache_key(lang, values, extras)
        path = CACHE_ROOT / lang / key
        path.mkdir(parents=True, exist_ok=True)
        return path.resolve()

    def _trim_dependency_cache(self) -> None:
        try:
            summary = trim_cache(default_ttl_days=30, dry_run=False)
        except Exception:
            return
        removed = summary.get("total_removed")
        if removed:
            print(f"[mcpd] trimmed {removed} dependency cache entries", file=sys.stderr)

    # Verb: plan.create@v1
    def plan_create_v1(self, prompt: str, lang: str = "python") -> dict:
        """Parse .al DSL input into execution plan."""
        if parse_pw is None:
            return {
                "ok": False,
                "version": "v1",
                "error": {"code": "E_RUNTIME", "message": "DSL parser not available"},
            }

        # Parse DSL input
        try:
            parsed = parse_pw(prompt)
        except Exception as e:
            return {
                "ok": False,
                "version": "v1",
                "error": {"code": "E_PARSE", "message": f"Failed to parse .al input: {str(e)}"},
            }

        # Check if valid DSL was found
        if parsed.plan:
            # Valid DSL found, return the plan
            plan = parsed.plan
            # Ensure lang is set from plan or parameter
            if "lang" not in plan:
                plan["lang"] = lang
            return {"ok": True, "version": "v1", "data": plan}
        else:
            # No valid DSL, return error
            error_preview = parsed.prompt[:100] if parsed.prompt else "empty input"
            return {
                "ok": False,
                "version": "v1",
                "error": {
                    "code": "E_SYNTAX",
                    "message": f"Invalid .al syntax. Expected DSL format, got: {error_preview}",
                },
            }

    # Verb: fs.apply@v1
    def fs_apply_v1(self, task_id: str, writes: list[dict]) -> dict:
        task_dir = ARTIFACT_ROOT / task_id / "source"
        task_dir.mkdir(parents=True, exist_ok=True)
        written = 0
        for w in writes:
            path = task_dir / w["path"]
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(w["content"], encoding="utf-8")
            if "mode" in w and isinstance(w["mode"], int):
                os.chmod(path, w["mode"])
            written += 1
        return {"ok": True, "version": "v1", "data": {"writes": written, "patches": 0}}

    # Verb: run.start@v1
    def run_start_v1(
        self,
        plan: Union[dict, str],
        ready_regex: Optional[str] = None,
        timeout_sec: int = 120,
        lang: str = "python",
    ) -> dict:
        timeline: List[Dict[str, Any]] = []

        def _record(phase: str, *, status: str = "ok", **details: Any) -> None:
            event = {"phase": phase, "status": status}
            if details:
                event.update(details)
            timeline.append(event)

        def _elapsed(start: float) -> float:
            return round((time.perf_counter() - start) * 1000, 3)

        task_id = secrets.token_hex(3)  # 6 hex chars
        socket_path = self.run_socket_dir / f"{task_id}.sock"
        task_dir = ARTIFACT_ROOT / task_id
        (task_dir / "source").mkdir(parents=True, exist_ok=True)
        (task_dir / "logs").mkdir(parents=True, exist_ok=True)
        manifest_path = task_dir / "manifest.json"

        env = os.environ.copy()
        # Lease a high-range TCP port and export via PORT
        try:
            port = self._lease_port(task_id)
        except RuntimeError as exc:
            _record("port", status="error", error=str(exc))
            return {
                "ok": False,
                "version": "v1",
                "error": {"code": "E_PORT", "message": str(exc)},
                "events": timeline,
            }
        env["PORT"] = str(port)
        # Runner: Python process runs inside task_dir/source
        log_file = open(task_dir / "logs" / "run.log", "wb")

        plan_payload: dict
        if isinstance(plan, str):
            plan_payload = {"files": [], "start": plan, "lang": lang}
        else:
            plan_payload = plan

        plan_lang = plan_payload.get("lang") or lang
        tool_id = plan_payload.get("tool")
        registry_entry = self._tool_registry.get(tool_id) if tool_id else None
        registry_policy = dict(registry_entry.get("policy", {})) if registry_entry else {}
        plan_policy = dict(plan_payload.get("policy") or {})
        effective_policy: dict[str, Any] = {}
        for key in ("network", "filesystem", "secrets"):
            reg_val = registry_policy.get(key)
            if reg_val is not None:
                effective_policy[key] = reg_val
            plan_val = plan_policy.get(key)
            if plan_val is not None:
                if reg_val is not None and plan_val != reg_val:
                    self._release_port(port)
                    _record(
                        "policy",
                        status="error",
                        error=f"{key} conflict",
                        requested=plan_val,
                        required=reg_val,
                    )
                    return {
                        "ok": False,
                        "version": "v1",
                        "error": {
                            "code": "E_POLICY",
                            "message": f"policy conflict for {key}: plan requested {plan_val}, registry requires {reg_val}",
                        },
                        "events": timeline,
                    }
                effective_policy[key] = plan_val if reg_val is None else reg_val

        policy_timeout = registry_policy.get("timeout_sec")
        if policy_timeout is not None:
            try:
                timeout_sec = min(timeout_sec, int(policy_timeout))
                effective_policy["timeout_sec"] = int(policy_timeout)
            except (TypeError, ValueError):
                pass
        elif "timeout_sec" in plan_policy:
            try:
                effective_policy["timeout_sec"] = int(plan_policy["timeout_sec"])
                timeout_sec = min(timeout_sec, int(plan_policy["timeout_sec"]))
            except (TypeError, ValueError):
                pass
        files = plan_payload.get("files") or []
        start_cmd = plan_payload.get("start")
        if not start_cmd:
            _record("plan", status="error", error="missing start command")
            return {
                "ok": False,
                "version": "v1",
                "error": {"code": "E_PLAN", "message": "plan missing start command"},
                "events": timeline,
            }

        # Step 1: write app files from provided plan
        apply_req = {
            "method": "apply",
            "task_id": task_id,
            "files": files,
            "target_dir": str(task_dir / "source"),
        }
        if files:
            apply_started = time.perf_counter()
            if plan_lang == "python":
                self._run_python_runner(apply_req)
            elif plan_lang in {"node", "nextjs"}:
                # Use python runner for file writes to avoid any node spawn issues during apply
                self._run_python_runner(apply_req)
            elif plan_lang == "go":
                self._run_go_runner(apply_req)
            elif plan_lang in {"rust", "java"}:
                # Reuse python runner for generic apply
                self._run_python_runner(apply_req)
            elif plan_lang == ".net":
                self._run_dotnet_runner(apply_req)
            elif plan_lang == "cpp":
                # Apply with python runner (write files)
                self._run_python_runner(apply_req)
            else:
                _record("apply", status="error", error=f"unsupported lang {plan_lang}")
                return {
                    "ok": False,
                    "version": "v1",
                    "error": {"code": "E_UNSUPPORTED", "message": f"unsupported lang {plan_lang}"},
                    "events": timeline,
                }
            _record("apply", files=len(files), duration_ms=_elapsed(apply_started))
        else:
            _record("apply", files=0, duration_ms=0.0)

        # Step 2: start user app on ephemeral port
        # For Next.js, pre-install and build synchronously to reduce startup time during serve
        if plan_lang == "nextjs":
            build_started = time.perf_counter()
            brew_paths = "/opt/homebrew/bin:/usr/local/bin"
            pre_env = os.environ.copy()
            pre_env["PATH"] = f"{brew_paths}:" + pre_env.get("PATH", "")
            pre_env["NEXT_TELEMETRY_DISABLED"] = "1"
            pre_env["CI"] = "1"
            try:
                subprocess.run(
                    ["bash", "-lc", "npm install --no-fund --no-audit"],
                    cwd=str(task_dir / "source"),
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    env=pre_env,
                    check=True,
                )
                subprocess.run(
                    ["bash", "-lc", "npm run build"],
                    cwd=str(task_dir / "source"),
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    env=pre_env,
                    check=True,
                )
            except subprocess.CalledProcessError:
                self._release_port(port)
                _record("build", status="error", error="Next.js install/build failed")
                return {
                    "ok": False,
                    "version": "v1",
                    "error": {"code": "E_BUILD", "message": "Next.js install/build failed"},
                    "events": timeline,
                }
            else:
                _record("build", duration_ms=_elapsed(build_started), stage="nextjs")

        start_req = {
            "method": "start",
            "task_id": task_id,
            "cmd": start_cmd,
            "cwd": str(task_dir / "source"),
            "port": port,
            "log_path": str(task_dir / "logs" / "run.log"),
        }
        plan_env = plan_payload.get("env")
        env_map: dict[str, str] = {}
        if registry_entry:
            default_env = registry_entry.get("policy", {}).get("env")
            if isinstance(default_env, dict):
                env_map.update({k: str(v) for k, v in default_env.items()})
        if isinstance(plan_env, dict):
            env_map.update({k: str(v) for k, v in plan_env.items()})
        deps = plan_payload.get("deps") or {}
        if registry_entry:
            for adapter in registry_entry.get("adapters", []):
                lang_entry = adapter.get("language")
                if not lang_entry:
                    continue
                reg_deps = adapter.get("deps") or {}
                if not reg_deps:
                    continue
                candidate = None
                if isinstance(reg_deps, dict) and lang_entry in reg_deps:
                    candidate = reg_deps.get(lang_entry)
                elif isinstance(reg_deps, dict):
                    candidate = reg_deps
                if candidate is not None:
                    existing = deps.get(lang_entry)
                    if not existing:
                        deps[lang_entry] = candidate
                    elif isinstance(existing, dict) and isinstance(candidate, dict):
                        # fill missing fields without overriding plan-provided entries
                        for key, value in candidate.items():
                            existing.setdefault(key, value)
        deps_started = time.perf_counter()
        try:
            dep_env = self._prepare_dependencies(task_dir, plan_lang, deps, env_map, log_file)
        except DependencyPolicyError as exc:
            self._release_port(port)
            _record("deps", status="error", error=str(exc))
            return {
                "ok": False,
                "version": "v1",
                "error": {"code": "E_POLICY", "message": str(exc)},
                "events": timeline,
            }
        except DependencyError as exc:
            self._release_port(port)
            _record("deps", status="error", error=str(exc))
            return {
                "ok": False,
                "version": "v1",
                "error": {"code": "E_BUILD", "message": str(exc)},
                "events": timeline,
            }
        if dep_env:
            env_map.update(dep_env)
        _record("deps", duration_ms=_elapsed(deps_started), env_keys=len(env_map))
        if plan_lang == "java":
            java_home = "/opt/homebrew/opt/openjdk"
            env_map.update(
                {
                    "JAVA_HOME": java_home,
                    "PATH": f"{java_home}/bin:" + os.environ.get("PATH", ""),
                }
            )
        elif plan_lang == ".net":
            dotnet_root = str(Path.home() / ".dotnet")
            base_path = env_map.get("PATH") or os.environ.get("PATH", "")
            new_path = f"{dotnet_root}:{base_path}" if base_path else dotnet_root
            env_map.update(
                {
                    "DOTNET_ROOT": dotnet_root,
                    "PATH": new_path,
                }
            )
            timeout_sec = max(timeout_sec, 300)
        elif plan_lang in {"node", "nextjs"}:
            # Ensure node binary is found when launched from Python venv
            brew_paths = "/opt/homebrew/bin:/usr/local/bin"
            base_path = env_map.get("PATH") or os.environ.get("PATH", "")
            new_path = f"{brew_paths}:{base_path}" if base_path else brew_paths
            env_map.update(
                {
                    "PATH": new_path,
                    "NEXT_TELEMETRY_DISABLED": "1",
                    "HOST": "127.0.0.1",
                }
            )
            timeout_sec = max(timeout_sec, 600)
        start_req["env"] = env_map
        if effective_policy:
            start_req["policy"] = effective_policy
            env_map.setdefault("PROMPTWARE_POLICY", json.dumps(effective_policy))
        # Prefer starting via python runner for stable process supervision and logging
        start_started = time.perf_counter()
        if plan_lang in {"python", "node", "nextjs", "cpp", "rust", "java"}:
            start_res = self._run_python_runner(start_req)
        elif plan_lang == "go":
            start_res = self._run_go_runner(start_req)
        elif plan_lang == ".net":
            start_res = self._run_dotnet_runner(start_req)
        else:
            start_res = self._run_python_runner(start_req)

        if not start_res.get("ok"):
            error = start_res.get("error", {}) if isinstance(start_res, dict) else {}
            code = error.get("code") or "E_RUNTIME"
            message = error.get("message") or "runner start failed"
            self._release_port(port)
            _record("start", status="error", error=message, duration_ms=_elapsed(start_started))
            return {
                "ok": False,
                "version": "v1",
                "error": {"code": code, "message": message},
                "events": timeline,
            }

        app_pid = start_res.get("data", {}).get("pid")
        _record("start", duration_ms=_elapsed(start_started), pid=app_pid)

        readiness_started = time.perf_counter()
        readiness_attempts = 0

        def _runner_health_ready() -> Optional[bool]:
            health_req = {"method": "health", "host": "127.0.0.1", "port": port}
            try:
                if plan_lang in {"python", "node", "nextjs", "cpp", "rust", "java"}:
                    res = self._run_python_runner(health_req)
                elif plan_lang == "go":
                    res = self._run_go_runner(health_req)
                elif plan_lang == ".net":
                    res = self._run_dotnet_runner(health_req)
                else:
                    return None
            except Exception:
                return False
            if not res.get("ok"):
                return False
            data = res.get("data", {})
            if "ready" in data:
                return bool(data.get("ready"))
            return None

        # Wait for runner readiness / TCP availability
        ready = False
        deadline = time.time() + timeout_sec
        while time.time() < deadline:
            readiness_attempts += 1
            health = _runner_health_ready()
            if health is True:
                ready = True
                break
            if health is False:
                time.sleep(0.1)
                continue
            try:
                with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                    ready = True
                    break
            except Exception:
                time.sleep(0.1)
        if not ready:
            try:
                if app_pid:
                    os.kill(app_pid, signal.SIGTERM)
            except Exception:
                pass
            self._release_port(port)
            _record(
                "ready",
                status="error",
                error="App did not start",
                duration_ms=_elapsed(readiness_started),
                attempts=readiness_attempts,
            )
            return {
                "ok": False,
                "version": "v1",
                "error": {"code": "E_TIMEOUT", "message": "App did not start"},
                "events": timeline,
            }

        _record(
            "ready",
            duration_ms=_elapsed(readiness_started),
            attempts=readiness_attempts,
        )

        transport: dict
        uds_path: Optional[str] = None
        if self.gateway_available:
            uds_path = str(socket_path)
            backend_url = f"http://127.0.0.1:{port}"
            route_started = time.perf_counter()
            subprocess.Popen(
                [
                    sys.executable,
                    str(Path("daemon/uds_shim.py")),
                    "--uds",
                    uds_path,
                    "--backend",
                    backend_url,
                ],
                cwd=str(Path.cwd()),
                stdout=log_file,
                stderr=subprocess.STDOUT,
                env=env,
            )
            uds_deadline = time.time() + 10
            while time.time() < uds_deadline:
                if os.path.exists(uds_path):
                    try:
                        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
                            s.settimeout(0.5)
                            s.connect(uds_path)
                            break
                    except Exception:
                        pass
                time.sleep(0.1)
            self.gateway.add_route(task_id, uds_path)
            self.gateway.add_tcp_route(task_id, "127.0.0.1", int(port))
            transport = {
                "type": "uds",
                "path": uds_path,
                "tcp_fallback": {"host": "127.0.0.1", "port": int(port)},
            }
            _record("route", duration_ms=_elapsed(route_started), transport="uds")
        else:
            transport = {"type": "tcp", "host": "127.0.0.1", "port": int(port)}
            _record("route", duration_ms=0.0, transport="tcp")

        manifest = {
            "task_id": task_id,
            "entry": {"cmd": start_cmd},
            "transport": transport,
            "files": [f["path"] for f in files],
            "lang": plan_lang,
            "pid": app_pid,
            "gateway_port": self.gateway_port,
            "port": int(port),
        }
        if effective_policy:
            manifest["policy"] = effective_policy
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

        self.tasks[task_id] = Task(
            task_id=task_id,
            dir=task_dir,
            socket_path=socket_path,
            pid=app_pid,
            port=port,
            events=list(timeline),
        )

        result_data = {
            "task_id": task_id,
            "transport": transport["type"],
            "pid": app_pid,
            "host": "127.0.0.1",
            "port": int(port),
            "gateway_port": self.gateway_port,
            "manifest_path": str(manifest_path),
        }
        if uds_path:
            result_data["socket"] = uds_path
        if effective_policy:
            result_data["policy"] = effective_policy
        result_data["events"] = timeline
        result = {"ok": True, "version": "v1", "data": result_data}

        return result

    # Verb: httpcheck.assert@v1
    def httpcheck_assert_v1(self, task_id: str, path: str = "/", expect_status: int = 200) -> dict:
        import time

        import requests

        task = self.tasks.get(task_id)
        host = "127.0.0.1"
        port = task.port if task else None
        gateway_port = getattr(self, "gateway_port", None)
        if self.gateway_available and gateway_port:
            base_url = f"http://{host}:{gateway_port}/apps/{task_id}"
        elif port:
            base_url = f"http://{host}:{port}"
        else:
            return {
                "ok": False,
                "version": "v1",
                "error": {"code": "E_RUNTIME", "message": "task port unavailable"},
            }
        url = f"{base_url}{path}"
        start_time = time.perf_counter()
        last_exc = None
        for _ in range(15):
            try:
                r = requests.get(url, timeout=2)
                passed = r.status_code == expect_status
                details = {"path": path, "status": r.status_code}
                duration_ms = round((time.perf_counter() - start_time) * 1000, 3)
                if task:
                    task.events.append(
                        {
                            "phase": "httpcheck",
                            "status": "ok" if passed else "fail",
                            "path": path,
                            "expected": expect_status,
                            "actual": r.status_code,
                            "duration_ms": duration_ms,
                        }
                    )
                data = {
                    "pass": passed,
                    "details": [details],
                    "events": list(task.events) if task else [],
                }
                return {"ok": True, "version": "v1", "data": data}
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                time.sleep(1)
        failure_message = str(last_exc) if last_exc else "timeout"
        if task:
            task.events.append(
                {
                    "phase": "httpcheck",
                    "status": "error",
                    "path": path,
                    "error": failure_message,
                    "duration_ms": round((time.perf_counter() - start_time) * 1000, 3),
                }
            )
        return {
            "ok": False,
            "version": "v1",
            "error": {"code": "E_NETWORK", "message": failure_message},
            "events": list(task.events) if task else [],
        }

    # Verb: report.finish@v1
    def report_finish_v1(self, task_id: str, verdict: str = "pass") -> dict:
        host = "127.0.0.1"
        gateway_port = getattr(self, "gateway_port", None)
        task = self.tasks.get(task_id)
        direct_port = task.port if task else None
        url = None
        if self.gateway_available and gateway_port:
            url = f"http://{host}:{gateway_port}/apps/{task_id}/"
        elif direct_port:
            url = f"http://{host}:{direct_port}/"
        files = []
        if (ARTIFACT_ROOT / task_id).exists():
            for p in (ARTIFACT_ROOT / task_id).rglob("*"):
                if p.is_file():
                    files.append(str(p.relative_to(ARTIFACT_ROOT / task_id)))
        if task:
            task.events.append(
                {
                    "phase": "report",
                    "status": verdict,
                    "url": url,
                    "direct_url": f"http://{host}:{direct_port}/" if direct_port else None,
                }
            )
        return {
            "ok": True,
            "version": "v1",
            "data": {
                "artifact_dir": str(ARTIFACT_ROOT / task_id),
                "url": url,
                "direct_url": f"http://{host}:{direct_port}/" if direct_port else None,
                "files": files,
                "events": list(task.events) if task else [],
            },
        }

    def stop_task(self, task_id: str) -> None:
        t = self.tasks.get(task_id)
        if not t:
            return
        status = "ok"
        error_msg = None
        try:
            # Ask runner to stop; fallback to SIGTERM
            if t.pid:
                stop_req = {"method": "stop", "pid": t.pid}
                self._run_python_runner(stop_req)
                try:
                    os.kill(t.pid, signal.SIGTERM)
                except Exception:
                    pass
        except Exception as exc:
            status = "error"
            error_msg = str(exc)
        self.gateway.remove_route(task_id)
        if t.port:
            self._release_port(t.port)
            t.port = None
        stop_event = {"phase": "stop", "status": status}
        if error_msg:
            stop_event["error"] = error_msg
        t.events.append(stop_event)
        # Leave artifacts for inspection

    def _run_python_runner(self, request: dict) -> dict:
        proc = subprocess.Popen(
            [sys.executable, str(Path("runners/python/runner.py"))],
            cwd=str(Path.cwd()),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        out, err = proc.communicate(json.dumps(request), timeout=60)
        try:
            res = json.loads(out or "{}")
        except Exception:
            res = {"ok": False, "error": {"code": "E_RUNNER", "message": err}}
        return res

    def _run_node_runner(self, request: dict) -> dict:
        env = os.environ.copy()
        env["PATH"] = "/opt/homebrew/bin:/usr/local/bin:" + env.get("PATH", "")
        proc = subprocess.Popen(
            ["node", str(Path("runners/node/runner.js")), "--json", json.dumps(request)],
            cwd=str(Path.cwd()),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
        )
        out, err = proc.communicate(timeout=120)
        try:
            res = json.loads(out or "{}")
        except Exception:
            res = {"ok": False, "error": {"code": "E_RUNNER", "message": err}}
        return res

    def _run_go_runner(self, request: dict) -> dict:
        proc = subprocess.Popen(
            ["go", "run", str(Path("runners/go/runner.go")), "--json", json.dumps(request)],
            cwd=str(Path.cwd()),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        out, err = proc.communicate(timeout=180)
        try:
            res = json.loads(out or "{}")
        except Exception:
            res = {"ok": False, "error": {"code": "E_RUNNER", "message": err}}
        return res

    def _run_dotnet_runner(self, request: dict) -> dict:
        proc = subprocess.Popen(
            [
                "dotnet",
                "run",
                "--project",
                str(Path("runners/dotnet/Runner.csproj")),
                "--",
                "--json",
                json.dumps(request),
            ],
            cwd=str(Path.cwd()),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        out, err = proc.communicate(timeout=240)
        try:
            res = json.loads(out or "{}")
        except Exception:
            res = {"ok": False, "error": {"code": "E_RUNNER", "message": err}}
        return res

    # Port leasing utilities (61000–64999)
    def _lease_port(self, task_id: str, ttl_sec: int = 900) -> int:
        now = time.time()
        # Cleanup expired leases
        self._leases = {p: exp for p, exp in self._leases.items() if exp > now}
        start = random.randint(61000, 64999)
        for i in range(65000 - 61000):
            port = 61000 + ((start - 61000 + i) % (65000 - 61000))
            if port in self._leases:
                continue
            if self._port_free(port):
                self._leases[port] = now + ttl_sec
                return port
        raise RuntimeError("No free high-range TCP ports available")

    def _release_port(self, port: int) -> None:
        self._leases.pop(port, None)

    @staticmethod
    def _port_free(port: int) -> bool:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind(("127.0.0.1", port))
            return True
        except OSError:
            return False

    def _prepare_dependencies(
        self,
        task_dir: Path,
        plan_lang: str,
        deps: Optional[dict],
        env_map: dict[str, str],
        log_file,
    ) -> dict[str, str]:
        deps = deps or {}
        updates: dict[str, str] = {}
        existing_path = env_map.get("PATH") or os.environ.get("PATH", "")

        try:
            if plan_lang == "python":
                py_cfg = deps.get("python") or {}
                requirements = py_cfg.get("requirements") or []
                self._enforce_allowlist("python", requirements)
                if not requirements and not py_cfg.get("create_venv", True):
                    return updates
                env_root = task_dir / "env" / "python"
                venv_dir = env_root / "venv"
                bin_dir = venv_dir / ("Scripts" if os.name == "nt" else "bin")
                python_bin = bin_dir / ("python.exe" if os.name == "nt" else "python")
                env_root.mkdir(parents=True, exist_ok=True)
                if not venv_dir.exists():
                    subprocess.run(
                        [sys.executable, "-m", "venv", str(venv_dir)],
                        stdout=log_file,
                        stderr=subprocess.STDOUT,
                        check=True,
                    )
                if requirements:
                    pip_env = os.environ.copy()
                    pip_env.update(self._allowlist_env("python"))
                    pip_cache = self._shared_cache_dir(
                        "python", requirements or ["default"], [sys.version.split(" ")[0]]
                    )
                    pip_env["PIP_CACHE_DIR"] = str(pip_cache)
                    cmd = [
                        str(python_bin),
                        "-m",
                        "pip",
                        "install",
                        "--no-input",
                        "--disable-pip-version-check",
                        *requirements,
                    ]
                    subprocess.run(
                        cmd,
                        stdout=log_file,
                        stderr=subprocess.STDOUT,
                        env=pip_env,
                        check=True,
                    )
                updates["VIRTUAL_ENV"] = str(venv_dir)
                updates["PATH"] = (
                    f"{bin_dir}{os.pathsep}{existing_path}" if existing_path else str(bin_dir)
                )
                return updates

            if plan_lang in {"node", "nextjs"}:
                node_cfg = deps.get("node") or {}
                packages = node_cfg.get("packages") or []
                self._enforce_allowlist("node", packages)
                self._enforce_allowlist("nextjs", packages)
                if not packages:
                    return updates
                source_dir = task_dir / "source"
                brew_paths = "/opt/homebrew/bin:/usr/local/bin"
                npm_env = os.environ.copy()
                npm_env["PATH"] = f"{brew_paths}:" + npm_env.get("PATH", "")
                npm_env.update(self._allowlist_env("node"))
                if plan_lang == "nextjs":
                    npm_env.update(self._allowlist_env("nextjs"))
                node_allow = self._dependency_allowlist.get("node") or {}
                registry_cfg = node_allow.get("registry") if isinstance(node_allow, dict) else None
                if isinstance(registry_cfg, dict):
                    registry_url = registry_cfg.get("url")
                    if registry_url:
                        npm_env["NPM_CONFIG_REGISTRY"] = str(registry_url)
                        npm_env["npm_config_registry"] = str(registry_url)
                    always_auth = registry_cfg.get("always_auth")
                    if always_auth is not None:
                        npm_env["NPM_CONFIG_ALWAYS_AUTH"] = "true" if always_auth else "false"
                    token_env = registry_cfg.get("token_env")
                    if token_env:
                        token_val = os.environ.get(str(token_env))
                        if token_val:
                            npm_env[str(token_env)] = token_val
                    ttl = registry_cfg.get("cache_ttl_days")
                    if ttl is not None:
                        ttl_str = str(ttl)
                        npm_env["PROMPTWARE_NODE_CACHE_TTL_DAYS"] = ttl_str
                        updates["PROMPTWARE_NODE_CACHE_TTL_DAYS"] = ttl_str
                npm_cache = self._shared_cache_dir("node", packages or ["default"])
                npm_env["npm_config_cache"] = str(npm_cache)
                npm_env["NPM_CONFIG_CACHE"] = str(npm_cache)
                if not (source_dir / "package.json").exists():
                    subprocess.run(
                        ["bash", "-lc", "npm init -y"],
                        cwd=str(source_dir),
                        env=npm_env,
                        stdout=log_file,
                        stderr=subprocess.STDOUT,
                        check=True,
                    )
                install_cmd = "npm install --no-fund --no-audit --save=false " + " ".join(packages)
                subprocess.run(
                    ["bash", "-lc", install_cmd],
                    cwd=str(source_dir),
                    env=npm_env,
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    check=True,
                )
                bin_dir = source_dir / "node_modules" / ".bin"
                path_prefix = (
                    f"{bin_dir}{os.pathsep}{existing_path}" if existing_path else str(bin_dir)
                )
                updates["PATH"] = path_prefix
                return updates

            if plan_lang == "go":
                go_cfg = deps.get("go") or {}
                modules = go_cfg.get("modules") or []
                self._enforce_allowlist("go", modules)
                if not modules:
                    return updates
                if not shutil.which("go"):
                    raise DependencyError("go toolchain not available")
                source_dir = task_dir / "source"
                source_dir.mkdir(parents=True, exist_ok=True)
                env_root = task_dir / "env" / "go"
                env_root.mkdir(parents=True, exist_ok=True)
                shared_root = self._shared_cache_dir("go", modules)
                gomod_cache = shared_root / "modcache"
                gopath = shared_root / "gopath"
                go_build_cache = shared_root / "buildcache"
                gomod_cache.mkdir(parents=True, exist_ok=True)
                gopath.mkdir(parents=True, exist_ok=True)
                go_build_cache.mkdir(parents=True, exist_ok=True)
                go_env = os.environ.copy()
                go_env.update(
                    {
                        "GOMODCACHE": str(gomod_cache),
                        "GOCACHE": str(go_build_cache),
                        "GOPATH": str(gopath),
                        "GO111MODULE": "on",
                    }
                )
                go_env.update(self._allowlist_env("go"))
                gomod_path = source_dir / "go.mod"
                if not gomod_path.exists():
                    module_name = go_cfg.get("module_name") or "promptwareapp"
                    gomod_content = "module " + module_name + "\n\ngo 1.22\n"
                    gomod_path.write_text(gomod_content, encoding="utf-8")
                for mod in modules:
                    subprocess.run(
                        ["bash", "-lc", f"go get {mod}"],
                        cwd=str(source_dir),
                        stdout=log_file,
                        stderr=subprocess.STDOUT,
                        env=go_env,
                        check=True,
                    )
                subprocess.run(
                    ["bash", "-lc", "go mod tidy"],
                    cwd=str(source_dir),
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    env=go_env,
                    check=True,
                )
                updates["GOMODCACHE"] = str(gomod_cache)
                updates["GOCACHE"] = str(go_build_cache)
                updates["GOPATH"] = str(gopath)
                return updates

            if plan_lang == ".net":
                dotnet_cfg = deps.get("dotnet") or {}
                packages = dotnet_cfg.get("packages") or []
                self._enforce_allowlist("dotnet", packages)
                env_root = task_dir / "env" / "dotnet"
                env_root.mkdir(parents=True, exist_ok=True)
                shared_root = self._shared_cache_dir("dotnet", packages or ["baseline"])
                nuget_dir = shared_root / "nuget"
                nuget_dir.mkdir(parents=True, exist_ok=True)
                updates["NUGET_PACKAGES"] = str(nuget_dir)
                allow_entry = self._dependency_allowlist.get("dotnet") or {}
                dotnet_root = (
                    dotnet_cfg.get("dotnet_root")
                    or allow_entry.get("dotnet_root")
                    or os.environ.get("DOTNET_ROOT")
                    or str(Path.home() / ".dotnet")
                )
                updates.setdefault("DOTNET_ROOT", dotnet_root)
                cache_ttl = allow_entry.get("cache_ttl_days")
                if cache_ttl is not None:
                    ttl_str = str(cache_ttl)
                    updates["PROMPTWARE_DOTNET_CACHE_TTL_DAYS"] = ttl_str
                if packages:
                    if not (
                        shutil.which("dotnet") or Path(dotnet_root).joinpath("dotnet").exists()
                    ):
                        raise DependencyError("dotnet SDK not available")
                    deps_dir = env_root / "deps"
                    deps_dir.mkdir(parents=True, exist_ok=True)
                    proj_path = deps_dir / "PromptwareDeps.csproj"
                    target_framework = (
                        dotnet_cfg.get("target_framework")
                        or allow_entry.get("target_framework")
                        or "net8.0"
                    )
                    pkg_lines = []
                    for raw in packages:
                        name, _, version = raw.partition("@")
                        attrib = f'Include="{name}"'
                        if version:
                            pkg_lines.append(
                                f'    <PackageReference {attrib} Version="{version}" />'
                            )
                        else:
                            pkg_lines.append(f"    <PackageReference {attrib} />")
                    proj_content = (
                        '<Project Sdk="Microsoft.NET.Sdk">\n'
                        "  <PropertyGroup>\n"
                        f"    <TargetFramework>{target_framework}</TargetFramework>\n"
                        "  </PropertyGroup>\n"
                        "  <ItemGroup>\n" + "\n".join(pkg_lines) + "\n  </ItemGroup>\n"
                        "</Project>\n"
                    )
                    proj_path.write_text(proj_content, encoding="utf-8")
                    restore_env = os.environ.copy()
                    restore_env.update(
                        {
                            "NUGET_PACKAGES": str(nuget_dir),
                            "DOTNET_ROOT": dotnet_root,
                        }
                    )
                    restore_env.update(self._allowlist_env("dotnet"))
                    if cache_ttl is not None:
                        restore_env["PROMPTWARE_DOTNET_CACHE_TTL_DAYS"] = str(cache_ttl)
                    feeds = allow_entry.get("feeds")
                    config_path = None
                    if isinstance(feeds, list) and feeds:
                        config_path = deps_dir / "NuGet.Config"
                        lines = [
                            "<configuration>",
                            "  <packageSources>",
                            "    <clear />",
                        ]
                        seen_default = False
                        credential_entries: dict[str, dict[str, str]] = {}
                        for feed in feeds:
                            name = feed.get("name") or "private"
                            url = feed.get("url")
                            if not url:
                                continue
                            if str(url) == "https://api.nuget.org/v3/index.json":
                                seen_default = True
                            lines.append(
                                f'    <add key="{name}" value="{url}" protocolVersion="3" />'
                            )
                            token_env = feed.get("token_env")
                            username_env = feed.get("username_env")
                            password_env = feed.get("password_env")
                            username_literal = feed.get("username")
                            cred_values: dict[str, str] = {}
                            token_val = os.environ.get(str(token_env)) if token_env else None
                            if token_val:
                                cred_values["ClearTextPassword"] = token_val
                            password_val = (
                                os.environ.get(str(password_env)) if password_env else None
                            )
                            if password_val and not token_val:
                                cred_values["ClearTextPassword"] = password_val
                            user_val = None
                            if username_env:
                                user_val = os.environ.get(str(username_env))
                            if user_val is None and username_literal:
                                user_val = str(username_literal)
                            if user_val:
                                cred_values["Username"] = str(user_val)
                            elif cred_values:
                                cred_values.setdefault("Username", "token")
                            if cred_values:
                                credential_entries[name] = cred_values
                        if not seen_default:
                            lines.insert(
                                3,
                                '    <add key="nuget.org" value="https://api.nuget.org/v3/index.json" protocolVersion="3" />',
                            )
                        lines.append("  </packageSources>")
                        if credential_entries:
                            lines.append("  <packageSourceCredentials>")
                            for src, creds in credential_entries.items():
                                lines.append(f"    <{src}>")
                                for key, value in creds.items():
                                    escaped = html.escape(str(value), quote=True)
                                    lines.append(f'      <add key="{key}" value="{escaped}" />')
                                lines.append(f"    </{src}>")
                            lines.append("  </packageSourceCredentials>")
                        lines.append("</configuration>")
                        config_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
                    if dotnet_root:
                        restore_env["PATH"] = f"{dotnet_root}:" + restore_env.get("PATH", "")
                    restore_cmd = ["dotnet", "restore", str(proj_path)]
                    if config_path is not None:
                        restore_cmd.extend(["--configfile", str(config_path)])
                    subprocess.run(
                        restore_cmd,
                        cwd=str(deps_dir),
                        stdout=log_file,
                        stderr=subprocess.STDOUT,
                        env=restore_env,
                        check=True,
                    )
                return updates

            if plan_lang == "rust":
                rust_cfg = deps.get("rust") or {}
                crates = rust_cfg.get("crates") or []
                self._enforce_allowlist("rust", crates)
                env_root = task_dir / "env" / "rust"
                env_root.mkdir(parents=True, exist_ok=True)
                shared_root = self._shared_cache_dir("rust", crates or ["baseline"])
                cargo_home = shared_root / "cargo"
                rustup_home = shared_root / "rustup"
                cargo_home.mkdir(parents=True, exist_ok=True)
                rustup_home.mkdir(parents=True, exist_ok=True)
                updates["CARGO_HOME"] = str(cargo_home)
                updates["RUSTUP_HOME"] = str(rustup_home)
                if crates:
                    if not shutil.which("cargo"):
                        raise DependencyError("cargo not available")
                    bootstrap_dir = env_root / "bootstrap"
                    bootstrap_dir.mkdir(parents=True, exist_ok=True)
                    cargo_toml = bootstrap_dir / "Cargo.toml"
                    deps_lines = []
                    for raw in crates:
                        name, _, version = raw.partition("@")
                        if version:
                            deps_lines.append(f'{name} = "{version}"')
                        else:
                            deps_lines.append(f'{name} = "*"')
                    cargo_toml.write_text(
                        "[package]\n"
                        'name = "promptware_bootstrap"\n'
                        'version = "0.1.0"\n'
                        'edition = "2021"\n\n'
                        "[dependencies]\n" + "\n".join(deps_lines) + "\n",
                        encoding="utf-8",
                    )
                    fetch_env = os.environ.copy()
                    fetch_env.update(
                        {
                            "CARGO_HOME": str(cargo_home),
                            "RUSTUP_HOME": str(rustup_home),
                        }
                    )
                    fetch_env.update(self._allowlist_env("rust"))
                    registries = (self._dependency_allowlist.get("rust") or {}).get("registries")
                    if isinstance(registries, list) and registries:
                        cargo_config_dir = bootstrap_dir / ".cargo"
                        cargo_config_dir.mkdir(parents=True, exist_ok=True)
                        config_lines: list[str] = []
                        for registry in registries:
                            name = registry.get("name")
                            index = registry.get("index")
                            if not name or not index:
                                continue
                            config_lines.append(f"[registries.{name}]")
                            config_lines.append(f'index = "{index}"')
                            config_lines.append("")
                            token_env = registry.get("token_env")
                            if token_env:
                                token_val = os.environ.get(str(token_env))
                                if token_val:
                                    env_key = f"CARGO_REGISTRIES_{str(name).upper().replace('-', '_')}_TOKEN"
                                    fetch_env[env_key] = token_val
                        if config_lines:
                            config_path = cargo_config_dir / "config.toml"
                            config_path.write_text(
                                "\n".join(config_lines).strip() + "\n", encoding="utf-8"
                            )
                    subprocess.run(
                        ["bash", "-lc", "cargo fetch"],
                        cwd=str(bootstrap_dir),
                        stdout=log_file,
                        stderr=subprocess.STDOUT,
                        env=fetch_env,
                        check=True,
                    )
                return updates
        except subprocess.CalledProcessError as exc:
            raise DependencyError(f"dependency preparation failed: {exc}") from exc
        except FileNotFoundError as exc:
            raise DependencyError(f"required tool missing: {exc}") from exc

        return updates


def main() -> None:
    d = MCPDaemon()
    d.start()
    # This module is not a long-lived daemon CLI for now; invoked by CLI commands
    print(json.dumps({"ok": True, "version": "v1", "data": {"status": "started"}}))


if __name__ == "__main__":
    main()
