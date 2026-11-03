# Existing solutions, and where Nafas differs

Researched 03-Nov-2026 from vendor pages, app-store listings and trade press (sources at the end). Vendor claims are reported as vendor claims.

## Summary

| Tool | Who it's for | What it does well | What it lacks for *sustaining* adherence |
|---|---|---|---|
| **ResMed myAir** | Patients on connected ResMed devices | A daily 0–100 score from usage, mask seal, events per hour and mask on/off. Coaching tips, mask-seal tips, how-to videos, shareable reports. On AirSense 11: guided set-up and mask fitting. Apple Health / Health Connect integration [1–3] | A per-night score, not a recovery plan: nothing turns a run of bad nights into "here is the likely barrier, try this one thing". No visible per-person learning of what works. ResMed devices only; several features need AirSense 11 [1, 2] |
| **ResMed AirView** | Clinicians and equipment providers | Cloud compliance reports, remote settings changes, Action Groups that sort patients by adherence status or a specific therapy problem. Used at very large scale (over 4 million connected patients reported) [4–7] | Clinician-side. It finds the at-risk patient, but someone still has to call. The patient sees nothing between calls. ResMed only |
| **Philips DreamMapper** | Patients on Philips devices | Daily feedback on progress, guides when progress lags, goals, reminders (e.g. filters), videos [8, 9] | Philips only. Philips stopped selling new sleep-therapy devices in the US from January 2024 under an FDA consent decree that followed the 2021 foam recall [10, 11] |
| **OSCAR** (open source) | Technically minded patients | Free desktop software (GPLv3) that reads SD cards from many brands down to breath-by-breath detail [12, 13] | Analysis, not behaviour change: no lapse detection, no coaching, no recovery. Needs a computer and some expertise |
| **SleepHQ** | Patients, with sharing to clinicians | Cloud upload (including Wi-Fi SD uploaders), reports, share links and clinician accounts; Pro adds a sleep journal, AI-insight PDF reports and an API [14, 15] | A reporting platform. Free tier shows only the last 30 days; the richer features are paid. No behaviour loop |
| **Generic habit apps** (streak trackers) | Anyone | Reminders, self-tracking, streaks | Know nothing about therapy data, leaks or AHI. Have no clinical guardrails. Usually built around a streak that resets on one miss, the all-or-nothing pattern linked to the "what-the-hell" effect, where one lapse turns into giving up [16, 17] |

## Where Nafas is different

1. **From "how did you sleep" to "what got in the way".** Nafas infers a likely barrier from the data and shows its evidence: leak with short nights, a slow leak drift, mask off 3+ times, a watch that saw sleep while CPAP saw none, a bedtime that moved 3 hours. The person can correct it with one tap.
2. **One small step, then learning.** One technique-tagged action at a time, judged on the next three nights, with Thompson sampling per person. Two misses on the same barrier move to a care-team step, so the app doesn't repeat itself.
3. **Progress that survives a bad week.** Banked nights never go down, one short night a week doesn't break the run, and a lapse opens a one-hour comeback goal instead of a reset.
4. **Brand-neutral input.** ResMed SD card, Garmin, Gadgetbridge, a smart ring, Apple Health, Fitbit and CSV, in one click from a phone or PC. Wearable sleep is what tells "away" apart from "skipped".
5. **Built for the region.** English and Arabic (right-to-left) from day one; Ramadan bedtimes, Eid travel and shift work are first-class barriers.
6. **Safety you can measure.** Rules decide and the language model only words the note. Notes describing an emergency stop coaching, with emergency-wording sensitivity of 100% on 47 cases (see [BENCHMARK.md](BENCHMARK.md)). Clinical patterns go to the care team in fixed wording.
7. **Outcome measurement built in.** Persistence, recovery after lapses, retention, residual AHI and equity gaps with confidence intervals (see [EVALUATION.md](EVALUATION.md)).

## Where the others are ahead (and how we fit)

- **Evidence and scale.** myAir and AirView have published, vendor-sponsored real-world adherence data across very large populations [6, 7]. Nafas has none yet; that's the pilot's job.
- **Direct device connection.** myAir, DreamMapper and SleepHQ's uploaders get data with no effort from the patient. Nafas needs an upload today; the pilot path is a partner feed (see ARCHITECTURE.md → Integration).
- **Clinical workflow.** AirView already sits in clinic and equipment-provider workflows. Nafas should **complement** it, not replace it: AirView finds the patient at risk, and Nafas gives that patient a reason, a step and a comeback between calls. The consent-gated care-team summary is the hand-off.

## Sources

1. ResMed UK, *myAir app*: https://www.resmed.co.uk/products/therapy-apps/myair-app/
2. Apple App Store, *myAir by ResMed* (US): https://apps.apple.com/us/app/-/id1109518523
3. Apple App Store, *myAir by ResMed EMEA*: https://apps.apple.com/lu/app/id1485334159
4. ResMed press release, *AirView Action Groups*: https://investor.resmed.com/news-events/press-releases/detail/190/resmed-launches-airview-action-groups-the-ultimate-time-saver-for-home-medical-equipment-providers
5. ResMed Asia-Pacific, *AirView*: https://ap.resmed.com/knowledge/airview
6. Sleep Review, *Large patient study shows digital self-monitoring and clinical management tools improve patients' adherence* (2016): https://sleepreviewmag.com/2016/10/large-patient-study-shows-digital-self-monitoring-clinical-management-tools-improve-patients-adherence/
7. Sleep Review, *Remote monitoring, automated resupply improve adherence to PAP therapy* (ResMed studies): https://sleepreviewmag.com/sleep-treatments/therapy-devices/cpap-pap-devices/remote-monitoring-automated-resupply-improve-adherence-pap-therapy-find-resmed-studies/
8. Philips (UAE), *DreamMapper*: https://www.philips.ae/c-e/hs/sleep-apnea-therapy/dream-mapper
9. Apple App Store, *DreamMapper*: https://apps.apple.com/us/app/sleepmapper/id530569351
10. ProPublica, *Philips agrees to stop selling sleep apnea machines in US* (2024): https://propublica.org/article/philips-agrees-to-stop-selling-sleep-apnea-machines-in-us
11. Healio, *Philips Respironics devices no longer being sold in US* (29-Jan-2024): https://cm.healio.com/news/pulmonology/20240129/philips-respironics-devices-no-longer-being-sold-in-us
12. OSCAR project page: https://www.sleepfiles.com/OSCAR/
13. OSCAR source (OSCAR Team, GitLab): https://gitlab.com/CPAPreporter/oscar-code
14. SleepHQ: https://www.sleephq.com/
15. SleepHQ FAQ: https://www.sleephq.com/faq
16. *The dark side of streaking: examining the backfire potential of run streaking in recreational runners who broke a long-term streak* (medRxiv preprint, 2024): https://www.medrxiv.org/content/10.1101/2024.12.26.24319676.full.pdf
17. EFPSA, *Research in a Nutshell* (the "what-the-hell" effect): https://more.efpsa.org/rpblog/?p=1172
