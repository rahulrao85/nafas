"""End-to-end demo in the terminal (no browser, no API key needed).

    python scripts/run_demo.py                 # all three personas, latest morning
    python scripts/run_demo.py layla 2026-08-11
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass

from datetime import date  # noqa: E402

from nafas import actions as lib  # noqa: E402
from nafas import coach, loop, synthetic  # noqa: E402
from nafas.engine import fill_gaps  # noqa: E402
from nafas.llm import get_provider  # noqa: E402
from nafas.outcomes import person_outcomes  # noqa: E402


def dmy(d) -> str:
    return d.strftime("%d-%b-%Y")


def show(pid: str, as_of: date | None) -> None:
    p = synthetic.PERSONAS[pid]()
    r = loop.run(p["profile"], fill_gaps(p["nights"]), p["checkins"], as_of=as_of)
    m = r.momentum
    print(f"\n━━ {r.profile.display_name} · night of {dmy(r.as_of)} ━━")
    print(f"   {p['story']}")
    print(f"   Banked {m['banked_nights']} · 30-night adherence {m['adherence_30']}% · run {m['run']} · "
          f"lapses {len(r.lapses)} ({sum(1 for l in r.lapses if l.recovered)} recovered)")
    for d in r.detections:
        print(f"   ! {d.kind}: {d.evidence[0]}")
    for b in r.barriers[:2]:
        print(f"   ? {b.label} ({b.source}, {b.confidence:.0%})")
    iv = r.open_intervention
    if iv:
        a = lib.BY_ID[iv.action_id]
        print(f"   → {a.title['en']}  [BCT {a.bct} {a.bct_name}{', care team' if a.care_team else ''}]")
    if r.in_recovery:
        print("   ↺ comeback mode: one hour counts")
    note = coach.compose(r, get_provider())
    print(f"   ✉ ({note['source']}) {note['text']}")
    o = person_outcomes(r)
    print(f"   Outcomes: adherence {o['adherence_first_30']}% → {o['adherence_last_30']}%, "
          f"steps helped {o['actions_helped_pct']}% of {o['actions_judged']}")


if __name__ == "__main__":
    args = sys.argv[1:]
    as_of = date.fromisoformat(args[1]) if len(args) > 1 else None
    for pid in ([args[0]] if args else list(synthetic.PERSONAS)):
        show(pid, as_of)
