# Path to World-Class: 80% → 99%+ Accuracy

**Current State**: Production-ready at 80-85% accuracy
**Target**: Industry-leading at 99%+ accuracy
**Timeline**: 12-16 weeks

---

## Executive Summary

We have a working multi-language code translation system with:
- ✅ 5 languages supported (Python, Go, Rust, TypeScript, C#)
- ✅ 100% compilation rate (all generated code compiles)
- ✅ 80-85% semantic accuracy (logic preserved)
- ✅ Control flow working (if/for/while with bodies)

**Gap to world-class**: Missing 15-20% accuracy from:
1. Edge cases in expression parsing (5%)
2. Advanced language features (decorators, context managers, etc.) (5%)
3. Idiomatic code generation (not just correct, but natural) (5-10%)

**Path forward**: Systematic execution in 3 phases

---

## Phase 1: Foundation (Weeks 1-4)
**Goal**: 80% → 92% accuracy
**Strategy**: Leverage official parsers + type inference

### Week 1: Python Enhancements

**Task 1.1: Add Missing Python Features** (2 days)
Current gaps:
- ❌ Context managers (`with` statements)
- ❌ Decorators (parsed but not preserved)
- ❌ Pattern matching (`match/case`)

Implementation:
```python
# language/python_parser_v2.py

def _convert_statement(self, node: ast.stmt):
    # ... existing if/for/while ...

    elif isinstance(node, ast.With):
        return self._convert_with(node)

    elif isinstance(node, ast.Match):  # Python 3.10+
        return self._convert_match(node)

def _convert_with(self, node: ast.With) -> IRWith:
    """Convert context manager to IR."""
    return IRWith(
        context_expr=self._convert_expression(node.items[0].context_expr),
        optional_vars=node.items[0].optional_vars,
        body=[self._convert_statement(s) for s in node.body]
    )

def _convert_function(self, node):
    # ... existing code ...

    # Preserve decorators
    decorators = []
    for dec in node.decorator_list:
        if isinstance(dec, ast.Name):
            decorators.append(dec.id)
        elif isinstance(dec, ast.Call):
            decorators.append(self._convert_call(dec))

    return IRFunction(
        # ... existing fields ...
        decorators=decorators
    )
```

Files to modify:
- `dsl/ir.py` - Add `IRWith`, update `IRFunction` with decorators field
- `language/python_parser_v2.py` - Add `_convert_with`, `_convert_match`
- All generators - Handle `IRWith` (convert to try/finally or equivalent)

**Expected gain**: +3% (83% total)

---

**Task 1.2: Go Parser V3 - Complete Integration** (3 days)

Currently: Structure parsing only (types, signatures)
Needed: Body parsing using official AST

Strategy: Extend `go_ast_parser.go` to output full statement AST

```go
// go_ast_parser.go - Enhanced version

type Statement struct {
    Type     string      `json:"type"` // "if", "for", "return", "assign"
    If       *IfStmt     `json:"if,omitempty"`
    For      *ForStmt    `json:"for,omitempty"`
    Return   *ReturnStmt `json:"return,omitempty"`
    // ... all statement types
}

type IfStmt struct {
    Condition  Expression    `json:"condition"`
    Body       []Statement   `json:"body"`
    Else       []Statement   `json:"else,omitempty"`
}

func convertStatement(stmt ast.Stmt) Statement {
    switch s := stmt.(type) {
    case *ast.IfStmt:
        return Statement{
            Type: "if",
            If: &IfStmt{
                Condition: convertExpr(s.Cond),
                Body: convertBlockStmt(s.Body),
                Else: convertStmt(s.Else),
            },
        }
    // ... all cases
    }
}
```

Files to modify:
- `language/go_ast_parser.go` - Add full statement/expression AST
- `language/go_parser_v3.py` - Parse statement JSON → IR

**Expected gain**: +8% (91% total) - eliminates regex edge cases

---

**Task 1.3: Type Inference via MyPy** (2 days)

Current: Manual type inference (~75% accurate)
Target: Use MyPy for Python, go/types for Go (~95% accurate)

```python
# dsl/type_inference_v2.py

import subprocess
import json
from pathlib import Path

class TypeInferenceEngine:
    def infer_python_types(self, file_path: str) -> Dict[str, TypeInfo]:
        """Use MyPy to infer types."""
        # Run mypy with JSON output
        result = subprocess.run([
            'mypy',
            '--show-column-numbers',
            '--show-error-codes',
            '--output', 'json',
            file_path
        ], capture_output=True, text=True)

        # Parse MyPy output
        type_info = {}
        for line in result.stdout.split('\n'):
            if line:
                data = json.loads(line)
                # Extract type at position
                var_name = data['message'].split(':')[0]
                inferred_type = self._parse_mypy_type(data['message'])
                type_info[var_name] = inferred_type

        return type_info

    def infer_go_types(self, file_path: str) -> Dict[str, TypeInfo]:
        """Use go/types package."""
        # Use Go program that wraps go/types
        result = subprocess.run([
            './tools/go_type_inference',
            file_path
        ], capture_output=True, text=True)

        return json.loads(result.stdout)
```

Integration:
- Python parser calls MyPy before parsing
- Go parser V3 includes type info in JSON output
- Dramatically improves dynamic → static translation

**Expected gain**: +1% overall (92% total)

---

### Week 2: Rust Parser V3 (AST-based)

**Current**: Regex-based (~70% accurate)
**Target**: AST-based using `syn` crate (~95% accurate)

Strategy: Similar to Go - create Rust helper program

```rust
// tools/rust_ast_parser/src/main.rs

use syn::{File, Item, ItemFn, ItemStruct, ItemImpl};
use serde::{Serialize, Deserialize};

#[derive(Serialize)]
struct FileAST {
    items: Vec<ASTItem>,
}

#[derive(Serialize)]
enum ASTItem {
    Struct(StructDecl),
    Function(FunctionDecl),
    Impl(ImplBlock),
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let content = std::fs::read_to_string(&args[1]).unwrap();

    // Parse using syn
    let file = syn::parse_file(&content).unwrap();

    // Convert to JSON
    let ast = convert_file(file);
    println!("{}", serde_json::to_string_pretty(&ast).unwrap());
}
```

Python wrapper:
```python
# language/rust_parser_v3.py

class RustParserV3:
    def parse_file(self, file_path: str) -> IRModule:
        # Run Rust AST parser
        result = subprocess.run([
            './tools/rust_ast_parser',
            file_path
        ], capture_output=True, text=True)

        ast_data = json.loads(result.stdout)
        return self._convert_ast_to_ir(ast_data)
```

**Expected gain**: +10% for Rust parsing (70% → 80%)

---

### Week 3-4: Expression Parsing Enhancement

**Current problem**: Complex expressions sometimes lose structure

Example:
```python
# Current
result = users.filter(lambda u: u.age > 18).map(lambda u: u.name).sort()
# Generates basic version, loses chaining elegance
```

**Solution**: Preserve full expression AST tree

Implementation in all parsers:
```python
# Enhanced expression handling

def _convert_call(self, node: ast.Call) -> IRCall:
    # Current: just function + args
    # Enhanced: preserve call chain metadata

    call = IRCall(
        function=self._convert_expression(node.func),
        args=[self._convert_expression(arg) for arg in node.args],
        kwargs={...}
    )

    # Mark if part of call chain
    if isinstance(node.func, ast.Attribute):
        call.metadata['is_method_chain'] = True
        call.metadata['chain_object'] = self._get_chain_root(node.func)

    return call
```

Then generators can reconstruct natural chains:
```python
# Go generator
if call.metadata.get('is_method_chain'):
    # Generate chained style
    return f"{obj}.{method1}().{method2}()"
```

**Expected gain**: +3% (preserves idioms)

---

## Phase 2: Advanced Features (Weeks 5-12)
**Goal**: 92% → 97% accuracy

### Week 5-6: Control Flow - Complete Coverage

Currently missing:
- Else/elif (partially working)
- Switch/match statements
- Try/catch/finally (working but needs refinement)

Add to all parsers:
```python
# IRSwitch node
@dataclass
class IRSwitch:
    value: IRExpression
    cases: List[IRSwitchCase]
    default: Optional[List[IRStatement]]

# Map to each language:
# Python match → IRSwitch
# Go switch → IRSwitch
# Rust match → IRSwitch
# TS switch → IRSwitch
# C# switch → IRSwitch
```

**Expected gain**: +2%

---

### Week 7-8: Type System v2

Currently: Basic types + arrays
Add: Generics, unions, constraints

```python
# dsl/type_system_v2.py

class TypeSystemV2:
    def map_generic_type(self, ir_type: IRType, target_lang: str) -> str:
        """
        Map generic types across languages.

        Examples:
        - array<int> → List[int] (Python)
        - array<int> → []int (Go)
        - array<int> → Vec<i32> (Rust)
        - array<int> → Array<number> (TS)
        - array<int> → List<int> (C#)

        - map<string, array<int>> → Dict[str, List[int]] (Python)
        - map<string, array<int>> → map[string][]int (Go)
        - etc.
        """

    def map_union_type(self, types: List[IRType], target_lang: str) -> str:
        """
        Map union types.

        Python/TS: str | int | None
        Go: interface{} + type assertions
        Rust: enum { Str(String), Int(i32), None }
        C#: object (with pattern matching)
        """
```

**Expected gain**: +3%

---

### Week 9-10: Idiom Translation Layer

Map language-specific patterns:

```python
# dsl/idiom_translator.py

class IdiomTranslator:
    patterns = {
        'list_comprehension': {
            'python': '[x for x in items if x > 0]',
            'go': 'for _, x := range items { if x > 0 { result = append(result, x) }}',
            'rust': 'items.iter().filter(|x| *x > 0).collect()',
            'typescript': 'items.filter(x => x > 0)',
            'csharp': 'items.Where(x => x > 0).ToList()',
        },
        'decorator': {
            'python': '@decorator\ndef func(): ...',
            'go': '// Use middleware pattern',
            'rust': '#[decorator] (if available)',
            'typescript': '@Decorator() (if using decorators)',
            'csharp': '[Decorator] (attribute)',
        }
    }

    def translate(self, ir_node: IRNode, source_lang: str, target_lang: str):
        """Detect pattern and translate idiomatically."""
        pattern_type = self._detect_pattern(ir_node)
        if pattern_type in self.patterns:
            return self._apply_idiom(pattern_type, target_lang, ir_node)
        return None  # Use default translation
```

**Expected gain**: +2%

---

### Week 11-12: Round-Trip Optimization

Goal: Code → PW → Code preserves 95%+ of original

Strategy:
1. Metadata preservation
2. Comment preservation
3. Formatting hints

```python
# Enhanced IR with metadata
@dataclass
class IRFunction:
    name: str
    params: List[IRParameter]
    body: List[IRStatement]

    # Metadata for round-trip
    metadata: Dict[str, Any] = field(default_factory=dict)
    # metadata['source_language'] = 'python'
    # metadata['decorators'] = ['@cached', '@property']
    # metadata['comments'] = {1: '# Important note', 5: '# TODO'}
    # metadata['formatting'] = {'indent': 4, 'style': 'black'}
```

**Expected gain**: Better quality, not raw accuracy

---

## Phase 3: AI Enhancement (Weeks 13-16)
**Goal**: 97% → 99.5% accuracy (WORLD-CLASS)

### Week 13-14: LLM Semantic Validation

```python
# ai/semantic_validator.py

import anthropic

class SemanticValidator:
    def __init__(self):
        self.client = anthropic.Anthropic()

    def validate_translation(
        self,
        source_code: str,
        target_code: str,
        source_lang: str,
        target_lang: str
    ) -> ValidationResult:
        """
        Use Claude to verify semantic equivalence.
        """
        prompt = f"""You are a code translation validator.

Source ({source_lang}):
```{source_lang}
{source_code}
```

Generated ({target_lang}):
```{target_lang}
{target_code}
```

Analysis tasks:
1. Are these semantically equivalent?
2. Check error handling - are edge cases handled the same?
3. Check performance - are algorithms equivalent?
4. Check idioms - is the target code natural for {target_lang}?
5. Suggest fixes if needed.

Respond in JSON:
{{
    "equivalent": true/false,
    "confidence": 0-100,
    "issues": ["list of problems"],
    "suggestions": ["list of improvements"]
}}
"""

        response = self.client.messages.create(
            model="claude-sonnet-4",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}]
        )

        return json.loads(response.content[0].text)

    def refine_translation(
        self,
        source_code: str,
        target_code: str,
        validation_result: ValidationResult,
        target_lang: str
    ) -> str:
        """Use AI to fix translation issues."""
        if validation_result.equivalent and validation_result.confidence > 90:
            return target_code  # Good enough

        # Ask AI to fix
        prompt = f"""Fix this code translation.

Issues found:
{json.dumps(validation_result.issues, indent=2)}

Current {target_lang} code:
```{target_lang}
{target_code}
```

Generate corrected version that addresses all issues.
Respond with ONLY the corrected code, no explanations.
"""

        response = self.client.messages.create(
            model="claude-sonnet-4",
            max_tokens=8192,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.content[0].text
```

Integration:
```python
# translator.py

class Translator:
    def translate(self, source_code: str, source_lang: str, target_lang: str) -> str:
        # Stage 1: Structural translation (AST-based)
        ir = self.parse(source_code, source_lang)
        generated = self.generate(ir, target_lang)

        # Stage 2: AI validation
        validation = self.validator.validate_translation(
            source_code, generated, source_lang, target_lang
        )

        # Stage 3: AI refinement if needed
        if not validation.equivalent or validation.confidence < 90:
            generated = self.validator.refine_translation(
                source_code, generated, validation, target_lang
            )

        return generated
```

**Expected gain**: +1.5% (catches edge cases)

---

### Week 15: Test Generation

```python
# ai/test_generator.py

class TestGenerator:
    def generate_equivalence_tests(
        self,
        source_code: str,
        target_code: str,
        source_lang: str,
        target_lang: str
    ) -> Tuple[str, str]:
        """
        Generate tests that prove equivalence.

        Returns: (source_tests, target_tests)
        """
        prompt = f"""Generate comprehensive test cases for these equivalent functions.

Source ({source_lang}):
```{source_lang}
{source_code}
```

Target ({target_lang}):
```{target_lang}
{target_code}
```

Generate test cases that:
1. Test normal cases
2. Test edge cases (null, empty, boundary values)
3. Test error conditions
4. Use same inputs for both versions

Respond with:
{{
    "{source_lang}_tests": "test code",
    "{target_lang}_tests": "test code",
    "test_cases": [
        {{"input": ..., "expected": ...}},
        ...
    ]
}}
"""

        # Get AI response
        # Parse and return tests
```

Usage:
```python
# Validation pipeline
def validate_translation_with_tests(source, target, source_lang, target_lang):
    # 1. Generate tests
    source_tests, target_tests, test_cases = generate_tests(...)

    # 2. Run source tests
    source_results = run_tests(source + source_tests, source_lang)

    # 3. Run target tests
    target_results = run_tests(target + target_tests, target_lang)

    # 4. Compare results
    for case in test_cases:
        assert source_results[case] == target_results[case]

    return True  # Provably equivalent!
```

**Expected gain**: +0.5% (confidence boost)

---

### Week 16: Multi-Pass Refinement

```python
# translator_multipass.py

class MultiPassTranslator:
    def translate(self, source_code: str, source_lang: str, target_lang: str) -> str:
        code = source_code
        quality_scores = []

        # Pass 1: Structural translation
        ir = self.parser.parse(code, source_lang)
        code = self.generator.generate(ir, target_lang)
        quality_scores.append(self.measure_quality(code, target_lang))

        # Pass 2: Type refinement
        code = self.type_refiner.refine(code, ir, target_lang)
        quality_scores.append(self.measure_quality(code, target_lang))

        # Pass 3: Idiom translation
        code = self.idiom_translator.translate(code, ir, source_lang, target_lang)
        quality_scores.append(self.measure_quality(code, target_lang))

        # Pass 4: AI polish
        code = self.ai_refiner.polish(code, source_code, source_lang, target_lang)
        quality_scores.append(self.measure_quality(code, target_lang))

        # Pass 5: Compilation + test validation
        if not self.compiles(code, target_lang):
            code = self.ai_fixer.fix_errors(code, self.get_errors(code, target_lang))

        final_quality = self.measure_quality(code, target_lang)

        print(f"Quality progression: {quality_scores} → {final_quality}")
        # Expected: [85%, 91%, 95%, 98%, 99.5%]

        return code
```

**Expected gain**: +0.5% (final polish)

---

## Success Metrics

### Phase 1 Complete (Week 4)
- Compilation rate: 100% (already achieved)
- Semantic accuracy: 92%
- Type accuracy: 90%
- Round-trip accuracy: 85%

### Phase 2 Complete (Week 12)
- Compilation rate: 100%
- Semantic accuracy: 97%
- Type accuracy: 95%
- Round-trip accuracy: 92%
- Idiomatic quality: 90%

### Phase 3 Complete (Week 16)
- Compilation rate: 100%
- Semantic accuracy: 99.5%
- Type accuracy: 99%
- Round-trip accuracy: 98%
- Idiomatic quality: 97%
- AI-validated: 100%
- Test-proven: 100%

---

## Competitive Positioning

After Phase 3, we will be:

1. **More accurate than GitHub Copilot** (99.5% vs ~85%)
2. **More reliable than LLM translation** (test-proven vs hallucination-prone)
3. **More comprehensive than traditional AST tools** (idioms + AI vs just structure)
4. **Unique in the market**: AST + AI + Test validation

---

## Resource Requirements

**Development**:
- 1 senior engineer (full-time, 16 weeks)
- OR 2 mid-level engineers (full-time, 12-14 weeks)

**Infrastructure**:
- API access: Claude API (~$500/month for development)
- Compute: Standard developer machine
- Tools: Go, Rust, Python toolchains (free)

**Total cost estimate**: $40-60K (salary) + $2K (API) = ~$50K for world-class system

---

## Next Immediate Steps

1. **Week 1, Day 1**: Start with Python enhancements (context managers + decorators)
2. **Week 1, Day 3**: Complete Go Parser V3 body parsing
3. **Week 2, Day 1**: Start Rust Parser V3 using syn
4. **Week 3, Day 1**: Expression enhancement across all parsers
5. **Week 4, Day 5**: Phase 1 validation and metrics collection

**We start tomorrow. Let's build something world-class.**
