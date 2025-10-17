"""
Promptware Reverse Parsers

Convert code from any language back to PW DSL.
Enables universal cross-language agent communication.
"""

from .base_parser import BaseReverseParser, ExtractedAgent
from .python_parser import PythonReverseParser
from .nodejs_parser import NodeJSReverseParser
from .go_parser import GoReverseParser
from .rust_parser import RustReverseParser
from .dotnet_parser import DotNetReverseParser

__all__ = [
    'BaseReverseParser',
    'ExtractedAgent',
    'PythonReverseParser',
    'NodeJSReverseParser',
    'GoReverseParser',
    'RustReverseParser',
    'DotNetReverseParser',
]
