"""
.NET/C# reverse parser: C# code → PW DSL

Extracts agent definitions from ASP.NET Core MCP servers.
"""

import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Set

from .base_parser import BaseReverseParser, ExtractedAgent


class DotNetReverseParser(BaseReverseParser):
    """Parse .NET/C# ASP.NET Core servers → PW DSL."""

    # Pattern to match handler method names: HandleVerbNameV1
    # Handles both: Dictionary<string, object> and Task<Dictionary<string, object>>
    HANDLER_PATTERN = re.compile(
        r'public\s+static\s+(?:async\s+)?(?:Task<)?Dictionary<string,\s*object>(?:>\s*)?\??'
        r'\s+Handle([A-Z]\w+)(V\d+)\s*\('
    )

    # Pattern to match verb names in tools/list: "verb.name@v1"
    VERB_PATTERN = re.compile(r'"name":\s*"([a-z0-9_.]+@v\d+)"')

    # Pattern to match XML doc comments
    XML_SUMMARY_PATTERN = re.compile(r'///\s*<summary>\s*(.*?)\s*///\s*</summary>', re.DOTALL)
    XML_PARAM_PATTERN = re.compile(r'///\s*<param\s+name="params\.(\w+)"\s*>\s*(.*?)\s*</param>')
    XML_RETURNS_PATTERN = re.compile(r'///\s*<returns>\s*(.*?)\s*///\s*</returns>', re.DOTALL)

    # Pattern to match configured tools
    TOOLS_ARRAY_PATTERN = re.compile(
        r'string\[\]\s+ConfiguredTools\s*=\s*(?:new\s+string\[\]\s*)?\{\s*([^}]+)\s*\}'
    )

    def parse_file(self, file_path: str) -> ExtractedAgent:
        """Parse C# file and extract agent definition."""
        with open(file_path, 'r') as f:
            source = f.read()

        # Extract components
        framework = self.detect_framework(source)
        agent_name = self._extract_agent_name(source)
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
            lang="dotnet",
            verbs=verbs,
            tools=tools,
            confidence_score=confidence,
            framework=framework,
            extraction_notes=notes
        )

    def detect_framework(self, source: str) -> str:
        """Detect ASP.NET Core framework."""
        # Check for ASP.NET Core using directives
        if 'using Microsoft.AspNetCore' in source:
            return 'aspnetcore'

        # Check for WebApplication
        if 'WebApplication.Create' in source or 'var app = WebApplication' in source:
            return 'aspnetcore'

        return 'unknown'

    def extract_handlers(self, source: str) -> List[Dict[str, Any]]:
        """Extract handler methods matching Handle*V* pattern."""
        handlers = []

        # Find all handler methods with their full context
        handler_matches = list(self.HANDLER_PATTERN.finditer(source))

        for match in handler_matches:
            handler_func_name = match.group(1)  # e.g., "Echo" or "FetchData"
            version = match.group(2).lower()  # e.g., "v1"

            # Extract the verb name from the handler function name
            # HandleEchoV1 -> echo@v1
            # HandleFetchDataV1 -> fetch.data@v1
            verb_name = self._handler_name_to_verb(handler_func_name, version)

            # Skip if this is an internal handler
            if verb_name is None:
                continue

            # Extract XML docs before the handler
            method_start = match.start()

            # Look for XML docs before the method (up to 1000 chars back)
            xml_search_start = max(0, method_start - 1000)
            preceding_text = source[xml_search_start:method_start]

            # Extract XML doc comment
            params = self._extract_params_from_xml(preceding_text)
            returns = self._extract_returns_from_xml(preceding_text)

            # Also extract from method body if XML docs are incomplete
            method_body = self._extract_method_body(source, method_start)
            if not params:
                params = self._extract_params_from_body(method_body)
            if not returns:
                returns = self._extract_returns_from_body(method_body)

            handler = {
                'name': verb_name,
                'params': params,
                'returns': returns
            }
            handlers.append(handler)

        return handlers

    def extract_port(self, source: str) -> int:
        """Extract port from app.Run() or builder configuration."""
        # Look for: var port = "5002"; followed by app.Run($"http://127.0.0.1:{port}")
        port_var_match = re.search(r'var\s+port\s*=\s*"(\d+)"', source)
        if port_var_match:
            return int(port_var_match.group(1))

        # Look for: app.Run("http://localhost:8080")
        match = re.search(r'app\.Run\s*\(\s*"http://[^:]+:(\d+)"\s*\)', source)
        if match:
            return int(match.group(1))

        # Look for: app.Run($"http://127.0.0.1:{port}")  - extract from variable
        match = re.search(r'app\.Run\s*\(\s*\$"http://[^:]+:\{(\w+)\}"', source)
        if match:
            port_var = match.group(1)
            # Find the variable definition
            var_match = re.search(rf'var\s+{port_var}\s*=\s*"(\d+)"', source)
            if var_match:
                return int(var_match.group(1))

        # Look for: builder.WebHost.UseUrls("http://localhost:8080")
        match = re.search(r'UseUrls\s*\(\s*"http://[^:]+:(\d+)"\s*\)', source)
        if match:
            return int(match.group(1))

        # Look for: const int PORT = 8080;
        match = re.search(r'(?:const|var)\s+(?:int\s+)?PORT\s*=\s*(\d+)', source, re.IGNORECASE)
        if match:
            return int(match.group(1))

        return 8000  # default

    def extract_tools(self, source: str) -> List[str]:
        """Extract tools from ConfiguredTools array."""
        # Pattern 1: var configuredTools = new[] { "tool1", "tool2" };
        match = re.search(r'var\s+configuredTools\s*=\s*new\[\]\s*\{\s*([^}]+)\s*\}', source)
        if match:
            tools_str = match.group(1)
            # Extract quoted strings
            tools = re.findall(r'"([^"]+)"', tools_str)
            return tools

        # Pattern 2: string[] ConfiguredTools = { "tool1", "tool2" }
        match = self.TOOLS_ARRAY_PATTERN.search(source)
        if match:
            tools_str = match.group(1)
            # Extract quoted strings
            tools = re.findall(r'"([^"]+)"', tools_str)
            return tools

        return []

    def _extract_agent_name(self, source: str) -> str:
        """Extract agent name from serverInfo or namespace."""
        # Look for: serverInfo = new { name = "agent-name", ... }
        match = re.search(r'serverInfo\s*=\s*new\s*\{\s*name\s*=\s*"([^"]+)"', source)
        if match:
            return match.group(1)

        # Look for namespace: UserServiceMcp
        match = re.search(r'namespace\s+(\w+)', source)
        if match:
            namespace = match.group(1)
            # Convert PascalCase to kebab-case
            agent_name = re.sub(r'([a-z])([A-Z])', r'\1-\2', namespace).lower()
            # Remove "Mcp" suffix
            agent_name = agent_name.replace('-mcp', '')
            return agent_name

        return "unknown-agent"

    def _handler_name_to_verb(self, handler_name: str, version: str) -> Optional[str]:
        """
        Convert handler method name to verb name.

        Examples:
        - HandleEchoV1 -> echo@v1
        - HandleFetchDataV1 -> fetch.data@v1
        - HandleProcessOrderV1 -> process.order@v1

        Returns None if the handler should be skipped (e.g., error handlers).
        """
        # Skip internal/utility handlers
        if handler_name.lower() in ['error', 'health', 'ready']:
            return None

        # Convert PascalCase to dot notation
        # EchoTest -> echo.test
        # FetchData -> fetch.data
        name = re.sub(r'([a-z])([A-Z])', r'\1.\2', handler_name).lower()

        return f"{name}@{version}"

    def _extract_params_from_xml(self, xml_text: str) -> List[Dict[str, str]]:
        """Extract parameters from XML doc comments."""
        params = []

        # Look for <param name="params.fieldName">description</param>
        for match in self.XML_PARAM_PATTERN.finditer(xml_text):
            param_name = match.group(1)
            param_desc = match.group(2).strip()

            # Try to extract type from description
            # Format: "(type) description" or "type - description"
            param_type = 'string'  # default

            # Pattern: (type) or {type}
            type_match = re.search(r'[({](\w+)[)}]', param_desc)
            if type_match:
                param_type = self._normalize_type(type_match.group(1))
            # Pattern: type - description
            elif ' - ' in param_desc:
                parts = param_desc.split(' - ', 1)
                if parts[0].strip() in ['string', 'int', 'bool', 'float', 'object', 'array']:
                    param_type = self._normalize_type(parts[0].strip())

            params.append({
                'name': param_name,
                'type': param_type
            })

        return params

    def _extract_returns_from_xml(self, xml_text: str) -> List[Dict[str, str]]:
        """Extract return fields from XML doc comments."""
        returns = []

        # Look for <returns> section with field descriptions
        match = self.XML_RETURNS_PATTERN.search(xml_text)
        if match:
            returns_text = match.group(1)

            # Parse individual return fields
            # Format: "- field_name (type): description" or "field_name (type)"
            for line in returns_text.split('\n'):
                line = line.strip()
                if not line or '///' in line:
                    continue

                # Match: - field_name (type)
                field_match = re.match(r'[-*]?\s*(\w+)\s*\(([^)]+)\)', line)
                if field_match:
                    field_name = field_match.group(1)
                    field_type = self._normalize_type(field_match.group(2).strip())
                    returns.append({
                        'name': field_name,
                        'type': field_type
                    })

        return returns

    def _extract_method_body(self, source: str, method_start: int) -> str:
        """Extract method body from source starting at method_start."""
        # Find the opening brace
        brace_start = source.find('{', method_start)
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

    def _extract_params_from_body(self, method_body: str) -> List[Dict[str, str]]:
        """Extract parameters from method body validation checks."""
        params = []

        # Look for: if (!parameters.ContainsKey("paramName"))
        param_checks = re.finditer(
            r'if\s*\(\s*!parameters\.ContainsKey\s*\(\s*"(\w+)"\s*\)\s*\)',
            method_body
        )

        for match in param_checks:
            param_name = match.group(1)
            if not any(p['name'] == param_name for p in params):
                params.append({
                    'name': param_name,
                    'type': 'string'  # default
                })

        return params

    def _extract_returns_from_body(self, method_body: str) -> List[Dict[str, str]]:
        """Extract return fields from method body return statements."""
        returns = []

        # Look for: return new Dictionary<string, object> { ["field"] = value }
        # or: ["field"] = value in a return statement
        return_section = None

        # Find the main return statement (not error returns)
        return_matches = re.finditer(
            r'return\s+new\s+Dictionary<string,\s*object>\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}',
            method_body,
            re.DOTALL
        )

        for match in return_matches:
            return_obj = match.group(1)

            # Skip if this is an error return
            if '["error"]' in return_obj or 'error' in return_obj[:50]:
                continue

            return_section = return_obj
            break

        if return_section:
            # Extract field assignments: ["field_name"] = value
            field_matches = re.finditer(r'\["(\w+)"\]\s*=\s*([^,\n]+)', return_section)

            for field_match in field_matches:
                field_name = field_match.group(1)
                field_value = field_match.group(2).strip()

                # Skip error and metadata fields
                if field_name in ['error', 'jsonrpc', 'id', 'code', 'message', 'data']:
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
        """Infer PW type from C# value."""
        value = value.strip()

        # Boolean values
        if value in ['true', 'false', 'True', 'False']:
            return 'bool'

        # Numeric values
        if re.match(r'^-?\d+$', value):
            return 'int'
        if re.match(r'^-?\d+\.\d+[fFdDmM]?$', value):
            return 'float'

        # Arrays/Lists
        if value.startswith('new List') or value.startswith('new []') or value.startswith('['):
            return 'array'

        # Objects/Dictionaries
        if value.startswith('new Dictionary') or value.startswith('new {'):
            return 'object'

        # String (default)
        return 'string'

    def _extract_verbs_from_routing(self, source: str) -> Dict[str, Set[str]]:
        """
        Extract verb names from routing logic in tools/list.

        Returns dict mapping verb names to set of fields mentioned in context.
        """
        verbs = {}

        # Look for verb patterns in string literals (in tools/list response)
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
        """Normalize C# type to PW type."""
        type_str = type_str.strip()

        # Handle List<...> and array types
        if type_str.startswith('List<') or type_str.startswith('list<'):
            inner_type = type_str[5:-1].strip()
            inner_pw = self._normalize_type(inner_type)
            return f'array<{inner_pw}>'

        if type_str.endswith('[]'):
            inner_type = type_str[:-2].strip()
            inner_pw = self._normalize_type(inner_type)
            return f'array<{inner_pw}>'

        # Handle Dictionary/dict
        if type_str.startswith('Dictionary') or type_str.startswith('dict'):
            return 'object'

        type_str_lower = type_str.lower()

        # Map C# types to PW types
        type_map = {
            'string': 'string',
            'int': 'int',
            'int32': 'int',
            'int64': 'int',
            'long': 'int',
            'bool': 'bool',
            'boolean': 'bool',
            'double': 'float',
            'float': 'float',
            'decimal': 'float',
            'object': 'object',
            'dictionary': 'object',
            'list': 'array',
            'array': 'array',
            'any': 'object',
        }

        return type_map.get(type_str_lower, 'string')
