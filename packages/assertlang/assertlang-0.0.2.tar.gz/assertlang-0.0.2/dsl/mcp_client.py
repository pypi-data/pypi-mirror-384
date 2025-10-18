"""
MCP Client for querying operation implementations
"""

import json
import urllib.request
import urllib.error
from typing import Dict, List, Any, Optional


class MCPClient:
    """Client for communicating with PW Operations MCP Server"""
    
    def __init__(self, server_url: str = "http://localhost:8765"):
        self.server_url = server_url
        self.request_id = 0
        self._operation_cache = {}  # Cache MCP responses
    
    def _rpc_call(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make JSON-RPC call to MCP server"""
        self.request_id += 1
        
        request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
            "params": params
        }
        
        req = urllib.request.Request(
            self.server_url,
            data=json.dumps(request).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        
        try:
            with urllib.request.urlopen(req, timeout=5) as response:
                result = json.loads(response.read().decode('utf-8'))
                
                if 'error' in result:
                    raise MCPError(result['error']['message'])
                
                return result['result']
        
        except urllib.error.URLError as e:
            raise MCPError(f"Failed to connect to MCP server: {e}")
        except json.JSONDecodeError as e:
            raise MCPError(f"Invalid JSON response from MCP server: {e}")
    
    def list_operations(self) -> List[Dict[str, Any]]:
        """List all available operations from MCP server"""
        result = self._rpc_call("tools/list", {})
        return result.get('tools', [])
    
    def get_operation(self, operation_id: str, target_lang: str = "python") -> Dict[str, Any]:
        """
        Get operation implementation for target language
        
        Returns:
            {
                "code": "{arg0}.split({arg1})",
                "imports": ["import something"],
                "returns": "list"
            }
        """
        # Check cache first
        cache_key = f"{operation_id}:{target_lang}"
        if cache_key in self._operation_cache:
            return self._operation_cache[cache_key]
        
        # Query MCP server
        result = self._rpc_call("tools/call", {
            "name": operation_id,
            "target_language": target_lang
        })
        
        # Cache result
        self._operation_cache[cache_key] = result
        return result
    
    def get_operations_batch(self, operation_ids: List[str], target_lang: str = "python") -> Dict[str, Dict[str, Any]]:
        """Get multiple operations at once"""
        results = {}
        for op_id in operation_ids:
            try:
                results[op_id] = self.get_operation(op_id, target_lang)
            except MCPError as e:
                print(f"Warning: Failed to get operation {op_id}: {e}")
        return results
    
    def clear_cache(self):
        """Clear the operation cache"""
        self._operation_cache.clear()


class MCPError(Exception):
    """MCP-related error"""
    pass


# Global MCP client instance
_mcp_client: Optional[MCPClient] = None


def get_mcp_client(server_url: str = "http://localhost:8765") -> MCPClient:
    """Get or create global MCP client instance"""
    global _mcp_client
    if _mcp_client is None:
        _mcp_client = MCPClient(server_url)
    return _mcp_client


if __name__ == "__main__":
    # Test MCP client
    client = MCPClient()
    
    print("Testing MCP Client...")
    print()
    
    # List operations
    print("1. Listing all operations:")
    ops = client.list_operations()
    print(f"   Found {len(ops)} operations")
    for op in ops[:5]:
        print(f"   - {op['name']}: {op['targets']}")
    print()
    
    # Get specific operation
    print("2. Getting str.split for Python:")
    impl = client.get_operation("str.split", "python")
    print(f"   Code: {impl['code']}")
    print(f"   Imports: {impl['imports']}")
    print()
    
    print("3. Getting file.read for JavaScript:")
    impl = client.get_operation("file.read", "javascript")
    print(f"   Code: {impl['code']}")
    print(f"   Imports: {impl['imports']}")
    print()
    
    print("4. Getting math.sqrt for Go:")
    impl = client.get_operation("math.sqrt", "go")
    print(f"   Code: {impl['code']}")
    print(f"   Imports: {impl['imports']}")
    print()
    
    print("✅ MCP Client working!")
