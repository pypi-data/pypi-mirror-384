# Recipe: CrewAI Agent Contracts

**Problem:** Validate CrewAI agent inputs/outputs to prevent cascading failures in multi-agent workflows.

**Difficulty:** Intermediate
**Time:** 15 minutes

---

## The Problem

CrewAI agents pass data between each other. Without contracts:
- **Silent failures**: Agent produces invalid output, next agent crashes
- **Incomplete data**: Missing required fields not caught until runtime
- **Quality issues**: Low-quality results propagate through pipeline
- **Debugging nightmare**: Hard to trace which agent caused failure

---

## Solution

```al
function validate_research_query(
    query: string,
    depth: int
) -> bool {
    @requires non_empty_query: len(query) > 0
    @requires query_not_whitespace: len(query.strip()) > 0
    @requires valid_depth: depth > 0 && depth <= 10

    @ensures validation_complete: result == true || result == false

    // Validation happens in contracts
    return true;
}

function validate_research_results(
    results: string,
    source_count: int,
    quality_score: float
) -> bool {
    @requires has_results: len(results) > 0
    @requires results_substantial: len(results) >= 100
    @requires sufficient_sources: source_count >= 3
    @requires quality_threshold: quality_score >= 0.7

    @ensures validation_complete: result == true || result == false

    // Validation happens in contracts
    return true;
}
```

**Generated Python with CrewAI:**
```python
from crewai import Agent, Task, Crew
from research_contracts import validate_research_query, validate_research_results

# Define agents
researcher = Agent(
    role='Research Analyst',
    goal='Conduct thorough research on given topics',
    backstory='Expert researcher with 10 years experience',
    verbose=True
)

analyst = Agent(
    role='Data Analyst',
    goal='Analyze research and extract insights',
    backstory='Analytical expert skilled at pattern recognition',
    verbose=True
)

# Define tasks with contract validation
research_task = Task(
    description='Research: {topic}',
    agent=researcher,
    expected_output='Comprehensive research report with sources'
)

def execute_research_with_contracts(topic: str, depth: int = 3):
    # Validate inputs with contracts
    validate_research_query(topic, depth)

    # Execute task
    crew = Crew(agents=[researcher], tasks=[research_task])
    result = crew.kickoff(inputs={'topic': topic})

    # Validate outputs with contracts
    quality_score = calculate_quality(result)
    source_count = count_sources(result)
    validate_research_results(result, source_count, quality_score)

    return result

# ✓ Contract validation at agent boundaries
```

---

## Explanation

**Two validation points:**
1. **Input validation** (`validate_research_query`) - Before agent execution
2. **Output validation** (`validate_research_results`) - After agent completion

**Why contracts instead of manual checks?**
- Declarative (states requirements, not implementation)
- Automatic (no `if` statements needed)
- Self-documenting (contracts serve as API spec)
- Reusable (same contracts across multiple agents)

---

## Variations

### Agent Coordination
```al
function can_analyst_proceed(
    research_complete: bool,
    research_quality: float,
    has_data: bool
) -> bool {
    @requires research_done: research_complete == true
    @requires quality_met: research_quality >= 0.7
    @requires data_present: has_data == true

    @ensures can_proceed: result == true

    return true;
}
```

**Usage:**
```python
# After researcher completes
research_done = researcher.execute()
quality = calculate_quality(research_done)

# Check if analyst can proceed
if can_analyst_proceed(True, quality, len(research_done) > 0):
    analyst_result = analyst.execute(research_done)
```

---

### Tool Contract Validation
```al
function validate_tool_call(
    tool_name: string,
    params_valid: bool,
    has_permission: bool
) -> bool {
    @requires known_tool: len(tool_name) > 0
    @requires valid_params: params_valid == true
    @requires authorized: has_permission == true

    @ensures call_allowed: result == true

    return true;
}
```

---

### Pipeline Stage Validation
```al
function validate_pipeline_stage(
    stage_name: string,
    prev_stage_complete: bool,
    data_valid: bool
) -> bool {
    @requires valid_stage: stage_name == "research" || stage_name == "analyze" || stage_name == "write"
    @requires previous_done: prev_stage_complete == true
    @requires valid_data: data_valid == true

    @ensures stage_ready: result == true

    return true;
}
```

---

## Common Pitfalls

### ❌ Validating too late
```python
# Agent already executed (failure already happened)
result = agent.execute()
validate_results(result)  # Too late!
```

**Fix**: Validate inputs BEFORE execution, outputs AFTER.

---

### ❌ Incomplete validation
```al
@requires non_empty: len(query) > 0
// Allows whitespace-only strings!
```

**Fix**: Check both length AND content quality.

---

### ❌ No quality thresholds
```python
# Any output accepted, even garbage
result = agent.execute()
return result  # No quality check!
```

**Fix**: Add quality score thresholds in contracts.

---

## Real-World Example

**Complete Multi-Agent Research Pipeline:**

```al
function execute_research_pipeline(
    topic: string,
    depth: int
) -> string {
    @requires valid_topic: len(topic.strip()) > 0
    @requires valid_depth: depth >= 1 && depth <= 5

    @ensures has_results: len(result) >= 500
    @ensures high_quality: calculate_quality_score(result) >= 0.8

    // Stage 1: Research
    let research_query = topic;
    validate_research_query(research_query, depth);

    let research_results = run_research_agent(research_query, depth);
    validate_research_results(
        research_results,
        count_sources(research_results),
        calculate_quality_score(research_results)
    );

    // Stage 2: Analysis
    can_analyst_proceed(
        true,  // research complete
        calculate_quality_score(research_results),
        len(research_results) > 0
    );

    let analysis = run_analysis_agent(research_results);
    validate_analysis_results(analysis);

    // Stage 3: Report Writing
    can_writer_proceed(
        true,  // analysis complete
        calculate_quality_score(analysis),
        len(analysis) > 0
    );

    let final_report = run_writer_agent(research_results, analysis);
    validate_report(final_report);

    return final_report;
}
```

**Python Implementation:**
```python
from crewai import Agent, Task, Crew
from pipeline_contracts import (
    validate_research_query,
    validate_research_results,
    can_analyst_proceed,
    validate_analysis_results,
    can_writer_proceed,
    validate_report
)

def execute_research_pipeline(topic: str, depth: int = 3) -> str:
    # Validate inputs
    validate_research_query(topic, depth)

    # Stage 1: Research
    researcher = create_researcher_agent()
    research_task = create_research_task(topic)
    research_crew = Crew(agents=[researcher], tasks=[research_task])
    research_results = research_crew.kickoff()

    # Validate research output
    validate_research_results(
        research_results,
        count_sources(research_results),
        calculate_quality(research_results)
    )

    # Stage 2: Analysis (only if research quality sufficient)
    if can_analyst_proceed(True, calculate_quality(research_results), True):
        analyst = create_analyst_agent()
        analysis_task = create_analysis_task(research_results)
        analysis_crew = Crew(agents=[analyst], tasks=[analysis_task])
        analysis = analysis_crew.kickoff()

        validate_analysis_results(analysis)
    else:
        raise ValueError("Research quality insufficient for analysis")

    # Stage 3: Report (only if analysis complete)
    if can_writer_proceed(True, calculate_quality(analysis), True):
        writer = create_writer_agent()
        report_task = create_report_task(research_results, analysis)
        writer_crew = Crew(agents=[writer], tasks=[report_task])
        final_report = writer_crew.kickoff()

        validate_report(final_report)
    else:
        raise ValueError("Analysis quality insufficient for report")

    return final_report
```

**Result:**
- ✓ Every agent input validated
- ✓ Every agent output validated
- ✓ Stage transitions gated by quality
- ✓ Clear error messages when contracts fail
- ✓ No cascading failures

---

## See Also

- **[LangGraph State Validation](langgraph-state-validation.md)** - State machine contracts
- **[Agent Coordination](agent-coordination.md)** - Multi-agent workflows
- **[Tool Contracts](tool-contracts.md)** - Validate tool calls
- **[Multi-Agent Research Example](../../../examples/real_world/02_multi_agent_research/)** - Complete working example

---

**Next**: Try [LangGraph State Validation](langgraph-state-validation.md) →
