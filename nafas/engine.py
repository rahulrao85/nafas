"""Adherence engine: classify nights, detect lapses, decline and leak, and keep score without resets.

Everything here is deterministic and explainable: each detection carries the evidence that fired it.
Thresholds are in one place so a clinician advisor can review and tune them.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from statistics import mean, median

from .i18n import Msg, tr
from .models import Night

# ─── Thresholds (reviewable) ──────────────────────────────────────────────────
ADHERENT_MIN = 240           # 4 h: the usual payer/clinical adherence bar
LARGE_LEAK_LPM = 24.0        # ResMed "large leak" threshold, 95th percentile
LAPSE_MISSED_IN_A_ROW = 2    # 2 nights with no use in a row = lapse
LAPSE_SHORT_OF_5 = 3         # or 3 of the last 5 nights under goal
RECOVERED_MET_OF_4 = 3       # recovered once 3 of the last 4 nights meet goal again
DECLINE_RECENT_DAYS = 14
DECLINE_BASELINE_DAYS = 28
DECLINE_RATIO = 0.80         # recent mean usage under 80% of baseline
LEAK_EPISODE_OF_3 = 2        # 2 of the last 3 used nights over the large-leak line
LEAK_CREEP_RATIO = 2.0       # 14-night median leak doubles vs prior 30 nights …
LEAK_CREEP_FLOOR = 12.0      # … and sits above 12 L/min (cushion wearing out)
AHI_FLAG = 10.0              # residual AHI worth a clinician's look
AHI_FLAG_NIGHTS = 3          # on 3 of the last 7 used nights
GRACE_PER_7 = 1              # one missed night per rolling week doesn't break the run


def status_of(n: Night, goal_min: float = ADHERENT_MIN) -> str:
    if n.usage_min <= 0:
        return "missed"
    return "met" if n.usage_min >= goal_min else "partial"


def fill_gaps(nights: list[Night], until: date | None = None) -> list[Night]:
    """Sort by date and insert zero-use nights for missing dates (no record = machine not used)."""
    if not nights:
        return []
    by_date = {n.date: n for n in nights}
    start = min(by_date)
    end = until or max(by_date)
    out, d = [], start
    while d <= end:
        out.append(by_date.get(d) or Night(date=d))
        d += timedelta(days=1)
    return out


@dataclass
class Detection:
    kind: str                    # lapse | decline | leak | leak_creep | clinical
    severity: str                # info | watch | act | clinician
    evidence: list[str] = field(default_factory=list)
    started: date | None = None

    def to_dict(self, lang: str = "en") -> dict:
        return {"kind": self.kind, "severity": self.severity, "evidence": tr(self.evidence, lang),
                "started": self.started.isoformat() if self.started else None}


def _used(window: list[Night]) -> list[Night]:
    return [n for n in window if n.usage_min > 0]


def detect_lapse(hist: list[Night]) -> Detection | None:
    last = hist[-5:]
    if len(last) >= LAPSE_MISSED_IN_A_ROW and all(n.usage_min <= 0 for n in hist[-LAPSE_MISSED_IN_A_ROW:]):
        run = 0
        for n in reversed(hist):
            if n.usage_min > 0:
                break
            run += 1
        return Detection("lapse", "act", [Msg("lapse_missed", n=run)],
                         started=hist[-run].date)
    short = [n for n in last if n.usage_min < ADHERENT_MIN]
    if len(last) == 5 and len(short) >= LAPSE_SHORT_OF_5:
        return Detection("lapse", "act", [Msg("lapse_short", n=len(short))],
                         started=short[0].date)
    return None


def detect_decline(hist: list[Night]) -> Detection | None:
    need = DECLINE_RECENT_DAYS + DECLINE_BASELINE_DAYS
    if len(hist) < need:
        return None
    recent = hist[-DECLINE_RECENT_DAYS:]
    base = hist[-need:-DECLINE_RECENT_DAYS]
    r, b = mean(n.usage_min for n in recent), mean(n.usage_min for n in base)
    if b >= ADHERENT_MIN and r < b * DECLINE_RATIO:
        return Detection("decline", "watch",
                         [Msg("decline", b=f"{b / 60:.1f}", r=f"{r / 60:.1f}",
                              recent=DECLINE_RECENT_DAYS, base=DECLINE_BASELINE_DAYS)],
                         started=recent[0].date)
    return None


def detect_leak(hist: list[Night]) -> Detection | None:
    used = [n for n in _used(hist[-7:]) if n.leak95_lpm is not None][-3:]
    high = [n for n in used if n.leak95_lpm > LARGE_LEAK_LPM]
    if len(used) >= 2 and len(high) >= LEAK_EPISODE_OF_3:
        worst = max(n.leak95_lpm for n in high)
        return Detection("leak", "act",
                         [Msg("leak", n=len(high), m=len(used), worst=f"{worst:.0f}", line=f"{LARGE_LEAK_LPM:.0f}")],
                         started=high[0].date)
    return None


def detect_leak_creep(hist: list[Night]) -> Detection | None:
    used = [n for n in _used(hist[-51:]) if n.leak95_lpm is not None]
    if len(used) < 35:
        return None
    recent, prior = used[-14:], used[:-21]
    r, p = median(n.leak95_lpm for n in recent), median(n.leak95_lpm for n in prior)
    # Creep means a slow drift: the week before the recent fortnight must already be rising.
    # A sudden jump from a normal baseline is an acute leak (mask fit), not wear.
    lead = median(n.leak95_lpm for n in used[-21:-14])
    if r >= LEAK_CREEP_FLOOR and r >= max(p, 1.0) * LEAK_CREEP_RATIO and lead >= p + 3:
        return Detection("leak_creep", "watch",
                         [Msg("leak_creep", p=f"{p:.0f}", r=f"{r:.0f}")],
                         started=recent[0].date)
    return None


def detect_clinical(hist: list[Night]) -> Detection | None:
    used = [n for n in _used(hist[-7:]) if n.ahi is not None]
    high = [n for n in used if n.ahi >= AHI_FLAG]
    if len(high) >= AHI_FLAG_NIGHTS:
        return Detection("clinical", "clinician",
                         [Msg("clinical", line=f"{AHI_FLAG:.0f}", n=len(high), m=len(used))],
                         started=high[0].date)
    return None


def detect_all(hist: list[Night]) -> list[Detection]:
    out = []
    for fn in (detect_clinical, detect_lapse, detect_leak, detect_leak_creep, detect_decline):
        d = fn(hist)
        if d:
            out.append(d)
    # A lapse already explains a decline; don't double-message.
    if any(d.kind == "lapse" for d in out):
        out = [d for d in out if d.kind != "decline"]
    return out


def is_recovered(hist: list[Night]) -> bool:
    last = hist[-4:]
    return len(last) == 4 and sum(n.usage_min >= ADHERENT_MIN for n in last) >= RECOVERED_MET_OF_4


def momentum(hist: list[Night], goal_min: float = ADHERENT_MIN) -> dict:
    """Progress that survives setbacks: banked nights never go down; the run has a weekly grace night."""
    statuses = [status_of(n, goal_min) for n in hist]
    banked = statuses.count("met")

    def run_ending_at(idx: int) -> tuple[int, int]:
        # Walk back from idx. A lone short/missed night is forgiven once per 7 days;
        # two non-met nights in a row end the run.
        run, graces, last_grace = 0, 0, None
        for j in range(idx, -1, -1):
            if statuses[j] == "met":
                run += 1
                continue
            if last_grace is not None and last_grace - j < 7:
                break
            if j > 0 and statuses[j - 1] != "met":
                break
            last_grace, graces = j, graces + 1
        return run, graces

    run, graces = run_ending_at(len(statuses) - 1) if statuses else (0, 0)
    best = 0
    for i in range(len(statuses)):
        if statuses[i] == "met" and (i + 1 == len(statuses) or statuses[i + 1] != "met"):
            best = max(best, run_ending_at(i)[0])
    best = max(best, run)
    last30 = statuses[-30:]
    return {
        "banked_nights": banked,
        "adherence_30": round(100 * last30.count("met") / len(last30), 1) if last30 else 0.0,
        "run": run,
        "run_grace_used": graces,
        "best_run": best,
        "avg_hours_7": round(mean(n.usage_min for n in hist[-7:]) / 60, 2) if hist else 0.0,
        "avg_hours_30": round(mean(n.usage_min for n in hist[-30:]) / 60, 2) if hist else 0.0,
    }
