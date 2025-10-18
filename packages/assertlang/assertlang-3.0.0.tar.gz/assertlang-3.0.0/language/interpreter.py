from __future__ import annotations

import time
from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Union

from language.parser import _transform_condition  # type: ignore[attr-defined]
from tools import run_tool


class PWExecutionError(RuntimeError):
    """Raised when executing a Promptware plan fails."""

    def __init__(self, message: str, *, code: str = "E_RUNTIME") -> None:
        super().__init__(message)
        self.code = code

    def __str__(self) -> str:  # pragma: no cover - formatting only
        base = super().__str__()
        if base.startswith(f"[{self.code}]"):
            return base
        return f"[{self.code}] {base}"


@dataclass
class CallStep:
    alias: str
    tool_id: str
    result: str
    payload: Dict[str, Any]
    expects: Dict[str, Any]
    retry: Dict[str, Any]


@dataclass
class LetStep:
    target: str
    value: Any


@dataclass
class IfStep:
    condition: str
    then_steps: List["Step"]
    else_steps: List["Step"]


@dataclass
class ParallelBranch:
    name: Optional[str]
    steps: List["Step"]


@dataclass
class ParallelStep:
    branches: List[ParallelBranch]


@dataclass
class FanoutCase:
    label: str
    condition: Optional[str]
    steps: List["Step"]


@dataclass
class FanoutStep:
    source: str
    cases: List[FanoutCase]


@dataclass
class MergeStep:
    target: str
    sources: List["MergeSource"]
    mode: Optional[str] = None
    append_key: Optional[str] = None


@dataclass
class StateStep:
    name: str
    steps: List["Step"]


@dataclass
class MergeSource:
    path: str
    alias: Optional[str]


Step = Union[CallStep, LetStep, IfStep, ParallelStep, FanoutStep, MergeStep, StateStep]


class ExecutionScope:
    def __init__(
        self,
        tools: Dict[str, str],
        responses: Optional[Dict[str, Any]] = None,
        parent: Optional[ExecutionScope] = None,
        runner=run_tool,
    ) -> None:
        self.tools = tools
        self.responses: Dict[str, Any] = responses or {}
        self.parent = parent
        self.runner = runner

    def resolve(self, path: Iterable[str]) -> Any:
        try:
            return _get_from_path(self.responses, path)
        except KeyError:
            if self.parent is not None:
                return self.parent.resolve(path)
            joined = ".".join(path)
            raise PWExecutionError(f"Undefined reference '{joined}'", code="E_PLAN_REF")

    def set_alias(self, target: str, value: Any) -> None:
        segments = target.split(".")
        _set_nested(self.responses, segments, value)

    def snapshot(self) -> Dict[str, Any]:
        if self.parent is None:
            return deepcopy(self.responses)
        merged = self.parent.snapshot()
        merged.update(self.responses)
        return merged


def _build_steps(actions: List[Dict[str, Any]], tools: Dict[str, str]) -> List[Step]:
    steps: List[Step] = []
    for action in actions:
        kind = action.get("type")
        if kind == "call":
            alias = action["alias"]
            tool_id = tools.get(alias)
            if not tool_id:
                raise PWExecutionError(f"call references unknown tool '{alias}'", code="E_PLAN_REF")
            result_alias = action.get("result") or alias
            payload = action.get("payload") or {}
            expects = action.get("expects") or {}
            retry = action.get("retry") or {}
            steps.append(
                CallStep(
                    alias=alias,
                    tool_id=tool_id,
                    result=result_alias,
                    payload=payload,
                    expects=expects,
                    retry=retry,
                )
            )
        elif kind == "let":
            target = action.get("target")
            if not target:
                raise PWExecutionError("let directive missing target", code="E_PLAN")
            steps.append(LetStep(target=target, value=action.get("value")))
        elif kind == "if":
            condition = action.get("condition")
            if condition is None:
                raise PWExecutionError("if directive missing condition", code="E_PLAN")
            then_steps = _build_steps(action.get("then", []), tools)
            else_steps = _build_steps(action.get("else", []) or [], tools)
            steps.append(IfStep(condition=condition, then_steps=then_steps, else_steps=else_steps))
        elif kind == "parallel":
            branches: List[ParallelBranch] = []
            for branch in action.get("branches", []):
                name = branch.get("name")
                branch_steps = _build_steps(branch.get("actions", []), tools)
                branches.append(ParallelBranch(name=name, steps=branch_steps))
            steps.append(ParallelStep(branches=branches))
        elif kind == "fanout":
            source = action.get("source")
            if not isinstance(source, str) or not source:
                raise PWExecutionError("fanout directive missing source alias", code="E_PLAN")
            cases: List[FanoutCase] = []
            for idx, case in enumerate(action.get("cases", [])):
                condition = case.get("when")
                label = case.get("label") or f"case_{idx}"
                case_steps = _build_steps(case.get("actions", []), tools)
                cases.append(FanoutCase(label=label, condition=condition, steps=case_steps))
            steps.append(FanoutStep(source=source, cases=cases))
        elif kind == "merge":
            target = action.get("target")
            sources = action.get("sources") or []
            if not isinstance(target, str) or not target:
                raise PWExecutionError("merge directive missing target alias", code="E_PLAN")
            if not isinstance(sources, list) or not sources:
                raise PWExecutionError("merge directive requires sources", code="E_PLAN")
            merge_sources: List[MergeSource] = []
            for src in sources:
                if isinstance(src, dict):
                    path = str(src.get("path"))
                    alias = src.get("alias")
                else:
                    path = str(src)
                    alias = None
                merge_sources.append(MergeSource(path=path, alias=alias))
            steps.append(
                MergeStep(
                    target=target,
                    sources=merge_sources,
                    mode=action.get("mode"),
                    append_key=action.get("append_key"),
                )
            )
        elif kind == "state":
            name = action.get("name")
            if not isinstance(name, str) or not name:
                raise PWExecutionError("state block missing name", code="E_PLAN")
            state_steps = _build_steps(action.get("actions", []), tools)
            steps.append(StateStep(name=name, steps=state_steps))
        else:
            raise PWExecutionError(f"Unknown action type '{kind}'", code="E_PLAN")
    return steps


class ActionExecutor:
    def __init__(self, tools: Dict[str, str], runner=run_tool) -> None:
        self.tools = tools
        self.runner = runner
        self.events: List[Dict[str, Any]] = []

    def execute(self, actions: List[Dict[str, Any]]) -> Dict[str, Any]:
        self.events = []
        scope = ExecutionScope(self.tools, runner=self.runner)
        steps = _build_steps(actions, self.tools)
        self._run_steps(steps, scope)
        return scope.responses

    def _run_steps(self, steps: List[Step], scope: ExecutionScope) -> None:
        for step in steps:
            if isinstance(step, CallStep):
                self._run_call(step, scope)
            elif isinstance(step, LetStep):
                self._run_let(step, scope)
            elif isinstance(step, IfStep):
                self._run_if(step, scope)
            elif isinstance(step, ParallelStep):
                self._run_parallel(step, scope)
            elif isinstance(step, FanoutStep):
                self._run_fanout(step, scope)
            elif isinstance(step, MergeStep):
                self._run_merge(step, scope)
            elif isinstance(step, StateStep):
                self._run_state(step, scope)
            else:  # pragma: no cover - defensive guard
                raise PWExecutionError(f"Unknown step type '{type(step).__name__}'", code="E_RUNTIME")

    def _record_event(self, **event: Any) -> None:
        self.events.append(event)

    def _run_call(self, step: CallStep, scope: ExecutionScope) -> None:
        alias = step.alias
        tool_id = step.tool_id

        payload = _build_payload(step.payload, scope)

        retry_meta = step.retry or {}
        max_attempts = max(int(retry_meta.get("max", 1)), 1)
        delay = float(retry_meta.get("delay", 0.0))
        expects = step.expects or {}

        last_error: Optional[PWExecutionError] = None
        result_alias = step.result or alias
        started = time.perf_counter()
        for attempt in range(max_attempts):
            try:
                response = scope.runner(tool_id, payload)
            except Exception as exc:  # pragma: no cover - runner failures
                last_error = PWExecutionError(
                    f"call {alias} raised {exc.__class__.__name__}: {exc}",
                    code="E_RUNTIME",
                )
                if delay > 0 and attempt < max_attempts - 1:
                    time.sleep(delay)
                continue

            if response.get("ok"):
                self._validate_expectations(alias, response, expects, scope)
                scope.set_alias(result_alias, response)
                self._record_event(
                    phase="call",
                    action="call",
                    alias=alias,
                    result_alias=result_alias,
                    status="ok",
                    attempt=attempt + 1,
                    duration_ms=_duration_ms(started),
                )
                return
            last_error = PWExecutionError(f"call {alias} failed (attempt {attempt + 1})", code="E_RUNTIME")
            if delay > 0 and attempt < max_attempts - 1:
                time.sleep(delay)

        if last_error:
            self._record_event(
                phase="call",
                action="call",
                alias=alias,
                status="error",
                error=str(last_error),
                code=last_error.code,
                attempt=max_attempts,
                duration_ms=_duration_ms(started),
            )
            raise last_error
        failure = PWExecutionError(f"call {alias} failed", code="E_RUNTIME")
        self._record_event(
            phase="call",
            action="call",
            alias=alias,
            status="error",
            error=str(failure),
            code=failure.code,
            attempt=max_attempts,
            duration_ms=_duration_ms(started),
        )
        raise failure

    def _run_let(self, step: LetStep, scope: ExecutionScope) -> None:
        started = time.perf_counter()
        target = step.target
        if not target:
            raise PWExecutionError("let directive missing target", code="E_PLAN")
        value = _resolve_value(step.value, scope)
        scope.set_alias(target, value)
        self._record_event(
            phase="let",
            action="let",
            target=target,
            status="ok",
            duration_ms=_duration_ms(started),
        )

    def _run_if(self, step: IfStep, scope: ExecutionScope) -> None:
        started = time.perf_counter()
        condition = step.condition
        if condition is None:
            raise PWExecutionError("if directive missing condition", code="E_PLAN")
        if self._evaluate_condition(condition, scope):
            self._run_steps(step.then_steps, scope)
            branch = "then"
        else:
            self._run_steps(step.else_steps, scope)
            branch = "else"
        self._record_event(
            phase="if",
            action="if",
            condition=condition,
            branch=branch,
            status="ok",
            duration_ms=_duration_ms(started),
        )

    def _run_parallel(self, step: ParallelStep, scope: ExecutionScope) -> None:
        started = time.perf_counter()
        branch_labels: List[str] = []
        for index, branch in enumerate(step.branches):
            label = branch.name or f"branch_{index}"
            branch_labels.append(label)
            branch_scope = ExecutionScope(scope.tools, responses={}, parent=scope, runner=scope.runner)
            self._run_steps(branch.steps, branch_scope)
            scope.responses[label] = branch_scope.responses
        self._record_event(
            phase="parallel",
            action="parallel",
            branches=branch_labels,
            status="ok",
            duration_ms=_duration_ms(started),
        )

    def _run_fanout(self, step: FanoutStep, scope: ExecutionScope) -> None:
        started = time.perf_counter()
        executed_keys: List[str] = []
        executed_meta: List[Dict[str, Any]] = []
        for index, case in enumerate(step.cases):
            condition = case.condition
            run_case = True
            if condition:
                try:
                    run_case = bool(self._evaluate_condition(condition, scope))
                except PWExecutionError:
                    run_case = False
            if not run_case:
                continue
            label = case.label or f"case_{index}"
            branch_scope = ExecutionScope(scope.tools, responses={}, parent=scope, runner=scope.runner)
            self._run_steps(case.steps, branch_scope)
            _set_nested(scope.responses, [step.source, label], branch_scope.responses)
            executed_keys.append(label)
            executed_meta.append({"label": label, "condition": condition})
        self._record_event(
            phase="fanout",
            action="fanout",
            source=step.source,
            branches=executed_keys,
            cases=executed_meta,
            status="ok",
            duration_ms=_duration_ms(started),
        )

    def _run_merge(self, step: MergeStep, scope: ExecutionScope) -> None:
        started = time.perf_counter()
        result: Dict[str, Any] = {}
        mode = getattr(step, "mode", None)
        bucket_key = step.append_key or "items"
        for idx, source in enumerate(step.sources):
            path = source.path
            alias = source.alias
            parts = [part for part in path.split(".") if part]
            if not parts:
                raise PWExecutionError(f"merge source '{path}' is invalid", code="E_PLAN")
            try:
                value = _get_from_path(scope.responses, parts)
            except KeyError as exc:
                raise PWExecutionError(f"merge source '{path}' missing", code="E_PLAN_REF") from exc
            cloned = deepcopy(value)
            if mode == "append":
                if not isinstance(cloned, list):
                    raise PWExecutionError(f"merge append expects list from '{path}'", code="E_RUNTIME")
                target_key = alias or bucket_key
                bucket = result.setdefault(target_key, [])
                if not isinstance(bucket, list):
                    raise PWExecutionError(f"merge append target '{target_key}' already used", code="E_PLAN")
                bucket.extend(cloned)
                continue
            if mode == "collect":
                target_key = alias or bucket_key
                bucket = result.setdefault(target_key, [])
                if not isinstance(bucket, list):
                    raise PWExecutionError(f"merge collect target '{target_key}' already used", code="E_PLAN")
                if isinstance(cloned, list):
                    bucket.extend(cloned)
                else:
                    bucket.append(cloned)
                continue
            if mode == "dict":
                if not isinstance(cloned, dict):
                    raise PWExecutionError(f"merge dict expects object from '{path}'", code="E_RUNTIME")
                if alias:
                    label = alias
                    if label in result:
                        raise PWExecutionError(f"merge dict alias '{label}' already used", code="E_PLAN")
                    result[label] = cloned
                else:
                    for key, val in cloned.items():
                        result[key] = deepcopy(val)
                continue
            label = alias or parts[-1] or f"source_{idx}"
            if label in result:
                label = f"{label}_{idx}"
            result[label] = cloned
        scope.set_alias(step.target, result)
        self._record_event(
            phase="merge",
            action="merge",
            target=step.target,
            mode=mode,
            append_key=bucket_key if mode in {"append", "collect"} else None,
            sources=[{"path": src.path, "alias": src.alias} for src in step.sources],
            status="ok",
            duration_ms=_duration_ms(started),
        )

    def _run_state(self, step: StateStep, scope: ExecutionScope) -> None:
        started = time.perf_counter()
        state_scope = ExecutionScope(scope.tools, responses={}, parent=scope, runner=scope.runner)
        self._run_steps(step.steps, state_scope)
        scope.set_alias(step.name, state_scope.responses)
        self._record_event(
            phase="state",
            action="state",
            name=step.name,
            status="ok",
            duration_ms=_duration_ms(started),
        )

    @staticmethod
    def _validate_expectations(alias: str, response: Dict[str, Any], expects: Dict[str, Any], scope: ExecutionScope) -> None:
        for key, expected_spec in expects.items():
            expected = _resolve_value(expected_spec, scope)
            try:
                actual = _get_from_path(response, key.split("."))
            except KeyError:
                raise PWExecutionError(f"call {alias} expectation {key} missing", code="E_RUNTIME")
            if actual != expected:
                raise PWExecutionError(f"call {alias} expectation {key} failed", code="E_RUNTIME")

    def _evaluate_condition(self, condition: str, scope: ExecutionScope) -> bool:
        expr = _transform_condition(condition)
        compiled = compile(expr, "<pw_condition>", "eval")
        env = {"__builtins__": {}, "responses": scope.snapshot()}
        return bool(eval(compiled, env))


def _build_payload(payload: Dict[str, Any], scope: ExecutionScope) -> Dict[str, Any]:
    base: Dict[str, Any] = {}
    for key, value in payload.items():
        path = key.split(".")
        resolved = _resolve_value(value, scope)
        _set_nested(base, path, resolved)
    return base


def _resolve_value(value: Any, scope: ExecutionScope) -> Any:
    if isinstance(value, dict):
        if "__ref__" in value:
            return scope.resolve(value["__ref__"])
        return {key: _resolve_value(val, scope) for key, val in value.items()}
    if isinstance(value, list):
        return [_resolve_value(item, scope) for item in value]
    return value


PathSegment = Union[str, int]


def _expand_path(path: Iterable[str]) -> List[PathSegment]:
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
                raise PWExecutionError(f"Malformed path segment '{segment}'", code="E_PLAN_REF")
            index_token = segment[i + 1 : end].strip()
            if not index_token.isdigit():
                raise PWExecutionError(f"List index must be numeric in '{segment}'", code="E_PLAN_REF")
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


def _get_from_path(mapping: Dict[str, Any], path: Iterable[str]) -> Any:
    cursor: Any = mapping
    for segment in _expand_path(path):
        if isinstance(segment, int):
            if isinstance(cursor, (list, tuple)):
                if segment >= len(cursor):
                    raise KeyError(segment)
                cursor = cursor[segment]
            elif isinstance(cursor, str):
                if segment >= len(cursor):
                    raise KeyError(segment)
                cursor = cursor[segment]
            else:
                raise KeyError(segment)
        else:
            if not isinstance(cursor, dict) or segment not in cursor:
                raise KeyError(segment)
            cursor = cursor[segment]
    return cursor


def _set_nested(target: Dict[str, Any], path: List[str], value: Any) -> None:
    segments = _expand_path(path)
    if not segments:
        raise PWExecutionError("Empty assignment path", code="E_PLAN")
    cursor: Any = target
    for idx, segment in enumerate(segments[:-1]):
        next_segment = segments[idx + 1]
        if isinstance(segment, int):
            if not isinstance(cursor, list):
                raise PWExecutionError("List assignment requires list context", code="E_PLAN")
            while len(cursor) <= segment:
                cursor.append({} if not isinstance(next_segment, int) else [])
            cursor = cursor[segment]
        else:
            if not isinstance(cursor, dict):
                raise PWExecutionError("Dict assignment requires mapping context", code="E_PLAN")
            if segment not in cursor:
                cursor[segment] = [] if isinstance(next_segment, int) else {}
            cursor = cursor[segment]
    last = segments[-1]
    if isinstance(last, int):
        if not isinstance(cursor, list):
            raise PWExecutionError("List assignment requires list context", code="E_PLAN")
        while len(cursor) <= last:
            cursor.append(None)
        cursor[last] = value
    else:
        if not isinstance(cursor, dict):
            raise PWExecutionError("Dict assignment requires mapping context", code="E_PLAN")
        cursor[last] = value


def _duration_ms(started: float) -> float:
    return round((time.perf_counter() - started) * 1000, 3)
