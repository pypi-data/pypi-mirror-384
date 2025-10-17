# AssertLang SDK Package Design

This document defines the package naming, versioning, and structure for AssertLang host SDKs.

---

## Package Names

### Python SDK

**Package name**: `promptware-sdk`

**Rationale**:
- Clear, descriptive name indicating SDK purpose
- Hyphenated format follows Python packaging conventions (e.g., `google-cloud-sdk`, `aws-cdk`)
- Distinguishes from core `promptware` package (reserved for CLI/daemon)

**Import structure**:
```python
from promptware_sdk import mcp
from promptware_sdk.timeline import TimelineReader
from promptware_sdk.errors import AssertLangError, E_RUNTIME
```

**PyPI registration**:
- Package: `promptware-sdk`
- Import: `promptware_sdk` (underscores per PEP 8)

---

### Node.js SDK

**Package name**: `@promptware/sdk`

**Rationale**:
- Scoped package format follows modern npm conventions (e.g., `@google-cloud/functions`, `@aws-sdk/client-s3`)
- `@promptware` namespace reserves future packages (`@promptware/cli`, `@promptware/tools`)
- Short, memorable scope

**Import structure**:
```javascript
// ESM
import { mcp, TimelineReader } from '@promptware/sdk';

// CommonJS
const { mcp, TimelineReader } = require('@promptware/sdk');
```

**npm registration**:
- Package: `@promptware/sdk`
- Scope: `@promptware` (requires npm org/user account)

---

## Versioning Strategy

### SemVer 2.0

Both SDKs follow [Semantic Versioning 2.0](https://semver.org/):

**Format**: `MAJOR.MINOR.PATCH`

**Rules**:
- **MAJOR**: Incompatible API changes (breaking changes)
- **MINOR**: Backwards-compatible functionality additions
- **PATCH**: Backwards-compatible bug fixes

**Pre-1.0 Development**:
- Start at `0.1.0` for initial release
- Stay in `0.x.y` until Wave 4 complete (stable API surface)
- Breaking changes allowed in MINOR version bumps during `0.x` (per SemVer spec)

**Post-1.0 Stability**:
- `1.0.0` release after Wave 4 (multi-language runners, Node interpreter complete)
- Strict SemVer adherence for all `1.x+` releases

---

### Version Pinning

**SDK → Daemon compatibility**:

| SDK Version | Min Daemon Version | Notes |
| --- | --- | --- |
| `0.1.x` | `0.1.0` | Wave 2: MCP verb wrappers, timeline helpers |
| `0.2.x` | `0.2.0` | Wave 3: Policy hooks, marketplace integration |
| `0.3.x` | `0.3.0` | Wave 4: Multi-language runner support |
| `1.0.x` | `1.0.0` | Stable API, production-ready |

**Enforcement**:
- SDK checks daemon version via MCP handshake
- SDK raises `CompatibilityError` if daemon version too old
- Daemon logs warning if SDK version too new (forward compatibility)

---

## Package Structure

### Python SDK (`promptware-sdk`)

**Directory layout**:
```
promptware_sdk/
├── __init__.py           # Public API exports
├── mcp/
│   ├── __init__.py       # MCP verb wrappers
│   ├── verbs.py          # plan_create_v1, run_start_v1, etc.
│   ├── transport.py      # WebSocket/HTTP transport
│   └── envelope.py       # Request/response envelope handling
├── timeline/
│   ├── __init__.py       # Timeline event readers
│   ├── reader.py         # TimelineReader class
│   ├── events.py         # Event type definitions
│   └── schema.py         # Event schema validation
├── errors.py             # Error taxonomy (E_RUNTIME, E_POLICY, etc.)
├── types.py              # Type hints (ToolRequest, ToolResponse, etc.)
└── version.py            # SDK version metadata
```

**Public API** (`promptware_sdk/__init__.py`):
```python
from .mcp import mcp
from .timeline import TimelineReader
from .errors import AssertLangError, E_RUNTIME, E_POLICY, E_TIMEOUT
from .types import ToolRequest, ToolResponse, TimelineEvent
from .version import __version__

__all__ = [
    'mcp',
    'TimelineReader',
    'AssertLangError',
    'E_RUNTIME',
    'E_POLICY',
    'E_TIMEOUT',
    'ToolRequest',
    'ToolResponse',
    'TimelineEvent',
    '__version__',
]
```

---

### Node.js SDK (`@promptware/sdk`)

**Directory layout**:
```
packages/sdk/
├── package.json
├── tsconfig.json
├── src/
│   ├── index.ts          # Public API exports
│   ├── mcp/
│   │   ├── index.ts      # MCP verb wrappers
│   │   ├── verbs.ts      # planCreateV1, runStartV1, etc.
│   │   ├── transport.ts  # WebSocket/HTTP transport
│   │   └── envelope.ts   # Request/response envelope handling
│   ├── timeline/
│   │   ├── index.ts      # Timeline event readers
│   │   ├── reader.ts     # TimelineReader class
│   │   ├── events.ts     # Event type definitions
│   │   └── schema.ts     # Event schema validation
│   ├── errors.ts         # Error taxonomy (E_RUNTIME, E_POLICY, etc.)
│   ├── types.ts          # TypeScript type definitions
│   └── version.ts        # SDK version metadata
├── dist/                 # Compiled JavaScript output
│   ├── index.js
│   ├── index.d.ts
│   └── ...
└── test/
    └── ...
```

**Public API** (`src/index.ts`):
```typescript
export { mcp } from './mcp';
export { TimelineReader } from './timeline';
export { AssertLangError, E_RUNTIME, E_POLICY, E_TIMEOUT } from './errors';
export type { ToolRequest, ToolResponse, TimelineEvent } from './types';
export { version } from './version';
```

---

## Module Organization

### MCP Verb Wrappers

**Python** (`promptware_sdk/mcp/verbs.py`):
```python
class MCP:
    def plan_create_v1(self, source: str, format: str = 'dsl') -> dict:
        """Create execution plan from DSL or natural language."""
        pass

    def run_start_v1(self, plan: dict, state: dict = None) -> str:
        """Start plan execution, return run_id."""
        pass

    def httpcheck_assert_v1(self, url: str, status_code: int = 200) -> dict:
        """Assert HTTP endpoint health."""
        pass

    def report_finish_v1(self, run_id: str, status: str) -> dict:
        """Mark run as complete."""
        pass

# Singleton instance
mcp = MCP()
```

**Node.js** (`src/mcp/verbs.ts`):
```typescript
class MCP {
  async planCreateV1(source: string, format: 'dsl' | 'natural' = 'dsl'): Promise<object> {
    // Create execution plan
  }

  async runStartV1(plan: object, state?: object): Promise<string> {
    // Start plan execution, return runId
  }

  async httpcheckAssertV1(url: string, statusCode: number = 200): Promise<object> {
    // Assert HTTP endpoint health
  }

  async reportFinishV1(runId: string, status: string): Promise<object> {
    // Mark run complete
  }
}

export const mcp = new MCP();
```

---

### Timeline Helpers

**Python** (`promptware_sdk/timeline/reader.py`):
```python
class TimelineReader:
    def __init__(self, run_id: str):
        self.run_id = run_id

    def events(self) -> Iterator[TimelineEvent]:
        """Stream timeline events for this run."""
        pass

    def wait_for_completion(self, timeout: int = 60) -> str:
        """Block until run completes, return final status."""
        pass

    def filter_by_phase(self, phase: str) -> list[TimelineEvent]:
        """Get all events matching phase (call, let, if, etc.)."""
        pass
```

**Node.js** (`src/timeline/reader.ts`):
```typescript
class TimelineReader {
  constructor(private runId: string) {}

  async *events(): AsyncIterator<TimelineEvent> {
    // Stream timeline events for this run
  }

  async waitForCompletion(timeout: number = 60): Promise<string> {
    // Block until run completes, return final status
  }

  async filterByPhase(phase: string): Promise<TimelineEvent[]> {
    // Get all events matching phase
  }
}
```

---

### Error Taxonomy

**Python** (`promptware_sdk/errors.py`):
```python
class AssertLangError(Exception):
    """Base exception for all SDK errors."""
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")

# Standard error codes
E_RUNTIME = "E_RUNTIME"
E_POLICY = "E_POLICY"
E_TIMEOUT = "E_TIMEOUT"
E_BUILD = "E_BUILD"
E_JSON = "E_JSON"
```

**Node.js** (`src/errors.ts`):
```typescript
export class AssertLangError extends Error {
  constructor(public code: string, message: string) {
    super(`${code}: ${message}`);
    this.name = 'AssertLangError';
  }
}

export const E_RUNTIME = 'E_RUNTIME';
export const E_POLICY = 'E_POLICY';
export const E_TIMEOUT = 'E_TIMEOUT';
export const E_BUILD = 'E_BUILD';
export const E_JSON = 'E_JSON';
```

---

## Build & Distribution

### Python SDK

**Build tool**: `setuptools` via `pyproject.toml`

**`pyproject.toml`**:
```toml
[build-system]
requires = ["setuptools>=61", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "promptware-sdk"
version = "0.1.0"
description = "Host SDK for AssertLang MCP integration"
requires-python = ">=3.10"
readme = "README.md"
authors = [{ name = "AssertLang Team" }]
dependencies = [
  "requests>=2.31",
  "websocket-client>=1.7",
  "jsonschema>=4.0",
]

[project.optional-dependencies]
dev = ["pytest>=7", "black>=23", "ruff>=0.1"]

[tool.setuptools.packages.find]
where = ["src"]
```

**Build commands**:
```bash
# Build wheel
python -m build

# Install locally
pip install -e .

# Publish to PyPI
twine upload dist/*
```

---

### Node.js SDK

**Build tool**: TypeScript compiler + npm

**`package.json`**:
```json
{
  "name": "@promptware/sdk",
  "version": "0.1.0",
  "description": "Host SDK for AssertLang MCP integration",
  "main": "dist/index.js",
  "types": "dist/index.d.ts",
  "type": "module",
  "exports": {
    ".": {
      "import": "./dist/index.js",
      "require": "./dist/index.cjs",
      "types": "./dist/index.d.ts"
    }
  },
  "scripts": {
    "build": "tsc && tsc --module commonjs --outDir dist",
    "test": "jest",
    "prepublishOnly": "npm run build"
  },
  "dependencies": {
    "ws": "^8.16",
    "node-fetch": "^3.3"
  },
  "devDependencies": {
    "typescript": "^5.3",
    "@types/node": "^20.10",
    "jest": "^29.7"
  },
  "engines": {
    "node": ">=18"
  }
}
```

**Build commands**:
```bash
# Build TypeScript
npm run build

# Install locally
npm link

# Publish to npm
npm publish --access public
```

---

## Installation

### Python

```bash
# From PyPI (after publish)
pip install promptware-sdk

# From source (development)
git clone https://github.com/promptware/sdk-python.git
cd sdk-python
pip install -e .
```

### Node.js

```bash
# From npm (after publish)
npm install @promptware/sdk

# From source (development)
git clone https://github.com/promptware/sdk-js.git
cd sdk-js
npm install
npm link
```

---

## Dependencies

### Python SDK Dependencies

**Core**:
- `requests>=2.31` — HTTP transport for MCP verbs
- `websocket-client>=1.7` — WebSocket transport for timeline streaming
- `jsonschema>=4.0` — Event schema validation

**Development**:
- `pytest>=7` — Testing framework
- `black>=23` — Code formatting
- `ruff>=0.1` — Linting

---

### Node.js SDK Dependencies

**Core**:
- `ws@^8.16` — WebSocket transport
- `node-fetch@^3.3` — HTTP transport (polyfill for Node <18)

**Development**:
- `typescript@^5.3` — Type checking and compilation
- `@types/node@^20.10` — Node.js type definitions
- `jest@^29.7` — Testing framework

---

## Repository Structure

### Monorepo Option (Recommended)

```
promptware/
├── cli/                  # AssertLang CLI/daemon (existing)
├── language/             # DSL parser/interpreter (existing)
├── runners/              # Multi-language runners (existing)
├── tools/                # Tool adapters (existing)
├── sdks/                 # SDKs (new)
│   ├── python/
│   │   ├── pyproject.toml
│   │   ├── src/promptware_sdk/
│   │   └── tests/
│   └── javascript/
│       ├── package.json
│       ├── src/
│       └── test/
└── docs/                 # Documentation (existing)
```

### Separate Repos Option

```
# Core repository
github.com/promptware/promptware

# SDK repositories
github.com/promptware/sdk-python
github.com/promptware/sdk-js
```

**Recommendation**: Start with monorepo in Wave 2, split to separate repos if SDKs gain independent release cycles.

---

## Release Process

### Pre-Release Checklist

- [ ] All tests pass (`pytest` / `npm test`)
- [ ] Documentation updated (`docs/sdk/`)
- [ ] Changelog updated (`CHANGELOG.md`)
- [ ] Version bumped in `pyproject.toml` / `package.json`
- [ ] Git tag created (`v0.1.0`)

### Python Release

```bash
# Build distribution
python -m build

# Check package
twine check dist/*

# Upload to TestPyPI
twine upload --repository testpypi dist/*

# Verify install
pip install --index-url https://test.pypi.org/simple/ promptware-sdk

# Upload to PyPI
twine upload dist/*
```

### Node.js Release

```bash
# Build package
npm run build

# Test package locally
npm pack
npm install -g promptware-sdk-0.1.0.tgz

# Publish to npm
npm publish --access public
```

---

## Open Questions

1. **Namespace ownership**: Who owns `@promptware` npm scope and `promptware-sdk` PyPI package?
2. **Repository hosting**: Monorepo vs separate repos for SDKs?
3. **Release automation**: Automate version bumping and publishing via GitHub Actions?
4. **Compatibility guarantees**: Should SDK `0.x` versions maintain backward compatibility with older daemon versions?

---

## References

- **Python packaging**: https://packaging.python.org/
- **npm scoped packages**: https://docs.npmjs.com/cli/using-npm/scope
- **SemVer 2.0**: https://semver.org/
- **MCP protocol**: `docs/development-guide.md`
- **Timeline events**: `docs/runner-timeline-parity.md`

---

**Last updated**: 2025-09-29