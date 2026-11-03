# Assumptions, dependencies and limitations

The submission asks for "a clear statement of your assumptions, dependencies, and limitations". Here it is.

## Assumptions

1. **The user is already diagnosed and prescribed CPAP.** The app supports adherence; it doesn't screen or diagnose.
2. **Nightly summary data is available**: usage, residual AHI, 95th-percentile leak and pressure, mask sessions. ResMed SD cards and cloud reports provide this. Other brands may provide less; the engine copes with missing AHI, leak or pressure but loses those detectors.
3. **4 h a night is a sensible default goal.** The person can raise it (Omar uses 6 h). Clinicians may set a different target.
4. **No record for a night means the machine wasn't used.** That's true for SD-card data; with cloud sync, a sync gap could look like a lapse. A pilot needs a "no data" state.
5. **Three nights is enough to judge a self-fix step, and seven for a care-team step.** It's a short window chosen for responsiveness, and it is noisy (see EVALUATION.md).
6. **A large leak above 24 L/min** follows ResMed's definition. Other manufacturers report leak differently and would need their own line.
7. **Wearable sleep, when present, is roughly right** about whether the person slept. It's used only to ask "were you away?", never as a clinical measure.
8. **Ramadan, shift work and travel are common reasons for lapses in the target population** (Abu Dhabi residents). They are first-class barriers.

## Dependencies

| Dependency | Needed for | Without it |
|---|---|---|
| Python 3.10+, Flask | Running the app | — |
| `anthropic` SDK and a Claude credential | AI-worded notes (default) | Reviewed template is used; everything else works |
| `openai` SDK and an Azure OpenAI deployment | Optional Azure provider | Same as above |
| Google Fonts (Inter, Outfit, Noto Sans Arabic) | Typography | System fonts |
| A browser | UI | `scripts/run_demo.py` shows the loop in a terminal |

No database, queue or cloud service is required to run the prototype.

## Limitations

**Clinical**

- Thresholds and the action library were written by the team (one CPAP patient plus engineering) and have **not yet been reviewed by a sleep clinician**. Getting that review is the top open item.
- The residual-AHI flag is a conservative heuristic, not a clinical rule.
- No symptom data (sleepiness, mood). Benefit is inferred from use alone.

**Evidence**

- **No real-user data has been run through the loop.** Persona stories are scripted, and the cohort is synthetic and independent of the app's steps. Nothing here shows effectiveness; that needs the pilot in EVALUATION.md.
- "Steps that helped" can't tell an effect from regression to the mean.

**Language and inclusion**

- Arabic action and UI text is a **first draft** and needs native review with clinical vocabulary. Engine evidence strings ("No CPAP use for the last 3 nights") are English only in this prototype.
- Two languages so far. Urdu, Hindi, Malayalam and Tagalog matter in the UAE and are not done.
- No formal accessibility audit yet; the UI uses semantic HTML, keyboard focus states, 40 px tap targets and reduced-motion support.

**Technical**

- Session-only memory: nothing persists across server restarts (on purpose for the demo).
- The loop replays from the first night on each request. That's fine to a few thousand nights per person; production would cache the nightly state.
- The EDF reader is tested on a synthetic STR.edf built to the ResMed layout and checked on one real AirSense 10 card copy, not on every device generation (AirSense 11 is untested).
- The Garmin FIT, Gadgetbridge, smart-ring, Apple Health and Fitbit parsers are tested on **synthetic** files only; no real exports were available during the build. Gadgetbridge's database schema changes between versions, so that reader is best effort. Garmin's newer sleep files may use message numbers beyond the public FIT profile; fields are matched by number to reduce that risk.
- Wearable values (sleep minutes, resting HR, HRV) are consumer estimates. They're used only to ask "were you away?" and shown for context, never as clinical measures.
- Emergency detection is phrase matching (English and Arabic). It scores 100% sensitivity on 47 phrasings, but a held-out batch first scored 8/15 (see BENCHMARK.md): unseen wording can still slip through. It is a safety net that stops coaching, not a triage tool.
- Units are never guessed: hours typed into a minutes column are flagged, not converted, so those nights read as short until the column is renamed. This is deliberate; a wrong guess could hide a lapse.
- A browser folder picker isn't available on phones; there, people pick files or a zip. Very large SD cards (over 64 MB) need zipping or picking `STR.edf` alone; the browser already leaves out per-breath DATALOG files.
- The Claude provider was exercised up to authentication; no live key was used during the build, so the coach prompt hasn't been tuned on real model output yet.
- Nudges are planned, not sent: no push, SMS or WhatsApp integration in the prototype.
