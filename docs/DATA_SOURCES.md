# Data sources (declared)

The organisers provide no data. The rules ask teams to "use only data you have the legal right to use, declare every data source, and avoid personal data you do not need". This page lists every source.

## 1. Synthetic demo data: the only data in the submission

| Item | Detail |
|---|---|
| What | 3 fictional personas (Layla 121 nights, Omar 790, Ravi 150) and a 150-person cohort of 180 nights each |
| How | `nafas/synthetic.py`, fixed seeds (101, 202, 303; cohort seed 7). `python scripts/generate_synthetic.py` writes identical files every time |
| Where | `data/synthetic/`: `*_nights.csv`, `*_checkins.json`, `cohort_profiles.json`, `MANIFEST.json` |
| Fields per night | date, usage minutes, residual AHI, 95th-percentile leak (L/min), 95th-percentile pressure (cmH2O), mask sessions, first session start time, optional wearable sleep minutes |
| Personal data | None. Names are fictional and marked "(fictional)" in the app. No device serials, dates of birth or free text from real people |
| Licence | Ours; free to use for evaluation |

### How the synthetic shape was set

Parameter ranges were chosen to look like real effective therapy:

- usage around 7–8 h a night on good nights;
- residual AHI log-normal around 1 event/hour (roughly 0.6–1.9 across most nights);
- 95th-percentile pressure 10–15 cmH2O;
- leak at 0 on about half of nights, otherwise usually under 16 L/min, sometimes over 24.

These ranges are consistent with the team lead's own long-term therapy summary (about 790 nights). Only aggregate ranges such as deciles informed the parameters. No night, date or identifier from any real person is copied, embedded or shipped, and the test suite fails if the code or data mentions the real-data folders (`tests/test_ingest_server.py::test_no_real_patient_data_is_referenced`).

The personas' life events are scripted to exercise the loop: a rocky start, a leak spell with raised AHI, travel, Ramadan bedtime shifts (dates follow the 2025 and 2026 Ramadan calendars), Eid travel, a flu week, a cushion wearing out, shift work, and "felt fine without it". Because they are scripted, they show the loop working. They are **not** evidence that it changes behaviour.

The cohort mixes six archetypes (steady 30%, rocky start 15%, fader 20%, repeated lapser 15%, shift worker 10%, drop-out 10%), so persistence lands well below 100%. Language, age band and shift-work attributes are assigned at random, apart from shift work, so that the equity breakdown has something to measure.

## 2. Data a user may upload (optional, not part of the submission)

| Format | Parser | Kept |
|---|---|---|
| ResMed AirSense / AirCurve `STR.edf` (SD card) | `ingest.read_resmed_str`, from the original Sleep IQ build | Nightly numbers only; serial and patient fields are not read |
| CSV (template from the app) | `ingest.read_csv` | Columns in `ingest.CSV_COLUMNS`; dates ISO or DD-Mon-YYYY |
| JSON (`{"nights": [...]}` or Sleep IQ v1 export) | `ingest.read_json` | Same fields |

Uploads are parsed in memory for that browser session only. They are never written to disk and are deleted by *Delete everything* or a server restart.

## 3. Reference knowledge used in the rules (no data, cited)

| Rule | Source |
|---|---|
| 4 h a night as the adherence bar; 70% of nights | Common adherence definition (e.g. US CMS: ≥4 h on 70% of nights in 30 consecutive days within the first 90 days) |
| Large leak above 24 L/min (95th percentile) | ResMed device "large leak" threshold, as used in myAir and AirView reports |
| Residual AHI 10 or more on several nights → clinician review | Conservative choice by the team; to be confirmed by the clinical advisor |
| Behaviour-change technique labels | BCT Taxonomy v1 (Michie et al., 2013) |
| CPAP non-adherence range 29–83% | Weaver TE, Grunstein RR. *Proc Am Thorac Soc* 2008;5:173–178 |

## 4. Data we do not use

- No data from the organisers, partners or any health system.
- No real patient's data, including the team lead's own CPAP exports.
- No scraped forums or social media.
- The legacy `cpap_data.json` from the original Sleep IQ repository holds real data. It is not copied into this project.
