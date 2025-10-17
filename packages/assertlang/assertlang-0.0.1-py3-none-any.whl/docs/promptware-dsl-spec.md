# AssertLang DSL Specification (Draft)

## 1. Grammar

The AssertLang DSL is a line-oriented, indentation-sensitive language. Directives begin in column 0 and block bodies are indented by two spaces per level. Comments (`# …`) run to the end of the line.

```
program        ::= statement*
statement      ::= metadata | action

metadata       ::= lang_decl | start_decl | prompt_decl | assume_decl
                 | dep_decl | tool_decl | file_block

lang_decl      ::= "lang" IDENT
start_decl     ::= "start" TEXT
prompt_decl    ::= "prompt" TEXT
assume_decl    ::= "assume" TEXT
dep_decl       ::= "dep" IDENT IDENT VALUE+
tool_decl      ::= "tool" IDENT "as" IDENT

file_block     ::= "file" PATH ":" NEWLINE INDENT file_line* DEDENT
file_line      ::= arbitrary text (preserved verbatim)

action         ::= call_stmt | let_stmt | if_block | parallel_block
                 | fanout_block | merge_stmt | state_block

call_stmt      ::= "call" IDENT call_modifier*
call_modifier  ::= arg_kv | expect_kv | retry_kv | result_alias
arg_kv         ::= KEY "=" VALUE
expect_kv      ::= "expect." PATH "=" VALUE
retry_kv       ::= "retry." KEY "=" VALUE
result_alias   ::= "as" IDENT

let_stmt       ::= "let" IDENT "=" VALUE

if_block       ::= "if" EXPR ":" NEWLINE INDENT action* DEDENT else_clause?
else_clause    ::= "else" ":" NEWLINE INDENT action* DEDENT

parallel_block ::= "parallel" ":" NEWLINE INDENT branch_block+ DEDENT
branch_block   ::= "branch" IDENT? ":" NEWLINE INDENT action* DEDENT

state_block    ::= "state" IDENT ":" NEWLINE INDENT action* DEDENT

fanout_block   ::= "fanout" IDENT ":" NEWLINE INDENT case_block+ DEDENT
case_block     ::= "case" EXPR? ":" NEWLINE INDENT action* DEDENT

merge_stmt     ::= "merge" merge_mode? "into" IDENT merge_source+
merge_mode     ::= "append" IDENT? | "collect" IDENT? | "dict"
merge_source   ::= PATH ("as" IDENT)?

VALUE          ::= reference | literal | inline_object | inline_list | TEXT
reference      ::= "${" PATH "}"
inline_object  ::= "{" (inline_pair ("," inline_pair)*)? "}"
inline_pair    ::= KEY ":" VALUE
inline_list    ::= "[" (VALUE ("," VALUE)*)? "]"
literal        ::= NUMBER | BOOLEAN | TEXT
PATH           ::= IDENT ("." IDENT | "[" NUMBER "]")*
IDENT          ::= /[A-Za-z_][A-Za-z0-9_-]*/
TEXT           ::= quoted string (single or double quotes)
NUMBER         ::= integer or floating literal
BOOLEAN        ::= "true" | "false"
```

Dataflow helpers follow two conventions:
- `input.from=${alias.data}` or `input.from=alias.data` compiles to structured references.
- `payload.section.item=value` expands into nested dictionaries and lists based on dotted or indexed paths.

## 2. Plan & Action Model

Parsing a `.pw` file produces `{ prompt?, plan? }`. When present, `plan` is a JSON object with the following shape:

- `lang`: target runtime (`python` by default).
- `start`: optional command executed after files are written (defaults to the first file when omitted).
- `files`: ordered list of `{ path, content }` blocks.
- `deps`: mapping `{ language: { group: [values...] } }` consumed by dependency bootstrap.
- `assumptions`: free-form strings that provide contextual hints.
- `tools`: `{ alias: tool_id }` bindings used during execution.
- `actions`: ordered list of directives executed by the interpreter.

Action nodes emitted by the parser:
- `call`: `{ type: "call", alias, result?, payload, expects, retry }`
  - Payload keys are nested using dot / index syntax; references become `{ "__ref__": [alias, ...] }`.
  - `expects` tracks `expect.<path>=<value>` clauses.
  - `retry` normalises to `{ "max": int, "delay": float }`.
- `let`: `{ type: "let", target, value }` where `value` may be a literal or reference.
- `if`: `{ type: "if", condition, then: [...], else: [...]? }`. Conditions support Python expressions with `${alias.path}` substitutions.
- `parallel`: `{ type: "parallel", branches: [{ name?, actions: [...] }] }`. Each branch receives a child scope but can read parent state.
- `fanout`: `{ type: "fanout", source, cases: [{ when?, label, actions: [...] }] }`. Case labels are slugified and stored for merges.
- `merge`: `{ type: "merge", target, sources: [{ path, alias? }...], mode?, append_key? }` supporting:
  - default: shallow copy of source objects into a new mapping;
  - `append`: concatenate list outputs into `append_key` (default `items`) or an alias;
  - `collect`: coerce each source (scalar or list) into an aggregate list;
  - `dict`: merge dictionaries (aliases keep payloads isolated).
- `state`: `{ type: "state", name, actions }` executes in an isolated scope and stores the result under `responses[name]`.

The interpreter records timeline events for every action. Error outcomes now include a `code` field so downstream tooling can apply consistent policy handling.

Lint rules currently warn when:
- Plans declare files without a `start` command.
- Tool calls omit expectations.
- Control-flow blocks (`parallel`, `fanout`, `state`) have empty bodies.
- `merge append` / `merge collect` sources do not look like list outputs; authors are nudged to reference `.items` or alias the result explicitly.

## 3. Error Taxonomy

| Code | Source | Example |
| --- | --- | --- |
| `E_SYNTAX` | Parser | Misaligned indentation, missing directive arguments. |
| `E_PLAN` | Interpreter plan validation | Missing `let` target, duplicate merge buckets. |
| `E_PLAN_REF` | Parser/interpreter reference resolution | Undefined tool alias or `${alias.path}` lookup. |
| `E_RUNTIME` | Interpreter execution | Tool failure, expectation mismatch, merge type mismatch. |

`PWParseError` and `PWExecutionError` normalise messages to `[CODE] message`. Timeline events bubble the same `code` to keep daemon and interpreter telemetry aligned.

## 4. Examples

```
lang python
start python app.py

file app.py:
  from promptware import http

assume downstream services respond within 200ms

tool rest.get as fetch
call fetch method=GET url="https://api.example.com" expect.status=200

state shared:
  fanout fetch:
  case ${fetch.data.status} == 200:
    call fetch as posts method=GET url="https://api.example.com/posts"
  case:
    let diagnostics.error = ${fetch}

merge append results into summary shared.fetch.case_fetch_data_status_200.items as posts
```

```
tool http as primary
call primary url="https://example.com" retry.max=3 retry.delay=1
let status = ${primary.data.status}
if ${status} == 200:
  call primary as confirmation url="https://example.com/confirm"
else:
  call primary as recovery url="https://status.example.com"
```

Keep this specification in sync with parser, formatter, and interpreter updates so Wave 1 remains well-documented.
