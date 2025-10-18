# Dual-Mode Agent Architecture

**Date:** 2025-09-30
**Status:** Design Phase
**Goal:** Support both IDE-integrated and standalone agent execution

---

## Problem Statement

Agents need to work in two environments:

1. **IDE-Integrated** (Cursor, Windsurf, Copilot)
   - IDE already has AI built-in
   - Agent should provide data/capabilities for IDE's AI to use
   - No API key needed from user
   - Cost controlled by IDE subscription

2. **Standalone** (CLI, API, custom integrations)
   - Agent has its own AI processing
   - Requires API keys (ANTHROPIC_API_KEY, etc.)
   - Full autonomy - returns processed results
   - User pays for API calls directly

---

## Current Implementation Issues

### What Works ✅
- MCP stdio protocol implementation
- Tool registration in Cursor
- Mock data execution
- Connection to 10 agents

### What's Missing ❌
- Tool execution (agents reference tools but don't execute them)
- Real data fetching (returns mock strings instead of actual data)
- Dual-mode logic (only attempts AI mode, falls back to useless mocks)
- Tool → Agent integration

---

## Architecture Design

### Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│ IDE (Cursor/Windsurf) or CLI                                 │
│   - User request: "Review this code"                         │
│   - Built-in AI (optional): Claude/GPT                       │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      │ MCP JSON-RPC (stdio)
                      │
┌─────────────────────▼───────────────────────────────────────┐
│ MCP Stdio Server (mcp_stdio_server.py)                       │
│   - Handles: initialize, tools/list, tools/call             │
│   - Routes tool calls to verb executor                       │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      │ verb_name + arguments
                      │
┌─────────────────────▼───────────────────────────────────────┐
│ Verb Executor (NEW)                                          │
│   1. Load agent definition (.al file)                        │
│   2. Execute referenced tools                                │
│   3. Collect real data                                       │
│   4. Decide execution mode                                   │
└─────────────────────┬───────────────────────────────────────┘
                      │
          ┌───────────┴───────────┐
          │                       │
          ▼                       ▼
┌─────────────────┐     ┌─────────────────┐
│ Tool Executor   │     │ Tool Executor   │
│ (toolbuilder/)  │     │ (toolbuilder/)  │
│                 │     │                 │
│ github_fetch_pr │     │ security_scanner│
│ file_reader     │     │ code_analyzer   │
│ http_client     │     │ json_validator  │
└────────┬────────┘     └────────┬────────┘
         │                       │
         └───────────┬───────────┘
                     │
         ┌───────────▼───────────┐
         │   Real Data Results   │
         │ {pr_data, scan_results}│
         └───────────┬───────────┘
                     │
         ┌───────────▼───────────────────────┐
         │  Mode Decision                    │
         │                                   │
         │  IF ANTHROPIC_API_KEY set:        │
         │    → Process with agent's LLM     │
         │    → Return AI analysis           │
         │  ELSE:                            │
         │    → Return raw data + metadata   │
         │    → IDE's AI processes it        │
         └───────────┬───────────────────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │   Return to Caller    │
         └───────────────────────┘
```

---

## Execution Modes

### Mode 1: IDE-Integrated (No API Key)

**Trigger:** `ANTHROPIC_API_KEY` not set

**Flow:**
```python
# User in Cursor: "Review this PR: facebook/react#123"

1. Cursor AI calls: review.analyze@v1(repo="facebook/react", pr_number=123)

2. MCP Server executes verb:
   a. Load agent tools: [github_fetch_pr, security_scanner, code_analyzer]
   b. Execute github_fetch_pr:
      - Calls GitHub API
      - Returns: {files: [...], diff: "...", commits: [...]}
   c. Execute security_scanner:
      - Scans code for vulnerabilities
      - Returns: {issues: [{severity: "high", ...}]}
   d. Execute code_analyzer:
      - Parses code structure
      - Returns: {complexity: 12, test_coverage: 0.78}

3. MCP Server returns structured data:
   {
     "raw_data": {
       "pr_info": {...},
       "security_scan": {...},
       "code_analysis": {...}
     },
     "summary": "Fetched PR with 15 files, found 3 security issues",
     "metadata": {
       "tools_executed": ["github_fetch_pr", "security_scanner", "code_analyzer"],
       "execution_time_ms": 1250
     }
   }

4. Cursor's AI processes the data:
   - Reads raw_data
   - Applies its own analysis
   - Explains to user: "I found 3 security issues..."
```

**Benefits:**
- No API key needed from user
- Fast execution (no extra LLM call)
- Cost included in IDE subscription
- Agent provides specialized data fetching/scanning

**Limitations:**
- Generic AI analysis (not specialized by agent's prompts)
- IDE's AI may not be as good at specific domain

---

### Mode 2: Standalone (With API Key)

**Trigger:** `ANTHROPIC_API_KEY` is set

**Flow:**
```python
# CLI or API: promptware run review.analyze@v1 --repo facebook/react --pr-number 123

1. Same tool execution as Mode 1:
   - github_fetch_pr → real PR data
   - security_scanner → scan results
   - code_analyzer → code metrics

2. Agent processes with its own LLM:
   a. Load agent's prompt_template:
      "You are an expert code reviewer with deep knowledge of..."
   b. Load verb's prompt_template:
      "Analyze the following PR. Look for security vulnerabilities..."
   c. Combine with tool results:
      system: agent.prompt_template
      user: verb.prompt_template + tool_results
   d. Call LLM (Claude via API key):
      response = llm.invoke(messages)

3. Agent returns AI-processed analysis:
   {
     "summary": "This PR introduces a critical SQL injection vulnerability in user.py:45",
     "issues": [
       {
         "severity": "critical",
         "file": "user.py",
         "line": 45,
         "description": "SQL injection via unsanitized input",
         "fix": "Use parameterized queries"
       }
     ],
     "suggestions": [...],
     "metadata": {
       "tools_executed": ["github_fetch_pr", "security_scanner"],
       "llm_model": "claude-3-5-sonnet-20241022",
       "execution_time_ms": 3400
     }
   }

4. Return to caller:
   - CLI: Print formatted analysis
   - API: Return JSON response
```

**Benefits:**
- Specialized AI analysis using agent's domain expertise
- Custom prompts tuned for specific tasks
- Full autonomy - can be used outside IDE

**Limitations:**
- Requires API key
- User pays for API calls
- Slower (extra LLM call)

---

## Implementation Plan

### Phase 1: Tool Executor Integration

**File:** `language/tool_executor.py` (NEW)

```python
class ToolExecutor:
    """Executes tools referenced by agents."""

    def __init__(self, agent_tools: List[str]):
        """Load tool implementations from tools/ directory."""
        self.tools = {}
        for tool_name in agent_tools:
            tool_impl = self._load_tool(tool_name)
            if tool_impl:
                self.tools[tool_name] = tool_impl

    def _load_tool(self, tool_name: str):
        """Dynamically import tool from tools/ directory."""
        # Import from tools/{tool_name}/tool.py
        # Or use toolbuilder to load schema + implementation
        pass

    def execute_tools(self, arguments: Dict) -> Dict:
        """Execute all agent's tools and return results."""
        results = {}
        for tool_name, tool in self.tools.items():
            try:
                result = tool.execute(arguments)
                results[tool_name] = result
            except Exception as e:
                results[tool_name] = {"error": str(e)}
        return results
```

**Integration points:**
- Import existing tool implementations from `tools/`
- Use `toolbuilder/` infrastructure
- Handle tool dependencies (tool A needs output of tool B)

---

### Phase 2: Update MCP Stdio Server

**File:** `language/mcp_stdio_server.py` (MODIFY)

**Changes to `_execute_verb()`:**

```python
def _execute_verb(self, verb_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Execute verb with real tool execution."""

    # Find verb definition
    verb_def = self._find_verb(verb_name)
    if not verb_def:
        return {"error": f"Verb not found: {verb_name}"}

    expose = verb_def.get("_expose")
    agent = self.agent_info.get("agent")

    # STEP 1: Execute tools to get real data
    tool_results = {}
    if agent and agent.tools:
        executor = ToolExecutor(agent.tools)
        tool_results = executor.execute_tools(arguments)

    # STEP 2: Decide execution mode
    has_api_key = bool(os.environ.get("ANTHROPIC_API_KEY"))
    has_prompts = bool(expose and expose.prompt_template)

    if has_api_key and has_prompts:
        # Mode 2: Standalone AI processing
        return self._execute_ai_mode(expose, agent, arguments, tool_results)
    else:
        # Mode 1: IDE-integrated (return raw data)
        return self._execute_ide_mode(expose, arguments, tool_results)
```

**New method: `_execute_ide_mode()`**

```python
def _execute_ide_mode(self, expose, arguments: Dict, tool_results: Dict) -> Dict:
    """Return structured data for IDE's AI to process."""

    # Build response matching the verb's return schema
    response = {
        "raw_data": tool_results,
        "input_params": arguments,
        "metadata": {
            "mode": "ide_integrated",
            "tools_executed": list(tool_results.keys()),
            "timestamp": datetime.now().isoformat()
        }
    }

    # Add human-readable summary
    if tool_results:
        response["summary"] = self._generate_summary(tool_results)

    # Match return schema if specified
    if expose and expose.returns:
        for ret_field in expose.returns:
            field_name = ret_field["name"]
            field_type = ret_field["type"]

            # Try to extract from tool_results
            if field_name in tool_results:
                response[field_name] = tool_results[field_name]
            elif field_name not in response:
                # Provide intelligent default based on tool results
                response[field_name] = self._smart_default(field_type, tool_results)

    return response
```

**Update: `_execute_ai_mode()` (formerly `_execute_ai_verb()`)**

```python
def _execute_ai_mode(self, expose, agent, arguments: Dict, tool_results: Dict) -> Dict:
    """Execute with agent's own LLM processing."""

    # Build enhanced prompt with tool results
    tool_summary = json.dumps(tool_results, indent=2)

    user_prompt = f"""{expose.prompt_template}

Input parameters:
{json.dumps(arguments, indent=2)}

Tool execution results:
{tool_summary}

Analyze the above data and provide your response in the required format.
"""

    # Rest of existing AI execution logic...
    # (Keep current LLM invocation code)
```

---

### Phase 3: Tool Discovery & Loading

**Challenge:** Agent .al files reference tools by name (e.g., `github_fetch_pr`), but we need to find and load the actual implementation.

**Solution:** Tool registry

**File:** `tools/registry.py` (NEW)

```python
"""Tool registry for dynamic tool loading."""

import os
import importlib
from pathlib import Path
from typing import Dict, Optional, Any

class ToolRegistry:
    """Central registry for all available tools."""

    def __init__(self):
        self.tools_dir = Path(__file__).parent
        self._cache = {}

    def get_tool(self, tool_name: str) -> Optional[Any]:
        """Load tool implementation by name."""

        if tool_name in self._cache:
            return self._cache[tool_name]

        # Try to find tool in tools/ subdirectories
        tool_paths = [
            self.tools_dir / tool_name / "tool.py",
            self.tools_dir / tool_name / f"{tool_name}.py",
            self.tools_dir / tool_name.replace("_", "-") / "tool.py"
        ]

        for tool_path in tool_paths:
            if tool_path.exists():
                tool_impl = self._load_from_file(tool_path)
                if tool_impl:
                    self._cache[tool_name] = tool_impl
                    return tool_impl

        # Tool not found
        return None

    def _load_from_file(self, tool_path: Path) -> Optional[Any]:
        """Load tool from Python file."""
        # Import module dynamically
        # Return tool class or function
        pass

    def list_available_tools(self) -> list[str]:
        """List all available tools."""
        tools = []
        for item in self.tools_dir.iterdir():
            if item.is_dir() and not item.name.startswith("_"):
                tools.append(item.name)
        return tools
```

---

### Phase 4: Response Format Standardization

Both modes should return consistent structure for MCP protocol:

```json
{
  "content": [
    {
      "type": "text",
      "text": "JSON string with actual results"
    }
  ],
  "metadata": {
    "mode": "ide_integrated" | "standalone_ai",
    "tools_executed": ["tool1", "tool2"],
    "execution_time_ms": 1250,
    "llm_model": "claude-3-5-sonnet" (if applicable)
  }
}
```

**IDE mode example:**
```json
{
  "content": [{
    "type": "text",
    "text": "{
      \"summary\": \"Fetched PR #123 with 15 files\",
      \"raw_data\": {
        \"pr_info\": {...},
        \"files_changed\": 15,
        \"additions\": 234,
        \"deletions\": 45
      },
      \"issues\": [...],
      \"suggestions\": [...]
    }"
  }]
}
```

**Standalone mode example:**
```json
{
  "content": [{
    "type": "text",
    "text": "{
      \"summary\": \"Found 3 critical security issues\",
      \"issues\": [
        {
          \"severity\": \"critical\",
          \"file\": \"user.py\",
          \"line\": 45,
          \"description\": \"SQL injection\",
          \"fix\": \"Use parameterized queries\"
        }
      ],
      \"suggestions\": [...]
    }"
  }]
}
```

---

## Testing Strategy

### Test IDE Mode (No API Key)

```bash
# Unset API key
unset ANTHROPIC_API_KEY

# Test in Cursor
1. Call review.analyze@v1 with real repo
2. Verify tools execute (GitHub API called)
3. Check response has raw_data
4. Verify Cursor's AI can interpret results
```

### Test Standalone Mode (With API Key)

```bash
# Set API key
export ANTHROPIC_API_KEY=sk-ant-...

# Test in Cursor or CLI
1. Call review.analyze@v1 with real repo
2. Verify tools execute
3. Verify agent's LLM called
4. Check response has AI analysis
5. Compare quality vs IDE mode
```

### Test Tool Execution

```bash
# Test individual tools
python3 -c "
from tools.registry import ToolRegistry
reg = ToolRegistry()
tool = reg.get_tool('github_fetch_pr')
result = tool.execute({'repo': 'facebook/react', 'pr_number': 123})
print(result)
"
```

---

## Migration Path

### Current State
- ✅ MCP protocol working
- ✅ Tool registration working
- ✅ Mock data execution
- ❌ No tool execution
- ❌ No real data
- ❌ No dual-mode logic

### Step 1: Add Tool Executor (Week 1)
- Create `tools/registry.py`
- Create `language/tool_executor.py`
- Test tool loading independently
- Don't integrate with MCP yet

### Step 2: Integrate Tool Execution (Week 1-2)
- Modify `mcp_stdio_server.py`
- Add tool execution to `_execute_verb()`
- Test IDE mode (return raw data)
- Verify with 3-5 agents

### Step 3: Implement Dual-Mode (Week 2)
- Add mode detection logic
- Implement `_execute_ide_mode()`
- Update `_execute_ai_mode()` with tool results
- Test both modes with API key on/off

### Step 4: Production Hardening (Week 3)
- Error handling for tool failures
- Timeout handling
- Tool dependency resolution
- Caching of tool results
- Performance optimization

### Step 5: Documentation (Week 3-4)
- Update docs/mcp-testing-plan.md
- Create user guide for both modes
- Add examples for each agent
- Document tool requirements (GitHub tokens, etc.)

---

## Open Questions

1. **Tool authentication:** How do tools get credentials (GitHub tokens, API keys)?
   - Option A: Pass through from user
   - Option B: Agent-level config
   - Option C: Environment variables per tool

2. **Tool caching:** Should tool results be cached?
   - github_fetch_pr could cache PR data for 5 minutes
   - security_scanner could cache scans by file hash

3. **Tool dependencies:** If tool B needs output of tool A?
   - Option A: Execute in dependency order
   - Option B: Let tools call each other
   - Option C: User defines execution graph

4. **IDE mode quality:** Is raw data + IDE's AI good enough?
   - May need to enhance raw data with more context
   - Consider hybrid: light processing + raw data

5. **Cost optimization:** Standalone mode calls both tools AND LLM
   - Could be expensive for large PRs
   - Consider streaming responses
   - Add budget limits

---

## Success Metrics

**IDE Mode:**
- [ ] All agent tools execute successfully
- [ ] Real data returned (not mocks)
- [ ] Cursor's AI can interpret results
- [ ] Response time <3s (without LLM call)
- [ ] Works without any API keys

**Standalone Mode:**
- [ ] Agent's LLM processes tool results
- [ ] Analysis quality better than generic AI
- [ ] Response time <10s (with LLM call)
- [ ] Cost reasonable (<$0.10 per analysis)

**Both Modes:**
- [ ] No crashes or errors
- [ ] Clear mode indication in responses
- [ ] Consistent JSON schema
- [ ] Good error messages
- [ ] Documentation complete

---

## Next Steps

1. Review this design doc
2. Decide on tool authentication strategy
3. Implement Phase 1 (Tool Executor)
4. Test with 2-3 simple tools first
5. Integrate with MCP server
6. Test end-to-end with Cursor

---

**Questions for review:**
- Is the dual-mode logic clear?
- Should IDE mode do any processing, or just return raw data?
- How should tool authentication work?
- What's the priority: IDE mode or standalone mode first?
