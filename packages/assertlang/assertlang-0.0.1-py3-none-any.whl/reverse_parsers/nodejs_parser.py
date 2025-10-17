"""
Node.js reverse parser: JavaScript code → PW DSL

Extracts agent definitions from Express.js/Fastify servers.
"""

import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Set

from .base_parser import BaseReverseParser, ExtractedAgent


class NodeJSReverseParser(BaseReverseParser):
    """Parse Node.js Express/Fastify servers → PW DSL."""

    # Pattern to match handler function names: handle_verb_name_v1 or handleVerbNameV1
    HANDLER_PATTERN = re.compile(r"(?:async\s+)?function\s+(handle[A-Z]\w+)\s*\(")

    # Pattern to match verb names in routing: "verb.name@v1"
    VERB_PATTERN = re.compile(r'["\']([a-z0-9_.]+@v\d+)["\']')

    # Pattern to match JSDoc params: @param {type} params.name - description
    JSDOC_PARAM_PATTERN = re.compile(r'@param\s+\{([^}]+)\}\s+params\.(\w+)\s*(?:-\s*(.+))?')

    # Pattern to match JSDoc returns: @returns {type} result.name - description
    JSDOC_RETURN_PATTERN = re.compile(r'@returns?\s+\{([^}]+)\}\s+(?:result\.)?(\w+)\s*(?:-\s*(.+))?')

    def parse_file(self, file_path: str) -> ExtractedAgent:
        """Parse JavaScript file and extract agent definition."""
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
            lang="nodejs",
            verbs=verbs,
            tools=tools,
            confidence_score=confidence,
            framework=framework,
            extraction_notes=notes
        )

    def detect_framework(self, source: str) -> str:
        """Detect Express vs Fastify vs other."""
        # Check imports
        if re.search(r"(?:import|require)\s*(?:\(['\"]express['\"]\)|express\s+from\s+['\"]express['\"])", source):
            return 'express'
        if re.search(r"(?:import|require)\s*(?:\(['\"]fastify['\"]\)|fastify\s+from\s+['\"]fastify['\"])", source):
            return 'fastify'

        # Check app creation
        if 'express()' in source:
            return 'express'
        if 'fastify()' in source:
            return 'fastify'

        return 'unknown'

    def extract_handlers(self, source: str) -> List[Dict[str, Any]]:
        """Extract handler functions matching handle* pattern."""
        handlers = []

        # Find all handler functions with their full context
        handler_matches = list(self.HANDLER_PATTERN.finditer(source))

        for match in handler_matches:
            handler_func_name = match.group(1)

            # Extract the verb name from the handler function name
            # handleEchoV1 -> echo@v1
            # handle_echo_v1 -> echo@v1
            verb_name = self._handler_name_to_verb(handler_func_name)

            # Skip if this is an internal handler
            if verb_name is None:
                continue

            # Extract JSDoc and function body
            func_start = match.start()

            # Look for JSDoc before the function (up to 500 chars back)
            jsdoc_search_start = max(0, func_start - 500)
            preceding_text = source[jsdoc_search_start:func_start]

            # Extract only the last JSDoc block (most recent /** ... */)
            jsdoc_match = re.search(r'/\*\*.*?\*/', preceding_text, re.DOTALL)
            jsdoc_text = jsdoc_match.group(0) if jsdoc_match else ""

            # Extract params and returns from JSDoc
            params = self._extract_params_from_jsdoc(jsdoc_text)
            returns = self._extract_returns_from_jsdoc(jsdoc_text)

            # Also extract from function body if JSDoc is incomplete
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
        """Extract port from app.listen() call."""
        # Look for app.listen(PORT, ...) or app.listen(8080, ...)
        patterns = [
            r'app\.listen\s*\(\s*(\d+)',  # Direct number: app.listen(8080)
            r'const\s+PORT\s*=\s*(\d+)',  # Const definition: const PORT = 8080
            r'const\s+port\s*=\s*(\d+)',  # Lowercase: const port = 8080
        ]

        for pattern in patterns:
            match = re.search(pattern, source)
            if match:
                return int(match.group(1))

        return 8000  # default

    def extract_tools(self, source: str) -> List[str]:
        """Extract tools from configuredTools array."""
        # Look for: const configuredTools = ['tool1', 'tool2']
        # or: app.locals.configuredTools = [...]
        patterns = [
            r'configuredTools\s*=\s*\[(.*?)\]',
            r'app\.locals\.configuredTools\s*=\s*\[(.*?)\]',
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
        """Extract agent name from Express app or comments."""
        # Look for: agent: 'agent-name' in /verbs endpoint
        match = re.search(r"agent:\s*['\"]([^'\"]+)['\"]", source)
        if match:
            return match.group(1)

        # Look for: serverInfo: { name: 'agent-name' }
        match = re.search(r"serverInfo:\s*\{\s*name:\s*['\"]([^'\"]+)['\"]", source)
        if match:
            return match.group(1)

        # Look for: MCP server for agent: agent-name
        match = re.search(r"MCP server for agent:\s*([^'\"]+)['\"]", source)
        if match:
            return match.group(1).strip()

        return "unknown-agent"

    def _handler_name_to_verb(self, handler_name: str) -> str:
        """
        Convert handler function name to verb name.

        Examples:
        - handleEchoV1 -> echo@v1
        - handleProcessDataV1 -> process.data@v1
        - handle_echo_v1 -> echo@v1

        Returns None if the handler should be skipped (e.g., error handlers).
        """
        # Remove 'handle' prefix
        name = re.sub(r'^handle', '', handler_name, flags=re.IGNORECASE)

        # Extract version (V1, V2, etc.)
        version_match = re.search(r'V(\d+)$', name)
        if version_match:
            version = f"v{version_match.group(1)}"
            name = name[:version_match.start()]
        else:
            version = "v1"

        # Convert camelCase to dot notation
        # EchoTest -> echo.test
        # ProcessData -> process.data
        name = re.sub(r'([a-z])([A-Z])', r'\1.\2', name).lower()

        # Handle snake_case: process_data -> process.data
        name = name.replace('_', '.')

        # Skip internal/utility handlers
        if name.lower() in ['error', 'health', 'ready']:
            return None

        return f"{name}@{version}"

    def _extract_params_from_jsdoc(self, jsdoc: str) -> List[Dict[str, str]]:
        """Extract parameters from JSDoc comment."""
        params = []

        for match in self.JSDOC_PARAM_PATTERN.finditer(jsdoc):
            param_type = match.group(1).strip()
            param_name = match.group(2).strip()

            params.append({
                'name': param_name,
                'type': self._normalize_type(param_type)
            })

        return params

    def _extract_returns_from_jsdoc(self, jsdoc: str) -> List[Dict[str, str]]:
        """Extract return fields from JSDoc comment."""
        returns = []

        for match in self.JSDOC_RETURN_PATTERN.finditer(jsdoc):
            return_type = match.group(1).strip()
            return_name = match.group(2).strip()

            # Skip generic 'Object' or 'result' without field name
            if return_name.lower() in ['object', 'result']:
                continue

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

        # Look for: if (!params.paramName)
        param_checks = re.finditer(r'if\s*\(\s*!params\.(\w+)\s*\)', func_body)

        for match in param_checks:
            param_name = match.group(1)
            if not any(p['name'] == param_name for p in params):
                params.append({
                    'name': param_name,
                    'type': 'string'  # default
                })

        return params

    def _extract_returns_from_body(self, func_body: str) -> List[Dict[str, str]]:
        """Extract return fields from function body return statements."""
        returns = []

        # Look for: return { field1: value1, field2: value2 }
        # But skip error returns: return { error: { ... } }
        # Need to match the main return object, not nested objects
        return_matches = re.finditer(r'return\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}', func_body, re.DOTALL)

        for match in return_matches:
            return_obj = match.group(1)

            # Skip if this is an error return
            if 'error:' in return_obj or re.search(r'error\s*:', return_obj):
                continue

            # Extract only top-level fields (not nested in arrays/objects)
            # Split by commas but be careful with nested structures
            lines = return_obj.split('\n')
            for line in lines:
                # Match field at the start of a line (ignoring indent)
                field_match = re.match(r'\s*(\w+)\s*:\s*([^,\n]+)', line)
                if field_match:
                    field_name = field_match.group(1)
                    field_value = field_match.group(2).strip()

                    # Skip error fields, metadata, and nested object fields
                    if field_name in ['error', 'jsonrpc', 'id', 'code', 'message', 'data']:
                        continue

                    # Skip if this looks like it's inside a nested structure
                    # (has more than standard indent)
                    if line.startswith('      '):  # More than 4 spaces = nested
                        continue

                    if not any(r['name'] == field_name for r in returns):
                        # Infer type from value
                        field_type = self._infer_type_from_value(field_value)
                        returns.append({
                            'name': field_name,
                            'type': field_type
                        })

        return returns

    def _infer_type_from_value(self, value: str) -> str:
        """Infer PW type from JavaScript value."""
        value = value.strip()

        # Boolean values
        if value in ['true', 'false']:
            return 'bool'

        # Numeric values
        if re.match(r'^-?\d+$', value):
            return 'int'
        if re.match(r'^-?\d+\.\d+$', value):
            return 'float'

        # Arrays
        if value.startswith('['):
            return 'array'

        # Objects
        if value.startswith('{'):
            return 'object'

        # String (default)
        return 'string'

    def _extract_verbs_from_routing(self, source: str) -> Dict[str, Set[str]]:
        """
        Extract verb names from routing logic in /mcp endpoint.

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
        """Normalize JavaScript type to PW type."""
        type_str = type_str.strip()

        # Handle Array<...> types
        if type_str.startswith('Array<') or type_str.startswith('array<'):
            inner_type = type_str[6:-1].strip()
            inner_pw = self._normalize_type(inner_type)
            return f'array<{inner_pw}>'

        # Handle Object/object
        if type_str.lower() in ['object', 'dict', 'record']:
            return 'object'

        type_str_lower = type_str.lower()

        # Map JavaScript types to PW types
        type_map = {
            'string': 'string',
            'number': 'int',  # Could be float, but int is more common
            'integer': 'int',
            'int': 'int',
            'boolean': 'bool',
            'bool': 'bool',
            'object': 'object',
            'array': 'array',
            'float': 'float',
            'any': 'object',
        }

        return type_map.get(type_str_lower, 'string')
