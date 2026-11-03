# Privacy, safety and responsible AI

## Safety boundaries (enforced in code)

| Line we don't cross | How it's enforced | Test |
|---|---|---|
| No therapy changes. The app never suggests a pressure value or a pressure change | Action library rule; `safety.FORBIDDEN["pressure_change"]` rejects any LLM draft that does | `test_action_library_passes_the_coach_safety_rules`, `test_safety_rules_catch_the_things_we_never_say` |
| No diagnosis and no medication advice | `diagnosis` and `medication` rules | same |
| Never tells anyone to stop therapy | `stop_therapy` rule | same |
| No blame | `blame` rule rejects *fail*, *lazy*, *should have*, *disappointing*… | same |
| High residual AHI goes to a human | `engine.detect_clinical` → fixed care-team wording, never sent through the LLM | `test_state_and_loop_endpoints` |
| Emergencies are not coached | Notes mentioning chest pain, trouble breathing, fainting or self-harm (English and Arabic) show an emergency message with the UAE number 998 | `test_crisis_notes_get_an_emergency_message` |
| The LLM can't decide anything | It receives a fact brief and returns text. Detection, barrier, step and escalation all happen before it is called | `test_coach_*` |
| Q&A can't make clinical calls | Emergency and clinical-decision questions (EN + AR) are routed before any model call to fixed answers; the model sees only a numbers-only fact pack; answers with pressure advice, diagnosis, medication, blame, links, invented numbers or a cut-off are replaced by a data summary | `tests/test_qa.py`; benchmark suite `qa` (31/31); live `scripts/qa_eval.py` (11/11) |
| No hidden failure | Any LLM error, refusal or failed check shows the reviewed template, with the reason | `test_coach_falls_back_*` |

## Responsible AI

- **Minimal input.** The brief sent to the LLM holds a first name, a few numbers (hours, banked nights, run, 30-night adherence), the situation label, the chosen step and up to two evidence sentences from the rules engine. It never holds dates of birth, device serials, uploads or the person's free-text notes.
- **Provider choice.** Claude is the default, Azure OpenAI is supported, and *offline* uses no model. Swapping is one environment variable. The person can turn AI wording off in Settings.
- **Explainability.** Every detection and barrier shows the evidence that produced it. Every step shows its technique, rationale and limits. The learner shows how often each step helped.
- **Determinism.** Same inputs, same plan (`test_replay_is_deterministic`). Disputes can be replayed.
- **Bias and equity.** The outcome pipeline breaks results down by language, age band and shift work and reports the widest persistence gap, counting only groups of 20 or more. The action library is bilingual from day one, and shift work and Ramadan schedules are first-class barriers, not edge cases.

## Privacy by design

| Principle | In the prototype | In a pilot |
|---|---|---|
| Data minimisation | Nightly summary numbers only. Never read: ResMed `Identification.*` and `SETTINGS/` (serial), FIT `file_id` (watch serial), Apple `<Me>` (birth date, sex), Gadgetbridge device and user tables, ring device addresses. Tested with planted fake identifiers | Same; no raw waveforms |
| Storage | None. Per-session memory, cleared by *Delete everything* or a restart | Encrypted at rest in a UAE region; retention set with the pilot partner |
| Consent | Care-team summary refused (403) until the person turns sharing on; a preview is shown first | Explicit, revocable, purpose-specific consent recorded |
| Control | Goal, language, nudge time, quiet hours, nudges on or off, AI wording on or off, swap or skip any step | Plus data export and account deletion |
| Session security | HttpOnly, SameSite=Lax session cookie; 64 MB upload cap; zips read in memory with size, ratio, nesting and path guards; coach rate limit | Plus SSO via the partner, audit log, penetration test |

### No punitive use

Challenge 09 warns against "punitive use by employers, insurers or others". In this design:

- there is **no employer, insurer or payer view**, and none is planned;
- the care-team summary is the only output that leaves the person, and only with their consent;
- adherence data is used to help the person, never to rank or penalise them. Any partner contract for a pilot should say so in writing.

## Regulatory position (to confirm with the clinical advisor)

- **Intended use:** behavioural support for people already prescribed CPAP. It doesn't diagnose, doesn't change therapy, and routes clinical patterns to clinicians. We expect this to fall under wellness and adherence support rather than a diagnostic medical device, but **this needs a formal classification check** for the UAE and any other launch market before real-user exposure.
- **UAE data rules to plan for:** Federal Decree-Law 45/2021 (personal data protection), Federal Law 2/2019 (use of ICT in health fields, including keeping health data in the country), and Abu Dhabi Department of Health requirements for digital health and AI. The challenge terms also cite India's IT Act for data security.
- **Not yet done:** DPIA, clinical safety case, clinical sign-off of thresholds and action library, accessibility audit, native-speaker review of the Arabic.
