"""Load nights from ResMed SD-card STR.edf, CSV, or JSON, and normalise them to `Night`.

The EDF reader is carried over from the original Sleep IQ build (Microsoft Agents League, 2026).
Uploaded files are parsed in memory and never written to disk by the server. Identifying fields in
the source (device serial, patient name) are dropped here: only the nightly numbers are kept.
"""

from __future__ import annotations

import csv
import io
import json
import struct
from datetime import date, datetime, timedelta

from .models import Night

EPOCH = date(1970, 1, 1)
_MONTHS = {m: i for i, m in enumerate(["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                                        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], start=1)}


def parse_date(s: str) -> date:
    s = str(s).strip()
    try:
        return date.fromisoformat(s[:10])
    except ValueError:
        pass
    d, m, y = s.split("-")           # DD-Mon-YYYY
    return date(int(y), _MONTHS[m[:3].title()], int(d))


def _f(v):
    if v in (None, ""):
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


# ─── ResMed STR.edf ──────────────────────────────────────────────────────────

def read_resmed_str(data: bytes) -> list[Night]:
    """Parse a ResMed STR.edf (one record per day) into nights."""
    if len(data) < 256 or not data[:1] == b"0":
        raise ValueError("Not an EDF file.")
    ns = int(data[252:256].decode("ascii").strip())
    header_bytes = int(data[184:192].decode("ascii").strip())

    def field(offset, width, i):
        return data[offset + i * width: offset + (i + 1) * width].decode("ascii", "replace").strip()

    o = 256
    labels = [field(o, 16, i) for i in range(ns)]; o += ns * 16
    o += ns * 80 + ns * 8                       # transducer, physical dimension
    pmin = [float(field(o, 8, i)) for i in range(ns)]; o += ns * 8
    pmax = [float(field(o, 8, i)) for i in range(ns)]; o += ns * 8
    dmin = [int(field(o, 8, i)) for i in range(ns)]; o += ns * 8
    dmax = [int(field(o, 8, i)) for i in range(ns)]; o += ns * 8
    o += ns * 80                                # prefiltering
    nsamp = [int(field(o, 8, i)) for i in range(ns)]
    rec_bytes = sum(nsamp) * 2
    if rec_bytes == 0:
        raise ValueError("Not a valid ResMed STR.edf file.")

    nights = []
    for r in range((len(data) - header_bytes) // rec_bytes):
        base, si, rec = header_bytes + r * rec_bytes, 0, {}
        for i, label in enumerate(labels):
            raw = struct.unpack_from(f"<{nsamp[i]}h", data, base + si * 2) if nsamp[i] else ()
            si += nsamp[i]
            span = dmax[i] - dmin[i]
            vals = [((v - dmin[i]) / span * (pmax[i] - pmin[i]) + pmin[i]) if span else float(v) for v in raw]
            rec[label] = vals if len(vals) > 1 else (vals[0] if vals else None)
        nights.append(_from_resmed_record(rec))
    return [n for n in nights if n is not None]


def _from_resmed_record(rec: dict) -> Night | None:
    d = rec.get("Date")
    if isinstance(d, list):
        d = d[0]
    if d is None:
        return None
    if isinstance(d, str):
        night_date = parse_date(d)
    else:
        night_date = EPOCH + timedelta(days=int(round(d)))
    def pos(label):   # ResMed writes -1 for "no value"
        v = _f(rec.get(label))
        return v if v is not None and v >= 0 else None

    # "Duration" is mask-on time (what adherence counts); "OnDuration" is machine-on time and can run longer.
    usage = (pos("Duration") if rec.get("Duration") is not None else pos("OnDuration")) or 0.0
    used = usage > 0
    leak = pos("Leak.95")
    ahi, press = pos("AHI"), pos("MaskPress.95")
    mask_on = rec.get("MaskOn")
    start = None
    if used and isinstance(mask_on, list) and mask_on and mask_on[0] is not None and mask_on[0] >= 0:
        start = (datetime(2000, 1, 1, 12) + timedelta(minutes=mask_on[0])).strftime("%H:%M")  # minutes from noon
    events = pos("MaskEvents")
    return Night(
        date=night_date, usage_min=round(usage, 1),
        ahi=round(ahi, 2) if used and ahi is not None else None,
        leak95_lpm=round(leak * 60, 1) if used and leak is not None else None,   # L/s → L/min
        pressure95=round(press, 2) if used and press is not None else None,
        mask_events=max(1, int(events // 2)) if used and events else (1 if used else 0),
        session_start=start,
    )


# ─── CSV / JSON ──────────────────────────────────────────────────────────────

CSV_COLUMNS = ["date", "usage_min", "ahi", "leak95_lpm", "pressure95", "mask_events", "session_start",
               "wearable_sleep_min", "wearable_rhr", "wearable_hrv_ms", "wearable_source"]


def _from_row(row: dict) -> Night:
    row = {k.strip().lower(): (v.strip() if isinstance(v, str) else v) for k, v in row.items() if k}
    usage = _f(row.get("usage_min"))
    if usage is None and _f(row.get("usage_hours")) is not None:
        usage = _f(row["usage_hours"]) * 60
    ev = _f(row.get("mask_events"))
    return Night(
        date=parse_date(row["date"]), usage_min=usage or 0.0, ahi=_f(row.get("ahi")),
        leak95_lpm=_f(row.get("leak95_lpm")), pressure95=_f(row.get("pressure95")),
        mask_events=int(ev) if ev is not None else None, session_start=row.get("session_start") or None,
        wearable_sleep_min=_f(row.get("wearable_sleep_min")), wearable_rhr=_f(row.get("wearable_rhr")),
        wearable_hrv_ms=_f(row.get("wearable_hrv_ms")), wearable_source=row.get("wearable_source") or None,
    )


def read_csv(text: str) -> list[Night]:
    rows = list(csv.DictReader(io.StringIO(text)))
    if not rows or "date" not in {k.strip().lower() for k in rows[0]}:
        raise ValueError("CSV needs a 'date' column. Template columns: " + ", ".join(CSV_COLUMNS))
    return [_from_row(r) for r in rows]


def read_json(text: str) -> list[Night]:
    obj = json.loads(text)
    if isinstance(obj, dict) and "records" in obj:          # original Sleep IQ export (ResMed keys)
        out = []
        for rec in obj["records"]:
            rec = dict(rec)
            if "DateFormatted" in rec:
                rec["Date"] = rec["DateFormatted"]
            n = _from_resmed_record(rec)
            if n:
                out.append(n)
        return out
    rows = obj.get("nights", obj) if isinstance(obj, dict) else obj
    return [_from_row({k: ("" if v is None else str(v)) for k, v in r.items()}) for r in rows]


def load_bytes(filename: str, data: bytes) -> list[Night]:
    name = filename.lower()
    if name.endswith(".edf"):
        nights = read_resmed_str(data)
    elif name.endswith(".csv"):
        nights = read_csv(data.decode("utf-8-sig"))
    elif name.endswith(".json"):
        nights = read_json(data.decode("utf-8-sig"))
    else:
        raise ValueError("Upload a ResMed STR.edf, a .csv or a .json file.")
    if not nights:
        raise ValueError("No nights found in the file.")
    return sorted(nights, key=lambda n: n.date)


def to_csv(nights: list[Night]) -> str:
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=CSV_COLUMNS)
    w.writeheader()
    for n in nights:
        w.writerow({k: ("" if v is None else v) for k, v in n.to_dict().items()})
    return buf.getvalue()
