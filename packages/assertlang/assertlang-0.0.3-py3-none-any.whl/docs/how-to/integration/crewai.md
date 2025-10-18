# How to Integrate with CrewAI

**Add contract validation to CrewAI agents and multi-agent pipelines.**

---

## What You'll Learn

- Add contracts to CrewAI agents
- Validate agent inputs and outputs
- Ensure pipeline data quality
- Test multi-agent workflows
- Handle contract violations in agents

**Prerequisites**:
- AssertLang installed
- CrewAI installed (`pip install crewai`)
- Basic CrewAI knowledge

**Time**: 30 minutes

**Difficulty**: Intermediate

---

## Why Add Contracts to CrewAI?

**CrewAI challenges:**
- Agent outputs may not match expected format
- Pipeline data gets corrupted between agents
- Hard to debug multi-agent failures
- No validation of agent inputs

**Contracts solve this:**
- ✅ Validate agent inputs before execution
- ✅ Verify agent outputs match spec
- ✅ Ensure data quality through pipeline
- ✅ Catch errors early with clear messages

---

## Step 1: Create Agent Contracts

Create `research_contracts.al`:

```al
// Research agent contracts
function validate_research_query(
    query: string,
    depth: int,
    max_sources: int
) -> bool {
    @requires query_not_empty: len(query) > 0
    @requires query_meaningful: len(query) >= 10
    @requires valid_depth: depth > 0 && depth <= 5
    @requires reasonable_sources: max_sources > 0 && max_sources <= 20

    @ensures validation_complete: result == true || result == false

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
    @requires valid_score: quality_score >= 0.0 && quality_score <= 1.0
    @requires quality_threshold: quality_score >= 0.7

    @ensures validation_complete: result == true || result == false

    return true;
}

// Writer agent contracts
function validate_article_draft(
    content: string,
    word_count: int,
    section_count: int
) -> bool {
    @requires has_content: len(content) > 0
    @requires minimum_length: word_count >= 500
    @requires maximum_length: word_count <= 5000
    @requires has_sections: section_count >= 3
    @requires structured: section_count <= 10

    @ensures validation_complete: result == true || result == false

    return true;
}
```

Generate Python:

```bash
asl build research_contracts.al -o research_contracts.py
```

---

## Step 2: Integrate with CrewAI Agent

Create `research_agent.py`:

```python
from crewai import Agent, Task, Crew
from research_contracts import (
    validate_research_query,
    validate_research_results
)
from promptware.runtime.contracts import ContractViolationError


class ResearchAgent:
    """Research agent with contract validation."""

    def __init__(self):
        self.agent = Agent(
            role='Research Analyst',
            goal='Conduct thorough research on given topics',
            backstory='Expert researcher with fact-checking skills',
            verbose=True
        )

    def research(self, query: str, depth: int = 3, max_sources: int = 10) -> dict:
        """
        Execute research with contract validation.

        Args:
            query: Research query
            depth: Research depth (1-5)
            max_sources: Maximum sources to use

        Returns:
            Research results dict with content, sources, quality score

        Raises:
            ContractViolationError: If inputs or outputs violate contracts
        """
        # Validate inputs
        try:
            validate_research_query(query, depth, max_sources)
        except ContractViolationError as e:
            print(f"❌ Invalid research query: {e.clause}")
            print(f"   {e.message}")
            raise

        # Execute research task
        task = Task(
            description=f"Research the following: {query}. Depth level: {depth}",
            agent=self.agent
        )

        # Get results
        results = task.execute()

        # Parse results (simplified)
        content = str(results)
        source_count = content.count("Source:")
        quality_score = min(len(content) / 1000.0, 1.0)  # Simple heuristic

        # Validate outputs
        try:
            validate_research_results(content, source_count, quality_score)
        except ContractViolationError as e:
            print(f"❌ Research results don't meet quality standards: {e.clause}")
            print(f"   Expected: {e.expression}")
            print(f"   Got: {e.context}")
            raise

        return {
            "content": content,
            "source_count": source_count,
            "quality_score": quality_score
        }


# Usage
if __name__ == "__main__":
    agent = ResearchAgent()

    # ✓ Valid query
    results = agent.research(
        "What are the latest advances in AI safety?",
        depth=3,
        max_sources=10
    )
    print(f"✓ Research complete: {results['source_count']} sources, "
          f"quality {results['quality_score']:.2f}")

    # ✗ Invalid query (too short)
    try:
        agent.research("AI", depth=3, max_sources=10)
    except ContractViolationError as e:
        print(f"✗ Query rejected: {e.clause}")
```

---

## Step 3: Multi-Agent Pipeline with Contracts

Create `research_pipeline.py`:

```python
from crewai import Agent, Task, Crew, Process
from research_contracts import (
    validate_research_query,
    validate_research_results,
    validate_article_draft
)
from promptware.runtime.contracts import ContractViolationError


class ResearchPipeline:
    """Multi-agent research pipeline with contract validation."""

    def __init__(self):
        # Researcher agent
        self.researcher = Agent(
            role='Research Analyst',
            goal='Gather comprehensive information',
            backstory='Expert at finding and evaluating sources',
            verbose=True
        )

        # Writer agent
        self.writer = Agent(
            role='Content Writer',
            goal='Create well-structured articles',
            backstory='Skilled writer who turns research into readable content',
            verbose=True
        )

        # Editor agent
        self.editor = Agent(
            role='Editor',
            goal='Ensure content quality and accuracy',
            backstory='Detail-oriented editor with high standards',
            verbose=True
        )

    def run_pipeline(self, topic: str) -> dict:
        """
        Execute full research pipeline with validation.

        Args:
            topic: Research topic

        Returns:
            Final article dict

        Raises:
            ContractViolationError: If any stage violates contracts
        """
        # Stage 1: Validate topic
        print("📋 Stage 1: Validating topic...")
        try:
            validate_research_query(
                query=topic,
                depth=3,
                max_sources=10
            )
        except ContractViolationError as e:
            print(f"❌ Invalid topic: {e.clause}")
            raise

        # Stage 2: Research
        print("🔍 Stage 2: Conducting research...")
        research_task = Task(
            description=f"Research: {topic}. Find at least 3 credible sources.",
            agent=self.researcher
        )
        research_results = research_task.execute()

        # Validate research output
        source_count = str(research_results).count("Source:")
        quality_score = min(len(str(research_results)) / 1000.0, 1.0)

        try:
            validate_research_results(
                results=str(research_results),
                source_count=source_count,
                quality_score=quality_score
            )
            print(f"✓ Research validated: {source_count} sources, "
                  f"quality {quality_score:.2f}")
        except ContractViolationError as e:
            print(f"❌ Research quality insufficient: {e.clause}")
            print(f"   Required: {e.expression}")
            raise

        # Stage 3: Write article
        print("✍️  Stage 3: Writing article...")
        writing_task = Task(
            description=f"Write a comprehensive article based on this research:\n{research_results}",
            agent=self.writer,
            context=[research_task]
        )
        draft = writing_task.execute()

        # Validate draft
        word_count = len(str(draft).split())
        section_count = str(draft).count("##")

        try:
            validate_article_draft(
                content=str(draft),
                word_count=word_count,
                section_count=section_count
            )
            print(f"✓ Draft validated: {word_count} words, {section_count} sections")
        except ContractViolationError as e:
            print(f"❌ Draft doesn't meet standards: {e.clause}")
            print(f"   Got word_count={word_count}, section_count={section_count}")
            raise

        # Stage 4: Edit
        print("📝 Stage 4: Editing...")
        editing_task = Task(
            description=f"Edit and improve this draft:\n{draft}",
            agent=self.editor,
            context=[writing_task]
        )
        final_article = editing_task.execute()

        return {
            "topic": topic,
            "research": str(research_results),
            "draft": str(draft),
            "final": str(final_article),
            "metadata": {
                "sources": source_count,
                "quality": quality_score,
                "words": word_count,
                "sections": section_count
            }
        }


# Usage
if __name__ == "__main__":
    pipeline = ResearchPipeline()

    # ✓ Valid pipeline execution
    article = pipeline.run_pipeline(
        "The impact of artificial intelligence on modern healthcare"
    )

    print("\n" + "="*60)
    print("✓ Pipeline completed successfully")
    print("="*60)
    print(f"Topic: {article['topic']}")
    print(f"Sources: {article['metadata']['sources']}")
    print(f"Quality: {article['metadata']['quality']:.2f}")
    print(f"Words: {article['metadata']['words']}")
```

---

## Step 4: Handle Contract Violations Gracefully

Create `robust_pipeline.py`:

```python
from crewai import Agent, Task
from research_contracts import validate_research_query
from promptware.runtime.contracts import ContractViolationError
import time


class RobustResearchAgent:
    """Research agent with graceful contract violation handling."""

    def __init__(self):
        self.agent = Agent(
            role='Research Analyst',
            goal='Conduct research',
            backstory='Expert researcher'
        )
        self.max_retries = 3

    def research_with_retry(self, query: str, depth: int = 3) -> dict:
        """
        Execute research with automatic retry on validation failures.

        Args:
            query: Research query
            depth: Research depth

        Returns:
            Research results or error dict
        """
        for attempt in range(self.max_retries):
            try:
                # Validate input
                validate_research_query(query, depth, max_sources=10)

                # Execute research
                task = Task(
                    description=f"Research: {query}",
                    agent=self.agent
                )
                results = task.execute()

                return {
                    "success": True,
                    "results": str(results),
                    "attempts": attempt + 1
                }

            except ContractViolationError as e:
                print(f"⚠️  Attempt {attempt + 1} failed: {e.clause}")

                # Handle specific violations
                if e.clause == "query_meaningful":
                    # Expand query automatically
                    query = f"{query} - provide detailed analysis with examples"
                    print(f"   Expanding query: {query}")

                elif e.clause == "valid_depth":
                    # Adjust depth
                    depth = max(1, min(5, depth))
                    print(f"   Adjusting depth to: {depth}")

                else:
                    # Can't auto-fix, return error
                    return {
                        "success": False,
                        "error": str(e),
                        "clause": e.clause,
                        "attempts": attempt + 1
                    }

                # Wait before retry
                time.sleep(1)

        return {
            "success": False,
            "error": "Max retries exceeded",
            "attempts": self.max_retries
        }


# Usage
if __name__ == "__main__":
    agent = RobustResearchAgent()

    # Try with short query (will auto-expand)
    result = agent.research_with_retry("AI", depth=3)

    if result["success"]:
        print(f"✓ Success after {result['attempts']} attempt(s)")
    else:
        print(f"✗ Failed: {result['error']}")
```

---

## Step 5: Test Multi-Agent Workflows

Create `test_research_pipeline.py`:

```python
import pytest
from research_pipeline import ResearchPipeline
from research_agent import ResearchAgent
from promptware.runtime.contracts import ContractViolationError


class TestResearchAgent:
    """Test research agent with contracts."""

    def test_valid_research(self):
        """Test research with valid inputs."""
        agent = ResearchAgent()
        results = agent.research(
            "Machine learning best practices",
            depth=3,
            max_sources=10
        )

        assert "content" in results
        assert results["source_count"] >= 3
        assert results["quality_score"] >= 0.7

    def test_invalid_query_too_short(self):
        """Test research rejects short query."""
        agent = ResearchAgent()

        with pytest.raises(ContractViolationError) as exc:
            agent.research("AI", depth=3, max_sources=10)

        assert exc.value.clause == "query_meaningful"

    def test_invalid_depth(self):
        """Test research rejects invalid depth."""
        agent = ResearchAgent()

        with pytest.raises(ContractViolationError) as exc:
            agent.research("Valid query here", depth=10, max_sources=5)

        assert exc.value.clause == "valid_depth"


class TestResearchPipeline:
    """Test multi-agent pipeline."""

    def test_full_pipeline(self):
        """Test complete pipeline execution."""
        pipeline = ResearchPipeline()
        article = pipeline.run_pipeline(
            "The future of renewable energy technologies"
        )

        assert article["topic"] is not None
        assert article["metadata"]["sources"] >= 3
        assert article["metadata"]["quality"] >= 0.7
        assert article["metadata"]["words"] >= 500

    def test_pipeline_rejects_invalid_topic(self):
        """Test pipeline rejects invalid topic."""
        pipeline = ResearchPipeline()

        with pytest.raises(ContractViolationError):
            pipeline.run_pipeline("Bad")  # Too short
```

---

## Integration Patterns

### Pattern 1: Input Validation

**Before every agent execution:**
```python
def execute_agent_task(agent, input_data):
    # Validate input
    validate_input(input_data)

    # Execute agent
    result = agent.execute(input_data)

    return result
```

---

### Pattern 2: Output Validation

**After every agent execution:**
```python
def execute_agent_task(agent, input_data):
    result = agent.execute(input_data)

    # Validate output
    validate_output(result)

    return result
```

---

### Pattern 3: Pipeline Checkpoints

**Validate between pipeline stages:**
```python
# Stage 1: Research
research = researcher.execute(query)
validate_research_results(research)  # ✓ Checkpoint

# Stage 2: Write (only if research valid)
draft = writer.execute(research)
validate_article_draft(draft)  # ✓ Checkpoint

# Stage 3: Edit (only if draft valid)
final = editor.execute(draft)
```

---

## What You Learned

✅ **Add contracts to CrewAI agents** - Validate inputs and outputs
✅ **Multi-agent pipelines** - Ensure data quality through stages
✅ **Handle violations gracefully** - Retry with corrections
✅ **Test agent workflows** - Verify contracts in tests
✅ **Pipeline checkpoints** - Validate between stages

---

## Next Steps

**Advanced integration**:
- [How-To: Integrate with LangGraph](langgraph.md)
- [Cookbook: CrewAI Agent Contracts](../../cookbook/framework-integration/crewai-agent-contracts.md)

**Learn more**:
- [Contract Syntax](../../reference/contract-syntax.md)
- [Runtime API](../../reference/runtime-api.md)

---

## See Also

- **[LangGraph Integration](langgraph.md)** - State graph validation
- **[CrewAI Recipe](../../cookbook/framework-integration/crewai-agent-contracts.md)** - Complete example
- **[Testing Contracts](../getting-started/testing-contracts.md)** - Test workflows

---

**[← MCP Server](mcp-server.md)** | **[LangGraph Integration →](langgraph.md)**
