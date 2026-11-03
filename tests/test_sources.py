import io
import json
import re
import zipfile

import pytest

from nafas import samples
from nafas.sources import archive, ingest
from nafas.server import MAX_UPLOAD_MB, create_app

ALL = samples.build_all()
STR = ALL["resmed_STR.edf"]


def _found(rep, kind):
    return next(f for f in rep.found if f["source"] == kind)


@pytest.mark.parametrize("name,kind,nights", [
    ("resmed_sd_card.zip", "resmed_str", 61),
    ("garmin_sleep_fit.zip", "garmin_fit", 30),
    ("gadgetbridge_export.zip", "gadgetbridge", 30),
    ("collector_ring_export.json", "collector", 20),
    ("apple_health_export.zip", "apple_health", 30),
    ("fitbit_sleep-2026-09.json", "fitbit", 20),
    ("nights.csv", "nafas_csv", 10),
])
def test_each_source_is_detected(name, kind, nights):
    rep = ingest([(name, ALL[name]), ("STR.edf", STR)], tz_offset_min=240)
    f = _found(rep, kind)
    assert f["nights"] == nights and f["first"] and f["last"]
    assert rep.error is None


def test_wearable_sleep_is_close_to_the_truth():
    truth = {n.date: n.wearable_sleep_min for n in samples._nights()}
    for name in ("garmin_sleep_fit.zip", "gadgetbridge_export.zip", "collector_ring_export.json",
                 "apple_health_export.zip"):
        rep = ingest([(name, ALL[name]), ("STR.edf", STR)], tz_offset_min=240)
        got = [(n.wearable_sleep_min, truth[n.date]) for n in rep.nights if n.wearable_sleep_min]
        assert got, name
        # stage files exclude short awakenings, so asleep time sits a little under time in bed
        assert all(0.85 * t <= w <= t for w, t in got), name


def test_apple_two_sources_are_not_double_counted():
    rep = ingest([("a.zip", ALL["apple_health_export.zip"]), ("STR.edf", STR)])
    assert max(n.wearable_sleep_min or 0 for n in rep.nights) < 12 * 60


def test_one_click_everything_merges_with_priority():
    rep = ingest(list(ALL.items()), tz_offset_min=240)
    by = {n.date.isoformat(): n for n in rep.nights}
    assert rep.summary()["nights"] == 61
    assert by["2026-11-02"].wearable_source == "garmin_fit"        # garmin beats the ring on shared nights
    assert by["2026-09-05"].wearable_source == "apple_health"      # apple beats fitbit
    assert by["2026-11-02"].wearable_hrv_ms and by["2026-11-02"].wearable_rhr
    # one row per source per upload, not one per FIT file
    assert sum(1 for f in rep.found if f["source"] == "garmin_fit") == 1
    assert _found(rep, "garmin_fit")["files"] == 30


def test_watch_sleep_without_cpap_feeds_the_travel_check():
    from nafas.loop import run
    from nafas.models import Profile
    rep = ingest([("a.zip", ALL["apple_health_export.zip"]), ("STR.edf", STR)], tz_offset_min=240)
    r = run(Profile(id="u", display_name="U"), rep.nights, as_of=__import__("datetime").date(2026, 9, 16))
    assert r.barriers[0].code == "TRAVEL_AWAY"


def test_identifiers_never_reach_the_nights_or_report():
    rep = ingest(list(ALL.items()), tz_offset_min=240)
    blob = json.dumps([n.to_dict() for n in rep.nights]) + json.dumps(rep.to_dict())
    for ident in (samples.FAKE_SERIAL, samples.FAKE_MAC, samples.FAKE_DOB, "Synthetic User", "Synthetic Watch"):
        assert ident not in blob, ident
    reasons = {s["file"].split("/")[-1]: s["reason"] for s in rep.skipped}
    assert reasons["Identification.tgt"] == "device_identity"
    assert reasons["20261101_231500_BRP.edf"] == "datalog"


def test_wearable_only_upload_asks_for_cpap():
    rep = ingest([("g.zip", ALL["garmin_sleep_fit.zip"])])
    assert rep.error == "no_cpap" and not rep.nights


def _zip(members: dict[str, bytes], level=zipfile.ZIP_DEFLATED) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", level) as z:
        for k, v in members.items():
            z.writestr(k, v)
    return buf.getvalue()


def test_zip_guards():
    evil = _zip({"../../etc/passwd": b"x", "C:/Windows/x.csv": b"x", "ok/STR.edf": STR,
                 "bomb.csv": b"0" * (30 * 1024 * 1024)})
    rep = ingest([("evil.zip", evil)])
    reasons = {s["file"].split("evil.zip/")[-1]: s["reason"] for s in rep.skipped}
    assert reasons["../../etc/passwd"] == "unsafe_path"
    assert reasons["C:/Windows/x.csv"] == "unsafe_path"
    assert reasons["bomb.csv"] == "zip_bomb"
    assert rep.summary()["nights"] == 61                            # the good member still counts


def test_nested_zip_depth_and_budget(monkeypatch):
    deep = _zip({"l1.zip": _zip({"l2.zip": _zip({"STR.edf": STR})})})
    rep = ingest([("deep.zip", deep)])
    assert any(s["reason"] == "zip_nested" for s in rep.skipped) and rep.error == "no_cpap"
    monkeypatch.setattr(archive, "MAX_TOTAL_BYTES", 1000)
    rep = ingest([("card.zip", ALL["resmed_sd_card.zip"])])
    assert any(s["reason"] in ("too_large", "zip_bad") for s in rep.skipped)


def test_damaged_fit_is_skipped_not_fatal():
    fit = samples.garmin_sleep_fit(samples._nights()[-1])
    broken = fit[:-6] + b"\x00\x00\x00\x00" + fit[-2:]
    rep = ingest([("x.fit", broken), ("STR.edf", STR)])
    assert any(s["reason"] == "unreadable" for s in rep.skipped) and rep.summary()["nights"] == 61


@pytest.fixture
def client():
    return create_app().test_client()


def test_upload_endpoint_takes_many_files_with_paths(client):
    # what a browser sends for "Choose a folder": each file of the card, with its relative path
    with zipfile.ZipFile(io.BytesIO(ALL["resmed_sd_card.zip"])) as z:
        card = {i.filename: z.read(i) for i in z.infolist()}
    data = {"files": [(io.BytesIO(v), k.split("/")[-1]) for k, v in card.items()]
            + [(io.BytesIO(ALL["collector_ring_export.json"]), "ring.json")],
            "paths": json.dumps(list(card) + ["ring.json"]), "tz_offset_min": "240",
            "skipped": json.dumps([{"file": "SD CARD/DATALOG/x_PLD.edf", "reason": "datalog"}])}
    r = client.post("/api/upload", data=data, content_type="multipart/form-data")
    j = r.get_json()
    assert r.status_code == 200 and j["nights"] == 61
    assert j["report"]["skipped_counts"]["datalog"] == 2           # one skipped in the browser, one on the server
    s = client.get(f"/api/state?persona={j['persona']}").get_json()
    assert s["last_night"]["wearable_source"] == "collector"


def test_upload_endpoint_refuses_wearable_only_and_reports_why(client):
    r = client.post("/api/upload", data={"files": [(io.BytesIO(ALL["fitbit_sleep-2026-09.json"]), "s.json")]},
                    content_type="multipart/form-data")
    assert r.status_code == 422 and r.get_json()["report"]["error"] == "no_cpap"


def test_sample_button_and_size_limit(client):
    j = client.post("/api/upload-samples").get_json()
    assert j["nights"] == 61 and len(j["report"]["found"]) == 8          # STR.edf and the card zip are two rows
    assert create_app().config["MAX_CONTENT_LENGTH"] == MAX_UPLOAD_MB * 1024 * 1024 >= 50 * 1024 * 1024


def test_engine_text_is_arabic_in_arabic_mode(client):
    s = client.get("/api/state?persona=omar").get_json()          # Omar's language is Arabic
    arabic = re.compile(r"[\u0600-\u06FF]")
    texts = [e for d in s["detections"] for e in d["evidence"]] + [e for b in s["barriers"] for e in b["evidence"]]
    texts += [s["nudge"]["reason"], s["persona"]["story"]] + [h["outcome_note"] for h in s["history"] if h["outcome_note"]]
    texts += [h["trigger_label"] for h in s["history"]]
    assert texts and all(arabic.search(t) for t in texts), [t for t in texts if not arabic.search(t)]
    en = client.get("/api/state?persona=layla").get_json()
    assert not arabic.search(json.dumps([d["evidence"] for d in en["detections"]], ensure_ascii=False))
