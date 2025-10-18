# Logger Tool

Structured logging sink with stdout forwarding.

## Quickstart

The Logger tool emits structured logs to stdout and returns confirmation.

## Examples

### Log a build completion

```python
run_tool("logger", {"message": "build finished", "context": {"duration_ms": 812}})
```
