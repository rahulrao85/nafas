from datetime import date

from nafas.benchmark import run_all, score
from nafas.models import Night
from nafas.quality import clean_cpap
from nafas.sources import ingest

S = score(run_all())


def test_safety_critical_suites_hold_their_numbers():
    crisis, clinical = S["suites"]["crisis"], S["suites"]["clinical"]
    assert crisis["sensitivity"] == 100.0                 # no emergency phrasing may be missed
    assert crisis["specificity"] >= 95.0                  # one accepted false alarm (third-person "fainted")
    assert clinical["accuracy"] == 100.0
    assert S["suites"]["qa"]["accuracy"] == 100.0             # Q&A routing and output checks
    assert not [f for f in S["failures"] if f["module"] == "crash"]


def test_benchmark_is_half_hard_and_names_modules():
    assert S["total"] >= 100 and S["hard"] >= S["total"] * 0.45
    assert all(f["module"] in {"safety", "quality", "engine", "barriers", "qa.route", "qa.output_checks", "crash"} for f in S["failures"])


def test_bad_csv_gives_warnings_not_crashes():
    bad = (b"date,usage_min,ahi,leak95_lpm,session_start\n2026-01-01,420,1.1,4,23:10\n2026-01-02,410,999,5,25:99\n"
           b"2026-01-02,400,1.0,5,23:00\nnot-a-date,7,1,0.3,\n2026-01-03,,1,0.2,\n2026-01-15,430,1,3,23:00\n")
    rep = ingest([("bad.csv", bad)])
    codes = {w.code for w in rep.warnings}
    assert {"bad_rows", "usage_missing", "impossible_ahi", "impossible_session_start", "duplicates", "gap",
            "missing_wearable"} <= codes
    assert rep.nights and rep.error is None
    assert all(w.to_dict("ar")["text"] for w in rep.warnings)


def test_stop_only_when_usage_is_missing_everywhere():
    rep = ingest([("x.csv", b"date,ahi\n2026-01-01,1\n2026-01-02,2\n")])
    assert rep.error == "no_usage" and rep.warnings[0].severity == "stop"


def test_units_are_flagged_not_guessed():
    ns = [Night(date(2026, 1, d), usage_min=7.5, leak95_lpm=0.4) for d in range(1, 6)]
    clean, warns = clean_cpap(ns, "nafas_csv", guess_units=True)
    assert {w.code for w in warns} >= {"usage_unit_suspect", "leak_unit_suspect"}
    assert clean[0].usage_min == 7.5 and clean[0].leak95_lpm == 0.4      # nothing silently converted


def test_impossible_usage_counts_as_not_used_and_unused_readings_are_dropped():
    ns = [Night(date(2026, 1, 1), usage_min=2000, ahi=1), Night(date(2026, 1, 2), usage_min=0, ahi=30)]
    clean, warns = clean_cpap(ns, "nafas_csv", guess_units=False)
    assert clean[0].usage_min == 0 and clean[1].ahi is None
    assert "impossible_usage_min" in {w.code for w in warns}
