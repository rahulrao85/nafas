"""Wearable sleep sources other than raw FIT: Gadgetbridge database, Collector (smart ring) export,
Apple Health export, Fitbit / Google Takeout sleep JSON.

Each parser returns {"sleep": {night: minutes}, "hrv": {night: ms}, "rhr": {night: bpm}}, where a night is the
evening date of a noon-to-noon day. Identifying fields (names, birth dates, device addresses and serials)
are never read or kept.
"""

from __future__ import annotations

import sqlite3
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from .fit import night_of


def _empty() -> dict:
    return {"sleep": {}, "hrv": {}, "rhr": {}}


def _mean(xs):
    return round(sum(xs) / len(xs), 1) if xs else None


# ─── Gadgetbridge database (inside a Gadgetbridge "Export zip") ──────────────

GB_ASLEEP = {2, 3, 4}     # Garmin sleep levels as Gadgetbridge stores them: 1 awake, 2 light, 3 deep, 4 rem


def is_sqlite(head: bytes) -> bool:
    return head.startswith(b"SQLite format 3\x00")


def parse_gadgetbridge_db(data: bytes, tz_offset_min: int = 0) -> dict:
    """Best effort: Gadgetbridge's schema varies by device and version. We read only tables named
    *SLEEP_STAGE_SAMPLE (TIMESTAMP in ms + STAGE) and *HRV_SUMMARY_SAMPLE (TIMESTAMP + LAST_NIGHT_AVERAGE)."""
    con = sqlite3.connect(":memory:")
    con.deserialize(data)
    out = _empty()
    off = timedelta(minutes=tz_offset_min)
    tables = [r[0] for r in con.execute("select name from sqlite_master where type='table'")]

    def cols(t):
        return {r[1].upper() for r in con.execute(f'pragma table_info("{t}")')}

    for t in tables:
        up, c = t.upper(), cols(t)
        if up.endswith("SLEEP_STAGE_SAMPLE") and {"TIMESTAMP", "STAGE"} <= c:
            rows = con.execute(f'select TIMESTAMP, STAGE from "{t}" order by TIMESTAMP').fetchall()
            for i, (ts, stage) in enumerate(rows):
                start = datetime.fromtimestamp(ts / 1000, timezone.utc)
                end = (datetime.fromtimestamp(rows[i + 1][0] / 1000, timezone.utc)
                       if i + 1 < len(rows) else start + timedelta(minutes=1))
                if end - start > timedelta(hours=3):
                    end = start + timedelta(minutes=1)
                if stage in GB_ASLEEP:
                    n = night_of(start + off)
                    out["sleep"][n] = out["sleep"].get(n, 0) + (end - start).total_seconds() / 60
        elif up.endswith("HRV_SUMMARY_SAMPLE") and {"TIMESTAMP", "LAST_NIGHT_AVERAGE"} <= c:
            for ts, v in con.execute(f'select TIMESTAMP, LAST_NIGHT_AVERAGE from "{t}"'):
                if v:
                    out["hrv"][night_of(datetime.fromtimestamp(ts / 1000, timezone.utc) + off)] = float(v)
    con.close()
    out["sleep"] = {k: round(v) for k, v in out["sleep"].items()}
    return out


# ─── Collector (smart ring) export: {"documents": [...]}, the Collector ingest contract v1 ──

def is_collector(obj) -> bool:
    docs = obj.get("documents") if isinstance(obj, dict) else obj
    return (isinstance(docs, list) and bool(docs) and isinstance(docs[0], dict)
            and "type" in docs[0] and "ts" in docs[0] and "payload" in docs[0])


def _iso(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def parse_collector(obj) -> dict:
    """`sleep.segment` (stage light/deep/rem/awake) → minutes asleep; `vitals.hr` / `vitals.hrv` readings
    inside that night's sleep window → averages. Times carry their own UTC offset, so local time is exact."""
    docs = obj.get("documents") if isinstance(obj, dict) else obj
    out = _empty()
    window: dict = {}
    for d in docs:
        if d.get("type") == "sleep.segment" and d.get("end_ts"):
            a, b = _iso(d["ts"]), _iso(d["end_ts"])
            n = night_of(a.replace(tzinfo=None))
            lo, hi = window.get(n, (a, b))
            window[n] = (min(lo, a), max(hi, b))
            if (d.get("payload") or {}).get("stage") in ("light", "deep", "rem"):
                out["sleep"][n] = out["sleep"].get(n, 0) + (b - a).total_seconds() / 60
    hr, hrv = defaultdict(list), defaultdict(list)
    for d in docs:
        if d.get("type") in ("vitals.hr", "vitals.hrv"):
            v = (d.get("payload") or {}).get("value")
            if not isinstance(v, (int, float)):
                continue
            t = _iso(d["ts"])
            n = night_of(t.replace(tzinfo=None))
            if n in window and window[n][0] <= t <= window[n][1]:
                (hr if d["type"] == "vitals.hr" else hrv)[n].append(float(v))
    out["sleep"] = {k: round(v) for k, v in out["sleep"].items()}
    out["rhr"] = {n: round(min(v)) for n, v in hr.items()}          # lowest overnight reading
    out["hrv"] = {n: _mean(v) for n, v in hrv.items()}
    return out


# ─── Apple Health export.xml (streamed) ──────────────────────────────────────

SLEEP = "HKCategoryTypeIdentifierSleepAnalysis"
HRV = "HKQuantityTypeIdentifierHeartRateVariabilitySDNN"
RHR = "HKQuantityTypeIdentifierRestingHeartRate"


def _apple_dt(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%d %H:%M:%S %z")


def parse_apple(fileobj) -> dict:
    """Asleep minutes per night per source (max across sources, so iPhone + Watch aren't double-counted),
    HRV (SDNN) and resting HR averaged per night. The <Me> element (birth date, sex) is skipped."""
    per_source = defaultdict(lambda: defaultdict(float))
    hrv, rhr = defaultdict(list), defaultdict(list)
    for _, el in ET.iterparse(fileobj, events=("end",)):
        if el.tag != "Record":
            if el.tag in ("Me", "Workout", "ActivitySummary"):
                el.clear()
            continue
        t = el.get("type")
        try:
            if t == SLEEP and "Asleep" in (el.get("value") or ""):
                a, b = _apple_dt(el.get("startDate")), _apple_dt(el.get("endDate"))
                n = night_of(a.replace(tzinfo=None))
                per_source[el.get("sourceName", "?")][n] += (b - a).total_seconds() / 60
            elif t in (HRV, RHR):
                a = _apple_dt(el.get("startDate"))
                (hrv if t == HRV else rhr)[night_of(a.replace(tzinfo=None))].append(float(el.get("value")))
        except (TypeError, ValueError):
            pass
        el.clear()
    out = _empty()
    for nights in per_source.values():
        for n, m in nights.items():
            out["sleep"][n] = max(out["sleep"].get(n, 0), round(m))
    out["hrv"] = {n: _mean(v) for n, v in hrv.items()}
    out["rhr"] = {n: _mean(v) for n, v in rhr.items()}
    return out


# ─── Fitbit / Google Takeout sleep-YYYY-MM-DD.json ───────────────────────────

def is_fitbit(obj) -> bool:
    return isinstance(obj, list) and bool(obj) and isinstance(obj[0], dict) and "dateOfSleep" in obj[0] \
        and "minutesAsleep" in obj[0]


def parse_fitbit(obj) -> dict:
    out = _empty()
    for s in obj:
        try:
            start = datetime.fromisoformat(s["startTime"][:19])
            n = night_of(start)
            out["sleep"][n] = out["sleep"].get(n, 0) + int(s["minutesAsleep"])
        except (KeyError, TypeError, ValueError):
            continue
    return out
