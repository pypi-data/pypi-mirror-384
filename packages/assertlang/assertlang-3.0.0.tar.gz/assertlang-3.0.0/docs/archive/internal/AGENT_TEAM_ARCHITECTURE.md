# Agent Team Architecture - AssertLang V2 Development

**Last Updated**: 2025-10-04
**Purpose**: Professional multi-agent development team for building universal code translation system
**Approach**: Specialized agents working in parallel, supervised by architect agent

---

## 🏗️ Team Structure (Inspired by LLVM/TypeScript/Babel)

### Based on Research:
- **LLVM**: Area teams with maintainers, distributed development model
- **TypeScript**: Corporate-backed with institutional resources
- **Babel**: Community-driven with core team + contributors
- **SWC**: Small core team with growing community

### Our Approach:
**Hybrid model** - Architect supervises specialized agents working in parallel, similar to LLVM's area teams but fully autonomous.

---

## 👥 Agent Team Roster (9 Specialized Agents)

```
┌─────────────────────────────────────────────────────────────┐
│                    ARCHITECT AGENT (You)                     │
│  • Overall coordination and supervision                      │
│  • Architecture decisions                                    │
│  • Quality gates and integration                            │
│  • Conflict resolution                                       │
└─────────────────────────────────────────────────────────────┘
                            │
            ┌───────────────┼───────────────┐
            ▼               ▼               ▼
┌────────────────┐  ┌──────────────┐  ┌───────────────┐
│ IR ARCHITECT   │  │ TYPE SYSTEM  │  │ GRAMMAR       │
│    AGENT       │  │    AGENT     │  │ DESIGNER      │
│                │  │              │  │   AGENT       │
│ • IR design    │  │ • Type       │  │               │
│ • Data         │  │   mappings   │  │ • PW DSL 2.0  │
│   structures   │  │ • Inference  │  │   grammar     │
│ • Validation   │  │   engine     │  │ • Syntax      │
└────────────────┘  └──────────────┘  └───────────────┘

┌────────────────────────────────────────────────────────────┐
│              LANGUAGE TEAM (5 Parser Agents)               │
├────────────┬────────────┬────────────┬────────────┬────────┤
│  Python    │  Node.js   │    Go      │   Rust     │  .NET  │
│  Parser    │  Parser    │  Parser    │  Parser    │ Parser │
│   Agent    │   Agent    │   Agent    │   Agent    │  Agent │
│            │            │            │            │        │
│ • Python   │ • JS/TS    │ • Go       │ • Rust     │ • C#   │
│   → IR     │   → IR     │   → IR     │   → IR     │  → IR  │
│ • Type     │ • Type     │ • Type     │ • Type     │ • Type │
│   inference│   inference│   inference│   inference│  infer │
└────────────┴────────────┴────────────┴────────────┴────────┘

┌────────────────────────────────────────────────────────────┐
│            LANGUAGE TEAM (5 Generator Agents)              │
├────────────┬────────────┬────────────┬────────────┬────────┤
│  Python    │  Node.js   │    Go      │   Rust     │  .NET  │
│ Generator  │ Generator  │ Generator  │ Generator  │  Gen   │
│   Agent    │   Agent    │   Agent    │   Agent    │  Agent │
│            │            │            │            │        │
│ • IR →     │ • IR →     │ • IR →     │ • IR →     │ • IR → │
│   Python   │   JS/TS    │   Go       │   Rust     │   C#   │
│ • Idiom    │ • Idiom    │ • Idiom    │ • Idiom    │ • Idiom│
│   trans    │   trans    │   trans    │   trans    │  trans │
└────────────┴────────────┴────────────┴────────────┴────────┘

┌────────────────────────────────────────────────────────────┐
│                    QUALITY TEAM                            │
├──────────────────────────┬─────────────────────────────────┤
│   TEST ENGINEER AGENT    │   INTEGRATION AGENT            │
│                          │                                │
│ • Write test suites      │ • Component integration       │
│ • Round-trip validation  │ • End-to-end testing          │
│ • Cross-language tests   │ • Performance validation      │
│ • Golden fixtures        │ • Documentation               │
└──────────────────────────┴─────────────────────────────────┘
```

---

## 📋 Agent Specifications

### 1. IR Architect Agent
**Role**: Design and implement intermediate representation

**Responsibilities**:
- Design IR data structures (`dsl/ir.py`)
- Define IR node types (Module, Function, Class, Expression, etc.)
- Build IR validator (semantic checks)
- Create IR serialization/deserialization
- Maintain IR documentation

**Deliverables**:
- `dsl/ir.py` - Complete IR implementation
- `dsl/validator.py` - IR semantic validator
- `tests/test_ir.py` - IR unit tests
- `docs/IR_SPECIFICATION.md` - IR documentation

**Timeline**: Week 1-2

**Dependencies**: None (foundational)

---

### 2. Type System Agent
**Role**: Design and implement universal type system

**Responsibilities**:
- Define universal type primitives
- Create cross-language type mappings
- Build type inference engine
- Implement type validation
- Handle dynamic ↔ static type bridging

**Deliverables**:
- `dsl/type_system.py` - Type system implementation
- `tests/test_type_system.py` - Type system tests
- `docs/TYPE_SYSTEM.md` - Type system documentation

**Timeline**: Week 3-4

**Dependencies**: IR Architect (needs IR node definitions)

---

### 3. Grammar Designer Agent
**Role**: Design PW DSL 2.0 grammar and parser

**Responsibilities**:
- Define complete PW DSL 2.0 grammar (BNF)
- Build PW parser (PW text → IR)
- Build PW generator (IR → PW text)
- Create syntax examples and documentation
- Define error messages and recovery

**Deliverables**:
- `dsl/pw_parser.py` - PW parser
- `dsl/pw_generator.py` - PW generator
- `docs/PW_DSL_2.0_SPEC.md` - Complete grammar spec
- `tests/test_pw_parser.py` - Parser tests

**Timeline**: Week 1-2

**Dependencies**: IR Architect (needs IR definition)

---

### 4-8. Language Parser Agents (5 agents)
**Role**: Parse arbitrary code in specific language → IR

**Agent 4: Python Parser Agent**
- Parse arbitrary Python code → IR
- AST extraction and transformation
- Python-specific type inference
- Handle Python idioms (decorators, generators, etc.)

**Agent 5: Node.js Parser Agent**
- Parse arbitrary JS/TS code → IR
- Handle both JavaScript and TypeScript
- TS type annotation extraction
- Handle async/await, promises

**Agent 6: Go Parser Agent**
- Parse arbitrary Go code → IR
- Handle goroutines and channels
- Interface and struct extraction
- Error handling patterns

**Agent 7: Rust Parser Agent**
- Parse arbitrary Rust code → IR
- Handle ownership and lifetimes (abstract in IR)
- Trait and impl extraction
- Pattern matching translation

**Agent 8: .NET Parser Agent**
- Parse arbitrary C# code → IR
- LINQ expression handling
- Async/await patterns
- Property and event extraction

**Common Deliverables (each agent)**:
- `language/{lang}_parser_v2.py` - Parser implementation
- `tests/test_{lang}_parser_v2.py` - Parser tests
- `docs/{LANG}_PARSER_GUIDE.md` - Language-specific docs

**Timeline**: Weeks 5-10 (can work in parallel)

**Dependencies**: IR Architect, Type System, Grammar Designer

---

### 9-13. Language Generator Agents (5 agents)
**Role**: Generate arbitrary code in specific language from IR

**Agent 9: Python Generator Agent**
- IR → idiomatic Python code
- Generate type annotations
- Python idiom generation (list comprehensions, etc.)
- Package imports and structure

**Agent 10: Node.js Generator Agent**
- IR → idiomatic JS/TS code
- TypeScript type generation
- Async/await generation
- Module exports and imports

**Agent 11: Go Generator Agent**
- IR → idiomatic Go code
- Interface generation
- Error handling pattern generation
- Goroutine translation

**Agent 12: Rust Generator Agent**
- IR → idiomatic Rust code
- Ownership/lifetime annotation generation
- Trait implementation
- Result/Option pattern generation

**Agent 13: .NET Generator Agent**
- IR → idiomatic C# code
- Property and event generation
- LINQ expression generation
- Async/await pattern generation

**Common Deliverables (each agent)**:
- `language/{lang}_generator_v2.py` - Generator implementation
- `tests/test_{lang}_generator_v2.py` - Generator tests
- `docs/{LANG}_GENERATOR_GUIDE.md` - Language-specific docs

**Timeline**: Weeks 10-14 (can work in parallel)

**Dependencies**: IR Architect, Type System, Grammar Designer

---

### 14. Test Engineer Agent
**Role**: Create comprehensive test infrastructure

**Responsibilities**:
- Design test strategy
- Write unit tests for all components
- Create round-trip tests (Code → PW → Code)
- Create cross-language tests (Python → PW → Go)
- Build golden fixture library
- Performance benchmarking

**Deliverables**:
- `tests/test_roundtrip_v2.py` - Round-trip tests
- `tests/test_cross_language.py` - Cross-language tests
- `tests/fixtures/` - Golden test fixtures
- `docs/TESTING_STRATEGY.md` - Test documentation

**Timeline**: Weeks 14-16 (ongoing from week 5)

**Dependencies**: All other agents (needs their outputs to test)

---

### 15. Integration Agent
**Role**: Integrate all components and ensure they work together

**Responsibilities**:
- Component integration
- End-to-end workflow validation
- Performance optimization
- Documentation generation
- V1 compatibility verification
- CI/CD pipeline updates

**Deliverables**:
- `docs/ARCHITECTURE_V2.md` - System architecture
- `docs/INTEGRATION_GUIDE.md` - Integration documentation
- `README.md` updates - Public documentation
- `.github/workflows/` - CI/CD updates

**Timeline**: Weeks 14-16

**Dependencies**: All other agents (integrates everything)

---

## 🔄 Development Workflow

### Phase 1: Foundation (Weeks 1-2)

**Parallel Work**:
1. IR Architect Agent → `dsl/ir.py`
2. Grammar Designer Agent → `dsl/pw_parser.py`, `docs/PW_DSL_2.0_SPEC.md`

**Coordination**:
- Daily sync between IR and Grammar agents (IR changes affect parser)
- Architect reviews and approves IR design
- Test Engineer starts planning test strategy

**Outputs**:
- IR data structures complete
- PW DSL 2.0 grammar complete
- Parser working (PW text → IR → PW text round-trip)

---

### Phase 2: Type System (Weeks 3-4)

**Serial Work** (depends on IR):
1. Type System Agent → `dsl/type_system.py`

**Parallel Work**:
1. Test Engineer → Start building test fixtures
2. Integration Agent → Start architecture documentation

**Coordination**:
- Type System agent works closely with IR Architect
- Test Engineer creates type system test cases

**Outputs**:
- Universal type system complete
- Cross-language type mappings validated
- Type inference engine working

---

### Phase 3: Parsers (Weeks 5-10)

**Parallel Work** (5 agents working simultaneously):
1. Python Parser Agent → `language/python_parser_v2.py`
2. Node.js Parser Agent → `language/nodejs_parser_v2.py`
3. Go Parser Agent → `language/go_parser_v2.py`
4. Rust Parser Agent → `language/rust_parser_v2.py`
5. .NET Parser Agent → `language/dotnet_parser_v2.py`

**Coordination**:
- Weekly sync meetings (all parser agents + architect)
- Share common patterns and utilities
- Test Engineer validates each parser as it's built
- Architect reviews code quality and consistency

**Outputs**:
- 5 language parsers complete
- Arbitrary code → IR working for all languages
- Parser test suites passing

---

### Phase 4: Generators (Weeks 10-14)

**Parallel Work** (5 agents working simultaneously):
1. Python Generator Agent → `language/python_generator_v2.py`
2. Node.js Generator Agent → `language/nodejs_generator_v2.py`
3. Go Generator Agent → `language/go_generator_v2.py`
4. Rust Generator Agent → `language/rust_generator_v2.py`
5. .NET Generator Agent → `language/dotnet_generator_v2.py`

**Coordination**:
- Weekly sync meetings (all generator agents + architect)
- Share idiom translation patterns
- Test Engineer validates each generator as it's built
- Architect ensures code quality and idiom correctness

**Outputs**:
- 5 language generators complete
- IR → arbitrary code working for all languages
- Generator test suites passing

---

### Phase 5: Testing & Integration (Weeks 14-16)

**Parallel Work**:
1. Test Engineer → Comprehensive test suite
2. Integration Agent → Component integration and docs

**Coordination**:
- All agents available for bug fixes
- Daily standups to address issues
- Architect prioritizes fixes and optimizations

**Outputs**:
- Full test suite passing
- Round-trip tests: 90%+ accuracy
- Cross-language tests: 90%+ semantic equivalence
- Documentation complete
- System integrated and production-ready

---

## 🎯 Agent Coordination Strategy

### Communication Channels

**1. Shared State** (Git repo)
- All agents commit to `raw-code-parsing` branch
- Clear file ownership (no conflicts)
- Atomic commits with descriptive messages

**2. Status Updates** (Current_Work.md)
- Each agent updates their section daily
- Architect reviews progress
- Blockers clearly documented

**3. Design Decisions** (docs/DECISIONS.md)
- Major design decisions documented
- Architect approves significant changes
- Rationale captured for future reference

---

### Daily Workflow

**Morning** (Start of work session):
1. Architect reviews overnight progress (git log)
2. Architect checks Current_Work.md for blockers
3. Architect assigns tasks for the day
4. Agents start parallel work

**Afternoon** (Mid-session):
1. Agents commit progress
2. Architect reviews commits
3. Architect resolves conflicts/questions
4. Agents continue work

**Evening** (End of session):
1. Agents commit final work
2. Agents update Current_Work.md with status
3. Architect reviews day's progress
4. Architect plans next day's work

---

### Conflict Resolution

**Technical Conflicts**:
- Architect makes final decision
- Document decision in DECISIONS.md
- Update affected agents

**Resource Conflicts** (file ownership):
- Clear file ownership matrix (see below)
- No two agents edit same file simultaneously
- Coordinate through Architect if overlap needed

---

## 📁 File Ownership Matrix

| File/Directory | Owner Agent | Collaborators |
|----------------|-------------|---------------|
| `dsl/ir.py` | IR Architect | Type System |
| `dsl/type_system.py` | Type System | IR Architect |
| `dsl/pw_parser.py` | Grammar Designer | IR Architect |
| `dsl/pw_generator.py` | Grammar Designer | IR Architect |
| `dsl/validator.py` | IR Architect | All |
| `language/python_parser_v2.py` | Python Parser | Type System |
| `language/python_generator_v2.py` | Python Generator | Type System |
| `language/nodejs_parser_v2.py` | Node Parser | Type System |
| `language/nodejs_generator_v2.py` | Node Generator | Type System |
| `language/go_parser_v2.py` | Go Parser | Type System |
| `language/go_generator_v2.py` | Go Generator | Type System |
| `language/rust_parser_v2.py` | Rust Parser | Type System |
| `language/rust_generator_v2.py` | Rust Generator | Type System |
| `language/dotnet_parser_v2.py` | .NET Parser | Type System |
| `language/dotnet_generator_v2.py` | .NET Generator | Type System |
| `tests/*` | Test Engineer | All |
| `docs/*` | Integration Agent | All |

---

## 🚀 Agent Launch Protocol

### How to Launch an Agent

**Using Task Tool**:
```
Task:
  subagent_type: general-purpose
  description: "Build IR data structures"
  prompt: "You are the IR Architect Agent for AssertLang V2.

  Your mission: Design and implement the intermediate representation (IR)
  for the universal code translation system.

  Read these files first:
  - CLAUDE.md (V2 architecture)
  - Current_Work.md (current status)
  - AGENT_TEAM_ARCHITECTURE.md (your role and responsibilities)

  Your deliverables:
  1. dsl/ir.py - Complete IR data structures
  2. dsl/validator.py - IR semantic validator
  3. tests/test_ir.py - IR unit tests
  4. Update Current_Work.md with your progress

  Follow these principles:
  - Real implementations only (no placeholders)
  - Test-driven development
  - Document all design decisions
  - Commit frequently with clear messages

  When complete, report back with:
  - Files created
  - Test results
  - Any blockers or questions
  - Next recommended steps"
```

---

## 📊 Success Metrics

### Individual Agent Success
- Code quality: Passes linting and type checking
- Test coverage: 90%+ for owned files
- Documentation: All public APIs documented
- Timeline: Completes deliverables on schedule

### Team Success
- Integration: All components work together
- Round-trip accuracy: 90%+ (Code → PW → Code)
- Cross-language accuracy: 90%+ semantic equivalence
- Performance: Parsers process 1000+ LOC/second
- V1 compatibility: No breaking changes to existing MCP functionality

---

## 🎓 Agent Training Materials

Each agent receives:
1. **CLAUDE.md** - Full V2 architecture and roadmap
2. **Current_Work.md** - Current project status
3. **AGENT_TEAM_ARCHITECTURE.md** - This file (team structure)
4. **Language-specific research** - Links to LLVM, CrossTL, transpiler guides
5. **Role-specific examples** - Sample code from V1 to study

---

## 🔧 Tools for Agents

Each agent has access to:
- **Read**: Read files from codebase
- **Write**: Create new files
- **Edit**: Modify existing files
- **Bash**: Run tests, linters, formatters
- **Glob/Grep**: Search codebase
- **WebFetch/WebSearch**: Research external resources

---

## 📝 Next Steps for Architect (You)

1. **Launch IR Architect Agent** (Week 1, Day 1)
   - Assign: Build `dsl/ir.py`
   - Monitor: Review commits, answer questions
   - Integrate: Approve IR design

2. **Launch Grammar Designer Agent** (Week 1, Day 1 - parallel)
   - Assign: Build `dsl/pw_parser.py` and grammar spec
   - Monitor: Ensure alignment with IR design
   - Integrate: Review grammar completeness

3. **Launch Type System Agent** (Week 3, Day 1)
   - Assign: Build `dsl/type_system.py`
   - Monitor: Ensure type mappings are correct
   - Integrate: Validate with IR and parsers

4. **Launch 5 Parser Agents** (Week 5, Day 1 - all parallel)
   - Assign: Each builds language-specific parser
   - Monitor: Weekly sync meetings, code reviews
   - Integrate: Ensure consistency across languages

5. **Launch 5 Generator Agents** (Week 10, Day 1 - all parallel)
   - Assign: Each builds language-specific generator
   - Monitor: Weekly sync meetings, idiom reviews
   - Integrate: Ensure idiomatic code generation

6. **Launch Test Engineer Agent** (Week 5, Day 1 - ongoing)
   - Assign: Build comprehensive test suite
   - Monitor: Daily test reports
   - Integrate: Validate all components

7. **Launch Integration Agent** (Week 14, Day 1)
   - Assign: Integrate all components, write docs
   - Monitor: End-to-end validation
   - Integrate: Final production readiness

---

**Last Updated**: 2025-10-04
**Status**: Agent team architecture designed and ready for deployment
**Next Action**: Launch first two agents (IR Architect + Grammar Designer)
**Timeline**: 16-week multi-agent development cycle
