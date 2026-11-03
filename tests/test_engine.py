from datetime import date

from conftest import make_nights
from nafas import engine
from nafas.models import Night


def test_status_and_gap_fill():
    nights = [Night(date(2026, 1, 1), 300), Night(date(2026, 1, 4), 100)]
    filled = engine.fill_gaps(nights)
    assert [n.date.day for n in filled] == [1, 2, 3, 4]
    assert [engine.status_of(n) for n in filled] == ["met", "missed", "missed", "partial"]


def test_lapse_two_missed_in_a_row():
    d = engine.detect_lapse(make_nights([420] * 10 + [0, 0]))
    assert d and d.kind == "lapse" and d.started == date(2026, 1, 11)


def test_lapse_three_of_five_short():
    assert engine.detect_lapse(make_nights([420] * 10 + [100, 420, 120, 420, 90]))
    assert engine.detect_lapse(make_nights([420] * 10 + [100, 420, 420, 420, 90])) is None


def test_decline_needs_a_real_drop_from_an_adherent_baseline():
    assert engine.detect_decline(make_nights([450] * 28 + [330] * 14))
    assert engine.detect_decline(make_nights([450] * 28 + [400] * 14)) is None
    assert engine.detect_decline(make_nights([200] * 28 + [100] * 14)) is None   # baseline never adherent


def test_leak_episode():
    leaks = [2.0] * 10 + [30.0, 5.0, 35.0]
    assert engine.detect_leak(make_nights([420] * 13, leak95_lpm=leaks))
    assert engine.detect_leak(make_nights([420] * 13, leak95_lpm=[2.0] * 12 + [30.0])) is None


def test_leak_creep_is_gradual_not_sudden():
    gradual = [2.0] * 30 + [8 + i for i in range(21)]          # rising for three weeks
    sudden = [2.0] * 37 + [30.0] * 14                          # jumps two weeks ago
    assert engine.detect_leak_creep(make_nights([420] * 51, leak95_lpm=gradual))
    assert engine.detect_leak_creep(make_nights([420] * 51, leak95_lpm=sudden)) is None


def test_clinical_flag_on_high_residual_ahi():
    d = engine.detect_clinical(make_nights([420] * 7, ahi=[1, 1, 1, 12, 11, 1, 14]))
    assert d and d.severity == "clinician"


def test_momentum_banked_nights_never_go_down():
    before = engine.momentum(make_nights([420] * 20))
    after = engine.momentum(make_nights([420] * 20 + [0, 0, 0]))
    assert after["banked_nights"] == before["banked_nights"] == 20


def test_run_forgives_one_short_night_a_week():
    m = engine.momentum(make_nights([420] * 5 + [0] + [420] * 5))
    assert m["run"] == 10 and m["run_grace_used"] == 1


def test_run_breaks_on_two_misses_in_a_row():
    m = engine.momentum(make_nights([420] * 5 + [0, 0] + [420] * 3))
    assert m["run"] == 3 and m["best_run"] == 5


def test_run_breaks_on_second_miss_inside_seven_days():
    m = engine.momentum(make_nights([420] * 5 + [0] + [420] * 3 + [0] + [420] * 2))
    assert m["run"] == 5      # 2 nights, a forgiven miss, 3 nights; the earlier miss is within 7 days, so it stops
