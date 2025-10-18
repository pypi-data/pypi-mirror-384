"""
Shared error handling patterns for MCP server generators.

Provides consistent error codes, validation, and middleware across all languages.
"""


# Standard MCP error codes
ERROR_CODES = {
    # JSON-RPC standard errors
    "PARSE_ERROR": -32700,
    "INVALID_REQUEST": -32600,
    "METHOD_NOT_FOUND": -32601,
    "INVALID_PARAMS": -32602,
    "INTERNAL_ERROR": -32603,

    # MCP-specific errors
    "E_ARGS": -32000,
    "E_TOOL_NOT_FOUND": -32001,
    "E_VERB_NOT_FOUND": -32002,
    "E_RUNTIME": -32003,
    "E_TIMEOUT": -32004,
    "E_AUTH": -32005,
    "E_RATE_LIMIT": -32006,
    "E_VALIDATION": -32007,
}


def get_python_error_middleware() -> str:
    """Generate Python error handling middleware."""
    return '''
# Error handling middleware
import logging
import traceback
from functools import wraps

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def handle_errors(func):
    """Decorator for consistent error handling."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except ValueError as e:
            logger.error(f"Validation error: {e}")
            return {
                "error": {
                    "code": -32602,
                    "message": f"Invalid parameters: {str(e)}"
                }
            }
        except TimeoutError as e:
            logger.error(f"Timeout: {e}")
            return {
                "error": {
                    "code": -32004,
                    "message": f"Operation timed out: {str(e)}"
                }
            }
        except Exception as e:
            logger.error(f"Unexpected error: {e}\\n{traceback.format_exc()}")
            return {
                "error": {
                    "code": -32603,
                    "message": "Internal server error",
                    "data": str(e) if os.environ.get("DEBUG") else None
                }
            }
    return wrapper
'''


def get_nodejs_error_middleware() -> str:
    """Generate Node.js error handling middleware."""
    return '''
// Error handling middleware
const winston = require('winston');

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  transports: [
    new winston.transports.Console({
      format: winston.format.simple()
    })
  ]
});

function handleError(error, req) {
  logger.error('Request error:', {
    error: error.message,
    stack: error.stack,
    method: req?.method,
    path: req?.path
  });

  if (error.name === 'ValidationError') {
    return {
      jsonrpc: '2.0',
      id: req?.id || null,
      error: {
        code: -32602,
        message: `Invalid parameters: ${error.message}`
      }
    };
  }

  if (error.name === 'TimeoutError') {
    return {
      jsonrpc: '2.0',
      id: req?.id || null,
      error: {
        code: -32004,
        message: `Operation timed out: ${error.message}`
      }
    };
  }

  return {
    jsonrpc: '2.0',
    id: req?.id || null,
    error: {
      code: -32603,
      message: 'Internal server error',
      data: process.env.DEBUG ? error.message : undefined
    }
  };
}
'''


def get_go_error_middleware() -> str:
    """Generate Go error handling middleware."""
    return '''
// Error handling
import (
\t"log"
\t"os"
)

type MCPError struct {
\tCode    int    `json:"code"`
\tMessage string `json:"message"`
\tData    string `json:"data,omitempty"`
}

func handleError(err error, errType string) map[string]interface{} {
\tlog.Printf("Error [%s]: %v", errType, err)

\tvar code int
\tvar message string

\tswitch errType {
\tcase "validation":
\t\tcode = -32602
\t\tmessage = "Invalid parameters: " + err.Error()
\tcase "timeout":
\t\tcode = -32004
\t\tmessage = "Operation timed out: " + err.Error()
\tcase "not_found":
\t\tcode = -32601
\t\tmessage = err.Error()
\tdefault:
\t\tcode = -32603
\t\tmessage = "Internal server error"
\t}

\tresponse := map[string]interface{}{
\t\t"code":    code,
\t\t"message": message,
\t}

\tif os.Getenv("DEBUG") != "" {
\t\tresponse["data"] = err.Error()
\t}

\treturn response
}
'''


def get_csharp_error_middleware() -> str:
    """Generate C# error handling middleware."""
    return '''
// Error handling
using Microsoft.Extensions.Logging;

public static class ErrorHandler
{
    private static readonly ILogger Logger = LoggerFactory
        .Create(builder => builder.AddConsole())
        .CreateLogger("MCP");

    public static Dictionary<string, object> HandleError(Exception ex, string errorType = "internal")
    {
        Logger.LogError(ex, "Error [{ErrorType}]: {Message}", errorType, ex.Message);

        int code;
        string message;

        switch (errorType)
        {
            case "validation":
                code = -32602;
                message = $"Invalid parameters: {ex.Message}";
                break;
            case "timeout":
                code = -32004;
                message = $"Operation timed out: {ex.Message}";
                break;
            case "not_found":
                code = -32601;
                message = ex.Message;
                break;
            default:
                code = -32603;
                message = "Internal server error";
                break;
        }

        var error = new Dictionary<string, object>
        {
            ["code"] = code,
            ["message"] = message
        };

        if (Environment.GetEnvironmentVariable("DEBUG") != null)
        {
            error["data"] = ex.Message;
        }

        return error;
    }
}
'''


def get_rust_error_middleware() -> str:
    """Generate Rust error handling middleware."""
    return '''
// Error handling
use std::env;

#[derive(Debug)]
pub enum McpError {
    Validation(String),
    Timeout(String),
    NotFound(String),
    Internal(String),
}

impl McpError {
    pub fn to_json(&self) -> Value {
        let (code, message_prefix) = match self {
            McpError::Validation(_) => (-32602, "Invalid parameters"),
            McpError::Timeout(_) => (-32004, "Operation timed out"),
            McpError::NotFound(_) => (-32601, "Not found"),
            McpError::Internal(_) => (-32603, "Internal server error"),
        };

        let message = match self {
            McpError::Validation(msg) |
            McpError::Timeout(msg) |
            McpError::NotFound(msg) |
            McpError::Internal(msg) => format!("{}: {}", message_prefix, msg),
        };

        let mut error = json!({
            "code": code,
            "message": message
        });

        if env::var("DEBUG").is_ok() {
            if let Value::Object(ref mut map) = error {
                map.insert("data".to_string(), json!(self.to_string()));
            }
        }

        error
    }
}
'''


def get_validation_helpers(language: str) -> str:
    """Get parameter validation helpers for a language."""
    if language == "python":
        return '''
def validate_params(params: dict, required: list[str], types: dict[str, type] = None) -> tuple[bool, str]:
    """Validate request parameters."""
    for param in required:
        if param not in params:
            return False, f"Missing required parameter: {param}"

    if types:
        for param, expected_type in types.items():
            if param in params and not isinstance(params[param], expected_type):
                return False, f"Parameter '{param}' must be of type {expected_type.__name__}"

    return True, ""
'''
    elif language == "nodejs":
        return '''
function validateParams(params, required, types = {}) {
  for (const param of required) {
    if (!(param in params)) {
      throw new ValidationError(`Missing required parameter: ${param}`);
    }
  }

  for (const [param, expectedType] of Object.entries(types)) {
    if (param in params && typeof params[param] !== expectedType) {
      throw new ValidationError(`Parameter '${param}' must be of type ${expectedType}`);
    }
  }
}

class ValidationError extends Error {
  constructor(message) {
    super(message);
    this.name = 'ValidationError';
  }
}
'''
    elif language == "go":
        return '''
func validateParams(params map[string]interface{}, required []string) error {
\tfor _, param := range required {
\t\tif _, ok := params[param]; !ok {
\t\t\treturn fmt.Errorf("missing required parameter: %s", param)
\t\t}
\t}
\treturn nil
}
'''
    elif language == "csharp":
        return '''
public static void ValidateParams(Dictionary<string, object> parameters, string[] required)
{
    foreach (var param in required)
    {
        if (!parameters.ContainsKey(param))
        {
            throw new ArgumentException($"Missing required parameter: {param}");
        }
    }
}
'''
    elif language == "rust":
        return '''
fn validate_params(params: &Value, required: &[&str]) -> Result<(), McpError> {
    let obj = params.as_object()
        .ok_or_else(|| McpError::Validation("Parameters must be an object".to_string()))?;

    for param in required {
        if !obj.contains_key(*param) {
            return Err(McpError::Validation(format!("Missing required parameter: {}", param)));
        }
    }

    Ok(())
}
'''
    return ""
