# Tool Contracts for Agents

**Validate agent tool calls with contracts - prevent invalid tool usage and ensure reliable multi-agent execution.**

---

## Problem

AI agents call tools with arbitrary inputs:
- LLM generates invalid arguments
- Type mismatches cause crashes
- Missing required parameters
- Out-of-range values
- No validation until runtime

**Bad approach:**
```python
# Python: Tool with no validation
@tool
def search_database(query: str, limit: int):
    # LLM might call with limit=-1 or limit=1000000
    # No validation = crashes or resource exhaustion
    results = db.query(query, limit=limit)
    return results
```

**Issues:**
- Tools crash on invalid inputs
- Resource exhaustion (limit=1000000)
- Silent failures
- Hard to debug LLM behavior

---

## Solution

Use contracts to validate tool calls:

```promptware
function search_database(query: String, limit: Int) -> Result<List<String>, String>
  requires:
    len(query) > 0
    len(query) <= 500
    limit > 0
    limit <= 100
  ensures:
    len(result) <= limit if result is Ok
  do
    # Query database
    let results = db_query(query, limit)
    return Ok(results)
  end
end
```

**Generated Python with embedded contracts:**
```python
def search_database(query: str, limit: int) -> Result[List[str], str]:
    # Contract enforces:
    # - query: non-empty, max 500 chars
    # - limit: 1-100 (prevents resource exhaustion)

    assert len(query) > 0, "Query cannot be empty"
    assert len(query) <= 500, "Query too long (max 500 chars)"
    assert limit > 0, "Limit must be positive"
    assert limit <= 100, "Limit too high (max 100)"

    results = db.query(query, limit=limit)

    assert len(results) <= limit, "Postcondition failed: too many results"

    return Ok(results)
```

---

## Basic Tool Patterns

### Simple Tool with Validation

```promptware
type SearchResult:
  title: String
  url: String
  snippet: String
end

function web_search(query: String, max_results: Int) -> Result<List<SearchResult>, String>
  requires:
    len(query) >= 3
    len(query) <= 200
    max_results > 0
    max_results <= 50
  ensures:
    len(result) <= max_results if result is Ok
  do
    # Perform web search
    let results = perform_search(query, max_results)
    return Ok(results)
  end
end
```

### Tool with Complex Validation

```promptware
type EmailRequest:
  recipient: String
  subject: String
  body: String
end

function send_email(request: EmailRequest) -> Result<Bool, String>
  requires:
    "@" in request.recipient
    len(request.recipient) <= 255
    len(request.subject) > 0
    len(request.subject) <= 200
    len(request.body) > 0
    len(request.body) <= 10000
  do
    # Send email
    let success = smtp_send(request.recipient, request.subject, request.body)

    if success:
      return Ok(true)
    else:
      return Err("Failed to send email")
    end
  end
end
```

---

## CrewAI Tool Integration

**Generate Contract:**
```bash
asl build tools.al --lang python -o tools_generated.py
```

**Wrap as CrewAI Tool:**
```python
# tools_crewai.py
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from tools_generated import search_database, Err

class SearchDatabaseInput(BaseModel):
    query: str = Field(description="Search query")
    limit: int = Field(description="Maximum results (1-100)", default=10)

class SearchDatabaseTool(BaseTool):
    name: str = "search_database"
    description: str = "Search database with validated inputs"
    args_schema: type[BaseModel] = SearchDatabaseInput

    def _run(self, query: str, limit: int) -> str:
        # Contract validates inputs
        result = search_database(query, limit)

        if isinstance(result, Err):
            return f"Error: {result.error}"

        return f"Found {len(result.value)} results: {result.value}"

# Usage in CrewAI agent
from crewai import Agent

agent = Agent(
    role="Research Assistant",
    goal="Find relevant information",
    tools=[SearchDatabaseTool()]
)
```

---

## LangChain Tool Integration

**LangChain Tool Wrapper:**
```python
# tools_langchain.py
from langchain.tools import BaseTool
from langchain.pydantic_v1 import BaseModel, Field
from tools_generated import web_search, Err

class WebSearchInput(BaseModel):
    query: str = Field(description="Search query")
    max_results: int = Field(description="Max results", default=10)

class WebSearchTool(BaseTool):
    name = "web_search"
    description = "Search the web with validated inputs"
    args_schema = WebSearchInput

    def _run(self, query: str, max_results: int = 10) -> str:
        # Contract validates inputs
        result = web_search(query, max_results)

        if isinstance(result, Err):
            return f"Search failed: {result.error}"

        results = result.value
        return f"Found {len(results)} results"

# Usage in LangChain
from langchain.agents import initialize_agent, AgentType
from langchain.llms import OpenAI

tools = [WebSearchTool()]
llm = OpenAI(temperature=0)

agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION
)

response = agent.run("Search for AI safety papers")
```

---

## LangGraph Tool Integration

```python
# tools_langgraph.py
from langgraph.prebuilt import ToolNode
from tools_generated import send_email, EmailRequest, Err

def send_email_tool(recipient: str, subject: str, body: str) -> dict:
    """LangGraph tool with contract validation."""

    request = EmailRequest(
        recipient=recipient,
        subject=subject,
        body=body
    )

    result = send_email(request)

    if isinstance(result, Err):
        return {
            "success": False,
            "error": result.error
        }

    return {
        "success": True,
        "message": f"Email sent to {recipient}"
    }

# Use in LangGraph workflow
from langgraph.graph import StateGraph

tools = [send_email_tool]
tool_node = ToolNode(tools)

workflow = StateGraph(state_schema=...)
workflow.add_node("tools", tool_node)
```

---

## Real-World Example: Database Tool

**Contract:**
```promptware
# database_tools.al
type QueryParams:
  table: String
  filters: Map<String, String>
  limit: Int
  offset: Int
end

type QueryResult:
  rows: List<Map<String, String>>
  total_count: Int
end

function query_table(params: QueryParams) -> Result<QueryResult, String>
  requires:
    len(params.table) > 0
    len(params.table) <= 100
    params.limit > 0
    params.limit <= 1000
    params.offset >= 0
  ensures:
    len(result.rows) <= params.limit if result is Ok
    result.total_count >= 0 if result is Ok
  do
    # Query database
    let rows = db_select(params.table, params.filters, params.limit, params.offset)
    let total = db_count(params.table, params.filters)

    return Ok(QueryResult(rows=rows, total_count=total))
  end
end
```

**CrewAI Integration:**
```python
# database_crewai.py
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Dict
from database_tools_generated import query_table, QueryParams, Err

class QueryTableInput(BaseModel):
    table: str = Field(description="Table name")
    filters: Dict[str, str] = Field(description="Filter conditions", default={})
    limit: int = Field(description="Max rows (1-1000)", default=100)
    offset: int = Field(description="Offset for pagination", default=0)

class QueryTableTool(BaseTool):
    name: str = "query_table"
    description: str = "Query database table with filters and pagination"
    args_schema: type[BaseModel] = QueryTableInput

    def _run(self, table: str, filters: Dict[str, str], limit: int, offset: int) -> str:
        params = QueryParams(
            table=table,
            filters=filters,
            limit=limit,
            offset=offset
        )

        result = query_table(params)

        if isinstance(result, Err):
            return f"Query failed: {result.error}"

        data = result.value
        return f"Retrieved {len(data.rows)} rows (total: {data.total_count})"

# Usage
from crewai import Agent

db_agent = Agent(
    role="Database Analyst",
    goal="Query and analyze database",
    tools=[QueryTableTool()]
)
```

---

## Testing Tool Contracts

```python
# test_tool_contracts.py
import pytest
from tools_generated import search_database, web_search, Err

def test_search_database_valid():
    result = search_database("AI safety", 10)
    assert isinstance(result, Ok)
    assert len(result.value) <= 10

def test_search_database_invalid_query():
    # Empty query violates contract
    with pytest.raises(AssertionError, match="Query cannot be empty"):
        search_database("", 10)

def test_search_database_invalid_limit():
    # Limit too high violates contract
    with pytest.raises(AssertionError, match="Limit too high"):
        search_database("query", 1000)

def test_web_search_query_too_short():
    with pytest.raises(AssertionError, match="len\\(query\\) >= 3"):
        web_search("AI", 10)

def test_web_search_query_too_long():
    long_query = "a" * 201
    with pytest.raises(AssertionError, match="len\\(query\\) <= 200"):
        web_search(long_query, 10)
```

---

## Common Pitfalls

### ❌ No Input Validation

```python
# Bad: Tool crashes on invalid inputs
@tool
def search(query: str, limit: int):
    # LLM might call with limit=-1
    return db.query(query, limit)  # Crashes!
```

### ✅ Contract Validation

```promptware
# Good: Contract enforces valid inputs
function search(query: String, limit: Int) -> Result<List<String>, String>
  requires:
    len(query) > 0
    limit > 0
    limit <= 100
  do
    return Ok(db_query(query, limit))
  end
end
```

### ❌ Missing Postcondition

```python
# Bad: Tool might return more results than limit
@tool
def search(query: str, limit: int):
    # No guarantee on result size
    return db.query(query)  # Might return 1000+ results!
```

### ✅ Postcondition Enforced

```promptware
# Good: Postcondition guarantees result size
function search(query: String, limit: Int) -> Result<List<String>, String>
  ensures:
    len(result) <= limit if result is Ok
  do
    let results = db_query(query, limit)
    return Ok(results)
  end
end
```

---

## Performance Considerations

### Disable Contracts in Production

```python
# Development: Full validation
import os
os.environ['PW_DISABLE_CONTRACTS'] = '0'

# Production: Skip contract checks
os.environ['PW_DISABLE_CONTRACTS'] = '1'

# Tool still returns Result<T,E> for error handling
result = search_database(query, limit)
```

---

## See Also

- [CrewAI Agent Contracts](crewai-agent-contracts.md) - CrewAI-specific patterns
- [Agent Coordination](agent-coordination.md) - Multi-agent workflows
- [Custom Validators](../validation/custom-validators.md) - Build validators
- [Range Checking](../validation/range-checking.md) - Numeric bounds

---

**Difficulty:** Intermediate
**Time:** 15 minutes
**Category:** Framework Integration
**Last Updated:** 2025-10-15
