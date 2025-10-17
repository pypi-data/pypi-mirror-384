# How-To: Optimize Performance

**Optimize AssertLang code for production: disable contracts, inline operations, and reduce overhead.**

---

## Overview

**What you'll learn:**
- Disable contract checks in production
- Inline pattern matching for speed
- Avoid unnecessary allocations
- Benchmark and profile code
- Production optimization strategies

**Time:** 30 minutes
**Difficulty:** Advanced
**Prerequisites:** [Handle Complex Types](complex-types.md)

---

## The Problem

Development code with full contract checking is safe but slower:

```promptware
function process_item(item: Item) -> Result<String, String>
  requires:
    item.price > 0.0
    len(item.name) > 0
    item.quantity > 0
  ensures:
    len(result) > 0 if result is Ok
  do
    # Business logic
  end
end
```

**Overhead:**
- Contract checks on every call
- Runtime validation
- Exception handling
- Memory allocations

**For production:**
- Contracts verified during testing
- Runtime checks add latency
- Need maximum throughput

---

## The Solution

Disable contracts in production while keeping them in development:

```bash
# Development: Full checking
python app.py

# Production: Contracts disabled
PW_DISABLE_CONTRACTS=1 python app.py
```

**Benefits:**
- Zero contract overhead in production
- Same code runs in both environments
- Safety during development
- Performance in production

---

## Step 1: Disable Contracts

### Environment Variable

```bash
# Disable all contract checks
export PW_DISABLE_CONTRACTS=1
python your_app.py
```

### Python Code

```python
# main.py
import os

# Disable contracts globally
os.environ['PW_DISABLE_CONTRACTS'] = '1'

# Import after setting env var
from mymodule import process_data

# Contracts are now no-ops
result = process_data(items)
```

### Docker/Kubernetes

```dockerfile
# Dockerfile
FROM python:3.11-slim

# Disable contracts in production container
ENV PW_DISABLE_CONTRACTS=1

COPY . /app
WORKDIR /app

CMD ["python", "main.py"]
```

**Kubernetes:**
```yaml
apiVersion: v1
kind: Deployment
metadata:
  name: myapp
spec:
  template:
    spec:
      containers:
      - name: app
        image: myapp:latest
        env:
        - name: PW_DISABLE_CONTRACTS
          value: "1"
```

---

## Step 2: Inline Operations

### Direct Pattern Matching vs. Functions

**Slow: Function calls**
```promptware
function get_value(opt: Option<Int>) -> Int
  do
    return option_unwrap_or(opt, 0)  # Function call overhead
  end
end
```

**Fast: Inline pattern matching**
```promptware
function get_value_fast(opt: Option<Int>) -> Int
  do
    if opt is Some(val):
      return val
    else:
      return 0
    end
  end
end
```

### Chaining vs. Explicit Checks

**Slow: Multiple function calls**
```promptware
function process(opt: Option<Int>) -> Int
  do
    let doubled = option_map(opt, fn(x) -> x * 2)
    let incremented = option_map(doubled, fn(x) -> x + 1)
    return option_unwrap_or(incremented, 0)
  end
end
```

**Fast: Single pattern match**
```promptware
function process_fast(opt: Option<Int>) -> Int
  do
    if opt is Some(val):
      return (val * 2) + 1
    else:
      return 0
    end
  end
end
```

---

## Step 3: Avoid Allocations

### Reuse Containers

**Slow: Repeated allocations**
```promptware
function sum_list(items: List<Int>) -> Int
  do
    let result = 0
    for item in items:
      # Each iteration creates new list (in some implementations)
      let doubled = [item * 2]
      result = result + doubled[0]
    end
    return result
  end
end
```

**Fast: Direct computation**
```promptware
function sum_list_fast(items: List<Int>) -> Int
  do
    let result = 0
    for item in items:
      result = result + (item * 2)
    end
    return result
  end
end
```

### Avoid Unnecessary Intermediate Values

**Slow: Multiple intermediate variables**
```promptware
function compute(a: Int, b: Int) -> Int
  do
    let x = a + b
    let y = x * 2
    let z = y + 10
    return z
  end
end
```

**Fast: Direct computation**
```promptware
function compute_fast(a: Int, b: Int) -> Int
  do
    return ((a + b) * 2) + 10
  end
end
```

---

## Step 4: Batch Operations

### Process in Batches

**Slow: One-by-one**
```promptware
function process_items(items: List<Item>) -> List<Result<String, String>>
  do
    let results = []
    for item in items:
      # Contract check on every iteration
      let result = process_item(item)
      results = results + [result]
    end
    return results
  end
end
```

**Fast: Batch validation**
```promptware
function process_items_batch(items: List<Item>) -> List<Result<String, String>>
  requires:
    # Validate batch once
    forall item in items: item.price > 0.0
    forall item in items: len(item.name) > 0
  do
    let results = []
    for item in items:
      # Skip per-item contract checks (validated above)
      let result = process_item_unchecked(item)
      results = results + [result]
    end
    return results
  end
end
```

---

## Step 5: Benchmark and Profile

### Python Benchmarking

```python
# benchmark.py
import time
from mymodule import process_item_fast, process_item_slow

items = [create_item(i) for i in range(10000)]

# Benchmark slow version
start = time.time()
for item in items:
    process_item_slow(item)
slow_time = time.time() - start

# Benchmark fast version
start = time.time()
for item in items:
    process_item_fast(item)
fast_time = time.time() - start

print(f"Slow: {slow_time:.3f}s")
print(f"Fast: {fast_time:.3f}s")
print(f"Speedup: {slow_time / fast_time:.2f}x")
```

### Using timeit

```python
# benchmark_timeit.py
import timeit

setup = """
from mymodule import process_item_fast, create_item
item = create_item(1)
"""

# Time slow version
slow_time = timeit.timeit(
    "process_item_slow(item)",
    setup=setup.replace("_fast", "_slow"),
    number=100000
)

# Time fast version
fast_time = timeit.timeit(
    "process_item_fast(item)",
    setup=setup,
    number=100000
)

print(f"Slow: {slow_time:.3f}s per 100k calls")
print(f"Fast: {fast_time:.3f}s per 100k calls")
```

### Profile with cProfile

```python
# profile_app.py
import cProfile
import pstats
from mymodule import main

# Profile the application
profiler = cProfile.Profile()
profiler.enable()

main()

profiler.disable()

# Print stats
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)  # Top 20 slowest functions
```

---

## Step 6: Language-Specific Optimizations

### Python

**Use Built-in Functions:**
```python
# Slow: Manual loop
def sum_list(items):
    total = 0
    for item in items:
        total += item
    return total

# Fast: Built-in sum()
def sum_list_fast(items):
    return sum(items)
```

**List Comprehensions:**
```python
# Slow: Manual append
def double_list(items):
    result = []
    for item in items:
        result.append(item * 2)
    return result

# Fast: List comprehension
def double_list_fast(items):
    return [item * 2 for item in items]
```

### JavaScript

**Use Array Methods:**
```javascript
// Slow: Manual loop
function doubleList(items) {
    const result = [];
    for (const item of items) {
        result.push(item * 2);
    }
    return result;
}

// Fast: Array.map()
function doubleListFast(items) {
    return items.map(item => item * 2);
}
```

### Go

**Preallocate Slices:**
```go
// Slow: Append without capacity
func doubleList(items []int) []int {
    var result []int
    for _, item := range items {
        result = append(result, item*2)
    }
    return result
}

// Fast: Preallocate with make()
func doubleListFast(items []int) []int {
    result := make([]int, 0, len(items))  // Preallocate capacity
    for _, item := range items {
        result = append(result, item*2)
    }
    return result
}
```

---

## Step 7: Production Configuration

### Development vs. Production

**development.env:**
```bash
# Full contract checking
PW_DISABLE_CONTRACTS=0
PW_DEBUG=1
LOG_LEVEL=DEBUG
```

**production.env:**
```bash
# Contracts disabled
PW_DISABLE_CONTRACTS=1
PW_DEBUG=0
LOG_LEVEL=INFO
```

### Load Configuration

```python
# config.py
import os
from dotenv import load_dotenv

# Load environment-specific config
env = os.getenv('ENV', 'development')
load_dotenv(f'.env.{env}')

# Check if contracts are disabled
CONTRACTS_DISABLED = os.getenv('PW_DISABLE_CONTRACTS', '0') == '1'

if CONTRACTS_DISABLED:
    print("Running in production mode (contracts disabled)")
else:
    print("Running in development mode (contracts enabled)")
```

---

## Step 8: Caching and Memoization

### Cache Expensive Operations

```promptware
# Without caching: Compute every time
function fibonacci(n: Int) -> Int
  do
    if n <= 1:
      return n
    else:
      return fibonacci(n - 1) + fibonacci(n - 2)
    end
  end
end
```

**Python with caching:**
```python
from functools import lru_cache

@lru_cache(maxsize=128)
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)

# First call: slow
result = fibonacci(100)  # Computes from scratch

# Subsequent calls: instant
result = fibonacci(100)  # Returns cached value
```

---

## Step 9: Parallel Processing

### Process Items in Parallel

**Python:**
```python
# parallel_process.py
from concurrent.futures import ProcessPoolExecutor
from mymodule import process_item

items = [create_item(i) for i in range(10000)]

# Sequential: One at a time
results = [process_item(item) for item in items]

# Parallel: Use all CPU cores
with ProcessPoolExecutor() as executor:
    results = list(executor.map(process_item, items))
```

**JavaScript (Node.js):**
```javascript
// parallel_process.js
const { Worker } = require('worker_threads');

async function processParallel(items) {
    const workers = [];
    const chunkSize = Math.ceil(items.length / 4);  // 4 workers

    for (let i = 0; i < 4; i++) {
        const chunk = items.slice(i * chunkSize, (i + 1) * chunkSize);
        const worker = new Worker('./worker.js', {
            workerData: chunk
        });
        workers.push(worker);
    }

    // Collect results
    const results = await Promise.all(workers);
    return results.flat();
}
```

---

## Step 10: Best Practices

### 1. Enable Contracts in Tests

```python
# test_contracts.py
import os
import pytest

def test_with_contracts():
    # Force enable contracts for testing
    os.environ['PW_DISABLE_CONTRACTS'] = '0'

    # These should pass
    assert process_valid_item(item) is not None

    # These should raise ContractViolation
    with pytest.raises(ContractViolation):
        process_invalid_item(bad_item)
```

### 2. Benchmark Before Optimizing

```python
# Always measure first!
import time

def benchmark(func, *args, iterations=1000):
    start = time.time()
    for _ in range(iterations):
        func(*args)
    elapsed = time.time() - start
    return elapsed / iterations

# Measure baseline
baseline = benchmark(original_function, data)
optimized = benchmark(optimized_function, data)

print(f"Baseline: {baseline*1000:.2f}ms")
print(f"Optimized: {optimized*1000:.2f}ms")
print(f"Speedup: {baseline/optimized:.2f}x")
```

### 3. Profile in Production

```python
# production_profiling.py
import cProfile
import os

# Only profile if explicitly enabled
if os.getenv('ENABLE_PROFILING') == '1':
    profiler = cProfile.Profile()
    profiler.enable()

# Run application
main()

if profiler:
    profiler.disable()
    profiler.dump_stats('production.prof')
```

### 4. Monitor Performance Metrics

```python
# metrics.py
import time
from prometheus_client import Summary, Counter

# Track function execution time
process_time = Summary('process_item_seconds', 'Time to process item')
process_errors = Counter('process_item_errors', 'Errors processing items')

@process_time.time()
def process_item(item):
    try:
        # Process item
        return result
    except Exception as e:
        process_errors.inc()
        raise
```

---

## Performance Checklist

**Development:**
- ✅ All contracts enabled (`PW_DISABLE_CONTRACTS=0`)
- ✅ Debug mode enabled
- ✅ Extensive logging
- ✅ All tests passing with contracts

**Production:**
- ✅ Contracts disabled (`PW_DISABLE_CONTRACTS=1`)
- ✅ Optimized builds
- ✅ Minimal logging
- ✅ Performance monitoring enabled

**Optimization:**
- ✅ Benchmarked before/after
- ✅ Profiled hot paths
- ✅ Inlined critical operations
- ✅ Avoided unnecessary allocations
- ✅ Used language-specific optimizations

---

## Summary

**Disable contracts in production:**
```bash
PW_DISABLE_CONTRACTS=1 python app.py
```

**Inline for performance:**
- Pattern match directly instead of function calls
- Avoid intermediate allocations
- Use language built-ins

**Benchmark and profile:**
- Measure before optimizing
- Profile to find bottlenecks
- Monitor production metrics

**Best practices:**
- Contracts in dev/test, disabled in production
- Optimize hot paths only
- Use parallel processing for batch operations
- Cache expensive computations

---

## Next Steps

- **[Deploy to Production](../../deployment/production.md)** - Production deployment guide
- **[Set Up CI/CD](../../deployment/ci-cd.md)** - Automate testing and deployment
- **[Monitor Contract Violations](../../deployment/monitoring.md)** - Track violations in production

---

## See Also

- **[API Reference: Runtime](../../reference/runtime-api.md)** - Runtime configuration options
- **[Cookbook: Performance Patterns](../../cookbook/patterns/)** - Optimization recipes

---

**Difficulty:** Advanced
**Time:** 30 minutes
**Last Updated:** 2025-10-15
