"""
PW Operations MCP Server
Provides operation implementations for multiple target languages via JSON-RPC
"""

import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Dict, Any

# Operation registry: operation_id → {target_lang → implementation}
OPERATIONS = {
    # String operations
    "str.split": {
        "python": {
            "code": "{arg0}.split({arg1})",
            "imports": [],
            "returns": "list"
        },
        "javascript": {
            "code": "{arg0}.split({arg1})",
            "imports": [],
            "returns": "Array<string>"
        },
        "go": {
            "code": "strings.Split({arg0}, {arg1})",
            "imports": ["strings"],
            "returns": "[]string"
        }
    },
    
    "str.upper": {
        "python": {
            "code": "{arg0}.upper()",
            "imports": [],
            "returns": "str"
        },
        "javascript": {
            "code": "{arg0}.toUpperCase()",
            "imports": [],
            "returns": "string"
        },
        "go": {
            "code": "strings.ToUpper({arg0})",
            "imports": ["strings"],
            "returns": "string"
        }
    },
    
    "str.lower": {
        "python": {
            "code": "{arg0}.lower()",
            "imports": [],
            "returns": "str"
        },
        "javascript": {
            "code": "{arg0}.toLowerCase()",
            "imports": [],
            "returns": "string"
        },
        "go": {
            "code": "strings.ToLower({arg0})",
            "imports": ["strings"],
            "returns": "string"
        }
    },
    
    "str.replace": {
        "python": {
            "code": "{arg0}.replace({arg1}, {arg2})",
            "imports": [],
            "returns": "str"
        },
        "javascript": {
            "code": "{arg0}.replace({arg1}, {arg2})",
            "imports": [],
            "returns": "string"
        },
        "go": {
            "code": "strings.Replace({arg0}, {arg1}, {arg2}, -1)",
            "imports": ["strings"],
            "returns": "string"
        }
    },
    
    "str.join": {
        "python": {
            "code": "{arg0}.join({arg1})",
            "imports": [],
            "returns": "str"
        },
        "javascript": {
            "code": "{arg1}.join({arg0})",
            "imports": [],
            "returns": "string"
        },
        "go": {
            "code": "strings.Join({arg1}, {arg0})",
            "imports": ["strings"],
            "returns": "string"
        }
    },
    
    "str.contains": {
        "python": {
            "code": "{arg1} in {arg0}",
            "imports": [],
            "returns": "bool"
        },
        "javascript": {
            "code": "{arg0}.includes({arg1})",
            "imports": [],
            "returns": "boolean"
        },
        "go": {
            "code": "strings.Contains({arg0}, {arg1})",
            "imports": ["strings"],
            "returns": "bool"
        }
    },
    
    "str.starts_with": {
        "python": {
            "code": "{arg0}.startswith({arg1})",
            "imports": [],
            "returns": "bool"
        },
        "javascript": {
            "code": "{arg0}.startsWith({arg1})",
            "imports": [],
            "returns": "boolean"
        },
        "go": {
            "code": "strings.HasPrefix({arg0}, {arg1})",
            "imports": ["strings"],
            "returns": "bool"
        }
    },
    
    "str.ends_with": {
        "python": {
            "code": "{arg0}.endswith({arg1})",
            "imports": [],
            "returns": "bool"
        },
        "javascript": {
            "code": "{arg0}.endsWith({arg1})",
            "imports": [],
            "returns": "boolean"
        },
        "go": {
            "code": "strings.HasSuffix({arg0}, {arg1})",
            "imports": ["strings"],
            "returns": "bool"
        }
    },
    
    # File operations
    "file.read": {
        "python": {
            "code": "Path({arg0}).read_text()",
            "imports": ["from pathlib import Path"],
            "returns": "str"
        },
        "javascript": {
            "code": "fs.readFileSync({arg0}, 'utf8')",
            "imports": ["const fs = require('fs');"],
            "returns": "string"
        },
        "go": {
            "code": "ioutil.ReadFile({arg0})",
            "imports": ["io/ioutil"],
            "returns": "[]byte, error"
        }
    },
    
    "file.write": {
        "python": {
            "code": "Path({arg0}).write_text({arg1})",
            "imports": ["from pathlib import Path"],
            "returns": "None"
        },
        "javascript": {
            "code": "fs.writeFileSync({arg0}, {arg1}, 'utf8')",
            "imports": ["const fs = require('fs');"],
            "returns": "void"
        },
        "go": {
            "code": "ioutil.WriteFile({arg0}, []byte({arg1}), 0644)",
            "imports": ["io/ioutil"],
            "returns": "error"
        }
    },
    
    "file.exists": {
        "python": {
            "code": "Path({arg0}).exists()",
            "imports": ["from pathlib import Path"],
            "returns": "bool"
        },
        "javascript": {
            "code": "fs.existsSync({arg0})",
            "imports": ["const fs = require('fs');"],
            "returns": "boolean"
        },
        "go": {
            "code": "fileExists({arg0})",
            "imports": ["os"],
            "helper": "func fileExists(path string) bool { _, err := os.Stat(path); return err == nil }",
            "returns": "bool"
        }
    },
    
    "file.delete": {
        "python": {
            "code": "Path({arg0}).unlink()",
            "imports": ["from pathlib import Path"],
            "returns": "None"
        },
        "javascript": {
            "code": "fs.unlinkSync({arg0})",
            "imports": ["const fs = require('fs');"],
            "returns": "void"
        },
        "go": {
            "code": "os.Remove({arg0})",
            "imports": ["os"],
            "returns": "error"
        }
    },
    
    # JSON operations
    "json.parse": {
        "python": {
            "code": "json.loads({arg0})",
            "imports": ["import json"],
            "returns": "Any"
        },
        "javascript": {
            "code": "JSON.parse({arg0})",
            "imports": [],
            "returns": "any"
        },
        "go": {
            "code": "json.Unmarshal([]byte({arg0}), &result)",
            "imports": ["encoding/json"],
            "returns": "error"
        }
    },
    
    "json.stringify": {
        "python": {
            "code": "json.dumps({arg0})",
            "imports": ["import json"],
            "returns": "str"
        },
        "javascript": {
            "code": "JSON.stringify({arg0})",
            "imports": [],
            "returns": "string"
        },
        "go": {
            "code": "json.Marshal({arg0})",
            "imports": ["encoding/json"],
            "returns": "[]byte, error"
        }
    },
    
    "json.stringify_pretty": {
        "python": {
            "code": "json.dumps({arg0}, indent=2)",
            "imports": ["import json"],
            "returns": "str"
        },
        "javascript": {
            "code": "JSON.stringify({arg0}, null, 2)",
            "imports": [],
            "returns": "string"
        },
        "go": {
            "code": "json.MarshalIndent({arg0}, \"\", \"  \")",
            "imports": ["encoding/json"],
            "returns": "[]byte, error"
        }
    },
    
    # Math operations
    "math.abs": {
        "python": {
            "code": "abs({arg0})",
            "imports": [],
            "returns": "float"
        },
        "javascript": {
            "code": "Math.abs({arg0})",
            "imports": [],
            "returns": "number"
        },
        "go": {
            "code": "math.Abs({arg0})",
            "imports": ["math"],
            "returns": "float64"
        }
    },
    
    "math.ceil": {
        "python": {
            "code": "math.ceil({arg0})",
            "imports": ["import math"],
            "returns": "int"
        },
        "javascript": {
            "code": "Math.ceil({arg0})",
            "imports": [],
            "returns": "number"
        },
        "go": {
            "code": "math.Ceil({arg0})",
            "imports": ["math"],
            "returns": "float64"
        }
    },
    
    "math.floor": {
        "python": {
            "code": "math.floor({arg0})",
            "imports": ["import math"],
            "returns": "int"
        },
        "javascript": {
            "code": "Math.floor({arg0})",
            "imports": [],
            "returns": "number"
        },
        "go": {
            "code": "math.Floor({arg0})",
            "imports": ["math"],
            "returns": "float64"
        }
    },
    
    "math.round": {
        "python": {
            "code": "round({arg0})",
            "imports": [],
            "returns": "int"
        },
        "javascript": {
            "code": "Math.round({arg0})",
            "imports": [],
            "returns": "number"
        },
        "go": {
            "code": "math.Round({arg0})",
            "imports": ["math"],
            "returns": "float64"
        }
    },
    
    "math.sqrt": {
        "python": {
            "code": "math.sqrt({arg0})",
            "imports": ["import math"],
            "returns": "float"
        },
        "javascript": {
            "code": "Math.sqrt({arg0})",
            "imports": [],
            "returns": "number"
        },
        "go": {
            "code": "math.Sqrt({arg0})",
            "imports": ["math"],
            "returns": "float64"
        }
    },
    
    "math.max": {
        "python": {
            "code": "max({arg0}, {arg1})",
            "imports": [],
            "returns": "float"
        },
        "javascript": {
            "code": "Math.max({arg0}, {arg1})",
            "imports": [],
            "returns": "number"
        },
        "go": {
            "code": "math.Max({arg0}, {arg1})",
            "imports": ["math"],
            "returns": "float64"
        }
    },
    
    "math.min": {
        "python": {
            "code": "math.Min({arg0}, {arg1})",
            "imports": [],
            "returns": "float"
        },
        "javascript": {
            "code": "Math.min({arg0}, {arg1})",
            "imports": [],
            "returns": "number"
        },
        "go": {
            "code": "math.Min({arg0}, {arg1})",
            "imports": ["math"],
            "returns": "float64"
        }
    },
}


class MCPHandler(BaseHTTPRequestHandler):
    """HTTP handler for JSON-RPC requests"""
    
    def do_POST(self):
        """Handle JSON-RPC POST requests"""
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length).decode('utf-8')
        
        try:
            request = json.loads(body)
            response = self.handle_jsonrpc(request)
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
            
        except Exception as e:
            error_response = {
                "jsonrpc": "2.0",
                "id": request.get('id') if 'request' in locals() else None,
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(error_response).encode('utf-8'))
    
    def handle_jsonrpc(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle JSON-RPC request"""
        method = request.get('method')
        params = request.get('params', {})
        req_id = request.get('id')
        
        if method == "tools/list":
            return self.tools_list(req_id)
        elif method == "tools/call":
            return self.tools_call(req_id, params)
        else:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }
    
    def tools_list(self, req_id) -> Dict[str, Any]:
        """List all available operations"""
        tools = []
        for op_id in OPERATIONS.keys():
            tools.append({
                "name": op_id,
                "description": f"Operation: {op_id}",
                "targets": list(OPERATIONS[op_id].keys())
            })
        
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {"tools": tools}
        }
    
    def tools_call(self, req_id, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get operation implementation for target language"""
        name = params.get('name')
        target = params.get('target_language', 'python')
        
        if name not in OPERATIONS:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {
                    "code": -32602,
                    "message": f"Operation not found: {name}"
                }
            }
        
        op = OPERATIONS[name]
        
        if target not in op:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {
                    "code": -32602,
                    "message": f"Target language not supported: {target}"
                }
            }
        
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": op[target]
        }
    
    def log_message(self, format, *args):
        """Custom log format"""
        sys.stderr.write(f"[MCP] {format % args}\n")


def run_server(port=8765):
    """Run the MCP server"""
    server = HTTPServer(('localhost', port), MCPHandler)
    print(f"PW Operations MCP Server running on http://localhost:{port}")
    print(f"Operations available: {len(OPERATIONS)}")
    print(f"Targets: python, javascript, go")
    print("Ready for requests...")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.shutdown()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    run_server(port)
