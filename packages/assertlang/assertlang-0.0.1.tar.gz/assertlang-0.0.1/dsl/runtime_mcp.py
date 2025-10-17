"""MCP Runtime"""
import subprocess, tempfile
from pathlib import Path
from dsl.pw_parser import parse_pw
from dsl.language_header import parse_language_header
from dsl.mcp_code_generator import generate_code

class PWRuntimeMCP:
    def execute_file(self, path: str):
        return self.execute(Path(path).read_text())
    
    def execute(self, code: str):
        target, clean = parse_language_header(code)
        ir = parse_pw(clean)
        generated = generate_code(ir, target)
        
        if target == "python":
            # Execute and call main
            namespace = {}
            exec(generated, namespace)
            if 'main' in namespace:
                namespace['main']()
        elif target == "javascript":
            # Add main() call
            generated += "\nmain();"
            with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
                f.write(generated)
                temp = f.name
            subprocess.run(['node', temp])
            Path(temp).unlink()
        elif target == "go":
            with tempfile.NamedTemporaryFile(mode='w', suffix='.go', delete=False) as f:
                f.write(f"package main\n\n{generated}\n\nfunc main() {{ main() }}")
                temp = f.name
            subprocess.run(['go', 'run', temp])
            Path(temp).unlink()

if __name__ == "__main__":
    import sys
    PWRuntimeMCP().execute_file(sys.argv[1]) if len(sys.argv) > 1 else print("Usage: python3 dsl/runtime_mcp.py <file.al>")
