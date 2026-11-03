"""One-click ingest: take any mix of files, folders and zips, detect each source, merge into nights.

    report = ingest([("SD card/STR.edf", bytes), ("garmin.zip", bytes), ...], tz_offset_min=240)
    report.nights   → list[Night] (gap-free, sorted)
    report.found    → what each file gave
    report.skipped  → files we ignored, with a reason code (the UI translates the code)

CPAP data is required: wearable sleep is only useful next to CPAP hours (it powers the
"slept, but no CPAP — were you away?" check). Wearable nights outside the CPAP date range are dropped.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date

from ..engine import fill_gaps
from ..ingest import read_csv, read_json, read_resmed_str
from ..models import Night
from . import fit, wearables
from .archive import Budget, BudgetExceeded, Entry, expand, from_bytes

# Which wearable wins when several cover the same night (CSV values given explicitly win over all).
WEARABLE_PRIORITY = ["garmin_fit", "gadgetbridge", "collector", "apple_health", "fitbit"]

LABELS = {
    "resmed_str": "ResMed SD card (STR.edf)",
    "nafas_csv": "CSV",
    "nafas_json": "JSON nights",
    "garmin_fit": "Garmin watch (.fit)",
    "gadgetbridge": "Gadgetbridge export",
    "collector": "Smart ring (Collector export)",
    "apple_health": "Apple Health export",
    "fitbit": "Fitbit / Google sleep",
}

# Files on a ResMed card we skip on purpose. Identification.* and SETTINGS hold the device serial.
CARD_PRIVATE = ("identification.tgt", "identification.crc", "identification.json", "journal.dat")


@dataclass
class Report:
    nights: list[Night] = field(default_factory=list)
    found: list[dict] = field(default_factory=list)
    skipped: list[dict] = field(default_factory=list)
    error: str | None = None

    def summary(self) -> dict:
        if not self.nights:
            return {"nights": 0}
        cpap = [n for n in self.nights if n.usage_min > 0]
        wear = [n for n in self.nights if n.wearable_sleep_min]
        return {"nights": len(self.nights), "first": self.nights[0].date.isoformat(),
                "last": self.nights[-1].date.isoformat(), "cpap_nights_used": len(cpap),
                "wearable_nights": len(wear)}

    def to_dict(self) -> dict:
        counts: dict[str, int] = {}
        for s in self.skipped:
            counts[s["reason"]] = counts.get(s["reason"], 0) + 1
        return {"found": self.found, "skipped": self.skipped[:200], "skipped_counts": counts,
                "summary": self.summary(), "error": self.error}


def _classify(e: Entry) -> str | None:
    """Source kind for a file, or None to skip. Raises nothing; peeks at most 64 bytes."""
    low, path = e.name.lower(), e.path.lower().replace("\\", "/")
    if low.endswith("str.edf"):
        return "resmed_str"
    if low.endswith(".edf"):
        return "skip:datalog"
    if low in CARD_PRIVATE or "/settings/" in f"/{path}" or low.endswith((".tgt", ".crc")):
        return "skip:device_identity"
    head = e.head(64)
    if low.endswith(".fit") or fit.is_fit(head):
        return "garmin_fit"
    if wearables.is_sqlite(head):
        return "gadgetbridge"
    if low in ("export.xml", "exportación.xml", "export_cda.xml") or (low.endswith(".xml") and b"<HealthData" in e.head(4096)):
        return "skip:apple_cda" if low == "export_cda.xml" else "apple_health"
    if low.endswith(".json"):
        return "json"
    if low.endswith(".csv"):
        return "nafas_csv"
    return "skip:unknown"


def _sniff_json(data: bytes) -> tuple[str, object]:
    obj = json.loads(data.decode("utf-8-sig"))
    if wearables.is_collector(obj):
        return "collector", obj
    if wearables.is_fitbit(obj):
        return "fitbit", obj
    return "nafas_json", obj


def ingest(files: list[tuple[str, bytes]], tz_offset_min: int = 0, pre_skipped: list[dict] | None = None) -> Report:
    rep = Report(skipped=list(pre_skipped or []))
    budget = Budget()
    cpap: dict[date, Night] = {}
    wear: dict[str, dict] = {k: {"sleep": {}, "hrv": {}, "rhr": {}} for k in WEARABLE_PRIORITY}

    groups: dict[tuple[str, str], dict] = {}

    def note(path, kind, nights_dict_or_list):
        # One row per source per uploaded folder or zip, not one per file (a watch writes a file a night).
        root = top_path.replace("\\", "/").split("/")[0]
        g = groups.setdefault((root, kind), {"file": root, "source": kind, "label": LABELS.get(kind, kind),
                                             "files": 0, "dates": set()})
        g["files"] += 1
        g["dates"] |= set(nights_dict_or_list)

    for top_path, data in files:
        try:
            for e in expand(from_bytes(top_path, data), budget, rep.skipped):
                kind = _classify(e)
                if kind is None or kind.startswith("skip:"):
                    rep.skipped.append({"file": e.path, "reason": kind.split(":", 1)[1] if kind else "unknown"})
                    continue
                try:
                    if kind == "apple_health":
                        with e.open() as fh:
                            got = wearables.parse_apple(fh)
                        _add_wear(wear, kind, got)
                        note(e.path, kind, got["sleep"])
                        continue
                    raw = e.read(budget)
                    if kind == "json":
                        kind, obj = _sniff_json(raw)
                    if kind == "resmed_str":
                        ns = read_resmed_str(raw)
                        for n in ns:
                            if n.usage_min > 0 or n.date not in cpap:
                                cpap[n.date] = n
                        note(e.path, kind, [n.date for n in ns])
                    elif kind in ("nafas_csv", "nafas_json"):
                        ns = read_csv(raw.decode("utf-8-sig")) if kind == "nafas_csv" else read_json(raw.decode("utf-8-sig"))
                        for n in ns:
                            cpap[n.date] = n
                        note(e.path, kind, [n.date for n in ns])
                    elif kind == "garmin_fit":
                        got = fit.parse(raw, tz_offset_min)
                        if not any(got.values()):
                            rep.skipped.append({"file": e.path, "reason": "fit_no_sleep"})
                            continue
                        _add_wear(wear, kind, got)
                        note(e.path, kind, set(got["sleep"]) | set(got["hrv"]) | set(got["rhr"]))
                    elif kind == "gadgetbridge":
                        got = wearables.parse_gadgetbridge_db(raw, tz_offset_min)
                        _add_wear(wear, kind, got)
                        note(e.path, kind, got["sleep"])
                    elif kind == "collector":
                        got = wearables.parse_collector(obj)
                        _add_wear(wear, kind, got)
                        note(e.path, kind, got["sleep"])
                    elif kind == "fitbit":
                        got = wearables.parse_fitbit(obj)
                        _add_wear(wear, kind, got)
                        note(e.path, kind, got["sleep"])
                except BudgetExceeded:
                    raise
                except Exception as ex:  # noqa: BLE001 - one bad file must not sink the upload
                    rep.skipped.append({"file": e.path, "reason": "unreadable", "detail": type(ex).__name__})
        except BudgetExceeded as ex:
            rep.skipped.append({"file": top_path, "reason": "too_large", "detail": str(ex)})

    for g in groups.values():
        ds = sorted(g.pop("dates"))
        rep.found.append({**g, "nights": len(ds), "first": ds[0].isoformat() if ds else None,
                          "last": ds[-1].isoformat() if ds else None})
    if not cpap:
        rep.error = "no_cpap"
        return rep
    rep.nights = _merge(cpap, wear, rep)
    return rep


def _add_wear(wear: dict, kind: str, got: dict) -> None:
    for k in ("sleep", "hrv", "rhr"):
        for n, v in got[k].items():
            if v is not None:
                wear[kind][k][n] = v


def _merge(cpap: dict[date, Night], wear: dict, rep: Report) -> list[Night]:
    first, last = min(cpap), max(cpap)
    nights = {n.date: n for n in fill_gaps(list(cpap.values()))}
    outside = 0
    for kind in reversed(WEARABLE_PRIORITY):          # lower priority first, higher overwrites
        w = wear[kind]
        for field_, attr in (("sleep", "wearable_sleep_min"), ("hrv", "wearable_hrv_ms"), ("rhr", "wearable_rhr")):
            for d, v in w[field_].items():
                if not (first <= d <= last):
                    outside += field_ == "sleep"
                    continue
                n = nights[d]
                if getattr(n, attr) is None or n.wearable_source in WEARABLE_PRIORITY:
                    setattr(n, attr, v)
                    n.wearable_source = kind
    if outside:
        rep.skipped.append({"file": "—", "reason": "wearable_outside_cpap", "detail": str(outside)})
    return [nights[d] for d in sorted(nights)]
