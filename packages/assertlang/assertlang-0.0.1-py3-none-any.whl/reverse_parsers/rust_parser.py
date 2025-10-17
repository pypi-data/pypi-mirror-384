"""
Rust reverse parser: Rust code → PW DSL

Extracts agent definitions from Warp/Actix servers.
"""

import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Set

from .base_parser import BaseReverseParser, ExtractedAgent


class RustReverseParser(BaseReverseParser):
    """Parse Rust Warp/Actix servers → PW DSL."""

    # Pattern to match handler function names: handle_verb_name_v1
    HANDLER_PATTERN = re.compile(r"fn\s+(handle_[a-z_]+_v\d+)\s*\(")

    # Pattern to match verb names in verbs endpoint: ["verb.name@v1", ...]
    VERB_PATTERN = re.compile(r'["\']([a-z0-9_.]+@v\d+)["\']')

    # Pattern to match doc comment params: /// - param_name (Type): Description
    DOC_PARAM_PATTERN = re.compile(r'///\s*(?:-\s*)?(\w+)\s*\(([^)]+)\):\s*(.+)')

    # Pattern to match returns from doc comments: /// Returns: field_name (Type): Description
    DOC_RETURN_PATTERN = re.compile(r'///\s*(?:Returns?:?\s*)?(\w+)\s*\(([^)]+)\):\s*(.+)')

    def parse_file(self, file_path: str) -> ExtractedAgent:
        """Parse Rust file and extract agent definition."""
        with open(file_path, 'r') as f:
            source = f.read()

        # Extract components
        framework = self.detect_framework(source)
        agent_name = self._extract_agent_name(source, framework)
        port = self.extract_port(source)
        handlers = self.extract_handlers(source)
        tools = self.extract_tools(source)

        # Extract verbs from routing logic (more reliable than handler names)
        routed_verbs = self._extract_verbs_from_routing(source)

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
            lang="rust",
            verbs=verbs,
            tools=tools,
            confidence_score=confidence,
            framework=framework,
            extraction_notes=notes
        )

    def detect_framework(self, source: str) -> str:
        """Detect Warp vs Actix vs other."""
        # Check use statements
        if re.search(r"use\s+warp::", source):
            return 'warp'
        if re.search(r"use\s+actix_web::", source):
            return 'actix'

        # Check for framework-specific patterns
        if 'warp::serve' in source or 'warp::Filter' in source:
            return 'warp'
        if 'HttpServer::new' in source or 'actix_web::' in source:
            return 'actix'

        return 'unknown'

    def extract_handlers(self, source: str) -> List[Dict[str, Any]]:
        """Extract handler functions matching handle_*_v* pattern."""
        handlers = []

        # Find all handler functions with their full context
        handler_matches = list(self.HANDLER_PATTERN.finditer(source))

        for match in handler_matches:
            handler_func_name = match.group(1)

            # Extract the verb name from the handler function name
            # handle_echo_message_v1 -> echo.message@v1
            verb_name = self._handler_name_to_verb(handler_func_name)

            # Skip if this is an internal handler
            if verb_name is None:
                continue

            # Extract doc comments and function body
            func_start = match.start()

            # Look for doc comments before the function (up to 1000 chars back)
            doc_search_start = max(0, func_start - 1000)
            preceding_text = source[doc_search_start:func_start]

            # Extract only the last block of /// comments
            doc_text = self._extract_doc_comments(preceding_text)

            # Extract params and returns from doc comments
            params = self._extract_params_from_docs(doc_text)
            returns = self._extract_returns_from_docs(doc_text)

            # Also extract from function body if docs are incomplete
            func_body = self._extract_function_body(source, func_start)
            if not params:
                params = self._extract_params_from_body(func_body)
            if not returns:
                returns = self._extract_returns_from_body(func_body)

            handler = {
                'name': verb_name,
                'params': params,
                'returns': returns
            }
            handlers.append(handler)

        return handlers

    def extract_port(self, source: str) -> int:
        """Extract port from warp::serve() or actix run() call."""
        # Look for various port patterns
        patterns = [
            r'\.run\(\(\[[\d,\s]+\],\s*(\d+)\)\)',  # Warp: .run(([127, 0, 0, 1], 9090))
            r'let\s+port:\s*u16\s*=\s*(\d+)',  # Direct assignment: let port: u16 = 9090
            r'const\s+PORT:\s*u16\s*=\s*(\d+)',  # Const: const PORT: u16 = 9090
            r'bind\(["\'][\d.]+:(\d+)["\']\)',  # Actix: bind("127.0.0.1:8080")
        ]

        for pattern in patterns:
            match = re.search(pattern, source)
            if match:
                return int(match.group(1))

        return 8000  # default

    def extract_tools(self, source: str) -> List[str]:
        """Extract tools from configured_tools or CONFIGURED_TOOLS."""
        # Look for various tool configuration patterns
        patterns = [
            r'let\s+configured_tools\s*=\s*vec!\[([^\]]+)\]',  # vec!["tool1", "tool2"]
            r'static\s+CONFIGURED_TOOLS:\s*&\[&str\]\s*=\s*&\[([^\]]+)\]',  # static array
            r'const\s+CONFIGURED_TOOLS:\s*&\[&str\]\s*=\s*&\[([^\]]+)\]',  # const array
        ]

        for pattern in patterns:
            match = re.search(pattern, source, re.DOTALL)
            if match:
                tools_str = match.group(1)
                # Extract quoted strings
                tools = re.findall(r'["\']([^"\']+)["\']', tools_str)
                return tools

        return []

    def _extract_agent_name(self, source: str, framework: str) -> str:
        """Extract agent name from server info or comments."""
        # Look for: "name": "agent-name" in serverInfo
        match = re.search(r'"name":\s*"([^"]+)"', source)
        if match:
            return match.group(1)

        # Look for: MCP server for agent: agent-name
        match = re.search(r'MCP server for agent:\s*([^"]+)"', source)
        if match:
            return match.group(1).strip()

        # Look for: agent: "agent-name" in verbs endpoint
        match = re.search(r'"agent":\s*"([^"]+)"', source)
        if match:
            return match.group(1)

        return "unknown-agent"

    def _handler_name_to_verb(self, handler_name: str) -> Optional[str]:
        """
        Convert handler function name to verb name.

        Examples:
        - handle_echo_v1 -> echo@v1
        - handle_process_data_v1 -> process.data@v1
        - handle_health_check_v1 -> health.check@v1

        Returns None if the handler should be skipped (e.g., internal handlers).
        """
        # Remove 'handle_' prefix
        name = re.sub(r'^handle_', '', handler_name)

        # Extract version (v1, v2, etc.)
        version_match = re.search(r'_v(\d+)$', name)
        if version_match:
            version = f"v{version_match.group(1)}"
            name = name[:version_match.start()]
        else:
            version = "v1"

        # Convert snake_case to dot notation
        # process_data -> process.data
        # health_check -> health.check
        name = name.replace('_', '.')

        # Skip internal/utility handlers
        if name.lower() in ['error', 'health', 'ready', 'verbs']:
            return None

        return f"{name}@{version}"

    def _extract_doc_comments(self, preceding_text: str) -> str:
        """Extract Rust doc comments (///) from preceding text."""
        lines = preceding_text.split('\n')
        doc_lines = []

        # Collect lines starting with /// (in reverse, then reverse back)
        for line in reversed(lines):
            stripped = line.strip()
            if stripped.startswith('///'):
                # Remove /// and leading/trailing whitespace
                doc_lines.append(stripped[3:].strip())
            elif stripped and not stripped.startswith('//'):
                # Stop at first non-comment line
                break

        # Reverse to get original order
        return '\n'.join(reversed(doc_lines))

    def _extract_params_from_docs(self, doc_text: str) -> List[Dict[str, str]]:
        """Extract parameters from Rust doc comments."""
        params = []

        # Look for patterns like:
        # - param_name (Type): Description
        # # Params or # Parameters section
        in_params_section = False

        for line in doc_text.split('\n'):
            # Check for params section header
            if re.match(r'#\s*Param', line, re.IGNORECASE):
                in_params_section = True
                continue

            # Check for other section headers (returns, examples, etc.)
            if line.startswith('#') and not re.match(r'#\s*Param', line, re.IGNORECASE):
                in_params_section = False
                continue

            if in_params_section or not params:  # Also check outside sections
                # Match: - param_name (Type): Description
                match = re.match(r'-\s*(\w+)\s*\(([^)]+)\):\s*(.+)', line)
                if match:
                    param_name = match.group(1)
                    param_type = match.group(2).strip()

                    params.append({
                        'name': param_name,
                        'type': self._normalize_type(param_type)
                    })

        return params

    def _extract_returns_from_docs(self, doc_text: str) -> List[Dict[str, str]]:
        """Extract return fields from Rust doc comments."""
        returns = []

        # Look for # Returns section
        in_returns_section = False

        for line in doc_text.split('\n'):
            # Check for returns section header
            if re.match(r'#\s*Returns?', line, re.IGNORECASE):
                in_returns_section = True
                continue

            # Check for other section headers
            if line.startswith('#') and not re.match(r'#\s*Returns?', line, re.IGNORECASE):
                in_returns_section = False
                continue

            if in_returns_section:
                # Match: - field_name (Type): Description
                match = re.match(r'-\s*(\w+)\s*\(([^)]+)\):\s*(.+)', line)
                if match:
                    return_name = match.group(1)
                    return_type = match.group(2).strip()

                    returns.append({
                        'name': return_name,
                        'type': self._normalize_type(return_type)
                    })

        return returns

    def _extract_function_body(self, source: str, func_start: int) -> str:
        """Extract function body from source starting at func_start."""
        # Find the opening brace
        brace_start = source.find('{', func_start)
        if brace_start == -1:
            return ""

        # Track braces to find matching closing brace
        depth = 0
        i = brace_start

        while i < len(source):
            if source[i] == '{':
                depth += 1
            elif source[i] == '}':
                depth -= 1
                if depth == 0:
                    return source[brace_start:i+1]
            i += 1

        return source[brace_start:]

    def _extract_params_from_body(self, func_body: str) -> List[Dict[str, str]]:
        """Extract parameters from function body validation checks."""
        params = []

        # Look for: if !params.get("param_name").is_some()
        # or: params.get("param_name")
        param_checks = re.finditer(r'params\.get\(["\'](\w+)["\']\)', func_body)

        seen = set()
        for match in param_checks:
            param_name = match.group(1)
            if param_name not in seen:
                seen.add(param_name)
                params.append({
                    'name': param_name,
                    'type': 'string'  # default
                })

        return params

    def _extract_returns_from_body(self, func_body: str) -> List[Dict[str, str]]:
        """Extract return fields from function body json! macro calls."""
        returns = []

        # Look for the last json!({ ... }) in the function (likely the main return)
        # This regex handles nested braces
        json_pattern = r'json!\s*\(\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}'
        json_matches = list(re.finditer(json_pattern, func_body, re.DOTALL))

        if not json_matches:
            return returns

        # Take the last json! macro (most likely the main return)
        for match in reversed(json_matches):
            json_obj = match.group(1)

            # Skip if this is an error return
            if '"error"' in json_obj or 'error:' in json_obj:
                continue

            # Extract top-level fields - match both "field": value and field: value
            # This regex matches field names that may or may not be quoted
            field_pattern = r'^\s*"(\w+)"\s*:\s*([^,\n]+)'

            lines = json_obj.split('\n')
            for line in lines:
                # Try quoted field names first
                field_match = re.match(field_pattern, line)
                if field_match:
                    field_name = field_match.group(1)
                    field_value = field_match.group(2).strip()

                    # Skip error fields, metadata, and jsonrpc fields
                    if field_name in ['error', 'jsonrpc', 'id', 'code', 'message', 'result']:
                        continue

                    if not any(r['name'] == field_name for r in returns):
                        # Infer type from value
                        field_type = self._infer_type_from_value(field_value)
                        returns.append({
                            'name': field_name,
                            'type': field_type
                        })

            # If we found fields in this json! block, stop searching
            if returns:
                break

        return returns

    def _infer_type_from_value(self, value: str) -> str:
        """Infer PW type from Rust value."""
        value = value.strip()

        # Boolean values
        if value in ['true', 'false']:
            return 'bool'

        # Numeric values
        if re.match(r'^-?\d+$', value):
            return 'int'
        if re.match(r'^-?\d+\.\d+$', value):
            return 'float'

        # String literals
        if value.startswith('"') or value.startswith("'"):
            return 'string'

        # Vec or arrays
        if value.startswith('vec!') or value.startswith('['):
            return 'array'

        # Objects/structs
        if value.startswith('{'):
            return 'object'

        # String (default)
        return 'string'

    def _extract_verbs_from_routing(self, source: str) -> Dict[str, Set[str]]:
        """
        Extract verb names from routing logic in verbs endpoint.

        Returns dict mapping verb names to set of fields mentioned in context.
        """
        verbs = {}

        # Look for verb patterns in string literals
        for match in self.VERB_PATTERN.finditer(source):
            verb_name = match.group(1)
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
        """Normalize Rust type to PW type."""
        type_str = type_str.strip()

        # Handle Vec<...> types
        if type_str.startswith('Vec<') or type_str.startswith('vec<'):
            inner_type = type_str[4:-1].strip()
            inner_pw = self._normalize_type(inner_type)
            return f'array<{inner_pw}>'

        # Handle Option<...> types (unwrap to inner type)
        if type_str.startswith('Option<'):
            inner_type = type_str[7:-1].strip()
            return self._normalize_type(inner_type)

        type_str_lower = type_str.lower()

        # Map Rust types to PW types
        type_map = {
            'string': 'string',
            'str': 'string',
            '&str': 'string',
            'i32': 'int',
            'i64': 'int',
            'u32': 'int',
            'u64': 'int',
            'usize': 'int',
            'isize': 'int',
            'f32': 'float',
            'f64': 'float',
            'bool': 'bool',
            'hashmap': 'object',
            'btreemap': 'object',
            'value': 'object',  # serde_json::Value
            'vec': 'array',
            'array': 'array',
        }

        return type_map.get(type_str_lower, 'string')
