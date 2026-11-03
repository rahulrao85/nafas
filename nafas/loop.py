"""The behaviour loop, replayed morning by morning.

For each morning: score last night, run the detectors, infer barriers, open at most one small action,
judge earlier actions on the three nights that followed, and learn from the result. Replaying from the
first night makes the whole history reproducible: the same data and the same user choices give the same plan.
"""

from __future__ import annotations

import random
import zlib
from dataclasses import dataclass, field
from datetime import date

from . import actions as lib
from .barriers import infer
from .barriers import label as barrier_label
from .engine import (DECLINE_RECENT_DAYS, LARGE_LEAK_LPM, LEAK_CREEP_FLOOR, Detection, detect_all,
                     is_recovered, momentum)
from .i18n import Msg, tr
from .learning import Learner
from .models import CheckIn, Night, Profile

OUTCOME_NIGHTS = 3
OUTCOME_NIGHTS_CARE_TEAM = 7     # a refit or a replacement part takes days to arrive; judge the last 3 of 7
TRIGGERS = {"lapse", "decline", "leak", "leak_creep"}
LEAK_BARRIERS = {"MASK_FIT", "MASK_WEAR"}


@dataclass
class Intervention:
    id: str
    start: date
    start_idx: int
    trigger: str                     # detection kind or "self-report"
    barrier: str
    barrier_source: str
    action_id: str
    evidence: list[str] = field(default_factory=list)
    escalated: bool = False
    swapped_out: list[str] = field(default_factory=list)
    accepted: bool | None = None     # None = no answer (not the same as ignored)
    status: str = "open"             # open | helped | not_helped | replanned
    outcome_note: str = ""

    def to_dict(self, lang: str = "en") -> dict:
        return {
            "id": self.id, "start": self.start.isoformat(), "trigger": self.trigger,
            "barrier": self.barrier, "barrier_label": barrier_label(self.barrier, lang),
            "barrier_source": self.barrier_source,
            "action": lib.BY_ID[self.action_id].render(lang), "evidence": tr(self.evidence, lang),
            "trigger_label": tr(Msg("trigger_" + self.trigger), lang),
            "escalated": self.escalated, "swapped_out": self.swapped_out, "accepted": self.accepted,
            "status": self.status, "outcome_note": tr(self.outcome_note, lang),
        }


@dataclass
class Lapse:
    start: date
    comeback: date | None = None     # first night with any use after the lapse began
    recovered: date | None = None    # 3 of 4 nights at goal again

    def to_dict(self) -> dict:
        return {k: (v.isoformat() if v else None) for k, v in
                {"start": self.start, "comeback": self.comeback, "recovered": self.recovered}.items()}


@dataclass
class LoopResult:
    profile: Profile
    nights: list[Night]
    as_of: date
    detections: list[Detection]
    barriers: list
    momentum: dict
    interventions: list[Intervention]
    lapses: list[Lapse]
    clinician_flags: list[dict]
    learner: Learner
    nudge: dict

    @property
    def open_intervention(self) -> Intervention | None:
        return next((iv for iv in reversed(self.interventions) if iv.status == "open"), None)

    @property
    def in_recovery(self) -> Lapse | None:
        return self.lapses[-1] if self.lapses and self.lapses[-1].recovered is None else None


def _rng(*parts) -> random.Random:
    return random.Random(zlib.crc32("|".join(map(str, parts)).encode()))


def _judge(iv: Intervention, after: list[Night], goal_min: float) -> tuple[bool, str]:
    if iv.barrier in LEAK_BARRIERS:
        used = [n for n in after if n.usage_min > 0 and n.leak95_lpm is not None]
        line = LARGE_LEAK_LPM if iv.barrier == "MASK_FIT" else LEAK_CREEP_FLOOR
        ok = [n for n in used if n.leak95_lpm <= line]
        return len(ok) >= 2, Msg("judge_leak", line=f"{line:.0f}", n=len(ok), m=len(after))
    if iv.trigger == "lapse":
        used = [n for n in after if n.usage_min > 0]
        return len(used) >= 2, Msg("judge_comeback", n=len(used), m=len(after))
    met = [n for n in after if n.usage_min >= goal_min]
    return len(met) >= 2, Msg("judge_goal", n=len(met), m=len(after))


def run(profile: Profile, nights: list[Night], checkins: list[CheckIn] | None = None,
        events: list[dict] | None = None, as_of: date | None = None) -> LoopResult:
    """Replay the loop up to `as_of` (inclusive). `nights` must already be gap-filled and sorted."""
    checkins = sorted(checkins or [], key=lambda c: c.date)
    events = events or []
    if as_of is not None:
        nights = [n for n in nights if n.date <= as_of]
    if not nights:
        raise ValueError("No nights on or before the selected date.")
    goal_min = max(60.0, profile.goal_hours * 60)

    learner = Learner()
    interventions: list[Intervention] = []
    lapses: list[Lapse] = []
    flags: list[dict] = []
    dets: list[Detection] = []
    barriers: list = []

    for i, night in enumerate(nights):
        hist = nights[: i + 1]
        today = night.date
        seen = [c for c in checkins if c.date <= today]

        # 1) Judge actions whose three follow-up nights are now in.
        for iv in interventions:
            window = OUTCOME_NIGHTS_CARE_TEAM if lib.BY_ID[iv.action_id].care_team else OUTCOME_NIGHTS
            if iv.status == "open" and i - iv.start_idx >= window:
                after = nights[iv.start_idx + 1 + window - OUTCOME_NIGHTS: iv.start_idx + 1 + window]
                helped, note = _judge(iv, after, goal_min)
                iv.status, iv.outcome_note = ("helped" if helped else "not_helped"), note
                learner.record(iv.action_id, helped)

        # 2) Detect.
        dets = detect_all(hist)
        # A recent, already-recovered lapse explains a dip in the 14-day average; don't call it a decline.
        if lapses and lapses[-1].recovered and (today - lapses[-1].recovered).days < DECLINE_RECENT_DAYS:
            dets = [d for d in dets if d.kind != "decline"]
        kinds = {d.kind for d in dets}

        # 3) Lapse bookkeeping — a lapse never erases banked nights; it opens a comeback.
        cur = lapses[-1] if lapses and lapses[-1].recovered is None else None
        if cur is None and "lapse" in kinds:
            cur = Lapse(start=next(d.started for d in dets if d.kind == "lapse"))
            lapses.append(cur)
        if cur is not None:
            if cur.comeback is None and night.usage_min > 0 and today > cur.start:
                cur.comeback = today
            if cur.comeback is not None and is_recovered(hist):
                cur.recovered = today

        # 4) Clinician flags: once per episode (7-day quiet period).
        if "clinical" in kinds and not (flags and (today - date.fromisoformat(flags[-1]["date"])).days < 7):
            d = next(d for d in dets if d.kind == "clinical")
            flags.append({"date": today.isoformat(), "evidence": d.evidence})

        # 5) Barriers and at most one new action per morning.
        barriers = infer(hist, dets, seen, profile)
        today_report = next((c for c in reversed(seen) if c.date == today), None)
        open_iv = next((iv for iv in interventions if iv.status == "open"), None)

        if open_iv and today_report and today_report.barrier != open_iv.barrier:
            open_iv.status, open_iv.outcome_note = "replanned", Msg("replanned")
            open_iv = None

        trigger = None
        if today_report:
            trigger = "self-report"
        elif kinds & TRIGGERS:
            trigger = next(d.kind for d in dets if d.kind in TRIGGERS)

        if open_iv is None and trigger and barriers:
            b = barriers[0]
            past = [iv for iv in interventions if iv.barrier == b.code and iv.status in ("helped", "not_helped")]
            escalate = len(past) >= 2 and all(iv.status == "not_helped" for iv in past[-2:])
            cands = lib.for_barrier(b.code)
            preferred = [a for a in cands if a.care_team == escalate] or cands
            act = learner.choose(preferred, _rng(profile.id, today, b.code))
            if act:
                interventions.append(Intervention(
                    id=f"{today.isoformat()}-{b.code}", start=today, start_idx=i,
                    trigger=trigger, barrier=b.code, barrier_source=b.source, action_id=act.id,
                    evidence=b.evidence + [e for d in dets if d.kind == trigger for e in d.evidence],
                    escalated=escalate))

        # 6) The person's own choices: swap, accept, dismiss.
        for ev in (e for e in events if e.get("date") == today.isoformat()):
            iv = next((x for x in interventions if x.id == ev.get("intervention_id")), None)
            if iv is None or iv.status != "open":
                continue
            if ev["type"] == "swap":
                iv.swapped_out.append(iv.action_id)
                nxt = learner.choose(lib.for_barrier(iv.barrier), _rng(profile.id, today, iv.id, len(iv.swapped_out)),
                                     exclude=set(iv.swapped_out))
                if nxt:
                    iv.action_id = nxt.id
                else:
                    iv.swapped_out.pop()
            elif ev["type"] in ("accept", "dismiss"):
                iv.accepted = ev["type"] == "accept"

    mom = momentum(nights, goal_min)
    result = LoopResult(profile, nights, nights[-1].date, dets, barriers, mom, interventions, lapses,
                        flags, learner, nudge={})
    result.nudge = plan_nudge(result)
    return result


def plan_nudge(r: LoopResult) -> dict:
    """At most one nudge a day, only when there is something to do, never in quiet hours."""
    p = r.profile
    if not p.nudges_enabled:
        return {"send": False, "reason": Msg("nudge_off")}
    offered = [iv for iv in r.interventions if iv.accepted is not None][-3:]
    every_other_day = len(offered) == 3 and not any(iv.accepted for iv in offered)
    hour, qs, qe = p.nudge_hour, p.quiet_start, p.quiet_end
    in_quiet = (qs <= hour < qe) if qs < qe else (hour >= qs or hour < qe)
    if in_quiet:
        return {"send": False, "reason": Msg("nudge_quiet")}
    iv = r.open_intervention
    rec = r.in_recovery
    if iv is None and rec is None:
        return {"send": False, "reason": Msg("nudge_ontrack")}
    if every_other_day and r.as_of.toordinal() % 2:
        return {"send": False, "reason": Msg("nudge_reduced")}
    if iv is not None and iv.trigger != "lapse":
        text = lib.BY_ID[iv.action_id].render(p.language)["title"]
    else:
        text = lib.COMEBACK.get(p.language, lib.COMEBACK["en"])
    return {"send": True, "at": f"{hour:02d}:00", "text": text,
            "reason": Msg("nudge_one_reduced" if every_other_day else "nudge_one")}
