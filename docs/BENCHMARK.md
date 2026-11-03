# Benchmark

The challenge webinar (Hack2Skill with the Department of Health Abu Dhabi, 03-Nov-2026) gave clear advice:
- build a labelled case set and record expected vs actual for every case;
- make about half the cases hard: missing fields, wrong values, bad inputs;
- score the safety-critical part on its own and claim a number;
- name the module that failed.

This is that benchmark. Run it with:

```bash
python scripts/benchmark.py        # prints scores, writes docs/BENCHMARK_RESULTS.md (every case, every failure)
```

## Headline (03-Nov-2026)

| Suite | Safety-critical | Cases (hard) | Result |
|---|---|---|---|
| Emergency wording in a free-text note, English + Arabic | **yes** | 77 (61) | **Sensitivity 100%** (47/47 emergency phrasings caught) · specificity 96.7% (29/30 near-misses left alone) |
| Care-team flag: high residual AHI | **yes** | 12 (6) | **100%** |
| Detectors: lapse, decline, large leak, leak creep | | 26 (16) | 100% |
| Barrier inference, top-1 | | 14 (6) | 100% |
| Ask-your-data guardrails: routing (emergency / care team / answer) + output checks on model answers | **yes** | 31 (21) | **100%** |
| **All** | | **160 (110)** | **159 / 160** |

The one failure is accepted on purpose. "Watched a film about someone who fainted" triggers the emergency notice. For emergencies we prefer a needless notice to a missed one.

A test (`tests/test_benchmark_quality.py`) fails the build if emergency sensitivity, the care-team flag or the Q&A guardrails drop below 100%, or if any case crashes.

**Q&A, live with a real model.** `python scripts/qa_eval.py` asks 14 fixed questions (English and Arabic) about the fictional personas. On 03-Nov-2026 with Gemini 3.5 Flash on Vertex AI: **11/11 model answers passed every output check**; the 3 emergency, stop-therapy and prompt-injection questions were answered by fixed text without calling the model. Earlier runs on the same day caught two problems now fixed:
- the coach's "no cmH2O" rule wrongly blocked answers that read back a real pressure value (Q&A now blocks pressure *advice* only, and the grounding check proves values are real);
- Gemini sometimes ran out of tokens mid-answer (cut-off answers are now rejected rather than shown, and the budget was raised).

The Q&A suite was written after the guardrails were built, so it is a development set; the live run is the independent check. Results: [QA_EVAL_RESULTS.md](QA_EVAL_RESULTS.md).

## How it's built

- **Every case states expected vs actual.** For example, "3 of 7 nights AHI ≥ 10 → flag", "AHI 999 on 3 nights → no flag, and the data check warns".
- **Hard cases** (89 of 129) include:
  - missing fields; impossible values (AHI 999, leak 9999, a 2,000-minute night, AHI −1);
  - hours typed into a minutes column; L/s typed into an L/min column;
  - duplicate nights; a 10-night gap in a card copy; data from two sources disagreeing;
  - unused nights carrying stale readings; isolated missed nights vs real trips; stale self-reports;
  - negation ("no chest pain"); third-party wording ("my partner says I stop breathing");
  - near-miss words ("chest strap", "breathing tube", "a faint hiss", "this mask is killing me");
  - Arabic in Modern Standard and Gulf/Levantine forms, with and without diacritics and hamza.
- **The same path as a real upload.** Data cases run through the same data checks an upload gets (`quality.clean_cpap` → gap filling → detectors), so each failure is pinned to a module: `safety`, `quality`, `engine`, `barriers`, or `crash`.

## History: what the benchmark caught

We report the runs, not just the final score.

1. **First run, 03-Nov-2026: 69 / 103.** The benchmark found real problems:
   - **Unit guessing was unsafe.** The data checks converted "looks like hours" and "looks like L/s" on a guess. A genuinely low leak (2 L/min) was multiplied into a fake 120 L/min leak, and the wrong guess could also make poor use look like good use. **Fix:** Nafas never converts on a guess. It flags the suspicion (`usage_unit_suspect`, `leak_unit_suspect`) and converts only explicitly named columns (`usage_hours`, `leak95_lps`).
   - **Emergency wording missed 17 phrasings,** mostly Arabic variants: dialect ("ما اقدر اتنفس"), spellings without hamza ("اغمي علي"), "short of breath", "blacked out", "tightness in my chest". It also raised 3 false alarms ("no chest pain", "a faint hissing noise", "لا يوجد ألم في الصدر"). **Fix:** text is normalised first (diacritics stripped, alef/ya/ta-marbuta forms unified), the phrase list is wider, and simple negation is handled.
   - **Leak creep used reading counts, not calendar days,** so missing leak values shifted its windows. **Fix:** calendar windows.
   - **An impossible nightly use (2,000 min) dropped the night** and hid a lapse. **Fix:** it counts as "not used" (the conservative reading) and is reported.
2. **Held-out run.** We wrote 26 new emergency cases after those fixes and ran them once, untouched. Sensitivity was **8/15**: phrasings like "I can hardly breathe", "can't catch my breath", "صدري يؤلمني" and "بدي أنتحر" were missed. **Lesson: keyword lists generalise poorly; a high score on your own cases overstates real coverage.** The misses were fixed and the held-out cases joined the set (marked `crisis-ho-*`).
3. **Now: 128 / 129.**

## Limits of this benchmark

- The cases are synthetic and written by the team. A real evaluation needs cases written by clinicians and patients who didn't build the rules. The held-out run shows why.
- Emergency detection is phrase matching. In a pilot it should be backed by a reviewed classifier and by human follow-up of every triggered note. Its job is to stop coaching and show the emergency number, never to triage.
- Barrier inference is scored top-1 against the barrier we scripted. Real barriers overlap; a pilot should score "was the person's own answer in the top 2?".
- The thresholds being tested (4 h, 24 L/min, AHI 10) are themselves awaiting clinical review.
