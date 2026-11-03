# Nafas

**A CPAP-adherence behaviour loop that survives bad weeks.**
*Nafas* (نَفَس) means "breath" in Arabic, Persian, Hindi and Urdu.
Entry for the Future Health Digital Innovation Challenge 2026 (Abu Dhabi, run by Hack2Skill), Wellbeing Challenge 09: *Sustaining Healthy Behaviors*.

About half of people prescribed CPAP for obstructive sleep apnoea stop using it or use it too little; published non-adherence rates run from 29% to 83% (Weaver & Grunstein, 2008). It rarely fails in one go. A trip, a leaky cushion, Ramadan bedtimes, a cold or a run of nights where you feel fine without it each break the habit for a few nights. Most apps then show a broken streak, and the person stops opening them.

Nafas watches each night's therapy data and does five things:

1. **Notices** a lapse, a slow decline, a large mask leak, or a leak creeping up, and shows the evidence.
2. **Names the likely barrier** from the data (mask seal, worn cushion, mid-night removal, travel, a moved bedtime, fading motivation). The person can correct it with one tap.
3. **Offers one small step**, tagged with its behaviour-change technique, with why it should help and where it stops helping.
4. **Judges the step** on the next three nights, learns what works for this person, and escalates to the care team after two misses.
5. **Keeps progress.** Banked nights never reset. A lapse opens a one-hour comeback goal instead of a restart from zero.

The team lead has been a CPAP patient for two years. Every barrier in the library is one they have hit.

> Prototype. Not a medical device and not medical advice. The demo uses **synthetic, fictional people only**.

---

## Run it

Requires Python 3.10 or later.

```bash
pip install -r requirements.txt
python run.py                      # → http://127.0.0.1:5057
```

No API key is needed: without one, coach notes come from the reviewed template. To have Claude word the notes:

```bash
export ANTHROPIC_API_KEY=...       # or: ant auth login
python run.py
```

Terminal-only demo: `python scripts/run_demo.py` (or `python scripts/run_demo.py layla 2026-08-11`).
Tests: `python -m pytest -q` (43 tests, about 6 s).
Regenerate the declared synthetic dataset: `python scripts/generate_synthetic.py`.

### Choosing the language model

| `NAFAS_LLM` | Needs | Notes |
|---|---|---|
| `claude` (default) | `ANTHROPIC_API_KEY`, `ANTHROPIC_AUTH_TOKEN` or an `ant auth login` profile | Model `NAFAS_CLAUDE_MODEL`, default `claude-opus-5-5`, effort `low`; refusals fall back to another model on the server |
| `azure` | `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_DEPLOYMENT` | Kept from the original Azure AI Foundry build |
| `offline` | nothing | Fixed template; used in tests |

If the chosen provider isn't configured or fails, the app uses the template and says why. Providers sit behind one small interface (`nafas/llm/base.py`), so adding another takes one file.

## A three-minute demo for judges

1. **Layla, a new user.** Drag the timeline to **12-Aug-2026**. The page shows a large leak, a care-team flag for high residual AHI (fixed wording, no LLM), and comeback mode. The step is *Ask for a mask refit*, flagged as escalated because two self-fix steps didn't help. Open **Weekly** to see the leak dots and those two failed steps.
2. Press **Play** from early September. On **15-Sep-2026** a trip starts and her ring sees sleep but CPAP sees none, so the app asks whether she's away. She comes back, and the banked count never dips.
3. **Omar, two years in, Arabic.** The interface switches to right-to-left. His leak has crept up over two weeks, so the step is *Order a replacement*. Scroll back to March 2025 or February 2026 to see Ramadan bedtimes picked up as *Changed sleep schedule*, with *Use it for every main sleep* offered.
4. **Ravi, a shift worker in a lapse now.** He reported *Felt fine without it* on 20-Oct-2026. Tap a different barrier and the plan changes. Type "chest pain" in the note and an emergency message appears instead of coaching.
5. **Outcomes → Run measurement.** This runs the Challenge 09 metrics (persistence, recovery after lapses, retention, residual AHI, equity by language, age band and shift work) on a 150-person synthetic cohort.
6. **Settings.** Set goal, language, nudge time and quiet hours, and turn AI wording and care-team sharing on or off. *Preview care-team summary* is refused until sharing is on. You can also upload a ResMed `STR.edf`, a CSV or a JSON file, or delete everything from the session.

## How this maps to Challenge 09

| Challenge 09 asks for | Where it is |
|---|---|
| Adaptive personal plans: small, achievable actions from goals, context and data | Goal setting; barrier → one step (`barriers.py`, `actions.py`); per-person learning (`learning.py`) |
| Detect declining engagement or a lapse, find barriers, adjust without blame, no reset to zero | `engine.py` detectors; `loop.py` comeback, re-plan and escalation; banked nights and the forgiving run in `engine.momentum` |
| Evidence-based support with rationale and limits visible | BCT tag, *Why this might help* and *Where it stops helping* on every step; [docs/BEHAVIOUR_CHANGE.md](docs/BEHAVIOUR_CHANGE.md) |
| User autonomy and inclusion; no manipulative or punitive use | Swap, skip, nudge limits, quiet hours, AI off switch, consent-gated sharing; English and Arabic (RTL); no employer or insurer view by design ([docs/PRIVACY_SAFETY.md](docs/PRIVACY_SAFETY.md)) |
| Sustained outcome measurement | `outcomes.py`, Outcomes tab, [docs/EVALUATION.md](docs/EVALUATION.md) |

## Documents

- [Architecture](docs/ARCHITECTURE.md)
- [Data sources (declared)](docs/DATA_SOURCES.md)
- [Privacy, safety and responsible AI](docs/PRIVACY_SAFETY.md)
- [Behaviour-change design](docs/BEHAVIOUR_CHANGE.md)
- [Evaluation and outcome measures](docs/EVALUATION.md)
- [Maturity: before vs during the challenge](docs/MATURITY.md)
- [Assumptions, dependencies and limitations](docs/ASSUMPTIONS_LIMITATIONS.md)
- [Commercial path to pilot](docs/COMMERCIAL_PATH.md)

## Layout

```
nafas/
  models.py       Night, CheckIn, Profile
  ingest.py       ResMed STR.edf / CSV / JSON → Night (drops identifiers)
  engine.py       detectors, thresholds, no-reset momentum
  barriers.py     barrier inference with evidence; self-report wins
  actions.py      action library (EN + AR), BCT-tagged
  learning.py     per-person Thompson sampling
  loop.py         the morning-by-morning loop, replayable
  weekly.py       weekly adherence view
  outcomes.py     person and cohort outcome metrics, equity breakdowns
  coach.py        fact brief → LLM wording → safety check → template fallback
  safety.py       output rules, crisis-note detection
  llm/            claude (default) · azure · offline
  server.py       Flask API, session memory only
  static/         single-page UI (design tokens, light and dark, 375 px+)
scripts/          generate_synthetic.py, run_demo.py
data/synthetic/   the declared demo dataset (generated)
tests/            43 tests
```
