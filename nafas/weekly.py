"""Weekly adherence view: one row per week (Monday–Sunday), with what happened and what we tried."""

from __future__ import annotations

from datetime import timedelta
from statistics import mean

from .engine import LARGE_LEAK_LPM, status_of
from .loop import LoopResult


def weekly_view(r: LoopResult, weeks: int = 12) -> list[dict]:
    goal_min = max(60.0, r.profile.goal_hours * 60)
    nights = r.nights
    if not nights:
        return []
    last = nights[-1].date
    first_monday = last - timedelta(days=last.weekday()) - timedelta(weeks=weeks - 1)
    by_date = {n.date: n for n in nights}
    rows = []
    for w in range(weeks):
        mon = first_monday + timedelta(weeks=w)
        days, used = [], []
        for k in range(7):
            d = mon + timedelta(days=k)
            n = by_date.get(d)
            if n is None:
                days.append({"date": d.isoformat(), "status": "future" if d > last else "none"})
                continue
            days.append({"date": d.isoformat(), "status": status_of(n, goal_min),
                         "hours": round(n.usage_min / 60, 1),
                         "leak": n.leak95_lpm, "high_leak": (n.leak95_lpm or 0) > LARGE_LEAK_LPM})
            if n.usage_min > 0:
                used.append(n)
        sun = mon + timedelta(days=6)
        in_week = lambda d: mon <= d <= sun  # noqa: E731
        recorded = [x for x in days if x["status"] not in ("future", "none")]
        if not recorded:
            continue
        ahis = [n.ahi for n in used if n.ahi is not None]
        rows.append({
            "week_start": mon.isoformat(),
            "days": days,
            "nights_recorded": len(recorded),
            "nights_used": len(used),
            "nights_met": sum(1 for x in recorded if x["status"] == "met"),
            "avg_hours": round(mean(x["hours"] for x in recorded), 1),
            "high_leak_nights": sum(1 for x in recorded if x.get("high_leak")),
            "avg_ahi": round(mean(ahis), 1) if ahis else None,
            "lapses_started": sum(1 for l in r.lapses if in_week(l.start)),
            "comebacks": sum(1 for l in r.lapses if l.comeback and in_week(l.comeback)),
            "actions": [{"id": iv.id, "barrier": iv.barrier, "action_id": iv.action_id, "status": iv.status}
                        for iv in r.interventions if in_week(iv.start)],
        })
    return rows
