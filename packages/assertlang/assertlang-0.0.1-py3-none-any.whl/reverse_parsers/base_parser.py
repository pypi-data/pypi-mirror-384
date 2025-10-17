"""
Base reverse parser for converting code to PW DSL.

All language-specific parsers inherit from BaseReverseParser.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class ExtractedAgent:
    """Intermediate representation of extracted agent from code."""

    name: str
    port: int
    lang: str
    verbs: List[Dict[str, Any]] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)
    llm: Optional[str] = None
    memory: Optional[str] = None
    observability: Optional[Dict[str, Any]] = None
    middleware: Optional[Dict[str, Any]] = None
    errors: List[Dict[str, Any]] = field(default_factory=list)
    confidence_score: float = 1.0

    # Metadata about extraction
    framework: Optional[str] = None
    extraction_notes: List[str] = field(default_factory=list)


class BaseReverseParser(ABC):
    """Base class for language-specific reverse parsers."""

    @abstractmethod
    def parse_file(self, file_path: str) -> ExtractedAgent:
        """
        Parse source file and extract agent definition.

        Args:
            file_path: Path to source code file

        Returns:
            ExtractedAgent with all extracted information
        """
        pass

    @abstractmethod
    def detect_framework(self, ast_root) -> str:
        """
        Detect which framework is being used.

        Args:
            ast_root: Root of AST tree

        Returns:
            Framework name (e.g., 'fastapi', 'flask', 'express')
        """
        pass

    @abstractmethod
    def extract_handlers(self, ast_root) -> List[Dict[str, Any]]:
        """
        Extract handler functions/methods from AST.

        Args:
            ast_root: Root of AST tree

        Returns:
            List of handler dicts with name, params, returns
        """
        pass

    @abstractmethod
    def extract_port(self, ast_root) -> int:
        """
        Extract server port from code.

        Args:
            ast_root: Root of AST tree

        Returns:
            Port number (default 8000 if not found)
        """
        pass

    @abstractmethod
    def extract_tools(self, ast_root) -> List[str]:
        """
        Extract configured tools from code.

        Args:
            ast_root: Root of AST tree

        Returns:
            List of tool names
        """
        pass

    def to_pw_dsl(self, agent: ExtractedAgent, include_metadata: bool = False) -> str:
        """
        Convert ExtractedAgent to PW DSL string.

        Args:
            agent: Extracted agent definition
            include_metadata: Include extraction metadata as comments

        Returns:
            PW DSL string
        """
        lines = []

        # Metadata comments (optional)
        if include_metadata:
            lines.append(f"# Extracted from {agent.lang} code")
            if agent.framework:
                lines.append(f"# Framework: {agent.framework}")
            lines.append(f"# Confidence: {agent.confidence_score:.0%}")
            if agent.extraction_notes:
                lines.append("# Notes:")
                for note in agent.extraction_notes:
                    lines.append(f"#   - {note}")
            lines.append("")

        # Agent definition
        lines.append(f"lang {agent.lang}")
        lines.append(f"agent {agent.name}")
        lines.append(f"port {agent.port}")
        lines.append("")

        # Tools
        if agent.tools:
            lines.append("tools:")
            for tool in agent.tools:
                lines.append(f"  - {tool}")
            lines.append("")

        # LLM configuration
        if agent.llm:
            lines.append(f"llm {agent.llm}")
            lines.append("")

        # Memory configuration
        if agent.memory:
            lines.append(f"memory {agent.memory}")
            lines.append("")

        # Middleware (if extracted)
        if agent.middleware:
            lines.append("middleware:")
            for key, value in agent.middleware.items():
                if isinstance(value, dict):
                    lines.append(f"  {key}:")
                    for k, v in value.items():
                        lines.append(f"    {k}: {v}")
                else:
                    lines.append(f"  {key}: {value}")
            lines.append("")

        # Errors (if extracted)
        if agent.errors:
            lines.append("errors:")
            for error in agent.errors:
                lines.append(f"  - code: {error.get('code', 'UNKNOWN')}")
                if 'status' in error:
                    lines.append(f"    status: {error['status']}")
                if 'message' in error:
                    lines.append(f"    message: \"{error['message']}\"")
            lines.append("")

        # Verbs
        for verb in agent.verbs:
            lines.append(f"expose {verb['name']}:")

            # Parameters
            if verb.get('params'):
                lines.append("  params:")
                for param in verb['params']:
                    param_type = param.get('type', 'string')
                    lines.append(f"    {param['name']} {param_type}")

            # Returns
            if verb.get('returns'):
                lines.append("  returns:")
                for ret in verb['returns']:
                    ret_type = ret.get('type', 'string')
                    lines.append(f"    {ret['name']} {ret_type}")

            lines.append("")

        # Observability (if extracted)
        if agent.observability:
            lines.append("observability:")
            for key, value in agent.observability.items():
                lines.append(f"  {key}: {value}")
            lines.append("")

        return "\n".join(lines).strip()

    def calculate_confidence(
        self,
        framework_detected: bool,
        verbs_found: int,
        params_extracted: int,
        returns_extracted: int
    ) -> float:
        """
        Calculate confidence score for extraction.

        Args:
            framework_detected: Whether framework was identified
            verbs_found: Number of verbs extracted
            params_extracted: Number of params extracted
            returns_extracted: Number of returns extracted

        Returns:
            Confidence score 0.0-1.0
        """
        score = 1.0

        if not framework_detected:
            score -= 0.2

        if verbs_found == 0:
            score -= 0.5
        elif verbs_found < 2:
            score -= 0.1

        if params_extracted == 0:
            score -= 0.1

        if returns_extracted == 0:
            score -= 0.1

        return max(0.0, min(1.0, score))
