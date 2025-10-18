# Agent Handoff Guide

This document defines expectations for agents (AI or human) picking up AssertLang development work mid-stream.

---

## Context Discovery

When starting work on AssertLang:

1. **Read execution-plan.md first** — Understand current Wave status, completed milestones, and pending tasks.
2. **Check the test suite** — Run `python3 -m pytest tests/ -q` to validate your local environment.
3. **Review recent commits** — `git log --oneline -10` shows the last 10 changes and helps orient to active areas.
4. **Identify your focus area**:
   - DSL work → `language/`, `docs/promptware-dsl-*.md`
   - Tool adapters → `tools/`, `docs/toolgen-*.md`, adapter smoke tests in `tests/tools/`
   - Runner protocol → `runners/`, `docs/development-guide.md`
   - SDK design → `docs/sdk/`

---

## Communication Protocol

### Between Agents

- **Status snapshots**: When handing off, provide a concise summary of what you completed, what failed, and what's next.
- **Timeline alignment**: If working on runner/interpreter changes, verify timeline event schema stays consistent across languages.
- **Test results**: Always report test outcomes. If tests fail, document error codes and reproduction steps.

### With Humans

- **Ask before destructive changes**: Confirm before modifying core DSL grammar, runner protocol schemas, or published SDK APIs.
- **Propose architectural shifts**: If you identify a better approach (e.g., different serialization format, container orchestration strategy), document trade-offs and get approval.
- **Report blockers immediately**: Missing dependencies, unclear specs, or contradictory requirements should surface early.

---

## Development Workflow Expectations

### Source of Truth & Branching

- `upstream/main` is the production branch. Never push directly.
- Planning artifacts (`.claude/Task Agent*/`) live on `planning/master-plan` (fork only).
- Implementation work happens on `feature/<mission>` branches created from `upstream/main` and pushed to `origin`.
- First-time setup: create planning branch once
  ```bash
  git checkout -b planning/master-plan
  git push origin HEAD:planning/master-plan
  git checkout feature/<mission>
  ```

**One-command setup for any mission**
```
python scripts/agent_sync.py start --mission TA<n>
```
The helper script:
1. Verifies the working tree is clean.
2. Fetches `origin/planning/master-plan` and the mission feature branch.
3. Checks out `feature/<mission>` and rebases on `origin`.
4. Writes the mission brief under `missions/TA<n>/mission.md` (ignored by git).

To log progress (without touching feature branches):
```
python scripts/agent_sync.py log --mission TA<n> --entry "What changed"
```
This appends an entry to the mission progress file on `planning/master-plan` using a temporary worktree and pushes it to origin.

### Local Testing

- Run language-specific smoke tests before committing adapter changes:
  ```bash
  python3 -m pytest tests/tools/test_node_adapters.py
  python3 -m pytest tests/tools/test_go_adapters.py
  python3 -m pytest tests/tools/test_rust_adapters.py
  python3 -m pytest tests/tools/test_dotnet_adapters.py
  ```
- For .NET, set `DOTNET_BIN` if using a non-standard SDK path.
- For Rust, ensure `cargo` is in `$PATH` and nightly toolchain is installed if required.

### Commit Hygiene

- Keep commits focused: one logical change per commit.
- Reference Wave/task tracker items in commit messages when applicable.
- Avoid committing build artifacts (`bin/`, `obj/`, `node_modules/`, `target/`).

### Documentation Updates

- If you change runner protocol, update `docs/development-guide.md`.
- If you add DSL syntax, update `docs/promptware-dsl-spec.md` and regenerate examples.
- If you introduce new toolgen templates, document them in `docs/toolgen-*-adapter-template.md`.

---

## Wave-Specific Handoff Notes

### Wave 2 (Current)

**Goal**: Multi-language adapter parity across Node/Go/Rust/.NET.

**Key files**:
- Adapter templates: `docs/toolgen-{node,go,rust,dotnet}-adapter-template.md`
- Smoke harnesses: `tests/tools/test_{node,go,rust,dotnet}_adapters.py`
- Runner specs: `docs/development-guide.md` § Runner Protocol Essentials

**Open work**:
- Expand test fixtures beyond `file_reader` and `json_validator` to cover more of the 36 tools.
- Compare runner timeline outputs across languages; document deltas.
- Prototype Python/Node SDK packages with MCP verb wrappers.
- Wire `scripts/run_test_batches.sh` into CI.

**Handoff checklist**:
- [ ] All four language smoke tests pass locally.
- [ ] New fixtures added to `tests/fixtures/{node,go,rust,dotnet}_adapters/`.
- [ ] Any runner protocol changes documented in development-guide.md.
- [ ] execution-plan.md task tracker updated with completed items.

### Wave 3 (Upcoming)

**Goal**: Policy enforcement, marketplace CLI, developer onboarding docs.

**Handoff prep**:
- Ensure Wave 2 runner parity is complete before starting policy hooks.
- Document policy hook schema (network/filesystem/secrets) in a new `docs/policy-hooks.md`.
- Marketplace commands should reuse existing tool suite; no new external dependencies unless justified.

---

## Troubleshooting Common Issues

| Symptom | Likely Cause | Fix |
| --- | --- | --- |
| `pytest` hangs on adapter tests | Missing runtime (node/go/cargo/dotnet) in `$PATH` | Install runtime or skip tests with `-k 'not adapter'` |
| Timeline events missing fields | Runner envelope schema mismatch | Check `runners/*/` for envelope structure; align with Python reference |
| Go adapter compile errors | Ephemeral module missing dependencies | Ensure `go.sum` generation logic in daemon is working |
| .NET adapter fails to load | SDK version mismatch (expects net7.0) | Set `DOTNET_BIN` to a 7.x SDK or update target framework |

---

## Cross-Agent Coordination

When multiple agents work in parallel:

- **Declare your scope** early (e.g., "I'm working on Rust adapter fixtures for tools 10-15").
- **Avoid overlapping edits** to the same files; coordinate via shared task tracker or execution-plan.md.
- **Merge frequently** to reduce conflicts.
- **Run full test suite** before declaring a handoff complete.

---

## Exit Checklist

Before handing off to the next agent or human:

- [ ] All local tests pass (`make test` or `pytest tests/`).
- [ ] execution-plan.md reflects your changes (task tracker, status notes).
- [ ] Any new files added to `.gitignore` if they're build artifacts.
- [ ] Commit message explains *why* the change was made, not just *what* changed.
- [ ] No commented-out code or debug prints left behind unless explicitly documented.

---

Keep this file in sync with `execution-plan.md` so handoffs remain seamless.

---

## CI/CD & Operator Prompts

- **“Start mission TA<n>”** → run `python scripts/agent_sync.py start --mission TA<n>`; obey the mission brief under `missions/`.
- **“Log progress for TA<n>”** → run `python scripts/agent_sync.py log --mission TA<n> --entry "…"` to append on `planning/master-plan`.
- **“Open a PR for <branch>”** → ensure tests pass, push `feature/<mission>` to origin, then open a PR targeting `upstream/main`.
- **“Ship version <tag>”** → after merge, tag release (`git tag vX.Y.Z`), push to both remotes, and rely on publish workflow (or run manual release script until automation lands).

### Integration Workflow

- Use `scripts/integration_run.sh` to merge all mission branches into `integration/nightly`, run tests, and prepare review builds.
- Resolve conflicts on `integration/nightly`, re-run the script, then push the integration branch and open a PR to `upstream/main`.
- After PR approval, run release tagging/publish steps.

### Planning Branch Maintenance

- Modify mission briefs/progress logs on `planning/master-plan` only. Feature branches should stay free of `.claude/` and `missions/`.
- To edit missions manually:
  ```
  git checkout -b planning/master-plan origin/planning/master-plan
  # edit files
  git add --force .claude/Task\ Agent\ */ta*-current-*.md
  git commit -m "Update missions"
  git push origin HEAD:planning/master-plan
```
- The helper script will always pull the latest mission snapshot before agents begin work.
- Update the roster table in `CLAUDE.md` whenever agents are reassigned or complete missions so every task knows which branch and status belongs to each TA<n>.
