lang python
agent monitored-service
port 23456

observability:
  traces: true
  metrics: true
  logs: structured
  export_to: console

expose task.execute@v1:
  params:
    task_id string
    priority int
  returns:
    result string
    status string

expose task.status@v1:
  params:
    task_id string
  returns:
    status string
    progress int