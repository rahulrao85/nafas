"""Data checks: every bad input becomes a visible warning, never a crash and never a silent drop.

Rules:
- A value that can't be right (AHI 999, leak −5, a 30-hour night) is set to empty and reported.
- A unit is never guessed. Values that look like the wrong unit (every "minutes" value ≤ 24, every leak ≤ 1.5)
  are flagged, and nothing is converted: a wrong guess could hide a lapse or invent a leak. Named columns
  (`usage_hours`, `leak95_lps`) are converted exactly. Only CSV/JSON are checked; device files have fixed units.
- Duplicate nights keep the more complete record and are reported.
- A missing field turns off only the checks that need it, and the warning says which.
- Nafas stops only when the field every decision needs, nightly usage, is missing everywhere.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, timedelta
from statistics import median

from .i18n import Msg, tr
from .models import Night

LIMITS = {   # field: (lowest possible, highest possible)
    "usage_min": (0, 1440), "ahi": (0, 150), "leak95_lpm": (0, 200), "pressure95": (3, 30),
    "mask_events": (0, 50), "wearable_sleep_min": (0, 1440), "wearable_rhr": (25, 150),
    "wearable_hrv_ms": (5, 300),
}
GAP_WARN_NIGHTS = 7
HHMM = re.compile(r"^([01]?\d|2[0-3]):[0-5]\d$")


@dataclass
class Warning:
    code: str
    severity: str                         # info | warn | stop
    msg: Msg
    count: int = 0
    dates: list[str] = field(default_factory=list)

    def to_dict(self, lang: str = "en") -> dict:
        return {"code": self.code, "severity": self.severity, "text": tr(self.msg, lang),
                "count": self.count, "dates": self.dates[:5]}


def _filled(n: Night) -> int:
    return sum(v is not None for v in (n.ahi, n.leak95_lpm, n.pressure95, n.mask_events, n.session_start))


def clean_cpap(nights: list[Night], source: str, guess_units: bool) -> tuple[list[Night], list[Warning]]:
    """Check one CPAP source. Returns usable nights and warnings."""
    warns: list[Warning] = []

    # 1) Nights with no usage at all can't be classed as used or not used.
    no_usage = [n for n in nights if n.usage_min is None]
    if no_usage:
        sev = "stop" if len(no_usage) == len(nights) else "warn"
        warns.append(Warning("usage_missing", sev, Msg("q_usage_missing", n=len(no_usage), src=source),
                             len(no_usage), [n.date.isoformat() for n in no_usage]))
    nights = [n for n in nights if n.usage_min is not None]
    if not nights:
        return [], warns

    # 2) Units: flag a suspicion, never convert on a guess.
    if guess_units:
        used = [n.usage_min for n in nights if n.usage_min > 0]
        if len(used) >= 3 and max(used) <= 24 and median(used) >= 1:
            warns.append(Warning("usage_unit_suspect", "warn", Msg("q_usage_hours", src=source), len(used)))
        leaks = [n.leak95_lpm for n in nights if n.leak95_lpm is not None]
        if len(leaks) >= 3 and max(leaks) <= 1.5 and any(v > 0 and v != int(v) for v in leaks):
            warns.append(Warning("leak_unit_suspect", "warn", Msg("q_leak_lps", src=source), len(leaks)))

    # 3) Impossible values → empty. An impossible usage counts as "not used" (the conservative reading).
    bad: dict[str, list[str]] = {}
    keep = []
    for n in nights:
        for f, (lo, hi) in LIMITS.items():
            v = getattr(n, f)
            if v is not None and not (lo <= v <= hi):
                bad.setdefault(f, []).append(n.date.isoformat())
                setattr(n, f, 0.0 if f == "usage_min" else None)
        if n.session_start is not None and not HHMM.match(str(n.session_start)):
            bad.setdefault("session_start", []).append(n.date.isoformat())
            n.session_start = None
        if n.usage_min is None:
            continue
        if n.usage_min == 0 and (n.ahi is not None or n.leak95_lpm is not None):
            n.ahi = n.leak95_lpm = n.pressure95 = None      # readings on an unused night are noise
        keep.append(n)
    for f, ds in bad.items():
        key = "q_impossible_usage" if f == "usage_min" else "q_impossible"
        warns.append(Warning(f"impossible_{f}", "warn", Msg(key, field=f, n=len(ds), src=source),
                             len(ds), ds))

    # 4) Duplicate nights: keep the most complete record (then the longest use).
    by: dict[date, Night] = {}
    dups = []
    for n in keep:
        cur = by.get(n.date)
        if cur is None:
            by[n.date] = n
            continue
        dups.append(n.date.isoformat())
        if (_filled(n), n.usage_min) > (_filled(cur), cur.usage_min):
            by[n.date] = n
    if dups:
        warns.append(Warning("duplicates", "warn", Msg("q_duplicates", n=len(dups), src=source), len(dups), dups))
    return [by[d] for d in sorted(by)], warns


def check_merged(nights: list[Night], recorded: set[date]) -> list[Warning]:
    """Checks on the final gap-filled nights: long gaps and fields that are missing everywhere."""
    warns: list[Warning] = []
    run_start, run = None, 0
    for n in nights + [None]:
        missing = n is not None and n.date not in recorded
        if missing:
            run_start = run_start or n.date
            run += 1
            continue
        if run >= GAP_WARN_NIGHTS:
            end = run_start + timedelta(days=run - 1)
            warns.append(Warning("gap", "warn", Msg("q_gap", n=run, a=run_start, b=end), run,
                                 [run_start.isoformat(), end.isoformat()]))
        run_start, run = None, 0

    used = [n for n in nights if n.usage_min > 0]
    for f, key in (("ahi", "q_no_ahi"), ("leak95_lpm", "q_no_leak"), ("session_start", "q_no_start"),
                   ("mask_events", "q_no_events")):
        if used and all(getattr(n, f) is None for n in used):
            warns.append(Warning(f"missing_{f}", "info", Msg(key)))
    if nights and all(n.wearable_sleep_min is None for n in nights):
        warns.append(Warning("missing_wearable", "info", Msg("q_no_wearable")))
    return warns


def clean_wearable(values: dict, kind: str) -> tuple[dict, list[Warning]]:
    """Drop impossible wearable values from one source's {"sleep"|"hrv"|"rhr": {night: value}}."""
    fields = {"sleep": "wearable_sleep_min", "hrv": "wearable_hrv_ms", "rhr": "wearable_rhr"}
    warns, out = [], {}
    for k, f in fields.items():
        lo, hi = LIMITS[f]
        good = {d: v for d, v in values.get(k, {}).items() if v is not None and lo <= v <= hi}
        bad = sorted(d.isoformat() for d in values.get(k, {}) if d not in good)
        if bad:
            warns.append(Warning(f"impossible_{f}", "warn", Msg("q_impossible", field=f, n=len(bad), src=kind),
                                 len(bad), bad))
        out[k] = good
    return out, warns
