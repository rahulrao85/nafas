# Evaluation and outcome measures

Challenge 09 asks solutions to "evaluate persistence over a meaningful period, recovery after lapses, change in the target behaviour or biomarker, retention and equitable benefit". The pipeline in `nafas/outcomes.py` computes each of these for one person and for a cohort.

## Measures

| Challenge asks | Measure | Definition |
|---|---|---|
| Persistence | Persisting | At least 70% of the last 30 nights at goal (4 h by default) |
| | Adherence, first vs last 30 nights | % of nights at goal |
| Recovery after lapses | Lapses per person; recovery rate | Lapse = 2 nights off, or 3 of 5 under goal; recovered = 3 of 4 nights at goal again |
| | Median days to recover | Lapse start → recovered |
| Change in behaviour | Hours a night, first vs last 30 | Mean usage |
| Change in biomarker | Residual AHI, first vs last 30 | Mean AHI on used nights. On therapy AHI is mostly flat; it matters as a safety signal and as a proxy where mask leak drives events up |
| Retention | Retained | Used on at least 4 of the last 28 nights (still engaged, even if not at goal) |
| Did the steps help? | Steps that helped | Share of judged steps followed by 2 of 3 good nights (leak steps: 2 of 3 nights under the leak line) |
| Equitable benefit | Each of the above by language, age band and shift work, with 95% Wilson intervals; widest persistence gap | Only groups of 20 or more count. A gap is flagged when the intervals don't overlap |

## What the synthetic cohort shows (and doesn't)

150 synthetic people, 180 nights each, seed 7. Run it from **Outcomes → Run measurement** or `GET /api/cohort`.

| Measure | Value |
|---|---|
| Persisting at six months | 77.3% (95% CI 70.0–83.3) |
| Retained | 88.0% |
| Adherence, first → last 30 nights | 82.2% → 72.0% |
| Lapses per person | 2.7, of which 88.6% recovered |
| Median days to recover | 7 |
| Residual AHI, first → last 30 | 1.2 → 1.1 |
| Steps judged as helping | 67.7% |

**It doesn't show that the loop works.** The synthetic nights are generated independently of the app's steps, so "helped" here means regression to the mean plus scripted recoveries. That is the point of the exercise: it shows what a naive before-and-after metric would credit to an intervention that did nothing.

**It does show the pipeline is honest about equity.** Language and age band are assigned at random, yet the age-band breakdown shows a 32.7-point persistence gap with non-overlapping intervals. With five groups, one chance difference like that is expected. A real evaluation must pre-register its comparisons and correct for multiple testing. The pipeline already reports intervals so nobody reads a raw gap as a finding.

## Pilot evaluation design (proposed)

- **Population:** adults starting or restarting CPAP through one Abu Dhabi sleep clinic or equipment provider, n ≈ 200, English or Arabic.
- **Design:** two arms, randomised at the individual level. Usual care (device app plus clinic follow-up) vs usual care plus Nafas. 90 days, with follow-up to 180.
- **Primary outcome:** adherence by the standard definition at day 90 (at least 4 h on 70% of nights in a 30-night window).
- **Secondary outcomes:** mean nightly use; lapses and time to recover; retention at day 180; residual AHI; leak nights; mask refits triggered; clinician contacts triggered (a safety and workload measure); Epworth Sleepiness Scale; user trust (short survey).
- **Equity:** pre-registered subgroups (language, age band, shift work, new vs experienced user), with intervals.
- **Safety:** every care-team flag reviewed; every LLM note logged with its safety-check result; complaints and adverse events reported.
- **Also judged:** whether the per-person learner beats a fixed rotation of actions (an internal A/B test once the pilot is large enough).
