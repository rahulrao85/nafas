"""Google Gemini, through Vertex AI (default) or an AI Studio API key.

Vertex:    NAFAS_GEMINI_VERTEX_PROJECT=<project>   (+ NAFAS_GEMINI_VERTEX_ACCOUNT=<gcloud account>, optional;
           NAFAS_GEMINI_LOCATION, default "global"). Auth is a short-lived token from `gcloud auth
           print-access-token`, so no key is stored anywhere.
AI Studio: NAFAS_GEMINI_API_KEY=<key>   (used only if no Vertex project is set)
Model:     NAFAS_GEMINI_MODEL (default gemini-3.5-flash); thinking NAFAS_GEMINI_THINKING (default LOW).

Plain REST with the standard library, the same request shape on both routes.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
import urllib.error
import urllib.request

from .base import LLMError, LLMProvider

DEFAULT_MODEL = "gemini-3.5-flash"
TOKEN_TTL_S = 50 * 60          # gcloud access tokens last an hour


class GeminiProvider(LLMProvider):
    name = "gemini"

    def __init__(self):
        self.model = os.getenv("NAFAS_GEMINI_MODEL", DEFAULT_MODEL)
        self.project = os.getenv("NAFAS_GEMINI_VERTEX_PROJECT", "")
        self.account = os.getenv("NAFAS_GEMINI_VERTEX_ACCOUNT", "")
        self.location = os.getenv("NAFAS_GEMINI_LOCATION", "global")
        self.api_key = os.getenv("NAFAS_GEMINI_API_KEY", "")
        self.thinking = os.getenv("NAFAS_GEMINI_THINKING", "LOW").upper()
        self._tok = (0.0, "")
        self._err = ""

    @property
    def route(self) -> str:
        return "vertex" if self.project else "ai-studio"

    def available(self) -> bool:
        if self.project:
            if not shutil.which("gcloud"):
                self._err = "gcloud CLI not found (needed for Vertex AI)"
                return False
            return True
        if self.api_key:
            return True
        self._err = "set NAFAS_GEMINI_VERTEX_PROJECT (Vertex) or NAFAS_GEMINI_API_KEY (AI Studio)"
        return False

    def why_unavailable(self) -> str:
        return self._err

    def describe(self) -> dict:
        return {"provider": self.name, "model": self.model, "route": self.route}

    def _token(self) -> str:
        if time.time() - self._tok[0] > TOKEN_TTL_S:
            cmd = [shutil.which("gcloud") or "gcloud", "auth", "print-access-token"]
            if self.account:
                cmd.append(f"--account={self.account}")
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if r.returncode != 0 or not r.stdout.strip():
                raise LLMError("gcloud could not issue an access token")
            self._tok = (time.time(), r.stdout.strip())
        return self._tok[1]

    def _request(self) -> tuple[str, dict]:
        if self.project:
            url = (f"https://aiplatform.googleapis.com/v1/projects/{self.project}/locations/{self.location}"
                   f"/publishers/google/models/{self.model}:generateContent")
            return url, {"Authorization": f"Bearer {self._token()}"}
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        return url, {"x-goog-api-key": self.api_key}

    def generate(self, system: str, user: str, max_tokens: int = 2000) -> str:
        body = {
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": user}]}],
            "generationConfig": {"maxOutputTokens": max_tokens, "thinkingConfig": {"thinkingLevel": self.thinking}},
        }
        url, auth = self._request()
        req = urllib.request.Request(url, json.dumps(body).encode(), {"Content-Type": "application/json", **auth})
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                data = json.loads(r.read())
        except urllib.error.HTTPError as e:
            raise LLMError(f"Gemini API error {e.code}") from e
        except (urllib.error.URLError, TimeoutError) as e:
            raise LLMError("Could not reach the Gemini API") from e
        if data.get("promptFeedback", {}).get("blockReason"):
            raise LLMError("Gemini declined this request")
        cands = data.get("candidates") or []
        if not cands:
            raise LLMError("Gemini returned no answer")
        c = cands[0]
        if c.get("finishReason") in ("SAFETY", "PROHIBITED_CONTENT", "BLOCKLIST", "SPII", "RECITATION"):
            raise LLMError("Gemini declined this request")
        if c.get("finishReason") == "MAX_TOKENS":
            raise LLMError("Gemini's answer was cut off")      # never show a half answer
        text = "".join(p.get("text", "") for p in c.get("content", {}).get("parts", []) if not p.get("thought")).strip()
        if not text:
            raise LLMError("Gemini returned no text")
        return text
