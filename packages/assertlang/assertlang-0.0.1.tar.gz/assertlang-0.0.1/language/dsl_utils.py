from __future__ import annotations

import json
import textwrap
from pathlib import Path
from typing import Iterable, List, Optional, Sequence

from .parser import PWParseError, _parse_dsl, parse_pw


def collect_pw_files(paths: Iterable[str] | None) -> List[Path]:
    files: List[Path] = []
    if not paths:
        paths = (".",)
    for raw in paths:
        p = Path(raw)
        if p.is_dir():
            files.extend(sorted(f for f in p.rglob("*.al") if f.is_file()))
        elif p.suffix == ".al" and p.exists():
            files.append(p)
    return files


def format_text(text: str) -> str:
    try:
        prog = parse_pw(text)
    except PWParseError:
        return _ensure_trailing_newline(text)
    if prog.plan is None:
        return _ensure_trailing_newline(textwrap.dedent(text))

    plan = prog.plan
    lines: List[str] = []

    if prog.prompt:
        lines.append(f"prompt {prog.prompt.strip()}")
    if plan.get("lang"):
        lines.append(f"lang {plan['lang']}")
    if plan.get("start"):
        lines.append(f"start {plan['start']}")

    files = plan.get("files", []) or []
    if files:
        if lines:
            lines.append("")
        for idx, file_entry in enumerate(files):
            lines.append(f"file {file_entry['path']}:")
            content = (file_entry.get("content") or "").splitlines()
            for line in content:
                lines.append(f"  {line}")
            if idx != len(files) - 1:
                lines.append("")

    deps = plan.get("deps", {}) or {}
    if deps:
        if lines and lines[-1] != "":
            lines.append("")
        for lang in sorted(deps):
            groups = deps[lang]
            for group in sorted(groups):
                values = " ".join(sorted(groups[group]))
                lines.append(f"dep {lang} {group} {values}".rstrip())

    assumptions = plan.get("assumptions", []) or []
    if assumptions:
        if lines and lines[-1] != "":
            lines.append("")
        for assumption in assumptions:
            lines.append(f"assume {assumption}")

    tools = plan.get("tools", {}) or {}
    if tools:
        if lines and lines[-1] != "":
            lines.append("")
        for alias, tool_id in sorted(tools.items(), key=lambda item: item[0]):
            lines.append(f"tool {tool_id} as {alias}")

    actions = plan.get("actions", []) or []
    if actions:
        if lines and lines[-1] != "":
            lines.append("")
        lines.extend(_format_actions(actions))

    while lines and lines[-1] == "":
        lines.pop()

    return "\n".join(lines).rstrip("\n") + "\n"


def lint_text(path: Path, text: str) -> List[str]:
    warnings: List[str] = []
    try:
        plan = _parse_dsl(text)
    except PWParseError as exc:
        message = str(exc)
        prog = parse_pw(text)
        if prog.plan is None and prog.prompt:
            warnings.append(f"{path}: file parses as prompt only (no plan)")
        else:
            warnings.append(f"{path}: {message}")
        return warnings

    has_actions = bool(plan.get("actions"))
    if not plan.get("files") and not has_actions:
        warnings.append(f"{path}: plan contains no files")
    if plan.get("files") and not plan.get("start"):
        warnings.append(f"{path}: plan missing start command")

    tools = plan.get("tools", {}) or {}
    warnings.extend(
        f"{path}: {message}" for message in _lint_actions(plan.get("actions", []) or [], tools)
    )
    warnings.extend(
        f"{path}: undefined reference to '{alias}'" for alias in _check_references(plan)
    )
    return warnings


def _format_actions(actions: List[dict], indent: str = "") -> List[str]:
    lines: List[str] = []
    for action in actions:
        if action.get("type") == "call":
            tokens = [f"{indent}call", action["alias"]]
            result_alias = action.get("result") or action["alias"]
            if result_alias != action["alias"]:
                tokens.extend(["as", result_alias])
            for key in sorted(action.get("payload", {})):
                value = action["payload"][key]
                ref = _as_reference(value)
                if ref is not None:
                    tokens.append(f"{key}.from={_stringify_reference(ref)}")
                else:
                    tokens.append(f"{key}={_encode_value(value)}")
            for key, value in sorted((action.get("expects") or {}).items()):
                tokens.append(f"expect.{key}={_encode_value(value)}")
            retry = action.get("retry") or {}
            if int(retry.get("max", 1)) > 1:
                tokens.append(f"retry.max={int(retry['max'])}")
            if float(retry.get("delay", 0.0)) > 0:
                tokens.append(f"retry.delay={retry['delay']}")
            lines.append(" ".join(tokens))
            for flow in action.get("dataflow", []) or []:
                lines.append(f"{indent}  case {flow.get('when')}:")
                lines.extend(_format_actions(flow.get("actions", []), indent + "      "))
        elif action.get("type") == "let":
            value = action.get("value")
            lines.append(f"{indent}let {action['target']} = {_encode_value(value)}")
        elif action.get("type") == "parallel":
            lines.append(f"{indent}parallel:")
            for branch in action.get("branches", []):
                branch_name = branch.get("name")
                prefix = f"{indent}  branch"
                if branch_name:
                    prefix += f" {branch_name}"
                prefix += ":"
                lines.append(prefix)
                lines.extend(_format_actions(branch.get("actions", []), indent + "    "))
        elif action.get("type") == "fanout":
            source = action.get("source")
            lines.append(f"{indent}fanout {source}:")
            for case in action.get("cases", []):
                condition = case.get("when")
                label = condition if condition else ""
                suffix = f" {label}" if label else ""
                lines.append(f"{indent}case{suffix}:")
                lines.extend(_format_actions(case.get("actions", []), indent + "  "))
        elif action.get("type") == "merge":
            tokens = [f"{indent}merge"]
            mode = action.get("mode")
            if mode:
                tokens.append(mode)
            tokens.extend(["into", action["target"]])
            for src in action.get("sources", []):
                if isinstance(src, dict):
                    path = src.get("path")
                    alias = src.get("alias")
                else:
                    path = str(src)
                    alias = None
                tokens.append(path)
                if alias:
                    tokens.extend(["as", alias])
            lines.append(" ".join(tokens))
        elif action.get("type") == "state":
            name = action.get("name")
            lines.append(f"{indent}state {name}:")
            lines.extend(_format_actions(action.get("actions", []), indent + "  "))
        elif action.get("type") == "if":
            lines.append(f"{indent}if {action['condition']}:")
            lines.extend(_format_actions(action.get("then", []), indent + "  "))
            else_block = action.get("else")
            if else_block:
                lines.append(f"{indent}else:")
                lines.extend(_format_actions(else_block, indent + "  "))
    return lines


def _lint_actions(actions: List[dict], tools: dict) -> List[str]:
    warnings: List[str] = []
    for action in actions:
        if action.get("type") == "call":
            alias = action["alias"]
            if alias not in tools:
                warnings.append(f"call '{alias}' references unknown tool")
            if not action.get("expects"):
                warnings.append(f"call '{alias}' has no expectations")
        elif action.get("type") == "let":
            target = action.get("target")
            if not target:
                warnings.append("let directive missing target")
        elif action.get("type") == "parallel":
            branches = action.get("branches") or []
            if not branches:
                warnings.append("parallel block has no branches")
            for branch in branches:
                branch_actions = branch.get("actions", [])
                if not branch_actions:
                    warnings.append("parallel branch has no actions")
                warnings.extend(_lint_actions(branch_actions, tools))
        elif action.get("type") == "fanout":
            cases = action.get("cases") or []
            if not cases:
                warnings.append("fanout block has no cases")
            for case in cases:
                case_actions = case.get("actions", [])
                if not case_actions:
                    warnings.append("fanout case has no actions")
                warnings.extend(_lint_actions(case_actions, tools))
        elif action.get("type") == "if":
            if not action.get("then"):
                warnings.append("if block has no body")
            warnings.extend(_lint_actions(action.get("then", []), tools))
            else_block = action.get("else")
            if else_block:
                warnings.extend(_lint_actions(else_block, tools))
        elif action.get("type") == "state":
            state_actions = action.get("actions") or []
            if not state_actions:
                warnings.append("state block has no actions")
            warnings.extend(_lint_actions(state_actions, tools))
        elif action.get("type") == "merge" and action.get("mode") in {"append", "collect"}:
            for source in action.get("sources", []):
                path = source.get("path") if isinstance(source, dict) else str(source)
                if path and not path.endswith("items") and source.get("alias") is None:
                    warnings.append(
                        "merge append/collect expects list outputs; consider using '.items' or an alias"
                    )
    return warnings


def _check_references(plan: dict) -> List[str]:
    known_aliases = set(plan.get("tools", {}).keys())
    seen_aliases = set()
    undefined: List[str] = []

    def visit(actions: List[dict]) -> None:
        for action in actions:
            if action.get("type") == "call":
                alias = action["alias"]
                result = action.get("result") or alias
                seen_aliases.add(result)
                payload = action.get("payload", {}) or {}
                expects = action.get("expects", {}) or {}
                retry = action.get("retry", {}) or {}
                _extract_refs(payload, undefined, known_aliases, seen_aliases)
                _extract_refs(expects, undefined, known_aliases, seen_aliases)
                _extract_refs(retry, undefined, known_aliases, seen_aliases)
            elif action.get("type") == "let":
                target = action.get("target")
                if target:
                    seen_aliases.add(target)
                value = action.get("value")
                if isinstance(value, dict) and "__ref__" in value:
                    alias = value["__ref__"][0]
                    if alias not in known_aliases and alias not in seen_aliases:
                        undefined.append(alias)
            elif action.get("type") == "parallel":
                for branch in action.get("branches", []):
                    branch_seen = set(seen_aliases)
                    visit_branch(branch.get("actions", []), branch_seen)
            elif action.get("type") == "if":
                visit(action.get("then", []))
                visit(action.get("else", []) or [])

    def visit_branch(actions: List[dict], branch_seen: set[str]) -> None:
        for action in actions:
            if action.get("type") == "call":
                alias = action["alias"]
                result = action.get("result") or alias
                branch_seen.add(result)
                payload = action.get("payload", {}) or {}
                expects = action.get("expects", {}) or {}
                retry = action.get("retry", {}) or {}
                _extract_refs(payload, undefined, known_aliases, branch_seen)
                _extract_refs(expects, undefined, known_aliases, branch_seen)
                _extract_refs(retry, undefined, known_aliases, branch_seen)
            elif action.get("type") == "let":
                target = action.get("target")
                if target:
                    branch_seen.add(target)
                value = action.get("value")
                if isinstance(value, dict) and "__ref__" in value:
                    alias = value["__ref__"][0]
                    if alias not in known_aliases and alias not in branch_seen:
                        undefined.append(alias)
            elif action.get("type") == "parallel":
                for branch in action.get("branches", []):
                    visit_branch(branch.get("actions", []), set(branch_seen))
            elif action.get("type") == "if":
                visit_branch(action.get("then", []), set(branch_seen))
                else_actions = action.get("else", []) or []
                visit_branch(else_actions, set(branch_seen))

    visit(plan.get("actions", []) or [])
    return sorted(set(undefined))


def _extract_refs(obj: dict, errors: List[str], known_aliases: set[str], seen_aliases: set[str]) -> None:
    for value in obj.values():
        if isinstance(value, dict) and "__ref__" in value:
            alias = value["__ref__"][0]
            if alias not in known_aliases and alias not in seen_aliases:
                errors.append(alias)


def _as_reference(value: object) -> Optional[List[str]]:
    if isinstance(value, dict) and set(value.keys()) == {"__ref__"}:
        ref = value["__ref__"]
        if isinstance(ref, list) and all(isinstance(part, str) for part in ref):
            return ref
    return None


def _stringify_reference(parts: Sequence[str]) -> str:
    return ".".join(parts)


def _encode_value(value: object) -> str:
    ref = _as_reference(value)
    if ref is not None:
        return "${" + _stringify_reference(ref) + "}"
    if isinstance(value, dict):
        return _format_inline_object(value)
    if isinstance(value, list):
        return _format_inline_list(value)
    if isinstance(value, str):
        return json.dumps(value)
    return json.dumps(value)


def _format_inline_object(value: dict) -> str:
    if not value:
        return "{}"
    parts: List[str] = []
    for key in sorted(value):
        val = value[key]
        key_str = key if isinstance(key, str) and key.isidentifier() else json.dumps(key)
        parts.append(f"{key_str}: {_encode_value(val)}")
    return "{ " + ", ".join(parts) + " }"


def _format_inline_list(values: List[object]) -> str:
    if not values:
        return "[]"
    return "[" + ", ".join(_encode_value(item) for item in values) + "]"


def _ensure_trailing_newline(text: str) -> str:
    return text if text.endswith("\n") else text + "\n"
