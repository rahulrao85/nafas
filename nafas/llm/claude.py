"""Claude via the Anthropic Messages API (default provider).

Credentials resolve the SDK's usual way: ANTHROPIC_API_KEY, ANTHROPIC_AUTH_TOKEN, or an `ant auth login` profile.
Model: NAFAS_CLAUDE_MODEL (default claude-opus-5-5). Coaching notes are short, so effort is "low".
Server-side refusal fallback is on, so a policy decline on the primary model is retried on another.
"""

from __future__ import annotations

import os

from .base import LLMError, LLMProvider

DEFAULT_MODEL = "claude-opus-5-5"


class ClaudeProvider(LLMProvider):
    name = "claude"

    def __init__(self, model: str | None = None):
        self.model = model or os.getenv("NAFAS_CLAUDE_MODEL", DEFAULT_MODEL)
        self._client = None
        self._err = ""
        try:
            import anthropic
            self._anthropic = anthropic
        except ImportError:
            self._anthropic = None
            self._err = "the 'anthropic' package is not installed (pip install anthropic)"

    def available(self) -> bool:
        if self._anthropic is None:
            return False
        if any(os.getenv(k) for k in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_PROFILE")):
            return True
        # An `ant auth login` profile on disk also works; the client exposes what it resolved.
        try:
            client = self._anthropic.Anthropic()
        except Exception as e:  # noqa: BLE001 - SDK raises different types for missing credentials
            self._err = f"no Anthropic credentials found ({type(e).__name__})"
            return False
        if any(getattr(client, a, None) for a in ("api_key", "auth_token", "credentials")):
            self._client = client
            return True
        self._err = "no Anthropic credentials found (set ANTHROPIC_API_KEY or run `ant auth login`)"
        return False

    def why_unavailable(self) -> str:
        return self._err

    def generate(self, system: str, user: str, max_tokens: int = 2000) -> str:
        a = self._anthropic
        client = self._client or a.Anthropic()
        kwargs = dict(model=self.model, max_tokens=max_tokens, system=system,
                      messages=[{"role": "user", "content": user}],
                      output_config={"effort": "low"})
        try:
            resp = client.beta.messages.create(betas=["server-side-fallback-2026-07-01"],
                                               fallbacks="default", **kwargs)
        except TypeError as e:  # raised by the SDK when no credentials resolve
            raise LLMError(f"Claude client not ready: {e}") from e
        except a.APIStatusError as e:
            raise LLMError(f"Claude API error {e.status_code}") from e
        except a.APIConnectionError as e:
            raise LLMError("Could not reach the Claude API") from e
        if resp.stop_reason == "refusal":
            raise LLMError("Claude declined this request")
        text = "".join(b.text for b in resp.content if b.type == "text").strip()
        if not text:
            raise LLMError("Claude returned no text")
        return text
