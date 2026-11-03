"""Sustained-outcome measurement: persistence, recovery after lapses, retention, biomarker change, equity.

These are the metrics Challenge 09 asks for. Here they run on a synthetic cohort to prove the pipeline;
the numbers describe synthetic people and say nothing about real-world effect.
"""

from __future__ import annotations

import math
from collections import defaultdict
from statistics import mean, median

from .engine import fill_gaps
from .loop import LoopResult, run

MIN_GROUP = 20


def person_outcomes(r: LoopResult) -> dict:
    goal_min = max(60.0, r.profile.goal_hours * 60)
    n = r.nights
    met = [x.usage_min >= goal_min for x in n]

    def adherence(window):
        return round(100 * sum(window) / len(window), 1) if window else None

    first30, last30 = n[:30], n[-30:]
    ahi_first = [x.ahi for x in first30 if x.ahi is not None]
    ahi_last = [x.ahi for x in last30 if x.ahi is not None]
    rec_days = [(l.recovered - l.start).days for l in r.lapses if l.recovered]
    closed = [iv for iv in r.interventions if iv.status in ("helped", "not_helped")]
    last28 = n[-28:]
    return {
        "nights": len(n),
        "adherence_first_30": adherence(met[:30]),
        "adherence_last_30": adherence(met[-30:]),
        "adherence_all": adherence(met),
        "persisting": adherence(met[-30:]) is not None and adherence(met[-30:]) >= 70,
        "retained": sum(1 for x in last28 if x.usage_min > 0) >= 4,   # still using at least weekly
        "lapses": len(r.lapses),
        "lapses_recovered": len(rec_days),
        "recovery_rate": round(100 * len(rec_days) / len(r.lapses), 1) if r.lapses else None,
        "median_days_to_recover": median(rec_days) if rec_days else None,
        "usage_h_first_30": round(mean(x.usage_min for x in first30) / 60, 2) if first30 else None,
        "usage_h_last_30": round(mean(x.usage_min for x in last30) / 60, 2) if last30 else None,
        "ahi_first_30": round(mean(ahi_first), 2) if ahi_first else None,
        "ahi_last_30": round(mean(ahi_last), 2) if ahi_last else None,
        "actions_judged": len(closed),
        "actions_helped_pct": round(100 * sum(iv.status == "helped" for iv in closed) / len(closed), 1) if closed else None,
    }


def wilson(k: int, n: int, z: float = 1.96) -> list[float] | None:
    """95% Wilson score interval for a proportion, in percent."""
    if n == 0:
        return None
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return [round(100 * (centre - half), 1), round(100 * (centre + half), 1)]


def _summarise(rows: list[dict]) -> dict:
    def avg(key):
        vals = [r[key] for r in rows if r.get(key) is not None]
        return round(mean(vals), 1) if vals else None

    def pct(key):
        return round(100 * sum(1 for r in rows if r[key]) / len(rows), 1) if rows else None

    days = [r["median_days_to_recover"] for r in rows if r["median_days_to_recover"] is not None]
    return {
        "people": len(rows),
        "persisting_pct": pct("persisting"),
        "persisting_ci95": wilson(sum(1 for r in rows if r["persisting"]), len(rows)),
        "retained_pct": pct("retained"),
        "adherence_first_30": avg("adherence_first_30"),
        "adherence_last_30": avg("adherence_last_30"),
        "lapses_per_person": avg("lapses"),
        "recovery_rate": avg("recovery_rate"),
        "median_days_to_recover": median(days) if days else None,
        "ahi_first_30": avg("ahi_first_30"),
        "ahi_last_30": avg("ahi_last_30"),
        "actions_helped_pct": avg("actions_helped_pct"),
    }


def cohort_report(users: list[dict]) -> dict:
    rows, tags = [], []
    for u in users:
        r = run(u["profile"], fill_gaps(u["nights"]), u.get("checkins", []))
        rows.append(person_outcomes(r))
        tags.append(u["profile"].tags)
    report = {"overall": _summarise(rows), "by": {}}
    for key in ("language", "age_band", "shift_worker"):
        groups = defaultdict(list)
        for row, t in zip(rows, tags):
            groups[str(t.get(key))].append(row)
        report["by"][key] = {g: _summarise(v) for g, v in sorted(groups.items())}
    # Equity gap: the widest difference in persistence between groups of each attribute,
    # counting only groups big enough to compare (small groups swing on one or two people).
    # A gap only counts as real if the best and worst groups' 95% intervals don't overlap.
    report["equity_gaps"], report["equity_gap_significant"] = {}, {}
    for key, grp in report["by"].items():
        big = [v for v in grp.values() if v["people"] >= MIN_GROUP]
        if len(big) < 2:
            report["equity_gaps"][key] = report["equity_gap_significant"][key] = None
            continue
        hi = max(big, key=lambda v: v["persisting_pct"])
        lo = min(big, key=lambda v: v["persisting_pct"])
        report["equity_gaps"][key] = round(hi["persisting_pct"] - lo["persisting_pct"], 1)
        report["equity_gap_significant"][key] = lo["persisting_ci95"][1] < hi["persisting_ci95"][0]
    report["min_group"] = MIN_GROUP
    report["caveat"] = ("Synthetic cohort. These figures test the measurement pipeline only; "
                        "they are not evidence of real-world effect.")
    return report
