"""No-network provider: signals the coach to use its fixed, reviewed template. Used in tests and when no key is set."""

from __future__ import annotations

from .base import LLMError, LLMProvider


class OfflineProvider(LLMProvider):
    name = "offline"
    model = "template"

    def __init__(self, reason: str = "offline mode"):
        self.reason = reason

    def generate(self, system: str, user: str, max_tokens: int = 2000) -> str:
        raise LLMError(self.reason)

    def describe(self) -> dict:
        return {"provider": self.name, "model": self.model, "note": self.reason}
