"""Personal hub mode, on a synthetic hub store (no real data)."""
import json
import sqlite3
from datetime import date, datetime, timedelta, timezone

import pytest

from nafas.server import create_app
from nafas.sources import hub

TZ = timezone(timedelta(hours=4))
SCHEMA = """create table ingest_documents (id text primary key, device_id text, device_kind text, type text,
            ts text, end_ts text, ts_utc text, end_ts_utc text, payload text, source text)"""


def _doc(con, i, kind, typ, ts, end_ts, payload):
    con.execute("insert into ingest_documents values (?,?,?,?,?,?,?,?,?,?)",
                (f"{i}", "dev:synthetic", kind, typ, ts, end_ts, ts, end_ts, json.dumps(payload), "test"))


def make_store(path, nights=30, ring=True, watch=False):
    con = sqlite3.connect(path)
    con.execute(SCHEMA)
    start = date(2026, 10, 1)
    for k in range(nights):
        d = start + timedelta(days=k)
        if k % 2:   # SD-card shape
            on = datetime.combine(d, datetime.min.time()) + timedelta(hours=23)
            p = {"date": d.isoformat(), "usage_min": 0 if k in (20, 21) else 420.0, "ahi": 1.1, "leak_95_lpm": 6.0,
                 "press_95": 12.4, "source": ["SD"],
                 "mask_sessions": [{"on": on.isoformat(), "off": (on + timedelta(hours=7)).isoformat()}]}
        else:       # myAir shape
            p = {"date": d.isoformat(), "usage_min": 0 if k in (20, 21) else 430, "ahi": 0.9, "leak_95_lpm": 2.4,
                 "mask_pairs": 1, "myair_score": 95, "source": ["myAir"]}
        _doc(con, f"cpap{k}", "cpap.airsense10", "cpap.night", f"{d}T12:00:00+05:30", None, p)
        for kind, on_flag in (("ring.r2n", ring), ("watch.venu3", watch)):
            if not on_flag:
                continue
            a = datetime.combine(d, datetime.min.time(), TZ) + timedelta(hours=23)
            for j, stage in enumerate(["light", "deep", "rem", "light"]):
                s = a + timedelta(minutes=100 * j)
                _doc(con, f"{kind}{k}-{j}", kind, "sleep.segment", s.isoformat(),
                     (s + timedelta(minutes=100)).isoformat(), {"stage": stage})
            _doc(con, f"{kind}{k}-hr", kind, "vitals.hr", (a + timedelta(minutes=30)).isoformat(), None,
                 {"value": 55, "unit": "bpm"})
    con.commit()
    con.close()


@pytest.fixture
def store(tmp_path):
    p = tmp_path / "hub.db"
    make_store(p)
    return p


def test_reads_cpap_and_ring_nights(store):
    rep = hub.load(store)
    assert rep.error is None and len(rep.nights) == 30
    n = {x.date.isoformat(): x for x in rep.nights}
    assert n["2026-10-02"].session_start == "23:00" and n["2026-10-02"].pressure95 == 12.4      # SD shape
    assert n["2026-10-01"].mask_events == 1 and n["2026-10-01"].leak95_lpm == 2.4             # myAir shape
    assert n["2026-10-05"].wearable_sleep_min == 400 and n["2026-10-05"].wearable_source == "collector"
    assert n["2026-10-21"].usage_min == 0 and n["2026-10-21"].wearable_sleep_min == 400        # slept, no CPAP


def test_watch_documents_are_picked_up_and_win_over_the_ring(tmp_path):
    p = tmp_path / "hub.db"
    make_store(p, watch=True)
    rep = hub.load(p)
    assert rep.nights[5].wearable_source == "gadgetbridge"
    assert any(f["source"] == "gadgetbridge" for f in rep.found)


def test_store_is_opened_read_only(store):
    con = hub._connect(store)
    with pytest.raises(sqlite3.OperationalError):
        con.execute("delete from ingest_documents")
    con.close()


def test_off_by_default_and_on_with_the_flag(store, monkeypatch):
    monkeypatch.delenv("NAFAS_PERSONAL_HUB", raising=False)
    import nafas.server as srv
    srv._HUB.clear()
    c = create_app().test_client()
    assert "hub" not in [p["id"] for p in c.get("/api/personas").get_json()["personas"]]
    assert c.get("/api/state?persona=hub").status_code == 404

    monkeypatch.setenv("NAFAS_PERSONAL_HUB", "1")
    monkeypatch.setenv("NAFAS_HUB_DB", str(store))
    srv._HUB.clear()
    ids = [p["id"] for p in c.get("/api/personas").get_json()["personas"]]
    assert ids[0] == "hub"
    s = c.get("/api/state?persona=hub").get_json()
    assert s["persona"]["uploaded"] and s["range"]["last"] == "2026-10-30"


def test_refreshes_when_the_store_changes(store, monkeypatch):
    import nafas.server as srv
    monkeypatch.setenv("NAFAS_PERSONAL_HUB", "1")
    monkeypatch.setenv("NAFAS_HUB_DB", str(store))
    srv._HUB.clear()
    c = create_app().test_client()
    assert c.get("/api/state?persona=hub").get_json()["range"]["last"] == "2026-10-30"
    con = sqlite3.connect(store)
    _doc(con, "cpap-new", "cpap.airsense10", "cpap.night", "2026-10-31T12:00:00+05:30", None,
         {"date": "2026-10-31", "usage_min": 410, "ahi": 1.0, "leak_95_lpm": 3.0, "mask_pairs": 1})
    con.commit()
    con.close()
    assert c.get("/api/state?persona=hub").get_json()["range"]["last"] == "2026-10-31"


def test_missing_store_does_not_break_the_app(tmp_path, monkeypatch):
    import nafas.server as srv
    monkeypatch.setenv("NAFAS_PERSONAL_HUB", "1")
    monkeypatch.setenv("NAFAS_HUB_DB", str(tmp_path / "nope.db"))
    srv._HUB.clear()
    c = create_app().test_client()
    r = c.get("/api/personas")
    assert r.status_code == 200 and "hub" not in [p["id"] for p in r.get_json()["personas"]]
