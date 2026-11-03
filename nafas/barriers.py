"""Barrier inference: turn what the data shows (plus what the person says) into ranked, explained guesses.

Self-report always outranks a data guess. Data guesses carry the evidence that produced them,
so the person can say "no, that's not it" and pick another.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta
from statistics import median

from .engine import ADHERENT_MIN, LARGE_LEAK_LPM, Detection
from .models import CheckIn, Night, Profile

# code -> (label, can be detected from data?)
BARRIERS: dict[str, dict] = {
    "MASK_FIT":         {"label": "Mask fit or seal", "label_ar": "ملاءمة القناع أو إحكامه",              "from_data": True},
    "MASK_WEAR":        {"label": "Worn cushion or headgear", "label_ar": "وسادة أو أحزمة مهترئة",      "from_data": True},
    "MIDNIGHT_REMOVAL": {"label": "Taking the mask off mid-night", "label_ar": "نزع القناع أثناء الليل", "from_data": True},
    "TRAVEL_AWAY":      {"label": "Away from home / travel", "label_ar": "السفر أو البعد عن المنزل",       "from_data": True},
    "ROUTINE_SHIFT":    {"label": "Changed sleep schedule", "label_ar": "تغيّر موعد النوم",        "from_data": True},
    "MOTIVATION_FADE":  {"label": "Motivation dipping", "label_ar": "تراجع الحافز",            "from_data": True},
    "PRESSURE_DISCOMFORT": {"label": "Pressure feels too strong", "label_ar": "الضغط يبدو قوياً",  "from_data": True},
    "DRYNESS":          {"label": "Dry mouth or nose", "label_ar": "جفاف الفم أو الأنف",             "from_data": False},
    "CLAUSTROPHOBIA":   {"label": "Feeling closed in", "label_ar": "الشعور بالضيق",             "from_data": False},
    "CONGESTION_ILLNESS": {"label": "Blocked nose or unwell", "label_ar": "انسداد الأنف أو المرض",      "from_data": False},
    "FORGOT":           {"label": "Forgot / fell asleep without it", "label_ar": "نسيت / نمت دونه", "from_data": False},
    "NOISE_PARTNER":    {"label": "Noise or bed partner", "label_ar": "الضجيج أو شريك النوم",          "from_data": False},
    "FELT_FINE":        {"label": "Felt fine without it", "label_ar": "شعرت أنني بخير دونه",          "from_data": False},
}

SELF_REPORT_WINDOW_DAYS = 3


def label(code: str, lang: str = "en") -> str:
    b = BARRIERS[code]
    return b.get("label_ar", b["label"]) if lang == "ar" else b["label"]


@dataclass
class Barrier:
    code: str
    confidence: float
    source: str                      # "self-report" | "data"
    evidence: list[str] = field(default_factory=list)

    @property
    def label(self) -> str:
        return BARRIERS[self.code]["label"]

    def to_dict(self, lang: str = "en") -> dict:
        return {"code": self.code, "label": label(self.code, lang), "confidence": round(self.confidence, 2),
                "source": self.source, "evidence": self.evidence}


def _hhmm_to_min(s: str | None) -> int | None:
    if not s:
        return None
    h, m = s.split(":")
    v = int(h) * 60 + int(m)
    return v + 1440 if v < 12 * 60 else v   # after-midnight starts sort after evening ones


def infer(hist: list[Night], detections: list[Detection], checkins: list[CheckIn],
          profile: Profile) -> list[Barrier]:
    """Rank likely barriers for the most recent night(s) in `hist`."""
    today = hist[-1].date
    out: dict[str, Barrier] = {}

    def add(code, conf, source, ev):
        cur = out.get(code)
        if cur is None or conf > cur.confidence:
            out[code] = Barrier(code, conf, source, ev)

    # 1) What the person told us recently wins.
    for c in checkins:
        if today - timedelta(days=SELF_REPORT_WINDOW_DAYS) <= c.date <= today and c.barrier in BARRIERS:
            add(c.barrier, 0.95, "self-report", [f"You told us on {c.date:%d-%b-%Y}."])

    kinds = {d.kind for d in detections}
    last7 = hist[-7:]
    used7 = [n for n in last7 if n.usage_min > 0]

    # 2) Leak-driven barriers.
    if "leak" in kinds:
        short_leaky = [n for n in used7 if (n.leak95_lpm or 0) > LARGE_LEAK_LPM and n.usage_min < ADHERENT_MIN]
        ev = ["Large leak on recent nights."]
        if short_leaky:
            ev.append(f"{len(short_leaky)} leaky night(s) were also short — a poor seal often wakes people.")
        add("MASK_FIT", 0.75 if short_leaky else 0.65, "data", ev)
    if "leak_creep" in kinds:
        add("MASK_WEAR", 0.7, "data", next(d.evidence for d in detections if d.kind == "leak_creep"))

    # 3) Mid-night removal: used, but short, with several mask-on sessions.
    removals = [n for n in used7 if n.usage_min < ADHERENT_MIN and (n.mask_events or 1) >= 3]
    if len(removals) >= 2:
        add("MIDNIGHT_REMOVAL", 0.6, "data",
            [f"On {len(removals)} recent nights the mask came off and on 3+ times and use stayed under 4 h."])

    # 4) Away: no CPAP, but a wearable says they slept.
    away, run = [], 0
    for n in last7:   # need 2+ consecutive nights: one-off misses are not a trip
        run = run + 1 if n.usage_min <= 0 and (n.wearable_sleep_min or 0) >= 240 else 0
        if run >= 2:
            away = [m for m in last7 if m.usage_min <= 0 and (m.wearable_sleep_min or 0) >= 240]
    if away:
        add("TRAVEL_AWAY", 0.6, "data",
            [f"No CPAP on {len(away)} nights your watch recorded normal sleep — maybe you were away?"])

    # 5) Routine shift: sessions starting much later than usual, or weekend-only misses.
    starts_recent = [_hhmm_to_min(n.session_start) for n in used7 if n.session_start]
    starts_base = [_hhmm_to_min(n.session_start) for n in hist[-45:-7] if n.usage_min > 0 and n.session_start]
    if len(starts_recent) >= 3 and len(starts_base) >= 10:
        shift = median(starts_recent) - median(starts_base)
        if abs(shift) >= 90:
            add("ROUTINE_SHIFT", 0.6, "data",
                [f"Bedtime moved by about {abs(shift) / 60:.1f} h compared with your usual."])
    last28 = hist[-28:]
    wkend_miss = [n for n in last28 if n.usage_min < ADHERENT_MIN and n.date.weekday() in (4, 5)]
    wkday_miss = [n for n in last28 if n.usage_min < ADHERENT_MIN and n.date.weekday() not in (4, 5)]
    if len(wkend_miss) >= 3 and len(wkday_miss) <= 1:
        add("ROUTINE_SHIFT", 0.55, "data",
            [f"{len(wkend_miss)} of your short nights in 4 weeks were Friday/Saturday nights."])

    # 6) Pressure discomfort: short use while pressure sits near the top of its range.
    hi_p = [n for n in used7 if n.pressure95 and n.pressure95 >= 0.9 * profile.max_pressure
            and n.usage_min < ADHERENT_MIN]
    if len(hi_p) >= 2:
        add("PRESSURE_DISCOMFORT", 0.5, "data",
            ["Pressure ran near its upper limit on short nights. Only your care team should change settings."])

    # 7) Nothing specific, but use is sliding: motivation.
    if ("decline" in kinds or "lapse" in kinds) and not out:
        add("MOTIVATION_FADE", 0.4, "data",
            ["Use is dropping and the data shows no mask or schedule problem."])

    return sorted(out.values(), key=lambda b: -b.confidence)
