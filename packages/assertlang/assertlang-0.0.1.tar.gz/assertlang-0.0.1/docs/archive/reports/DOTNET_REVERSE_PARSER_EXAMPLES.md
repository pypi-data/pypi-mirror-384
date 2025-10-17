# .NET/C# Reverse Parser Examples

This document demonstrates the .NET/C# reverse parser that extracts PW DSL from ASP.NET Core servers.

## Overview

The .NET reverse parser (`reverse_parsers/dotnet_parser.py`) can parse C# ASP.NET Core code and extract:
- Agent name
- Port configuration
- Verbs/handlers
- Parameters and returns
- Tools configuration
- Framework detection

## Example 1: Minimal Echo Server

### Original PW DSL
```pw
lang dotnet
agent minimal-dotnet-agent
port 5002

expose echo@v1:
  params:
    message string
  returns:
    echo string
    timestamp string
```

### Generated C# Code (excerpt)
```csharp
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http;

namespace UserServiceMcp;

public static class VerbHandlers
{
    // Handler for echo@v1
    public static Dictionary<string, object> HandleEchoV1(Dictionary<string, object> parameters)
    {
        if (!parameters.ContainsKey("message"))
        {
            return new Dictionary<string, object>
            {
                ["error"] = new Dictionary<string, object>
                {
                    ["code"] = "E_ARGS",
                    ["message"] = "Missing required parameter: message"
                }
            };
        }

        return new Dictionary<string, object>
        {
            ["echo"] = "echo_value",
            ["timestamp"] = "timestamp_value"
        };
    }
}

// ... MCP routing ...

var port = "5002";
app.Run($"http://127.0.0.1:{port}");
```

### Extracted PW DSL
```pw
# Extracted from dotnet code
# Framework: aspnetcore
# Confidence: 90%

lang dotnet
agent minimal-dotnet-agent
port 5002

expose echo@v1:
  params:
    message string
  returns:
    echo string
    timestamp string
```

**Result**: ✅ Perfect round-trip! 100% match.

## Example 2: Server with Tools

### Original PW DSL
```pw
lang dotnet
agent dotnet-http-agent
port 5001

tools:
  - http

expose fetch.data@v1:
  params:
    url string
  returns:
    status int
    body string
    success bool
```

### Generated C# Code (excerpt)
```csharp
// Tool registry
public static class ToolRegistry
{
    private static readonly Dictionary<string, Func<Dictionary<string, object>, Dictionary<string, object>>> Handlers = new()
    {
        { "http", HttpHandler.Handle }
    };

    public static Dictionary<string, Dictionary<string, object>> ExecuteTools(Dictionary<string, object> parameters)
    {
        var configuredTools = new[] { "http" };
        var results = new Dictionary<string, Dictionary<string, object>>();

        foreach (var toolName in configuredTools)
        {
            results[toolName] = ExecuteTool(toolName, parameters);
        }

        return results;
    }
}

// Verb handlers
public static class VerbHandlers
{
    // Handler for fetch.data@v1
    public static Dictionary<string, object> HandleFetchDataV1(Dictionary<string, object> parameters)
    {
        if (!parameters.ContainsKey("url"))
        {
            return new Dictionary<string, object>
            {
                ["error"] = new Dictionary<string, object>
                {
                    ["code"] = "E_ARGS",
                    ["message"] = "Missing required parameter: url"
                }
            };
        }

        return new Dictionary<string, object>
        {
            ["status"] = 0,
            ["body"] = "body_value",
            ["success"] = true
        };
    }
}
```

### Extracted PW DSL
```pw
# Extracted from dotnet code
# Framework: aspnetcore
# Confidence: 90%

lang dotnet
agent dotnet-http-agent
port 5001

tools:
  - http

expose fetch.data@v1:
  params:
    url string
  returns:
    status int
    body string
    success bool
```

**Result**: ✅ Perfect round-trip! 100% match with tools.

## Pattern Detection

The parser recognizes these C# patterns:

### 1. Handler Methods
```csharp
// Pattern: HandleVerbNameV1
public static Dictionary<string, object> HandleEchoV1(Dictionary<string, object> parameters)
public static Dictionary<string, object> HandleFetchDataV1(Dictionary<string, object> parameters)

// Extracted as:
// echo@v1
// fetch.data@v1
```

### 2. Parameter Validation
```csharp
if (!parameters.ContainsKey("message"))
{
    return new Dictionary<string, object>
    {
        ["error"] = new Dictionary<string, object>
        {
            ["code"] = "E_ARGS",
            ["message"] = "Missing required parameter: message"
        }
    };
}

// Extracted as:
// params:
//   message string
```

### 3. Return Values
```csharp
return new Dictionary<string, object>
{
    ["status"] = 0,
    ["body"] = "body_value",
    ["success"] = true
};

// Extracted as:
// returns:
//   status int
//   body string
//   success bool
```

### 4. Tools Configuration
```csharp
var configuredTools = new[] { "http", "database", "email" };

// Extracted as:
// tools:
//   - http
//   - database
//   - email
```

### 5. Port Configuration
```csharp
var port = "5001";
app.Run($"http://127.0.0.1:{port}");

// Extracted as:
// port 5001
```

### 6. Agent Name
```csharp
serverInfo = new { name = "dotnet-http-agent", version = "v1" }

// OR from namespace:
namespace UserServiceMcp;

// Extracted as:
// agent dotnet-http-agent
```

## XML Documentation Support

The parser also supports XML doc comments:

```csharp
/// <summary>
/// Handle fetch data request
/// </summary>
/// <param name="params.url">(string) URL to fetch</param>
/// <param name="params.timeout">(int) Timeout in seconds</param>
/// <returns>
/// - status (int): HTTP status code
/// - body (string): Response body
/// - success (bool): Whether request succeeded
/// </returns>
public static Dictionary<string, object> HandleFetchDataV1(Dictionary<string, object> parameters)
{
    // Implementation
}
```

## Usage

### Via CLI
```bash
# Parse C# file
python3 reverse_parsers/cli.py Program.cs

# With metadata
python3 reverse_parsers/cli.py Program.cs --metadata

# Save to file
python3 reverse_parsers/cli.py Program.cs -o agent.pw

# Verbose mode
python3 reverse_parsers/cli.py Program.cs --verbose
```

### Programmatically
```python
from reverse_parsers.dotnet_parser import DotNetReverseParser

parser = DotNetReverseParser()
extracted = parser.parse_file("Program.cs")

print(f"Agent: {extracted.name}")
print(f"Port: {extracted.port}")
print(f"Verbs: {len(extracted.verbs)}")
print(f"Tools: {extracted.tools}")
print(f"Confidence: {extracted.confidence_score:.0%}")

# Convert to PW DSL
pw_dsl = parser.to_pw_dsl(extracted, include_metadata=True)
print(pw_dsl)
```

## Test Results

Running the test suite:
```bash
python3 test_dotnet_reverse_parser.py
```

**Results**:
```
================================================================================
.NET REVERSE PARSER TESTS
================================================================================

Found 2 .NET fixtures:
  - dotnet_with_tools.pw
  - dotnet_minimal.pw

Testing: dotnet_with_tools.pw
--------------------------------------------------------------------------------
✓ All verbs extracted correctly!
✓ All tools extracted correctly!
Confidence Score: 90%
Verbs Coverage: 100%
Params Extracted: 1
Returns Extracted: 3

Testing: dotnet_minimal.pw
--------------------------------------------------------------------------------
✓ All verbs extracted correctly!
✓ All tools extracted correctly!
Confidence Score: 90%
Verbs Coverage: 100%
Params Extracted: 1
Returns Extracted: 2

================================================================================
SUMMARY
================================================================================
✓ PASS: dotnet_with_tools.pw
✓ PASS: dotnet_minimal.pw

Total: 2/2 passed (100%)
```

## Success Criteria

✅ **All criteria met:**
- Extract all verbs from generated .NET code: **100%**
- Confidence score for generated code: **90%+**
- Round-trip works (PW → .NET → PW): **100% match**
- Parameter extraction: **100%**
- Return value extraction: **100%**
- Tools extraction: **100%**
- Port extraction: **100%**
- Agent name extraction: **100%**

## Implementation Details

The parser uses regex-based extraction (like other AssertLang parsers):

1. **Framework Detection**: Looks for `using Microsoft.AspNetCore`
2. **Handler Extraction**: Matches `HandleVerbNameV1` method signatures
3. **Parameter Extraction**: Scans `ContainsKey` validation checks
4. **Return Extraction**: Parses dictionary initializers in return statements
5. **Tools Extraction**: Finds `var configuredTools = new[] { ... }` arrays
6. **Port Extraction**: Extracts from `var port = "5001"` and `app.Run()`
7. **Agent Name Extraction**: From `serverInfo` or namespace conversion

## Notes

- The parser achieves 90%+ confidence for generated code
- It successfully handles both minimal and complex agents
- Round-trip conversion (PW → C# → PW) is lossless
- The implementation follows the same pattern as Python/Node.js/Rust parsers
- ASP.NET Core framework is automatically detected
