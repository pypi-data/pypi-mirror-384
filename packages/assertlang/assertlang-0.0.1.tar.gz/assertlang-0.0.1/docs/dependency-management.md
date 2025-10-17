# Dependency Management Overview

AssertLang prepares language-specific environments immediately before `run.start@v1` hands control to a runner. Plans (and registry defaults) describe their dependency needs in a `deps` block, the daemon enforces repository allowlists, and each runtime receives isolated caches under `.mcpd/<task>/env/` so host tooling remains untouched.

## Goals
- Deterministic environment prep per task, independent of the developer host.
- Allowlist-driven installs that fail fast when a plan requests an unapproved dependency.
- Sandboxed cache directories for every runtime to keep downloads local to the task.
- Registry-driven defaults so minimal plans stay ergonomic.

## Inputs & Metadata
- `plan.deps`: emitted by `plan.create@v1` and merged with registry defaults during `run_start_v1`.
- `data/tools_registry.json`: tool adapters may define baseline dependencies (merged unless the plan overrides them).
- `configs/dependency-allowlist.yaml`: enumerates approved packages/modules per language; entries may omit versions (the daemon treats `pkg` and `pkg@version` as compatible).

## Preparation by Language

### Python
- Create `.mcpd/<task>/env/python/venv` with `python -m venv` the first time a task touches Python deps.
- Install plan + registry requirements via `pip install --no-input --disable-pip-version-check` using the venv interpreter.
- Point `PIP_CACHE_DIR` at a hashed cache in `.mcpd/cache/python/<hash>/` (hash includes the requirement list + interpreter version) so download wheels are shared across tasks.
- Return `VIRTUAL_ENV` and update `PATH` to put the venv’s `bin/` (or `Scripts/`) first.

### Node / Next.js
- When `deps.node.packages` is non-empty, run `npm init -y` (if `package.json` is missing) followed by `npm install --no-fund --no-audit --save=false <packages>`.
- Set `npm_config_cache` / `NPM_CONFIG_CACHE` to `.mcpd/cache/node/<hash>/` keyed by the requested packages so tarballs are reused.
- Add `node_modules/.bin` to `PATH` and ensure `/opt/homebrew/bin:/usr/local/bin` precede the existing PATH so `node` is discoverable inside Python venvs.
- If the allowlist specifies `registry.cache_ttl_days`, the daemon exports `PROMPTWARE_NODE_CACHE_TTL_DAYS` for runners to honour cache retention policies.

### Go
- Ensure `.mcpd/<task>/env/go` exists (for source + logging); shared caches live under `.mcpd/cache/go/<hash>/` where `<hash>` reflects the requested modules.
- Generate `source/go.mod` if absent (using `deps.go.module_name` or `promptwareapp`).
- For each allowlisted module run `go get <module>` followed by `go mod tidy` with `GOMODCACHE`, `GOCACHE`, `GOPATH`, and `GO111MODULE=on` pointing to the shared cache directories.
- Return the three cache environment variables so the runner inherits the hydrated caches on future runs.

### .NET
- Create `.mcpd/<task>/env/dotnet` for generated project files; NuGet packages are cached in `.mcpd/cache/dotnet/<hash>/nuget` where `<hash>` reflects the requested packages.
- Render `deps/AssertLangDeps.csproj` containing `<PackageReference>` entries for each allowlisted package (version optional).
- Execute `dotnet restore` with `NUGET_PACKAGES` pointed at the shared cache. When the allowlist declares private feeds, the daemon renders a `NuGet.Config` (and passes `--configfile`) so restores respect those sources.
- Return `NUGET_PACKAGES` and `DOTNET_ROOT` so the runner can reuse the hydrated cache.
- Expose `PROMPTWARE_DOTNET_CACHE_TTL_DAYS` when the allowlist includes `cache_ttl_days`, enabling downstream tooling to prune shared caches.

### Rust
- Create `.mcpd/<task>/env/rust` for bootstrap manifests; `CARGO_HOME` and `RUSTUP_HOME` point to `.mcpd/cache/rust/<hash>/` where `<hash>` reflects the crate list.
- Render `bootstrap/Cargo.toml` referencing each crate (version optional; `*` is used when none supplied).
- Run `cargo fetch` inside the bootstrap workspace with `CARGO_HOME` and `RUSTUP_HOME` directed to the shared cache.
- Return both environment variables so subsequent `cargo` commands reuse the hydrated cache.
- When registries declare `token_env`, the daemon writes `.cargo/config.toml` entries and injects `CARGO_REGISTRIES_<NAME>_TOKEN` into the fetch environment so private registries remain authenticated without persisting secrets.

## Allowlist Enforcement
- The daemon raises `DependencyPolicyError` (`E_POLICY`) when requested dependencies fall outside `configs/dependency-allowlist.yaml`.
- Allowlist entries accept base names; specifying `pkg@version` or `module@v1` passes validation when `pkg` is present in the allowlist’s `allow` block.
- Registry defaults are validated the same way, preventing accidentally check-in of forbidden deps.

### Allowlist Schema At A Glance

```yaml
python:
  requirements:
    allow: [requests, jsonschema]
  env:
    PIP_INDEX_URL: https://pypi.org/simple

node:
  packages:
    allow: [axios]
  registry:
    url: https://registry.npmjs.org/
    token_env: NPM_TOKEN
    always_auth: false
    cache_ttl_days: 7

dotnet:
  packages:
    allow: [Newtonsoft.Json]
  cache_ttl_days: 30
  feeds:
    - name: nuget.org
      url: https://api.nuget.org/v3/index.json
    - name: internal
      url: https://nuget.example.com/v3/index.json
      token_env: NUGET_INTERNAL_PAT
      username: svc-account

rust:
  crates:
    allow: [serde]
  registries:
    - name: crates-io
      index: https://github.com/rust-lang/crates.io-index
    - name: internal
      index: https://git.example.com/rust/index
      token_env: CARGO_INTERNAL_TOKEN
```

### Private Registry Hooks
- Allowlist entries can inject environment overrides via an `env` block (e.g., `GO_ENV`, `PIP_INDEX_URL`, `NPM_CONFIG_REGISTRY`). The daemon merges these values into the subprocess environment during dependency prep.
- Node registries may specify `token_env` and `cache_ttl_days`; `_prepare_dependencies` pulls tokens from the host environment, sets `PROMPTWARE_NODE_CACHE_TTL_DAYS`, and keeps credentials scoped to the install command.
- `.NET` feeds can list private sources with optional `token_env`, `username_env`, or `password_env`. The daemon emits a temporary `NuGet.Config` with `<packageSourceCredentials>` and exports `PROMPTWARE_DOTNET_CACHE_TTL_DAYS` for downstream usage.
- Rust registries support `token_env`, prompting `_prepare_dependencies` to write `.cargo/config.toml` entries and expose `CARGO_REGISTRIES_<NAME>_TOKEN` during `cargo fetch`.
- Future enhancements will expand mirror support and retention policies (e.g., cache pruning) beyond the current TTL hints.

## Failure Handling
- Missing toolchains (`go`, `dotnet`, `cargo`, `npm`, etc.) trigger `DependencyError` which returns an `E_BUILD` response.
- Command output is streamed into `.mcpd/<task>/logs/run.log` so failures include actionable tracebacks.
- Ports leased for the task are released immediately when dependency prep fails.

## Future Improvements
- Shared caches keyed by dependency manifest hashes so repeated tasks reuse downloads without breaking isolation.
- Private registry support (custom npm registries, NuGet feeds, Cargo registries) driven by allowlist metadata.
- CLI helpers (`promptware deps check`, `promptware deps trim-cache`) to inspect the merged dependency view and manage caches without editing YAML manually.

## CLI Helpers
- Run `promptware deps check [--plan plan.json]` (or the underlying `python scripts/show_dependency_allowlist.py`) to emit a JSON summary of the current allowlist, optional merged plan + registry deps, and any violations before invoking `run.start@v1`.
- Use `promptware deps trim-cache [--dry-run] [--default-ttl-days N]` to prune `.mcpd/cache` based on allowlist TTL hints; the daemon automatically invokes the same logic on startup, but the CLI command lets operators inspect proposed removals or tune policies.

Keep this document current as new languages or caching strategies land.
