# AssertLang SDKs

This directory will house the language-specific SDK guides that accompany Wave 2.

- **Python SDK**: MCP verb wrappers, timeline helper utilities, dependency bootstrap expectations.
- **Node SDK**: CommonJS/ESM usage, error taxonomy mapping, transport bootstrap guidance.

Each SDK doc should cover:
1. Installation (`pip install`, `npm install`), including how the daemon provisions caches.
2. Quickstart example that issues verbs (`state.apply`, `tool.call`, etc.) and reads timeline events.
3. Error handling guidelines aligning with `E_*` taxonomy and retry semantics.
4. Testing notes for local development (recommended mocks, fixtures, CI expectations).

Link back to `docs/runners/` (once created) for deep dives into runner internals and policy hooks.
