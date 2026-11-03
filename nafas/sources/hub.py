"""Personal mode: read nights straight from a home hub's SQLite store (read-only), no upload.

Off unless NAFAS_PERSONAL_HUB=1 and NAFAS_HUB_DB points at the store. The path lives in a git-ignored
.env, never in code. The file is opened with SQLite's read-only URI, so Nafas can't change it, and no
token is needed.

What it reads (the hub's `ingest_documents` table, Collector ingest contract v1):
  cpap.night      one per night; payload carries usage_min, ahi, leak_95_lpm, press_95, mask_sessions
                  or mask_pairs (SD-card and myAir nights share this shape)
  sleep.segment   stage light/deep/rem/awake with ts/end_ts, from any device_kind
  vitals.hr/.hrv  overnight readings, from any device_kind

Wearable documents are grouped by device_kind: `ring.*` counts as the smart ring, and `watch.*` or anything
Garmin as the watch. A Gadgetbridge import that writes `sleep.segment` documents with a `watch.*` kind is
picked up with no change here.
"""

from __future__ import annotations

import json
import os
from contextlib import closing
import sqlite3
from datetime import date, datetime
from pathlib import Path

from ..models import Night
from ..quality import clean_cpap, clean_wearable
from . import Report, _add_wear, empty_wear, finish, wearables

WEAR_TYPES = ("sleep.segment", "vitals.hr", "vitals.hrv")


def enabled() -> bool:
    return os.getenv("NAFAS_PERSONAL_HUB") == "1" and bool(os.getenv("NAFAS_HUB_DB"))


def db_path() -> Path:
    return Path(os.environ["NAFAS_HUB_DB"])


def signature(path: Path) -> tuple:
    """Changes whenever the store does (the main file or its write-ahead log)."""
    out = []
    for p in (path, path.with_name(path.name + "-wal")):
        try:
            st = p.stat()
            out.append((st.st_mtime_ns, st.st_size))
        except OSError:
            out.append(None)
    return tuple(out)


def _connect(path: Path) -> sqlite3.Connection:
    con = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    return con


def _hhmm(sessions) -> str | None:
    for s in sessions or []:
        try:
            on, off = datetime.fromisoformat(s["on"]), datetime.fromisoformat(s["off"])
        except (KeyError, TypeError, ValueError):
            continue
        if off > on:
            return on.strftime("%H:%M")
    return None


def _num(v):
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def night_from_payload(p: dict) -> Night | None:
    try:
        d = date.fromisoformat(str(p.get("date"))[:10])
    except ValueError:
        return None
    sessions = p.get("mask_sessions")
    real = [s for s in sessions or [] if isinstance(s, dict) and s.get("on") != s.get("off")]
    events = len(real) if sessions is not None else (int(p["mask_pairs"]) if _num(p.get("mask_pairs")) else None)
    return Night(date=d, usage_min=_num(p.get("usage_min")), ahi=_num(p.get("ahi")),
                 leak95_lpm=_num(p.get("leak_95_lpm")), pressure95=_num(p.get("press_95")),
                 mask_events=events, session_start=_hhmm(sessions))


def _wear_kind(device_kind: str) -> str:
    k = (device_kind or "").lower()
    if k.startswith("ring."):
        return "collector"
    if k.startswith("watch.") or "garmin" in k or "gadgetbridge" in k:
        return "gadgetbridge"
    return "collector"


def load(path: Path | None = None) -> Report:
    path = path or db_path()
    rep = Report()
    with closing(_connect(path)) as con:
        rows = con.execute("SELECT payload FROM ingest_documents WHERE type = 'cpap.night'").fetchall()
        wear_rows = con.execute(
            f"SELECT device_kind, type, ts, end_ts, payload FROM ingest_documents WHERE type IN "
            f"({','.join('?' * len(WEAR_TYPES))})", WEAR_TYPES).fetchall()

    nights = [n for n in (night_from_payload(json.loads(r["payload"])) for r in rows) if n is not None]
    clean, warns = clean_cpap(nights, "hub", guess_units=False)
    rep.warnings.extend(warns)
    if nights:
        ds = sorted(n.date for n in nights)
        rep.found.append({"file": "hub", "source": "hub", "label": "Home hub (CPAP nights)", "files": 1,
                          "nights": len(ds), "first": ds[0].isoformat(), "last": ds[-1].isoformat()})

    wear = empty_wear()
    by_kind: dict[str, list[dict]] = {}
    for r in wear_rows:
        by_kind.setdefault(_wear_kind(r["device_kind"]), []).append(
            {"type": r["type"], "ts": r["ts"], "end_ts": r["end_ts"], "payload": json.loads(r["payload"])})
    for kind, docs in by_kind.items():
        got, warns = clean_wearable(wearables.parse_collector(docs), kind)
        rep.warnings.extend(warns)
        _add_wear(wear, kind, got)
        if got["sleep"]:
            ds = sorted(got["sleep"])
            rep.found.append({"file": "hub", "source": kind, "label": f"Home hub ({kind})", "files": 1,
                              "nights": len(ds), "first": ds[0].isoformat(), "last": ds[-1].isoformat()})
    return finish(rep, [("hub", clean)], wear)
