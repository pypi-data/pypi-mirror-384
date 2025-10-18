"""Tool generator CLI scaffolder.

This module defines the skeleton for the Promptware tool generator. It parses a
`toolgen.yaml` specification, validates it against a forthcoming schema, and
prepares to render tool artifacts (schemas, adapters, tests, docs). Actual
rendering logic will be filled in incrementally as templates land.
"""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterable, List

import click
import yaml

try:
    import jsonschema
except ImportError as exc:  # pragma: no cover - fail fast when dependency missing
    raise RuntimeError(
        "jsonschema is required for tool generation; install via `pip install jsonschema`"
    ) from exc


@dataclass(slots=True)
class ToolSpec:
    raw: Dict[str, Any]
    path: Path

    @property
    def tool_id(self) -> str:
        return self.raw.get("tool", {}).get("id", "")


def _load_spec(spec_path: Path) -> ToolSpec:
    data = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):  # defensive guard, full schema validation to follow
        raise ValueError("tool specification must be a mapping")
    return ToolSpec(raw=data, path=spec_path)


@lru_cache(maxsize=1)
def _spec_schema() -> Dict[str, Any]:
    root = Path(__file__).resolve().parents[1]
    schema_path = root / "schemas" / "toolgen.spec.schema.json"
    return json.loads(schema_path.read_text(encoding="utf-8"))


def _validate_spec(spec: ToolSpec) -> None:
    schema = _spec_schema()
    jsonschema.validate(instance=spec.raw, schema=schema)


LANG_ENUM = ["python", "node", "nextjs", "go", "rust", "java", "dotnet", "cpp"]

SHARED_FIELD_SCHEMAS: Dict[str, Dict[str, Any]] = {
    "lang": {"type": "string", "enum": LANG_ENUM},
    "adapter": {"type": "string"},
    "runtime": {"type": "string"},
    "limits": {
        "type": "object",
        "properties": {
            "cpu_pct": {"type": "integer", "minimum": 1, "maximum": 100},
            "mem_mb": {"type": "integer", "minimum": 16},
            "wall_sec": {"type": "integer", "minimum": 1},
        },
        "additionalProperties": False,
    },
    "deps": {"type": "object"},
    "egress": {
        "oneOf": [
            {"type": "string", "enum": ["deny", "allow"]},
            {
                "type": "object",
                "properties": {
                    "allow": {"type": "array", "items": {"type": "string"}, "uniqueItems": True}
                },
                "additionalProperties": False,
            },
        ]
    },
    "env": {"type": "object", "additionalProperties": {"type": "string"}},
    "cwd": {"type": "string"},
}


def _package_name(tool_id: str) -> str:
    pkg = tool_id.replace("-", "_")
    if pkg in {"async", "await", "class", "def"}:
        pkg += "_tool"
    return pkg


ADAPTER_FILENAMES: Dict[str, str] = {
    "python": "adapter_py.py",
    "node": "adapter_node.js",
    "nextjs": "adapter_nextjs.js",
    "go": "adapter_go.go",
    "rust": "adapter_rust.rs",
    "java": "Adapter.java",
    "dotnet": "Adapter.cs",
    "cpp": "adapter_cpp.cpp",
}


def _schema_output(spec: ToolSpec) -> Dict[str, Any]:
    schema_cfg = spec.raw.get("schema", {})
    request = copy.deepcopy(schema_cfg.get("request", {})) or {}
    if not isinstance(request, dict):
        raise ValueError("schema.request must be an object")
    request.setdefault("type", "object")
    request.setdefault("properties", {})
    request_props = request["properties"]
    shared_fields: Iterable[str] = schema_cfg.get("shared_fields", []) or []
    for field in shared_fields:
        if field not in SHARED_FIELD_SCHEMAS:
            raise ValueError(f"unknown shared field: {field}")
        request_props.setdefault(field, SHARED_FIELD_SCHEMAS[field])
    request.setdefault("additionalProperties", False)
    schema_doc = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"https://assertlang.dev/schemas/tools/{spec.tool_id}.v1.json",
        "title": spec.raw.get("tool", {}).get("name", spec.tool_id.capitalize()),
    }
    schema_doc.update(request)
    return schema_doc


def _adapter_content(tool_id: str, language: str, template_name: str) -> str:
    pkg = _package_name(tool_id)
    key = (language, template_name)
    if key == ("python", "stdout_logger"):
        return """from __future__ import annotations

import json
from typing import Any, Dict

from tools.envelope import ok

VERSION = 'v1'


def handle(request: Dict[str, Any]) -> Dict[str, Any]:
    level = request.get('level', 'info').upper()
    message = request.get('message', '')
    context = request.get('context') or {}
    print(f"[{level}] {message} {json.dumps(context)}")
    return ok({'logged': True})
"""
    if key == ("node", "stdout_logger"):
        return """const VERSION = 'v1';

function handle(request) {
  const level = (request.level || 'info').toUpperCase();
  const message = request.message || '';
  const context = request.context || {};
  console.log(`[${level}] ${message} ${JSON.stringify(context)}`);
  return { ok: true, version: VERSION, data: { logged: true } };
}

module.exports = { VERSION, handle };
"""
    if key == ("nextjs", "stdout_logger"):
        return """export const VERSION = 'v1';

export default function handle(request) {
  const level = (request?.level || 'info').toUpperCase();
  const message = request?.message || '';
  const context = request?.context || {};
  console.log(`[${level}] ${message} ${JSON.stringify(context)}`);
  return { ok: true, version: VERSION, data: { logged: true } };
}
"""
    if key == ("go", "stdout_logger"):
        return """package main

import (
    "encoding/json"
    "fmt"
    "strings"
)

const Version = "v1"

func Handle(req map[string]interface{}) map[string]interface{} {
    level := "INFO"
    if v, ok := req["level"].(string); ok {
        level = strings.ToUpper(v)
    }
    message := ""
    if v, ok := req["message"].(string); ok {
        message = v
    }
    ctxBytes, _ := json.Marshal(req["context"])
    fmt.Printf("[%s] %s %s\\n", level, message, string(ctxBytes))
    return map[string]interface{}{
        "ok":      true,
        "version": Version,
        "data": map[string]interface{}{
            "logged": true,
        },
    }
}
"""
    if key == ("rust", "stdout_logger"):
        return """use serde_json::{json, Value};

pub const VERSION: &str = "v1";

pub fn handle(request: &Value) -> Value {
    let level = request.get("level").and_then(Value::as_str).unwrap_or("info").to_uppercase();
    let message = request.get("message").and_then(Value::as_str).unwrap_or("");
    let context = request.get("context").cloned().unwrap_or_else(|| json!({}));
    println!("[{}] {} {}", level, message, context);
    json!({ "ok": true, "version": VERSION, "data": { "logged": true } })
}
"""
    if key == ("java", "stdout_logger"):
        return """import java.util.*;

public class Adapter {
  public static final String VERSION = "v1";

  public static Map<String, Object> handle(Map<String, Object> request) {
    String level = Optional.ofNullable((String) request.get("level")).orElse("info").toUpperCase();
    String message = Optional.ofNullable((String) request.get("message")).orElse("");
    Object context = Optional.ofNullable(request.get("context")).orElse(Collections.emptyMap());
    System.out.println(String.format("[%s] %s %s", level, message, context));
    Map<String, Object> data = new HashMap<>();
    data.put("logged", true);
    Map<String, Object> response = new HashMap<>();
    response.put("ok", true);
    response.put("version", VERSION);
    response.put("data", data);
    return response;
  }
}
"""
    if key == ("dotnet", "stdout_logger"):
        return """using System;
using System.Collections.Generic;

public static class Adapter {
  public const string Version = "v1";

  public static Dictionary<string, object> Handle(Dictionary<string, object> request) {
    request ??= new Dictionary<string, object>();
    var level = request.TryGetValue("level", out var levelObj) ? (levelObj?.ToString() ?? "info") : "info";
    var message = request.TryGetValue("message", out var messageObj) ? (messageObj?.ToString() ?? "") : "";
    var context = request.TryGetValue("context", out var ctx) ? ctx : new Dictionary<string, object>();
    Console.WriteLine($"[{level.ToUpper()}] {message} {context}");
    return new Dictionary<string, object> {
      {"ok", true},
      {"version", Version},
      {"data", new Dictionary<string, object> { {"logged", true} }}
    };
  }
}
"""
    if key == ("cpp", "stdout_logger"):
        return """#include <iostream>
#include <map>
#include <string>

constexpr const char* VERSION = "v1";

std::map<std::string, std::string> handle(const std::map<std::string, std::string>& request) {
    auto levelIt = request.find("level");
    std::string level = levelIt != request.end() ? levelIt->second : "info";
    auto messageIt = request.find("message");
    std::string message = messageIt != request.end() ? messageIt->second : "";
    std::cout << "[" << level << "] " << message << std::endl;
    return {{"ok", "true"}, {"version", VERSION}, {"logged", "true"}};
}
"""
    if key == ("python", "auth_header"):
        return """from __future__ import annotations

from typing import Any, Dict

from tools.envelope import error, ok

VERSION = 'v1'


def handle(request: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(request, dict):
        return error('E_SCHEMA', 'request must be an object')

    auth_type = request.get('type')
    token = request.get('token')
    if not isinstance(auth_type, str) or not isinstance(token, str):
        return error('E_ARGS', 'type and token are required strings')

    header = request.get('header', 'Authorization') or 'Authorization'
    prefix = request.get('prefix', 'Bearer ')

    if auth_type not in {'apiKey', 'jwt'}:
        return error('E_UNSUPPORTED', f'unsupported auth type: {auth_type}')

    value = f"{prefix}{token}" if prefix else token
    return ok({'headers': {header: value}})
"""
    if key in {("node", "auth_header"), ("nextjs", "auth_header")}:
        is_node = language == "node"
        header = "const VERSION = 'v1';\n\n" if is_node else "export const VERSION = 'v1';\n\n"
        fn_def = (
            "function handle(request) {" if is_node else "export default function handle(request) {"
        )
        footer = "}\n\nmodule.exports = { VERSION, handle };\n" if is_node else "}\n"
        body = (
            "  if (typeof request !== 'object' || request === null) {\n"
            "    return error('E_SCHEMA', 'request must be an object');\n"
            "  }\n"
            "  const authType = request.type;\n"
            "  const token = request.token;\n"
            "  if (typeof authType !== 'string' || typeof token !== 'string') {\n"
            "    return error('E_ARGS', 'type and token are required strings');\n"
            "  }\n"
            "  if (authType !== 'apiKey' && authType !== 'jwt') {\n"
            "    return error('E_UNSUPPORTED', `unsupported auth type: ${authType}`);\n"
            "  }\n"
            "  const headerName = typeof request.header === 'string' && request.header.trim() ? request.header : 'Authorization';\n"
            "  const prefix = typeof request.prefix === 'string' ? request.prefix : 'Bearer ';\n"
            "  const value = prefix ? `${prefix}${token}` : token;\n"
            "  return ok({ headers: { [headerName]: value } });\n"
        )
        helpers = (
            "\nfunction ok(data) {\n"
            "  return { ok: true, version: VERSION, data };\n"
            "}\n\n"
            "function error(code, message) {\n"
            "  return { ok: false, version: VERSION, error: { code, message } };\n"
            "}\n\n"
        )
        return header + helpers + fn_def + "\n" + body + footer
    if key == ("go", "auth_header"):
        return """package main

import "strings"

const Version = "v1"

func Handle(req map[string]interface{}) map[string]interface{} {
    if req == nil {
        return errResp("E_SCHEMA", "request must be an object")
    }
    authType, _ := req["type"].(string)
    token, _ := req["token"].(string)
    if authType == "" || token == "" {
        return errResp("E_ARGS", "type and token are required strings")
    }
    if authType != "apiKey" && authType != "jwt" {
        return errResp("E_UNSUPPORTED", "unsupported auth type: "+authType)
    }
    header := "Authorization"
    if h, ok := req["header"].(string); ok && strings.TrimSpace(h) != "" {
        header = h
    }
    prefix := "Bearer "
    if p, ok := req["prefix"].(string); ok {
        prefix = p
    }
    value := token
    if prefix != "" {
        value = prefix + token
    }
    headers := map[string]string{header: value}
    return okResp(map[string]interface{}{"headers": headers})
}

func okResp(data map[string]interface{}) map[string]interface{} {
    return map[string]interface{}{
        "ok":      true,
        "version": Version,
        "data":    data,
    }
}

func errResp(code, message string) map[string]interface{} {
    return map[string]interface{}{
        "ok": false,
        "version": Version,
        "error": map[string]interface{}{
            "code":    code,
            "message": message,
        },
    }
}
"""
    if key == ("go", "output_writer"):
        return """package main

import (
    "fmt"
    "os"
    "path/filepath"
)

const Version = "v1"

func Handle(req map[string]interface{}) map[string]interface{} {
    if req == nil {
        return errResp("E_SCHEMA", "request must be an object")
    }
    target, _ := req["target"].(string)
    if target != "stdout" && target != "file" {
        return errResp("E_ARGS", "target must be stdout or file")
    }
    content := toString(req["content"])
    if target == "stdout" {
        fmt.Println(content)
        return okResp(map[string]interface{}{"written": true})
    }
    pathAny, _ := req["path"].(string)
    if pathAny == "" {
        return errResp("E_ARGS", "path is required for file target")
    }
    absPath, _ := filepath.Abs(pathAny)
    if err := os.MkdirAll(filepath.Dir(absPath), 0o755); err != nil {
        return errErr(err)
    }
    if err := os.WriteFile(absPath, []byte(content), 0o644); err != nil {
        return errErr(err)
    }
    return okResp(map[string]interface{}{"written": true, "path": absPath})
}

func toString(v interface{}) string {
    if s, ok := v.(string); ok {
        return s
    }
    if v == nil {
        return ""
    }
    return fmt.Sprint(v)
}

func okResp(data map[string]interface{}) map[string]interface{} {
    return map[string]interface{}{
        "ok":      true,
        "version": Version,
        "data":    data,
    }
}

func errResp(code, message string) map[string]interface{} {
    return map[string]interface{}{
        "ok": false,
        "version": Version,
        "error": map[string]interface{}{
            "code":    code,
            "message": message,
        },
    }
}

func errErr(err error) map[string]interface{} {
    return errResp("E_RUNTIME", err.Error())
}
"""
    if key == ("go", "loop_counter"):
        return """package main

const Version = "v1"

func Handle(req map[string]interface{}) map[string]interface{} {
    if req == nil {
        return errResp("E_SCHEMA", "request must be an object")
    }
    itemsAny, ok := req["items"].([]interface{})
    if !ok {
        return errResp("E_ARGS", "items must be a list")
    }
    iterations := len(itemsAny)
    return okResp(map[string]interface{}{"iterations": iterations})
}

func okResp(data map[string]interface{}) map[string]interface{} {
    return map[string]interface{}{
        "ok":      true,
        "version": Version,
        "data":    data,
    }
}

func errResp(code, message string) map[string]interface{} {
    return map[string]interface{}{
        "ok": false,
        "version": Version,
        "error": map[string]interface{}{
            "code":    code,
            "message": message,
        },
    }
}
"""
    if key == ("go", "branch_select"):
        return """package main

import "fmt"

const Version = "v1"

func Handle(req map[string]interface{}) map[string]interface{} {
    if req == nil {
        return errResp("E_SCHEMA", "request must be an object")
    }
    casesAny, ok := req["cases"].(map[string]interface{})
    if !ok {
        return errResp("E_ARGS", "cases must be an object")
    }
    value := fmt.Sprint(req["value"])
    if _, exists := casesAny[value]; exists {
        return okResp(map[string]interface{}{"selected": value})
    }
    return okResp(map[string]interface{}{"selected": "default"})
}

func okResp(data map[string]interface{}) map[string]interface{} {
    return map[string]interface{}{
        "ok":      true,
        "version": Version,
        "data":    data,
    }
}

func errResp(code, message string) map[string]interface{} {
    return map[string]interface{}{
        "ok": false,
        "version": Version,
        "error": map[string]interface{}{
            "code":    code,
            "message": message,
        },
    }
}
"""
    if key == ("go", "transform_convert"):
        return """package main

import (
    "encoding/json"
    "gopkg.in/yaml.v3"
)

const Version = "v1"

func Handle(req map[string]interface{}) map[string]interface{} {
    if req == nil {
        return errResp("E_SCHEMA", "request must be an object")
    }
    from, _ := req["from"].(string)
    to, _ := req["to"].(string)
    content, _ := req["content"].(string)
    if (from != "json" && from != "yaml") || (to != "json" && to != "yaml") {
        return errResp("E_ARGS", "from/to must be json or yaml")
    }
    var data interface{}
    if from == "json" {
        if err := json.Unmarshal([]byte(content), &data); err != nil {
            return errResp("E_RUNTIME", err.Error())
        }
    } else {
        if err := yaml.Unmarshal([]byte(content), &data); err != nil {
            return errResp("E_RUNTIME", err.Error())
        }
    }
    if to == "json" {
        bytes, err := json.MarshalIndent(data, "", "  ")
        if err != nil {
            return errResp("E_RUNTIME", err.Error())
        }
        return okResp(map[string]interface{}{"content": string(bytes)})
    }
    bytes, err := yaml.Marshal(data)
    if err != nil {
        return errResp("E_RUNTIME", err.Error())
    }
    return okResp(map[string]interface{}{"content": string(bytes)})
}

func okResp(data map[string]interface{}) map[string]interface{} {
    return map[string]interface{}{
        "ok":      true,
        "version": Version,
        "data":    data,
    }
}

func errResp(code, message string) map[string]interface{} {
    return map[string]interface{}{
        "ok": false,
        "version": Version,
        "error": map[string]interface{}{
            "code":    code,
            "message": message,
        },
    }
}
"""
    if key == ("rust", "auth_header"):
        return """use serde_json::{json, Value};

pub const VERSION: &str = "v1";

pub fn handle(request: &Value) -> Value {
    if !request.is_object() {
        return error("E_SCHEMA", "request must be an object");
    }
    let auth_type = request.get("type").and_then(Value::as_str);
    let token = request.get("token").and_then(Value::as_str);
    if auth_type.is_none() || token.is_none() {
        return error("E_ARGS", "type and token are required strings");
    }
    let auth_type = auth_type.unwrap();
    if auth_type != "apiKey" && auth_type != "jwt" {
        return error("E_UNSUPPORTED", &format!("unsupported auth type: {}", auth_type));
    }
    let header = request
        .get("header")
        .and_then(Value::as_str)
        .filter(|s| !s.trim().is_empty())
        .unwrap_or("Authorization");
    let prefix = request
        .get("prefix")
        .and_then(Value::as_str)
        .unwrap_or("Bearer ");
    let token = token.unwrap();
    let value = if prefix.is_empty() {
        token.to_string()
    } else {
        format!("{}{}", prefix, token)
    };
    ok(json!({ "headers": { header: value } }))
}

fn ok(data: Value) -> Value {
    json!({ "ok": true, "version": VERSION, "data": data })
}

fn error(code: &str, message: &str) -> Value {
    json!({
        "ok": false,
        "version": VERSION,
        "error": { "code": code, "message": message }
    })
}
"""
    if key == ("dotnet", "auth_header"):
        return """using System;
using System.Collections.Generic;

public static class Adapter {
  public const string Version = "v1";

  public static Dictionary<string, object> Handle(Dictionary<string, object> request) {
    if (request == null) {
      return Error("E_SCHEMA", "request must be an object");
    }
    var authType = GetString(request, "type");
    var token = GetString(request, "token");
    if (string.IsNullOrEmpty(authType) || string.IsNullOrEmpty(token)) {
      return Error("E_ARGS", "type and token are required strings");
    }
    if (authType != "apiKey" && authType != "jwt") {
      return Error("E_UNSUPPORTED", $"unsupported auth type: {authType}");
    }
    var header = GetString(request, "header");
    if (string.IsNullOrWhiteSpace(header)) {
      header = "Authorization";
    }
    var prefix = request.TryGetValue("prefix", out var prefixObj) && prefixObj is string s ? s : "Bearer ";
    var value = string.IsNullOrEmpty(prefix) ? token : prefix + token;
    var headers = new Dictionary<string, object> { { header, value } };
    return Ok(new Dictionary<string, object> { { "headers", headers } });
  }

  private static Dictionary<string, object> Ok(Dictionary<string, object> data) => new() {
    { "ok", true },
    { "version", Version },
    { "data", data },
  };

  private static Dictionary<string, object> Error(string code, string message) => new() {
    { "ok", false },
    { "version", Version },
    { "error", new Dictionary<string, object> { { "code", code }, { "message", message } } },
  };

  private static string GetString(Dictionary<string, object> request, string key) {
    return request.TryGetValue(key, out var value) && value is string s ? s : string.Empty;
  }
}
"""
    if key == ("python", "rest_client"):
        return """from __future__ import annotations

import json
from typing import Any, Dict

import requests

from tools.envelope import error, ok

VERSION = 'v1'


def handle(request: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(request, dict):
        return error('E_SCHEMA', 'request must be an object')

    base = request.get('base')
    path = request.get('path')
    if not isinstance(base, str) or not isinstance(path, str):
        return error('E_PLAN', 'base and path are required strings')

    method = request.get('method', 'GET')
    headers = request.get('headers') or {}
    params = request.get('params') or {}
    body = request.get('body')

    url = base.rstrip('/') + (path if path.startswith('/') else '/' + path)

    try:
        resp = requests.request(method, url, headers=headers, params=params, data=body, timeout=15)
    except Exception as exc:
        return error('E_NETWORK', str(exc))

    try:
        payload = resp.json()
    except ValueError:
        payload = None

    return ok({'status': resp.status_code, 'json': payload, 'text': resp.text})
"""
    if key in {("node", "rest_client"), ("nextjs", "rest_client")}:
        is_node = language == "node"
        header = "const VERSION = 'v1';\n\n" if is_node else "export const VERSION = 'v1';\n\n"
        fn_def = (
            "async function handle(request) {"
            if is_node
            else "export default async function handle(request) {"
        )
        footer = "}\n\nmodule.exports = { VERSION, handle };\n" if is_node else "}\n"
        helpers = (
            "function ok(data) {\n"
            "  return { ok: true, version: VERSION, data };\n"
            "}\n\n"
            "function error(code, message) {\n"
            "  return { ok: false, version: VERSION, error: { code, message } };\n"
            "}\n\n"
        )
        body = (
            "  if (typeof request !== 'object' || request === null) {\n"
            "    return error('E_SCHEMA', 'request must be an object');\n"
            "  }\n"
            "  const base = request.base;\n"
            "  const path = request.path;\n"
            "  if (typeof base !== 'string' || typeof path !== 'string') {\n"
            "    return error('E_ARGS', 'base and path are required strings');\n"
            "  }\n"
            "  let url;\n"
            "  try {\n"
            "    url = new URL(path, base);\n"
            "  } catch (err) {\n"
            "    return error('E_ARGS', `invalid URL components: ${String(err)}`);\n"
            "  }\n"
            "  const params = request.params || {};\n"
            "  Object.entries(params).forEach(([key, value]) => {\n"
            "    if (value !== undefined && value !== null) {\n"
            "      url.searchParams.set(key, String(value));\n"
            "    }\n"
            "  });\n"
            "  const method = (request.method || 'GET').toUpperCase();\n"
            "  const headers = request.headers || {};\n"
            "  let bodyValue = request.body;\n"
            "  if (bodyValue !== undefined && bodyValue !== null && typeof bodyValue !== 'string') {\n"
            "    bodyValue = JSON.stringify(bodyValue);\n"
            "    if (!headers['Content-Type']) {\n"
            "      headers['Content-Type'] = 'application/json';\n"
            "    }\n"
            "  }\n"
            "  const controller = new AbortController();\n"
            "  const timeout = (request.timeout_sec ?? 30) * 1000;\n"
            "  const timer = setTimeout(() => controller.abort(), timeout);\n"
            "  try {\n"
            "    const resp = await fetch(url.toString(), { method, headers, body: bodyValue ?? null, signal: controller.signal });\n"
            "    const text = await resp.text();\n"
            "    let jsonPayload = null;\n"
            "    try {\n"
            "      jsonPayload = JSON.parse(text);\n"
            "    } catch (err) {\n"
            "      jsonPayload = null;\n"
            "    }\n"
            "    const headerPairs = {};\n"
            "    resp.headers.forEach((value, key) => { headerPairs[key] = value; });\n"
            "    return ok({ status: resp.status, headers: headerPairs, text, json: jsonPayload });\n"
            "  } catch (err) {\n"
            "    return error('E_NETWORK', String(err));\n"
            "  } finally {\n"
            "    clearTimeout(timer);\n"
            "  }\n"
        )
        return header + helpers + fn_def + "\n" + body + footer
    if key == ("go", "rest_client"):
        return """package main

import (
    "bytes"
    "encoding/json"
    "fmt"
    "io"
    "net/http"
    "net/url"
    "time"
)

const Version = "v1"

func Handle(req map[string]interface{}) map[string]interface{} {
    if req == nil {
        return errResp("E_SCHEMA", "request must be an object")
    }
    base, _ := req["base"].(string)
    path, _ := req["path"].(string)
    if base == "" || path == "" {
        return errResp("E_ARGS", "base and path are required strings")
    }
    baseURL, err := url.Parse(base)
    if err != nil {
        return errResp("E_ARGS", err.Error())
    }
    rel, err := url.Parse(path)
    if err != nil {
        return errResp("E_ARGS", err.Error())
    }
    resolved := baseURL.ResolveReference(rel)
    if params, ok := req["params"].(map[string]interface{}); ok {
        q := resolved.Query()
        for key, value := range params {
            q.Set(key, fmt.Sprint(value))
        }
        resolved.RawQuery = q.Encode()
    }
    method := "GET"
    if m, ok := req["method"].(string); ok && m != "" {
        method = m
    }
    var bodyReader io.Reader
    if body, exists := req["body"]; exists && body != nil {
        switch typed := body.(type) {
        case string:
            bodyReader = bytes.NewBufferString(typed)
        default:
            encoded, err := json.Marshal(typed)
            if err != nil {
                return errResp("E_ARGS", err.Error())
            }
            bodyReader = bytes.NewBuffer(encoded)
        }
    }
    request, err := http.NewRequest(method, resolved.String(), bodyReader)
    if err != nil {
        return errResp("E_RUNTIME", err.Error())
    }
    if headers, ok := req["headers"].(map[string]interface{}); ok {
        for key, value := range headers {
            if str, ok := value.(string); ok {
                request.Header.Set(key, str)
            }
        }
    }
    client := &http.Client{}
    if t, ok := req["timeout_sec"].(float64); ok {
        client.Timeout = time.Duration(t * float64(time.Second))
    }
    resp, err := client.Do(request)
    if err != nil {
        return errResp("E_NETWORK", err.Error())
    }
    defer resp.Body.Close()
    bodyBytes, _ := io.ReadAll(resp.Body)
    headersOut := map[string]string{}
    for key, values := range resp.Header {
        if len(values) > 0 {
            headersOut[key] = values[0]
        }
    }
    var jsonPayload interface{}
    if err := json.Unmarshal(bodyBytes, &jsonPayload); err != nil {
        jsonPayload = nil
    }
    return okResp(map[string]interface{}{
        "status": resp.StatusCode,
        "headers": headersOut,
        "text":   string(bodyBytes),
        "json":   jsonPayload,
    })
}

func okResp(data map[string]interface{}) map[string]interface{} {
    return map[string]interface{}{
        "ok":      true,
        "version": Version,
        "data":    data,
    }
}

func errResp(code, message string) map[string]interface{} {
    return map[string]interface{}{
        "ok": false,
        "version": Version,
        "error": map[string]interface{}{
            "code":    code,
            "message": message,
        },
    }
}
"""
    if key == ("rust", "rest_client"):
        return """use reqwest::blocking::Client;
use reqwest::header::HeaderMap;
use serde_json::{json, Value};
use std::time::Duration;

pub const VERSION: &str = "v1";

pub fn handle(request: &Value) -> Value {
    if !request.is_object() {
        return error("E_SCHEMA", "request must be an object");
    }
    let base = match request.get("base").and_then(Value::as_str) {
        Some(v) => v,
        None => return error("E_ARGS", "base and path are required strings"),
    };
    let path = match request.get("path").and_then(Value::as_str) {
        Some(v) => v,
        None => return error("E_ARGS", "base and path are required strings"),
    };
    let mut url = match reqwest::Url::parse(base) {
        Ok(u) => u,
        Err(err) => return error("E_ARGS", &err.to_string()),
    };
    url = match url.join(path) {
        Ok(u) => u,
        Err(err) => return error("E_ARGS", &err.to_string()),
    };
    if let Some(params) = request.get("params").and_then(Value::as_object) {
        let mut pairs = url.query_pairs_mut();
        for (key, value) in params {
            pairs.append_pair(key, &value_to_string(value));
        }
    }
    let method = request
        .get("method")
        .and_then(Value::as_str)
        .unwrap_or("GET")
        .to_uppercase();
    let method = reqwest::Method::from_bytes(method.as_bytes()).unwrap_or(reqwest::Method::GET);
    let timeout_sec = request
        .get("timeout_sec")
        .and_then(Value::as_f64)
        .unwrap_or(30.0);
    let client = match Client::builder().timeout(Duration::from_secs_f64(timeout_sec)).build() {
        Ok(c) => c,
        Err(err) => return error("E_RUNTIME", &err.to_string()),
    };
    let mut builder = client.request(method, url);
    if let Some(headers) = request.get("headers").and_then(Value::as_object) {
        let mut header_map = HeaderMap::new();
        for (key, value) in headers {
            if let Ok(header_value) = value_to_string(value).parse() {
                if let Ok(name) = key.parse() {
                    header_map.insert(name, header_value);
                }
            }
        }
        builder = builder.headers(header_map);
    }
    if let Some(body_value) = request.get("body") {
        if let Some(s) = body_value.as_str() {
            builder = builder.body(s.to_string());
        } else {
            builder = builder.json(body_value);
        }
    }
    let response = match builder.send() {
        Ok(r) => r,
        Err(err) => return error("E_NETWORK", &err.to_string()),
    };
    let status = response.status().as_u16();
    let mut header_map = serde_json::Map::new();
    for (key, value) in response.headers().iter() {
        header_map.insert(key.to_string(), json!(value.to_str().unwrap_or("")));
    }
    let text = match response.text() {
        Ok(t) => t,
        Err(err) => return error("E_RUNTIME", &err.to_string()),
    };
    let json_payload = serde_json::from_str::<Value>(&text).ok();
    ok(json!({
        "status": status,
        "headers": Value::Object(header_map),
        "text": text,
        "json": json_payload.unwrap_or(Value::Null)
    }))
}

fn value_to_string(value: &Value) -> String {
    match value {
        Value::String(s) => s.clone(),
        Value::Number(n) => n.to_string(),
        Value::Bool(b) => b.to_string(),
        other => other.to_string(),
    }
}

fn ok(data: Value) -> Value {
    json!({ "ok": true, "version": VERSION, "data": data })
}

fn error(code: &str, message: &str) -> Value {
    json!({
        "ok": false,
        "version": VERSION,
        "error": { "code": code, "message": message }
    })
}
"""
    if key == ("dotnet", "rest_client"):
        return """using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Text;

public static class Adapter {
  public const string Version = "v1";

  public static Dictionary<string, object> Handle(Dictionary<string, object> request) {
    if (request == null) {
      return Error("E_SCHEMA", "request must be an object");
    }
    var baseUrl = GetString(request, "base");
    var path = GetString(request, "path");
    if (string.IsNullOrEmpty(baseUrl) || string.IsNullOrEmpty(path)) {
      return Error("E_ARGS", "base and path are required strings");
    }
    Uri baseUri;
    try {
      baseUri = new Uri(baseUrl);
    } catch (Exception ex) {
      return Error("E_ARGS", $"invalid base URL: {ex.Message}");
    }
    if (!Uri.TryCreate(baseUri, path, out var target)) {
      return Error("E_ARGS", "invalid path component");
    }
    if (request.TryGetValue("params", out var paramsObj) && paramsObj is Dictionary<string, object> query) {
      var builder = new UriBuilder(target);
      var segments = query
        .Where(kvp => kvp.Value != null)
        .Select(kvp => $"{Uri.EscapeDataString(kvp.Key)}={Uri.EscapeDataString(kvp.Value.ToString())}")
        .ToArray();
      if (segments.Length > 0) {
        builder.Query = string.Join("&", segments);
        target = builder.Uri;
      }
    }
    var method = GetString(request, "method").ToUpperInvariant();
    if (string.IsNullOrEmpty(method)) {
      method = "GET";
    }
    using var message = new HttpRequestMessage(new HttpMethod(method), target);
    if (request.TryGetValue("headers", out var headersObj) && headersObj is Dictionary<string, object> headers) {
      foreach (var kvp in headers) {
        message.Headers.TryAddWithoutValidation(kvp.Key, kvp.Value?.ToString());
      }
    }
    if (request.TryGetValue("body", out var bodyObj) && bodyObj != null) {
      if (bodyObj is string s) {
        message.Content = new StringContent(s);
      } else {
        var json = System.Text.Json.JsonSerializer.Serialize(bodyObj);
        message.Content = new StringContent(json, Encoding.UTF8, "application/json");
      }
    }
    var timeoutSec = request.TryGetValue("timeout_sec", out var timeoutObj) && timeoutObj is double d ? d : 30.0;
    using var client = new HttpClient { Timeout = TimeSpan.FromSeconds(timeoutSec) };
    try {
      using var response = client.Send(message);
      var text = response.Content.ReadAsStringAsync().GetAwaiter().GetResult();
      Dictionary<string, object> jsonPayload;
      try {
        jsonPayload = System.Text.Json.JsonSerializer.Deserialize<Dictionary<string, object>>(text);
      } catch {
        jsonPayload = null;
      }
      var headersOut = new Dictionary<string, object>();
      foreach (var header in response.Headers) {
        headersOut[header.Key] = string.Join(",", header.Value);
      }
      foreach (var header in response.Content.Headers) {
        headersOut[header.Key] = string.Join(",", header.Value);
      }
      return Ok(new Dictionary<string, object> {
        { "status", (int)response.StatusCode },
        { "headers", headersOut },
        { "text", text },
        { "json", jsonPayload }
      });
    } catch (Exception ex) {
      return Error("E_NETWORK", ex.Message);
    }
  }

  private static Dictionary<string, object> Ok(Dictionary<string, object> data) => new() {
    { "ok", true },
    { "version", Version },
    { "data", data },
  };

  private static Dictionary<string, object> Error(string code, string message) => new() {
    { "ok", false },
    { "version", Version },
    { "error", new Dictionary<string, object> { { "code", code }, { "message", message } } },
  };

  private static string GetString(Dictionary<string, object> request, string key) {
    return request.TryGetValue(key, out var value) && value is string s ? s : string.Empty;
  }
}
"""
    if key == ("python", "json_validator"):
        return """from __future__ import annotations

import json
from typing import Any, Dict

import jsonschema

from tools.envelope import error, ok

VERSION = 'v1'


def handle(request: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(request, dict):
        return error('E_SCHEMA', 'request must be an object')

    fmt = request.get('format')
    schema = request.get('schema')
    content = request.get('content')
    if fmt != 'json':
        return error('E_UNSUPPORTED', f'unsupported format: {fmt}')
    if not isinstance(schema, dict) or not isinstance(content, str):
        return error('E_ARGS', 'schema must be an object and content must be a string')

    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        return ok({'valid': False, 'issues': [f'json decode failed: {exc}']})

    try:
        jsonschema.validate(data, schema)
    except jsonschema.ValidationError as exc:
        return ok({'valid': False, 'issues': [exc.message]})
    except jsonschema.SchemaError as exc:
        return error('E_SCHEMA', f'invalid schema: {exc}')

    return ok({'valid': True, 'issues': []})
"""
    if key == ("node", "json_validator"):
        return """const Ajv = require('ajv');

const VERSION = 'v1';

function ok(data) {
  return { ok: true, version: VERSION, data };
}

function error(code, message) {
  return { ok: false, version: VERSION, error: { code, message } };
}

function handle(request) {
  if (typeof request !== 'object' || request === null) {
    return error('E_SCHEMA', 'request must be an object');
  }
  const fmt = request.format;
  if (fmt !== 'json') {
    return error('E_UNSUPPORTED', `unsupported format: ${fmt}`);
  }
  const schema = request.schema;
  const content = request.content;
  if (typeof schema !== 'object' || schema === null || typeof content !== 'string') {
    return error('E_ARGS', 'schema must be an object and content must be a string');
  }
  let data;
  try {
    data = JSON.parse(content);
  } catch (err) {
    return ok({ valid: false, issues: [`json decode failed: ${err.message}`] });
  }
  const ajv = new Ajv({ allErrors: true, strict: false });
  let validate;
  try {
    validate = ajv.compile(schema);
  } catch (err) {
    return error('E_SCHEMA', `invalid schema: ${err.message}`);
  }
  const valid = validate(data);
  if (!valid) {
    const issues = (validate.errors || []).map(e => (e && e.message) ? e.message : 'validation failed');
    return ok({ valid: false, issues });
  }
  return ok({ valid: true, issues: [] });
}

module.exports = { VERSION, handle };
"""
    if key == ("python", "conditional_eval"):
        return """from __future__ import annotations

import re
from typing import Any, Dict

from tools.envelope import error, ok

VERSION = 'v1'


def handle(request: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(request, dict):
        return error('E_SCHEMA', 'request must be an object')

    left = str(request.get('left', ''))
    op = request.get('op')
    right = str(request.get('right', ''))
    if not isinstance(op, str):
        return error('E_ARGS', 'op is required')

    if op == '==':
        result = left == right
    elif op == '!=':
        result = left != right
    elif op == 'regex':
        try:
            result = re.search(right, left) is not None
        except re.error as exc:
            return error('E_RUNTIME', f'regex error: {exc}')
    else:
        return error('E_ARGS', f'unsupported operator: {op}')

    return ok({'pass': result})
"""
    if key == ("python", "branch_select"):
        return """from __future__ import annotations

from typing import Any, Dict

from tools.envelope import error, ok

VERSION = 'v1'


def handle(request: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(request, dict):
        return error('E_SCHEMA', 'request must be an object')
    cases = request.get('cases')
    if not isinstance(cases, dict):
        return error('E_ARGS', 'cases must be an object')
    value = str(request.get('value', ''))
    selected = value if value in cases else 'default'
    return ok({'selected': selected})
"""
    if key == ("python", "async_simulator"):
        return """from __future__ import annotations

from typing import Any, Dict, List

from tools.envelope import error, ok

VERSION = 'v1'


def handle(request: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(request, dict):
        return error('E_SCHEMA', 'request must be an object')
    tasks = request.get('tasks')
    if not isinstance(tasks, list):
        return error('E_ARGS', 'tasks must be an array')
    results: List[Dict[str, Any]] = []
    for idx, task in enumerate(tasks):
        results.append({'index': idx, 'status': 'done', 'result': task})
    return ok({'results': results})
"""
    if key in {("node", "conditional_eval"), ("nextjs", "conditional_eval")}:
        is_node = language == "node"
        header = "const VERSION = 'v1';\n\n" if is_node else "export const VERSION = 'v1';\n\n"
        fn_def = (
            "function handle(request) {" if is_node else "export default function handle(request) {"
        )
        footer = "}\n\nmodule.exports = { VERSION, handle };\n" if is_node else "}\n"
        helpers = (
            "function ok(data) {\n"
            "  return { ok: true, version: VERSION, data };\n"
            "}\n\n"
            "function error(code, message) {\n"
            "  return { ok: false, version: VERSION, error: { code, message } };\n"
            "}\n\n"
        )
        body = (
            "  if (typeof request !== 'object' || request === null) {\n"
            "    return error('E_SCHEMA', 'request must be an object');\n"
            "  }\n"
            "  const left = String(request.left ?? '');\n"
            "  const op = request.op;\n"
            "  const right = String(request.right ?? '');\n"
            "  if (typeof op !== 'string') {\n"
            "    return error('E_ARGS', 'op is required');\n"
            "  }\n"
            "  if (op === '==') {\n"
            "    return ok({ pass: left === right });\n"
            "  }\n"
            "  if (op === '!=') {\n"
            "    return ok({ pass: left !== right });\n"
            "  }\n"
            "  if (op === 'regex') {\n"
            "    try {\n"
            "      const re = new RegExp(right);\n"
            "      return ok({ pass: re.test(left) });\n"
            "    } catch (err) {\n"
            "      return error('E_RUNTIME', String(err));\n"
            "    }\n"
            "  }\n"
            "  return error('E_ARGS', `unsupported operator: ${op}`);\n"
        )
        return header + helpers + fn_def + "\n" + body + footer
    if key in {("node", "branch_select"), ("nextjs", "branch_select")}:
        is_node = language == "node"
        header = "const VERSION = 'v1';\n\n" if is_node else "export const VERSION = 'v1';\n\n"
        fn_def = (
            "function handle(request) {" if is_node else "export default function handle(request) {"
        )
        footer = "}\n\nmodule.exports = { VERSION, handle };\n" if is_node else "}\n"
        helpers = (
            "function ok(data) {\n"
            "  return { ok: true, version: VERSION, data };\n"
            "}\n\n"
            "function error(code, message) {\n"
            "  return { ok: false, version: VERSION, error: { code, message } };\n"
            "}\n\n"
        )
        body = (
            "  if (typeof request !== 'object' || request === null) {\n"
            "    return error('E_SCHEMA', 'request must be an object');\n"
            "  }\n"
            "  const cases = request.cases;\n"
            "  if (typeof cases !== 'object' || cases === null) {\n"
            "    return error('E_ARGS', 'cases must be an object');\n"
            "  }\n"
            "  const value = String(request.value ?? '');\n"
            "  const selected = Object.prototype.hasOwnProperty.call(cases, value) ? value : 'default';\n"
            "  return ok({ selected });\n"
        )
        return header + helpers + fn_def + "\n" + body + footer
    if key in {("node", "async_simulator"), ("nextjs", "async_simulator")}:
        is_node = language == "node"
        header = "const VERSION = 'v1';\n\n" if is_node else "export const VERSION = 'v1';\n\n"
        fn_def = (
            "async function handle(request) {"
            if is_node
            else "export default async function handle(request) {"
        )
        footer = "}\n\nmodule.exports = { VERSION, handle };\n" if is_node else "}\n"
        helpers = (
            "function ok(data) {\n"
            "  return { ok: true, version: VERSION, data };\n"
            "}\n\n"
            "function error(code, message) {\n"
            "  return { ok: false, version: VERSION, error: { code, message } };\n"
            "}\n\n"
        )
        body = (
            "  if (typeof request !== 'object' || request === null) {\n"
            "    return error('E_SCHEMA', 'request must be an object');\n"
            "  }\n"
            "  const tasks = Array.isArray(request.tasks) ? request.tasks : null;\n"
            "  if (!tasks) {\n"
            "    return error('E_ARGS', 'tasks must be an array');\n"
            "  }\n"
            "  const results = tasks.map((task, index) => ({ index, status: 'done', result: task }));\n"
            "  return ok({ results });\n"
        )
        return header + helpers + fn_def + "\n" + body + footer
    if key == ("go", "conditional_eval"):
        return """package main

import (
    "fmt"
    "regexp"
)

const Version = "v1"

func Handle(req map[string]interface{}) map[string]interface{} {
    if req == nil {
        return errResp("E_SCHEMA", "request must be an object")
    }
    left := toString(req["left"])
    op, _ := req["op"].(string)
    right := toString(req["right"])
    if op == "" {
        return errResp("E_ARGS", "op is required")
    }
    switch op {
    case "==":
        return okResp(map[string]interface{}{"pass": left == right})
    case "!=":
        return okResp(map[string]interface{}{"pass": left != right})
    case "regex":
        re, err := regexp.Compile(right)
        if err != nil {
            return errResp("E_RUNTIME", err.Error())
        }
        return okResp(map[string]interface{}{"pass": re.MatchString(left)})
    default:
        return errResp("E_ARGS", "unsupported operator")
    }
}

func toString(v interface{}) string {
    if s, ok := v.(string); ok {
        return s
    }
    if v == nil {
        return ""
    }
    return fmt.Sprint(v)
}

func okResp(data map[string]interface{}) map[string]interface{} {
    return map[string]interface{}{
        "ok":      true,
        "version": Version,
        "data":    data,
    }
}

func errResp(code, message string) map[string]interface{} {
    return map[string]interface{}{
        "ok": false,
        "version": Version,
        "error": map[string]interface{}{
            "code":    code,
            "message": message,
        },
    }
}
"""
    if key == ("go", "async_simulator"):
        return """package main

const Version = "v1"

func Handle(req map[string]interface{}) map[string]interface{} {
    if req == nil {
        return errResp("E_SCHEMA", "request must be an object")
    }
    tasksAny, ok := req["tasks"].([]interface{})
    if !ok {
        return errResp("E_ARGS", "tasks must be an array")
    }
    results := make([]map[string]interface{}, 0, len(tasksAny))
    for idx, task := range tasksAny {
        results = append(results, map[string]interface{}{
            "index":  idx,
            "status": "done",
            "result": task,
        })
    }
    return okResp(map[string]interface{}{"results": results})
}

func okResp(data map[string]interface{}) map[string]interface{} {
    return map[string]interface{}{
        "ok":      true,
        "version": Version,
        "data":    data,
    }
}

func errResp(code, message string) map[string]interface{} {
    return map[string]interface{}{
        "ok": false,
        "version": Version,
        "error": map[string]interface{}{
            "code":    code,
            "message": message,
        },
    }
}
"""
    if key == ("rust", "conditional_eval"):
        return """use regex::Regex;
use serde_json::{json, Value};

pub const VERSION: &str = "v1";

pub fn handle(request: &Value) -> Value {
    if !request.is_object() {
        return error("E_SCHEMA", "request must be an object");
    }
    let left = request
        .get("left")
        .and_then(Value::as_str)
        .unwrap_or("");
    let op = match request.get("op").and_then(Value::as_str) {
        Some(v) => v,
        None => return error("E_ARGS", "op is required"),
    };
    let right = request
        .get("right")
        .and_then(Value::as_str)
        .unwrap_or("");
    match op {
        "==" => ok(json!({ "pass": left == right })),
        "!=" => ok(json!({ "pass": left != right })),
        "regex" => match Regex::new(right) {
            Ok(re) => ok(json!({ "pass": re.is_match(left) })),
            Err(err) => error("E_RUNTIME", &err.to_string()),
        },
        _ => error("E_ARGS", &format!("unsupported operator: {}", op)),
    }
}

fn ok(data: Value) -> Value {
    json!({ "ok": true, "version": VERSION, "data": data })
}

fn error(code: &str, message: &str) -> Value {
    json!({
        "ok": false,
        "version": VERSION,
        "error": { "code": code, "message": message }
    })
}
"""
    if key == ("rust", "branch_select"):
        return """use serde_json::{json, Value};

pub const VERSION: &str = "v1";

pub fn handle(request: &Value) -> Value {
    if !request.is_object() {
        return error("E_SCHEMA", "request must be an object");
    }
    let cases = match request.get("cases").and_then(Value::as_object) {
        Some(map) => map,
        None => return error("E_ARGS", "cases must be an object"),
    };
    let value = request
        .get("value")
        .map(|v| v.as_str().map(str::to_string).unwrap_or_else(|| v.to_string()))
        .unwrap_or_default();
    let selected = if cases.contains_key(value.as_str()) {
        value
    } else {
        "default".to_string()
    };
    ok(json!({ "selected": selected }))
}

fn ok(data: Value) -> Value {
    json!({ "ok": true, "version": VERSION, "data": data })
}

fn error(code: &str, message: &str) -> Value {
    json!({
        "ok": false,
        "version": VERSION,
        "error": { "code": code, "message": message }
    })
}
"""
    if key == ("rust", "async_simulator"):
        return """use serde_json::{json, Value};

pub const VERSION: &str = "v1";

pub fn handle(request: &Value) -> Value {
    if !request.is_object() {
        return error("E_SCHEMA", "request must be an object");
    }
    let tasks = match request.get("tasks").and_then(Value::as_array) {
        Some(items) => items,
        None => return error("E_ARGS", "tasks must be an array"),
    };
    let results: Vec<Value> = tasks
        .iter()
        .enumerate()
        .map(|(idx, task)| {
            json!({
                "index": idx,
                "status": "done",
                "result": task,
            })
        })
        .collect();
    ok(json!({ "results": results }))
}

fn ok(data: Value) -> Value {
    json!({ "ok": true, "version": VERSION, "data": data })
}

fn error(code: &str, message: &str) -> Value {
    json!({
        "ok": false,
        "version": VERSION,
        "error": { "code": code, "message": message }
    })
}
"""
    if key == ("rust", "loop_counter"):
        return """use serde_json::{json, Value};

pub const VERSION: &str = "v1";

pub fn handle(request: &Value) -> Value {
    if !request.is_object() {
        return error("E_SCHEMA", "request must be an object");
    }
    let items = match request.get("items").and_then(Value::as_array) {
        Some(arr) => arr,
        None => return error("E_ARGS", "items must be a list"),
    };
    ok(json!({ "iterations": items.len() }))
}

fn ok(data: Value) -> Value {
    json!({ "ok": true, "version": VERSION, "data": data })
}

fn error(code: &str, message: &str) -> Value {
    json!({
        "ok": false,
        "version": VERSION,
        "error": { "code": code, "message": message }
    })
}
"""
    if key == ("rust", "output_writer"):
        return """use serde_json::{json, Value};
use std::fs;
use std::path::Path;

pub const VERSION: &str = "v1";

pub fn handle(request: &Value) -> Value {
    if !request.is_object() {
        return error("E_SCHEMA", "request must be an object");
    }
    let target = match request.get("target").and_then(Value::as_str) {
        Some(t) => t,
        None => return error("E_ARGS", "target must be stdout or file"),
    };
    let content = request
        .get("content")
        .map(|v| v.as_str().map(str::to_string).unwrap_or_else(|| v.to_string()))
        .unwrap_or_default();
    if target == "stdout" {
        println!("{}", content);
        return ok(json!({ "written": true }));
    }
    if target != "file" {
        return error("E_ARGS", "target must be stdout or file");
    }
    let path = match request.get("path").and_then(Value::as_str) {
        Some(p) if !p.is_empty() => Path::new(p),
        _ => return error("E_ARGS", "path is required for file target"),
    };
    if let Some(parent) = path.parent() {
        if let Err(err) = fs::create_dir_all(parent) {
            return error("E_RUNTIME", &err.to_string());
        }
    }
    if let Err(err) = fs::write(path, &content) {
        return error("E_RUNTIME", &err.to_string());
    }
    ok(json!({ "written": true, "path": path.to_string_lossy() }))
}

fn ok(data: Value) -> Value {
    json!({ "ok": true, "version": VERSION, "data": data })
}

fn error(code: &str, message: &str) -> Value {
    json!({
        "ok": false,
        "version": VERSION,
        "error": { "code": code, "message": message }
    })
}
"""
    if key == ("dotnet", "conditional_eval"):
        return """using System;
using System.Collections.Generic;
using System.Text.RegularExpressions;

public static class Adapter {
  public const string Version = "v1";

  public static Dictionary<string, object> Handle(Dictionary<string, object> request) {
    if (request == null) {
      return Error("E_SCHEMA", "request must be an object");
    }
    var left = ToString(request, "left");
    var op = request.TryGetValue("op", out var opObj) ? opObj as string : null;
    var right = ToString(request, "right");
    if (string.IsNullOrEmpty(op)) {
      return Error("E_ARGS", "op is required");
    }
    return op switch {
      "==" => Ok(new Dictionary<string, object> { { "pass", left == right } }),
      "!=" => Ok(new Dictionary<string, object> { { "pass", left != right } }),
      "regex" => EvaluateRegex(left, right),
      _ => Error("E_ARGS", $"unsupported operator: {op}"),
    };
  }

  private static Dictionary<string, object> EvaluateRegex(string left, string pattern) {
    try {
      var match = Regex.IsMatch(left, pattern ?? string.Empty);
      return Ok(new Dictionary<string, object> { { "pass", match } });
    } catch (Exception ex) {
      return Error("E_RUNTIME", ex.Message);
    }
  }

  private static string ToString(Dictionary<string, object> request, string key) {
    return request.TryGetValue(key, out var value) ? value?.ToString() ?? string.Empty : string.Empty;
  }

  private static Dictionary<string, object> Ok(Dictionary<string, object> data) => new() {
    { "ok", true },
    { "version", Version },
    { "data", data },
  };

  private static Dictionary<string, object> Error(string code, string message) => new() {
    { "ok", false },
    { "version", Version },
    { "error", new Dictionary<string, object> { { "code", code }, { "message", message } } },
  };
}
"""

    if key == ("rust", "transform_convert"):
        return """use serde_json::{json, Value};
use serde_yaml;

pub const VERSION: &str = "v1";

pub fn handle(request: &Value) -> Value {
    if !request.is_object() {
        return error("E_SCHEMA", "request must be an object");
    }
    let from = match request.get("from").and_then(Value::as_str) {
        Some(v) => v,
        None => return error("E_ARGS", "from must be json or yaml"),
    };
    let to = match request.get("to").and_then(Value::as_str) {
        Some(v) => v,
        None => return error("E_ARGS", "to must be json or yaml"),
    };
    let content = request
        .get("content")
        .and_then(Value::as_str)
        .unwrap_or("");

    let data: Value = match from {
        "json" => match serde_json::from_str(content) {
            Ok(val) => val,
            Err(err) => return error("E_RUNTIME", &err.to_string()),
        },
        "yaml" => match serde_yaml::from_str(content) {
            Ok(val) => val,
            Err(err) => return error("E_RUNTIME", &err.to_string()),
        },
        _ => return error("E_ARGS", "from must be json or yaml"),
    };

    let converted = match to {
        "json" => match serde_json::to_string_pretty(&data) {
            Ok(val) => val,
            Err(err) => return error("E_RUNTIME", &err.to_string()),
        },
        "yaml" => match serde_yaml::to_string(&data) {
            Ok(val) => val,
            Err(err) => return error("E_RUNTIME", &err.to_string()),
        },
        _ => return error("E_ARGS", "to must be json or yaml"),
    };

    ok(json!({ "content": converted }))
}

fn ok(data: Value) -> Value {
    json!({ "ok": true, "version": VERSION, "data": data })
}

fn error(code: &str, message: &str) -> Value {
    json!({
        "ok": false,
        "version": VERSION,
        "error": { "code": code, "message": message }
    })
}
"""
    if key == ("rust", "error_log_collector"):
        return """use serde_json::{json, Value};
use std::fs;
use std::path::Path;

pub const VERSION: &str = "v1";

pub fn handle(request: &Value) -> Value {
    if !request.is_object() {
        return error("E_SCHEMA", "request must be an object");
    }
    let task_id = match request.get("task_id").and_then(Value::as_str) {
        Some(v) if !v.is_empty() => v,
        _ => return error("E_ARGS", "task_id is required"),
    };
    let base = Path::new(".mcpd").join(task_id);
    let run_log = base.join("run.log");
    let mut logs: Vec<String> = Vec::new();
    let mut errors: Vec<String> = Vec::new();
    if let Ok(content) = fs::read_to_string(&run_log) {
        for line in content.lines() {
            logs.push(line.to_string());
            if line.to_lowercase().contains("error") {
                errors.push(line.to_string());
            }
        }
    }
    let summary = if errors.is_empty() {
        "no errors".to_string()
    } else {
        format!("{} errors", errors.len())
    };
    ok(json!({ "errors": errors, "summary": summary, "logs": logs }))
}

fn ok(data: Value) -> Value {
    json!({ "ok": true, "version": VERSION, "data": data })
}

fn error(code: &str, message: &str) -> Value {
    json!({
        "ok": false,
        "version": VERSION,
        "error": { "code": code, "message": message }
    })
}
"""
    if key == ("dotnet", "conditional_eval"):
        return """using System;
using System.Collections.Generic;
using System.Text.RegularExpressions;

public static class Adapter {
  public const string Version = "v1";

  public static Dictionary<string, object> Handle(Dictionary<string, object> request) {
    if (request == null) {
      return Error("E_SCHEMA", "request must be an object");
    }
    var left = ToString(request, "left");
    var op = request.TryGetValue("op", out var opObj) ? opObj as string : null;
    var right = ToString(request, "right");
    if (string.IsNullOrEmpty(op)) {
      return Error("E_ARGS", "op is required");
    }
    return op switch {
      "==" => Ok(new Dictionary<string, object> { { "pass", left == right } }),
      "!=" => Ok(new Dictionary<string, object> { { "pass", left != right } }),
      "regex" => EvaluateRegex(left, right),
      _ => Error("E_ARGS", $"unsupported operator: {op}"),
    };
  }

  private static Dictionary<string, object> EvaluateRegex(string left, string pattern) {
    try {
      var match = Regex.IsMatch(left, pattern ?? string.Empty);
      return Ok(new Dictionary<string, object> { { "pass", match } });
    } catch (Exception ex) {
      return Error("E_RUNTIME", ex.Message);
    }
  }

  private static string ToString(Dictionary<string, object> request, string key) {
    return request.TryGetValue(key, out var value) ? value?.ToString() ?? string.Empty : string.Empty;
  }

  private static Dictionary<string, object> Ok(Dictionary<string, object> data) => new() {
    { "ok", true },
    { "version", Version },
    { "data", data },
  };

  private static Dictionary<string, object> Error(string code, string message) => new() {
    { "ok", false },
    { "version", Version },
    { "error", new Dictionary<string, object> { { "code", code }, { "message", message } } },
  };
}
"""

    if key == ("rust", "transform_convert"):
        return """use serde_json::{json, Value};
use serde_yaml;

pub const VERSION: &str = "v1";

pub fn handle(request: &Value) -> Value {
    if !request.is_object() {
        return error("E_SCHEMA", "request must be an object");
    }
    let from = match request.get("from").and_then(Value::as_str) {
        Some(v) => v,
        None => return error("E_ARGS", "from must be json or yaml"),
    };
    let to = match request.get("to").and_then(Value::as_str) {
        Some(v) => v,
        None => return error("E_ARGS", "to must be json or yaml"),
    };
    let content = request
        .get("content")
        .and_then(Value::as_str)
        .unwrap_or("");

    let data: Value = match from {
        "json" => match serde_json::from_str(content) {
            Ok(val) => val,
            Err(err) => return error("E_RUNTIME", &err.to_string()),
        },
        "yaml" => match serde_yaml::from_str(content) {
            Ok(val) => val,
            Err(err) => return error("E_RUNTIME", &err.to_string()),
        },
        _ => return error("E_ARGS", "from must be json or yaml"),
    };

    let converted = match to {
        "json" => match serde_json::to_string_pretty(&data) {
            Ok(val) => val,
            Err(err) => return error("E_RUNTIME", &err.to_string()),
        },
        "yaml" => match serde_yaml::to_string(&data) {
            Ok(val) => val,
            Err(err) => return error("E_RUNTIME", &err.to_string()),
        },
        _ => return error("E_ARGS", "to must be json or yaml"),
    };

    ok(json!({ "content": converted }))
}

fn ok(data: Value) -> Value {
    json!({ "ok": true, "version": VERSION, "data": data })
}

fn error(code: &str, message: &str) -> Value {
    json!({
        "ok": false,
        "version": VERSION,
        "error": { "code": code, "message": message }
    })
}
"""
    if key == ("rust", "error_log_collector"):
        return """use serde_json::{json, Value};
use std::fs;
use std::path::Path;

pub const VERSION: &str = "v1";

pub fn handle(request: &Value) -> Value {
    if !request.is_object() {
        return error("E_SCHEMA", "request must be an object");
    }
    let task_id = match request.get("task_id").and_then(Value::as_str) {
        Some(v) if !v.is_empty() => v,
        _ => return error("E_ARGS", "task_id is required"),
    };
    let base = Path::new(".mcpd").join(task_id);
    let run_log = base.join("run.log");
    let mut logs: Vec<String> = Vec::new();
    let mut errors: Vec<String> = Vec::new();
    if let Ok(content) = fs::read_to_string(&run_log) {
        for line in content.lines() {
            logs.push(line.to_string());
            if line.to_lowercase().contains("error") {
                errors.push(line.to_string());
            }
        }
    }
    let summary = if errors.is_empty() {
        "no errors".to_string()
    } else {
        format!("{} errors", errors.len())
    };
    ok(json!({ "errors": errors, "summary": summary, "logs": logs }))
}

fn ok(data: Value) -> Value {
    json!({ "ok": true, "version": VERSION, "data": data })
}

fn error(code: &str, message: &str) -> Value {
    json!({
        "ok": false,
        "version": VERSION,
        "error": { "code": code, "message": message }
    })
}
"""
    if key == ("dotnet", "conditional_eval"):
        return """using System;
using System.Collections.Generic;
using System.Text.RegularExpressions;

public static class Adapter {
  public const string Version = "v1";

  public static Dictionary<string, object> Handle(Dictionary<string, object> request) {
    if (request == null) {
      return Error("E_SCHEMA", "request must be an object");
    }
    var left = ToString(request, "left");
    var op = request.TryGetValue("op", out var opObj) ? opObj as string : null;
    var right = ToString(request, "right");
    if (string.IsNullOrEmpty(op)) {
      return Error("E_ARGS", "op is required");
    }
    return op switch {
      "==" => Ok(new Dictionary<string, object> { { "pass", left == right } }),
      "!=" => Ok(new Dictionary<string, object> { { "pass", left != right } }),
      "regex" => EvaluateRegex(left, right),
      _ => Error("E_ARGS", $"unsupported operator: {op}"),
    };
  }

  private static Dictionary<string, object> EvaluateRegex(string left, string pattern) {
    try {
      var match = Regex.IsMatch(left, pattern ?? string.Empty);
      return Ok(new Dictionary<string, object> { { "pass", match } });
    } catch (Exception ex) {
      return Error("E_RUNTIME", ex.Message);
    }
  }

  private static string ToString(Dictionary<string, object> request, string key) {
    return request.TryGetValue(key, out var value) ? value?.ToString() ?? string.Empty : string.Empty;
  }

  private static Dictionary<string, object> Ok(Dictionary<string, object> data) => new() {
    { "ok", true },
    { "version", Version },
    { "data", data },
  };

  private static Dictionary<string, object> Error(string code, string message) => new() {
    { "ok", false },
    { "version", Version },
    { "error", new Dictionary<string, object> { { "code", code }, { "message", message } } },
  };
}
"""

    if key == ("dotnet", "output_writer"):
        return """using System;
using System.Collections.Generic;
using System.IO;

public static class Adapter {
  public const string Version = "v1";

  public static Dictionary<string, object> Handle(Dictionary<string, object> request) {
    if (request == null) {
      return Error("E_SCHEMA", "request must be an object");
    }
    if (!request.TryGetValue("target", out var targetObj) || targetObj is not string target) {
      return Error("E_ARGS", "target must be stdout or file");
    }
    var content = request.TryGetValue("content", out var contentObj) ? contentObj?.ToString() ?? string.Empty : string.Empty;
    if (target == "stdout") {
      Console.WriteLine(content);
      return Ok(new Dictionary<string, object> { { "written", true } });
    }
    if (target != "file") {
      return Error("E_ARGS", "target must be stdout or file");
    }
    if (!request.TryGetValue("path", out var pathObj) || pathObj is not string path || string.IsNullOrEmpty(path)) {
      return Error("E_ARGS", "path is required for file target");
    }
    var directory = Path.GetDirectoryName(path);
    if (!string.IsNullOrEmpty(directory)) {
      Directory.CreateDirectory(directory);
    }
    File.WriteAllText(path, content);
    return Ok(new Dictionary<string, object> { { "written", true }, { "path", path } });
  }

  private static Dictionary<string, object> Ok(Dictionary<string, object> data) => new() {
    { "ok", true },
    { "version", Version },
    { "data", data },
  };

  private static Dictionary<string, object> Error(string code, string message) => new() {
    { "ok", false },
    { "version", Version },
    { "error", new Dictionary<string, object> { { "code", code }, { "message", message } } },
  };
}
"""
    if key == ("dotnet", "async_simulator"):
        return """using System;
using System.Collections.Generic;

public static class Adapter {
  public const string Version = "v1";

  public static Dictionary<string, object> Handle(Dictionary<string, object> request) {
    if (request == null) {
      return Error("E_SCHEMA", "request must be an object");
    }
    if (!request.TryGetValue("tasks", out var tasksObj) || tasksObj is not IEnumerable<object> tasks) {
      return Error("E_ARGS", "tasks must be an array");
    }
    var results = new List<Dictionary<string, object>>();
    var index = 0;
    foreach (var task in tasks) {
      results.Add(new Dictionary<string, object> {
        { "index", index++ },
        { "status", "done" },
        { "result", task }
      });
    }
    return Ok(new Dictionary<string, object> { { "results", results } });
  }

  private static Dictionary<string, object> Ok(Dictionary<string, object> data) => new() {
    { "ok", true },
    { "version", Version },
    { "data", data },
  };

  private static Dictionary<string, object> Error(string code, string message) => new() {
    { "ok", false },
    { "version", Version },
    { "error", new Dictionary<string, object> { { "code", code }, { "message", message } } },
  };
}
"""
    if key == ("dotnet", "transform_convert"):
        return """using System;
using System.Collections.Generic;
using System.Text.Json;
using YamlDotNet.Core;
using YamlDotNet.Serialization;

public static class Adapter {
  public const string Version = "v1";

  public static Dictionary<string, object> Handle(Dictionary<string, object> request) {
    if (request == null) {
      return Error("E_SCHEMA", "request must be an object");
    }
    if (!request.TryGetValue("from", out var fromObj) || fromObj is not string from || (from != "json" && from != "yaml")) {
      return Error("E_ARGS", "from must be json or yaml");
    }
    if (!request.TryGetValue("to", out var toObj) || toObj is not string to || (to != "json" && to != "yaml")) {
      return Error("E_ARGS", "to must be json or yaml");
    }
    var content = request.TryGetValue("content", out var contentObj) ? contentObj?.ToString() ?? string.Empty : string.Empty;

    object data;
    try {
      if (from == "json") {
        data = JsonSerializer.Deserialize<object>(string.IsNullOrEmpty(content) ? "{}" : content)!;
      } else {
        var deserializer = new DeserializerBuilder().Build();
        data = deserializer.Deserialize<object>(content ?? string.Empty) ?? new Dictionary<string, object>();
      }
    } catch (YamlException ex) {
      return Error("E_RUNTIME", ex.Message);
    } catch (JsonException ex) {
      return Error("E_RUNTIME", ex.Message);
    }

    try {
      if (to == "json") {
        var options = new JsonSerializerOptions { WriteIndented = true };
        var json = JsonSerializer.Serialize(data, options);
        return Ok(new Dictionary<string, object> { { "content", json } });
      }
      var serializer = new SerializerBuilder().Build();
      var yaml = serializer.Serialize(data);
      return Ok(new Dictionary<string, object> { { "content", yaml } });
    } catch (Exception ex) {
      return Error("E_RUNTIME", ex.Message);
    }
  }

  private static Dictionary<string, object> Ok(Dictionary<string, object> data) => new() {
    { "ok", true },
    { "version", Version },
    { "data", data },
  };

  private static Dictionary<string, object> Error(string code, string message) => new() {
    { "ok", false },
    { "version", Version },
    { "error", new Dictionary<string, object> { { "code", code }, { "message", message } } },
  };
}
"""
    if key == ("dotnet", "error_log_collector"):
        return """using System;
using System.Collections.Generic;
using System.IO;

public static class Adapter {
  public const string Version = "v1";

  public static Dictionary<string, object> Handle(Dictionary<string, object> request) {
    if (request == null) {
      return Error("E_SCHEMA", "request must be an object");
    }
    if (!request.TryGetValue("task_id", out var taskIdObj) || taskIdObj is not string taskId || string.IsNullOrEmpty(taskId)) {
      return Error("E_ARGS", "task_id is required");
    }
    var basePath = Path.Combine(".mcpd", taskId);
    var runLog = Path.Combine(basePath, "run.log");
    var logs = new List<string>();
    var errors = new List<string>();
    if (File.Exists(runLog)) {
      foreach (var line in File.ReadAllLines(runLog)) {
        logs.Add(line);
        if (line.IndexOf("error", StringComparison.OrdinalIgnoreCase) >= 0) {
          errors.Add(line);
        }
      }
    }
    var summary = errors.Count > 0 ? $"{errors.Count} errors" : "no errors";
    return Ok(new Dictionary<string, object> {
      { "errors", errors },
      { "summary", summary },
      { "logs", logs }
    });
  }

  private static Dictionary<string, object> Ok(Dictionary<string, object> data) => new() {
    { "ok", true },
    { "version", Version },
    { "data", data },
  };

  private static Dictionary<string, object> Error(string code, string message) => new() {
    { "ok", false },
    { "version", Version },
    { "error", new Dictionary<string, object> { { "code", code }, { "message", message } } },
  };
}
"""
    if key == ("dotnet", "loop_counter"):
        return """using System;
using System.Collections.Generic;

public static class Adapter {
  public const string Version = "v1";

  public static Dictionary<string, object> Handle(Dictionary<string, object> request) {
    if (request == null) {
      return Error("E_SCHEMA", "request must be an object");
    }
    if (!request.TryGetValue("items", out var itemsObj) || itemsObj is not IEnumerable<object> items) {
      return Error("E_ARGS", "items must be a list");
    }
    var count = 0;
    foreach (var _ in items) {
      count += 1;
    }
    return Ok(new Dictionary<string, object> { { "iterations", count } });
  }

  private static Dictionary<string, object> Ok(Dictionary<string, object> data) => new() {
    { "ok", true },
    { "version", Version },
    { "data", data },
  };

  private static Dictionary<string, object> Error(string code, string message) => new() {
    { "ok", false },
    { "version", Version },
    { "error", new Dictionary<string, object> { { "code", code }, { "message", message } } },
  };
}
"""
    if key == ("python", "output_writer"):
        return """from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from tools.envelope import error, ok

VERSION = 'v1'


def handle(request: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(request, dict):
        return error('E_SCHEMA', 'request must be an object')
    target = request.get('target')
    if target not in {'stdout', 'file'}:
        return error('E_ARGS', 'target must be stdout or file')
    content = request.get('content', '')
    if target == 'stdout':
        print(str(content))
        return ok({'written': True})
    path = request.get('path')
    if not isinstance(path, str) or not path:
        return error('E_ARGS', 'path is required for file target')
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(str(content), encoding='utf-8')
    return ok({'written': True, 'path': str(file_path)})
"""
    if key == ("dotnet", "branch_select"):
        return """using System;
using System.Collections.Generic;

public static class Adapter {
  public const string Version = "v1";

  public static Dictionary<string, object> Handle(Dictionary<string, object> request) {
    if (request == null) {
      return Error("E_SCHEMA", "request must be an object");
    }
    if (!request.TryGetValue("cases", out var casesObj) || casesObj is not Dictionary<string, object> cases) {
      return Error("E_ARGS", "cases must be an object");
    }
    var value = request.TryGetValue("value", out var valueObj) ? valueObj?.ToString() ?? string.Empty : string.Empty;
    var selected = cases.ContainsKey(value) ? value : "default";
    return Ok(new Dictionary<string, object> { { "selected", selected } });
  }

  private static Dictionary<string, object> Ok(Dictionary<string, object> data) => new() {
    { "ok", true },
    { "version", Version },
    { "data", data },
  };

  private static Dictionary<string, object> Error(string code, string message) => new() {
    { "ok", false },
    { "version", Version },
    { "error", new Dictionary<string, object> { { "code", code }, { "message", message } } },
  };
}
"""
    if key == ("python", "error_toggle"):
        return """from __future__ import annotations

from typing import Any, Dict

from tools.envelope import error, ok

VERSION = 'v1'


def handle(request: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(request, dict):
        return error('E_SCHEMA', 'request must be an object')
    return ok({'thrown': bool(request.get('thrown', False))})
"""

    if key == ("python", "transform_convert"):
        return """from __future__ import annotations

import json
from typing import Any, Dict

import yaml

from tools.envelope import error, ok

VERSION = 'v1'


def handle(request: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(request, dict):
        return error('E_SCHEMA', 'request must be an object')
    source = request.get('from')
    target = request.get('to')
    content = request.get('content', '')
    if source not in {'json', 'yaml'} or target not in {'json', 'yaml'}:
        return error('E_ARGS', "from/to must be 'json' or 'yaml'")
    try:
        if source == 'json':
            data = json.loads(str(content))
        else:
            data = yaml.safe_load(str(content))
    except Exception as exc:  # noqa: BLE001
        return error('E_RUNTIME', str(exc))

    try:
        if target == 'json':
            converted = json.dumps(data, indent=2)
        else:
            converted = yaml.safe_dump(data, sort_keys=False)
    except Exception as exc:  # noqa: BLE001
        return error('E_RUNTIME', str(exc))

    return ok({'content': converted})
"""
    if key == ("python", "error_log_collector"):
        return """from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from tools.envelope import error, ok

VERSION = 'v1'


def handle(request: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(request, dict):
        return error('E_SCHEMA', 'request must be an object')
    task_id = request.get('task_id')
    if not isinstance(task_id, str) or not task_id:
        return error('E_ARGS', 'task_id is required')

    base = Path('.mcpd') / task_id
    run_log = base / 'run.log'
    errors: list[str] = []
    logs: list[str] = []

    if run_log.exists():
        content = run_log.read_text(encoding='utf-8', errors='ignore')
        logs = content.splitlines()
        errors = [line for line in logs if 'error' in line.lower()]

    summary = f"{len(errors)} errors" if errors else 'no errors'
    return ok({'errors': errors, 'summary': summary, 'logs': logs})
"""
    if key == ("node", "error_toggle"):
        return """const VERSION = 'v1';

function ok(data) {
  return { ok: true, version: VERSION, data };
}

function error(code, message) {
  return { ok: false, version: VERSION, error: { code, message } };
}

function handle(request) {
  if (typeof request !== 'object' || request === null) {
    return error('E_SCHEMA', 'request must be an object');
  }
  return ok({ thrown: Boolean(request.thrown) });
}

module.exports = { VERSION, handle };
"""
    if key in {("node", "transform_convert"), ("nextjs", "transform_convert")}:
        is_node = language == "node"
        header = "const VERSION = 'v1';\n\n" if is_node else "export const VERSION = 'v1';\n\n"
        fn_def = (
            "function handle(request) {" if is_node else "export default function handle(request) {"
        )
        footer = "}\n\nmodule.exports = { VERSION, handle };\n" if is_node else "}\n"
        imports = (
            "const yaml = require('js-yaml');\n\n" if is_node else "import yaml from 'js-yaml';\n\n"
        )
        helpers = (
            "function ok(data) {\n"
            "  return { ok: true, version: VERSION, data };\n"
            "}\n\n"
            "function error(code, message) {\n"
            "  return { ok: false, version: VERSION, error: { code, message } };\n"
            "}\n\n"
        )
        body = (
            "  if (typeof request !== 'object' || request === null) {\n"
            "    return error('E_SCHEMA', 'request must be an object');\n"
            "  }\n"
            "  const from = request.from;\n"
            "  const to = request.to;\n"
            "  if ((from !== 'json' && from !== 'yaml') || (to !== 'json' && to !== 'yaml')) {\n"
            "    return error('E_ARGS', 'from/to must be json or yaml');\n"
            "  }\n"
            "  const content = request.content ?? '';\n"
            "  let data;\n"
            "  try {\n"
            "    if (from === 'json') {\n"
            "      data = JSON.parse(String(content || '{}'));\n"
            "    } else {\n"
            "      data = yaml.load(String(content || '')) || {};\n"
            "    }\n"
            "  } catch (err) {\n"
            "    return error('E_RUNTIME', String(err));\n"
            "  }\n"
            "  try {\n"
            "    if (to === 'json') {\n"
            "      const json = JSON.stringify(data, null, 2);\n"
            "      return ok({ content: json });\n"
            "    }\n"
            "    const yamlContent = yaml.dump(data, { sortKeys: false });\n"
            "    return ok({ content: yamlContent });\n"
            "  } catch (err) {\n"
            "    return error('E_RUNTIME', String(err));\n"
            "  }\n"
        )
        return header + fn_def + "\n" + imports + helpers + body + footer
    if key in {("node", "error_log_collector"), ("nextjs", "error_log_collector")}:
        is_node = language == "node"
        header = "const VERSION = 'v1';\n\n" if is_node else "export const VERSION = 'v1';\n\n"
        fn_def = (
            "function handle(request) {" if is_node else "export default function handle(request) {"
        )
        footer = "}\n\nmodule.exports = { VERSION, handle };\n" if is_node else "}\n"
        imports = (
            "const fs = require('fs');\nconst path = require('path');\n\n"
            if is_node
            else "import fs from 'node:fs';\nimport path from 'node:path';\n\n"
        )
        helpers = (
            "function ok(data) {\n"
            "  return { ok: true, version: VERSION, data };\n"
            "}\n\n"
            "function error(code, message) {\n"
            "  return { ok: false, version: VERSION, error: { code, message } };\n"
            "}\n\n"
        )
        body = (
            "  if (typeof request !== 'object' || request === null) {\n"
            "    return error('E_SCHEMA', 'request must be an object');\n"
            "  }\n"
            "  const taskId = request.task_id;\n"
            "  if (typeof taskId !== 'string' || !taskId) {\n"
            "    return error('E_ARGS', 'task_id is required');\n"
            "  }\n"
            "  const base = path.resolve('.mcpd', taskId);\n"
            "  const runLog = path.join(base, 'run.log');\n"
            "  let logs = [];\n"
            "  let errors = [];\n"
            "  if (fs.existsSync(runLog)) {\n"
            "    const content = fs.readFileSync(runLog, 'utf-8');\n"
            "    logs = content.split(/\\n/);\n"
            "    errors = logs.filter((line) => line.toLowerCase().includes('error'));\n"
            "  }\n"
            "  const summary = errors.length ? `${errors.length} errors` : 'no errors';\n"
            "  return ok({ errors, summary, logs });\n"
        )
        return header + fn_def + "\n" + imports + helpers + body + footer
    if key == ("go", "error_toggle"):
        return """package main

const Version = "v1"

func Handle(req map[string]interface{}) map[string]interface{} {
    if req == nil {
        return errResp("E_SCHEMA", "request must be an object")
    }
    thrown := false
    if val, ok := req["thrown"].(bool); ok {
        thrown = val
    }
    return okResp(map[string]interface{}{"thrown": thrown})
}

func okResp(data map[string]interface{}) map[string]interface{} {
    return map[string]interface{}{
        "ok":      true,
        "version": Version,
        "data":    data,
    }
}

func errResp(code, message string) map[string]interface{} {
    return map[string]interface{}{
        "ok": false,
        "version": Version,
        "error": map[string]interface{}{
            "code":    code,
            "message": message,
        },
    }
}
"""
    if key == ("go", "error_log_collector"):
        return """package main

import (
    "fmt"
    "os"
    "path/filepath"
    "strings"
)

const Version = "v1"

func Handle(req map[string]interface{}) map[string]interface{} {
    if req == nil {
        return errResp("E_SCHEMA", "request must be an object")
    }
    taskID, _ := req["task_id"].(string)
    if taskID == "" {
        return errResp("E_ARGS", "task_id is required")
    }
    base := filepath.Join(".mcpd", taskID)
    runLog := filepath.Join(base, "run.log")
    logs := []string{}
    errors := []string{}
    if data, err := os.ReadFile(runLog); err == nil {
        lines := strings.Split(string(data), "\n")
        logs = lines
        for _, line := range lines {
            if strings.Contains(strings.ToLower(line), "error") {
                errors = append(errors, line)
            }
        }
    }
    summary := "no errors"
    if len(errors) > 0 {
        summary = fmt.Sprintf("%d errors", len(errors))
    }
    return okResp(map[string]interface{}{
        "errors":  errors,
        "summary": summary,
        "logs":    logs,
    })
}

func okResp(data map[string]interface{}) map[string]interface{} {
    return map[string]interface{}{
        "ok":      true,
        "version": Version,
        "data":    data,
    }
}

func errResp(code, message string) map[string]interface{} {
    return map[string]interface{}{
        "ok": false,
        "version": Version,
        "error": map[string]interface{}{
            "code":    code,
            "message": message,
        },
    }
}
"""
    if key == ("rust", "error_toggle"):
        return """use serde_json::{json, Value};

pub const VERSION: &str = "v1";

pub fn handle(request: &Value) -> Value {
    if !request.is_object() {
        return error("E_SCHEMA", "request must be an object");
    }
    let thrown = request
        .get("thrown")
        .and_then(Value::as_bool)
        .unwrap_or(false);
    ok(json!({ "thrown": thrown }))
}

fn ok(data: Value) -> Value {
    json!({ "ok": true, "version": VERSION, "data": data })
}

fn error(code: &str, message: &str) -> Value {
    json!({
        "ok": false,
        "version": VERSION,
        "error": { "code": code, "message": message }
    })
}
"""
    if key == ("dotnet", "error_toggle"):
        return """using System;
using System.Collections.Generic;

public static class Adapter {
  public const string Version = "v1";

  public static Dictionary<string, object> Handle(Dictionary<string, object> request) {
    if (request == null) {
      return Error("E_SCHEMA", "request must be an object");
    }
    var thrown = request.TryGetValue("thrown", out var value) && value is bool flag ? flag : false;
    return Ok(new Dictionary<string, object> { { "thrown", thrown } });
  }

  private static Dictionary<string, object> Ok(Dictionary<string, object> data) => new() {
    { "ok", true },
    { "version", Version },
    { "data", data },
  };

  private static Dictionary<string, object> Error(string code, string message) => new() {
    { "ok", false },
    { "version", Version },
    { "error", new Dictionary<string, object> { { "code", code }, { "message", message } } },
  };
}
"""
    if key == ("python", "loop_counter"):
        return """from __future__ import annotations

from typing import Any, Dict

from tools.envelope import error, ok

VERSION = 'v1'


def handle(request: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(request, dict):
        return error('E_SCHEMA', 'request must be an object')
    items = request.get('items')
    if not isinstance(items, list):
        return error('E_ARGS', 'items must be a list')
    return ok({'iterations': len(items)})
"""
    if key == ("python", "transform_convert"):
        return """from __future__ import annotations

import json
from typing import Any, Dict

import yaml

from tools.envelope import error, ok

VERSION = 'v1'


def handle(request: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(request, dict):
        return error('E_SCHEMA', 'request must be an object')
    source = request.get('from')
    target = request.get('to')
    content = request.get('content', '')
    if source not in {'json', 'yaml'} or target not in {'json', 'yaml'}:
        return error('E_ARGS', "from/to must be 'json' or 'yaml'")
    try:
        if source == 'json':
            data = json.loads(str(content))
        else:
            data = yaml.safe_load(str(content))
    except Exception as exc:  # noqa: BLE001
        return error('E_RUNTIME', str(exc))

    try:
        if target == 'json':
            converted = json.dumps(data, indent=2)
        else:
            converted = yaml.safe_dump(data, sort_keys=False)
    except Exception as exc:  # noqa: BLE001
        return error('E_RUNTIME', str(exc))

    return ok({'content': converted})
"""
    if key in {("node", "loop_counter"), ("nextjs", "loop_counter")}:
        is_node = language == "node"
        header = "const VERSION = 'v1';\n\n" if is_node else "export const VERSION = 'v1';\n\n"
        fn_def = (
            "function handle(request) {" if is_node else "export default function handle(request) {"
        )
        footer = "}\n\nmodule.exports = { VERSION, handle };\n" if is_node else "}\n"
        helpers = (
            "function ok(data) {\n"
            "  return { ok: true, version: VERSION, data };\n"
            "}\n\n"
            "function error(code, message) {\n"
            "  return { ok: false, version: VERSION, error: { code, message } };\n"
            "}\n\n"
        )
        body = (
            "  if (typeof request !== 'object' || request === null) {\n"
            "    return error('E_SCHEMA', 'request must be an object');\n"
            "  }\n"
            "  const items = Array.isArray(request.items) ? request.items : null;\n"
            "  if (!items) {\n"
            "    return error('E_ARGS', 'items must be a list');\n"
            "  }\n"
            "  return ok({ iterations: items.length });\n"
        )
        return header + helpers + fn_def + "\n" + body + footer
    if key in {("node", "output_writer"), ("nextjs", "output_writer")}:
        is_node = language == "node"
        header = "const VERSION = 'v1';\n\n" if is_node else "export const VERSION = 'v1';\n\n"
        fn_def = (
            "function handle(request) {" if is_node else "export default function handle(request) {"
        )
        footer = "}\n\nmodule.exports = { VERSION, handle };\n" if is_node else "}\n"
        imports = (
            "const fs = require('fs');\nconst path = require('path');\n\n"
            if is_node
            else "import fs from 'node:fs';\nimport path from 'node:path';\n\n"
        )
        helpers = (
            "function ok(data) {\n"
            "  return { ok: true, version: VERSION, data };\n"
            "}\n\n"
            "function error(code, message) {\n"
            "  return { ok: false, version: VERSION, error: { code, message } };\n"
            "}\n\n"
        )
        body = (
            "  if (typeof request !== 'object' || request === null) {\n"
            "    return error('E_SCHEMA', 'request must be an object');\n"
            "  }\n"
            "  const target = request.target;\n"
            "  if (target !== 'stdout' && target !== 'file') {\n"
            "    return error('E_ARGS', 'target must be stdout or file');\n"
            "  }\n"
            "  const content = request.content ?? '';\n"
            "  if (target === 'stdout') {\n"
            "    console.log(String(content));\n"
            "    return ok({ written: true });\n"
            "  }\n"
            "  const filePath = request.path;\n"
            "  if (typeof filePath !== 'string' || !filePath) {\n"
            "    return error('E_ARGS', 'path is required for file target');\n"
            "  }\n"
            "  const resolved = path.resolve(filePath);\n"
            "  fs.mkdirSync(path.dirname(resolved), { recursive: true });\n"
            "  fs.writeFileSync(resolved, String(content), 'utf-8');\n"
            "  return ok({ written: true, path: resolved });\n"
        )
        return header + fn_def + "\n" + imports + helpers + body + footer
    if key in {("node", "transform_convert"), ("nextjs", "transform_convert")}:
        is_node = language == "node"
        header = "const VERSION = 'v1';\n\n" if is_node else "export const VERSION = 'v1';\n\n"
        fn_def = (
            "function handle(request) {" if is_node else "export default function handle(request) {"
        )
        footer = "}\n\nmodule.exports = { VERSION, handle };\n" if is_node else "}\n"
        imports = (
            "const yaml = require('js-yaml');\n\n" if is_node else "import yaml from 'js-yaml';\n\n"
        )
        helpers = (
            "function ok(data) {\n"
            "  return { ok: true, version: VERSION, data };\n"
            "}\n\n"
            "function error(code, message) {\n"
            "  return { ok: false, version: VERSION, error: { code, message } };\n"
            "}\n\n"
        )
        body = (
            "  if (typeof request !== 'object' || request === null) {\n"
            "    return error('E_SCHEMA', 'request must be an object');\n"
            "  }\n"
            "  const from = request.from;\n"
            "  const to = request.to;\n"
            "  if ((from !== 'json' && from !== 'yaml') || (to !== 'json' && to !== 'yaml')) {\n"
            "    return error('E_ARGS', 'from/to must be json or yaml');\n"
            "  }\n"
            "  const content = request.content ?? '';\n"
            "  let data;\n"
            "  try {\n"
            "    if (from === 'json') {\n"
            "      data = JSON.parse(String(content || '{}'));\n"
            "    } else {\n"
            "      data = yaml.load(String(content || '')) || {};\n"
            "    }\n"
            "  } catch (err) {\n"
            "    return error('E_RUNTIME', String(err));\n"
            "  }\n"
            "  try {\n"
            "    if (to === 'json') {\n"
            "      const json = JSON.stringify(data, null, 2);\n"
            "      return ok({ content: json });\n"
            "    }\n"
            "    const yamlContent = yaml.dump(data, { sortKeys: false });\n"
            "    return ok({ content: yamlContent });\n"
            "  } catch (err) {\n"
            "    return error('E_RUNTIME', String(err));\n"
            "  }\n"
        )
        return header + fn_def + "\n" + imports + helpers + body + footer
    if key == ("python", "branch_select"):
        return """from __future__ import annotations

from typing import Any, Dict

from tools.envelope import error, ok

VERSION = 'v1'


def handle(request: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(request, dict):
        return error('E_SCHEMA', 'request must be an object')
    cases = request.get('cases')
    if not isinstance(cases, dict):
        return error('E_ARGS', 'cases must be an object')
    value = str(request.get('value', ''))
    selected = value if value in cases else 'default'
    return ok({'selected': selected})
"""
    if key == ("python", "timing_sleep"):
        return """from __future__ import annotations

import time
from typing import Any, Dict

from tools.envelope import error, ok

VERSION = 'v1'


def handle(request: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(request, dict):
        return error('E_SCHEMA', 'request must be an object')
    if request.get('op') != 'sleep':
        return error('E_UNSUPPORTED', 'only sleep supported')
    ms = request.get('ms')
    if not isinstance(ms, int) or ms < 0:
        return error('E_ARGS', 'ms must be a non-negative integer')
    start = time.time()
    time.sleep(ms / 1000)
    elapsed = int((time.time() - start) * 1000)
    return ok({'elapsed_ms': elapsed})
"""
    if key == ("python", "input_file"):
        return """from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from tools.envelope import error, ok

VERSION = 'v1'


def handle(request: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(request, dict):
        return error('E_SCHEMA', 'request must be an object')
    if request.get('source') != 'file':
        return error('E_UNSUPPORTED', 'only file source supported')
    path = request.get('path')
    if not isinstance(path, str):
        return error('E_ARGS', 'path must be a string')
    encoding = request.get('encoding', 'utf-8')
    try:
        content = Path(path).read_text(encoding=encoding)
    except FileNotFoundError:
        return error('E_RUNTIME', 'file not found')
    return ok({'content': content})
"""
    if key == ("python", "hash_utility"):
        return """from __future__ import annotations

import hashlib
from typing import Any, Dict

from tools.envelope import error, ok

VERSION = 'v1'


def handle(request: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(request, dict):
        return error('E_SCHEMA', 'request must be an object')
    if request.get('op') != 'hash' or request.get('alg') != 'sha256':
        return error('E_UNSUPPORTED', 'only sha256 hash supported')
    data = request.get('data')
    if not isinstance(data, str):
        return error('E_ARGS', 'data must be a string')
    digest = hashlib.sha256(data.encode('utf-8')).hexdigest()
    return ok({'result': digest})

def handle(request: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(request, dict):
        return error('E_SCHEMA', 'request must be an object')

    fmt = request.get('format')
    schema = request.get('schema')
    content = request.get('content')
    if fmt != 'json':
        return error('E_UNSUPPORTED', f'unsupported format: {fmt}')
    if not isinstance(schema, dict) or not isinstance(content, str):
        return error('E_ARGS', 'schema must be an object and content must be a string')

    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        return ok({'valid': False, 'issues': [f'json decode failed: {exc}']})

    try:
        jsonschema.validate(data, schema)
    except jsonschema.ValidationError as exc:
        return ok({'valid': False, 'issues': [exc.message]})
    except jsonschema.SchemaError as exc:
        return error('E_SCHEMA', f'invalid schema: {exc}')

    return ok({'valid': True, 'issues': []})
"""
    if key == ("python", "http_client"):
        return (
            "from __future__ import annotations\n\n"
            "import json\n"
            "from typing import Any, Dict\n\n"
            "import requests\n\n"
            "from tools.envelope import error, ok\n\n"
            "VERSION = 'v1'\n\n"
            "\n"
            "def handle(request: Dict[str, Any]) -> Dict[str, Any]:\n"
            "    if not isinstance(request, dict):\n"
            "        return error('E_SCHEMA', 'request must be a JSON object')\n"
            "    method = request.get('method', 'GET')\n"
            "    url = request.get('url')\n"
            "    if not url:\n"
            "        return error('E_ARGS', 'url is required')\n"
            "    headers = request.get('headers') or {}\n"
            "    body = request.get('body')\n"
            "    timeout = float(request.get('timeout_sec', 30))\n"
            "    try:\n"
            "        resp = requests.request(method, url, headers=headers, data=body, timeout=timeout)\n"
            "    except Exception as exc:\n"
            "        return error('E_NETWORK', str(exc))\n"
            "    return ok({'status': resp.status_code, 'headers': dict(resp.headers), 'body': resp.text})\n"
        )
    if key in {("node", "http_client"), ("nextjs", "http_client")}:
        is_node = language == "node"
        header = "const VERSION = 'v1';\n\n" if is_node else "export const VERSION = 'v1';\n\n"
        fn_def = (
            "async function handle(request) {"
            if is_node
            else "export default async function handle(request) {"
        )
        footer = "}\n\nmodule.exports = { VERSION, handle };\n" if is_node else "}\n"
        body = (
            "  if (typeof request !== 'object' || request === null) {\n"
            "    return { ok: false, version: VERSION, error: { code: 'E_SCHEMA', message: 'request must be an object' } };\n"
            "  }\n"
            "  const method = (request.method || 'GET').toUpperCase();\n"
            "  const url = request.url;\n"
            "  if (!url) {\n"
            "    return { ok: false, version: VERSION, error: { code: 'E_ARGS', message: 'url is required' } };\n"
            "  }\n"
            "  const headers = request.headers || {};\n"
            "  const body = request.body ?? null;\n"
            "  const controller = new AbortController();\n"
            "  const timeout = (request.timeout_sec ?? 30) * 1000;\n"
            "  const timer = setTimeout(() => controller.abort(), timeout);\n"
            "  try {\n"
            "    const resp = await fetch(url, { method, headers, body, signal: controller.signal });\n"
            "    const text = await resp.text();\n"
            "    const headerPairs = {};\n"
            "    resp.headers.forEach((value, key) => { headerPairs[key] = value; });\n"
            "    return { ok: true, version: VERSION, data: { status: resp.status, headers: headerPairs, body: text } };\n"
            "  } catch (err) {\n"
            "    return { ok: false, version: VERSION, error: { code: 'E_NETWORK', message: String(err) } };\n"
            "  } finally {\n"
            "    clearTimeout(timer);\n"
            "  }\n"
        )
        return header + fn_def + "\n" + body + footer
    if key == ("go", "http_client"):
        return """package main

import (
    "bytes"
    "io"
    "net/http"
    "time"
)

const Version = "v1"

func Handle(req map[string]interface{}) map[string]interface{} {
    urlAny, ok := req["url"]
    if !ok {
        return map[string]interface{}{
            "ok": false,
            "version": Version,
            "error": map[string]interface{}{
                "code":    "E_ARGS",
                "message": "url is required",
            },
        }
    }
    url, _ := urlAny.(string)
    if url == "" {
        return map[string]interface{}{
            "ok": false,
            "version": Version,
            "error": map[string]interface{}{
                "code":    "E_ARGS",
                "message": "url is required",
            },
        }
    }
    method := "GET"
    if m, ok := req["method"].(string); ok {
        method = m
    }
    var bodyReader io.Reader
    if body, ok := req["body"].(string); ok {
        bodyReader = bytes.NewBufferString(body)
    }
    request, err := http.NewRequest(method, url, bodyReader)
    if err != nil {
        return map[string]interface{}{
            "ok": false,
            "version": Version,
            "error": map[string]interface{}{
                "code":    "E_RUNTIME",
                "message": err.Error(),
            },
        }
    }
    if headers, ok := req["headers"].(map[string]interface{}); ok {
        for k, v := range headers {
            if s, ok := v.(string); ok {
                request.Header.Set(k, s)
            }
        }
    }
    client := &http.Client{}
    if t, ok := req["timeout_sec"].(float64); ok {
        client.Timeout = time.Duration(t * float64(time.Second))
    }
    resp, err := client.Do(request)
    if err != nil {
        return map[string]interface{}{
            "ok": false,
            "version": Version,
            "error": map[string]interface{}{
                "code":    "E_NETWORK",
                "message": err.Error(),
            },
        }
    }
    defer resp.Body.Close()
    bodyBytes, _ := io.ReadAll(resp.Body)
    headerMap := map[string]string{}
    for k, v := range resp.Header {
        if len(v) > 0 {
            headerMap[k] = v[0]
        }
    }
    return map[string]interface{}{
        "ok":      true,
        "version": Version,
        "data": map[string]interface{}{
            "status":  resp.StatusCode,
            "headers": headerMap,
            "body":    string(bodyBytes),
        },
    }
}
"""
    if key == ("rust", "http_client"):
        return """use reqwest::blocking::Client;
use reqwest::header::HeaderMap;
use serde_json::{json, Value};
use std::time::Duration;

pub const VERSION: &str = "v1";

pub fn handle(request: &Value) -> Value {
    if !request.is_object() {
        return error("E_SCHEMA", "request must be an object");
    }
    let url = match request.get("url").and_then(Value::as_str) {
        Some(v) => v,
        None => return error("E_ARGS", "url is required"),
    };
    let method = request
        .get("method")
        .and_then(Value::as_str)
        .unwrap_or("GET")
        .to_uppercase();
    let method = reqwest::Method::from_bytes(method.as_bytes()).unwrap_or(reqwest::Method::GET);
    let timeout = request
        .get("timeout_sec")
        .and_then(Value::as_f64)
        .unwrap_or(30.0);
    let client = match Client::builder().timeout(Duration::from_secs_f64(timeout)).build() {
        Ok(c) => c,
        Err(err) => return error("E_RUNTIME", &err.to_string()),
    };
    let mut builder = client.request(method, url);
    if let Some(headers) = request.get("headers").and_then(Value::as_object) {
        let mut header_map = HeaderMap::new();
        for (key, value) in headers {
            if let Ok(header_value) = value_to_string(value).parse() {
                if let Ok(name) = key.parse() {
                    header_map.insert(name, header_value);
                }
            }
        }
        builder = builder.headers(header_map);
    }
    if let Some(body_value) = request.get("body") {
        if let Some(s) = body_value.as_str() {
            builder = builder.body(s.to_string());
        } else {
            builder = builder.body(body_value.to_string());
        }
    }
    let response = match builder.send() {
        Ok(r) => r,
        Err(err) => return error("E_NETWORK", &err.to_string()),
    };
    let status = response.status().as_u16();
    let mut header_map = serde_json::Map::new();
    for (key, value) in response.headers().iter() {
        header_map.insert(key.to_string(), json!(value.to_str().unwrap_or("")));
    }
    let body = match response.text() {
        Ok(b) => b,
        Err(err) => return error("E_RUNTIME", &err.to_string()),
    };
    ok(json!({
        "status": status,
        "headers": Value::Object(header_map),
        "body": body
    }))
}

fn value_to_string(value: &Value) -> String {
    match value {
        Value::String(s) => s.clone(),
        Value::Number(n) => n.to_string(),
        Value::Bool(b) => b.to_string(),
        other => other.to_string(),
    }
}

fn ok(data: Value) -> Value {
    json!({ "ok": true, "version": VERSION, "data": data })
}

fn error(code: &str, message: &str) -> Value {
    json!({
        "ok": false,
        "version": VERSION,
        "error": { "code": code, "message": message }
    })
}
"""
    if key == ("dotnet", "http_client"):
        return """using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Text;

public static class Adapter {
  public const string Version = "v1";

  public static Dictionary<string, object> Handle(Dictionary<string, object> request) {
    if (request == null) {
      return Error("E_SCHEMA", "request must be an object");
    }
    var url = GetString(request, "url");
    if (string.IsNullOrEmpty(url)) {
      return Error("E_ARGS", "url is required");
    }
    var method = GetString(request, "method").ToUpperInvariant();
    if (string.IsNullOrEmpty(method)) {
      method = "GET";
    }
    using var message = new HttpRequestMessage(new HttpMethod(method), url);
    if (request.TryGetValue("headers", out var headersObj) && headersObj is Dictionary<string, object> headers) {
      foreach (var kvp in headers) {
        message.Headers.TryAddWithoutValidation(kvp.Key, kvp.Value?.ToString());
      }
    }
    if (request.TryGetValue("body", out var bodyObj) && bodyObj != null) {
      if (bodyObj is string s) {
        message.Content = new StringContent(s);
      } else {
        var json = System.Text.Json.JsonSerializer.Serialize(bodyObj);
        message.Content = new StringContent(json, Encoding.UTF8, "application/json");
      }
    }
    var timeoutSec = request.TryGetValue("timeout_sec", out var timeoutObj) && timeoutObj is double d ? d : 30.0;
    using var client = new HttpClient { Timeout = TimeSpan.FromSeconds(timeoutSec) };
    try {
      using var response = client.Send(message);
      var body = response.Content.ReadAsStringAsync().GetAwaiter().GetResult();
      var headersOut = new Dictionary<string, object>();
      foreach (var header in response.Headers) {
        headersOut[header.Key] = string.Join(",", header.Value);
      }
      foreach (var header in response.Content.Headers) {
        headersOut[header.Key] = string.Join(",", header.Value);
      }
      return Ok(new Dictionary<string, object> {
        { "status", (int)response.StatusCode },
        { "headers", headersOut },
        { "body", body }
      });
    } catch (Exception ex) {
      return Error("E_NETWORK", ex.Message);
    }
  }

  private static Dictionary<string, object> Ok(Dictionary<string, object> data) => new() {
    { "ok", true },
    { "version", Version },
    { "data", data },
  };

  private static Dictionary<string, object> Error(string code, string message) => new() {
    { "ok", false },
    { "version", Version },
    { "error", new Dictionary<string, object> { { "code", code }, { "message", message } } },
  };

  private static string GetString(Dictionary<string, object> request, string key) {
    return request.TryGetValue(key, out var value) && value is string s ? s : string.Empty;
  }
}
"""
    if key == ("python", "storage_fs"):
        return (
            "from __future__ import annotations\n\n"
            "from pathlib import Path\n"
            "from typing import Any, Dict\n\n"
            "from tools.envelope import error, ok\n\n"
            "VERSION = 'v1'\n\n"
            "\n"
            "def handle(request: Dict[str, Any]) -> Dict[str, Any]:\n"
            "    if not isinstance(request, dict):\n"
            "        return error('E_SCHEMA', 'request must be an object')\n"
            "    backend = request.get('backend', 'fs')\n"
            "    if backend != 'fs':\n"
            "        return error('E_UNSUPPORTED', f'unsupported backend: {backend}')\n"
            "    op = request.get('op')\n"
            "    params = request.get('params') or {}\n"
            "    path_value = params.get('path')\n"
            "    if not path_value:\n"
            "        return error('E_ARGS', 'path is required')\n"
            "    path = Path(path_value)\n"
            "    if op == 'put':\n"
            "        content = params.get('content', '')\n"
            "        path.parent.mkdir(parents=True, exist_ok=True)\n"
            "        path.write_text(str(content), encoding='utf-8')\n"
            "        return ok({'written': True})\n"
            "    if op == 'get':\n"
            "        try:\n"
            "            content = path.read_text(encoding='utf-8')\n"
            "        except FileNotFoundError:\n"
            "            return error('E_RUNTIME', 'file not found')\n"
            "        return ok({'content': content})\n"
            "    if op == 'list':\n"
            "        glob = params.get('glob', '*')\n"
            "        items = [str(p) for p in path.glob(glob)]\n"
            "        return ok({'items': items})\n"
            "    if op == 'delete':\n"
            "        path.unlink(missing_ok=True)\n"
            "        return ok({'deleted': True})\n"
            "    return error('E_ARGS', f'unsupported op: {op}')\n"
        )
    if key == ("node", "storage_fs"):
        return """const VERSION = 'v1';
const fs = require('fs');
const path = require('path');

function handle(request) {
  if (typeof request !== 'object' || request === null) {
    return { ok: false, version: VERSION, error: { code: 'E_SCHEMA', message: 'request must be an object' } };
  }
  const backend = request.backend || 'fs';
  if (backend !== 'fs') {
    return { ok: false, version: VERSION, error: { code: 'E_UNSUPPORTED', message: `unsupported backend: ${backend}` } };
  }
  const op = request.op;
  const params = request.params || {};
  const p = params.path;
  if (!p) {
    return { ok: false, version: VERSION, error: { code: 'E_ARGS', message: 'path is required' } };
  }
  const target = path.resolve(p);
  try {
    if (op === 'put') {
      fs.mkdirSync(path.dirname(target), { recursive: true });
      fs.writeFileSync(target, String(params.content ?? ''), 'utf-8');
      return { ok: true, version: VERSION, data: { written: true } };
    }
    if (op === 'get') {
      const content = fs.readFileSync(target, 'utf-8');
      return { ok: true, version: VERSION, data: { content } };
    }
    if (op === 'list') {
      const glob = params.glob || '';
      const dir = fs.existsSync(target) ? fs.readdirSync(target) : [];
      return { ok: true, version: VERSION, data: { items: dir.map((file) => path.join(target, file)) } };
    }
    if (op === 'delete') {
      if (fs.existsSync(target)) fs.rmSync(target);
      return { ok: true, version: VERSION, data: { deleted: true } };
    }
  } catch (err) {
    return { ok: false, version: VERSION, error: { code: 'E_RUNTIME', message: String(err) } };
  }
  return { ok: false, version: VERSION, error: { code: 'E_ARGS', message: `unsupported op: ${op}` } };
}

module.exports = { VERSION, handle };
"""
    if key == ("go", "storage_fs"):
        return """package main

import (
    "io/fs"
    "os"
    "path/filepath"
)

const Version = "v1"

func Handle(req map[string]interface{}) map[string]interface{} {
    backend := "fs"
    if b, ok := req["backend"].(string); ok {
        backend = b
    }
    if backend != "fs" {
        return map[string]interface{}{
            "ok": false,
            "version": Version,
            "error": map[string]interface{}{
                "code":    "E_UNSUPPORTED",
                "message": "unsupported backend",
            },
        }
    }
    op, _ := req["op"].(string)
    params, _ := req["params"].(map[string]interface{})
    pathAny := params["path"]
    path, _ := pathAny.(string)
    if path == "" {
        return map[string]interface{}{
            "ok": false,
            "version": Version,
            "error": map[string]interface{}{
                "code":    "E_ARGS",
                "message": "path is required",
            },
        }
    }
    absPath, _ := filepath.Abs(path)
    switch op {
    case "put":
        content, _ := params["content"].(string)
        if err := os.MkdirAll(filepath.Dir(absPath), 0o755); err != nil {
            return errResp(err)
        }
        if err := os.WriteFile(absPath, []byte(content), 0o644); err != nil {
            return errResp(err)
        }
        return okResp(map[string]interface{}{"written": true})
    case "get":
        bytes, err := os.ReadFile(absPath)
        if err != nil {
            return errResp(err)
        }
        return okResp(map[string]interface{}{"content": string(bytes)})
    case "list":
        entries, err := os.ReadDir(absPath)
        if err != nil {
            if os.IsNotExist(err) {
                return okResp(map[string]interface{}{"items": []string{}})
            }
            return errResp(err)
        }
        items := make([]string, 0, len(entries))
        for _, entry := range entries {
            items = append(items, filepath.Join(absPath, entry.Name()))
        }
        return okResp(map[string]interface{}{"items": items})
    case "delete":
        if err := os.Remove(absPath); err != nil && !os.IsNotExist(err) {
            return errResp(err)
        }
        return okResp(map[string]interface{}{"deleted": true})
    default:
        return map[string]interface{}{
            "ok": false,
            "version": Version,
            "error": map[string]interface{}{
                "code":    "E_ARGS",
                "message": "unsupported op",
            },
        }
    }
}

func okResp(data map[string]interface{}) map[string]interface{} {
    return map[string]interface{}{
        "ok":      true,
        "version": Version,
        "data":    data,
    }
}

func errResp(err error) map[string]interface{} {
    return map[string]interface{}{
        "ok": false,
        "version": Version,
        "error": map[string]interface{}{
            "code":    "E_RUNTIME",
            "message": err.Error(),
        },
    }
}
"""
    if key == ("rust", "storage_fs"):
        return """use serde_json::{json, Map, Value};
use std::fs;
use std::path::Path;

pub const VERSION: &str = "v1";

pub fn handle(request: &Value) -> Value {
    if !request.is_object() {
        return error("E_SCHEMA", "request must be an object");
    }
    let backend = request
        .get("backend")
        .and_then(Value::as_str)
        .unwrap_or("fs");
    if backend != "fs" {
        return error("E_UNSUPPORTED", &format!("unsupported backend: {}", backend));
    }
    let op = request
        .get("op")
        .and_then(Value::as_str)
        .unwrap_or("");
    let params = request
        .get("params")
        .and_then(Value::as_object)
        .cloned()
        .unwrap_or_else(Map::new);
    let path = match params.get("path").and_then(Value::as_str) {
        Some(p) if !p.is_empty() => Path::new(p),
        _ => return error("E_ARGS", "path is required"),
    };

    match op {
        "put" => {
            let content = params
                .get("content")
                .map(|v| v.as_str().map(|s| s.to_owned()).unwrap_or_else(|| v.to_string()))
                .unwrap_or_default();
            if let Some(parent) = path.parent() {
                if let Err(err) = fs::create_dir_all(parent) {
                    return error("E_RUNTIME", &err.to_string());
                }
            }
            if let Err(err) = fs::write(path, content) {
                return error("E_RUNTIME", &err.to_string());
            }
            ok(json!({ "written": true }))
        }
        "get" => match fs::read_to_string(path) {
            Ok(content) => ok(json!({ "content": content })),
            Err(err) => error("E_RUNTIME", &err.to_string()),
        },
        "list" => {
            let glob = params
                .get("glob")
                .and_then(Value::as_str)
                .unwrap_or("*");
            if glob != "*" {
                return error("E_UNSUPPORTED", "glob patterns other than '*' are not supported");
            }
            let mut items = Vec::new();
            if path.is_dir() {
                match fs::read_dir(path) {
                    Ok(entries) => {
                        for entry in entries.flatten() {
                            items.push(entry.path().to_string_lossy().to_string());
                        }
                    }
                    Err(err) => return error("E_RUNTIME", &err.to_string()),
                }
            } else if path.exists() {
                items.push(path.to_string_lossy().to_string());
            }
            ok(json!({ "items": items }))
        }
        "delete" => {
            if path.is_dir() {
                if let Err(err) = fs::remove_dir_all(path) {
                    return error("E_RUNTIME", &err.to_string());
                }
            } else if path.exists() {
                if let Err(err) = fs::remove_file(path) {
                    return error("E_RUNTIME", &err.to_string());
                }
            }
            ok(json!({ "deleted": true }))
        }
        _ => error("E_ARGS", &format!("unsupported op: {}", op)),
    }
}

fn ok(data: Value) -> Value {
    json!({ "ok": true, "version": VERSION, "data": data })
}

fn error(code: &str, message: &str) -> Value {
    json!({
        "ok": false,
        "version": VERSION,
        "error": { "code": code, "message": message }
    })
}
"""
    if key == ("dotnet", "storage_fs"):
        return """using System;
using System.Collections.Generic;
using System.IO;

public static class Adapter {
  public const string Version = "v1";

  public static Dictionary<string, object> Handle(Dictionary<string, object> request) {
    if (request == null) {
      return Error("E_SCHEMA", "request must be an object");
    }
    var backend = GetString(request, "backend");
    if (string.IsNullOrEmpty(backend)) {
      backend = "fs";
    }
    if (backend != "fs") {
      return Error("E_UNSUPPORTED", $"unsupported backend: {backend}");
    }
    var op = GetString(request, "op");
    var parameters = request.TryGetValue("params", out var paramsObj) && paramsObj is Dictionary<string, object> map
      ? map
      : new Dictionary<string, object>();
    var path = parameters.TryGetValue("path", out var pathObj) ? pathObj?.ToString() : null;
    if (string.IsNullOrEmpty(path)) {
      return Error("E_ARGS", "path is required");
    }
    var fullPath = Path.GetFullPath(path);
    try {
      switch (op) {
        case "put":
          var content = parameters.TryGetValue("content", out var contentObj) ? contentObj?.ToString() ?? string.Empty : string.Empty;
          var directory = Path.GetDirectoryName(fullPath);
          if (!string.IsNullOrEmpty(directory)) {
            Directory.CreateDirectory(directory);
          }
          File.WriteAllText(fullPath, content);
          return Ok(new Dictionary<string, object> { { "written", true } });
        case "get":
          if (!File.Exists(fullPath)) {
            return Error("E_RUNTIME", "file not found");
          }
          var text = File.ReadAllText(fullPath);
          return Ok(new Dictionary<string, object> { { "content", text } });
        case "list":
          var glob = parameters.TryGetValue("glob", out var globObj) ? globObj?.ToString() : "*";
          string[] items;
          if (Directory.Exists(fullPath)) {
            items = Directory.GetFileSystemEntries(fullPath, string.IsNullOrEmpty(glob) ? "*" : glob);
          } else if (File.Exists(fullPath)) {
            items = new[] { fullPath };
          } else {
            items = Array.Empty<string>();
          }
          return Ok(new Dictionary<string, object> { { "items", items } });
        case "delete":
          if (Directory.Exists(fullPath)) {
            Directory.Delete(fullPath, true);
          } else if (File.Exists(fullPath)) {
            File.Delete(fullPath);
          }
          return Ok(new Dictionary<string, object> { { "deleted", true } });
        default:
          return Error("E_ARGS", $"unsupported op: {op}");
      }
    } catch (Exception ex) {
      return Error("E_RUNTIME", ex.Message);
    }
  }

  private static Dictionary<string, object> Ok(Dictionary<string, object> data) => new() {
    { "ok", true },
    { "version", Version },
    { "data", data },
  };

  private static Dictionary<string, object> Error(string code, string message) => new() {
    { "ok", false },
    { "version", Version },
    { "error", new Dictionary<string, object> { { "code", code }, { "message", message } } },
  };

  private static string GetString(Dictionary<string, object> request, string key) {
    return request.TryGetValue(key, out var value) && value is string s ? s : string.Empty;
  }
}
"""
    if key[1] == "schema_stub":
        if language == "python":
            return (
                "from __future__ import annotations\n\n"
                "from pathlib import Path\n"
                "from typing import Any, Dict\n\n"
                "from tools.envelope import error, ok\n\n"
                "VERSION = 'v1'\n"
                f"SCHEMA_PATH = Path(__file__).resolve().parent.parent / '{pkg}' / 'schema.v1.json'\n\n"
                "\n"
                "def handle(request: Dict[str, Any]) -> Dict[str, Any]:\n"
                "    if not isinstance(request, dict):\n"
                "        return error('E_SCHEMA', 'request must be a JSON object')\n"
                "    # TODO: load SCHEMA_PATH and validate request when jsonschema is available\n"
                "    return ok({{}})\n"
            )
        if language in {"node", "nextjs"}:
            if language == "node":
                header = "const VERSION = 'v1';\n\nfunction handle(request) {"
                footer = "}\n\nmodule.exports = { VERSION, handle };\n"
            else:
                header = "export const VERSION = 'v1';\n\nexport default function handle(request) {"
                footer = "}\n"
            body = (
                "\n  if (typeof request !== 'object' || request === null) {\n"
                "    return { ok: false, version: VERSION, error: { code: 'E_SCHEMA', message: 'request must be an object' } };\n"
                "  }\n"
                f"  // TODO: validate request against schemas/tools/{tool_id}.v1.json\n"
                "  return { ok: true, version: VERSION, data: {} };\n"
            )
            return header + body + footer
        if language == "go":
            return (
                """package main

const Version = "v1"

func Handle(req map[string]interface{}) map[string]interface{} {
    if req == nil {
        return map[string]interface{}{
            "ok": false,
            "version": Version,
            "error": map[string]interface{}{
                "code":    "E_SCHEMA",
                "message": "request must be an object",
            },
        }
    }
    // TODO: validate req against schemas/tools/%s.v1.json
    return map[string]interface{}{
        "ok":      true,
        "version": Version,
        "data":    map[string]interface{}{},
    }
}
"""
                % tool_id
            )
        if language == "rust":
            return f"""use serde_json::{{json, Value}};

pub const VERSION: &str = "v1";

pub fn handle(request: &Value) -> Value {{
    if !request.is_object() {{
        return json!({{ "ok": false, "version": VERSION, "error": {{ "code": "E_SCHEMA", "message": "request must be an object" }} }});
    }}
    // TODO: validate request against schemas/tools/{tool_id}.v1.json
    json!({{ "ok": true, "version": VERSION, "data": {{}} }})
}}
"""
        if language == "java":
            return (
                """import java.util.HashMap;
import java.util.Map;

public class Adapter {
  public static final String VERSION = "v1";

  public static Map<String, Object> handle(Map<String, Object> request) {
    if (request == null) {
      return error("E_SCHEMA", "request must be an object");
    }
    // TODO: validate request against schemas/tools/%s.v1.json
    return ok(new HashMap<>());
  }

  private static Map<String, Object> ok(Map<String, Object> data) {
    Map<String, Object> res = new HashMap<>();
    res.put("ok", true);
    res.put("version", VERSION);
    res.put("data", data);
    return res;
  }

  private static Map<String, Object> error(String code, String message) {
    Map<String, Object> res = new HashMap<>();
    res.put("ok", false);
    res.put("version", VERSION);
    Map<String, Object> err = new HashMap<>();
    err.put("code", code);
    err.put("message", message);
    res.put("error", err);
    return res;
  }
}
"""
                % tool_id
            )
        if language == "dotnet":
            return (
                """using System;
using System.Collections.Generic;

public static class Adapter {
  public const string Version = "v1";

  public static Dictionary<string, object> Handle(Dictionary<string, object> request) {
    if (request == null) {
      return Error("E_SCHEMA", "request must be an object");
    }
    // TODO: validate request against schemas/tools/%s.v1.json
    return Ok(new Dictionary<string, object>());
  }

  private static Dictionary<string, object> Ok(Dictionary<string, object> data) => new() {
    { "ok", true },
    { "version", Version },
    { "data", data },
  };

  private static Dictionary<string, object> Error(string code, string message) => new() {
    { "ok", false },
    { "version", Version },
    { "error", new Dictionary<string, object> { { "code", code }, { "message", message } } },
  };
}
"""
                % tool_id
            )
    raise ValueError(f"no adapter template for {language}:{template_name}")


def _render_adapter(tool_id: str, adapter_cfg: Dict[str, Any], repo_root: Path) -> Path:
    language = adapter_cfg["language"]
    template_name = adapter_cfg["template"]
    filename = ADAPTER_FILENAMES.get(language)
    if not filename:
        raise ValueError(f"unsupported adapter language: {language}")
    content = _adapter_content(tool_id, language, template_name)
    target = repo_root / "tools" / _package_name(tool_id) / "adapters" / filename
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return target


def _generate_doc(spec: ToolSpec) -> str:
    tool_meta = spec.raw.get("tool", {})
    summary = tool_meta.get("summary", "")
    body: List[str] = [f"# {tool_meta.get('name', spec.tool_id.capitalize())}", "", summary, ""]
    quickstart = spec.raw.get("docs", {}).get("quickstart")
    if quickstart:
        body.extend(["## Quickstart", "", quickstart.strip(), ""])
    examples = spec.raw.get("docs", {}).get("examples", [])
    if examples:
        body.append("## Examples")
        body.append("")
        for example in examples:
            body.append(f"### {example.get('title', 'Example')}")
            body.append("")
            body.append("```python")
            body.append(example.get("code", "").rstrip())
            body.append("```")
            body.append("")
    return "\n".join(body).rstrip() + "\n"


def _expect_lines(expect: Dict[str, Any]) -> List[str]:
    lines: List[str] = []
    for path, value in expect.items():
        access = "res"
        for segment in path.split("."):
            access += f"[{json.dumps(segment)}]"
        if isinstance(value, bool):
            lines.append(f"    assert {access} is {value}")
        else:
            lines.append(f"    assert {access} == {repr(value)}")
    return lines


def _generate_tests(spec: ToolSpec) -> str:
    explicit_cases = list(spec.raw.get("testing", {}).get("cases", []))
    op_cases: List[Dict[str, Any]] = []
    for op in spec.raw.get("operations", []):
        example = op.get("example") if isinstance(op, dict) else None
        if not isinstance(example, dict):
            continue
        req = example.get("request")
        resp = example.get("response")
        if not isinstance(req, dict):
            continue
        case: Dict[str, Any] = {"description": f"operation {op.get('id')} example", "request": req}
        if isinstance(resp, dict):
            # Treat response as the expected data payload unless explicitly wrapped
            if "data" in resp or "ok" in resp:
                case["expect"] = resp
            else:
                case["expect"] = {f"data.{k}": v for k, v in resp.items()}
        op_cases.append(case)
    cases = explicit_cases + op_cases
    lines = ["import json", "", "from tools import run_tool", "", ""]
    tool_id = spec.tool_id
    for idx, case in enumerate(cases, start=1):
        func_name = f"test_{tool_id}_{idx}"
        lines.append(f"def {func_name}() -> None:")
        payload = case.get("request", {})
        lines.append(f"    payload = {repr(payload)}")
        lines.append(f"    res = run_tool({json.dumps(tool_id)}, payload)")
        lines.append("    assert res['ok'] is True")
        expect = case.get("expect")
        if isinstance(expect, dict):
            lines.extend(_expect_lines(expect))
        lines.append("")
    if len(lines) == 5:  # no cases added
        lines.append(f"def test_{tool_id}_noop() -> None:")
        lines.append(f"    res = run_tool({json.dumps(tool_id)}, {{}})")
        lines.append("    assert res['ok'] is True")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _render_artifacts(spec: ToolSpec, output_root: Path, dry_run: bool) -> Dict[str, Any]:
    repo_root = Path(__file__).resolve().parents[1]
    pkg = _package_name(spec.tool_id)
    planned = {
        "schema": f"schemas/tools/{spec.tool_id}.v1.json",
        "adapters": [
            f"tools/{pkg}/adapters/{ADAPTER_FILENAMES.get(adapter['language'], '<unknown>')}"
            for adapter in spec.raw.get("adapters", [])
        ],
        "tests": [f"tests/tools/test_{pkg}.py"],
        "docs": [f"docs/tools/{spec.tool_id}.md"],
        "registry": "data/tools_registry.json",
    }
    if dry_run:
        return {"planned": planned}

    written: List[str] = []

    schema_path = repo_root / planned["schema"]
    schema_path.parent.mkdir(parents=True, exist_ok=True)
    schema_content = _schema_output(spec)
    schema_path.write_text(json.dumps(schema_content, indent=2) + "\n", encoding="utf-8")
    written.append(str(schema_path))

    for adapter in spec.raw.get("adapters", []):
        path = _render_adapter(spec.tool_id, adapter, repo_root)
        written.append(str(path))

    doc_path = repo_root / planned["docs"][0]
    doc_path.parent.mkdir(parents=True, exist_ok=True)
    doc_path.write_text(_generate_doc(spec), encoding="utf-8")
    written.append(str(doc_path))

    test_path = repo_root / planned["tests"][0]
    test_path.parent.mkdir(parents=True, exist_ok=True)
    test_path.write_text(_generate_tests(spec), encoding="utf-8")
    written.append(str(test_path))

    registry_path = _update_registry(spec, repo_root)
    written.append(str(registry_path))

    return {"written": written}


def _collect_registry_entry(spec: ToolSpec) -> Dict[str, Any]:
    tool_meta = spec.raw.get("tool", {})
    entry = {
        "id": tool_meta.get("id"),
        "name": tool_meta.get("name"),
        "summary": tool_meta.get("summary"),
        "category": tool_meta.get("category"),
        "version": tool_meta.get("version"),
        "envelope": spec.raw.get("envelope", {}),
        "policy": spec.raw.get("policy", {}),
        "adapters": [],
    }
    for adapter in spec.raw.get("adapters", []):
        entry["adapters"].append(
            {
                "language": adapter.get("language"),
                "template": adapter.get("template"),
                "deps": adapter.get("deps", {}),
            }
        )
    return entry


def _update_registry(spec: ToolSpec, repo_root: Path) -> Path:
    registry_path = repo_root / "data" / "tools_registry.json"
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    if registry_path.exists():
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
    else:
        registry = {"tools": {}}
    if "tools" not in registry or not isinstance(registry["tools"], dict):
        registry["tools"] = {}
    entry = _collect_registry_entry(spec)
    registry["tools"][entry["id"]] = entry
    registry["tools"] = dict(sorted(registry["tools"].items(), key=lambda item: item[0]))
    registry_path.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")
    return registry_path


@click.command()
@click.argument("spec", type=click.Path(path_type=Path))
@click.option(
    "--output", "output_root", type=click.Path(path_type=Path), default=Path(".mcpd/toolgen")
)
@click.option("--dry-run", is_flag=True, help="Report artifacts without writing them")
def toolgen(spec: Path, output_root: Path, dry_run: bool) -> None:
    # Scaffold Promptware tools from a tool generator spec.
    spec_obj = _load_spec(spec)
    _validate_spec(spec_obj)
    result = _render_artifacts(spec_obj, output_root, dry_run)
    click.echo(json.dumps({"ok": True, "version": "v1", "data": result}, indent=2))


if __name__ == "__main__":  # pragma: no cover
    toolgen()
