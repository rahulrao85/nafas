import re

from conftest import make_nights
from nafas import actions as lib
from nafas.barriers import BARRIERS, infer
from nafas.engine import detect_all
from nafas.models import CheckIn
from nafas.safety import check_output


def test_self_report_outranks_data(profile):
    leaks = [2.0] * 10 + [30.0, 35.0, 40.0]
    hist = make_nights([420] * 10 + [200, 210, 190], leak95_lpm=leaks)
    ranked = infer(hist, detect_all(hist), [CheckIn(hist[-1].date, "DRYNESS")], profile)
    assert ranked[0].code == "DRYNESS" and ranked[0].source == "self-report"
    assert any(b.code == "MASK_FIT" for b in ranked)


def test_leak_with_short_nights_points_to_mask_fit(profile):
    hist = make_nights([420] * 10 + [200, 210, 190], leak95_lpm=[2.0] * 10 + [30.0, 35.0, 40.0])
    b = infer(hist, detect_all(hist), [], profile)[0]
    assert b.code == "MASK_FIT" and b.evidence


def test_travel_needs_consecutive_away_nights(profile):
    sleep = [None] * 10 + [400, 410, 395]
    hist = make_nights([420] * 10 + [0, 0, 0], wearable_sleep_min=sleep)
    assert infer(hist, detect_all(hist), [], profile)[0].code == "TRAVEL_AWAY"
    one_off = make_nights([420, 0, 420, 0, 420, 0, 420], wearable_sleep_min=[None, 400] * 3 + [None])
    assert all(b.code != "TRAVEL_AWAY" for b in infer(one_off, detect_all(one_off), [], profile))


def test_bedtime_shift_points_to_routine(profile):
    starts = ["23:00"] * 40 + ["02:00"] * 7
    usage = [450] * 40 + [200, 210, 0, 0, 230, 220, 200]
    hist = make_nights(usage, session_start=[s if u else None for s, u in zip(starts, usage)])
    assert "ROUTINE_SHIFT" in {b.code for b in infer(hist, detect_all(hist), [], profile)}


def test_every_barrier_has_an_action_and_every_action_is_complete():
    for code in BARRIERS:
        assert lib.for_barrier(code), code
    for a in lib.LIBRARY:
        assert set(a.title) == set(a.step) == {"en", "ar"}, a.id
        assert re.fullmatch(r"\d{1,2}\.\d{1,2}", a.bct), a.id
        assert a.rationale and a.limits and a.bct_name, a.id


def test_action_library_passes_the_coach_safety_rules():
    for a in lib.LIBRARY:
        for lang in ("en", "ar"):
            assert check_output(a.title[lang] + " " + a.step[lang]) == [], (a.id, lang)


def test_pressure_actions_never_suggest_a_number():
    for a in lib.for_barrier("PRESSURE_DISCOMFORT"):
        assert not re.search(r"\d+\s*(cm|hpa)", a.step["en"], re.I)
