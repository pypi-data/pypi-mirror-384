# How-To: Monitor Contract Violations

**Track, analyze, and alert on contract violations in production for proactive issue detection.**

---

## Overview

**What you'll learn:**
- Log contract violations
- Set up metrics and dashboards
- Configure alerts
- Track violation patterns
- Debug production issues
- Use monitoring tools (Prometheus, Grafana, Sentry)

**Time:** 30 minutes
**Difficulty:** Advanced
**Prerequisites:** [Deploy to Production](production.md), [Set Up CI/CD](ci-cd.md)

---

## The Problem

Contracts disabled in production means violations go undetected:

**Issues:**
- Invalid data silently processed
- Bugs only caught by users
- No visibility into contract-related issues
- Hard to diagnose production problems
- No way to know if contracts would have caught bugs

**Need:**
- Track violations during development/testing
- Monitor for contract-like issues in production
- Alert on anomalies
- Debug with full context

---

## The Solution

Comprehensive monitoring strategy:

1. **Development:** Full contracts enabled, violations logged
2. **Testing:** All violations tracked and reported
3. **Production:** Contracts disabled, but monitoring mimics contract checks
4. **Analysis:** Dashboards show violation patterns

---

## Step 1: Logging Violations

### Custom Violation Logger

```python
# violation_logger.py
import logging
import json
from datetime import datetime

logger = logging.getLogger('contract_violations')

def log_contract_violation(
    contract_name: str,
    function_name: str,
    condition: str,
    values: dict,
    violation_type: str = 'precondition'
):
    """Log contract violation with full context."""
    violation = {
        'timestamp': datetime.utcnow().isoformat(),
        'type': 'contract_violation',
        'violation_type': violation_type,
        'contract': contract_name,
        'function': function_name,
        'condition': condition,
        'values': values,
        'severity': 'error',
    }

    logger.error(json.dumps(violation))

    # Also send to error tracking
    try:
        from sentry_sdk import capture_message
        capture_message(
            f"Contract violation: {contract_name} in {function_name}",
            level='error',
            extras=violation
        )
    except ImportError:
        pass  # Sentry not configured
```

### Integrate with Generated Code

```python
# Generated contract code with logging
from promptware.runtime.contracts import check_precondition

def process_order(order_id, amount):
    # Precondition check with logging
    if not (amount > 0):
        log_contract_violation(
            contract_name='process_order',
            function_name='process_order',
            condition='amount > 0',
            values={'order_id': order_id, 'amount': amount},
            violation_type='precondition'
        )
        # Raise exception (development/testing)
        check_precondition(
            amount > 0,
            "amount_positive",
            "amount > 0",
            "process_order",
            context={'order_id': order_id, 'amount': amount}
        )

    # Process order
    return result
```

---

## Step 2: Metrics Collection

### Prometheus Metrics

```python
# contract_metrics.py
from prometheus_client import Counter, Histogram, Gauge

# Count violations by type
contract_violations = Counter(
    'contract_violations_total',
    'Total contract violations',
    ['function', 'violation_type', 'contract']
)

# Track violation frequency
violation_rate = Gauge(
    'contract_violation_rate',
    'Violations per minute',
    ['function']
)

# Track time spent in contract checks (if enabled)
contract_check_duration = Histogram(
    'contract_check_duration_seconds',
    'Time spent in contract checks',
    ['function', 'check_type']
)

def record_violation(function: str, violation_type: str, contract: str):
    """Record contract violation in metrics."""
    contract_violations.labels(
        function=function,
        violation_type=violation_type,
        contract=contract
    ).inc()

def record_check_duration(function: str, check_type: str, duration: float):
    """Record duration of contract check."""
    contract_check_duration.labels(
        function=function,
        check_type=check_type
    ).observe(duration)
```

### Integrate with Application

```python
# app.py
from contract_metrics import record_violation
from violation_logger import log_contract_violation

def process_order(order_id, amount):
    # Check precondition
    if amount <= 0:
        # Log violation
        log_contract_violation(
            contract_name='process_order_precondition',
            function_name='process_order',
            condition='amount > 0',
            values={'order_id': order_id, 'amount': amount},
            violation_type='precondition'
        )

        # Record metric
        record_violation(
            function='process_order',
            violation_type='precondition',
            contract='amount_positive'
        )

        # In dev/test: raise exception
        # In production: handle gracefully or disable contracts
        if os.getenv('PW_DISABLE_CONTRACTS') != '1':
            raise ContractViolation("amount must be positive")

    # Process order
    return result
```

---

## Step 3: Error Tracking with Sentry

### Configure Sentry

```python
# sentry_config.py
import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration

sentry_sdk.init(
    dsn="https://your-dsn@sentry.io/project",
    traces_sample_rate=0.1,  # 10% of transactions
    environment=os.getenv('ENV', 'development'),
    integrations=[
        LoggingIntegration(
            level=logging.INFO,
            event_level=logging.ERROR
        ),
    ],
)
```

### Report Violations to Sentry

```python
# sentry_violations.py
import sentry_sdk

def report_violation_to_sentry(
    function_name: str,
    contract: str,
    condition: str,
    values: dict
):
    """Report contract violation to Sentry."""
    with sentry_sdk.push_scope() as scope:
        # Add context
        scope.set_context("contract", {
            "function": function_name,
            "contract": contract,
            "condition": condition,
        })

        scope.set_context("values", values)

        # Set tags for filtering
        scope.set_tag("violation_type", "contract")
        scope.set_tag("function", function_name)

        # Capture as error
        sentry_sdk.capture_message(
            f"Contract violation in {function_name}: {condition}",
            level="error"
        )
```

---

## Step 4: Grafana Dashboards

### Create Dashboard

```json
{
  "dashboard": {
    "title": "Contract Violations",
    "panels": [
      {
        "title": "Violations per Minute",
        "targets": [
          {
            "expr": "rate(contract_violations_total[1m])",
            "legendFormat": "{{function}} - {{violation_type}}"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Total Violations by Function",
        "targets": [
          {
            "expr": "sum(contract_violations_total) by (function)",
            "legendFormat": "{{function}}"
          }
        ],
        "type": "bar"
      },
      {
        "title": "Violation Types",
        "targets": [
          {
            "expr": "sum(contract_violations_total) by (violation_type)",
            "legendFormat": "{{violation_type}}"
          }
        ],
        "type": "pie"
      }
    ]
  }
}
```

### PromQL Queries

```promql
# Violations per minute
rate(contract_violations_total[1m])

# Top 10 functions with violations
topk(10, sum(contract_violations_total) by (function))

# Precondition vs postcondition violations
sum(contract_violations_total) by (violation_type)

# Violations in last hour
increase(contract_violations_total[1h])

# Functions with > 100 violations
contract_violations_total > 100
```

---

## Step 5: Alerting

### Prometheus Alert Rules

```yaml
# alert_rules.yml
groups:
  - name: contract_violations
    interval: 1m
    rules:
      - alert: HighContractViolationRate
        expr: rate(contract_violations_total[5m]) > 10
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High contract violation rate"
          description: "{{ $labels.function }} has {{ $value }} violations/sec"

      - alert: CriticalContractViolation
        expr: rate(contract_violations_total{violation_type="precondition"}[1m]) > 50
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Critical precondition violations"
          description: "{{ $labels.function }} precondition failing rapidly"

      - alert: NewContractViolation
        expr: changes(contract_violations_total[5m]) > 0
        labels:
          severity: info
        annotations:
          summary: "New contract violation detected"
          description: "First violation in {{ $labels.function }}"
```

### Alertmanager Configuration

```yaml
# alertmanager.yml
route:
  receiver: 'team-slack'
  group_by: ['alertname', 'function']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h

  routes:
    - match:
        severity: critical
      receiver: 'pagerduty'
      continue: true

    - match:
        severity: warning
      receiver: 'team-slack'

receivers:
  - name: 'team-slack'
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'
        channel: '#alerts'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'

  - name: 'pagerduty'
    pagerduty_configs:
      - service_key: 'YOUR_PAGERDUTY_KEY'
```

---

## Step 6: Log Aggregation

### ELK Stack (Elasticsearch, Logstash, Kibana)

**Logstash Pipeline:**
```
# logstash.conf
input {
  file {
    path => "/var/log/app/*.log"
    codec => json
  }
}

filter {
  if [type] == "contract_violation" {
    mutate {
      add_tag => ["contract", "violation"]
    }
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "contract-violations-%{+YYYY.MM.dd}"
  }
}
```

**Kibana Dashboard:**
- Violation timeline
- Top violated functions
- Violation types breakdown
- User impact (requests affected)

---

## Step 7: Analyzing Patterns

### Violation Analysis Script

```python
# analyze_violations.py
import pandas as pd
from elasticsearch import Elasticsearch

es = Elasticsearch(['http://localhost:9200'])

def get_violations(days=7):
    """Fetch violations from last N days."""
    query = {
        "query": {
            "bool": {
                "must": [
                    {"term": {"type": "contract_violation"}},
                    {"range": {"timestamp": {"gte": f"now-{days}d"}}}
                ]
            }
        },
        "size": 10000
    }

    response = es.search(index="contract-violations-*", body=query)
    return [hit['_source'] for hit in response['hits']['hits']]

def analyze_patterns(violations):
    """Analyze violation patterns."""
    df = pd.DataFrame(violations)

    # Most violated functions
    top_functions = df['function'].value_counts().head(10)
    print("Top 10 violated functions:")
    print(top_functions)

    # Violation types
    violation_types = df['violation_type'].value_counts()
    print("\nViolation types:")
    print(violation_types)

    # Hourly distribution
    df['hour'] = pd.to_datetime(df['timestamp']).dt.hour
    hourly = df.groupby('hour').size()
    print("\nViolations by hour:")
    print(hourly)

    # Common conditions that fail
    top_conditions = df['condition'].value_counts().head(10)
    print("\nMost failed conditions:")
    print(top_conditions)

# Run analysis
violations = get_violations(days=7)
analyze_patterns(violations)
```

---

## Step 8: Production Monitoring (Contracts Disabled)

### Mimic Contract Checks

Even with contracts disabled, monitor for contract-like issues:

```python
# production_monitoring.py
import logging
from contract_metrics import record_violation

def process_order_monitored(order_id, amount):
    """Process order with monitoring (contracts disabled)."""

    # Log potential violations (but don't raise)
    if amount <= 0:
        logging.warning(
            f"Invalid amount in process_order: {amount}",
            extra={
                'function': 'process_order',
                'order_id': order_id,
                'amount': amount,
                'potential_violation': 'amount > 0'
            }
        )

        record_violation(
            function='process_order',
            violation_type='precondition',
            contract='amount_positive'
        )

        # Handle gracefully in production
        return {"error": "Invalid amount", "order_id": order_id}

    # Normal processing
    return process_order_impl(order_id, amount)
```

---

## Step 9: Performance Impact Monitoring

### Track Contract Overhead

```python
# performance_monitoring.py
import time
from contract_metrics import record_check_duration

def timed_contract_check(check_type: str, function: str):
    """Decorator to measure contract check duration."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start = time.time()
            result = func(*args, **kwargs)
            duration = time.time() - start

            record_check_duration(function, check_type, duration)

            return result
        return wrapper
    return decorator

@timed_contract_check('precondition', 'process_order')
def check_process_order_preconditions(order_id, amount):
    """Check preconditions for process_order."""
    assert amount > 0, "amount must be positive"
    assert order_id is not None, "order_id required"
```

---

## Monitoring Checklist

**Logging:**
- ✅ Contract violations logged with full context
- ✅ Structured JSON logging
- ✅ Log aggregation configured (ELK, Splunk, etc.)
- ✅ Log retention policy (30-90 days)

**Metrics:**
- ✅ Violation counts by function
- ✅ Violation types tracked
- ✅ Violation rate monitored
- ✅ Contract check duration measured

**Alerting:**
- ✅ High violation rate alert
- ✅ Critical violations alert
- ✅ New violation types alert
- ✅ Alert routing configured (Slack, PagerDuty)

**Dashboards:**
- ✅ Real-time violation dashboard
- ✅ Historical trends
- ✅ Function-level breakdown
- ✅ User impact metrics

**Error Tracking:**
- ✅ Sentry/Rollbar configured
- ✅ Violations reported with context
- ✅ Source maps uploaded
- ✅ Release tracking enabled

---

## Summary

**Monitor violations in development:**
```python
# Contracts enabled, log everything
PW_DISABLE_CONTRACTS=0
log_contract_violation(...)
record_violation(...)
```

**Monitor in production:**
```python
# Contracts disabled, but track issues
PW_DISABLE_CONTRACTS=1

if potentially_invalid_input:
    logging.warning("Potential violation", extra={...})
    record_violation(...)
    # Handle gracefully
```

**Alert on issues:**
```yaml
# Prometheus alert
expr: rate(contract_violations_total[5m]) > 10
```

**Analyze patterns:**
```python
# Weekly violation analysis
violations = get_violations(days=7)
analyze_patterns(violations)
```

---

## Next Steps

- **[Deploy to Production](production.md)** - Production deployment guide
- **[Set Up CI/CD](ci-cd.md)** - Automate testing and deployment
- **[Optimize Performance](../advanced/performance.md)** - Reduce monitoring overhead

---

## See Also

- **[API Reference: Runtime](../../reference/runtime-api.md)** - Runtime configuration
- **[Cookbook: Monitoring Patterns](../../cookbook/)** - Monitoring recipes
- **[Prometheus Documentation](https://prometheus.io/docs/)** - Metrics and alerting
- **[Sentry Documentation](https://docs.sentry.io/)** - Error tracking

---

**Difficulty:** Advanced
**Time:** 30 minutes
**Last Updated:** 2025-10-15
