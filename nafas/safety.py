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

# Emergency wording in a free-text note. Matched on normalised text (lower case; Arabic without diacritics,
# with أ/إ/آ → ا, ى → ي, ة → ه), so spelling variants and dialect forms hit the same pattern.
# (pattern, negatable): a negatable symptom preceded by "no / without / لا يوجد…" is not an emergency.
CRISIS_PATTERNS = [(re.compile(p), neg) for p, neg in [
    # chest
    (r"\bchest\s*pains?\b", True),
    (r"\bpain\w*\b[^.!?]{0,25}\bchest\b", True),                      # "crushing pain across my chest"
    (r"\bchest\s+(\w+\s+){0,2}(tight|hurt\w*|heavy|pressure|ache\w*)", True),
    (r"\btight(ness)?\s+(in\s+)?(my\s+)?chest\b", True),
    (r"(الم|وجع)\s*(\S+\s*)?(في|ب)?\s*(ال)?صدر", True),               # "ألم شديد بالصدر"
    (r"ضيق\s*(في|ب)?\s*(ال)?صدر", True),                               # chest tightness
    (r"صدر\S*\s*(يولم|يوجع|يعور|توجع)", True),                          # "صدري يؤلمني"
    # breathing
    (r"\b(can'?t|cannot|can not|unable to|not able to|struggling to|struggle to|hard to|could not|couldn'?t"
     r"|hardly|barely)\s+breathe?\b", False),
    (r"\b(can'?t|cannot|couldn'?t|unable to)\s+catch\s+my\s+breath\b", False),
    (r"\b(trouble|difficulty|difficult)\s+breathing\b", True),
    (r"\bshort(ness)?\s+of\s+breath\b", True),
    (r"(لا|ما|مو|مش)\s*(استطيع|اقدر|قادر|اقدرش)\s*(علي\s*|ان\s*)?(ال|ات|ا)?تنفس", False),
    (r"(ضيق|صعوبه)\s*(في\s*)?(ال)?تنفس", True),
    # consciousness
    (r"\b(fainted|fainting|passed out|blacked out|lost consciousness|collapsed)\b", False),
    (r"\b(felt|feel|feeling)\s+faint\b", False),
    (r"اغمي\s*علي|اغماء|فقدت\s*(ال)?وعي", False),
    # self-harm
    (r"\bsuicid|\bkill(ing)?\s+myself\b|\bend\s+my\s+life\b|\bend\s+it\s+all\b|\bwant\s+to\s+die\b|\bself[- ]?harm|\bhurt\s+myself\b", False),
    (r"انتحار|انتحر|اقتل\s*نفسي|(اريد|ابي|ابغي|بدي)\s*(ان\s*)?اموت|انهي\s*حياتي", False),
]]
NEGATION = re.compile(r"(\b(no|without|never|denies|deny)\s+(\w+\s+)?|(لا\s*يوجد|ما\s*في|مافي|بدون|ليس\s*عندي|ما\s*عندي)\s*)$")
_AR_DIACRITICS = re.compile(r"[ً-ْٰـ]")


def _normalise(text: str) -> str:
    t = _AR_DIACRITICS.sub("", text.lower().replace("’", "'"))
    for a, b in (("أ", "ا"), ("إ", "ا"), ("آ", "ا"), ("ى", "ي"), ("ة", "ه"), ("ؤ", "و"), ("ئ", "ي")):
        t = t.replace(a, b)
    return re.sub(r"\s+", " ", t)


def is_crisis(note: str) -> bool:
    t = _normalise(note or "")
    for rx, negatable in CRISIS_PATTERNS:
        for m in rx.finditer(t):
            if negatable and NEGATION.search(t[:m.start()]):
                continue
            return True
    return False

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
    if is_crisis(note):
        return CRISIS_MESSAGE.get(lang, CRISIS_MESSAGE["en"])
    return None
