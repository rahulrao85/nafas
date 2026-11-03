"""Synthetic CPAP nights — the only data the demo uses.

Shapes are realistic (ResMed-style 95th-percentile leak and pressure, residual AHI around 1 on
effective therapy, usage around 7 h) but every value is generated from a fixed seed. No real person's
data is used or embedded. The three personas are fictional and their stories are scripted to show the
loop end to end; they are not evidence that the loop works (see docs/EVALUATION.md).
"""

from __future__ import annotations

import math
import random
from datetime import date, timedelta

from .models import CheckIn, Night, Profile

LAST_NIGHT = date(2026, 11, 2)   # demo "today" is the morning of 03-Nov-2026


def _d(s: str) -> date:
    return date.fromisoformat(s)


def _clip(v, lo, hi):
    return max(lo, min(hi, v))


def _fmt_time(minutes: float) -> str:
    m = int(round(minutes)) % 1440
    return f"{m // 60:02d}:{m % 60:02d}"


def gen_nights(start: date, n: int, rng: random.Random, *, usage_mean=455, usage_sd=55, p_miss=0.02,
               bedtime_min=23 * 60 + 10, wearable=False, episodes=()) -> list[Night]:
    """episodes: iterable of (kind, start_date, end_date, params-dict)."""
    out = []
    for k in range(n):
        d = start + timedelta(days=k)
        active = [(kind, s, e, p) for kind, s, e, p in episodes if s <= d <= e]

        def frac(s, e):
            span = max(1, (e - s).days)
            return (d - s).days / span

        usage = rng.gauss(usage_mean, usage_sd)
        miss = rng.random() < p_miss
        bedtime = rng.gauss(bedtime_min, 25)
        mask_events = 1 if rng.random() < 0.8 else 2
        leak = 0.0 if rng.random() < 0.5 else rng.expovariate(1 / 8.0)
        ahi = math.exp(rng.gauss(math.log(1.05), 0.38))
        pressure = _clip(rng.gauss(12.8, 1.4), 9.5, 15.5)
        away = False

        for kind, s, e, p in active:
            if kind == "rocky_start":          # new user: short, broken nights
                usage = rng.gauss(210, 90)
                mask_events = rng.choice([2, 3, 3, 4])
                miss = miss or rng.random() < 0.12
            elif kind == "leak":                # poor seal: big leak, shorter nights, events creep up
                leak = rng.uniform(27, 46)
                usage *= rng.uniform(0.6, 0.9)
                ahi *= p.get("ahi_mult", 1.6)
            elif kind == "leak_creep":          # cushion wearing out: leak drifts up over weeks
                leak = max(leak, rng.gauss(10 + 22 * frac(s, e), 4))
            elif kind == "travel":
                miss, away = True, True
            elif kind == "illness":
                usage = rng.uniform(0, 140)
                miss = miss or rng.random() < 0.5
            elif kind == "routine_shift":       # e.g. Ramadan nights: later, shorter, split sleep
                bedtime += p.get("shift_min", 150)
                usage *= rng.uniform(0.55, 0.9)
                mask_events = rng.choice([1, 2, 2, 3])
            elif kind == "decline":             # motivation fading: shorter nights, more misses
                f = frac(s, e)
                usage *= 1 - p.get("depth", 0.55) * f
                miss = miss or rng.random() < p.get("miss_to", 0.35) * f
            elif kind == "weekend_skip" and d.weekday() in (4, 5):
                miss = miss or rng.random() < 0.7
            elif kind == "shift_work" and ((d - s).days // 7) % 3 == 2:   # every third week on nights
                bedtime = rng.gauss(8 * 60 + 30, 30)
                usage *= rng.uniform(0.6, 0.85)
            elif kind == "lapse":
                miss = True

        usage = 0.0 if miss else round(_clip(usage, 15, 620))
        used = usage > 0
        night = Night(
            date=d,
            usage_min=usage,
            ahi=round(ahi, 1) if used else None,
            leak95_lpm=round(_clip(leak, 0, 60), 1) if used else None,
            pressure95=round(pressure, 1) if used else None,
            mask_events=mask_events if used else 0,
            session_start=_fmt_time(bedtime) if used else None,
        )
        if wearable:
            night.wearable_sleep_min = round(_clip(rng.gauss(410, 40), 200, 560)) if (away or not used) \
                else round(_clip(usage + rng.gauss(25, 15), 0, 600))
        out.append(night)
    return out


# ─── Fictional personas ───────────────────────────────────────────────────────

def persona_layla() -> dict:
    """New to CPAP: rocky first fortnight, a leak spell that nudges AHI up, a trip, then a fade and recovery."""
    start = _d("2026-07-05")
    eps = [
        ("rocky_start", _d("2026-07-05"), _d("2026-07-18"), {}),
        ("leak", _d("2026-08-03"), _d("2026-08-13"), {"ahi_mult": 2.0}),
        ("leak", _d("2026-08-08"), _d("2026-08-11"), {"ahi_mult": 6.0}),
        ("travel", _d("2026-09-14"), _d("2026-09-18"), {}),
        ("decline", _d("2026-10-06"), _d("2026-11-02"), {"depth": 0.45, "miss_to": 0.2}),
    ]
    nights = gen_nights(start, (LAST_NIGHT - start).days + 1, random.Random(101),
                        wearable=True, episodes=eps)
    profile = Profile(id="layla", display_name="Layla (fictional)", language="en", goal_hours=4,
                      mask_type="full face", notes="New CPAP user, 4 months in. Smart ring for sleep.",
                      tags={"language": "en", "age_band": "35-44", "shift_worker": False})
    checkins = [CheckIn(_d("2026-07-09"), "DRYNESS", "Mouth like sandpaper at 3 a.m."),
                CheckIn(_d("2026-09-19"), "TRAVEL_AWAY", "Back from Muscat.")]
    return {"profile": profile, "nights": nights, "checkins": checkins,
            "story": {"en": "New user: rocky start → leak spell (care-team flag) → travel lapse and comeback → "
                            "an October fade she came back from.",
                      "ar": "مستخدمة جديدة: بداية متعثرة ← فترة تسرب (تنبيه لفريق الرعاية) ← انقطاع بسبب السفر ثم عودة ← "
                            "تراجع في أكتوبر عادت منه."}}


def persona_omar() -> dict:
    """Two years on CPAP: Ramadan schedule shifts, Eid travel, sick days, and cushions that wear out."""
    n = 790
    start = LAST_NIGHT - timedelta(days=n - 1)
    eps = [
        ("leak_creep", _d("2025-06-01"), _d("2025-06-28"), {}),
        ("illness", _d("2025-11-10"), _d("2025-11-14"), {}),
        ("leak_creep", _d("2026-01-05"), _d("2026-01-30"), {}),
        ("routine_shift", _d("2025-03-01"), _d("2025-03-29"), {"shift_min": 160}),
        ("travel", _d("2025-03-31"), _d("2025-04-03"), {}),
        ("routine_shift", _d("2026-02-18"), _d("2026-03-19"), {"shift_min": 160}),
        ("travel", _d("2026-03-21"), _d("2026-03-24"), {}),
        ("leak_creep", _d("2026-10-08"), _d("2026-11-02"), {}),
    ]
    nights = gen_nights(start, n, random.Random(202), usage_mean=465, wearable=True, episodes=eps)
    profile = Profile(id="omar", display_name="Omar (fictional)", language="ar", goal_hours=6,
                      mask_type="nasal", notes="Long-term user, prefers Arabic. Goal 6 h a night.",
                      tags={"language": "ar", "age_band": "45-54", "shift_worker": False})
    checkins = [CheckIn(_d("2025-11-11"), "CONGESTION_ILLNESS", "Flu.")]
    return {"profile": profile, "nights": nights, "checkins": checkins,
            "story": {"en": "Long-term user: Ramadan bedtimes, Eid travel, a flu week, and cushions wearing out "
                            "(leak creeping now).",
                      "ar": "مستخدم منذ مدة طويلة: مواعيد نوم رمضان، سفر العيد، أسبوع إنفلونزا، ووسائد تهترئ "
                            "(التسرب يزداد الآن)."}}


def persona_ravi() -> dict:
    """Shift worker: day sleeps every third week, weekend misses, then 'I feel fine' and a lapse."""
    start = _d("2026-06-06")
    eps = [
        ("rocky_start", _d("2026-06-06"), _d("2026-06-14"), {}),
        ("shift_work", _d("2026-06-06"), _d("2026-11-02"), {}),
        ("weekend_skip", _d("2026-07-01"), _d("2026-08-15"), {}),
        ("decline", _d("2026-09-20"), _d("2026-10-25"), {"depth": 0.6, "miss_to": 0.4}),
        ("lapse", _d("2026-10-29"), _d("2026-11-02"), {}),
    ]
    nights = gen_nights(start, (LAST_NIGHT - start).days + 1, random.Random(303),
                        usage_mean=420, usage_sd=60, episodes=eps)
    profile = Profile(id="ravi", display_name="Ravi (fictional)", language="en", goal_hours=4,
                      mask_type="nasal pillows", notes="Hospital shift worker; nights every third week.",
                      tags={"language": "en", "age_band": "25-34", "shift_worker": True})
    checkins = [CheckIn(_d("2026-10-20"), "FELT_FINE", "Honestly feel ok without it.")]
    return {"profile": profile, "nights": nights, "checkins": checkins,
            "story": {"en": "Shift worker: day sleeps, weekend misses, 'I feel fine' — and a lapse right now.",
                      "ar": "يعمل بنظام المناوبات: نوم نهاري، ليالٍ فائتة في العطل، \"أشعر أنني بخير\"، وانقطاع الآن."}}


PERSONAS = {"layla": persona_layla, "omar": persona_omar, "ravi": persona_ravi}


# ─── Synthetic cohort (for the outcome-measurement pipeline) ──────────────────

# Mix chosen so that the cohort is not all green: about three in four still meet the 70% bar at six
# months. That is still kinder than published real-world adherence; it is not tuned to flatter the loop.
ARCHETYPES = [("steady", 0.3), ("rocky_start", 0.15), ("fader", 0.2), ("lapser", 0.15), ("shift", 0.1),
              ("dropout", 0.1)]


def cohort(n: int = 150, days: int = 180, seed: int = 7) -> list[dict]:
    rng = random.Random(seed)
    start = LAST_NIGHT - timedelta(days=days - 1)
    users = []
    for u in range(n):
        arche = rng.choices([a for a, _ in ARCHETYPES], weights=[w for _, w in ARCHETYPES])[0]
        eps = []
        if arche == "rocky_start":
            eps.append(("rocky_start", start, start + timedelta(days=rng.randint(10, 30)), {}))
        if arche == "fader":
            s = start + timedelta(days=rng.randint(40, 120))
            # half the faders keep fading to the end of the window; the rest bottom out and come back
            e = LAST_NIGHT if rng.random() < 0.5 else s + timedelta(days=rng.randint(25, 50))
            eps.append(("decline", s, e, {"depth": rng.uniform(0.5, 0.85), "miss_to": rng.uniform(0.3, 0.7)}))
        if arche == "dropout":
            s = start + timedelta(days=rng.randint(30, days - 20))
            eps.append(("decline", s - timedelta(days=14), s, {"depth": 0.6, "miss_to": 0.5}))
            eps.append(("lapse", s, LAST_NIGHT, {}))
        if arche in ("lapser", "steady", "fader") and rng.random() < (0.9 if arche == "lapser" else 0.3):
            for _ in range(rng.randint(1, 3)):
                s = start + timedelta(days=rng.randint(15, days - 10))
                eps.append(("travel", s, s + timedelta(days=rng.randint(2, 6)), {}))
        if rng.random() < 0.3:
            s = start + timedelta(days=rng.randint(10, days - 15))
            eps.append(("leak", s, s + timedelta(days=rng.randint(4, 10)), {}))
        if arche == "shift":
            eps.append(("shift_work", start, LAST_NIGHT, {}))
        lang = rng.choices(["en", "ar", "other"], weights=[0.5, 0.35, 0.15])[0]
        profile = Profile(id=f"c{u:03d}", display_name=f"Synthetic {u:03d}",
                          language="ar" if lang == "ar" else "en",
                          tags={"language": lang, "age_band": rng.choice(["25-34", "35-44", "45-54", "55-64", "65+"]),
                                "shift_worker": arche == "shift", "archetype": arche})
        nights = gen_nights(start, days, random.Random(seed * 1000 + u),
                            usage_mean=rng.gauss(410, 55), usage_sd=rng.uniform(50, 110),
                            p_miss=rng.uniform(0.01, 0.12),
                            wearable=rng.random() < 0.4, episodes=eps)
        users.append({"profile": profile, "nights": nights, "checkins": []})
    return users
