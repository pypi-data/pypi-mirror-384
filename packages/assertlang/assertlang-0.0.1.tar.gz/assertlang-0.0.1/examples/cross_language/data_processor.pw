lang nodejs
agent data-processor
port 23500

expose data.transform@v1:
  params:
    input string
    format string
  returns:
    output string
    status string

expose data.validate@v1:
  params:
    data object
    schema string
  returns:
    valid bool
    errors array