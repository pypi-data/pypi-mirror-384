"""
Python reverse parser: Python code → PW DSL

Extracts agent definitions from Python FastAPI/Flask servers.
"""

import ast
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Set

from .base_parser import BaseReverseParser, ExtractedAgent


class PythonReverseParser(BaseReverseParser):
    """Parse Python FastAPI/Flask servers → PW DSL."""

    # Pattern to match handler function names: handle_verb_name_v1
    HANDLER_PATTERN = re.compile(r"handle_(.+)_v(\d+)")

    # Pattern to match verb names in routing: "verb.name@v1"
    VERB_PATTERN = re.compile(r'"([a-z0-9_.]+)@v(\d+)"')

    def parse_file(self, file_path: str) -> ExtractedAgent:
        """Parse Python file and extract agent definition."""
        with open(file_path, 'r') as f:
            source = f.read()

        tree = ast.parse(source)

        # Extract components
        framework = self.detect_framework(tree)
        agent_name = self._extract_agent_name(tree, framework)
        port = self.extract_port(tree)
        handlers = self.extract_handlers(tree)
        tools = self.extract_tools(tree)

        # Extract verbs from routing logic (more reliable than handler names)
        routed_verbs = self._extract_verbs_from_routing(tree)

        # Merge handler info with routing info
        verbs = self._merge_verb_info(handlers, routed_verbs)

        # Calculate confidence
        confidence = self.calculate_confidence(
            framework_detected=(framework != 'unknown'),
            verbs_found=len(verbs),
            params_extracted=sum(len(v.get('params', [])) for v in verbs),
            returns_extracted=sum(len(v.get('returns', [])) for v in verbs)
        )

        notes = []
        if framework == 'unknown':
            notes.append("Framework could not be detected automatically")
        if not verbs:
            notes.append("No verbs/handlers found - may not be an MCP server")

        return ExtractedAgent(
            name=agent_name,
            port=port,
            lang="python",
            verbs=verbs,
            tools=tools,
            confidence_score=confidence,
            framework=framework,
            extraction_notes=notes
        )

    def detect_framework(self, tree: ast.Module) -> str:
        """Detect FastAPI vs Flask vs other."""
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module == 'fastapi':
                    return 'fastapi'
                elif node.module == 'flask':
                    return 'flask'
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if 'fastapi' in alias.name:
                        return 'fastapi'
                    elif 'flask' in alias.name:
                        return 'flask'
        return 'unknown'

    def extract_handlers(self, tree: ast.Module) -> List[Dict[str, Any]]:
        """Extract handler functions matching handle_*_v* pattern."""
        handlers = []

        for node in ast.walk(tree):
            # Handle both sync and async functions
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                match = self.HANDLER_PATTERN.match(node.name)
                if match:
                    verb_name = match.group(1).replace('_', '.')
                    version = f"v{match.group(2)}"

                    handler = {
                        'name': f"{verb_name}@{version}",
                        'function': node,
                        'params': self._extract_params_from_function(node),
                        'returns': self._extract_returns_from_function(node)
                    }
                    handlers.append(handler)

        return handlers

    def extract_port(self, tree: ast.Module) -> int:
        """Extract port from uvicorn.run() or app.run() call."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Check for uvicorn.run(app, port=XXXX)
                if (hasattr(node.func, 'attr') and
                    node.func.attr == 'run'):
                    for keyword in node.keywords:
                        if keyword.arg == 'port':
                            if isinstance(keyword.value, ast.Constant):
                                return keyword.value.value

                # Check for app.run(port=XXXX) - Flask
                if (hasattr(node.func, 'attr') and
                    node.func.attr == 'run'):
                    for keyword in node.keywords:
                        if keyword.arg == 'port':
                            if isinstance(keyword.value, ast.Constant):
                                return keyword.value.value

        return 8000  # default

    def extract_tools(self, tree: ast.Module) -> List[str]:
        """Extract tools from configured_tools list."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if (isinstance(target, ast.Name) and
                        target.id == 'configured_tools'):
                        if isinstance(node.value, ast.List):
                            tools = []
                            for elt in node.value.elts:
                                if isinstance(elt, ast.Constant):
                                    tools.append(elt.value)
                            return tools
        return []

    def _extract_agent_name(self, tree: ast.Module, framework: str) -> str:
        """Extract agent name from FastAPI title or app name."""
        if framework == 'fastapi':
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if (hasattr(node.func, 'id') and
                        node.func.id == 'FastAPI'):
                        for keyword in node.keywords:
                            if keyword.arg == 'title':
                                if isinstance(keyword.value, ast.Constant):
                                    return keyword.value.value

        # Fallback: look for app assignment
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == 'app':
                        if isinstance(node.value, ast.Call):
                            # Try to extract from call
                            pass

        return "unknown-agent"

    def _extract_params_from_function(self, func: ast.FunctionDef) -> List[Dict[str, str]]:
        """Extract parameters from function signature and validation."""
        params = []

        # 1. Parse docstring for parameter info
        docstring = ast.get_docstring(func)
        if docstring:
            # Look for "Parameters:" section
            in_params = False
            for line in docstring.split('\n'):
                if 'Parameters:' in line or 'params:' in line.lower():
                    in_params = True
                    continue
                elif 'Returns:' in line or 'returns:' in line.lower():
                    in_params = False

                if in_params and '- ' in line:
                    # Format: "- param_name (type): description" or "- param_name (type)"
                    parts = line.strip().split('(')
                    if len(parts) >= 2:
                        param_name = parts[0].replace('-', '').strip()
                        # Extract type between ( and )
                        type_part = parts[1].split(')')[0].strip()
                        # Remove any trailing colon and description
                        param_type = type_part.split(':')[0].strip()
                        params.append({
                            'name': param_name,
                            'type': self._normalize_type(param_type)
                        })

        # 2. Scan function body for validation checks
        for node in ast.walk(func):
            if isinstance(node, ast.Compare):
                # Look for: if "param_name" not in params:
                if (isinstance(node.left, ast.Constant) and
                    any(isinstance(op, ast.NotIn) for op in node.ops)):
                    param_name = node.left.value
                    # Don't duplicate
                    if not any(p['name'] == param_name for p in params):
                        params.append({
                            'name': param_name,
                            'type': 'string'  # default
                        })

        # 3. Check function signature type hints
        for arg in func.args.args:
            if arg.arg == 'self' or arg.arg == 'params':
                continue
            if arg.annotation:
                param_type = self._extract_type_from_annotation(arg.annotation)
                if not any(p['name'] == arg.arg for p in params):
                    params.append({
                        'name': arg.arg,
                        'type': param_type
                    })

        return params

    def _extract_returns_from_function(self, func: ast.FunctionDef) -> List[Dict[str, str]]:
        """Extract return fields from function."""
        returns = []

        # 1. Parse docstring
        docstring = ast.get_docstring(func)
        if docstring:
            in_returns = False
            for line in docstring.split('\n'):
                if 'Returns:' in line or 'returns:' in line.lower():
                    in_returns = True
                    continue
                elif in_returns and '- ' in line:
                    parts = line.strip().split('(')
                    if len(parts) >= 2:
                        return_name = parts[0].replace('-', '').strip()
                        return_type = parts[1].replace(')', '').strip()
                        returns.append({
                            'name': return_name,
                            'type': self._normalize_type(return_type)
                        })
                elif in_returns and not line.strip().startswith('-'):
                    # End of returns section
                    break

        # 2. Scan return statements for dict keys
        for node in ast.walk(func):
            if isinstance(node, ast.Return):
                if isinstance(node.value, ast.Dict):
                    for key in node.value.keys:
                        if isinstance(key, ast.Constant):
                            return_name = key.value
                            # Skip error keys (from error handling, not actual returns)
                            if return_name == 'error':
                                continue
                            # Don't duplicate
                            if not any(r['name'] == return_name for r in returns):
                                # Try to infer type from value
                                return_type = 'string'  # default
                                returns.append({
                                    'name': return_name,
                                    'type': return_type
                                })

        return returns

    def _extract_verbs_from_routing(self, tree: ast.Module) -> Dict[str, Set[str]]:
        """
        Extract verb names from routing logic in /mcp endpoint.

        Returns dict mapping verb names to set of fields mentioned in context.
        """
        verbs = {}

        for node in ast.walk(tree):
            # Look for string literals matching verb pattern
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                match = self.VERB_PATTERN.match(node.value)
                if match:
                    verb_name = f"{match.group(1)}@v{match.group(2)}"
                    if verb_name not in verbs:
                        verbs[verb_name] = set()

        return verbs

    def _merge_verb_info(
        self,
        handlers: List[Dict[str, Any]],
        routed_verbs: Dict[str, Set[str]]
    ) -> List[Dict[str, Any]]:
        """
        Merge information from handlers and routing.

        Handlers have param/return info.
        Routing confirms which verbs are actually exposed.
        """
        merged = []

        # Start with handlers (they have the most info)
        handler_map = {h['name']: h for h in handlers}

        # Add all routed verbs
        for verb_name in routed_verbs.keys():
            if verb_name in handler_map:
                # Use handler info
                merged.append({
                    'name': verb_name,
                    'params': handler_map[verb_name]['params'],
                    'returns': handler_map[verb_name]['returns']
                })
            else:
                # Verb is routed but no handler found
                merged.append({
                    'name': verb_name,
                    'params': [],
                    'returns': []
                })

        # Add handlers that weren't in routing (defensive)
        for verb_name, handler in handler_map.items():
            if verb_name not in routed_verbs:
                merged.append({
                    'name': verb_name,
                    'params': handler['params'],
                    'returns': handler['returns']
                })

        return merged

    def _normalize_type(self, type_str: str) -> str:
        """Normalize Python type to PW type."""
        type_str = type_str.strip()

        # Handle List[...] and array types
        if type_str.startswith('List[') or type_str.startswith('list['):
            inner_type = type_str[5:-1].strip()
            inner_pw = self._normalize_type(inner_type)
            return f'array<{inner_pw}>'

        # Handle Dict/dict
        if type_str.startswith('Dict') or type_str.startswith('dict'):
            return 'object'

        type_str_lower = type_str.lower()

        # Map Python types to PW types
        type_map = {
            'str': 'string',
            'string': 'string',
            'int': 'int',
            'integer': 'int',
            'bool': 'bool',
            'boolean': 'bool',
            'dict': 'object',
            'list': 'array',
            'float': 'float',
            'any': 'object',
        }

        return type_map.get(type_str_lower, 'string')

    def _extract_type_from_annotation(self, annotation: ast.AST) -> str:
        """Extract type from AST annotation node."""
        if isinstance(annotation, ast.Name):
            return self._normalize_type(annotation.id)
        elif isinstance(annotation, ast.Constant):
            return self._normalize_type(str(annotation.value))
        return 'string'  # default
