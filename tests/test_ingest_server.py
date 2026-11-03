import io
import json
import struct
from pathlib import Path

import pytest

from nafas import ingest, synthetic
from nafas.server import create_app

ROOT = Path(__file__).resolve().parents[1]


def build_str_edf(days: list[dict]) -> bytes:
    """A minimal ResMed-style STR.edf: one record per day, one sample per signal (two for MaskOn)."""
    sig = [("Date", 0, 40000, 0, 40000, 1), ("OnDuration", 0, 1440, 0, 14400, 1), ("AHI", 0, 100, 0, 1000, 1),
           ("Leak.95", 0, 2, 0, 1000, 1), ("MaskPress.95", 0, 30, 0, 3000, 1), ("MaskEvents", 0, 100, 0, 100, 1),
           ("MaskOn", 0, 1440, 0, 1440, 2)]
    ns = len(sig)
    pad = lambda s, w: str(s).ljust(w)[:w].encode("ascii")  # noqa: E731
    hdr = pad("0", 8) + pad("X", 80) + pad("Y", 80) + pad("01.01.26", 8) + pad("00.00.00", 8)
    hdr += pad(256 + ns * 256, 8) + pad("", 44) + pad(len(days), 8) + pad(86400, 8) + pad(ns, 4)
    hdr += b"".join(pad(s[0], 16) for s in sig) + pad("", 80) * ns + pad("", 8) * ns
    for k in (1, 2, 3, 4):
        hdr += b"".join(pad(s[k], 8) for s in sig)
    hdr += pad("", 80) * ns + b"".join(pad(s[5], 8) for s in sig) + pad("", 32) * ns
    body = b""
    for d in days:
        body += struct.pack("<7hh", d["date"], round(d["min"] * 10), round(d["ahi"] * 10),
                            round(d["leak_ls"] * 500), round(d["press"] * 100), d["events"], d["on"], 0)
    return hdr + body


def test_resmed_str_edf_is_parsed_and_identifiers_dropped():
    days = [{"date": 20575 + i, "min": 420 + i, "ahi": 1.2, "leak_ls": 0.5, "press": 12.5, "events": 2, "on": 660}
            for i in range(3)]
    nights = ingest.read_resmed_str(build_str_edf(days))
    n = nights[0]
    assert len(nights) == 3 and n.date.isoformat() == "2026-05-02"
    assert n.usage_min == pytest.approx(420, abs=0.2) and n.ahi == pytest.approx(1.2, abs=0.01)
    assert n.leak95_lpm == pytest.approx(30.0, abs=0.1)         # 0.5 L/s → 30 L/min
    assert n.session_start == "23:00" and n.mask_events == 1
    assert not any(hasattr(x, "serial") for x in nights)


def test_csv_round_trip_and_ddmonyyyy_dates():
    nights = synthetic.persona_layla()["nights"][:10]
    again = ingest.read_csv(ingest.to_csv(nights))
    assert [n.to_dict() for n in again] == [n.to_dict() for n in nights]
    one = ingest.read_csv("date,usage_hours,ahi\n03-Nov-2026,7.5,1.1\n")[0]
    assert one.date.isoformat() == "2026-11-03" and one.usage_min == 450


def test_json_and_bad_files():
    nights = ingest.read_json(json.dumps({"nights": [{"date": "2026-01-01", "usage_min": 300}]}))
    assert nights[0].usage_min == 300
    with pytest.raises(ValueError):
        ingest.read_csv("day,hours\n1,2\n")


@pytest.fixture
def client():
    return create_app().test_client()


def test_state_and_loop_endpoints(client):
    s = client.get("/api/state?persona=layla&as_of=2026-08-11").get_json()
    assert s["as_of"] == "2026-08-11" and s["clinician_flag"] and s["intervention"]["action"]["care_team"]
    assert 1 <= len(s["weekly"]) <= 12 and len(s["series"]) <= 90
    assert s["weekly"][-1]["days"][0]["date"] <= "2026-08-11" <= s["weekly"][-1]["days"][6]["date"]
    iv = s["intervention"]["id"]
    after = client.post("/api/action", json={"persona": "layla", "as_of": "2026-08-11",
                                             "type": "accept", "intervention_id": iv}).get_json()
    assert after["intervention"]["accepted"] is True
    r = client.post("/api/checkin", json={"persona": "ravi", "barrier": "FORGOT", "note": "chest pain"}).get_json()
    assert r["urgent"] and r["state"]["intervention"]["barrier"] == "FORGOT"
    assert client.post("/api/checkin", json={"persona": "ravi", "barrier": "NOPE"}).status_code == 400
    assert client.get("/api/state?persona=nobody").status_code == 404


def test_coach_endpoint_works_offline(client, monkeypatch):
    monkeypatch.setenv("NAFAS_LLM", "offline")
    out = client.post("/api/coach", json={"persona": "omar"}).get_json()
    assert out["source"] == "template" and out["lang"] == "ar"


def test_care_team_summary_needs_consent(client):
    assert client.get("/api/care-team-summary?persona=ravi").status_code == 403
    client.post("/api/settings", json={"persona": "ravi", "share_with_care_team": True})
    s = client.get("/api/care-team-summary?persona=ravi").get_json()
    assert "not a diagnosis" in s["note"]


def test_settings_are_clamped(client):
    s = client.post("/api/settings", json={"persona": "layla", "goal_hours": 99, "language": "xx",
                                           "nudge_hour": 30}).get_json()
    assert s["profile"]["goal_hours"] == 10 and s["profile"]["language"] == "en" and s["profile"]["nudge_hour"] == 6


def test_upload_lives_in_session_memory_and_forget_clears_it(client):
    csv_bytes = ingest.to_csv(synthetic.persona_ravi()["nights"][:40]).encode()
    r = client.post("/api/upload", data={"file": (io.BytesIO(csv_bytes), "mine.csv")},
                    content_type="multipart/form-data").get_json()
    assert r["nights"] == 40
    assert client.get(f"/api/state?persona={r['persona']}").status_code == 200
    client.post("/api/forget")
    assert client.get(f"/api/state?persona={r['persona']}").status_code == 404


def test_cohort_report_has_the_challenge_metrics(client):
    rep = client.get("/api/cohort").get_json()
    o = rep["overall"]
    for k in ("persisting_pct", "retained_pct", "recovery_rate", "median_days_to_recover", "ahi_first_30"):
        assert o[k] is not None, k
    assert set(rep["by"]) == {"language", "age_band", "shift_worker"} and "Synthetic" in rep["caveat"]


# SHA-256 of identifying tokens (a real name and a real device serial), so the guard itself leaks nothing.
BANNED_TOKEN_HASHES = {
    "af4a400a2ceb7963a424d9cf3779175c8d258facf8a31ee8bc1949dc060e10e6",
    "b237b4c49912394c152b8fa59521372a8cca140099e35c650d0b0c2ec7d4791d",
}
BANNED_PATHS = ("own-apps", "cpap_data.json", "myair")


def test_no_real_patient_data_is_referenced():
    """Guard: code and data must never read a real patient's CPAP exports or carry their identifiers."""
    import hashlib
    import re
    for path in list((ROOT / "nafas").rglob("*.py")) + list((ROOT / "data").rglob("*")):
        if path.is_file():
            text = path.read_text(encoding="utf-8", errors="ignore")
            for word in BANNED_PATHS:
                assert word not in text, f"{word} found in {path}"
            tokens = {hashlib.sha256(t.lower().encode()).hexdigest() for t in re.findall(r"\w+", text)}
            assert not tokens & BANNED_TOKEN_HASHES, f"identifying token found in {path}"
