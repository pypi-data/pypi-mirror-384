lang python
agent orchestrator
port 23457

expose workflow.execute@v1:
  params:
    pr_url string
  returns:
    workflow_id string
    status string
    review_id string

expose workflow.status@v1:
  params:
    workflow_id string
  returns:
    status string
    steps array