# How-To: Set Up CI/CD

**Automate testing, building, and deploying AssertLang applications with CI/CD pipelines.**

---

## Overview

**What you'll learn:**
- Set up GitHub Actions for AssertLang projects
- Configure GitLab CI/CD
- Run tests with contracts enabled
- Build and publish Docker images
- Automate deployments to production
- Implement continuous deployment strategies

**Time:** 45 minutes
**Difficulty:** Advanced
**Prerequisites:** [Deploy to Production](production.md)

---

## The Problem

Manual deployment is error-prone and slow:

**Issues:**
- Forgetting to run tests before deploying
- Inconsistent build environments
- Manual Docker builds and pushes
- No automated rollback
- Deployment downtime
- Human error in production

---

## The Solution

Automated CI/CD pipeline:

```yaml
# .github/workflows/ci.yml
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: pytest
      - name: Deploy
        if: github.ref == 'refs/heads/main'
        run: ./deploy.sh
```

**Benefits:**
- Automated testing on every commit
- Consistent builds
- Automatic deployments
- Fast feedback
- Rollback on failure

---

## Step 1: GitHub Actions - Basic CI

### Test on Every Push

```yaml
# .github/workflows/test.yml
name: Test

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - name: Checkout code
      uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov

    - name: Run tests with contracts enabled
      env:
        PW_DISABLE_CONTRACTS: 0  # Enable contracts for testing
      run: |
        pytest --cov=. --cov-report=term-missing

    - name: Check test coverage
      run: |
        pytest --cov=. --cov-report=xml
        coverage report --fail-under=80
```

---

## Step 2: Multi-Language Testing

### Test Python + JavaScript + Go

```yaml
# .github/workflows/multi-lang.yml
name: Multi-Language Tests

on: [push, pull_request]

jobs:
  test-python:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    - run: pip install -r requirements.txt
    - run: pytest tests/

  test-javascript:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - uses: actions/setup-node@v3
      with:
        node-version: '18'
    - run: npm ci
    - run: npm test

  test-go:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - uses: actions/setup-go@v4
      with:
        go-version: '1.21'
    - run: go test ./...
```

---

## Step 3: Build and Push Docker Image

### Docker Build on Main

```yaml
# .github/workflows/docker.yml
name: Build and Push Docker Image

on:
  push:
    branches: [ main ]
    tags: [ 'v*' ]

jobs:
  docker:
    runs-on: ubuntu-latest

    steps:
    - name: Checkout code
      uses: actions/checkout@v3

    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v2

    - name: Log in to Docker Hub
      uses: docker/login-action@v2
      with:
        username: ${{ secrets.DOCKER_USERNAME }}
        password: ${{ secrets.DOCKER_PASSWORD }}

    - name: Extract metadata
      id: meta
      uses: docker/metadata-action@v4
      with:
        images: myorg/myapp
        tags: |
          type=ref,event=branch
          type=semver,pattern={{version}}
          type=sha

    - name: Build and push
      uses: docker/build-push-action@v4
      with:
        context: .
        push: true
        tags: ${{ steps.meta.outputs.tags }}
        labels: ${{ steps.meta.outputs.labels }}
        cache-from: type=registry,ref=myorg/myapp:latest
        cache-to: type=inline
```

---

## Step 4: Automated Deployment

### Deploy to Production

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    - run: pip install -r requirements.txt
    - run: pytest

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: success()

    steps:
    - name: Checkout code
      uses: actions/checkout@v3

    - name: Set up kubectl
      uses: azure/setup-kubectl@v3

    - name: Configure kubectl
      run: |
        echo "${{ secrets.KUBE_CONFIG }}" > kubeconfig
        export KUBECONFIG=kubeconfig

    - name: Deploy to Kubernetes
      run: |
        kubectl set image deployment/myapp \
          myapp=myorg/myapp:${{ github.sha }}

        kubectl rollout status deployment/myapp

    - name: Verify deployment
      run: |
        kubectl get pods -l app=myapp
        kubectl logs -l app=myapp --tail=50

    - name: Rollback on failure
      if: failure()
      run: |
        kubectl rollout undo deployment/myapp
```

---

## Step 5: GitLab CI/CD

### Complete Pipeline

```yaml
# .gitlab-ci.yml
stages:
  - test
  - build
  - deploy

variables:
  DOCKER_IMAGE: $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA

# Run tests with contracts enabled
test:
  stage: test
  image: python:3.11
  variables:
    PW_DISABLE_CONTRACTS: 0  # Enable for testing
  script:
    - pip install -r requirements.txt
    - pytest --cov=. --cov-report=term-missing
  coverage: '/TOTAL.*\s+(\d+%)$/'
  only:
    - merge_requests
    - main

# Build Docker image
build:
  stage: build
  image: docker:24.0
  services:
    - docker:24.0-dind
  script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
    - docker build -t $DOCKER_IMAGE .
    - docker push $DOCKER_IMAGE
  only:
    - main

# Deploy to production
deploy:production:
  stage: deploy
  image: bitnami/kubectl:latest
  script:
    - kubectl config use-context $KUBE_CONTEXT
    - kubectl set image deployment/myapp myapp=$DOCKER_IMAGE
    - kubectl rollout status deployment/myapp
  environment:
    name: production
    url: https://app.example.com
  only:
    - main
  when: manual  # Require manual approval
```

---

## Step 6: Testing Strategies

### Test Matrix

```yaml
# .github/workflows/matrix.yml
name: Test Matrix

on: [push, pull_request]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        python-version: ['3.9', '3.10', '3.11', '3.12']

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install dependencies
      run: pip install -r requirements.txt

    - name: Run tests with contracts
      env:
        PW_DISABLE_CONTRACTS: 0
      run: pytest
```

### Parallel Tests

```yaml
# .github/workflows/parallel.yml
name: Parallel Tests

on: [push]

jobs:
  test-unit:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - run: pip install -r requirements.txt
    - run: pytest tests/unit/

  test-integration:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - run: pip install -r requirements.txt
    - run: pytest tests/integration/

  test-e2e:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - run: pip install -r requirements.txt
    - run: pytest tests/e2e/
```

---

## Step 7: Secrets Management

### Store Secrets Safely

**GitHub Secrets:**
```
Settings → Secrets and variables → Actions → New repository secret
```

**Add secrets:**
- `DOCKER_USERNAME` - Docker Hub username
- `DOCKER_PASSWORD` - Docker Hub password
- `KUBE_CONFIG` - Kubernetes config
- `DATABASE_URL` - Production database URL

**Use in workflow:**
```yaml
steps:
  - name: Deploy with secrets
    env:
      DATABASE_URL: ${{ secrets.DATABASE_URL }}
      API_KEY: ${{ secrets.API_KEY }}
    run: |
      ./deploy.sh
```

---

## Step 8: Deployment Strategies

### Blue-Green Deployment

```yaml
# .github/workflows/blue-green.yml
name: Blue-Green Deployment

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - name: Deploy to green
      run: |
        kubectl apply -f deployment-green.yaml

    - name: Wait for green to be ready
      run: |
        kubectl wait --for=condition=available \
          deployment/myapp-green --timeout=300s

    - name: Run smoke tests
      run: |
        curl https://green.example.com/health

    - name: Switch traffic to green
      run: |
        kubectl patch service myapp-service \
          -p '{"spec":{"selector":{"version":"green"}}}'

    - name: Delete blue deployment
      run: |
        sleep 60  # Keep blue for 1 minute
        kubectl delete deployment myapp-blue
```

### Canary Deployment

```yaml
# deployment-canary.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp-canary
spec:
  replicas: 1  # 10% of traffic (1 of 10 pods)
  template:
    metadata:
      labels:
        app: myapp
        track: canary
    spec:
      containers:
      - name: myapp
        image: myapp:v1.1.0
```

```yaml
# .github/workflows/canary.yml
name: Canary Deployment

on:
  push:
    branches: [ main ]

jobs:
  canary:
    runs-on: ubuntu-latest
    steps:
    - name: Deploy canary
      run: kubectl apply -f deployment-canary.yaml

    - name: Wait 5 minutes
      run: sleep 300

    - name: Check error rates
      run: |
        # Query Prometheus for error rate
        ERROR_RATE=$(curl -s 'http://prometheus:9090/api/v1/query?query=rate(errors_total[5m])')

        if [ $ERROR_RATE -gt 0.01 ]; then
          echo "Error rate too high, rolling back"
          kubectl delete deployment myapp-canary
          exit 1
        fi

    - name: Promote canary
      run: |
        kubectl scale deployment/myapp-canary --replicas=10
        kubectl scale deployment/myapp-stable --replicas=0
```

---

## Step 9: Performance Testing in CI

### Load Test Before Deploy

```yaml
# .github/workflows/load-test.yml
name: Load Test

on:
  pull_request:
    branches: [ main ]

jobs:
  load-test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Start application
      run: |
        docker-compose up -d
        sleep 10

    - name: Run load test
      run: |
        # Using k6
        docker run --network host \
          grafana/k6 run - <load-test.js

    - name: Check results
      run: |
        # Fail if p95 latency > 500ms
        if [ $(k6 stats | grep p95 | awk '{print $2}') -gt 500 ]; then
          echo "Performance regression detected"
          exit 1
        fi

    - name: Cleanup
      if: always()
      run: docker-compose down
```

**load-test.js:**
```javascript
import http from 'k6/http';
import { check } from 'k6';

export const options = {
  stages: [
    { duration: '1m', target: 100 },  // Ramp up
    { duration: '3m', target: 100 },  // Stay at 100 RPS
    { duration: '1m', target: 0 },    // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'],  // 95% of requests < 500ms
    http_req_failed: ['rate<0.01'],    // Error rate < 1%
  },
};

export default function () {
  const res = http.get('http://localhost:8000/api/users');
  check(res, {
    'status is 200': (r) => r.status === 200,
  });
}
```

---

## Step 10: Notifications

### Slack Notifications

```yaml
# .github/workflows/notify.yml
name: Deploy with Notifications

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
    - name: Deploy
      id: deploy
      run: ./deploy.sh

    - name: Notify Slack on success
      if: success()
      uses: slackapi/slack-github-action@v1
      with:
        payload: |
          {
            "text": "✅ Deployment successful: ${{ github.sha }}",
            "blocks": [
              {
                "type": "section",
                "text": {
                  "type": "mrkdwn",
                  "text": "✅ *Deployment Successful*\nCommit: `${{ github.sha }}`\nBranch: `${{ github.ref_name }}`"
                }
              }
            ]
          }
      env:
        SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}

    - name: Notify Slack on failure
      if: failure()
      uses: slackapi/slack-github-action@v1
      with:
        payload: |
          {
            "text": "❌ Deployment failed: ${{ github.sha }}"
          }
      env:
        SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
```

---

## CI/CD Checklist

**Testing:**
- ✅ Unit tests run on every commit
- ✅ Integration tests run on PRs
- ✅ E2E tests run before deploy
- ✅ Contracts enabled during testing (`PW_DISABLE_CONTRACTS=0`)
- ✅ Code coverage tracked
- ✅ Performance tests before deploy

**Building:**
- ✅ Docker images built automatically
- ✅ Images tagged with commit SHA
- ✅ Build cache configured
- ✅ Multi-stage builds for size

**Deployment:**
- ✅ Automated deployment to staging
- ✅ Manual approval for production
- ✅ Rolling updates configured
- ✅ Health checks verified
- ✅ Automatic rollback on failure

**Security:**
- ✅ Secrets stored securely
- ✅ Dependency scanning enabled
- ✅ Container image scanning
- ✅ HTTPS/TLS enforced

---

## Summary

**GitHub Actions CI:**
```yaml
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: pip install -r requirements.txt
      - run: pytest  # Contracts enabled
```

**Deploy:**
```yaml
deploy:
  needs: test
  steps:
    - run: kubectl set image deployment/myapp myapp:${{ github.sha }}
    - run: kubectl rollout status deployment/myapp
```

**Key practices:**
- Test with contracts enabled
- Deploy with contracts disabled
- Automate everything
- Fast feedback (<5 minutes)
- Rollback on failure

---

## Next Steps

- **[Monitor Contract Violations](monitoring.md)** - Track violations in production
- **[Deploy to Production](production.md)** - Production deployment guide
- **[Optimize Performance](../advanced/performance.md)** - Optimize for speed

---

## See Also

- **[GitHub Actions Docs](https://docs.github.com/en/actions)** - Official documentation
- **[GitLab CI/CD Docs](https://docs.gitlab.com/ee/ci/)** - GitLab CI guide
- **[Cookbook: CI/CD Patterns](../../cookbook/)** - CI/CD recipes

---

**Difficulty:** Advanced
**Time:** 45 minutes
**Last Updated:** 2025-10-15
