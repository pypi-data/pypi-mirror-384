from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


def load_schema(tool: str, spec_dir: str = "schemas/tools") -> Dict[str, Any]:
    p = Path(spec_dir) / f"{tool}.v1.json"
    if not p.exists():
        raise FileNotFoundError(f"schema not found for tool: {tool}")
    return json.loads(p.read_text(encoding="utf-8"))


def _write_python(tool: str, out_dir: Path, schema: Dict[str, Any]) -> Path:
    target = out_dir / "adapter_py.py"
    content = (
        """
from __future__ import annotations

import json
from typing import Dict, Any
from pathlib import Path

from tools.envelope import ok, error, validate_request
from tools.validator import validate_with_schema

VERSION = 'v1'

# Capability discovery: tools can advertise supported versions/features
def capabilities() -> Dict[str, Any]:
    return {
        'tool': '__TOOL__',
        'versions': ['v1'],
        'features': ['validation', 'envelope', 'idempotency'],
    }


def handle(request: Dict[str, Any]) -> Dict[str, Any]:
    # Envelope + schema validation (extend with jsonschema against schema.v1.json)
    err = validate_request(request)
    if err:
        return err
    # Optional: idempotency support
    _idempotency_key = request.get('idempotency_key')
    valid, emsg = validate_with_schema(Path(__file__).parent.parent / '__TOOL__' / 'schema.v1.json', request)
    if not valid:
        return error('E_SCHEMA', emsg or 'invalid request')
    try:
        # TODO: implement tool logic using request['data'] per schema
        return ok({})
    except Exception as ex:  # noqa: BLE001
        return error('E_RUNTIME', str(ex))
"""
    ).lstrip()
    content = content.replace("__TOOL__", tool)
    target.write_text(content, encoding="utf-8")
    return target


def _write_node(tool: str, out_dir: Path, schema: Dict[str, Any]) -> Path:
    target = out_dir / "adapter_node.js"
    content = (
        """
'use strict';
const VERSION='v1';
const fs = require('fs');
const path = require('path');

let _validator = undefined;
function _loadValidator() {
  if (_validator !== undefined) return _validator;
  try {
    const Ajv = require('ajv');
    let addFormats = null; try { addFormats = require('ajv-formats'); } catch (_e) { /* optional */ }
    const ajv = new Ajv({ allErrors: true, strict: false });
    if (addFormats) addFormats(ajv);
    const schemaPath = path.join(__dirname, '..', 'schema.v1.json');
    const schema = JSON.parse(fs.readFileSync(schemaPath, 'utf-8'));
    const requestSchema = (schema.properties && schema.properties.request) || schema.request || schema;
    _validator = ajv.compile(requestSchema);
  } catch (e) {
    _validator = null; // Ajv not available; skip deep validation
  }
  return _validator;
}

function capabilities() {
  return { tool: '__TOOL__', versions: ['v1'], features: ['validation','envelope','idempotency'] };
}

function ok(data) { return { ok: true, version: VERSION, data: data||{} }; }
function error(code, message, details) {
  const err={ code, message }; if (details) err.details=details; return { ok:false, version: VERSION, error: err };
}

function validateRequest(req) {
  if (typeof req !== 'object' || req === null) return error('E_SCHEMA','request must be an object');
  const validate = _loadValidator();
  if (validate) {
    const valid = validate(req);
    if (!valid) return error('E_SCHEMA','schema validation failed', { errors: validate.errors });
  }
  return null;
}

exports.capabilities = capabilities;
exports.handle = function(req) {
  const e = validateRequest(req); if (e) return e;
  const _idempotencyKey = req.idempotency_key;
  try {
    // TODO: implement tool logic using req.data per schema
    return ok({});
  } catch (ex) {
    return error('E_RUNTIME', String((ex && ex.message) || ex));
  }
};
"""
    )
    content = content.replace("__TOOL__", tool)
    target.write_text(content, encoding="utf-8")
    return target


def _write_go(tool: str, out_dir: Path, schema: Dict[str, Any]) -> Path:
    target = out_dir / "adapter_go.go"
    content = (
        f"package {tool.replace('-', '_')}\n\n" +
        "import (\n\t\"encoding/json\"\n\t\"errors\"\n)\n\n" +
        "type Response struct { Ok bool `json:\"ok\"`; Version string `json:\"version\"`; Data map[string]any `json:\"data\"`; Error *RespError `json:\"error,omitempty\"` }\n" +
        "type RespError struct { Code string `json:\"code\"`; Message string `json:\"message\"`; Details map[string]any `json:\"details,omitempty\"` }\n\n" +
        "func capabilities() map[string]any { return map[string]any{\"tool\": \"" + tool + "\", \"versions\": []string{\"v1\"}, \"features\": []string{\"validation\",\"envelope\",\"idempotency\"}} }\n\n" +
        "func ok(data map[string]any) Response { if data==nil { data = map[string]any{} }; return Response{Ok:true, Version:\"v1\", Data:data} }\n" +
        "func err(code, msg string, details map[string]any) Response { return Response{Ok:false, Version:\"v1\", Error:&RespError{Code:code, Message:msg, Details:details}} }\n\n" +
        "func validateRequest(req map[string]any) error { if req==nil { return errors.New(\"request must be an object\") }; return nil }\n\n" +
        "func Handle(req map[string]any) Response { if e:=validateRequest(req); e!=nil { return err(\"E_SCHEMA\", e.Error(), nil) }; /* TODO implement */ return ok(map[string]any{}) }\n"
    )
    target.write_text(content, encoding="utf-8")
    return target


def _write_rust(tool: str, out_dir: Path, schema: Dict[str, Any]) -> Path:
    target = out_dir / "adapter_rust.rs"
    content = (
        "use std::collections::HashMap;\nuse serde_json::{json, Value};\n\n" +
        "pub fn capabilities() -> Value { json!({ \"tool\": \"" + tool + "\", \"versions\": [\"v1\"], \"features\": [\"validation\",\"envelope\",\"idempotency\"] }) }\n\n" +
        "fn ok(data: Value) -> Value { json!({ \"ok\": true, \"version\": \"v1\", \"data\": data }) }\n" +
        "fn err(code: &str, message: &str) -> Value { json!({ \"ok\": false, \"version\": \"v1\", \"error\": { \"code\": code, \"message\": message } }) }\n\n" +
        "fn validate_request(req: &HashMap<String, Value>) -> Option<Value> { if req.is_empty() { return Some(err(\"E_SCHEMA\", \"request must be an object\")); } None }\n\n" +
        "pub fn handle(req: &HashMap<String, Value>) -> Value { if let Some(e)=validate_request(req) { return e; } /* TODO implement */ ok(json!({})) }\n"
    )
    target.write_text(content, encoding="utf-8")
    return target


def _write_java(tool: str, out_dir: Path, schema: Dict[str, Any]) -> Path:
    target = out_dir / "Adapter.java"
    content = (
        "import java.util.*;\n\n" +
        "public class Adapter {\n" +
        "  public static Map<String,Object> capabilities(){ Map<String,Object> m=new HashMap<>(); m.put(\"tool\", \"" + tool + "\"); m.put(\"versions\", Arrays.asList(\"v1\")); m.put(\"features\", Arrays.asList(\"validation\",\"envelope\",\"idempotency\")); return m; }\n" +
        "  private static Map<String,Object> ok(Map<String,Object> data){ Map<String,Object> r=new HashMap<>(); r.put(\"ok\", true); r.put(\"version\", \"v1\"); r.put(\"data\", data!=null?data:new HashMap<>()); return r; }\n" +
        "  private static Map<String,Object> err(String code,String msg){ Map<String,Object> r=new HashMap<>(); r.put(\"ok\", false); r.put(\"version\", \"v1\"); Map<String,Object> e=new HashMap<>(); e.put(\"code\", code); e.put(\"message\", msg); r.put(\"error\", e); return r; }\n" +
        "  private static Map<String,Object> validateRequest(Map<String,Object> req){ if (req==null) return err(\"E_SCHEMA\", \"request must be an object\"); return null; }\n" +
        "  public static Map<String,Object> handle(Map<String,Object> req){ Map<String,Object> v=validateRequest(req); if (v!=null) return v; /* TODO implement */ return ok(new HashMap<>()); }\n" +
        "}\n"
    )
    target.write_text(content, encoding="utf-8")
    return target


def _write_dotnet(tool: str, out_dir: Path, schema: Dict[str, Any]) -> Path:
    target = out_dir / "Adapter.cs"
    content = (
        "using System.Collections.Generic;\n\n" +
        "public static class Adapter {\n" +
        "  public static Dictionary<string,object> Capabilities(){ return new Dictionary<string,object>{ {\"tool\", \"" + tool + "\"}, {\"versions\", new List<string>{\"v1\"}}, {\"features\", new List<string>{\"validation\",\"envelope\",\"idempotency\"}} }; }\n" +
        "  private static Dictionary<string,object> Ok(Dictionary<string,object> data){ return new Dictionary<string,object>{{\"ok\", true},{\"version\", \"v1\"},{\"data\", data ?? new Dictionary<string,object>()}}; }\n" +
        "  private static Dictionary<string,object> Err(string code,string msg){ return new Dictionary<string,object>{{\"ok\", false},{\"version\", \"v1\"},{\"error\", new Dictionary<string,object>{{\"code\", code},{\"message\", msg}}}}; }\n" +
        "  private static Dictionary<string,object>? ValidateRequest(Dictionary<string,object> req){ if (req==null) return Err(\"E_SCHEMA\", \"request must be an object\"); return null; }\n" +
        "  public static Dictionary<string,object> Handle(Dictionary<string,object> req){ var v=ValidateRequest(req); if (v!=null) return v; /* TODO implement */ return Ok(new Dictionary<string,object>()); }\n" +
        "}\n"
    )
    target.write_text(content, encoding="utf-8")
    return target


def _write_cpp(tool: str, out_dir: Path, schema: Dict[str, Any]) -> Path:
    target = out_dir / "adapter_cpp.cpp"
    content = (
        "#include <string>\n#include <map>\n\n" +
        "std::map<std::string,std::string> capabilities(){ return {{ {\"tool\", \"" + tool + "\"}, {\"versions\", \"v1\"}, {\"features\", \"validation,envelope,idempotency\"} }}; }\n" +
        "std::map<std::string,std::string> ok(){ return {{ {\"ok\", \"true\"}, {\"version\", \"v1\"} }}; }\n" +
        "std::map<std::string,std::string> err(const std::string& code,const std::string& msg){ return {{ {\"ok\", \"false\"}, {\"version\", \"v1\"}, {\"error\", code+\":\"+msg} }}; }\n\n" +
        "std::map<std::string,std::string> handle(){ /* TODO validate/implement */ return ok(); }\n"
    )
    target.write_text(content, encoding="utf-8")
    return target


def generate(tool: str, spec_dir: str = "schemas/tools") -> Dict[str, Any]:
    schema = load_schema(tool, spec_dir)
    base = Path("tools") / tool
    out_dir = base / "adapters"
    out_dir.mkdir(parents=True, exist_ok=True)
    py = _write_python(tool, out_dir, schema)
    js = _write_node(tool, out_dir, schema)
    go = _write_go(tool, out_dir, schema)
    rs = _write_rust(tool, out_dir, schema)
    jv = _write_java(tool, out_dir, schema)
    cs = _write_dotnet(tool, out_dir, schema)
    cp = _write_cpp(tool, out_dir, schema)
    (base / "schema.v1.json").write_text(json.dumps(schema, indent=2), encoding="utf-8")
    return {
        "python": str(py),
        "node": str(js),
        "go": str(go),
        "rust": str(rs),
        "java": str(jv),
        ".net": str(cs),
        "cpp": str(cp),
        "schema": str(base / "schema.v1.json"),
    }


def generate_all(spec_dir: str = "schemas/tools") -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    for p in Path(spec_dir).glob("*.json"):
        tool = p.stem.split(".")[0]
        results.append(generate(tool, spec_dir))
    return results


