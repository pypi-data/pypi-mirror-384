# Bidirectional Multi-Language Test Plan

**Objective**: Prove PW as universal agent communication protocol across all languages
**Date**: 2025-10-03
**Status**: Planning → Execution

---

## Test Strategy

### Phase 1: Per-Language Reverse Parsers ✅ Python Complete

Build reverse parser for each language to extract PW DSL from generated code.

**Success Criteria per Language**:
- ✅ 95%+ round-trip accuracy (PW → Code → PW)
- ✅ All verbs preserved
- ✅ All parameters preserved
- ✅ All returns preserved
- ✅ Tools/port/agent name preserved
- ✅ Multi-word agent names work
- ✅ Type inference works

**Languages**:
1. ✅ **Python** - COMPLETE (100% accuracy)
2. ⏳ **Node.js** - TODO
3. ⏳ **Go** - TODO
4. ⏳ **Rust** - TODO
5. ⏳ **C#/.NET** - TODO

---

## Phase 2: Blind Multi-Agent Tests

For each language, run the same test as Python:
1. Agent 1 writes complex random server (no PW knowledge)
2. Reverse parse → PW
3. Forward generate → Code
4. Reverse parse → PW
5. Compare: Original PW vs Final PW (must be 100% match)

**Test Cases per Language**:

### Node.js Test
**Agent 1 Task**: "Write complex Express.js e-commerce API with 10+ endpoints, nested types, async handlers"
**Expected Patterns**:
```javascript
const express = require('express');
const app = express();

app.locals.configuredTools = ['database', 'payment', 'email'];

async function handle_create_order_v1(params) {
    // Handler logic
}

app.post('/mcp', async (req, res) => {
    // MCP routing
});

app.listen(8080);
```

### Go Test
**Agent 1 Task**: "Write complex net/http e-commerce API with 10+ endpoints, structs, goroutines"
**Expected Patterns**:
```go
package main

var ConfiguredTools = []string{"database", "payment", "email"}

func handleCreateOrderV1(params map[string]interface{}) (map[string]interface{}, error) {
    // Handler logic
}

func main() {
    http.HandleFunc("/mcp", mcpHandler)
    http.ListenAndServe(":8080", nil)
}
```

### Rust Test
**Agent 1 Task**: "Write complex warp/actix e-commerce API with 10+ endpoints, structs, async"
**Expected Patterns**:
```rust
use warp::Filter;

static CONFIGURED_TOOLS: &[&str] = &["database", "payment", "email"];

async fn handle_create_order_v1(params: HashMap<String, Value>) -> Result<HashMap<String, Value>, Error> {
    // Handler logic
}

#[tokio::main]
async fn main() {
    warp::serve(routes).run(([0,0,0,0], 8080)).await;
}
```

### .NET Test
**Agent 1 Task**: "Write complex ASP.NET Core e-commerce API with 10+ endpoints, models, async"
**Expected Patterns**:
```csharp
var builder = WebApplication.CreateBuilder();
var app = builder.Build();

string[] ConfiguredTools = { "database", "payment", "email" };

async Task<Dictionary<string, object>> HandleCreateOrderV1(Dictionary<string, object> parameters) {
    // Handler logic
}

app.MapPost("/mcp", async context => {
    // MCP routing
});

app.Run("http://localhost:8080");
```

---

## Phase 3: Cross-Language Translation Tests

Test that PW enables translation between any language pair.

### Test Matrix (20 combinations)

| Source Lang | Target Lang | Test Case |
|-------------|-------------|-----------|
| Python → Node.js | E-commerce API | Write in Python, translate to Node |
| Python → Go | E-commerce API | Write in Python, translate to Go |
| Python → Rust | E-commerce API | Write in Python, translate to Rust |
| Python → .NET | E-commerce API | Write in Python, translate to .NET |
| Node.js → Python | Payment API | Write in Node, translate to Python |
| Node.js → Go | Payment API | Write in Node, translate to Go |
| Node.js → Rust | Payment API | Write in Node, translate to Rust |
| Node.js → .NET | Payment API | Write in Node, translate to .NET |
| Go → Python | Auth API | Write in Go, translate to Python |
| Go → Node.js | Auth API | Write in Go, translate to Node |
| Go → Rust | Auth API | Write in Go, translate to Rust |
| Go → .NET | Auth API | Write in Go, translate to .NET |
| Rust → Python | Inventory API | Write in Rust, translate to Python |
| Rust → Node.js | Inventory API | Write in Rust, translate to Node |
| Rust → Go | Inventory API | Write in Rust, translate to Go |
| Rust → .NET | Inventory API | Write in Rust, translate to .NET |
| .NET → Python | Customer API | Write in .NET, translate to Python |
| .NET → Node.js | Customer API | Write in .NET, translate to Node |
| .NET → Go | Customer API | Write in .NET, translate to Go |
| .NET → Rust | Customer API | Write in .NET, translate to Rust |

**Success Criteria per Translation**:
- Source code → PW extraction (95%+ accuracy)
- PW → Target code generation (valid, runnable)
- Target code → PW extraction (95%+ accuracy)
- Semantic equivalence (same verbs, params, returns)

### Translation Flow Example
```
1. Python Agent writes payment service in Python
2. Reverse parse Python → payment.pw
3. Go Agent reads payment.pw
4. Generate Go implementation
5. Reverse parse Go → payment_go.pw
6. Compare: payment.pw ≈ payment_go.pw (95%+ match)
7. Both services handle same MCP calls
```

---

## Phase 4: Multi-Agent Collaboration Test

**Scenario**: Build full-stack SaaS app with agent swarm

**Agents & Responsibilities**:

1. **Backend Agent (Python)**
   - Writes: `auth-service.pw`, `user-service.pw`, `payment-service.pw`
   - Generates: Python FastAPI services

2. **Performance Agent (Go)**
   - Reads: `payment-service.pw`
   - Generates: High-performance Go implementation
   - Goal: 10x throughput vs Python

3. **Client Agent (TypeScript/Node.js)**
   - Reads: All .pw files
   - Generates: TypeScript SDK for frontend

4. **Infra Agent**
   - Reads: All .pw files
   - Generates: Docker Compose, K8s manifests, API Gateway configs

5. **Test Agent**
   - Reads: All .pw files
   - Generates: Integration tests that work for ANY language implementation

6. **Docs Agent**
   - Reads: All .pw files
   - Generates: OpenAPI specs, developer docs, Postman collections

**Success Criteria**:
- All agents coordinate via .pw files only
- No direct code sharing between agents
- Any service can be reimplemented in any language
- Tests pass regardless of implementation language
- Documentation auto-updates from .pw changes

---

## Phase 5: Gap Analysis & System Hardening

### Known Gaps to Test

1. **Type System Limitations**
   - Test: Complex nested types (arrays of objects, unions)
   - Test: Optional/nullable fields
   - Test: Custom type definitions

2. **Middleware/Config**
   - Test: CORS settings preservation
   - Test: Auth configuration
   - Test: Rate limiting rules

3. **Error Handling**
   - Test: Custom error types
   - Test: Error codes/messages
   - Test: HTTP status mappings

4. **Advanced Features**
   - Test: Streaming responses
   - Test: File uploads
   - Test: WebSocket endpoints
   - Test: GraphQL APIs

5. **Edge Cases**
   - Test: Empty verbs (no params or returns)
   - Test: 50+ verb agents
   - Test: Very long agent names (100+ chars)
   - Test: Unicode in names/descriptions
   - Test: Reserved keywords as verb names

### Hardening Tests

**Fuzzing**:
- Generate 1000 random .pw files → Test all generators
- Generate mutated code → Test all parsers
- Inject malformed data → Validate error handling

**Performance**:
- Parse 10MB Python file → Measure time
- Generate 100 verbs → Measure code size
- Round-trip 1000 times → Measure drift

**Security**:
- Inject code in .pw comments → Ensure sanitization
- Path traversal in file operations → Validate sandboxing
- Resource exhaustion (infinite loops in generation) → Validate timeouts

---

## Implementation Order

### Week 1: Reverse Parsers
- [x] Day 1: Python reverse parser (DONE - 100%)
- [ ] Day 2-3: Node.js reverse parser
- [ ] Day 4-5: Go reverse parser
- [ ] Day 6-7: Rust reverse parser

### Week 2: Validation & .NET
- [ ] Day 1-2: .NET reverse parser
- [ ] Day 3-4: Blind multi-agent tests (all languages)
- [ ] Day 5-7: Cross-language translation tests (20 combinations)

### Week 3: Advanced Testing
- [ ] Day 1-3: Multi-agent collaboration scenario
- [ ] Day 4-5: Gap analysis & edge cases
- [ ] Day 6-7: Performance & security hardening

---

## Success Metrics

**Per-Language Targets**:
- ✅ 95%+ round-trip accuracy
- ✅ All standard features preserved
- ✅ Generated code passes linters
- ✅ Generated code runs without errors

**Cross-Language Targets**:
- ✅ Any language → PW → Any language works
- ✅ Semantic equivalence maintained
- ✅ 90%+ information preservation

**System-Wide Targets**:
- ✅ Multi-agent collaboration proven
- ✅ All gaps documented
- ✅ Security validated
- ✅ Performance benchmarked

---

## Deliverables

### Documentation
- [ ] `NODE_REVERSE_PARSER.md` - Node.js implementation
- [ ] `GO_REVERSE_PARSER.md` - Go implementation
- [ ] `RUST_REVERSE_PARSER.md` - Rust implementation
- [ ] `DOTNET_REVERSE_PARSER.md` - .NET implementation
- [ ] `CROSS_LANGUAGE_TEST_RESULTS.md` - Translation matrix
- [ ] `MULTI_AGENT_COLLABORATION.md` - Swarm test results
- [ ] `SYSTEM_GAPS_AND_LIMITATIONS.md` - Known issues
- [ ] `PRODUCTION_READINESS_REPORT.md` - Final assessment

### Code Artifacts
- [ ] `reverse_parsers/nodejs_parser.py`
- [ ] `reverse_parsers/go_parser.py` (or Go helper program)
- [ ] `reverse_parsers/rust_parser.py` (or Rust helper)
- [ ] `reverse_parsers/dotnet_parser.py` (or C# helper)
- [ ] `tests/cross_language/` - Translation test suite
- [ ] `tests/multi_agent/` - Collaboration test scenarios

### Test Reports
- [ ] Per-language blind test reports (5 total)
- [ ] Cross-language translation results (20 combinations)
- [ ] Multi-agent collaboration report
- [ ] Gap analysis document
- [ ] Performance benchmarks
- [ ] Security audit results

---

## Current Status

**Completed**:
- ✅ Python reverse parser (100% accuracy)
- ✅ Python blind multi-agent test (100% match)
- ✅ Type inference (int, bool, float, array<T>)
- ✅ Multi-word agent name support
- ✅ Async function support

**Next Immediate Steps**:
1. Build Node.js reverse parser (2-3 days)
2. Run Node.js blind test
3. Build Go reverse parser (2-3 days)
4. Continue pattern...

**Timeline**: 3 weeks to complete full bidirectional validation across all languages

---

**Test Plan Status**: Ready for execution
**First Target**: Node.js reverse parser + blind test
**Expected Completion**: 2025-10-24
