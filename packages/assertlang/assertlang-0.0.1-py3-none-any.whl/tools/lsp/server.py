#!/usr/bin/env python3
"""
PW Language Server
LSP server for Promptware (.al files) with CharCNN + MCP integration
"""

import sys
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from pygls.server import LanguageServer
from lsprotocol import types

# PW imports
from dsl.pw_parser import parse_pw, PWParseError
from ml.inference import OperationLookup

# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('tools/lsp/server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize LSP server
server = LanguageServer('pw-language-server', 'v0.1.0')

# Global state
operation_lookup: Optional[OperationLookup] = None
document_cache: Dict[str, Any] = {}


@dataclass
class ParseResult:
    """Result of parsing a PW file"""
    success: bool
    ir: Optional[Any] = None
    diagnostics: List[types.Diagnostic] = None

    def __post_init__(self):
        if self.diagnostics is None:
            self.diagnostics = []


def parse_document(uri: str, text: str) -> ParseResult:
    """Parse PW document and return diagnostics"""
    diagnostics = []

    try:
        # Parse PW code
        ir = parse_pw(text)
        logger.info(f"Successfully parsed {uri}")
        return ParseResult(success=True, ir=ir, diagnostics=[])

    except PWParseError as e:
        # Parse error - create diagnostic
        diagnostic = types.Diagnostic(
            range=types.Range(
                start=types.Position(line=e.line - 1 if hasattr(e, 'line') else 0, character=e.column if hasattr(e, 'column') else 0),
                end=types.Position(line=e.line - 1 if hasattr(e, 'line') else 0, character=e.column + 1 if hasattr(e, 'column') else 1)
            ),
            message=str(e),
            severity=types.DiagnosticSeverity.Error,
            source='pw-parser'
        )
        diagnostics.append(diagnostic)
        logger.warning(f"Parse error in {uri}: {e}")
        return ParseResult(success=False, diagnostics=diagnostics)

    except Exception as e:
        # Unexpected error
        diagnostic = types.Diagnostic(
            range=types.Range(
                start=types.Position(line=0, character=0),
                end=types.Position(line=0, character=1)
            ),
            message=f"Internal error: {str(e)}",
            severity=types.DiagnosticSeverity.Error,
            source='pw-parser'
        )
        diagnostics.append(diagnostic)
        logger.error(f"Unexpected error parsing {uri}: {e}", exc_info=True)
        return ParseResult(success=False, diagnostics=diagnostics)


def get_code_at_position(text: str, position: types.Position, max_chars: int = 50) -> str:
    """Extract code snippet around a position"""
    lines = text.split('\n')
    if position.line >= len(lines):
        return ""

    line = lines[position.line]

    # Find operation call around cursor
    # Look backwards to find start
    start = position.character
    while start > 0 and line[start - 1] not in [' ', '\t', '\n', '(', ',']:
        start -= 1

    # Look forwards to find end
    end = position.character
    while end < len(line) and line[end] not in [' ', '\t', '\n', ')', ',', ';']:
        end += 1

    # Expand to include method call if present
    if start > 0 and line[start - 1] == '.':
        # Include object name
        obj_start = start - 1
        while obj_start > 0 and line[obj_start - 1] not in [' ', '\t', '\n', '(', ',', '=']:
            obj_start -= 1
        start = obj_start

    snippet = line[start:end].strip()
    logger.debug(f"Code snippet at {position}: '{snippet}'")
    return snippet


@server.feature(types.TEXT_DOCUMENT_DID_OPEN)
async def did_open(ls: LanguageServer, params: types.DidOpenTextDocumentParams):
    """Handle document open - parse and send diagnostics"""
    uri = params.text_document.uri
    text = params.text_document.text

    logger.info(f"Document opened: {uri}")

    # Parse document
    result = parse_document(uri, text)

    # Cache result
    document_cache[uri] = result

    # Send diagnostics
    ls.publish_diagnostics(uri, result.diagnostics)


@server.feature(types.TEXT_DOCUMENT_DID_CHANGE)
async def did_change(ls: LanguageServer, params: types.DidChangeTextDocumentParams):
    """Handle document change - reparse and send diagnostics"""
    uri = params.text_document.uri

    # Get new text (full document sync)
    text = params.content_changes[0].text

    logger.debug(f"Document changed: {uri}")

    # Parse document
    result = parse_document(uri, text)

    # Cache result
    document_cache[uri] = result

    # Send diagnostics
    ls.publish_diagnostics(uri, result.diagnostics)


@server.feature(types.TEXT_DOCUMENT_HOVER)
async def hover(ls: LanguageServer, params: types.TextDocumentPositionParams) -> Optional[types.Hover]:
    """Handle hover request - show operation info"""
    global operation_lookup

    uri = params.text_document.uri
    position = params.position

    # Get document text
    doc = ls.workspace.get_document(uri)
    text = doc.source

    # Get code at position
    code_snippet = get_code_at_position(text, position)

    if not code_snippet:
        return None

    logger.debug(f"Hover on: '{code_snippet}'")

    # Use CharCNN to predict operation
    try:
        if operation_lookup is None:
            operation_lookup = OperationLookup(model_path='ml/charcnn_large.pt')

        predictions = operation_lookup.predict(code_snippet, top_k=3)

        if not predictions:
            return None

        # Get top prediction
        operation_id, confidence = predictions[0]

        # Format hover content
        content = f"**Operation**: `{operation_id}`\n\n"
        content += f"**Confidence**: {confidence:.0%}\n\n"

        # Add operation description (from MCP would be here)
        # For now, show basic info
        content += f"CharCNN identified this as `{operation_id}` with {confidence:.0%} confidence.\n\n"

        # Show alternative predictions
        if len(predictions) > 1:
            content += "**Alternatives**:\n"
            for alt_op, alt_conf in predictions[1:]:
                content += f"- `{alt_op}` ({alt_conf:.0%})\n"

        logger.info(f"Hover: {operation_id} ({confidence:.0%})")

        return types.Hover(
            contents=types.MarkupContent(
                kind=types.MarkupKind.Markdown,
                value=content
            )
        )

    except Exception as e:
        logger.error(f"Hover error: {e}", exc_info=True)
        return None


@server.feature(types.TEXT_DOCUMENT_COMPLETION)
async def completion(ls: LanguageServer, params: types.CompletionParams) -> Optional[types.CompletionList]:
    """Handle completion request - suggest operations"""
    global operation_lookup

    uri = params.text_document.uri
    position = params.position

    # Get document text
    doc = ls.workspace.get_document(uri)
    text = doc.source

    # Get code at position
    code_snippet = get_code_at_position(text, position, max_chars=100)

    if not code_snippet:
        return None

    logger.debug(f"Completion for: '{code_snippet}'")

    # Use CharCNN to suggest operations
    try:
        if operation_lookup is None:
            operation_lookup = OperationLookup(model_path='ml/charcnn_large.pt')

        predictions = operation_lookup.predict(code_snippet, top_k=10)

        if not predictions:
            return None

        # Create completion items
        items = []
        for idx, (operation_id, confidence) in enumerate(predictions):
            # Parse operation
            parts = operation_id.split('.')
            if len(parts) == 2:
                namespace, method = parts
            else:
                namespace = ""
                method = operation_id

            item = types.CompletionItem(
                label=operation_id,
                kind=types.CompletionItemKind.Function,
                detail=f"{confidence:.0%} confidence",
                documentation=f"Operation: {operation_id}\nNamespace: {namespace}\nConfidence: {confidence:.0%}",
                sort_text=f"{idx:02d}",  # Sort by confidence
                insert_text=method + "()" if namespace else operation_id + "()"
            )
            items.append(item)

        logger.info(f"Completion: {len(items)} suggestions")

        return types.CompletionList(
            is_incomplete=False,
            items=items
        )

    except Exception as e:
        logger.error(f"Completion error: {e}", exc_info=True)
        return None


@server.feature(types.TEXT_DOCUMENT_DEFINITION)
async def definition(ls: LanguageServer, params: types.TextDocumentPositionParams) -> Optional[List[types.Location]]:
    """Handle go-to-definition request"""
    uri = params.text_document.uri
    position = params.position

    # Get document
    doc = ls.workspace.get_document(uri)
    text = doc.source

    # Get code at position
    code_snippet = get_code_at_position(text, position)

    if not code_snippet:
        return None

    logger.debug(f"Definition for: '{code_snippet}'")

    # Parse document to find definition
    result = document_cache.get(uri)
    if not result or not result.success:
        return None

    # Find function definition in IR
    # For now, return None (would need to traverse IR to find definition)
    # This is a placeholder for future implementation

    logger.info(f"Definition: not found for '{code_snippet}'")
    return None


@server.feature(types.INITIALIZE)
async def initialize(ls: LanguageServer, params: types.InitializeParams):
    """Handle initialization"""
    logger.info("LSP server initializing...")

    # Load CharCNN model
    global operation_lookup
    try:
        operation_lookup = OperationLookup(model_path='ml/charcnn_large.pt')
        logger.info("CharCNN model loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load CharCNN model: {e}")

    logger.info("LSP server initialized")


@server.feature(types.SHUTDOWN)
async def shutdown(ls: LanguageServer):
    """Handle shutdown"""
    logger.info("LSP server shutting down...")


def main():
    """Start LSP server"""
    logger.info("Starting PW Language Server...")
    logger.info(f"Python: {sys.version}")
    logger.info(f"Working directory: {Path.cwd()}")

    # Start server (stdio mode)
    server.start_io()


if __name__ == "__main__":
    main()
