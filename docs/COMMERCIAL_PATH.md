# Commercial path to pilot

Draft for the team. Figures marked *(to validate)* are assumptions, not research.

## Who pays, and why

CPAP only works if it's used. Each party that loses when it isn't used is a possible buyer:

| Buyer | What they lose when adherence fails | What they would buy |
|---|---|---|
| **Sleep clinics / hospital sleep services** | Repeat visits, wasted titration, poor outcomes on their books | Adherence support for new starts; triage of who needs a call |
| **Equipment providers (DMEs)** | Returned or abandoned devices; mask resupply that never happens; adherence-linked reimbursement in some markets | Leak and wear detection that turns into resupply orders and refits; fewer support calls |
| **Payers / insurers** | Prescribed therapy that goes unused, with the health and cost consequences that follow *(size to validate)* | Better adherence across a population, **reported in aggregate only**. No individual penalties (see PRIVACY_SAFETY.md) |
| **Employers' wellbeing programmes** | Sleepiness, absence | Not a target. The punitive-use risk is too high |

**Start with B2B2C through a clinic or equipment provider.** They already hold the patient relationship and the device data feed, and they have a direct financial reason to care.

## Pilot plan (Abu Dhabi first)

| Step | What | Who | Time |
|---|---|---|---|
| 1 | Clinical advisor signs off thresholds, action library and wording | Advisor (to recruit) | 2–4 weeks |
| 2 | Arabic native review; add one more language (Urdu or Malayalam) based on the partner's patients | Reviewer | 2 weeks |
| 3 | Partner agreement with one sleep clinic or equipment provider; data feed (AirView or myAir export, or SD sync) | Team + partner | 4–8 weeks |
| 4 | DPIA, regulatory classification check, hosting in a UAE region | Team + advisor | in parallel |
| 5 | 90-day randomised pilot, n ≈ 200 (EVALUATION.md) | Partner clinic | 3–6 months |
| 6 | Readout: adherence at day 90, time to recover, refits triggered, clinician workload, equity | All | +1 month |

The challenge's "readiness assessment and potential pathway beyond the Challenge" would map onto steps 1–4.

## Pricing hypotheses *(to validate)*

- **Per active patient per month** to the clinic or equipment provider, priced below the cost of one avoided support call or one recovered resupply order a year.
- **Outcome-linked tier:** a share of the price tied to the adherence improvement measured against the comparison arm.
- **Free to the patient.** Patients never pay to be reminded to use a device they were already prescribed.

## Why this team, why now

- **Lived experience.** The team lead uses CPAP every night and has hit the everyday barriers in the library: leaks, worn cushions, Ramadan nights, travel, "felt fine" weeks.
- **Working code today.** A tested loop on synthetic data, an existing ResMed parser, and a model-agnostic design.
- **Regional fit.** Bilingual from day one, with Ramadan and shift work handled as first-class cases.

## Risks

| Risk | Mitigation |
|---|---|
| No clinician on the team | Recruit a clinical advisor to review thresholds and emergency wording before any pilot |
| Device data access depends on manufacturers | SD-card path works today; partner feeds via the clinic or equipment provider |
| Regulatory reclassification as a medical device | Keep intended use to adherence support; never change therapy; clinical patterns go to clinicians |
| LLM cost or availability | Template fallback is complete; LLM is optional |
| Adherence apps exist from manufacturers | Ours is brand-neutral, works across devices, is bilingual, and learns what works per person with recovery built in, not just a usage score |
