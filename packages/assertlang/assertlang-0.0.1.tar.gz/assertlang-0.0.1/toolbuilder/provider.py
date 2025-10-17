from __future__ import annotations

import os
from typing import Any, Dict


class Provider:
    def generate(self, instruction: str, context: Dict[str, Any]) -> str:  # pragma: no cover
        raise NotImplementedError


class AnthropicProvider(Provider):
    def __init__(self) -> None:
        self.api_key = os.environ.get("ANTHROPIC_API_KEY", "")

    def generate(self, instruction: str, context: Dict[str, Any]) -> str:
        # Placeholder: integrate real API call here
        # Return a scaffold string based on instruction/context
        return f"// scaffold for {context.get('tool')} v{context.get('version')}\n"


def get_provider(name: str) -> Provider:
    if name == "anthropic":
        return AnthropicProvider()
    raise ValueError(f"unknown provider: {name}")




