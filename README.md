# Nafas

**Nafas helps people with sleep apnoea keep using their CPAP through bad weeks, using the nightly data their machine already records (SD card or app export), plus optional watch or ring sleep.**

*Nafas* (نَفَس) means "breath" in Arabic, Persian, Hindi and Urdu. Entry for the Future Health Digital Innovation Challenge 2026 (Abu Dhabi, run by Hack2Skill), Wellbeing Challenge 09: *Sustaining Healthy Behaviors*.

Published CPAP non-adherence runs from 29% to 83% (Weaver & Grunstein, 2008). Therapy rarely fails in one go. A trip, a leaky cushion, Ramadan bedtimes, a cold or "I feel fine without it" each break the habit for a few nights. Most apps then show a broken streak, and the person stops opening them.

Each morning Nafas:

1. **Notices** a lapse, a slow decline, a large mask leak or a leak creeping up, and shows the evidence.
2. **Names the likely barrier** (mask seal, worn cushion, mask off at night, a trip, a moved bedtime, fading motivation). One tap corrects it.
3. **Offers one small step**, tagged with its behaviour-change technique, saying why it should help and where it stops helping.
4. **Judges the step** on the next three nights, learns what works for this person, and brings in the care team after two misses.
5. **Keeps progress.** Banked nights never reset; a lapse opens a one-hour comeback goal.

The team lead has used CPAP nightly for two years. Every barrier in the library is one they have hit.

> Prototype. Not a medical device and not medical advice. The demo uses **synthetic, fictional people only**.

## Tested: 160 labelled cases, 110 of them hard

| What | Result |
|---|---|
| Emergency wording in a note (English + Arabic) → stop coaching, show the emergency number | **Sensitivity 100%** (47/47) · specificity 96.7% (29/30) |
| High residual AHI → care-team flag | **100%** (12/12) |
| Lapse, decline, leak and leak-creep detectors | 100% (26/26) |
| Barrier inference, top-1 | 100% (14/14) |
| Ask-your-data guardrails: question routing + checks on model answers | **100%** (31/31) |
| Live Q&A with Gemini 3.5 Flash (14 questions, EN + AR) | 11/11 model answers passed every check; emergency, clinical and prompt-injection questions never reached the model ([results](docs/QA_EVAL_RESULTS.md)) |

The hard cases are: missing fields, impossible values, wrong units, duplicate nights, gaps, mixed sources, negation, near-miss wording, and Arabic dialects. The scores above are after fixes. The first run scored 69/103. A held-out batch of emergency phrasings, run once untouched, caught only 8 of 15. Both are reported, with what was fixed, in [docs/BENCHMARK.md](docs/BENCHMARK.md); every case is listed in [docs/BENCHMARK_RESULTS.md](docs/BENCHMARK_RESULTS.md). Reproduce with `python scripts/benchmark.py`.

Bad data never crashes the app and is never silently dropped. Each problem becomes a visible warning saying which checks it turns off. Nafas stops only when nightly usage, which every decision needs, is missing everywhere.

## Run it

Requires Python 3.10 or later.

```bash
pip install -r requirements.txt
python run.py                      # → http://127.0.0.1:5057
```

No API key is needed: without one, coach notes and answers come from the reviewed template. To use a model: Claude (default) via `ANTHROPIC_API_KEY` or `ant auth login`; Gemini with `NAFAS_LLM=gemini` plus `NAFAS_GEMINI_VERTEX_PROJECT` (Vertex AI through your gcloud login, no key stored) or `NAFAS_GEMINI_API_KEY`; `NAFAS_LLM=azure` for Azure OpenAI; `NAFAS_LLM=offline` forces the template. Any provider failure falls back to the template and says why (see `.env.example`).

| Command | What |
|---|---|
| `python -m pytest -q` | 86 tests |
| `python scripts/benchmark.py` | The labelled benchmark |
| `python scripts/run_demo.py` | The loop in a terminal, no browser |
| `python scripts/make_samples.py` | A synthetic sample file for every data source → `data/samples/` |
| `python scripts/generate_synthetic.py` | The declared synthetic personas and cohort → `data/synthetic/` |
| `python run.py --port 5058 --hub PATH/hub.db` | Personal mode (off by default): your own nights from a home hub store, read-only, refreshed on load |

## A three-minute demo for judges

1. **Layla, a new user.** Drag the timeline to **12-Aug-2026**: a large leak, a care-team flag for high residual AHI (fixed wording, no LLM) and comeback mode. The step is *Ask for a mask refit*, escalated because two self-fix steps didn't help (see **Weekly**).
2. Press **Play** from early September. On **15-Sep-2026** her ring sees sleep while CPAP sees none, so Nafas asks whether she's away. The banked count never dips.
3. **Omar, Arabic.** The page switches to right-to-left. His leak has crept up for two weeks → *Order a replacement*. In March 2025 or February 2026, Ramadan bedtimes show up as *Changed sleep schedule*.
4. **Ravi, shift worker, in a lapse.** Tap a different barrier and the plan changes. Type "chest pain" or "ما اقدر اتنفس" in the note and an emergency message replaces the coaching.
5. **Outcomes → Run measurement.** The Challenge 09 metrics (persistence, recovery after lapses, retention, residual AHI, equity with confidence intervals) on a 150-person synthetic cohort.
6. **Add your data**, one click from a phone or PC. Drop a ResMed SD card folder or zip, Garmin `.fit` or a Gadgetbridge export, a smart-ring export, Apple Health or Fitbit. Nafas reports what it found, what it skipped and any data warnings. No files to hand? **Try sample files**.
7. **Settings.** Goal, language, nudge time and quiet hours; AI wording and care-team sharing on or off. *Preview care-team summary* is refused until sharing is on.

## How this maps to Challenge 09

| Challenge 09 asks for | Where it is |
|---|---|
| Adaptive plans: small actions from goals, context and data | Barrier → one step (`barriers.py`, `actions.py`); per-person learning (`learning.py`) |
| Detect lapses, find barriers, adjust without blame, no reset to zero | `engine.py` detectors; `loop.py` comeback, re-plan, escalation; `engine.momentum` |
| Evidence-based support, rationale and limits visible | Technique, *why* and *limits* on every step; [BEHAVIOUR_CHANGE.md](docs/BEHAVIOUR_CHANGE.md) |
| Autonomy and inclusion; no manipulative or punitive use | Swap, skip, nudge limits, quiet hours, AI off, consent-gated sharing; English + Arabic; no employer or insurer view ([PRIVACY_SAFETY.md](docs/PRIVACY_SAFETY.md)) |
| Sustained outcome measurement | `outcomes.py`, Outcomes tab, [EVALUATION.md](docs/EVALUATION.md) |

## Documents

| | |
|---|---|
| [Benchmark](docs/BENCHMARK.md) | Labelled cases, safety-critical scores, history of failures and fixes |
| [Existing solutions](docs/EXISTING_SOLUTIONS.md) | myAir, AirView, DreamMapper, OSCAR, SleepHQ, habit apps: what each lacks, where Nafas differs |
| [Architecture](docs/ARCHITECTURE.md) | Components, API, data checks, integration with existing systems |
| [Data sources](docs/DATA_SOURCES.md) | Every source declared; what each upload format gives |
| [Privacy, safety, responsible AI](docs/PRIVACY_SAFETY.md) | Lines the app never crosses, and how they're enforced |
| [Behaviour-change design](docs/BEHAVIOUR_CHANGE.md) | The 29 actions and their techniques |
| [Evaluation](docs/EVALUATION.md) | Outcome measures and the proposed pilot |
| [Maturity](docs/MATURITY.md) | What existed before vs what was built for the challenge |
| [Assumptions and limitations](docs/ASSUMPTIONS_LIMITATIONS.md) | What we assume, depend on, and can't do yet |
| [Commercial path](docs/COMMERCIAL_PATH.md) | Who pays, pilot plan, risks |

## Layout

```
nafas/
  sources/     one-click ingest: safe unzip, detect, ResMed, Garmin FIT, Gadgetbridge, ring, Apple, Fitbit, merge
  quality.py   data checks: warnings, never crashes or silent drops
  ingest.py    ResMed STR.edf, CSV and JSON readers
  engine.py    detectors, thresholds, no-reset momentum
  barriers.py  barrier inference with evidence; self-report wins
  actions.py   29 actions (EN + AR), technique-tagged
  learning.py  per-person Thompson sampling
  loop.py      the morning-by-morning loop, replayable
  coach.py     fact brief → LLM wording → safety check → template fallback
  safety.py    output rules; emergency wording (EN + AR)
  qa.py        ask about your data: routed, grounded, checked
  benchmark.py labelled cases and scoring
  i18n.py      engine messages in English and Arabic
  weekly.py, outcomes.py, samples.py, synthetic.py, models.py
  llm/         claude (default) · azure · offline
  server.py    Flask API, session memory only
  static/      single-page UI: light and dark, English and Arabic, 375 px and up
scripts/       benchmark, run_demo, make_samples, generate_synthetic
data/          synthetic personas and cohort; sample files for every source
tests/         86 tests
```
