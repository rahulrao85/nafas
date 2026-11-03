# Maturity: what existed before vs what was built for the challenge

The FAQ allows existing products, provided the team states "how mature your solution is now and what you will build or improve during the Challenge".

## Before the challenge: Sleep IQ v1 (early 2026)

Built for the Microsoft Agents League (Reasoning Agents track):

- a **ResMed `STR.edf` parser**, plus Apple Health XML, Fitbit and generic CSV readers;
- a **descriptive analytics engine**: AHI severity, trend (first third vs last third), compliance percentage, leak and pressure summaries;
- an **AI Q&A agent** on Azure AI Foundry (with an OpenRouter fallback) that answers questions about the data with citations to sleep guidelines;
- a printable doctor summary.

v1 *explained* the data. It had no behaviour loop: no lapse detection, no barriers, no actions, no learning, no recovery logic, no outcome measurement. It was tied to Azure, and its demo dataset was a real person's data.

## Built for the challenge: Nafas (from 03-Nov-2026)

Nafas is a separate project with its own code base. From Sleep IQ v1 it takes the idea (helping CPAP users with their own therapy data) and the approach to reading ResMed `STR.edf` files. Everything else is new.

| Area | Status |
|---|---|
| Adherence engine: lapse, decline, large leak, leak creep, clinical flag, with evidence | Built, tested |
| No-reset momentum: banked nights, forgiving run, comebacks, comeback goal | Built, tested |
| Barrier inference (13 barriers, 7 from data) with self-report override | Built, tested |
| Action library: 29 BCT-tagged actions, English and Arabic, rationale and limits | Built (clinical and Arabic review pending) |
| Per-person learning (Thompson sampling) and escalation to care team | Built, tested |
| Replayable morning loop: deterministic, auditable | Built, tested |
| Nudge planner: one a day, quiet hours, frequency drops when ignored | Built, tested |
| LLM made swappable: Claude (default), Azure OpenAI, offline template; output safety checks | Built, tested (Claude path checked up to authentication; no live key used in the build) |
| Crisis-note detection (English and Arabic) | Built, tested |
| Weekly adherence view, 90-night chart | Built |
| Outcome pipeline with equity breakdown and confidence intervals | Built, tested |
| Synthetic personas and cohort, with real data barred by a test | Built, tested |
| UI: design tokens, light and dark, English and Arabic RTL, 375 px | Built, checked by hand in a browser |
| Consent-gated care-team summary; session-only storage; delete everything | Built, tested |
| ResMed `STR.edf` reader, carried over from v1 (identifiers dropped) | Carried over, tested on a synthetic EDF |

Code reused from v1: the EDF parsing approach only. Everything else in the `nafas` package is new.

## Still to do before 20-Nov-2026 (if time allows)

- Clinical advisor reviews thresholds, action library and wording.
- Native Arabic review of the action library and UI strings.
- A live Claude run with a key to tune the coach prompt; record example outputs and safety-check pass rates.
- Accessibility pass: screen reader, keyboard, contrast.
- Demo video (7 minutes, the length used in the finals format).

## Beyond the challenge (pilot readiness)

Partner data feed (ResMed AirView or myAir, or Philips Care Orchestrator); push and WhatsApp channels; accounts and persistent encrypted storage in a UAE region; a clinician dashboard limited to consented summaries; DPIA and clinical safety case; regulatory classification check. See [COMMERCIAL_PATH.md](COMMERCIAL_PATH.md).
