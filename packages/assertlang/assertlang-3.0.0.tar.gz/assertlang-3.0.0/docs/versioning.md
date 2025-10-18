# Versioning

## Framework Versions
- Global versions: `v1`, `v2`, etc.
- Apply to core MCP verbs, runtime, CLI.

## Tool Versions
- Each tool tagged with semantic version: `tool@1.0.0`
- Breaking changes → major version bump

## Local Runs
- Programs do **not** increment framework version.
- Local `pw` scripts can pin tool versions.

## Policy
- Backward compatible for 2 major versions.
- Deprecated tools flagged with warnings.