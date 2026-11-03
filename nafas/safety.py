"""Guardrails around the language model and free-text notes.

The rules engine decides; the LLM only words the decision. Anything it writes is checked here
before a person sees it, and a failed check falls back to the fixed template.
"""

from __future__ import annotations

import re

MAX_CHARS = 700

# Patterns the coach must never produce. Each is (name, regex).
FORBIDDEN = [
    ("pressure_change", re.compile(
        r"\b(increase|raise|lower|decrease|reduce|change|adjust|turn (up|down))\b[^.]{0,40}\bpressure\b"
        r"|\bpressure\b[^.]{0,30}\b(up|down|higher|lower)\b|cm\s?h2o|سم ماء|(ارفع|اخفض|غيّر|غير)\s+الضغط", re.I)),
    ("diagnosis", re.compile(
        r"\byou (have|may have|probably have|might have|are suffering from) (an? )?(\w+ ){0,2}"
        r"(apn(o)?ea|insomnia|disorder|disease|condition|syndrome|narcolepsy|copd|heart)|\bdiagnos", re.I)),
    ("medication", re.compile(r"\b(medication|medicine|melatonin|sleeping pills?|sedative|dose|dosage)\b", re.I)),
    ("stop_therapy", re.compile(r"\b(stop|quit|pause) (using )?(your )?(cpap|therapy|machine)\b", re.I)),
    ("blame", re.compile(r"\b(fail(ed|ure|ing)?|lazy|should have|disappoint\w*|bad patient|no excuse)\b", re.I)),
    ("link", re.compile(r"https?://|www\.", re.I)),
]

CRISIS = re.compile(
    r"chest pain|can'?t breathe|cannot breathe|struggling to breathe|faint(ed|ing)?|passed out|"
    r"suicid|kill myself|end my life|ألم في الصدر|لا أستطيع التنفس|انتحار|أغمي علي", re.I)

CRISIS_MESSAGE = {
    "en": "What you wrote may need urgent care. If you have chest pain, trouble breathing or have fainted, "
          "call your local emergency number now (998 in the UAE). This app can't help with emergencies.",
    "ar": "ما كتبته قد يحتاج إلى رعاية عاجلة. إذا كان لديك ألم في الصدر أو صعوبة في التنفس أو أُغمي عليك، "
          "اتصل برقم الطوارئ المحلي الآن (998 في الإمارات). هذا التطبيق لا يتعامل مع الحالات الطارئة.",
}


def check_output(text: str) -> list[str]:
    """Return the names of every rule the text breaks (empty list = safe to show)."""
    problems = [name for name, rx in FORBIDDEN if rx.search(text or "")]
    if not text or not text.strip():
        problems.append("empty")
    if len(text or "") > MAX_CHARS:
        problems.append("too_long")
    return problems


def crisis_check(note: str, lang: str = "en") -> str | None:
    if note and CRISIS.search(note):
        return CRISIS_MESSAGE.get(lang, CRISIS_MESSAGE["en"])
    return None
