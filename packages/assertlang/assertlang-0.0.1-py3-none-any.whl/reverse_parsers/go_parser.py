"""
Go reverse parser: Go code → PW DSL

Extracts agent definitions from Go net/http servers.
"""

import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Set

from .base_parser import BaseReverseParser, ExtractedAgent


class GoReverseParser(BaseReverseParser):
    """Parse Go net/http servers → PW DSL."""

    # Pattern to match handler function names: handleCreateOrderV1 or handle_create_order_v1
    HANDLER_PATTERN = re.compile(r'func\s+(handle[A-Z][a-zA-Z0-9]*V\d+)\s*\(')

    # Pattern to match verb names in routing: case "verb.name@v1":
    VERB_PATTERN = re.compile(r'case\s+"([a-z0-9_.]+@v\d+)":')

    # Pattern to match ConfiguredTools variable
    TOOLS_PATTERN = re.compile(r'(?:var\s+ConfiguredTools|configuredTools)\s*=\s*\[\]string\{([^}]+)\}')

    # Pattern to match tool schemas in MCP endpoint (from generated code)
    TOOL_LIST_PATTERN = re.compile(r'configuredTools\s*:=\s*\[\]string\{([^}]+)\}')

    def parse_file(self, file_path: str) -> ExtractedAgent:
        """Parse Go file and extract agent definition."""
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
            lang="go",
            verbs=verbs,
            tools=tools,
            confidence_score=confidence,
            framework=framework,
            extraction_notes=notes
        )

    def detect_framework(self, source: str) -> str:
        """Detect net/http vs other Go frameworks."""
        # Check imports
        if re.search(r'import\s+\(.*?"net/http"', source, re.DOTALL):
            return 'net/http'
        if '"net/http"' in source:
            return 'net/http'

        # Check for http.ListenAndServe
        if 'http.ListenAndServe' in source:
            return 'net/http'

        # Check for other frameworks
        if 'gin-gonic/gin' in source or 'gin.Engine' in source:
            return 'gin'
        if 'gorilla/mux' in source or 'mux.Router' in source:
            return 'gorilla/mux'

        return 'unknown'

    def extract_handlers(self, source: str) -> List[Dict[str, Any]]:
        """Extract handler functions matching handle* pattern."""
        handlers = []

        # Find all handler functions with their full context
        handler_matches = list(self.HANDLER_PATTERN.finditer(source))

        # If no PW-style handlers found, try generic http.HandleFunc patterns
        if not handler_matches:
            return self._extract_generic_http_handlers(source)

        for match in handler_matches:
            handler_func_name = match.group(1)

            # Extract the verb name from the handler function name
            # handleCreateOrderV1 -> create.order@v1
            # handleGreetV1 -> greet@v1
            verb_name = self._handler_name_to_verb(handler_func_name)

            # Skip if this is an internal handler
            if verb_name is None:
                continue

            # Extract function body and comments
            func_start = match.start()

            # Look for comments before the function (up to 500 chars back)
            comment_search_start = max(0, func_start - 500)
            preceding_text = source[comment_search_start:func_start]

            # Extract Go doc comments (lines starting with //)
            comment_lines = []
            for line in preceding_text.split('\n'):
                stripped = line.strip()
                if stripped.startswith('//'):
                    comment_lines.append(stripped[2:].strip())

            comments_text = '\n'.join(comment_lines)

            # Extract params and returns from comments
            params = self._extract_params_from_comments(comments_text)
            returns = self._extract_returns_from_comments(comments_text)

            # Also extract from function body if comments are incomplete
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
        """Extract port from http.ListenAndServe() call."""
        # Look for http.ListenAndServe(":8080", ...) or http.ListenAndServe(":"+port, ...)
        patterns = [
            r'http\.ListenAndServe\s*\(\s*":(\d+)"',  # Direct: ":8080"
            r'port\s*:=\s*"(\d+)"',  # Variable: port := "8080"
            r'port\s*:=\s*(\d+)',  # Variable: port := 8080
            r'Port:\s*(\d+)',  # Struct field: Port: 8080
            r'port\s*:=\s*(\d+)\s*\+\s*rand',  # Base port with random offset
        ]

        for pattern in patterns:
            match = re.search(pattern, source)
            if match:
                return int(match.group(1))

        return 8000  # default

    def extract_tools(self, source: str) -> List[str]:
        """Extract tools from ConfiguredTools variable or tool registry."""
        # Try to find ConfiguredTools or configuredTools array
        patterns = [
            self.TOOLS_PATTERN,
            self.TOOL_LIST_PATTERN,
            re.compile(r'executeTool.*?configuredTools\s*:=\s*\[\]string\{([^}]+)\}', re.DOTALL),
        ]

        for pattern in patterns:
            match = pattern.search(source)
            if match:
                tools_str = match.group(1)
                # Extract quoted strings
                tools = re.findall(r'"([^"]+)"', tools_str)
                return tools

        return []

    def _extract_agent_name(self, source: str) -> str:
        """Extract agent name from log statements or serverInfo."""
        # Look for: "name": "agent-name" in serverInfo
        match = re.search(r'"name":\s*"([^"]+)"', source)
        if match:
            return match.group(1)

        # Look for: MCP server for agent: agent-name
        match = re.search(r'MCP server for agent:\s+([^\\"]+)', source)
        if match:
            return match.group(1).strip()

        # Look for: log.Printf("MCP server for agent: agent-name")
        match = re.search(r'log\.Printf\([^,]*agent[^,]*:\s+([^\\"]+)', source)
        if match:
            return match.group(1).strip()

        # Look for generic server names in log messages
        # "Digital Commerce Platform", "E-commerce API", etc.
        log_patterns = [
            r'log\.Printf\("([^"]+?)(?:\s+starting|server)',
            r'log\.Println\("([^"]+?)(?:\s+starting|server)',
            r'fmt\.Printf\("([^"]+?)(?:\s+starting|server)',
        ]
        for pattern in log_patterns:
            match = re.search(pattern, source, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                # Convert to agent-friendly name
                name = name.lower().replace(' ', '-')
                return name

        return "unknown-agent"

    def _handler_name_to_verb(self, handler_name: str) -> Optional[str]:
        """
        Convert handler function name to verb name.

        Examples:
        - handleGreetV1 -> greet@v1
        - handleCreateOrderV1 -> create.order@v1
        - handleFetchDataV2 -> fetch.data@v2

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

        # Convert PascalCase to dot notation
        # CreateOrder -> create.order
        # FetchData -> fetch.data
        # Insert dots before capital letters (except the first)
        name = re.sub(r'([a-z])([A-Z])', r'\1.\2', name).lower()

        # Skip internal/utility handlers
        if name.lower() in ['error', 'health', 'ready', 'verbs', 'mcp']:
            return None

        return f"{name}@{version}"

    def _extract_params_from_comments(self, comments: str) -> List[Dict[str, str]]:
        """
        Extract parameters from Go doc comments.

        Format:
        // Params:
        //   - customer_id (string): Customer ID
        //   - amount (int): Order amount
        """
        params = []

        # Look for Params: section
        in_params = False
        for line in comments.split('\n'):
            line_lower = line.lower()
            if 'params:' in line_lower or 'parameters:' in line_lower:
                in_params = True
                continue
            elif 'returns:' in line_lower or 'return:' in line_lower:
                in_params = False
                break

            if in_params and '- ' in line:
                # Format: "- param_name (type): description" or "- param_name (type)"
                parts = line.strip().split('(')
                if len(parts) >= 2:
                    param_name = parts[0].replace('-', '').strip()
                    # Extract type between ( and )
                    type_part = parts[1].split(')')[0].strip()
                    param_type = type_part.split(':')[0].strip()
                    params.append({
                        'name': param_name,
                        'type': self._normalize_type(param_type)
                    })

        return params

    def _extract_returns_from_comments(self, comments: str) -> List[Dict[str, str]]:
        """
        Extract return fields from Go doc comments.

        Format:
        // Returns:
        //   - order_id (string): Created order ID
        //   - status (string): Order status
        """
        returns = []

        # Look for Returns: section
        in_returns = False
        for line in comments.split('\n'):
            line_lower = line.lower()
            if 'returns:' in line_lower or 'return:' in line_lower:
                in_returns = True
                continue
            elif in_returns and '- ' in line:
                # Format: "- return_name (type): description"
                parts = line.strip().split('(')
                if len(parts) >= 2:
                    return_name = parts[0].replace('-', '').strip()
                    type_part = parts[1].split(')')[0].strip()
                    return_type = type_part.split(':')[0].strip()
                    returns.append({
                        'name': return_name,
                        'type': self._normalize_type(return_type)
                    })
            elif in_returns and not line.strip().startswith('-'):
                # End of returns section
                break

        return returns

    def _extract_function_body(self, source: str, func_start: int) -> str:
        """Extract function body from source starting at func_start."""
        # Find the function signature end (after the closing paren and return type)
        # Pattern: func name(...) return_type {
        # We need to find the { that's after the ) and return type

        # First, find the opening paren of parameters
        paren_start = source.find('(', func_start)
        if paren_start == -1:
            return ""

        # Track parentheses to find matching closing paren
        depth = 0
        i = paren_start
        paren_end = -1

        while i < len(source):
            if source[i] == '(':
                depth += 1
            elif source[i] == ')':
                depth -= 1
                if depth == 0:
                    paren_end = i
                    break
            i += 1

        if paren_end == -1:
            return ""

        # Now find the opening brace after the closing paren
        # This should be the function body
        # But we need to skip over interface{} in the return type
        # Look for a { that's followed by a newline or is on a new line
        search_start = paren_end
        brace_start = -1

        while search_start < len(source):
            next_brace = source.find('{', search_start)
            if next_brace == -1:
                break

            # Check if this is part of interface{}
            # Look ahead for immediate closing brace
            if next_brace + 1 < len(source) and source[next_brace + 1] == '}':
                # This is interface{}, skip it
                search_start = next_brace + 2
                continue

            # Check if there's content or newline after the brace
            # Function body braces are usually followed by newline
            after_brace = source[next_brace + 1:next_brace + 10].strip()
            if after_brace and not after_brace.startswith('}'):
                # This looks like a function body
                brace_start = next_brace
                break

            search_start = next_brace + 1

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

        # Look for: if _, ok := params["param_name"].(string); !ok {
        # This pattern captures both param name and type assertion
        param_pattern = re.compile(r'params\["([^"]+)"\]\.\(([^)]+)\)')

        for match in param_pattern.finditer(func_body):
            param_name = match.group(1)
            go_type = match.group(2)

            if not any(p['name'] == param_name for p in params):
                param_type = self._normalize_type(go_type)
                params.append({
                    'name': param_name,
                    'type': param_type
                })

        # Also look for params without type assertion: params["param_name"]
        # But skip if already found with type assertion
        simple_pattern = re.compile(r'params\["([^"]+)"\]')
        for match in simple_pattern.finditer(func_body):
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

        # Find ALL return statements
        # We need to skip error returns and find the success return
        return_pattern = r'return\s+map\[string\]interface\{\}\{'

        # Find all return statement positions
        return_positions = [m.start() for m in re.finditer(return_pattern, func_body)]

        for return_pos in return_positions:
            # Extract the return map content
            # Find the actual opening brace of the map content
            # Pattern: return map[string]interface{}{  <- we want this last {

            # Find "interface{}" first, then the brace after it
            interface_pos = func_body.find('interface{}', return_pos)
            if interface_pos == -1:
                continue

            # Find the opening brace AFTER "interface{}"
            brace_start = func_body.find('{', interface_pos + len('interface{}'))
            if brace_start == -1:
                continue

            # Now find the matching closing brace
            depth = 0
            i = brace_start
            brace_end = -1

            while i < len(func_body):
                if func_body[i] == '{':
                    depth += 1
                elif func_body[i] == '}':
                    depth -= 1
                    if depth == 0:
                        brace_end = i
                        break
                i += 1

            if brace_end == -1:
                continue

            # Extract the content between braces
            return_obj = func_body[brace_start + 1:brace_end]

            # Skip if this return contains "error" field
            if '"error":' in return_obj or '"error" :' in return_obj:
                continue

            # Extract field names and values
            # Match: "field_name": value,
            field_matches = re.finditer(
                r'"([^"]+)":\s*([^,\n]+)',
                return_obj
            )

            for field_match in field_matches:
                field_name = field_match.group(1)
                field_value = field_match.group(2).strip().rstrip(',')

                # Skip metadata fields (but NOT message - it's a valid return field!)
                # Only skip jsonrpc/id which are JSON-RPC specific
                if field_name in ['jsonrpc', 'id']:
                    continue

                if not any(r['name'] == field_name for r in returns):
                    # Infer type from value
                    field_type = self._infer_type_from_value(field_value)
                    returns.append({
                        'name': field_name,
                        'type': field_type
                    })

            # We found a success return, stop here
            if returns:
                break

        return returns

    def _infer_type_from_value(self, value: str) -> str:
        """Infer PW type from Go value."""
        value = value.strip().rstrip(',')

        # Boolean values
        if value in ['true', 'false']:
            return 'bool'

        # Numeric values
        if re.match(r'^-?\d+$', value):
            return 'int'
        if re.match(r'^-?\d+\.\d+$', value):
            return 'float'

        # Arrays/slices
        if value.startswith('[') or value.startswith('[]'):
            return 'array'

        # Maps/structs
        if value.startswith('map[') or value.startswith('{'):
            return 'object'

        # String (default)
        return 'string'

    def _extract_verbs_from_routing(self, source: str) -> Dict[str, Set[str]]:
        """
        Extract verb names from routing logic in switch statement.

        Returns dict mapping verb names to set of fields mentioned in context.
        """
        verbs = {}

        # Look for verb patterns in case statements
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
        """Normalize Go type to PW type."""
        type_str = type_str.strip()

        # Handle []type arrays
        if type_str.startswith('[]'):
            inner_type = type_str[2:].strip()
            inner_pw = self._normalize_type(inner_type)
            return f'array<{inner_pw}>'

        # Handle map[string]... types
        if type_str.startswith('map['):
            return 'object'

        type_str_lower = type_str.lower()

        # Map Go types to PW types
        type_map = {
            'string': 'string',
            'int': 'int',
            'int32': 'int',
            'int64': 'int',
            'integer': 'int',
            'bool': 'bool',
            'boolean': 'bool',
            'float32': 'float',
            'float64': 'float',
            'float': 'float',
            'map': 'object',
            'interface{}': 'object',
            'interface': 'object',
            'any': 'object',
            'slice': 'array',
        }

        return type_map.get(type_str_lower, 'string')

    def _extract_generic_http_handlers(self, source: str) -> List[Dict[str, Any]]:
        """
        Extract handlers from generic http.HandleFunc() calls.
        Fallback for non-PW Go servers.
        """
        handlers = []

        # Pattern: http.HandleFunc("/path", handlerFunc)
        handlefunc_pattern = re.compile(r'http\.HandleFunc\s*\(\s*"([^"]+)"\s*,\s*(\w+)\s*\)')

        for match in handlefunc_pattern.finditer(source):
            path = match.group(1)
            func_name = match.group(2)

            # Convert path to verb name
            # "/products" -> get.products@v1
            # "/orders/status" -> get.orders.status@v1
            # "/customers/profile" -> get.customers.profile@v1

            # Remove leading/trailing slashes
            path = path.strip('/')

            # Skip health/system endpoints
            if path in ['health', 'ready', 'metrics']:
                continue

            # Convert path to dot notation
            verb_parts = path.replace('/', '.')

            # Determine HTTP method from function name or default to get
            method = 'get'
            func_lower = func_name.lower()
            if 'post' in func_lower or 'create' in func_lower or 'add' in func_lower:
                method = 'create'
            elif 'put' in func_lower or 'update' in func_lower:
                method = 'update'
            elif 'delete' in func_lower or 'remove' in func_lower:
                method = 'delete'
            elif 'get' in func_lower or 'fetch' in func_lower or 'list' in func_lower:
                method = 'get'

            # Build verb name - use path as-is for verbs
            verb_name = f"{verb_parts}@v1"

            # Try to extract params and returns from function body
            func_pattern = re.compile(rf'func\s+{func_name}\s*\([^)]*\)\s*\{{', re.DOTALL)
            func_match = func_pattern.search(source)

            params = []
            returns = []

            if func_match:
                func_start = func_match.start()
                func_body = self._extract_function_body(source, func_start)

                # Extract params from JSON decode patterns
                # json.NewDecoder(r.Body).Decode(&req)
                decode_pattern = re.compile(r'Decode\s*\(\s*&(\w+)\s*\)')
                for dec_match in decode_pattern.finditer(func_body):
                    struct_var = dec_match.group(1)
                    # Look for struct definition
                    struct_pattern = re.compile(rf'var\s+{struct_var}\s+struct\s*\{{([^}}]+)\}}', re.DOTALL)
                    struct_match = struct_pattern.search(func_body)
                    if struct_match:
                        struct_fields = struct_match.group(1)
                        # Extract fields: FieldName Type `json:"field_name"`
                        field_pattern = re.compile(r'(\w+)\s+(\w+(?:\[\]\w+)?)\s*`json:"([^"]+)"`')
                        for field_match in field_pattern.finditer(struct_fields):
                            field_name = field_match.group(3)  # JSON name
                            field_type = field_match.group(2)  # Go type
                            params.append({
                                'name': field_name,
                                'type': self._normalize_type(field_type)
                            })

                # Also check query parameters: r.URL.Query().Get("param")
                query_pattern = re.compile(r'Query\s*\(\s*\)\s*\.Get\s*\(\s*"([^"]+)"\s*\)')
                for q_match in query_pattern.finditer(func_body):
                    param_name = q_match.group(1)
                    params.append({
                        'name': param_name,
                        'type': 'string'
                    })

                # Extract returns from JSON encode patterns
                # json.NewEncoder(w).Encode(response)
                encode_pattern = re.compile(r'Encode\s*\(\s*(\w+)\s*\)')
                for enc_match in encode_pattern.finditer(func_body):
                    response_var = enc_match.group(1)
                    # Look for struct definition or type
                    resp_struct_pattern = re.compile(rf'{response_var}\s*:=.*?(\w+)\s*\{{', re.DOTALL)
                    resp_match = resp_struct_pattern.search(func_body)
                    if resp_match:
                        resp_type = resp_match.group(1)
                        # Try to find type definition
                        type_pattern = re.compile(rf'type\s+{resp_type}\s+struct\s*\{{([^}}]+)\}}', re.DOTALL)
                        type_match = type_pattern.search(source)
                        if type_match:
                            type_fields = type_match.group(1)
                            field_pattern = re.compile(r'(\w+)\s+(\w+(?:\[\]\w+)?)\s*`json:"([^"]+)"`')
                            for field_match in field_pattern.finditer(type_fields):
                                field_name = field_match.group(3)
                                field_type = field_match.group(2)
                                returns.append({
                                    'name': field_name,
                                    'type': self._normalize_type(field_type)
                                })

            handlers.append({
                'name': verb_name,
                'params': params,
                'returns': returns
            })

        return handlers
