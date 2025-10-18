# LangChain Integration

**Integrate AssertLang contracts with LangChain chains, agents, and tools for validated LLM workflows.**

---

## Problem

LangChain workflows need validation:
- Chain inputs/outputs have no type guarantees
- Tools accept arbitrary LLM-generated arguments
- No validation on chain composition
- Hard to debug multi-step chains
- Silent failures in production

**Bad approach:**
```python
# Python: No validation
from langchain.chains import LLMChain

chain = LLMChain(llm=llm, prompt=prompt)

# No validation on input or output
result = chain.run({"input": anything})  # Could be anything!
```

**Issues:**
- No type safety
- Invalid inputs crash chains
- Hard to compose chains
- No guarantees on output shape

---

## Solution

Use AssertLang contracts with LangChain:

**1. Define contract:**
```promptware
type ChainInput:
  query: String
  max_length: Int
end

type ChainOutput:
  response: String
  tokens_used: Int
end

function validate_chain_io(
    input: ChainInput,
    output: ChainOutput
) -> Result<ChainOutput, String>
  requires:
    len(input.query) > 0
    len(input.query) <= 1000
    input.max_length > 0
    input.max_length <= 4000
  ensures:
    len(result.response) > 0 if result is Ok
    result.tokens_used > 0 if result is Ok
    result.tokens_used <= input.max_length if result is Ok
  do
    return Ok(output)
  end
end
```

**2. Wrap LangChain chain:**
```python
from langchain.chains import LLMChain
from langchain.llms import OpenAI
from chain_contracts import validate_chain_io, ChainInput, ChainOutput, Err

class ValidatedChain:
    def __init__(self, llm, prompt):
        self.chain = LLMChain(llm=llm, prompt=prompt)

    def run(self, query: str, max_length: int) -> dict:
        # Validate input
        chain_input = ChainInput(query=query, max_length=max_length)

        # Run chain
        response = self.chain.run({"query": query, "max_length": max_length})

        # Create output
        output = ChainOutput(
            response=response,
            tokens_used=len(response.split())  # Simplified token count
        )

        # Validate input/output together
        result = validate_chain_io(chain_input, output)

        if isinstance(result, Err):
            raise ValueError(f"Contract violation: {result.error}")

        return {
            "response": result.value.response,
            "tokens_used": result.value.tokens_used
        }
```

---

## Basic Patterns

### Simple Chain Validation

```promptware
type QuestionInput:
  question: String
  context: Option<String>
end

type AnswerOutput:
  answer: String
  confidence: Float
end

function validate_qa_chain(
    input: QuestionInput,
    output: AnswerOutput
) -> Result<AnswerOutput, String>
  requires:
    len(input.question) > 0
  ensures:
    len(result.answer) > 0 if result is Ok
    result.confidence >= 0.0 if result is Ok
    result.confidence <= 1.0 if result is Ok
  do
    return Ok(output)
  end
end
```

---

## Tool Validation

### LangChain Tool with Contracts

```promptware
type ToolInput:
  operation: String
  arguments: Map<String, String>
end

type ToolOutput:
  result: String
  success: Bool
end

function validate_tool_call(
    input: ToolInput,
    output: ToolOutput
) -> Result<ToolOutput, String>
  requires:
    len(input.operation) > 0
    len(input.arguments) > 0
  do
    if not output.success:
      return Err("Tool execution failed")
    end

    if len(output.result) == 0:
      return Err("Tool returned empty result")
    end

    return Ok(output)
  end
end
```

**LangChain Integration:**
```python
from langchain.tools import BaseTool
from langchain.pydantic_v1 import BaseModel, Field
from typing import Dict
from tool_contracts import validate_tool_call, ToolInput, ToolOutput, Err

class ValidatedTool(BaseTool):
    name = "validated_tool"
    description = "Tool with contract validation"

    class InputSchema(BaseModel):
        operation: str = Field(description="Operation to perform")
        arguments: Dict[str, str] = Field(description="Operation arguments")

    args_schema = InputSchema

    def _run(self, operation: str, arguments: Dict[str, str]) -> str:
        # Create input
        tool_input = ToolInput(operation=operation, arguments=arguments)

        # Execute operation
        result_str, success = self._execute_operation(operation, arguments)

        # Create output
        tool_output = ToolOutput(result=result_str, success=success)

        # Validate
        validation_result = validate_tool_call(tool_input, tool_output)

        if isinstance(validation_result, Err):
            return f"Validation failed: {validation_result.error}"

        return validation_result.value.result

    def _execute_operation(self, operation: str, arguments: Dict[str, str]):
        # Implementation
        return f"Executed {operation}", True
```

---

## Agent Validation

### LangChain Agent with Validated Tools

```python
from langchain.agents import initialize_agent, AgentType
from langchain.llms import OpenAI
from validated_tools import ValidatedSearchTool, ValidatedCalculatorTool

# Create validated tools
search_tool = ValidatedSearchTool()
calc_tool = ValidatedCalculatorTool()

# Initialize agent with validated tools
llm = OpenAI(temperature=0)
agent = initialize_agent(
    tools=[search_tool, calc_tool],
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)

# Run agent - tools validate all LLM-generated calls
response = agent.run("Search for AI papers and calculate average citations")

# If LLM generates invalid tool arguments, contracts catch it
```

---

## Chain Composition

### Sequential Chain with Validation

```promptware
type Step1Input:
  raw_text: String
end

type Step1Output:
  cleaned_text: String
  word_count: Int
end

type Step2Input:
  cleaned_text: String
  min_words: Int
end

type Step2Output:
  summary: String
end

function validate_step1(
    input: Step1Input,
    output: Step1Output
) -> Result<Step1Output, String>
  requires:
    len(input.raw_text) > 0
  ensures:
    len(result.cleaned_text) > 0 if result is Ok
    result.word_count > 0 if result is Ok
  do
    return Ok(output)
  end
end

function validate_step2(
    input: Step2Input,
    output: Step2Output
) -> Result<Step2Output, String>
  requires:
    len(input.cleaned_text) > 0
    input.min_words > 0
  ensures:
    len(result.summary) > 0 if result is Ok
  do
    return Ok(output)
  end
end
```

**LangChain Sequential Chain:**
```python
from langchain.chains import SequentialChain, LLMChain
from langchain.prompts import PromptTemplate
from chain_contracts import *

# Step 1: Clean text
clean_chain = LLMChain(
    llm=llm,
    prompt=PromptTemplate(template="Clean this text: {raw_text}"),
    output_key="cleaned_text"
)

# Step 2: Summarize
summary_chain = LLMChain(
    llm=llm,
    prompt=PromptTemplate(template="Summarize: {cleaned_text}"),
    output_key="summary"
)

# Compose with validation
class ValidatedSequentialChain:
    def __init__(self):
        self.chain = SequentialChain(
            chains=[clean_chain, summary_chain],
            input_variables=["raw_text"],
            output_variables=["cleaned_text", "summary"]
        )

    def run(self, raw_text: str) -> dict:
        # Validate step 1 input
        step1_input = Step1Input(raw_text=raw_text)

        # Run chain
        result = self.chain({"raw_text": raw_text})

        # Validate step 1 output
        step1_output = Step1Output(
            cleaned_text=result["cleaned_text"],
            word_count=len(result["cleaned_text"].split())
        )

        validate_result = validate_step1(step1_input, step1_output)
        if isinstance(validate_result, Err):
            raise ValueError(f"Step 1 failed: {validate_result.error}")

        # Validate step 2
        step2_input = Step2Input(cleaned_text=result["cleaned_text"], min_words=10)
        step2_output = Step2Output(summary=result["summary"])

        validate_result = validate_step2(step2_input, step2_output)
        if isinstance(validate_result, Err):
            raise ValueError(f"Step 2 failed: {validate_result.error}")

        return result
```

---

## Real-World Example: Document QA

**Contract:**
```promptware
# document_qa.al
type DocumentInput:
  document: String
  question: String
end

type AnswerOutput:
  answer: String
  sources: List<String>
  confidence: Float
end

function validate_document_qa(
    input: DocumentInput,
    output: AnswerOutput
) -> Result<AnswerOutput, String>
  requires:
    len(input.document) > 0
    len(input.document) <= 50000  # Max document size
    len(input.question) > 0
    len(input.question) <= 500
  ensures:
    len(result.answer) > 0 if result is Ok
    len(result.sources) > 0 if result is Ok
    result.confidence >= 0.0 if result is Ok
    result.confidence <= 1.0 if result is Ok
  do
    return Ok(output)
  end
end
```

**LangChain Integration:**
```python
from langchain.chains.question_answering import load_qa_chain
from langchain.docstore.document import Document
from langchain.llms import OpenAI
from document_qa_contracts import validate_document_qa, DocumentInput, AnswerOutput, Err

class ValidatedDocumentQA:
    def __init__(self):
        self.llm = OpenAI(temperature=0)
        self.chain = load_qa_chain(self.llm, chain_type="stuff")

    def answer_question(self, document: str, question: str) -> dict:
        # Validate input
        doc_input = DocumentInput(document=document, question=question)

        # Create document
        docs = [Document(page_content=document)]

        # Run chain
        response = self.chain({"input_documents": docs, "question": question})

        # Parse output
        answer = response["output_text"]
        sources = [doc.page_content[:100] for doc in docs]  # Source snippets
        confidence = 0.85  # Simplified confidence score

        # Create output
        output = AnswerOutput(
            answer=answer,
            sources=sources,
            confidence=confidence
        )

        # Validate
        result = validate_document_qa(doc_input, output)

        if isinstance(result, Err):
            raise ValueError(f"Validation failed: {result.error}")

        return {
            "answer": result.value.answer,
            "sources": result.value.sources,
            "confidence": result.value.confidence
        }

# Usage
qa = ValidatedDocumentQA()

document = """
AssertLang is a language for writing executable contracts
that compile to multiple languages. It enables deterministic
multi-agent coordination across frameworks.
"""

question = "What is AssertLang?"

result = qa.answer_question(document, question)
print(f"Answer: {result['answer']}")
print(f"Confidence: {result['confidence']}")
```

---

## Testing

```python
# test_langchain_integration.py
import pytest
from document_qa_integration import ValidatedDocumentQA

def test_valid_qa():
    qa = ValidatedDocumentQA()

    document = "AI is transforming software development."
    question = "What is AI doing?"

    result = qa.answer_question(document, question)

    assert "answer" in result
    assert len(result["answer"]) > 0
    assert result["confidence"] >= 0.0
    assert result["confidence"] <= 1.0

def test_document_too_large():
    qa = ValidatedDocumentQA()

    # Document exceeds 50,000 char limit
    document = "a" * 50001
    question = "What is this?"

    with pytest.raises(ValueError, match="Validation failed"):
        qa.answer_question(document, question)

def test_empty_question():
    qa = ValidatedDocumentQA()

    document = "Valid document"
    question = ""  # Empty question violates contract

    with pytest.raises(AssertionError):
        qa.answer_question(document, question)
```

---

## Common Pitfalls

### ❌ No Chain Validation

```python
# Bad: Chain outputs not validated
chain = LLMChain(llm=llm, prompt=prompt)
result = chain.run(input_data)  # Could be anything!
```

### ✅ Validated Chain

```python
# Good: Contract validates output
result = chain.run(input_data)
output = ChainOutput(response=result, ...)
validated = validate_chain_io(input_obj, output)
```

### ❌ Tool Crashes on Invalid Args

```python
# Bad: Tool accepts any LLM-generated args
@tool
def search(query: str, limit: int):
    # LLM might generate limit="-1"
    return db.query(query, limit)  # Crashes!
```

### ✅ Tool Validates Args

```promptware
# Good: Contract enforces valid args
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

---

## See Also

- [CrewAI Agent Contracts](crewai-agent-contracts.md) - CrewAI integration
- [LangGraph State Validation](langgraph-state-validation.md) - LangGraph workflows
- [Tool Contracts](tool-contracts.md) - Validate tool calls
- [Agent Coordination](agent-coordination.md) - Multi-agent workflows

---

**Difficulty:** Intermediate
**Time:** 15 minutes
**Category:** Framework Integration
**Last Updated:** 2025-10-15
