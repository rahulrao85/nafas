"""Swappable language-model providers. Choose with NAFAS_LLM = claude (default) | gemini | azure | offline."""

from __future__ import annotations

import os

from .base import LLMError, LLMProvider
from .offline import OfflineProvider


def get_provider(name: str | None = None) -> LLMProvider:
    name = (name or os.getenv("NAFAS_LLM") or "claude").lower()
    if name == "claude":
        from .claude import ClaudeProvider
        p = ClaudeProvider()
    elif name == "gemini":
        from .gemini import GeminiProvider
        p = GeminiProvider()
    elif name == "azure":
        from .azure import AzureOpenAIProvider
        p = AzureOpenAIProvider()
    else:
        return OfflineProvider()
    if not p.available():
        return OfflineProvider(reason=f"{p.name} not configured: {p.why_unavailable()}")
    return p


__all__ = ["get_provider", "LLMProvider", "LLMError", "OfflineProvider"]
