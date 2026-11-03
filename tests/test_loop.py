from conftest import make_nights
from nafas import actions as lib
from nafas import loop, synthetic
from nafas.engine import fill_gaps
from nafas.models import CheckIn


def test_lapse_opens_comeback_and_recovers_without_reset(profile):
    nights = make_nights([420] * 20 + [0, 0, 0] + [420] * 5)
    mid = loop.run(profile, nights, as_of=nights[22].date)
    assert mid.in_recovery is not None and mid.nudge["send"]
    assert lib.COMEBACK["en"] == mid.nudge["text"]
    end = loop.run(profile, nights)
    lapse = end.lapses[-1]
    assert lapse.comeback == nights[23].date and lapse.recovered is not None
    assert end.momentum["banked_nights"] == 25            # nothing lost to the lapse


def test_leak_opens_one_action_and_judges_it_three_nights_later(profile):
    leaks = [2.0] * 15 + [30.0, 35.0] + [3.0] * 6
    nights = make_nights([420] * 23, leak95_lpm=leaks)
    r = loop.run(profile, nights)
    first = r.interventions[0]
    assert first.barrier == "MASK_FIT" and first.trigger == "leak"
    assert first.status == "helped" and "Leak under" in first.outcome_note
    assert r.learner.stats[first.action_id].helped == 1


def test_two_failures_on_a_barrier_escalate_to_care_team(profile):
    nights = make_nights([400] * 15 + [380] * 20, leak95_lpm=[2.0] * 15 + [38.0] * 20)
    r = loop.run(profile, nights)
    fit = [iv for iv in r.interventions if iv.barrier == "MASK_FIT"]
    assert fit[0].status == fit[1].status == "not_helped"
    assert fit[2].escalated and lib.BY_ID[fit[2].action_id].care_team


def test_self_report_replans_open_action(profile):
    leaks = [2.0] * 15 + [30.0, 35.0] + [3.0] * 3
    nights = make_nights([420] * 20, leak95_lpm=leaks)
    ci = [CheckIn(nights[17].date, "NOISE_PARTNER")]
    r = loop.run(profile, nights, ci)
    assert r.interventions[0].status == "replanned"
    assert r.interventions[1].barrier == "NOISE_PARTNER" and r.interventions[1].barrier_source == "self-report"


def test_swap_offers_a_different_action(profile):
    nights = make_nights([420] * 15 + [0, 0])
    r = loop.run(profile, nights)
    iv = r.open_intervention
    swapped = loop.run(profile, nights, events=[{"type": "swap", "date": nights[-1].date.isoformat(),
                                                 "intervention_id": iv.id}])
    assert swapped.open_intervention.action_id != iv.action_id
    assert iv.action_id in swapped.open_intervention.swapped_out


def test_replay_is_deterministic():
    p = synthetic.persona_layla()
    a = loop.run(p["profile"], fill_gaps(p["nights"]), p["checkins"])
    b = loop.run(p["profile"], fill_gaps(p["nights"]), p["checkins"])
    assert [(i.id, i.action_id, i.status) for i in a.interventions] == \
           [(i.id, i.action_id, i.status) for i in b.interventions]


def test_nudges_respect_choice_and_quiet_hours(profile):
    nights = make_nights([420] * 15 + [0, 0])
    profile.nudges_enabled = False
    assert not loop.run(profile, nights).nudge["send"]
    profile.nudges_enabled, profile.nudge_hour = True, 23
    assert "quiet" in loop.run(profile, nights).nudge["reason"]


def test_personas_tell_their_stories():
    def last(pid):
        p = synthetic.PERSONAS[pid]()
        return loop.run(p["profile"], fill_gaps(p["nights"]), p["checkins"])
    layla, omar, ravi = last("layla"), last("omar"), last("ravi")
    assert layla.clinician_flags and any(iv.escalated for iv in layla.interventions)
    assert any(l.recovered for l in layla.lapses)
    assert {d.kind for d in omar.detections} & {"leak", "leak_creep"}
    assert any(iv.barrier == "ROUTINE_SHIFT" for iv in omar.interventions)    # Ramadan
    assert ravi.in_recovery is not None and any(iv.barrier == "FELT_FINE" for iv in ravi.interventions)
