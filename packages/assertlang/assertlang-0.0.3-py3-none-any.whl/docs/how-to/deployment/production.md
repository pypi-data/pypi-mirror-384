# How-To: Deploy to Production

**Deploy AssertLang applications to production with confidence: checklist, containers, monitoring, and best practices.**

---

## Overview

**What you'll learn:**
- Production deployment checklist
- Deploy with Docker and Kubernetes
- Configure environment variables
- Set up monitoring and logging
- Security best practices
- Rolling updates and rollback

**Time:** 60 minutes
**Difficulty:** Advanced
**Prerequisites:** [Optimize Performance](../advanced/performance.md)

---

## The Problem

Deploying contracts to production requires careful configuration:

**Risks:**
- Contracts slow down production (if not disabled)
- Missing environment variables break deployment
- No monitoring means silent failures
- Security vulnerabilities from exposed configs
- Difficult rollback if issues occur

---

## The Solution

Systematic production deployment with:
- Disabled contracts for performance
- Proper environment configuration
- Comprehensive monitoring
- Security hardening
- Automated rollback

---

## Step 1: Pre-Deployment Checklist

### Code Quality

- ✅ All tests passing (unit, integration, e2e)
- ✅ 100% contract coverage in tests
- ✅ No failing contracts in test suite
- ✅ Code reviewed and approved
- ✅ Documentation updated

### Security

- ✅ No secrets in code (use environment variables)
- ✅ Dependencies scanned for vulnerabilities
- ✅ Input validation on all APIs
- ✅ Rate limiting configured
- ✅ HTTPS/TLS enabled

### Performance

- ✅ Contracts disabled in production (`PW_DISABLE_CONTRACTS=1`)
- ✅ Performance benchmarked
- ✅ Load tested
- ✅ Resource limits configured
- ✅ Caching enabled where appropriate

### Monitoring

- ✅ Logging configured
- ✅ Metrics collection enabled
- ✅ Alerts configured
- ✅ Health checks implemented
- ✅ Error tracking setup

---

## Step 2: Environment Configuration

### Development Environment

```bash
# .env.development
ENV=development
PW_DISABLE_CONTRACTS=0  # Contracts enabled
PW_DEBUG=1              # Debug logging
LOG_LEVEL=DEBUG
DATABASE_URL=postgresql://localhost:5432/myapp_dev
API_BASE_URL=http://localhost:8000
```

### Production Environment

```bash
# .env.production
ENV=production
PW_DISABLE_CONTRACTS=1  # Contracts disabled
PW_DEBUG=0              # Production logging
LOG_LEVEL=INFO
DATABASE_URL=${DATABASE_URL}  # From secret manager
API_BASE_URL=https://api.example.com
```

### Load Environment

```python
# config.py
import os
from dotenv import load_dotenv

# Load environment-specific config
env = os.getenv('ENV', 'development')
load_dotenv(f'.env.{env}')

class Config:
    ENV = os.getenv('ENV', 'development')
    DEBUG = os.getenv('PW_DEBUG', '0') == '1'
    CONTRACTS_DISABLED = os.getenv('PW_DISABLE_CONTRACTS', '0') == '1'
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    DATABASE_URL = os.getenv('DATABASE_URL')
    API_BASE_URL = os.getenv('API_BASE_URL')

    @classmethod
    def validate(cls):
        """Validate required config."""
        required = ['DATABASE_URL', 'API_BASE_URL']
        missing = [k for k in required if not getattr(cls, k)]
        if missing:
            raise ValueError(f"Missing required config: {missing}")

# Validate on import
Config.validate()
```

---

## Step 3: Docker Deployment

### Dockerfile

```dockerfile
# Dockerfile
FROM python:3.11-slim

# Set production environment
ENV ENV=production
ENV PW_DISABLE_CONTRACTS=1
ENV PYTHONUNBUFFERED=1

# Create app directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run application
CMD ["python", "main.py"]
```

### Build and Run

```bash
# Build image
docker build -t myapp:latest .

# Run container
docker run -d \
  --name myapp \
  -p 8000:8000 \
  -e DATABASE_URL="postgresql://..." \
  -e API_KEY="..." \
  myapp:latest

# Check logs
docker logs myapp

# Check health
curl http://localhost:8000/health
```

---

## Step 4: Kubernetes Deployment

### Deployment YAML

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
  labels:
    app: myapp
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
    spec:
      containers:
      - name: myapp
        image: myapp:v1.0.0
        ports:
        - containerPort: 8000
        env:
        - name: ENV
          value: "production"
        - name: PW_DISABLE_CONTRACTS
          value: "1"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: myapp-secrets
              key: database-url
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
```

### Service YAML

```yaml
# service.yaml
apiVersion: v1
kind: Service
metadata:
  name: myapp-service
spec:
  selector:
    app: myapp
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

### Secrets

```bash
# Create secrets
kubectl create secret generic myapp-secrets \
  --from-literal=database-url="postgresql://..." \
  --from-literal=api-key="..."

# Deploy
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml

# Check status
kubectl get pods
kubectl get svc myapp-service

# View logs
kubectl logs -f deployment/myapp
```

---

## Step 5: Health Checks

### Implement Health Endpoint

```python
# health.py
from fastapi import FastAPI, Response, status

app = FastAPI()

@app.get("/health")
async def health_check():
    """Basic health check - service is running."""
    return {"status": "healthy"}

@app.get("/ready")
async def readiness_check():
    """Readiness check - service can handle requests."""
    try:
        # Check database connection
        db.execute("SELECT 1")

        # Check dependencies
        if not redis_client.ping():
            return Response(status_code=status.HTTP_503_SERVICE_UNAVAILABLE)

        return {"status": "ready"}
    except Exception as e:
        return Response(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not ready", "error": str(e)}
        )
```

---

## Step 6: Monitoring and Logging

### Structured Logging

```python
# logging_config.py
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    handlers=[
        logging.StreamHandler()
    ]
)

# Set JSON formatter
for handler in logging.root.handlers:
    handler.setFormatter(JSONFormatter())
```

### Prometheus Metrics

```python
# metrics.py
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi import FastAPI, Response

app = FastAPI()

# Define metrics
requests_total = Counter('requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
request_duration = Histogram('request_duration_seconds', 'HTTP request duration', ['method', 'endpoint'])
active_requests = Gauge('active_requests', 'Number of active requests')

# Middleware to track metrics
@app.middleware("http")
async def track_metrics(request, call_next):
    active_requests.inc()

    with request_duration.labels(method=request.method, endpoint=request.url.path).time():
        response = await call_next(request)

    active_requests.dec()
    requests_total.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()

    return response

# Metrics endpoint
@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type="text/plain")
```

---

## Step 7: Security Best Practices

### Secrets Management

```python
# secrets.py
import os
from google.cloud import secretmanager

def get_secret(secret_id):
    """Fetch secret from Google Secret Manager."""
    client = secretmanager.SecretManagerServiceClient()
    project_id = os.getenv('GCP_PROJECT_ID')

    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})

    return response.payload.data.decode('UTF-8')

# Usage
DATABASE_URL = get_secret('database-url')
API_KEY = get_secret('api-key')
```

### Input Validation

```python
# validation.py
from pydantic import BaseModel, validator

class CreateUserRequest(BaseModel):
    name: str
    email: str
    age: int

    @validator('name')
    def name_must_be_valid(cls, v):
        if not v or len(v) > 100:
            raise ValueError('Name must be 1-100 characters')
        return v

    @validator('email')
    def email_must_be_valid(cls, v):
        if '@' not in v or len(v) > 255:
            raise ValueError('Invalid email')
        return v

    @validator('age')
    def age_must_be_valid(cls, v):
        if v < 0 or v > 150:
            raise ValueError('Age must be 0-150')
        return v
```

### Rate Limiting

```python
# rate_limiting.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from fastapi import FastAPI, Request

limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(429, _rate_limit_exceeded_handler)

@app.post("/api/users")
@limiter.limit("10/minute")
async def create_user(request: Request, user: CreateUserRequest):
    # Create user
    pass
```

---

## Step 8: Rolling Updates and Rollback

### Rolling Update

```bash
# Update to new version
kubectl set image deployment/myapp myapp=myapp:v1.1.0

# Watch rollout
kubectl rollout status deployment/myapp

# Check pods
kubectl get pods -l app=myapp
```

### Rollback

```bash
# Check rollout history
kubectl rollout history deployment/myapp

# Rollback to previous version
kubectl rollout undo deployment/myapp

# Rollback to specific revision
kubectl rollout undo deployment/myapp --to-revision=2

# Verify rollback
kubectl get pods -l app=myapp
```

### Blue-Green Deployment

```yaml
# deployment-blue.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp-blue
spec:
  replicas: 3
  template:
    metadata:
      labels:
        app: myapp
        version: blue
    spec:
      containers:
      - name: myapp
        image: myapp:v1.0.0
```

```yaml
# deployment-green.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp-green
spec:
  replicas: 3
  template:
    metadata:
      labels:
        app: myapp
        version: green
    spec:
      containers:
      - name: myapp
        image: myapp:v1.1.0
```

```bash
# Deploy green
kubectl apply -f deployment-green.yaml

# Wait for green to be ready
kubectl wait --for=condition=available deployment/myapp-green

# Switch traffic
kubectl patch service myapp-service -p '{"spec":{"selector":{"version":"green"}}}'

# Delete blue (after verification)
kubectl delete deployment myapp-blue
```

---

## Step 9: Disaster Recovery

### Database Backups

```bash
# Automated daily backups
0 2 * * * pg_dump $DATABASE_URL | gzip > /backups/db_$(date +\%Y\%m\%d).sql.gz

# Keep last 30 days
find /backups -name "db_*.sql.gz" -mtime +30 -delete
```

### Application State

```python
# backup.py
import boto3
import json
from datetime import datetime

s3 = boto3.client('s3')

def backup_application_state():
    """Backup application state to S3."""
    state = {
        "timestamp": datetime.utcnow().isoformat(),
        "users": get_all_users(),
        "config": get_config(),
    }

    s3.put_object(
        Bucket='myapp-backups',
        Key=f'state_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.json',
        Body=json.dumps(state)
    )
```

---

## Production Checklist

**Pre-Deployment:**
- ✅ All tests passing
- ✅ Contracts disabled (`PW_DISABLE_CONTRACTS=1`)
- ✅ Secrets not in code
- ✅ Environment variables configured
- ✅ Resource limits set
- ✅ Health checks implemented
- ✅ Monitoring enabled
- ✅ Backups configured

**Deployment:**
- ✅ Rolling update strategy
- ✅ Zero-downtime deployment
- ✅ Health checks passing
- ✅ Logs being collected
- ✅ Metrics being reported

**Post-Deployment:**
- ✅ Verify deployment successful
- ✅ Check error rates
- ✅ Monitor performance
- ✅ Test critical paths
- ✅ Rollback plan ready

---

## Summary

**Production configuration:**
```bash
PW_DISABLE_CONTRACTS=1  # Disable contracts
ENV=production          # Production mode
LOG_LEVEL=INFO          # Production logging
```

**Deploy with Docker:**
```bash
docker build -t myapp:v1.0.0 .
docker run -d -p 8000:8000 myapp:v1.0.0
```

**Deploy with Kubernetes:**
```bash
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
kubectl rollout status deployment/myapp
```

**Monitor:**
- Health checks: `/health`, `/ready`
- Metrics: `/metrics` (Prometheus)
- Logs: Structured JSON
- Alerts: On errors/performance issues

---

## Next Steps

- **[Set Up CI/CD](ci-cd.md)** - Automate deployments
- **[Monitor Contract Violations](monitoring.md)** - Track violations in production
- **[Optimize Performance](../advanced/performance.md)** - Further optimize

---

## See Also

- **[API Reference: Runtime](../../reference/runtime-api.md)** - Runtime configuration
- **[Cookbook: Production Patterns](../../cookbook/)** - Production recipes

---

**Difficulty:** Advanced
**Time:** 60 minutes
**Last Updated:** 2025-10-15
