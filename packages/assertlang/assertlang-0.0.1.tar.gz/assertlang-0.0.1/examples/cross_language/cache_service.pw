lang go
agent cache-service
port 23501

expose cache.get@v1:
  params:
    key string
  returns:
    value string
    found bool

expose cache.set@v1:
  params:
    key string
    value string
    ttl int
  returns:
    success bool

expose cache.delete@v1:
  params:
    key string
  returns:
    deleted bool