lang python
agent test-tool-agent
port 23460

tools:
  - http

expose fetch.url@v1:
  params:
    url string
    method string
  returns:
    status int
    body string
    summary string
