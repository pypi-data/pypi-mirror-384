# AssertLang Cookbook

**Recipes for common contract patterns - copy, paste, adapt.**

---

## Quick Navigation

| Category | Recipes | Difficulty | Time |
|----------|---------|------------|------|
| [Validation](#validation) | 10 recipes | Beginner | 5-10 min |
| [Framework Integration](#framework-integration) | 6 recipes | Intermediate | 10-15 min |
| [Design Patterns](#design-patterns) | 8 recipes | Intermediate | 15-20 min |
| [Advanced Patterns](#advanced-patterns) | 6 recipes | Advanced | 20-30 min |

**Total**: 30 recipes covering 80% of common use cases

---

## Validation

**Problem**: Ensure inputs meet requirements before processing.

| Recipe | What It Does | Time |
|--------|--------------|------|
| [Non-Empty Strings](validation/non-empty-strings.md) | Prevent empty string inputs | 5 min |
| [Positive Numbers](validation/positive-numbers.md) | Ensure numbers > 0 | 5 min |
| [Array Bounds](validation/array-bounds.md) | Validate array indices and sizes | 10 min |
| [Enum Validation](validation/enum-validation.md) | Check values against allowed set | 10 min |
| [Range Checking](validation/range-checking.md) | Ensure values within min/max bounds | 5 min |
| [Email Validation](validation/email-validation.md) | Validate email format | 10 min |
| [Custom Validators](validation/custom-validators.md) | Build reusable validation functions | 15 min |
| [Nested Object Validation](validation/nested-validation.md) | Validate complex data structures | 15 min |
| [Conditional Validation](validation/conditional-validation.md) | Validate based on other fields | 10 min |
| [Multi-Field Constraints](validation/multi-field-constraints.md) | Rules spanning multiple fields | 10 min |

---

## Framework Integration

**Problem**: Integrate contracts with popular AI/data frameworks.

| Recipe | What It Does | Time |
|--------|--------------|------|
| [CrewAI Agent Contracts](framework-integration/crewai-agent-contracts.md) | Validate agent inputs/outputs | 15 min |
| [LangGraph State Validation](framework-integration/langgraph-state-validation.md) | Validate state machine transitions | 15 min |
| [Agent Coordination](framework-integration/agent-coordination.md) | Coordinate multi-agent workflows | 20 min |
| [Tool Contracts](framework-integration/tool-contracts.md) | Validate agent tool calls | 15 min |
| [FastAPI Integration](framework-integration/fastapi-integration.md) | Validate API requests/responses | 15 min |
| [LangChain Integration](framework-integration/langchain-integration.md) | Validate chain inputs/outputs | 15 min |

---

## Design Patterns

**Problem**: Implement common software patterns with contract safety.

| Recipe | What It Does | Time |
|--------|--------------|------|
| [State Machines](patterns/state-machines.md) | Validate state transitions | 20 min |
| [Builder Pattern](patterns/builder-pattern.md) | Ensure complete object construction | 15 min |
| [Factory Pattern](patterns/factory-pattern.md) | Validate factory inputs/outputs | 15 min |
| [Repository Pattern](patterns/repository-pattern.md) | Validate data access operations | 15 min |
| [Command Pattern](patterns/command-pattern.md) | Validate command preconditions | 15 min |
| [Observer Pattern](patterns/observer-pattern.md) | Validate event handlers | 15 min |
| [Strategy Pattern](patterns/strategy-pattern.md) | Validate strategy implementations | 15 min |
| [Pipeline Pattern](patterns/pipeline-pattern.md) | Validate data transformations | 20 min |

---

## Advanced Patterns

**Problem**: Handle complex contract scenarios.

| Recipe | What It Does | Time |
|--------|--------------|------|
| [Complex Invariants](advanced/complex-invariants.md) | Multi-condition state invariants | 20 min |
| [Contract Composition](advanced/contract-composition.md) | Compose reusable contract fragments | 25 min |
| [Performance Tuning](advanced/performance-tuning.md) | Optimize contract checking overhead | 30 min |
| [Debugging Contracts](advanced/debugging-contracts.md) | Diagnose contract failures | 20 min |
| [Contract Testing](advanced/contract-testing.md) | Test contract correctness | 25 min |
| [Gradual Migration](advanced/gradual-migration.md) | Add contracts to existing codebase | 30 min |

---

## How to Use This Cookbook

1. **Find Your Pattern** - Browse categories or use search
2. **Copy the Example** - Each recipe has working code
3. **Adapt to Your Needs** - Modify for your specific use case
4. **Learn the Variations** - See alternative approaches

**Pro Tip**: Start with [Validation](#validation) recipes - they're the most common and easiest to learn.

---

## Recipe Format

Every recipe follows this structure:

- **Problem**: One-sentence problem statement
- **Difficulty**: Beginner | Intermediate | Advanced
- **Time**: Estimated time to understand and implement
- **Solution**: Working code you can copy
- **Explanation**: Why it works
- **Variations**: Alternative approaches
- **Common Pitfalls**: What to avoid
- **See Also**: Related recipes

---

## Quick Examples

### Need to validate non-empty strings?
```al
@requires non_empty: len(text) > 0
```

### Need to ensure positive numbers?
```al
@requires positive: amount > 0
@ensures result_positive: result > 0
```

### Need to validate state transitions?
```al
@requires valid_transition: current_state == "idle" && next_state == "active"
```

### Need to coordinate agents?
```al
@requires researcher_done: researcher_status == "completed"
@requires has_data: len(research_results) > 0
```

---

## Real-World Examples

For complete, production-ready examples, see:

- **[E-commerce Orders](../../examples/real_world/01_ecommerce_orders/)** - State machines + refunds
- **[Multi-Agent Research](../../examples/real_world/02_multi_agent_research/)** - CrewAI contracts
- **[Data Pipelines](../../examples/real_world/03_data_processing_workflow/)** - LangGraph validation
- **[Rate Limiting](../../examples/real_world/04_api_rate_limiting/)** - Token buckets
- **[State Machines](../../examples/real_world/05_state_machine_patterns/)** - Generic patterns

---

## Contributing Recipes

Have a useful pattern? [Submit a recipe →](https://github.com/AssertLang/AssertLang/blob/main/CONTRIBUTING.md)

**Good recipes are:**
- Focused on one problem
- Include working code
- Explain the "why" not just the "how"
- Show common pitfalls
- Link to related patterns

---

**Browse by Category**: [Validation](#validation) | [Framework Integration](#framework-integration) | [Design Patterns](#design-patterns) | [Advanced](#advanced-patterns)
