from __future__ import annotations


class LLMError(RuntimeError):
    """Any provider failure (network, auth, refusal). The coach falls back to the template."""


class LLMProvider:
    name = "base"
    model = ""

    def available(self) -> bool:
        return True

    def why_unavailable(self) -> str:
        return ""

    def generate(self, system: str, user: str, max_tokens: int = 2000) -> str:
        raise NotImplementedError

    def describe(self) -> dict:
        return {"provider": self.name, "model": self.model}
