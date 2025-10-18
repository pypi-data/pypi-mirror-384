lang python
agent test-runner
port 23451

observability:
  traces: true
  metrics: true
  logs: structured
  export_to: console

expose test.run@v1:
  params:
    project_path string
    test_suite string
    environment string
  returns:
    test_id string
    status string
    total_tests int
    passed int
    failed int

expose test.status@v1:
  params:
    test_id string
  returns:
    status string
    progress int
    results array

expose test.report@v1:
  params:
    test_id string
  returns:
    report string
    coverage float
    duration float