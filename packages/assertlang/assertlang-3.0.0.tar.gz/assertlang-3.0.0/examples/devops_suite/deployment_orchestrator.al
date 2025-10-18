lang python
agent deployment-orchestrator
port 23452
temporal: true
llm anthropic claude-3-5-sonnet-20241022

observability:
  traces: true
  metrics: true
  logs: structured
  export_to: console

prompt_template:
  You are a DevOps orchestrator that coordinates code reviews, testing, and deployments.
  Make intelligent decisions about deployment readiness based on review and test results.

workflow ci_cd_pipeline@v1:
  params:
    service string
    version string
    branch string
    commit_sha string
  returns:
    deployment_id string
    status string
    deployed_at string

  steps:
    - activity: fetch_code_changes
      timeout: 5m
      retry: 2

    - activity: run_code_review
      timeout: 10m
      retry: 1
      on_failure: notify_review_failure

    - activity: run_tests
      timeout: 15m
      retry: 2
      on_failure: notify_test_failure

    - activity: build_artifacts
      timeout: 20m
      retry: 1

    - activity: deploy_to_staging
      timeout: 10m
      on_failure: rollback_staging

    - activity: run_smoke_tests
      timeout: 5m
      retry: 1

    - activity: deploy_to_production
      timeout: 15m
      requires_approval: true
      on_failure: rollback_production

    - activity: verify_deployment
      timeout: 5m
      retry: 2

expose workflow.execute@v1:
  params:
    workflow_id string
    params object
  returns:
    execution_id string
    status string

expose deployment.status@v1:
  params:
    deployment_id string
  returns:
    status string
    current_step string
    progress int

expose deployment.approve@v1:
  params:
    deployment_id string
    approved bool
    approver string
  returns:
    status string
  prompt_template:
    Evaluate if this deployment should be approved based on:
    - Code review results
    - Test coverage and results
    - Staging environment health
    - Risk assessment

    Provide recommendation: approve/reject with reasoning.