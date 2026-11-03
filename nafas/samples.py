"""Synthetic sample files in every format Nafas reads, built from the fictional persona Layla.

    python scripts/make_samples.py      → data/samples/
    build_all() → {"filename": bytes}   (used by tests, in memory)

Everything is generated: the ResMed card holds a fake serial, the watch and ring files carry made-up device
ids, and the Apple export has a made-up birth date. That lets the tests prove these fields are never read.
"""

from __future__ import annotations

import io
import json
import sqlite3
import struct
import zipfile
from datetime import date, datetime, timedelta, timezone

from .synthetic import persona_layla

FIRST, LAST = date(2026, 9, 3), date(2026, 11, 2)
TZ = timezone(timedelta(hours=4))            # Abu Dhabi
FAKE_SERIAL = "SYNTH0000001"
FAKE_MAC = "00:00:5E:00:53:01"               # documentation-range MAC
FAKE_DOB = "1980-01-01"


def _nights():
    return [n for n in persona_layla()["nights"] if FIRST <= n.date <= LAST]


def _sleep_window(n):
    """Where the wearable says the person slept: CPAP start time if used, else 23:15."""
    hh, mm = (n.session_start or "23:15").split(":")
    start = datetime.combine(n.date, datetime.min.time(), TZ) + timedelta(hours=int(hh), minutes=int(mm))
    if int(hh) < 12:
        start += timedelta(days=1)
    return start, start + timedelta(minutes=n.wearable_sleep_min or 0)


def _stages(start, end):
    """A plausible hypnogram: 90-minute cycles of light → deep → light → rem, short awakenings."""
    t, out, cycle = start, [], [("light", 30), ("deep", 25), ("light", 20), ("rem", 15)]
    while t < end:
        for stage, mins in cycle:
            if t >= end:
                break
            e = min(end, t + timedelta(minutes=mins))
            out.append((t, e, stage))
            t = e
        if t < end:
            e = min(end, t + timedelta(minutes=3))
            out.append((t, e, "awake"))
            t = e
    return out


# ─── ResMed STR.edf ──────────────────────────────────────────────────────────

def resmed_str_edf(nights) -> bytes:
    sig = [  # label, pmin, pmax, dmin, dmax, samples per record
        ("Date", 0, 40000, 0, 40000, 1), ("MaskOn", -1, 1440, -1, 1440, 10), ("MaskOff", -1, 1440, -1, 1440, 10),
        ("MaskEvents", 0, 100, 0, 100, 1), ("Duration", 0, 1440, 0, 14400, 1), ("OnDuration", 0, 1440, 0, 14400, 1),
        ("AHI", -1, 100, -10, 1000, 1), ("Leak.95", -1, 2, -1000, 2000, 1), ("MaskPress.95", -1, 30, -100, 3000, 1),
    ]
    pad = lambda s, w: str(s).ljust(w)[:w].encode("ascii")  # noqa: E731
    ns = len(sig)
    hdr = pad("0", 8) + pad("X X X X", 80) + pad("Startdate X X X X", 80)
    hdr += pad(nights[0].date.strftime("%d.%m.%y"), 8) + pad("12.00.00", 8)
    hdr += pad(256 + ns * 256, 8) + pad("", 44) + pad(len(nights), 8) + pad(86400, 8) + pad(ns, 4)
    hdr += b"".join(pad(s[0], 16) for s in sig) + pad("", 80) * ns + pad("", 8) * ns
    for k in (1, 2, 3, 4):
        hdr += b"".join(pad(s[k], 8) for s in sig)
    hdr += pad("", 80) * ns + b"".join(pad(s[5], 8) for s in sig) + pad("", 32) * ns

    def dig(label, value):
        _, pmin, pmax, dmin, dmax, _ = next(s for s in sig if s[0] == label)
        return round((value - pmin) / (pmax - pmin) * (dmax - dmin) + dmin)

    body = b""
    for n in nights:
        used = n.usage_min > 0
        ons, offs = [-1] * 10, [-1] * 10
        if used:
            hh, mm = map(int, n.session_start.split(":"))
            on = (hh * 60 + mm - 720) % 1440
            ons[0], offs[0] = on, min(1440, on + int(n.usage_min))
        rec = [dig("Date", (n.date - date(1970, 1, 1)).days)]
        rec += [dig("MaskOn", v) for v in ons] + [dig("MaskOff", v) for v in offs]
        rec += [dig("MaskEvents", 2 * (n.mask_events or 1) if used else 0),
                dig("Duration", n.usage_min), dig("OnDuration", n.usage_min + (5 if used else 0)),
                dig("AHI", n.ahi if used else -1), dig("Leak.95", n.leak95_lpm / 60 if used else -1),
                dig("MaskPress.95", n.pressure95 if used else -1)]
        body += struct.pack(f"<{len(rec)}h", *rec)
    return hdr + body


def resmed_card_zip(nights) -> bytes:
    """What a copied SD card looks like: STR.edf, an identity file, settings and per-night DATALOG files."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("SD CARD/STR.edf", resmed_str_edf(nights))
        z.writestr("SD CARD/Identification.tgt", f"#SRN {FAKE_SERIAL}\n#PNA AirSense 10 AutoSet\n")
        z.writestr("SD CARD/SETTINGS/CGL.tgt", "synthetic settings\n")
        z.writestr("SD CARD/DATALOG/20261101/20261101_231500_BRP.edf", b"0" + b" " * 255)
    return buf.getvalue()


# ─── Garmin FIT ──────────────────────────────────────────────────────────────

_CRC = [0x0000, 0xCC01, 0xD801, 0x1400, 0xF001, 0x3C00, 0x2800, 0xE401,
        0xA001, 0x6C00, 0x7800, 0xB401, 0x5000, 0x9C01, 0x8801, 0x4400]
FIT_EPOCH = datetime(1989, 12, 31, tzinfo=timezone.utc)
LEVEL = {"awake": 1, "light": 2, "deep": 3, "rem": 4}


def _fit_crc(data: bytes, crc: int = 0) -> int:
    for b in data:
        for nib in (b & 0xF, b >> 4):
            tmp = _CRC[crc & 0xF]
            crc = ((crc >> 4) & 0x0FFF) ^ tmp ^ _CRC[nib]
    return crc


def _fts(dt: datetime) -> int:
    return int((dt - FIT_EPOCH).total_seconds())


def fit_file(messages: list[tuple[int, list[tuple[int, int, int, int]]]]) -> bytes:
    """messages: [(global_num, [(field_num, size, base_type, value), ...]), ...] (one definition per message)."""
    data, defined = b"", {}
    fmt = {1: "B", 2: "H", 4: "I"}
    for gnum, fields in messages:
        sig = (gnum, tuple((f[0], f[1], f[2]) for f in fields))
        if sig not in defined:
            local = len(defined) % 16
            defined[sig] = local
            data += bytes([0x40 | local, 0, 0]) + struct.pack("<H", gnum) + bytes([len(fields)])
            data += b"".join(bytes([n, s, t]) for n, s, t, _ in fields)
        data += bytes([defined[sig]]) + b"".join(struct.pack("<" + fmt[s], v) for _, s, _, v in fields)
    head = struct.pack("<BBHI4s", 14, 0x20, 2132, len(data), b".FIT")
    head += struct.pack("<H", _fit_crc(head))
    body = head + data
    return body + struct.pack("<H", _fit_crc(body))


def garmin_sleep_fit(n) -> bytes:
    start, end = _sleep_window(n)
    utc = start.astimezone(timezone.utc)
    msgs = [(0, [(0, 1, 0x00, 49), (1, 2, 0x84, 255), (4, 4, 0x86, _fts(utc))]),           # file_id (no serial)
            (162, [(253, 4, 0x86, _fts(utc)), (3, 4, 0x86, _fts(utc) + 4 * 3600)])]       # local = UTC+4
    for a, _, stage in _stages(start, end):
        msgs.append((275, [(253, 4, 0x86, _fts(a.astimezone(timezone.utc))), (0, 1, 0x00, LEVEL[stage])]))
    msgs.append((275, [(253, 4, 0x86, _fts(end.astimezone(timezone.utc))), (0, 1, 0x00, LEVEL["awake"])]))
    wake = end.astimezone(timezone.utc)
    hrv = 42 + (n.date.toordinal() % 9)
    msgs.append((370, [(253, 4, 0x86, _fts(wake)), (1, 2, 0x84, hrv * 128)]))
    msgs.append((211, [(253, 4, 0x86, _fts(wake)), (0, 1, 0x02, 58), (1, 1, 0x02, 56 + n.date.toordinal() % 5)]))
    return fit_file(msgs)


def garmin_zip(nights) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for n in nights:
            if n.wearable_sleep_min:
                z.writestr(f"GARMIN/SLEEP/{n.date.isoformat()}-sleep.fit", garmin_sleep_fit(n))
    return buf.getvalue()


# ─── Gadgetbridge export zip ─────────────────────────────────────────────────

def gadgetbridge_zip(nights) -> bytes:
    con = sqlite3.connect(":memory:")
    con.executescript("""
        create table DEVICE (_id integer primary key, NAME text, IDENTIFIER text);
        create table USER (_id integer primary key, NAME text, BIRTHDAY integer);
        create table GARMIN_SLEEP_STAGE_SAMPLE (TIMESTAMP integer, DEVICE_ID integer, USER_ID integer, STAGE integer);
        create table GARMIN_HRV_SUMMARY_SAMPLE (TIMESTAMP integer, DEVICE_ID integer, USER_ID integer,
                                                WEEKLY_AVERAGE integer, LAST_NIGHT_AVERAGE integer);
    """)
    con.execute("insert into DEVICE values (1, 'Synthetic Watch', ?)", (FAKE_MAC,))
    con.execute("insert into USER values (1, 'Synthetic User', 315532800000)")
    for n in nights:
        if not n.wearable_sleep_min:
            continue
        start, end = _sleep_window(n)
        for a, _, stage in _stages(start, end):
            con.execute("insert into GARMIN_SLEEP_STAGE_SAMPLE values (?,?,?,?)",
                        (int(a.timestamp() * 1000), 1, 1, LEVEL[stage]))
        con.execute("insert into GARMIN_SLEEP_STAGE_SAMPLE values (?,?,?,?)", (int(end.timestamp() * 1000), 1, 1, 1))
        con.execute("insert into GARMIN_HRV_SUMMARY_SAMPLE values (?,?,?,?,?)",
                    (int(end.timestamp() * 1000), 1, 1, 45, 42 + n.date.toordinal() % 9))
    con.commit()
    db = con.serialize()
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("database/Gadgetbridge", db)
        z.writestr("preferences/devicesettings_synthetic.xml", "<map/>")
    return buf.getvalue()


# ─── Collector (smart ring) export ───────────────────────────────────────────

def collector_json(nights) -> bytes:
    dev = f"r2n:{FAKE_MAC}"
    docs = []
    for n in nights:
        if not n.wearable_sleep_min:
            continue
        start, end = _sleep_window(n)
        for a, b, stage in _stages(start, end):
            key = int(a.timestamp() * 1000)
            docs.append({"id": f"{dev}/sleep.segment/{key}", "device_id": dev, "device_kind": "ring.r2n",
                         "type": "sleep.segment", "ts": a.isoformat(), "end_ts": b.isoformat(),
                         "payload": {"stage": stage}, "source": "collector/1.0.0"})
        t = start
        while t < end:
            key = int(t.timestamp() * 1000)
            hr = 52 + (t.minute // 5) % 7
            docs.append({"id": f"{dev}/vitals.hr/{key}", "device_id": dev, "device_kind": "ring.r2n",
                         "type": "vitals.hr", "ts": t.isoformat(), "end_ts": (t + timedelta(minutes=5)).isoformat(),
                         "payload": {"value": hr, "unit": "bpm"}, "source": "collector/1.0.0"})
            if t.minute % 30 == 0:
                docs.append({"id": f"{dev}/vitals.hrv/{key}", "device_id": dev, "device_kind": "ring.r2n",
                             "type": "vitals.hrv", "ts": t.isoformat(),
                             "payload": {"value": 40 + (t.hour % 6), "unit": "ms"}, "source": "collector/1.0.0"})
            t += timedelta(minutes=30)
    return json.dumps({"documents": docs}).encode()


# ─── Apple Health ────────────────────────────────────────────────────────────

def apple_export_zip(nights) -> bytes:
    fmt = "%Y-%m-%d %H:%M:%S %z"
    rows = [f'<Me HKCharacteristicTypeIdentifierDateOfBirth="{FAKE_DOB}" '
            'HKCharacteristicTypeIdentifierBiologicalSex="HKBiologicalSexNotSet"/>']
    for n in nights:
        if not n.wearable_sleep_min:
            continue
        start, end = _sleep_window(n)
        for src in ("Synthetic Watch", "Synthetic Phone"):           # two sources: must not double-count
            for a, b, stage in _stages(start, end):
                value = {"light": "AsleepCore", "deep": "AsleepDeep", "rem": "AsleepREM", "awake": "Awake"}[stage]
                rows.append(f'<Record type="HKCategoryTypeIdentifierSleepAnalysis" sourceName="{src}" '
                            f'startDate="{a.strftime(fmt)}" endDate="{b.strftime(fmt)}" '
                            f'value="HKCategoryValueSleepAnalysis{value}"/>')
        rows.append(f'<Record type="HKQuantityTypeIdentifierHeartRateVariabilitySDNN" sourceName="Synthetic Watch" '
                    f'unit="ms" startDate="{start.strftime(fmt)}" endDate="{start.strftime(fmt)}" value="45"/>')
        rows.append(f'<Record type="HKQuantityTypeIdentifierRestingHeartRate" sourceName="Synthetic Watch" '
                    f'unit="count/min" startDate="{end.strftime(fmt)}" endDate="{end.strftime(fmt)}" value="57"/>')
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n<HealthData locale="en_AE">\n'
           + "\n".join(rows) + "\n</HealthData>\n")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("apple_health_export/export.xml", xml)
        z.writestr("apple_health_export/export_cda.xml", "<ClinicalDocument/>")
    return buf.getvalue()


# ─── Fitbit / Google Takeout ─────────────────────────────────────────────────

def fitbit_json(nights) -> bytes:
    out = []
    for n in nights:
        if not n.wearable_sleep_min:
            continue
        start, end = _sleep_window(n)
        out.append({"logId": n.date.toordinal(), "dateOfSleep": end.date().isoformat(),
                    "startTime": start.strftime("%Y-%m-%dT%H:%M:%S.000"),
                    "endTime": end.strftime("%Y-%m-%dT%H:%M:%S.000"),
                    "minutesAsleep": int(n.wearable_sleep_min) - 20, "minutesAwake": 20,
                    "mainSleep": True, "type": "stages"})
    return json.dumps(out).encode()


def build_all() -> dict[str, bytes]:
    nights = _nights()
    from .ingest import to_csv
    return {
        "resmed_STR.edf": resmed_str_edf(nights),
        "resmed_sd_card.zip": resmed_card_zip(nights),
        "garmin_sleep_fit.zip": garmin_zip(nights[-30:]),
        "gadgetbridge_export.zip": gadgetbridge_zip(nights[-45:-15]),
        "collector_ring_export.json": collector_json(nights[-20:]),
        "apple_health_export.zip": apple_export_zip(nights[:30]),
        "fitbit_sleep-2026-09.json": fitbit_json(nights[:20]),
        "nights.csv": to_csv(nights[:10]).encode(),
    }
