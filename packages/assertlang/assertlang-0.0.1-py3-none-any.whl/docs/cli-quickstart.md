# AssertLang CLI Quickstart

Get started with AssertLang in 5 minutes.

## Installation

```bash
git clone https://github.com/promptware/promptware.git
cd promptware
pip install -e .

# Add to PATH for global access
export PATH="$(pwd)/bin:$PATH"
```

## Your First Agent

### 1. Create Agent

```bash
promptware init hello-world --template basic
```

This creates `hello-world.pw`:

```
agent hello-world

port 3000

expose task.execute@v1 (
    task: string
) -> (
    result: string
)
```

### 2. Customize (Optional)

Edit `hello-world.pw` to add tools:

```
agent hello-world

port 3000

tools: http, logger

expose api.call@v1 (
    url: string,
    method: string
) -> (
    response: object,
    status: int
)
```

### 3. Validate

```bash
promptware validate hello-world.al --verbose
```

Output:
```
🔍 Validating hello-world.pw...
✓ Syntax valid

📋 Agent Details:
  Name: hello-world
  Port: 3000
  Verbs: 1
    - api.call@v1 (2 params, 2 returns)
  Tools: http, logger
```

### 4. Generate Server

```bash
promptware generate hello-world.al --lang python
```

Output:
```
📖 Reading hello-world.pw...
✓ Parsed agent: hello-world
  Port: 3000
  Verbs: 1
  Tools: 2

🔨 Generating python server...
✓ Generated: ./generated/hello-world/hello-world_server.py
✓ Created: ./generated/hello-world/requirements.txt

📦 Next steps:
  cd ./generated/hello-world
  pip install -r requirements.txt
  python hello-world_server.py

✨ Server generated successfully!
```

### 5. Run Server

```bash
cd generated/hello-world
pip install -r requirements.txt
python hello-world_server.py
```

Output:
```
Starting MCP server for agent: hello-world
Port: 3000
Exposed verbs: ['api.call@v1']
Health check: http://127.0.0.1:3000/health
Readiness check: http://127.0.0.1:3000/ready
MCP endpoint: http://127.0.0.1:3000/mcp
INFO:     Uvicorn running on http://127.0.0.1:3000
```

### 6. Test Server

```bash
# Health check
curl http://localhost:3000/health

# List verbs
curl http://localhost:3000/verbs

# Call verb
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "api.call@v1",
      "arguments": {
        "url": "https://api.example.com",
        "method": "GET"
      }
    }
  }'
```

## Common Use Cases

### API Service Agent

```bash
# Create API agent
promptware init api-service --template api --port 8080

# Generated agent includes http, auth, logger tools
cat api-service.al
```

### AI-Powered Agent

```bash
# Create AI agent
promptware init chatbot --template ai

# Set API key
export ANTHROPIC_API_KEY="your-key-here"

# Generate and run
promptware generate chatbot.al --lang python
cd generated/chatbot
pip install -r requirements.txt
python chatbot_server.py
```

### Multi-Language Deployment

```bash
# Generate same agent in multiple languages
promptware generate my-agent.al --lang python --output ./servers/python
promptware generate my-agent.al --lang nodejs --output ./servers/nodejs
promptware generate my-agent.al --lang go --output ./servers/go

# Each server is production-ready with:
# - Error handling
# - Health checks (/health, /ready)
# - Rate limiting (100 req/min)
# - CORS
# - Security headers
```

## CLI Commands Cheatsheet

```bash
# Create agent
promptware init <name> [--template basic|api|workflow|ai] [--port 3000]

# Validate agent
promptware validate <file.al> [--verbose]

# List available tools
promptware list-tools [--lang python|nodejs|go|csharp|rust] [--category "HTTP & APIs"]

# Generate server
promptware generate <file.al> [--lang python] [--output ./dir] [--build]

# Get help
promptware help [command]
promptware --version
```

## Templates

### basic
Simple agent with single verb.

```
agent my-agent
port 3000

expose task.execute@v1 (
    task: string
) -> (
    result: string
)
```

### api
API agent with HTTP tools.

```
agent my-agent
port 3000

tools: http, auth, logger

expose api.call@v1 (
    endpoint: string,
    method: string
) -> (
    response: object,
    status: int
)
```

### workflow
Workflow agent with scheduler.

```
agent my-agent
port 3000

tools: scheduler, async, logger

expose workflow.start@v1 (
    workflow_id: string,
    params: object
) -> (
    execution_id: string,
    status: string
)
```

### ai
AI-powered agent with LLM.

```
agent my-agent
port 3000

llm: anthropic claude-3-5-sonnet-20241022

prompt: "You are a helpful AI assistant."

expose chat.message@v1 (
    message: string
) -> (
    response: string
)
```

## Next Steps

- [Full CLI Reference](./cli-guide.md)
- [Writing .al Agents](./promptware-dsl-spec.md)
- [Production Deployment](./production-hardening.md)
- [Tool Development](./tool-development.md)
