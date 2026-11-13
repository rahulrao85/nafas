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
| Licence | Ours; released with the code under MIT (see LICENSE) |

### How the synthetic shape was set

The personas and the cohort are synthetic, generated with the fixed seeds above. Parameter ranges were chosen to look like effective therapy:

- usage around 7–8 h a night on good nights;
- residual AHI log-normal around 1 event/hour (roughly 0.6–1.9 across most nights);
- 95th-percentile pressure 10–15 cmH2O;
- leak at 0 on about half of nights, otherwise usually under 16 L/min, sometimes over 24.

**Where these ranges come from.** They were sanity-checked against published reference thresholds (§3) and, at aggregate level only, against the team lead's own long-term experience of CPAP therapy. No night, date, identifier or value from any real person, the team lead included, is copied, embedded or shipped. The test suite fails if the code or data mentions the real-data folders or carries a real identifier (`tests/test_ingest_server.py::test_no_real_patient_data_is_referenced`).

The personas' life events are scripted to exercise the loop: a rocky start, a leak spell with raised AHI, travel, Ramadan bedtime shifts (dates follow the 2025 and 2026 Ramadan calendars), Eid travel, a flu week, a cushion wearing out, shift work, and "felt fine without it". Because they are scripted, they show the loop working. They are **not** evidence that it changes behaviour.

The cohort mixes six archetypes (steady 30%, rocky start 15%, fader 20%, repeated lapser 15%, shift worker 10%, drop-out 10%), so persistence lands well below 100%. Language, age band and shift-work attributes are assigned at random, apart from shift work, so that the equity breakdown has something to measure.

## 2. Data a user may add: one click, any mix (optional, not part of the submission)

One **Add your data** button takes files, a whole folder (desktop) or zips, from a phone or a PC, all at once. Each file is detected, parsed and merged, and the app shows what it found (source, nights, date range) and what it skipped and why.

| Source | What you give it | What Nafas reads | Verified on |
|---|---|---|---|
| **ResMed SD card** (AirSense / AirCurve) | `STR.edf`, the whole card folder, or a zip of it | Per night: usage, residual AHI, 95th-percentile leak (L/s → L/min) and pressure, mask sessions, first mask-on time. `DATALOG` (per-breath detail) is skipped: the nightly summary is all the loop needs. `Identification.*` and `SETTINGS/` (they hold the device serial) are skipped on purpose | Synthetic card **and** a real card copy (read on the team's PC only, never shared; matched an independent SD-card parser night for night) |
| **Garmin watch** | `.fit` sleep files (one per night), any folder or zip of them | Sleep minutes from `sleep_level` stages (light, deep, REM), overnight HRV (`hrv_status_summary`), resting HR (`monitoring_hr_data`). Device UTC offset from `timestamp_correlation`. The `file_id` message (watch serial) is never read | Synthetic FIT files built to the FIT 2.0 format (with CRCs) |
| **Gadgetbridge** (Garmin without Garmin's cloud) | The "Export zip" from Gadgetbridge | `*SLEEP_STAGE_SAMPLE` and `*HRV_SUMMARY_SAMPLE` tables from its database, plus any `.fit` files in the zip. Device and user tables are not read | Synthetic database only: Gadgetbridge's schema varies by version, so treat this as best effort |
| **Smart ring** (Collector app) | Its export: `{"documents": [...]}` JSON (Collector ingest contract v1) | `sleep.segment` stages → minutes asleep; `vitals.hr` (lowest overnight) and `vitals.hrv` (mean) inside the sleep window. Device addresses are not kept | Synthetic export only |
| **Apple Health** | `export.zip` (or `export.xml`) from the Health app | Asleep minutes per night (largest single source, so iPhone + Watch aren't double-counted), HRV (SDNN), resting HR. Streamed, so large exports work. `<Me>` (birth date, sex) and `export_cda.xml` are skipped | Synthetic export only |
| **Fitbit / Google Takeout** | `sleep-YYYY-MM-DD.json` | `minutesAsleep` per sleep log, by the night it started | Synthetic export only |
| **CSV / JSON** | The app's CSV template, or `{"nights": [...]}` | All `Night` fields, including optional wearable columns | Synthetic |

**How they merge.** CPAP nights come from the card, CSV or JSON. Wearable values attach to the CPAP night they belong to; a night runs noon to noon, so 01:30 sleep counts for the evening before. When several wearables cover a night: Garmin FIT, then Gadgetbridge, then ring, then Apple, then Fitbit. Values given explicitly in a CSV win over all of them. Wearable nights outside the CPAP dates are dropped and reported. If no CPAP data comes in, the upload is refused with a plain explanation, because wearable sleep only matters next to CPAP hours. That pairing powers the "slept, but no CPAP — were you away?" check.

**Safety of the upload path.** Uploads are capped at 64 MB per request and 2,500 files. Zips are read in memory, never extracted to disk. The upload is refused if it unpacks to more than 1 GB in total, has more than 20,000 entries, or nests zips more than two levels deep. Any single file over 512 MB is refused, as are encrypted members and absolute or `..` paths. Members over 10 MB with a compression ratio above 200 are skipped as possible zip bombs. One unreadable file is skipped and reported; it doesn't sink the rest of the upload.

**Sample files.** `python scripts/make_samples.py` writes a synthetic file for every source to `data/samples/` (built from the fictional persona Layla). It also writes `data/samples/resmed_sd_card/`, a fake card folder for trying "Choose a folder". The app's **Try sample files** button runs the same files through the same path.

Uploads are read in memory for that browser session only. They are never written to disk and are deleted by *Delete everything* or a server restart. **Real files used to check the parsers stay on the team's PC. They, their outputs and anything derived from them are never committed; the guard test enforces this for code and data.**

## 3. Reference knowledge used in the rules (no data, cited)

| Rule | Source |
|---|---|
| 4 h a night as the adherence bar; 70% of nights | Common adherence definition (e.g. US CMS: ≥4 h on 70% of nights in 30 consecutive days within the first 90 days) |
| Large leak above 24 L/min (95th percentile) | ResMed device "large leak" threshold, as used in myAir and AirView reports |
| Residual AHI 10 or more on several nights → clinician review | Conservative heuristic chosen by the team; pending clinician review |
| Behaviour-change technique labels | BCT Taxonomy v1 (Michie et al., 2013) |
| CPAP non-adherence range 29–83% | Weaver TE, Grunstein RR. *Proc Am Thorac Soc* 2008;5:173–178 |

## 4. Data we do not use

- No data from the organisers, partners or any health system.
- No real patient's data. The team lead's own CPAP exports are not used, copied or shipped; their experience informed the parameter ranges at aggregate level only (§1).
- No scraped forums or social media.
- The legacy `cpap_data.json` from the original Sleep IQ repository holds real data. It is not copied into this project.
