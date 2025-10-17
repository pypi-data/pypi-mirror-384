# AssertLang DSL Formatter & Linter Plan

## Formatter (`pwfmt`, CLI skeleton)
- `promptware dsl format <file>`
- Normalise directives (keyword + single space, arguments sorted where applicable).
- Canonical indentation: directives at column 0; block bodies indented by two spaces.
- Ensure blank line separation between logical sections (files, calls, control blocks).
- Auto-quote strings with double quotes; normalise boolean/null tokens (True/False/None) for embedded Python.
- Reformat key/value arguments (`key=value`), align expect/retry tokens on the same line as the call.
- Idempotent output; provide `--check` to detect unformatted files.
- Normalize whitespace:
  - Directives at column 0 with a single space between keyword and arguments.
  - Indent block bodies by two spaces per nesting level (file contents, `if`, `else`).
  - Ensure one blank line between top-level directives of different types.
- Reformat key/value arguments:
  - Use `key=value` with double-quoted strings when needed; canonicalise lists by sorting.
  - `expect.<path>=<value>` tokens stay attached to their `call` line.
- Align multi-line file content by removing inconsistent tabs.
- Preserve comments but align to nearest directive.
- Provide an idempotent operation: running pwfmt multiple times should not change output.

## Linter (`pwlint`, CLI skeleton)
- `promptware dsl lint <file>` (exit code 0/1).
- Undefined tool aliases, unused tool outputs, missing `start` or `file` directives.
- Reference validation: `${alias.path}` must resolve; flag circular dependencies.
- Control-flow warnings: empty branches, unreachable `else`, improper indentation.
- Tool call diagnostics: missing retries where policies require them, expectation misuse.
- Optionally output JSON diagnostics for IDE integration.
- Undefined tool alias detection (call references a tool alias not declared).
- Unused alias warnings (tool alias never called, call result never referenced).
- Reference validation: `${alias.path}` points to existing alias path; support nested merges.
- Start command guardrails: warn if `start` missing or mismatched with `lang`.
- Branch analysis: check for empty bodies, unreachable `else`, missing indentation.
- Suggestions for repeated payload keys, duplicate deps.
- Provide exit codes (0 success, 1 warnings, 2 errors) for CI integration.

First iteration can embed formatter/linter in CLI (`promptware dsl format/lint`).
