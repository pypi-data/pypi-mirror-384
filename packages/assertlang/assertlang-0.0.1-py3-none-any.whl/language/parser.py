from __future__ import annotations

import ast
import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple, Union


class PWParseError(ValueError):
    """Raised when the Promptware DSL cannot be parsed."""

    def __init__(self, message: str, *, code: str = "E_SYNTAX") -> None:
        super().__init__(message)
        self.code = code

    def __str__(self) -> str:  # pragma: no cover - trivial formatting
        base = super().__str__()
        if base.startswith(f"[{self.code}]"):
            return base
        return f"[{self.code}] {base}"


@dataclass
class PWProgram:
    prompt: Optional[str] = None
    plan: Optional[Dict[str, Any]] = None


@dataclass
class _PlanBuilder:
    prompt: Optional[str] = None
    lang: Optional[str] = None
    start: Optional[str] = None
    files: List[Dict[str, Any]] = field(default_factory=list)
    deps: Dict[str, Dict[str, List[str]]] = field(default_factory=dict)
    assumptions: List[str] = field(default_factory=list)
    tools: Dict[str, str] = field(default_factory=dict)  # alias -> tool id
    actions: List[Dict[str, Any]] = field(default_factory=list)


def parse_pw(text: str) -> PWProgram:
    stripped = text.strip()
    if not stripped:
        return PWProgram(prompt=None, plan=None)
    try:
        plan = _parse_dsl(text)
        prompt = plan.pop("prompt", None)
        return PWProgram(prompt=prompt, plan=plan)
    except PWParseError:
        return PWProgram(prompt=stripped, plan=None)


def _parse_dsl(text: str) -> Dict[str, Any]:
    builder = _PlanBuilder()
    lines = text.splitlines()
    stack: List[Tuple[str, int, Any]] = [("block", 0, builder.actions)]

    def current_actions() -> List[Dict[str, Any]]:
        if not stack or stack[-1][0] != "block":
            raise PWParseError("Internal parser error: expected block context", code="E_SYNTAX")
        return stack[-1][2]

    i = 0
    total = len(lines)
    while i < total:
        raw_line = lines[i]
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            i += 1
            continue

        indent = len(raw_line) - len(raw_line.lstrip(" "))
        if indent % 2 != 0:
            raise PWParseError(
                f"Indentation must be multiples of two spaces (line {i+1})",
                code="E_SYNTAX",
            )

        while stack and indent < stack[-1][1]:
            ctx, _, payload = stack.pop()
            if ctx == "file":
                entry = payload
                content = "\n".join(entry["lines"]).rstrip("\n")
                builder.files.append({"path": entry["path"], "content": content})

        if stack[-1][0] == "file" and indent >= stack[-1][1]:
            entry = stack[-1][2]
            entry["lines"].append(raw_line[stack[-1][1]:])
            i += 1
            continue

        if stack and stack[-1][0] == "state" and indent <= stack[-1][1]:
            stack.pop()

        stripped = raw_line.strip()
        tokens = _split_line(stripped)
        if not tokens:
            i += 1
            continue

        head, args = tokens[0], tokens[1:]

        if stack and stack[-1][0] == "fanout" and head not in {"case", "case:"}:
            stack.pop()

        if head == "file" and stripped.endswith(":"):
            path_token = stripped[5:-1].strip()
            if not path_token:
                raise PWParseError(f"Missing path for file on line {i+1}", code="E_SYNTAX")
            entry = {"path": _strip_quotes(path_token), "lines": []}
            stack.append(("file", indent + 2, entry))
            i += 1
            continue

        if head == "lang":
            if not args:
                raise PWParseError("lang directive requires a value", code="E_SYNTAX")
            builder.lang = args[0]
        elif head == "start":
            if not args:
                raise PWParseError("start directive requires a command", code="E_SYNTAX")
            builder.start = " ".join(args)
        elif head == "prompt":
            builder.prompt = " ".join(args)
        elif head == "assume":
            if not args:
                raise PWParseError("assume directive requires text", code="E_SYNTAX")
            builder.assumptions.append(" ".join(args))
        elif head == "dep":
            if len(args) < 2:
                raise PWParseError("dep directive requires language and group", code="E_SYNTAX")
            lang = args[0]
            group = args[1]
            values = args[2:]
            if not values:
                raise PWParseError("dep directive requires at least one value", code="E_SYNTAX")
            lang_deps = builder.deps.setdefault(lang, {})
            group_list = lang_deps.setdefault(group, [])
            group_list.extend(values)
        elif head == "tool":
            if len(args) < 3 or args[1] != "as":
                raise PWParseError(
                    "tool directive must be in the form 'tool <id> as <alias>'",
                    code="E_SYNTAX",
                )
            builder.tools[args[2]] = args[0]
        elif head == "call":
            if not args:
                raise PWParseError("call directive requires an alias", code="E_SYNTAX")
            alias = args[0]
            if alias not in builder.tools:
                raise PWParseError(
                    f"call references undefined tool alias '{alias}'",
                    code="E_PLAN_REF",
                )
            result_alias = alias
            kv_args = args[1:]
            if "as" in kv_args:
                idx = kv_args.index("as")
                if idx + 1 >= len(kv_args):
                    raise PWParseError("call 'as' directive requires a result alias", code="E_SYNTAX")
                result_alias = kv_args[idx + 1]
                kv_args = kv_args[:idx] + kv_args[idx + 2 :]
            payload, expects, retry_cfg = _parse_key_values(kv_args)
            payload = _normalise_payload(payload)
            retry_meta = _normalise_retry(retry_cfg)
            current_actions().append(
                {
                    "type": "call",
                    "alias": alias,
                    "result": result_alias,
                    "payload": payload,
                    "expects": expects,
                    "retry": retry_meta,
                }
            )
        elif head == "let":
            remainder = stripped[len("let") :].strip()
            if "=" not in remainder:
                raise PWParseError("let directive requires an assignment", code="E_SYNTAX")
            target_text, value_text = remainder.split("=", 1)
            target = target_text.strip()
            if not target:
                raise PWParseError("let directive requires a target name", code="E_SYNTAX")
            value_literal = value_text.strip()
            if not value_literal:
                raise PWParseError("let directive requires a value", code="E_SYNTAX")
            value = _decode_value(value_literal)
            current_actions().append({"type": "let", "target": target, "value": value})
        elif head == "fanout" and stripped.endswith(":"):
            source_token = stripped[len("fanout") : -1].strip()
            if not source_token:
                raise PWParseError("fanout directive requires a source alias", code="E_SYNTAX")
            source_alias = _strip_quotes(source_token)
            entry = {"type": "fanout", "source": source_alias, "cases": []}
            current_actions().append(entry)
            stack.append(("fanout", indent, entry))
            i += 1
            continue
        elif head in {"case", "case:"} and stripped.endswith(":"):
            if not stack or stack[-1][0] != "fanout":
                raise PWParseError("case directive must appear within a fanout block", code="E_SYNTAX")
            _, fanout_indent, fanout_entry = stack[-1]
            if indent != fanout_indent:
                raise PWParseError("case indentation must align with fanout", code="E_SYNTAX")
            scenario = stripped[5:-1].strip()
            cases_list = fanout_entry.setdefault("cases", [])
            index = len(cases_list)
            label = _normalise_case_label(scenario or None, index, {c.get("label") for c in cases_list if c.get("label")})
            case_entry: Dict[str, Any] = {"when": scenario or None, "label": label, "actions": []}
            cases_list.append(case_entry)
            stack.append(("block", indent + 2, case_entry["actions"]))
            i += 1
            continue
        elif head == "merge":
            mode: Optional[str] = None
            bucket_key: Optional[str] = None
            cursor = 0
            if cursor < len(args) and args[cursor] in {"append", "collect"}:
                mode = args[cursor]
                cursor += 1
                if cursor >= len(args):
                    raise PWParseError("merge append/collect requires 'into <target>'", code="E_SYNTAX")
                if args[cursor] != "into":
                    bucket_key = args[cursor]
                    cursor += 1
            elif cursor < len(args) and args[cursor] == "dict":
                mode = "dict"
                cursor += 1
            if cursor >= len(args) or args[cursor] != "into":
                raise PWParseError("merge directive must be 'merge into <alias> <source> ...'", code="E_SYNTAX")
            cursor += 1
            if cursor >= len(args):
                raise PWParseError("merge directive requires target alias and at least one source", code="E_SYNTAX")
            target_alias = args[cursor]
            cursor += 1
            if cursor >= len(args):
                raise PWParseError("merge directive requires at least one source", code="E_SYNTAX")
            source_tokens = args[cursor:]
            sources: List[Dict[str, str]] = []
            idx = 0
            while idx < len(source_tokens):
                source = source_tokens[idx]
                alias = None
                if idx + 2 < len(source_tokens) and source_tokens[idx + 1] == "as":
                    alias = source_tokens[idx + 2]
                    idx += 3
                else:
                    idx += 1
                sources.append({"path": source, "alias": alias})
            merge_action: Dict[str, Any] = {
                "type": "merge",
                "target": target_alias,
                "sources": sources,
            }
            if mode:
                merge_action["mode"] = mode
            if bucket_key:
                merge_action["append_key"] = bucket_key
            current_actions().append(merge_action)
        elif head in {"parallel", "parallel:"} and stripped.endswith(":"):
            node = {"type": "parallel", "branches": []}
            current_actions().append(node)
            stack.append(("branches", indent + 2, node))
            i += 1
            continue
        elif head in {"branch", "branch:"} and stripped.endswith(":"):
            if not stack or stack[-1][0] != "branches":
                raise PWParseError("branch directive must appear within a parallel block", code="E_SYNTAX")
            _, branch_indent, parallel_node = stack[-1]
            if indent != branch_indent:
                raise PWParseError("branch indentation must align with parallel block", code="E_SYNTAX")
            name_token = stripped[6:-1].strip()
            branch_name = _strip_quotes(name_token) if name_token else None
            branch = {"name": branch_name, "actions": []}
            parallel_node["branches"].append(branch)
            stack.append(("block", indent + 2, branch["actions"]))
            i += 1
            continue
        elif head == "state" and stripped.endswith(":"):
            state_name = stripped[len("state") : -1].strip()
            if not state_name:
                raise PWParseError("state block requires a name", code="E_SYNTAX")
            node = {"type": "state", "name": state_name, "actions": []}
            current_actions().append(node)
            stack.append(("state", indent, node))
            stack.append(("block", indent + 2, node["actions"]))
        elif head == "if" and stripped.endswith(":"):
            condition = stripped[3:-1].strip()
            node = {"type": "if", "condition": condition, "then": [], "else": None}
            current_actions().append(node)
            stack.append(("if", indent, node))
            stack.append(("block", indent + 2, node["then"]))
        elif head in {"else", "else:"} and stripped.endswith(":"):
            if not stack or stack[-1][0] != "if":
                raise PWParseError("else without matching if", code="E_SYNTAX")
            _, if_indent, node = stack[-1]
            if indent != if_indent:
                raise PWParseError("else must align with matching if", code="E_SYNTAX")
            if node.get("else") is not None:
                raise PWParseError("if already has an else block", code="E_SYNTAX")
            node["else"] = []
            stack.append(("block", indent + 2, node["else"]))
        else:
            raise PWParseError(f"Unknown directive '{head}' on line {i+1}", code="E_SYNTAX")

        i += 1

    while len(stack) > 1:
        ctx, _, payload = stack.pop()
        if ctx == "file":
            entry = payload
            content = "\n".join(entry["lines"]).rstrip("\n")
            builder.files.append({"path": entry["path"], "content": content})

    if not builder.files and not builder.actions:
        raise PWParseError("DSL must declare at least one file block or actions", code="E_SYNTAX")
    if not builder.start and builder.files:
        builder.start = f"python {builder.files[0]['path']}"

    plan = {
        "lang": builder.lang or "python",
        "files": builder.files,
        "deps": builder.deps,
        "actions": builder.actions,
        "tools": builder.tools,
    }
    if builder.start:
        plan["start"] = builder.start
    if builder.assumptions:
        plan["assumptions"] = builder.assumptions
    return plan


def _split_line(line: str) -> List[str]:
    tokens: List[str] = []
    token = ''
    in_quote = False
    quote_char = ''
    brace_depth = 0
    bracket_depth = 0
    i = 0
    while i < len(line):
        ch = line[i]
        if in_quote:
            token += ch
            if ch == quote_char and (i == 0 or line[i - 1] != '\\'):
                in_quote = False
        else:
            if ch in ('"', "'"):
                in_quote = True
                quote_char = ch
                token += ch
            elif ch == '{':
                brace_depth += 1
                token += ch
            elif ch == '}':
                brace_depth = max(0, brace_depth - 1)
                token += ch
            elif ch == '[':
                bracket_depth += 1
                token += ch
            elif ch == ']':
                bracket_depth = max(0, bracket_depth - 1)
                token += ch
            elif ch.isspace() and brace_depth == 0 and bracket_depth == 0:
                if token:
                    tokens.append(token)
                    token = ''
            else:
                token += ch
        i += 1
    if token:
        tokens.append(token)
    return tokens


_REFERENCE_RE = re.compile(r"\$\{([^}]+)\}")


def _transform_condition(expr: str) -> str:
    expr = expr.strip()
    expr = _REFERENCE_RE.sub(lambda m: _path_to_expr(m.group(1).strip().split('.'), base_var="responses"), expr)
    _validate_expression(expr)
    return expr


ALLOWED_EXPRESSION_NODES = {
    ast.Expression,
    ast.BoolOp,
    ast.BinOp,
    ast.UnaryOp,
    ast.Compare,
    ast.Name,
    ast.Load,
    ast.Constant,
    ast.Subscript,
    ast.And,
    ast.Or,
    ast.Not,
    ast.Eq,
    ast.NotEq,
    ast.Lt,
    ast.LtE,
    ast.Gt,
    ast.GtE,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.Mod,
}


def _validate_expression(expr: str) -> None:
    try:
        node = ast.parse(expr, mode="eval")
    except SyntaxError as exc:
        raise PWParseError(f"Invalid expression '{expr}': {exc.msg}", code="E_SYNTAX") from exc

    class Visitor(ast.NodeVisitor):
        def generic_visit(self, node):
            if type(node) not in ALLOWED_EXPRESSION_NODES:
                raise PWParseError(
                    f"Disallowed expression component: {type(node).__name__}",
                    code="E_SYNTAX",
                )
            super().generic_visit(node)

    Visitor().visit(node)


def _parse_key_values(tokens: List[str]) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    result: Dict[str, Any] = {}
    expects: Dict[str, Any] = {}
    retry: Dict[str, Any] = {}
    for token in tokens:
        if "=" not in token:
            raise PWParseError(f"Expected key=value pair, got '{token}'", code="E_SYNTAX")
        key, value = token.split("=", 1)
        if key.startswith("expect."):
            expects[key[len("expect."):]] = _decode_value(value)
        elif key.startswith("retry."):
            retry[key[len("retry."):]] = _decode_value(value)
        else:
            result[key] = _decode_value(value)
    return result, expects, retry


def _decode_value(value: str) -> Any:
    stripped = _strip_quotes(value)
    ref = _maybe_reference(stripped)
    if ref is not None:
        return {"__ref__": ref}
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        literal = _parse_inline_literal(stripped)
        if literal is not None:
            return literal
        return stripped


def _maybe_reference(value: str) -> Optional[List[str]]:
    if value.startswith("${") and value.endswith("}"):
        inner = value[2:-1].strip()
        if not inner:
            raise PWParseError("Empty reference detected", code="E_PLAN_REF")
        parts = inner.split('.')
        if any(not part for part in parts):
            raise PWParseError(f"Invalid reference '{value}'", code="E_PLAN_REF")
        return parts
    return None


def _parse_inline_literal(text: str) -> Optional[Any]:
    candidate = text.strip()
    if not candidate or candidate[0] not in "{[":
        return None

    ref_map: Dict[str, List[str]] = {}

    def _ref_repl(match: re.Match[str]) -> str:
        token = match.group(0)
        ref = _maybe_reference(token)
        if ref is None:
            return token
        placeholder = f"__PW_REF_{len(ref_map)}__"
        ref_map[placeholder] = ref
        return f'"{placeholder}"'

    placeholder_json = _REFERENCE_RE.sub(_ref_repl, candidate)
    placeholder_json = placeholder_json.replace("'", '"')
    placeholder_json = re.sub(
        r'({|,)\s*([A-Za-z_][A-Za-z0-9_]*)\s*:',
        lambda m: f'{m.group(1)} "{m.group(2)}":',
        placeholder_json,
    )
    try:
        loaded = json.loads(placeholder_json)
    except json.JSONDecodeError:
        return None

    def _restore(obj: Any) -> Any:
        if isinstance(obj, str) and obj in ref_map:
            return {"__ref__": ref_map[obj]}
        if isinstance(obj, list):
            return [_restore(item) for item in obj]
        if isinstance(obj, dict):
            return {key: _restore(val) for key, val in obj.items()}
        return obj

    return _restore(loaded)




def _normalise_payload(flat: Dict[str, Any]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for key, value in flat.items():
        segments = key.split('.')
        if segments and segments[-1] == "from":
            segments = segments[:-1]
            value = _force_reference(key, value)
        _set_nested(result, segments, value)
    return result


def _set_nested(target: Dict[str, Any], path: List[str], value: Any) -> None:
    segments = _expand_path(path)
    if not segments:
        raise PWParseError("Empty assignment path", code="E_SYNTAX")
    cursor: Any = target
    for idx, segment in enumerate(segments[:-1]):
        next_segment = segments[idx + 1]
        if isinstance(segment, int):
            if not isinstance(cursor, list):
                raise PWParseError("List assignment requires list context", code="E_SYNTAX")
            while len(cursor) <= segment:
                cursor.append({} if not isinstance(next_segment, int) else [])
            cursor = cursor[segment]
        else:
            if not isinstance(cursor, dict):
                raise PWParseError("Dict assignment requires mapping context", code="E_SYNTAX")
            if segment not in cursor:
                cursor[segment] = [] if isinstance(next_segment, int) else {}
            cursor = cursor[segment]
    last = segments[-1]
    if isinstance(last, int):
        if not isinstance(cursor, list):
            raise PWParseError("List assignment requires list context", code="E_SYNTAX")
        while len(cursor) <= last:
            cursor.append(None)
        cursor[last] = value
    else:
        if not isinstance(cursor, dict):
            raise PWParseError("Dict assignment requires mapping context", code="E_SYNTAX")
        cursor[last] = value


PathSegment = Union[str, int]


def _expand_path(path: List[str]) -> List[PathSegment]:
    segments: List[PathSegment] = []
    for segment in path:
        segments.extend(_expand_segment(segment))
    return segments


def _expand_segment(segment: str) -> List[PathSegment]:
    parts: List[PathSegment] = []
    token = ""
    i = 0
    while i < len(segment):
        ch = segment[i]
        if ch == '[':
            if token:
                parts.append(token)
                token = ""
            end = segment.find(']', i)
            if end == -1:
                raise PWParseError(f"Malformed path segment '{segment}'", code="E_PLAN_REF")
            index_token = segment[i + 1 : end].strip()
            if not index_token.isdigit():
                raise PWParseError(f"List index must be numeric in '{segment}'", code="E_PLAN_REF")
            parts.append(int(index_token))
            i = end + 1
            continue
        token += ch
        i += 1
    if token:
        if token.isdigit():
            parts.append(int(token))
        else:
            parts.append(token)
    return parts


def _path_to_expr(path: List[str], *, base_var: str) -> str:
    expr = base_var
    for segment in _expand_path(path):
        if isinstance(segment, int):
            expr += f"[{segment}]"
        else:
            expr += f"[{json.dumps(segment)}]"
    return expr


def _force_reference(key: str, value: Any) -> Dict[str, Any]:
    if isinstance(value, dict) and "__ref__" in value:
        return value
    if isinstance(value, str):
        ref = _maybe_reference(value)
        if ref is not None:
            return {"__ref__": ref}
        parts = [part.strip() for part in value.split('.') if part.strip()]
        if not parts:
            raise PWParseError(f"Invalid reference '{value}' for key '{key}'", code="E_PLAN_REF")
        if not parts[0].isidentifier():
            raise PWParseError(
                f"Reference must start with alias identifier (got '{value}')",
                code="E_PLAN_REF",
            )
        return {"__ref__": parts}
    raise PWParseError(
        f"Reference assignment for '{key}' requires string value",
        code="E_PLAN_REF",
    )


def _strip_quotes(value: str) -> str:
    if value.startswith(("\"", "'")) and value.endswith(("\"", "'")) and len(value) >= 2:
        return value[1:-1]
    return value


def _to_python_literal(value: Any) -> str:
    literal = json.dumps(value, indent=4, sort_keys=True)
    literal = literal.replace("true", "True").replace("false", "False").replace("null", "None")
    return literal


def _normalise_retry(cfg: Dict[str, Any]) -> Dict[str, Any]:
    if not cfg:
        return {"max": 1, "delay": 0.0}
    max_attempts = int(cfg.get("max", 3))
    if max_attempts < 1:
        max_attempts = 1
    delay = float(cfg.get("delay", 0.0))
    if delay < 0:
        delay = 0.0
    return {"max": max_attempts, "delay": delay}


def _actions_need_sleep(actions: List[Dict[str, Any]]) -> bool:
    for action in actions:
        if action.get("type") == "call" and action.get("retry", {}).get("delay", 0) > 0:
            return True
        if action.get("type") == "if":
            if _actions_need_sleep(action.get("then", [])):
                return True
            if _actions_need_sleep(action.get("else", []) or []):
                return True
        if action.get("type") == "parallel":
            for branch in action.get("branches", []):
                if _actions_need_sleep(branch.get("actions", [])):
                    return True
    return False


def _actions_support_autofile(actions: List[Dict[str, Any]]) -> bool:
    for action in actions:
        if action.get("type") == "parallel":
            return False
        if action.get("type") == "if":
            if not _actions_support_autofile(action.get("then", [])):
                return False
            if not _actions_support_autofile(action.get("else", []) or []):
                return False
    return True


def _normalise_case_label(condition: Optional[str], index: int, existing: Set[str]) -> str:
    base = f"case_{index}"
    if condition:
        slug = re.sub(r"[^a-zA-Z0-9]+", "_", condition).strip("_")
        if slug:
            base = f"case_{slug.lower()}"
    candidate = base
    counter = 1
    while candidate in existing:
        candidate = f"{base}_{counter}"
        counter += 1
    return candidate

