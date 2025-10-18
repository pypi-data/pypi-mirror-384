lang python
agent deployment-manager
port 23456
temporal: true

workflow deploy_service@v1:
  params:
    service string
    version string
  returns:
    deployment_id string
    status string

  steps:
    - activity: build_image
      timeout: 10m
      retry: 3

    - activity: run_tests
      timeout: 5m
      retry: 2

    - activity: deploy_to_staging
      timeout: 3m
      on_failure: rollback_staging

    - activity: health_check
      timeout: 2m

    - activity: deploy_to_production
      timeout: 5m
      on_failure: rollback_production
      requires_approval: true

expose workflow.execute@v1:
  params:
    workflow_id string
    params object
  returns:
    execution_id string
    status string