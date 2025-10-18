# Policy Hooks Documentation

This document defines the policy hook system for AssertLang runners, specifying how network, filesystem, and secrets policies are declared in tool specs and enforced during execution.

---

## Overview

**Policy hooks** are declarative constraints defined in tool specifications (`toolgen/specs/*.tool.yaml`) that limit what operations a tool can perform during execution. The daemon enforces these policies before invoking tool adapters, logging policy decisions in timeline events.

**Status**: Policy declaration exists in tool specs (Wave 1/2). Policy enforcement is planned for Wave 3.

---

## Policy Schema

Each tool spec includes a `policy` section:

```yaml
policy:
  network: deny | allow | { allow: ["domain", ...] }
  filesystem: deny | read | write | readwrite
  secrets: deny | allow | { allow: ["KEY_PATTERN", ...] }
  timeout_sec: 30  # optional: max execution time
```

### Field Reference

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `network` | string \| object | Yes | Network access policy |
| `filesystem` | string | Yes | Filesystem access policy |
| `secrets` | string \| object | Yes | Secrets/environment variable access policy |
| `timeout_sec` | integer | No | Maximum execution time in seconds |
| `retry` | object | No | Retry policy (max_attempts, delay_sec) |

---

## Network Policy

Controls outbound network access from tool adapters.

### Allowed Values

**`deny`** (default for most tools):
```yaml
policy:
  network: deny
```
- No outbound network connections permitted.
- DNS resolution blocked.
- Use for: data transformers, validators, local file operations.

**`allow`** (permissive):
```yaml
policy:
  network: allow
```
- All outbound connections permitted (any protocol, any destination).
- Use for: HTTP clients, API integrations, external service calls.

**`{ allow: [...] }`** (domain allowlist):
```yaml
policy:
  network:
    allow:
      - "api.example.com"
      - "*.cloudflare.com"
      - "192.168.1.0/24"
```
- Only connections to specified domains/IPs permitted.
- Supports wildcards (`*.domain.com`) and CIDR ranges.
- Use for: tools that call specific external APIs.

### Examples from Tool Specs

**HTTP tool** (full network access):
```yaml
# toolgen/specs/http.tool.yaml
policy:
  network: allow
  filesystem: deny
  secrets: deny
  timeout_sec: 60
```

**Storage tool** (no network):
```yaml
# toolgen/specs/storage.tool.yaml
policy:
  network: deny
  filesystem: readwrite
  secrets: deny
  timeout_sec: 30
```

**Auth tool** (no network, needs secrets):
```yaml
# toolgen/specs/auth.tool.yaml
policy:
  network: deny
  filesystem: deny
  secrets: allow
```

### Runner-Specific Enforcement

| Runner | Enforcement Mechanism | Wave |
| --- | --- | --- |
| **Python** | Daemon blocks adapter invocation if policy violated | 3 |
| **Node** | Daemon blocks adapter invocation if policy violated | 3 |
| **Go** | Daemon blocks adapter invocation if policy violated | 3 |
| **.NET** | Daemon blocks adapter invocation if policy violated | 3 |
| **Rust** | Daemon blocks adapter invocation if policy violated | 3 |

**Implementation notes**:
- Runners themselves don't enforce network policies (they're stateless protocol adapters).
- Daemon reads tool policy from `data/tools_registry.json` before invoking adapter.
- Daemon spawns adapters in network-restricted environments (Docker network modes, iptables rules, etc.).
- Policy violations logged as timeline events with `status: "denied"`.

---

## Filesystem Policy

Controls filesystem access from tool adapters.

### Allowed Values

**`deny`** (default for network/compute tools):
```yaml
policy:
  filesystem: deny
```
- No filesystem access permitted (except adapter code itself).
- Use for: HTTP clients, data transformers, validators.

**`read`**:
```yaml
policy:
  filesystem: read
```
- Read-only access to workspace directory.
- Cannot create/modify/delete files.
- Use for: file readers, template renderers, config parsers.

**`write`**:
```yaml
policy:
  filesystem: write
```
- Write access to workspace directory (can create new files).
- Cannot modify existing files outside workspace.
- Use for: loggers, report generators, artifact writers.

**`readwrite`**:
```yaml
policy:
  filesystem: readwrite
```
- Full read/write access to workspace directory.
- Can create, modify, delete files.
- Use for: storage backends, file processors, build tools.

### Filesystem Scopes

All filesystem policies are scoped to the **ephemeral workspace directory**:
- Workspace: `/tmp/promptware/<task_id>/` (Linux/macOS) or `C:\Temp\promptware\<task_id>\` (Windows)
- Adapters cannot access:
  - Parent directories (`../`)
  - Absolute paths outside workspace
  - System directories (`/etc`, `/usr`, `C:\Windows`)
  - User home directories

### Examples from Tool Specs

**Input tool** (read-only):
```yaml
# toolgen/specs/input.tool.yaml
policy:
  network: deny
  filesystem: read
  secrets: deny
```

**Output tool** (write-only):
```yaml
# toolgen/specs/output.tool.yaml
policy:
  network: deny
  filesystem: write
  secrets: deny
```

**Storage tool** (full access):
```yaml
# toolgen/specs/storage.tool.yaml
policy:
  network: deny
  filesystem: readwrite
  secrets: deny
  timeout_sec: 30
```

### Runner-Specific Enforcement

| Runner | Enforcement Mechanism | Wave |
| --- | --- | --- |
| **Python** | Chroot jail or bind mount workspace only | 3 |
| **Node** | Chroot jail or bind mount workspace only | 3 |
| **Go** | Chroot jail or bind mount workspace only | 3 |
| **.NET** | Chroot jail or bind mount workspace only | 3 |
| **Rust** | Chroot jail or bind mount workspace only | 3 |

**Implementation notes**:
- Daemon spawns adapters with restricted filesystem views (Docker volumes, bind mounts).
- `filesystem: deny` → Empty ephemeral volume (adapter code read-only).
- `filesystem: read` → Workspace mounted read-only.
- `filesystem: write` → Workspace mounted read-write, but adapter cannot modify existing files (enforced via file permissions).
- `filesystem: readwrite` → Workspace mounted read-write with full permissions.

---

## Secrets Policy

Controls access to sensitive environment variables and credential stores.

### Allowed Values

**`deny`** (default for most tools):
```yaml
policy:
  secrets: deny
```
- No access to environment variables except `PORT`, `LANG`, `PATH`.
- Cannot read credential files or keystores.
- Use for: data processors, validators, transformers.

**`allow`** (permissive):
```yaml
policy:
  secrets: allow
```
- Full access to all environment variables.
- Can read credential files in workspace.
- Use for: auth generators, API clients requiring tokens.

**`{ allow: [...] }`** (key allowlist):
```yaml
policy:
  secrets:
    allow:
      - "API_TOKEN"
      - "DB_PASSWORD"
      - "AWS_*"  # wildcard patterns
```
- Access only to specified environment variables.
- Supports wildcards (`AWS_*` matches `AWS_REGION`, `AWS_SECRET_KEY`, etc.).
- Use for: tools requiring specific credentials.

### Examples from Tool Specs

**HTTP tool** (no secrets):
```yaml
# toolgen/specs/http.tool.yaml
policy:
  network: allow
  filesystem: deny
  secrets: deny
```

**Auth tool** (needs secrets):
```yaml
# toolgen/specs/auth.tool.yaml
policy:
  network: deny
  filesystem: deny
  secrets: allow
```

**API Auth tool** (needs secrets):
```yaml
# toolgen/specs/api-auth.tool.yaml
policy:
  network: deny
  filesystem: deny
  secrets: allow
```

### Runner-Specific Enforcement

| Runner | Enforcement Mechanism | Wave |
| --- | --- | --- |
| **Python** | Daemon filters `env` dict passed to `subprocess.Popen()` | 3 |
| **Node** | Daemon filters `env` object passed to `spawn()` | 3 |
| **Go** | Daemon filters `os/exec.Cmd.Env` slice | 3 |
| **.NET** | Daemon filters `ProcessStartInfo.Environment` | 3 |
| **Rust** | Daemon filters `Command::env()` calls | 3 |

**Implementation notes**:
- Daemon reads tool policy before invoking adapter.
- Daemon constructs minimal environment with only allowed keys.
- Always allowed: `PORT`, `LANG`, `PATH`, `PWD`, `HOME` (minimal POSIX env).
- `secrets: deny` → Only minimal env provided.
- `secrets: allow` → All secrets from daemon context passed through.
- `secrets: { allow: [...] }` → Only matching keys passed through.

---

## Timeout Policy

Controls maximum execution time for tool adapters.

### Schema

```yaml
policy:
  timeout_sec: 30  # max execution time in seconds
```

### Default Behavior

If `timeout_sec` not specified:
- Default timeout: **60 seconds** for all adapters.
- Daemon terminates adapter process if exceeded.
- Timeline event logged with `status: "timeout"`, `error.code: "E_TIMEOUT"`.

### Examples from Tool Specs

**Storage tool** (30 seconds):
```yaml
# toolgen/specs/storage.tool.yaml
policy:
  network: deny
  filesystem: readwrite
  secrets: deny
  timeout_sec: 30
```

**HTTP tool** (60 seconds):
```yaml
# toolgen/specs/http.tool.yaml
policy:
  network: allow
  filesystem: deny
  secrets: deny
  timeout_sec: 60
```

**Logger tool** (5 seconds):
```yaml
# toolgen/specs/logger.tool.yaml
policy:
  network: deny
  filesystem: read
  secrets: deny
  timeout_sec: 5
```

### Runner-Specific Enforcement

| Runner | Enforcement Mechanism | Wave |
| --- | --- | --- |
| **Python** | `subprocess.Popen()` with `timeout` in `.wait()` | 3 |
| **Node** | `spawn()` with `setTimeout()` to kill child | 3 |
| **Go** | `context.WithTimeout()` in adapter invocation | 3 |
| **.NET** | `Process.WaitForExit(timeout)` | 3 |
| **Rust** | `tokio::time::timeout()` in adapter invocation | 3 |

---

## Retry Policy

Controls automatic retry behavior for transient failures.

### Schema

```yaml
policy:
  retry:
    max_attempts: 3
    delay_sec: 1.0
    backoff: exponential  # optional: linear | exponential
```

### Default Behavior

If `retry` not specified:
- Default: **no retries** (`max_attempts: 1`).
- Adapter failure immediately propagates to caller.

### Examples from Tool Specs

**Logger tool** (no retries):
```yaml
# toolgen/specs/logger.tool.yaml
policy:
  network: deny
  filesystem: read
  secrets: deny
  retry:
    max_attempts: 1
  timeout_sec: 5
```

### Runner-Specific Enforcement

Retry logic implemented in **interpreter** (`language/interpreter.py`), not runners:
- Interpreter calls runner/adapter up to `max_attempts` times.
- Waits `delay_sec` between attempts.
- Timeline events track `attempt` number.
- Final failure includes all attempt errors.

---

## Policy Enforcement Flow

### Wave 3 Implementation Plan

1. **Daemon reads tool policy**:
   ```python
   tool_id = "http"
   policy = tools_registry["tools"][tool_id]["policy"]
   ```

2. **Daemon validates request against policy**:
   ```python
   if policy["network"] == "deny" and request_needs_network():
       return error("E_POLICY", "Tool http does not allow network access")
   ```

3. **Daemon spawns adapter with constraints**:
   ```python
   # Network constraint
   if policy["network"] == "deny":
       docker_args.append("--network=none")

   # Filesystem constraint
   if policy["filesystem"] == "read":
       docker_args.append("--read-only")

   # Secrets constraint
   if policy["secrets"] == "deny":
       env = {"PORT": str(port)}  # minimal env only
   ```

4. **Daemon logs policy decision**:
   ```python
   timeline_event = {
       "phase": "policy",
       "action": "enforce",
       "tool_id": "http",
       "policy": policy,
       "verdict": "allowed",
       "duration_ms": 0.5
   }
   ```

5. **Adapter executes within constraints**:
   - Network access blocked by Docker/iptables.
   - Filesystem access restricted by mount options.
   - Secrets filtered from environment.

6. **Violations logged**:
   ```python
   if adapter_attempted_forbidden_action():
       timeline_event = {
           "phase": "policy",
           "action": "violation",
           "tool_id": "http",
           "violation_type": "network",
           "status": "denied",
           "error.code": "E_POLICY"
       }
   ```

---

## Timeline Events for Policy Enforcement

### Policy Check Event

Emitted before adapter invocation:

```json
{
  "phase": "policy",
  "action": "check",
  "tool_id": "http",
  "policy": {
    "network": "allow",
    "filesystem": "deny",
    "secrets": "deny",
    "timeout_sec": 60
  },
  "verdict": "allowed",
  "duration_ms": 0.3
}
```

### Policy Violation Event

Emitted if adapter attempts forbidden operation:

```json
{
  "phase": "policy",
  "action": "violation",
  "tool_id": "storage",
  "violation_type": "filesystem",
  "attempted_action": "write to /etc/hosts",
  "status": "denied",
  "error": {
    "code": "E_POLICY",
    "message": "Tool storage attempted to write outside workspace"
  },
  "duration_ms": 1.2
}
```

### Timeout Event

Emitted if adapter exceeds `timeout_sec`:

```json
{
  "phase": "call",
  "action": "call",
  "alias": "slow_service",
  "status": "error",
  "error": {
    "code": "E_TIMEOUT",
    "message": "Tool http exceeded timeout_sec: 60"
  },
  "duration_ms": 60000
}
```

---

## Tool Policy Matrix

Summary of policy declarations across existing tool specs:

| Tool | Network | Filesystem | Secrets | Timeout |
| --- | --- | --- | --- | --- |
| `api-auth` | deny | deny | allow | - |
| `auth` | deny | deny | allow | - |
| `conditional` | deny | deny | deny | - |
| `http` | allow | deny | deny | 60 |
| `input` | deny | read | deny | - |
| `logger` | deny | read | deny | 5 |
| `loop` | deny | deny | deny | - |
| `output` | deny | write | deny | - |
| `rest` | allow | deny | deny | - |
| `storage` | deny | readwrite | deny | 30 |
| `transform` | deny | deny | deny | - |
| `validate-data` | deny | deny | deny | - |

**Patterns**:
- Network tools (`http`, `rest`): `network: allow`, no filesystem/secrets.
- Auth tools (`api-auth`, `auth`): `secrets: allow`, no network/filesystem.
- Storage tools (`storage`, `input`, `output`): filesystem access, no network/secrets.
- Pure compute tools (`conditional`, `loop`, `transform`, `validate-data`): all deny.

---

## Testing Policy Enforcement

### Unit Tests (Wave 3)

**`tests/daemon/test_policy_enforcement.py`**:
```python
def test_network_deny_blocks_http():
    policy = {"network": "deny", "filesystem": "deny", "secrets": "deny"}
    result = daemon.invoke_tool("http", {"url": "https://example.com"}, policy)
    assert result["ok"] is False
    assert result["error"]["code"] == "E_POLICY"

def test_filesystem_read_prevents_write():
    policy = {"network": "deny", "filesystem": "read", "secrets": "deny"}
    result = daemon.invoke_tool("output", {"path": "file.txt", "content": "..."}, policy)
    assert result["ok"] is False
    assert result["error"]["code"] == "E_POLICY"

def test_secrets_deny_filters_env():
    policy = {"network": "deny", "filesystem": "deny", "secrets": "deny"}
    env = daemon.build_adapter_env(policy, {"API_KEY": "secret123"})
    assert "API_KEY" not in env
    assert "PORT" in env  # always allowed

def test_timeout_terminates_adapter():
    policy = {"network": "allow", "filesystem": "deny", "secrets": "deny", "timeout_sec": 1}
    start = time.time()
    result = daemon.invoke_tool("http", {"url": "http://httpbin.org/delay/10"}, policy)
    elapsed = time.time() - start
    assert elapsed < 2  # terminated around 1 second
    assert result["error"]["code"] == "E_TIMEOUT"
```

### Integration Tests (Wave 3)

**`tests/integration/test_policy_e2e.py`**:
```python
def test_http_tool_respects_network_policy():
    # Spawn daemon, invoke http tool with network: deny
    # Verify request blocked before adapter invocation
    pass

def test_storage_tool_respects_filesystem_policy():
    # Invoke storage tool with filesystem: read
    # Attempt write operation
    # Verify operation blocked, timeline event logged
    pass
```

---

## Open Questions (Wave 3)

1. **Network allowlist wildcards**: Should `*.example.com` match `sub.sub.example.com`?
2. **Filesystem write-only enforcement**: How to prevent read-then-write patterns in `filesystem: write` mode?
3. **Secrets rotation**: How to handle credential expiry during long-running adapter execution?
4. **Policy versioning**: Should policy schema be versioned separately from tool schema?
5. **Cross-tool policies**: Should daemon enforce global policies (e.g., "no tool can access /etc")?

---

## References

- **Tool specs**: `toolgen/specs/*.tool.yaml`
- **Runner protocol**: `docs/development-guide.md`
- **Timeline events**: `docs/runner-timeline-parity.md`
- **Execution plan**: `docs/execution-plan.md` (Wave 3: Policy enforcement)
- **Daemon implementation**: `daemon/mcpd.py` (policy enforcement to be added in Wave 3)