# AssertLang SDK Guide

Official client libraries for calling AssertLang MCP agents.

## Installation

### Python

```bash
pip install promptware
```

### Node.js

```bash
npm install @promptware/client
```

## Quick Start

### Python

```python
from promptware.sdk import Agent

# Create agent client
agent = Agent("http://localhost:3000")

# Call verbs with dot notation
result = agent.user.create(email="test@example.com", name="Test User")
print(result)

# Get user
user = agent.user.get(user_id="123")
print(user)
```

### Node.js

```javascript
import { Agent } from '@promptware/client/sdk';

// Create agent client
const agent = new Agent('http://localhost:3000');

// Call verbs with dot notation
const result = await agent.user.create({
  email: 'test@example.com',
  name: 'Test User'
});
console.log(result);

// Get user
const user = await agent.user.get({ userId: '123' });
console.log(user);
```

## Features

### Dynamic Verb Discovery

SDKs automatically discover available verbs from the agent:

**Python:**
```python
agent = Agent("http://localhost:3000")

# List all verbs
verbs = agent.list_verbs()
print(verbs)  # ['user.create@v1', 'user.get@v1', ...]

# Get verb schema
schema = agent.get_verb_schema("user.create@v1")
print(schema['inputSchema'])
```

**Node.js:**
```javascript
const agent = new Agent('http://localhost:3000');

// List all verbs
const verbs = await agent.listVerbs();
console.log(verbs);  // ['user.create@v1', 'user.get@v1', ...]

// Get verb schema
const schema = await agent.getVerbSchema('user.create@v1');
console.log(schema.inputSchema);
```

### Health Checks

Check agent health and readiness:

**Python:**
```python
# Liveness check
health = agent.health()
print(health)  # {'status': 'alive', 'uptime_seconds': 3600, ...}

# Readiness check
ready = agent.ready()
print(ready)  # {'status': 'ok', 'checks': {...}, ...}
```

**Node.js:**
```javascript
// Liveness check
const health = await agent.health();
console.log(health);  // {status: 'alive', uptime_seconds: 3600, ...}

// Readiness check
const ready = await agent.ready();
console.log(ready);  // {status: 'ok', checks: {...}, ...}
```

### Automatic Retries

SDKs automatically retry failed requests with exponential backoff:

**Python:**
```python
agent = Agent(
    "http://localhost:3000",
    max_retries=5,           # Retry up to 5 times
    retry_delay=2.0,         # Initial delay: 2 seconds
    timeout=60               # Request timeout: 60 seconds
)

# Automatically retries on network errors
result = agent.user.create(email="test@example.com", name="Test")
```

**Node.js:**
```javascript
const agent = new Agent('http://localhost:3000', {
  maxRetries: 5,            // Retry up to 5 times
  retryDelay: 2000,         // Initial delay: 2 seconds
  timeout: 60000            // Request timeout: 60 seconds
});

// Automatically retries on network errors
const result = await agent.user.create({
  email: 'test@example.com',
  name: 'Test'
});
```

### Circuit Breaker

SDKs include circuit breaker pattern for fault tolerance:

**Python:**
```python
from promptware.sdk import Agent, CircuitBreakerError

agent = Agent(
    "http://localhost:3000",
    circuit_breaker_threshold=10,  # Open after 10 failures
    circuit_breaker_timeout=60     # Try again after 60 seconds
)

try:
    result = agent.user.create(email="test@example.com", name="Test")
except CircuitBreakerError:
    print("Service unavailable - circuit breaker is open")
```

**Node.js:**
```javascript
import { Agent, CircuitBreakerError } from '@promptware/client/sdk';

const agent = new Agent('http://localhost:3000', {
  circuitBreakerThreshold: 10,  // Open after 10 failures
  circuitBreakerTimeout: 60000  // Try again after 60 seconds
});

// Listen to circuit breaker events
agent.on('circuit-breaker-state', (state) => {
  console.log('Circuit breaker state:', state);
});

try {
  const result = await agent.user.create({
    email: 'test@example.com',
    name: 'Test'
  });
} catch (error) {
  if (error instanceof CircuitBreakerError) {
    console.log('Service unavailable - circuit breaker is open');
  }
}
```

### Connection Pooling

SDKs use connection pooling for better performance:

**Python:**
```python
agent = Agent("http://localhost:3000")

# Reuse same connection for multiple requests
for i in range(100):
    user = agent.user.get(user_id=str(i))
```

**Node.js:**
```javascript
const agent = new Agent('http://localhost:3000');

// Reuse same connection for multiple requests
for (let i = 0; i < 100; i++) {
  const user = await agent.user.get({ userId: String(i) });
}
```

### Context Managers

Use context managers for automatic cleanup:

**Python:**
```python
from promptware.sdk import Agent

with Agent("http://localhost:3000") as agent:
    result = agent.user.create(email="test@example.com", name="Test")
    # Connection automatically closed when exiting context
```

**Node.js:**
```javascript
// Node.js doesn't have context managers, but you can use try/finally
const agent = new Agent('http://localhost:3000');
try {
  const result = await agent.user.create({
    email: 'test@example.com',
    name: 'Test'
  });
} finally {
  agent.close();
}
```

## API Reference

### Agent Class

#### Constructor

**Python:**
```python
Agent(
    base_url: str,
    timeout: int = 30,
    max_retries: int = 3,
    retry_delay: float = 1.0,
    enable_logging: bool = False
)
```

**Node.js:**
```typescript
new Agent(
  baseUrl: string,
  options?: {
    timeout?: number,           // Default: 30000
    maxRetries?: number,        // Default: 3
    retryDelay?: number,        // Default: 1000
    retryBackoff?: number,      // Default: 2.0
    circuitBreakerThreshold?: number,  // Default: 5
    circuitBreakerTimeout?: number,    // Default: 60000
    enableLogging?: boolean     // Default: false
  }
)
```

#### Methods

| Method | Description | Returns |
|--------|-------------|---------|
| `health()` | Check liveness | `Promise<HealthStatus>` |
| `ready()` | Check readiness | `Promise<ReadinessStatus>` |
| `discover()` | Discover verbs | `Promise<VerbSchema[]>` |
| `list_verbs()` | List verb names | `Promise<string[]>` |
| `get_verb_schema(name)` | Get verb schema | `Promise<VerbSchema \| null>` |
| `call_verb(name, params)` | Call verb | `Promise<any>` |
| `close()` | Close connection | `void` |

### Exceptions / Errors

**Python:**
```python
from promptware.sdk import (
    AgentError,           # Base error
    ConnectionError,      # Connection failed
    TimeoutError,         # Request timed out
    VerbNotFoundError,    # Verb doesn't exist
    InvalidParamsError,   # Invalid parameters
    CircuitBreakerError   # Circuit breaker open
)
```

**Node.js:**
```javascript
import {
  AgentError,           // Base error
  ConnectionError,      // Connection failed
  TimeoutError,         // Request timed out
  VerbNotFoundError,    // Verb doesn't exist
  InvalidParamsError,   // Invalid parameters
  CircuitBreakerError   // Circuit breaker open
} from '@promptware/client/sdk';
```

## Examples

### Basic Usage

**Python:**
```python
from promptware.sdk import Agent

agent = Agent("http://localhost:3000")

# Create user
result = agent.user.create(
    email="alice@example.com",
    name="Alice Johnson",
    role="admin"
)
print(f"Created user: {result}")

# Get user
user = agent.user.get(user_id=result['user_id'])
print(f"Retrieved: {user}")

# List users
users = agent.user.list(limit=10, offset=0)
print(f"Found {len(users)} users")
```

**Node.js:**
```javascript
import { Agent } from '@promptware/client/sdk';

const agent = new Agent('http://localhost:3000');

// Create user
const result = await agent.user.create({
  email: 'alice@example.com',
  name: 'Alice Johnson',
  role: 'admin'
});
console.log('Created user:', result);

// Get user
const user = await agent.user.get({ userId: result.user_id });
console.log('Retrieved:', user);

// List users
const users = await agent.user.list({ limit: 10, offset: 0 });
console.log(`Found ${users.length} users`);
```

### Error Handling

**Python:**
```python
from promptware.sdk import (
    Agent,
    VerbNotFoundError,
    InvalidParamsError,
    ConnectionError
)

agent = Agent("http://localhost:3000")

try:
    result = agent.user.create(email="test@example.com")
except InvalidParamsError as e:
    print(f"Invalid parameters: {e}")
except VerbNotFoundError as e:
    print(f"Verb not found: {e}")
except ConnectionError as e:
    print(f"Connection failed: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

**Node.js:**
```javascript
import {
  Agent,
  VerbNotFoundError,
  InvalidParamsError,
  ConnectionError
} from '@promptware/client/sdk';

const agent = new Agent('http://localhost:3000');

try {
  const result = await agent.user.create({ email: 'test@example.com' });
} catch (error) {
  if (error instanceof InvalidParamsError) {
    console.log('Invalid parameters:', error.message);
  } else if (error instanceof VerbNotFoundError) {
    console.log('Verb not found:', error.message);
  } else if (error instanceof ConnectionError) {
    console.log('Connection failed:', error.message);
  } else {
    console.log('Unexpected error:', error);
  }
}
```

### Production Configuration

**Python:**
```python
from promptware.sdk import Agent
import logging

# Enable detailed logging
logging.basicConfig(level=logging.INFO)

agent = Agent(
    base_url="https://api.example.com",
    timeout=60,
    max_retries=5,
    retry_delay=2.0,
    circuit_breaker_threshold=10,
    circuit_breaker_timeout=120,
    enable_logging=True
)

# Use in production
with agent:
    result = agent.user.create(email="prod@example.com", name="Production User")
```

**Node.js:**
```javascript
import { Agent } from '@promptware/client/sdk';
import http from 'http';
import https from 'https';

// Custom HTTP agents for connection pooling
const httpAgent = new http.Agent({ keepAlive: true, maxSockets: 50 });
const httpsAgent = new https.Agent({ keepAlive: true, maxSockets: 50 });

const agent = new Agent('https://api.example.com', {
  timeout: 60000,
  maxRetries: 5,
  retryDelay: 2000,
  retryBackoff: 2.0,
  circuitBreakerThreshold: 10,
  circuitBreakerTimeout: 120000,
  enableLogging: true,
  httpAgent,
  httpsAgent
});

// Monitor circuit breaker
agent.on('circuit-breaker-state', (state) => {
  console.log(`[Circuit Breaker] State changed to: ${state}`);
});

// Use in production
try {
  const result = await agent.user.create({
    email: 'prod@example.com',
    name: 'Production User'
  });
} finally {
  agent.close();
}
```

## TypeScript Support (Node.js)

The Node.js SDK includes full TypeScript definitions:

```typescript
import { Agent, VerbSchema } from '@promptware/client/sdk';

const agent = new Agent('http://localhost:3000', {
  timeout: 30000,
  maxRetries: 3
});

// Type-safe verb calls
interface User {
  user_id: string;
  email: string;
  name: string;
}

const result: User = await agent.user.create({
  email: 'test@example.com',
  name: 'Test User'
});

// Type-safe schema access
const schema: VerbSchema | null = await agent.getVerbSchema('user.create@v1');
if (schema) {
  console.log(schema.inputSchema.properties);
}
```

## Next Steps

- [CLI Guide](./cli-guide.md) - Generate MCP servers
- [Production Hardening](./production-hardening.md) - Production features
- [Examples](../examples/) - More code examples
