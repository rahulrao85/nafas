"""Azure OpenAI (kept from the original Sleep IQ build, which ran on Azure AI Foundry).

Needs AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY and AZURE_OPENAI_DEPLOYMENT
(optional AZURE_OPENAI_API_VERSION). Same prompt and same safety checks as every other provider.
"""

from __future__ import annotations

import os

from .base import LLMError, LLMProvider

REQUIRED = ("AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_API_KEY", "AZURE_OPENAI_DEPLOYMENT")


class AzureOpenAIProvider(LLMProvider):
    name = "azure"

    def __init__(self):
        self.model = os.getenv("AZURE_OPENAI_DEPLOYMENT", "")
        self._err = ""

    def available(self) -> bool:
        missing = [k for k in REQUIRED if not os.getenv(k)]
        if missing:
            self._err = "missing " + ", ".join(missing)
            return False
        try:
            import openai  # noqa: F401
        except ImportError:
            self._err = "the 'openai' package is not installed (pip install openai)"
            return False
        return True

    def why_unavailable(self) -> str:
        return self._err

    def generate(self, system: str, user: str, max_tokens: int = 2000) -> str:
        import openai
        client = openai.AzureOpenAI(
            api_key=os.environ["AZURE_OPENAI_API_KEY"],
            azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21"),
        )
        try:
            resp = client.chat.completions.create(
                model=self.model, max_tokens=max_tokens,
                messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            )
        except openai.OpenAIError as e:
            raise LLMError(f"Azure OpenAI error: {type(e).__name__}") from e
        text = (resp.choices[0].message.content or "").strip()
        if not text:
            raise LLMError("Azure OpenAI returned no text")
        return text
