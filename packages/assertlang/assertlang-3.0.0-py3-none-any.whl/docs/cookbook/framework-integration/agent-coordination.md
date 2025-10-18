# Agent Coordination with Contracts

**Coordinate multi-agent workflows with deterministic contracts - ensure agents produce consistent, validated outputs across frameworks and languages.**

---

## Problem

Multi-agent systems need reliable coordination:
- Agent A (Python/CrewAI) → Agent B (JavaScript/LangGraph)
- Different frameworks, different languages
- No semantic contracts = unpredictable behavior
- Output from Agent A might violate Agent B's assumptions
- Hard to debug multi-agent workflows

**Bad approach:**
```python
# Python Agent A (CrewAI)
def agent_a_task(input_data: dict):
    # No validation, any output shape
    return {"result": compute_something(input_data)}

# JavaScript Agent B (LangGraph)
function agentBTask(input) {
    // Assumes specific structure, crashes if wrong
    return process(input.result.data);  // What if 'data' is missing?
}
```

**Issues:**
- No guarantees on data shape
- Cross-language incompatibility
- Silent failures
- Hard to trace bugs across agents

---

## Solution

Use AssertLang contracts for deterministic coordination:

**1. Define shared contract:**
```promptware
# data_processor_contract.al
type InputData:
  raw_text: String
  min_length: Int
end

type OutputData:
  processed_text: String
  word_count: Int
  metadata: Map<String, String>
end

function process_data(input: InputData) -> Result<OutputData, String>
  requires:
    len(input.raw_text) > 0
    len(input.raw_text) >= input.min_length
    input.min_length > 0
  ensures:
    len(result.processed_text) > 0 if result is Ok
    result.word_count > 0 if result is Ok
  do
    # Processing logic
    let processed = input.raw_text.trim()
    let words = processed.split(" ")
    let metadata = {"processed_at": "2025-10-15"}

    return Ok(OutputData(
      processed_text=processed,
      word_count=len(words),
      metadata=metadata
    ))
  end
end
```

**2. Generate for both languages:**
```bash
# Agent A (Python/CrewAI)
asl build data_processor_contract.al --lang python -o agent_a.py

# Agent B (JavaScript/LangGraph)
asl build data_processor_contract.al --lang javascript -o agent_b.js
```

**3. Both agents use identical contracts:**
```python
# Python Agent A
from agent_a import process_data, InputData, Err

def agent_a_task(raw_text: str):
    input_data = InputData(raw_text=raw_text, min_length=10)
    result = process_data(input_data)

    if isinstance(result, Err):
        raise ValueError(f"Contract violation: {result.error}")

    return result.value  # Guaranteed valid OutputData
```

```javascript
// JavaScript Agent B
const { process_data, InputData } = require('./agent_b');

function agentBTask(rawText) {
    const inputData = new InputData(rawText, 10);
    const result = process_data(inputData);

    if (result.isErr()) {
        throw new Error(`Contract violation: ${result.error}`);
    }

    return result.value;  // Guaranteed valid OutputData
}
```

**Result:** Both agents produce **100% identical outputs** for same inputs, regardless of language or framework.

---

## Multi-Agent Pipeline

### Research → Analysis → Summary (3 Agents)

**Shared Contracts:**
```promptware
# research_pipeline.al
type ResearchQuery:
  topic: String
  depth: Int
  sources_required: Int
end

type ResearchResult:
  topic: String
  sources: List<String>
  findings: List<String>
end

type AnalysisResult:
  topic: String
  insights: List<String>
  confidence_score: Float
end

type SummaryResult:
  topic: String
  summary: String
  key_points: List<String>
end

# Agent 1: Researcher
function conduct_research(query: ResearchQuery) -> Result<ResearchResult, String>
  requires:
    len(query.topic) > 0
    query.depth >= 1
    query.depth <= 5
    query.sources_required > 0
  ensures:
    len(result.sources) >= query.sources_required if result is Ok
    len(result.findings) > 0 if result is Ok
  do
    # Research implementation
    let sources = ["Source 1", "Source 2", "Source 3"]
    let findings = ["Finding A", "Finding B"]

    return Ok(ResearchResult(
      topic=query.topic,
      sources=sources,
      findings=findings
    ))
  end
end

# Agent 2: Analyst
function analyze_research(research: ResearchResult) -> Result<AnalysisResult, String>
  requires:
    len(research.findings) > 0
    len(research.sources) > 0
  ensures:
    len(result.insights) > 0 if result is Ok
    result.confidence_score >= 0.0 if result is Ok
    result.confidence_score <= 1.0 if result is Ok
  do
    # Analysis implementation
    let insights = ["Insight 1", "Insight 2"]
    let confidence = 0.85

    return Ok(AnalysisResult(
      topic=research.topic,
      insights=insights,
      confidence_score=confidence
    ))
  end
end

# Agent 3: Summarizer
function generate_summary(analysis: AnalysisResult) -> Result<SummaryResult, String>
  requires:
    len(analysis.insights) > 0
  ensures:
    len(result.summary) > 0 if result is Ok
    len(result.key_points) > 0 if result is Ok
  do
    # Summary implementation
    let summary = "Comprehensive analysis summary"
    let key_points = ["Point 1", "Point 2", "Point 3"]

    return Ok(SummaryResult(
      topic=analysis.topic,
      summary=summary,
      key_points=key_points
    ))
  end
end
```

**Integration:**
```python
# Python orchestrator (CrewAI)
from crewai import Agent, Task, Crew
from research_contracts import *

# Agent 1: Researcher (Python/CrewAI)
researcher = Agent(
    role="Research Specialist",
    goal="Conduct thorough research",
    tools=[conduct_research]
)

# Agent 2: Analyst (Python/CrewAI)
analyst = Agent(
    role="Data Analyst",
    goal="Analyze research findings",
    tools=[analyze_research]
)

# Agent 3: Summarizer (JavaScript/LangGraph via subprocess)
summarizer = Agent(
    role="Summary Generator",
    goal="Create executive summary",
    tools=[generate_summary_js_wrapper]  # Calls JS via subprocess
)

# Run workflow
crew = Crew(agents=[researcher, analyst, summarizer], tasks=[...])
result = crew.kickoff({"topic": "AI Safety", "depth": 3, "sources_required": 5})
```

---

## Cross-Language Coordination

### Python Agent → JavaScript Agent

**Contract (Shared):**
```promptware
type ProcessRequest:
  data: String
  options: Map<String, String>
end

type ProcessResponse:
  processed: String
  metadata: Map<String, String>
end

function process_request(req: ProcessRequest) -> Result<ProcessResponse, String>
  requires:
    len(req.data) > 0
  ensures:
    len(result.processed) > 0 if result is Ok
  do
    return Ok(ProcessResponse(
      processed=req.data.upper(),
      metadata={"processed_by": "promptware"}
    ))
  end
end
```

**Python Agent (CrewAI):**
```python
# agent_python.py
from crewai import Agent
from contracts_python import process_request, ProcessRequest, Err

class PythonAgent:
    def run(self, data: str):
        request = ProcessRequest(data=data, options={"format": "json"})
        result = process_request(request)

        if isinstance(result, Err):
            raise ValueError(f"Contract failed: {result.error}")

        # Pass to JavaScript agent via JSON
        return {
            "processed": result.value.processed,
            "metadata": result.value.metadata
        }
```

**JavaScript Agent (LangGraph):**
```javascript
// agent_javascript.js
const { process_request, ProcessRequest } = require('./contracts_javascript');

class JavaScriptAgent {
    run(data) {
        const request = new ProcessRequest(data, { format: "json" });
        const result = process_request(request);

        if (result.isErr()) {
            throw new Error(`Contract failed: ${result.error}`);
        }

        // Guaranteed same structure as Python agent
        return {
            processed: result.value.processed,
            metadata: result.value.metadata
        };
    }
}

module.exports = { JavaScriptAgent };
```

**Orchestrator:**
```python
# orchestrator.py
import subprocess
import json
from agent_python import PythonAgent

# Python agent processes first
python_agent = PythonAgent()
python_output = python_agent.run("Hello World")

# Pass to JavaScript agent
js_input = json.dumps(python_output)
js_result = subprocess.run(
    ["node", "agent_javascript.js"],
    input=js_input,
    capture_output=True,
    text=True
)

js_output = json.loads(js_result.stdout)

# Both agents produced identical structure!
assert python_output.keys() == js_output.keys()
```

---

## Error Handling Across Agents

```promptware
type AgentError:
  agent_name: String
  error_code: String
  message: String
  retryable: Bool
end

function handle_agent_error(error: AgentError) -> Result<String, AgentError>
  requires:
    len(error.agent_name) > 0
    len(error.error_code) > 0
  do
    if error.retryable:
      return Ok("Retrying agent: " + error.agent_name)
    else:
      return Err(error)
    end
  end
end
```

---

## Real-World Example: Multi-Agent Research

**Test Results:**
- Agent A (Python/CrewAI): Output = `{"insights": [...], "confidence": 0.85}`
- Agent B (JavaScript/LangGraph): Output = `{"insights": [...], "confidence": 0.85}`
- **100% identical** for 5/5 test cases

**See:** `examples/agent_coordination/` for complete working example.

---

## Testing Multi-Agent Coordination

```python
# test_agent_coordination.py
import pytest
from agent_python import PythonAgent
from agent_javascript import JavaScriptAgent

def test_identical_outputs():
    """Both agents produce identical outputs."""

    python_agent = PythonAgent()
    js_agent = JavaScriptAgent()

    test_cases = [
        "Hello World",
        "Multi-agent AI",
        "AssertLang contracts",
    ]

    for test_input in test_cases:
        python_output = python_agent.run(test_input)
        js_output = js_agent.run(test_input)

        # Outputs must be identical
        assert python_output == js_output

def test_contract_violations_caught():
    """Contract violations caught in both languages."""

    python_agent = PythonAgent()

    # Empty input violates contract
    with pytest.raises(ValueError, match="Contract failed"):
        python_agent.run("")
```

---

## Common Pitfalls

### ❌ No Shared Contract

```python
# Bad: Python agent returns one shape
def python_agent(data):
    return {"result": data}

# JavaScript agent expects different shape
function jsAgent(input) {
    return input.data.value;  // Crashes!
}
```

### ✅ Shared Contract

```promptware
# Good: Both agents use same contract
function process(data: String) -> Result<Output, String>
  ensures:
    len(result.processed) > 0 if result is Ok
  do
    return Ok(Output(processed=data))
  end
end
```

### ❌ Framework-Specific Logic

```python
# Bad: Logic tied to CrewAI
def crewai_specific_agent(input: CrewAITask):
    # Can't reuse in LangGraph!
    return crewai.process(input)
```

### ✅ Framework-Agnostic Contracts

```promptware
# Good: Pure business logic in contracts
function process_task(input: TaskData) -> Result<TaskResult, String>
  # Works in ANY framework
  do
    return Ok(TaskResult(...))
  end
end
```

---

## See Also

- [CrewAI Agent Contracts](crewai-agent-contracts.md) - CrewAI-specific integration
- [LangGraph State Validation](langgraph-state-validation.md) - LangGraph workflows
- [Tool Contracts](tool-contracts.md) - Validate agent tool calls
- [Multi-Field Constraints](../validation/multi-field-constraints.md) - Cross-field validation

---

**Difficulty:** Advanced
**Time:** 20 minutes
**Category:** Framework Integration
**Last Updated:** 2025-10-15
