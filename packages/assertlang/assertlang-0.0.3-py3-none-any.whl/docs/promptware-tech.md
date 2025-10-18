# AssertLang Tech Spec Pack (UDS First, Dynamic Port Fallback)

This pack contains **everything a coding agent (and human devs) need** to implement AssertLang cleanly: contracts, schemas, runner interfaces, CLI, security, routing, testing, and error models.

---

## 0) Quick Reference

* **Brand**: AssertLang
* **Gateway**: `http://127.0.0.1:23456/` (falls back to an ephemeral port when 23456 is unavailable)
* **Transport (local)**: Unix domain sockets (UDS) at `/run/mcpd/sock/<task_id>.sock` (fallback `/tmp/mcpd/...`), Windows named pipes `\\.\pipe\mcpd\<task_id>`
* **Direct access**: When the gateway cannot bind, clients connect directly to `127.0.0.1:<leased_port>` announced by the CLI and report APIs.
* **Core verbs**: `plan.create@v1`, `fs.apply@v1`, `run.start@v1`, `httpcheck.assert@v1`, `report.finish@v1`
* **Task folder**: `.mcpd/<task_id>/`

---

## 1) MCP Capability & Versioning

**Capability discovery response (example):**

```json
{
  "name": "promptware-mcpd",
  "version": "0.1.0",
  "capabilities": [
    {"verb": "plan.create", "version": "v1"},
    {"verb": "fs.apply", "version": "v1"},
    {"verb": "run.start", "version": "v1"},
    {"verb": "httpcheck.assert", "version": "v1"},
    {"verb": "report.finish", "version": "v1"}
  ]
}
```

**Versioning rule**: breaking changes → bump to `verb@v2` and keep `@v1` live for back-compat for ≥2 minor releases.

---

## 2) JSON Schemas (v1)

> All responses share `{ ok: boolean, version: string, data?: any, error?: Error }`.

### 2.1 `plan.create@v1` (Prompt → File Plan)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://assertlang.dev/schemas/plan.create.v1.json",
  "type": "object",
  "required": ["prompt"],
  "properties": {
    "prompt": {"type": "string", "minLength": 1},
    "constraints": {
      "type": "object",
      "properties": {
        "lang_hint": {"type": "array", "items": {"type": "string", "enum": ["python","node","go","rust","java","dotnet"]}},
        "deps_allowlist": {"type": "array", "items": {"type": "string"}},
        "port_hint": {"type": ["integer","null"], "minimum": 1025, "maximum": 65535}
      }
    }
  }
}
```

**Plan output (`data`)**

```json
{
  "files": [
    {"path": "app.py", "content": "...", "mode": 420}
  ],
  "start": "python app.py",
  "assumptions": ["Using Python standard library HTTP server"],
  "lang": "python",
  "deps": {
    "python": {
      "requirements": []
    }
  }
}
```

> `deps` is optional but recommended; see `docs/dependency-management.md` for per-language formats.

### 2.2 `fs.apply@v1` (Atomic writes/patches)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://assertlang.dev/schemas/fs.apply.v1.json",
  "type": "object",
  "properties": {
    "writes": {"type": "array", "items": {"type": "object", "required":["path","content"], "properties": {"path": {"type": "string"}, "content": {"type": "string"}, "mode": {"type": "integer"}}}},
    "patches": {"type": "array", "items": {"type": "object", "required":["path","diff"], "properties": {"path": {"type": "string"}, "diff": {"type": "string"}}}}
  },
  "additionalProperties": false
}
```

**Response**

```json
{"ok": true, "version":"v1", "data": {"writes":1, "patches":0}}
```

### 2.3 `run.start@v1` (Start process + readiness)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://assertlang.dev/schemas/run.start.v1.json",
  "type": "object",
  "required": ["cmd"],
  "properties": {
    "cmd": {"type": "string"},
    "env": {"type": "object", "additionalProperties": {"type":"string"}},
    "ready": {
      "type": "object",
      "properties": {
        "regex": {"type": "string"},
        "timeout_sec": {"type": "integer", "minimum": 1, "maximum": 600}
      }
    },
    "limits": {"type":"object","properties": {"cpu_pct":{"type":"integer","minimum":1,"maximum":100}, "mem_mb":{"type":"integer","minimum":32,"maximum":8192}, "wall_sec":{"type":"integer","minimum":1,"maximum":3600}}}
  }
}
```

**Response**

```json
{
  "ok": true,
  "version": "v1",
  "data": {
    "task_id": "ab12cd",
    "transport": "uds",
    "socket": "/run/mcpd/sock/ab12cd.sock",
    "host": "127.0.0.1",
    "port": 61842,
    "pid": 23121
  }
}
```

> `transport` can be `uds` or `tcp`. When `tcp`, the response omits `socket` and the daemon skips gateway registration.

### 2.4 `httpcheck.assert@v1` (Probes)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://assertlang.dev/schemas/httpcheck.assert.v1.json",
  "type": "object",
  "required": ["probes"],
  "properties": {
    "probes": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["method","path","expect_status"],
        "properties": {
          "method": {"type": "string", "enum": ["GET","POST","PUT","PATCH","DELETE"]},
          "path": {"type": "string"},
          "expect_status": {"type": "integer"},
          "expect_body": {"type": ["string","null"]},
          "headers": {"type": "object", "additionalProperties": {"type": "string"}}
        }
      }
    },
    "via": {"type":"object","properties":{"gateway":{"type":"string","format":"uri"}, "task_id": {"type":"string"}}}
  }
}
```

**Response**

```json
{"ok": true, "version":"v1", "data": {"pass": true, "details": [{"path":"/","status":200,"latency_ms": 12}]}}
```

### 2.5 `report.finish@v1` (Artifacts + verdict)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://assertlang.dev/schemas/report.finish.v1.json",
  "type": "object",
  "properties": {
    "include": {"type": "array", "items": {"type": "string"}},
    "verdict": {"type": "string", "enum": ["pass","fail"]}
  }
}
```

**Response**

```json
{
  "ok": true,
  "version": "v1",
  "data": {
    "artifact_dir": ".mcpd/ab12cd/",
    "url": "http://127.0.0.1:23456/apps/ab12cd/",
    "direct_url": "http://127.0.0.1:61842/",
    "files": ["manifest.json","run.log","probes.log"]
  }
}
```

---

## 3) Runner Plugin Protocol

Runners are separate executables invoked by `mcpd`. Communication is **stdin/stdout JSON envelopes** (`{"ok": bool, "version": "v1", ...}`). Minimal methods (all optional beyond `apply`, `start`, `stop`):

* `apply(plan)` → writes files, returns `{writes, target}`.
* `start(manifest)` → spawns process under sandbox; returns `{pid, host, port, socket?}`.
* `stop(task_id)` → graceful shutdown.
* `health(task_id)` → liveness/readiness check.

Requirements:

* Exactly one JSON object per invocation; no extra logging on stdout/stderr.
* Failures must set `ok=false` and provide `error.code` (`E_BUILD`, `E_RUNTIME`, etc.).
* Runners should respect the provided `env`, especially `PORT`.

**Manifest (runner-generated)**

```json
{
  "task_id": "ab12cd",
  "entry": {"cmd": "python app.py"},
  "transport": {"type":"uds","path":"/run/mcpd/sock/ab12cd.sock","tcp_fallback":{"host":"127.0.0.1","port":61842}},
  "files": ["app.py"],
  "lang": "python"
}
```

**Exit codes**

* `0` success, `10` invalid plan, `20` deps blocked, `30` build failure, `40` runtime failure.

---

## 4) Gateway Routing & Sockets

* **Default port**: `23456` (memorable, non-ephemeral range)
* Map: `/apps/<task_id>/*` → proxy to UDS `/run/mcpd/sock/<task_id>.sock`
* Health: `GET /apps/<task_id>/_health` → 200 if backend reachable
* Auto-cleanup: when process exits, gateway removes route; 410 on access

**TCP fallback (rare)**

* If a runner absolutely requires TCP: lease from **61000–64999** (never common dev ports)
* Lease TTL: 900s; pre-bind probe; auto-release on exit/TTL

---

## 5) Security & Policy

* **Default egress**: deny (no outbound net) unless `deps.install@v1` allowed
* **Allowlist example**:

```yaml
policies:
  deps_allowlist:
    python: ["flask","fastapi","requests"]
    node: ["express","node-fetch"]
    go:   []
```

* **Sandbox**: non-root, read-only root FS, temp project dir, cgroup caps (CPU %, mem MB), wall-clock timeout
* **Secrets & SAST (phase 3+)**: simple regex scans before `run.start`

---

## 6) CLI Spec (Human-Friendly)

```text
mcp run "<prompt>"                  # full pipeline
mcp change <task_id> "<delta>"      # planner produces patch plan → apply → restart → revalidate
mcp list                             # show tasks, status, URLs
mcp open <task_id>                   # open artifacts and URL
mcp export <task_id> <dir>           # write source tree for git
mcp kill <task_id>                   # stop and clean up
```

**Flags**: `--lang python|node|go`, `--timeout 60`, `--mem 512`, `--cpu 50`, `--no-egress`

---

## 7) Test Plan & Acceptance

### MVP Acceptance (Hello Web)

* `mcp run "Create a web service that responds 'Hello, World!'"` → PASS
* Artifacts exist: `manifest.json`, `run.log`, `probes.log`
* URL responds via gateway; killing task removes route (410)

### Matrix

* OS: macOS, Ubuntu, Windows
* Runners: Python (Flask), Node (Express), Go (net/http)
* Negative tests: blocked deps, port bind failure, runtime crash → proper errors, auto-cleanup

**Automated tests**

* Contract tests per verb (happy/failure paths)
* Runner conformance tests (apply/start/stop/health)
* Gateway routing tests (UDS + TCP fallback)

---

## 8) Error Model

**Error**

```json
{
  "code": "E_RUNTIME",
  "message": "Process exited with code 1",
  "hints": ["Check run.log", "Ensure allowed deps only"],
  "task_id": "ab12cd"
}
```

**Common codes**: `E_PLAN`, `E_FS`, `E_POLICY`, `E_BUILD`, `E_RUNTIME`, `E_TIMEOUT`, `E_NETWORK`, `E_PORT`

---

## 9) Sample End-to-End Transcript

1. `plan.create@v1` → File Plan
2. `fs.apply@v1` → write app
3. `run.start@v1` → socket `/run/mcpd/sock/ab12cd.sock`
4. `httpcheck.assert@v1` → 200 + "Hello, World!"
5. `report.finish@v1` → url `http://127.0.0.1:23456/apps/ab12cd/`

Artifacts:

```
.mcpd/ab12cd/
  plan.json
  manifest.json
  run.log
  probes.log
  patches/
  source/
```

---

## 10) Milestones (Engineering)

**M1 (2–3 wks)**: `mcpd` verbs, Python runner, gateway UDS, CLI `run`, `list`, acceptance test green

**M2 (4–6 wks)**: Node & Go runners, `change` + patch flow, artifact index, idle kill, better errors

**M3 (6–10 wks)**: GitHub Action mode, allowlist policy, secret scan, basic SAST, `export`

**M4 (10–16 wks)**: Rust runner (Axum/WASI), managed gateway (hostnames), auth/RBAC, observability

---

## 11) Contribution & Style (for repos)

* **Repo layout**

```
/daemon (mcpd core)
/runners/python
/runners/node
/runners/go
/cli
/schemas
/tests
/docs
```

* **Code style**: Prettier/ESLint for Node, Black/Ruff for Python, gofmt/go vet for Go
* **CI**: run contract tests, runner conformance, E2E smoke on PRs

---

## 12) Naming & Identity

* **Framework**: AssertLang
* **Port**: 23456
* **Slogans**: "One port, five verbs, infinite software." / "Prompted, not programmed."

---

## 13) Appendix: Example Minimal Plans

**Python/Flask**

```json
{"files":[{"path":"app.py","content":"from flask import Flask\\napp=Flask(__name__)\\n@app.get('/')\\ndef hi(): return 'Hello, World!'\\napp.run(host='0.0.0.0')\\n"}],"start":"python -m pip install flask && python app.py","lang":"python"}
```

**Node/Express**

```json
{"files":[{"path":"index.js","content":"const express=require('express');const app=express();app.get('/',(_,res)=>res.send('Hello, World!'));app.listen(0,'0.0.0.0');"}],"start":"npm init -y && npm i express && node index.js","lang":"node"}
```

**Go/net-http**

```json
{"files":[{"path":"main.go","content":"package main\\nimport (\\n\\t\\"fmt\\"\\n\\t\\"net/http\\"\\n)\\nfunc main(){http.HandleFunc(\\"/\\",func(w http.ResponseWriter,r *http.Request){fmt.Fprint(w,\\"Hello, World!\\")});http.ListenAndServe(\\\":0\\\",nil)}\\n"}],"start":"go run main.go","lang":"go"}
```

*(Note: `0` = bind ephemeral port; gateway maps it under 23456/public URL)*
