"""Flask API + single-page UI.

State lives in memory, per browser session, and disappears when the server stops. Nothing is written to disk.
"""

from __future__ import annotations

import json
import os
import secrets
import time
from collections import defaultdict
from datetime import date
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory, session

from . import actions as lib
from . import coach, synthetic
from .barriers import BARRIERS
from .barriers import label as barrier_label
from .engine import fill_gaps, status_of
from .ingest import CSV_COLUMNS, to_csv
from .sources import hub
from .sources import ingest as ingest_sources
from .i18n import dmy, tr
from .llm import get_provider
from .loop import run
from .models import CheckIn, Profile
from .outcomes import cohort_report, person_outcomes
from .safety import crisis_check
from .weekly import weekly_view

STATIC = Path(__file__).parent / "static"
MAX_UPLOAD_MB = 64
MAX_FILES = 2500
SETTINGS_FIELDS = {"goal_hours": float, "language": str, "nudges_enabled": bool, "nudge_hour": int,
                   "quiet_start": int, "quiet_end": int, "share_with_care_team": bool, "use_llm": bool}

_BASE: dict[str, dict] = {}
_SESSIONS: dict[str, dict] = defaultdict(lambda: {"overlay": {}, "uploads": {}, "calls": []})
_COHORT: dict = {}


def _base(pid: str) -> dict:
    if pid not in _BASE:
        p = synthetic.PERSONAS[pid]()
        p["nights"] = fill_gaps(p["nights"])
        _BASE[pid] = p
    return _BASE[pid]


def _sid() -> str:
    if "sid" not in session:
        session["sid"] = secrets.token_hex(16)
    return session["sid"]


_HUB: dict = {}
HUB_ID = "hub"


def _hub_data() -> dict | None:
    """Personal mode only: the hub's nights, re-read whenever the store changes."""
    if not hub.enabled():
        return None
    path = hub.db_path()
    sig = hub.signature(path)
    if _HUB.get("sig") != sig:
        try:
            rep = hub.load(path)
        except Exception as e:  # noqa: BLE001 - a missing or locked store must not take the app down
            _HUB.update(sig=None, data=None, error=f"{type(e).__name__}")
            return None
        if rep.error:
            _HUB.update(sig=sig, data=None, error=rep.error)
            return None
        n = rep.nights
        first, last = dmy(n[0].date), dmy(n[-1].date)
        _HUB.update(sig=sig, error=None, data={
            "profile": Profile(id=HUB_ID, display_name="My data (hub)",
                               notes="Read from the home hub on every load; never stored by Nafas."),
            "nights": n, "checkins": [], "warnings": rep.warnings,
            "story": {"en": f"My data from the home hub: {len(n)} nights, {first} to {last}.",
                      "ar": f"بياناتي من المحور المنزلي: {len(n)} ليلة، من {first} إلى {last}."}})
    return _HUB.get("data")


def _persona(pid: str) -> tuple[dict, dict]:
    """Return (persona data, this session's overlay for it)."""
    s = _SESSIONS[_sid()]
    if pid == HUB_ID and _hub_data() is not None:
        data = _hub_data()
    elif pid in s["uploads"]:
        data = s["uploads"][pid]
    elif pid in synthetic.PERSONAS:
        data = _base(pid)
    else:
        raise KeyError(pid)
    ov = s["overlay"].setdefault(pid, {"checkins": [], "events": [], "settings": {}})
    return data, ov


def _profile(data: dict, ov: dict) -> Profile:
    p = Profile.from_dict({**data["profile"].to_dict(), **ov["settings"]})
    return p


def _as_of(data: dict) -> date:
    raw = request.values.get("as_of") or (request.get_json(silent=True) or {}).get("as_of")
    last = data["nights"][-1].date
    first = data["nights"][0].date
    if not raw:
        return last
    d = date.fromisoformat(raw)
    return min(max(d, first), last)


def _result(pid: str, as_of: date | None = None):
    data, ov = _persona(pid)
    prof = _profile(data, ov)
    checkins = list(data.get("checkins", [])) + [CheckIn.from_dict(c) for c in ov["checkins"]]
    return run(prof, data["nights"], checkins, ov["events"], as_of=as_of), data, ov


def _rate_limited(limit: int = 20, window: int = 60) -> bool:
    calls = _SESSIONS[_sid()]["calls"]
    now = time.time()
    calls[:] = [t for t in calls if now - t < window]
    if len(calls) >= limit:
        return True
    calls.append(now)
    return False


def _story(data: dict, lang: str) -> str:
    s = data.get("story", "")
    return s.get(lang) or s.get("en", "") if isinstance(s, dict) else s


def state_json(pid: str, as_of: date) -> dict:
    r, data, ov = _result(pid, as_of)
    lang = r.profile.language
    goal_min = max(60.0, r.profile.goal_hours * 60)
    iv = r.open_intervention
    rec = r.in_recovery
    flag = next((f for f in reversed(r.clinician_flags)
                 if (r.as_of - date.fromisoformat(f["date"])).days <= 14), None)
    last = r.nights[-1]
    return {
        "persona": {"id": pid, "display_name": r.profile.display_name, "story": _story(data, lang),
                    "notes": r.profile.notes, "mask_type": r.profile.mask_type,
                    "uploaded": pid in _SESSIONS[_sid()]["uploads"] or pid == HUB_ID},
        "profile": r.profile.to_dict(),
        "range": {"first": data["nights"][0].date.isoformat(), "last": data["nights"][-1].date.isoformat()},
        "as_of": r.as_of.isoformat(),
        "last_night": {**last.to_dict(), "status": status_of(last, goal_min), "hours": round(last.usage_min / 60, 1)},
        "momentum": r.momentum,
        "detections": [d.to_dict(lang) for d in r.detections],
        "barriers": [b.to_dict(lang) for b in r.barriers],
        "intervention": iv.to_dict(lang) if iv else None,
        "recovery": {"active": True, **rec.to_dict(), "goal_text": lib.COMEBACK.get(lang, lib.COMEBACK["en"]),
                     "goal_min": lib.COMEBACK_GOAL_MIN} if rec else {"active": False},
        "clinician_flag": {"date": flag["date"], "evidence": tr(flag["evidence"], lang)} if flag else None,
        "nudge": {**r.nudge, "reason": tr(r.nudge.get("reason"), lang)},
        "weekly": weekly_view(r, 12),
        "series": [{"date": n.date.isoformat(), "hours": round(n.usage_min / 60, 2), "leak": n.leak95_lpm,
                    "ahi": n.ahi, "status": status_of(n, goal_min)} for n in r.nights[-90:]],
        "history": [x.to_dict(lang) for x in reversed(r.interventions[-40:])],
        "lapses": [l.to_dict() for l in r.lapses],
        "learner": [{**row, "title": lib.BY_ID[row["action_id"]].render(lang)["title"],
                     "bct": lib.BY_ID[row["action_id"]].bct} for row in r.learner.summary()],
        "outcomes": person_outcomes(r),
        "checkins": [c.to_dict() for c in (data.get("checkins", []))] + ov["checkins"],
        "barrier_options": [{"code": k, "label": barrier_label(k, lang)} for k in BARRIERS],
        "llm": get_provider().describe(),
        "data_warnings": [w.to_dict(lang) for w in data.get("warnings", [])],
    }


def create_app() -> Flask:
    app = Flask(__name__, static_folder=None)
    app.secret_key = os.getenv("NAFAS_SECRET") or secrets.token_hex(32)
    app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_MB * 1024 * 1024   # an SD-card or watch export zip
    app.config["MAX_FORM_PARTS"] = 3000                               # a card folder picked file by file
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["SESSION_COOKIE_HTTPONLY"] = True

    @app.errorhandler(KeyError)
    def _unknown(e):
        return jsonify(error=f"Unknown persona {e}"), 404

    @app.errorhandler(ValueError)
    def _bad(e):
        return jsonify(error=str(e)), 400

    @app.get("/")
    def index():
        return send_from_directory(STATIC, "index.html")

    @app.get("/static/<path:name>")
    def static_files(name):
        return send_from_directory(STATIC, name)

    @app.get("/api/personas")
    def personas():
        out = []
        h = _hub_data()
        if h is not None:
            out.append({"id": HUB_ID, "display_name": h["profile"].display_name, "story": _story(h, "en"),
                        "nights": len(h["nights"]), "synthetic": False})
        for pid in synthetic.PERSONAS:
            d = _base(pid)
            out.append({"id": pid, "display_name": d["profile"].display_name, "story": _story(d, "en"),
                        "nights": len(d["nights"]), "synthetic": True})
        for pid, d in _SESSIONS[_sid()]["uploads"].items():
            out.append({"id": pid, "display_name": d["profile"].display_name, "story": _story(d, "en"),
                        "nights": len(d["nights"]), "synthetic": False})
        return jsonify(personas=out, llm=get_provider().describe())

    @app.get("/api/state")
    def state():
        pid = request.args.get("persona", "layla")
        data, _ = _persona(pid)
        return jsonify(state_json(pid, _as_of(data)))

    @app.post("/api/checkin")
    def checkin():
        body = request.get_json(force=True)
        pid = body["persona"]
        data, ov = _persona(pid)
        d = _as_of(data)
        barrier = body.get("barrier")
        note = (body.get("note") or "")[:280]
        lang = _profile(data, ov).language
        urgent = crisis_check(note, lang)
        if barrier and barrier not in BARRIERS:
            raise ValueError("Unknown barrier.")
        if barrier:
            ov["checkins"] = [c for c in ov["checkins"] if c["date"] != d.isoformat()]
            ov["checkins"].append({"date": d.isoformat(), "barrier": barrier, "note": note})
        return jsonify(urgent=urgent, state=state_json(pid, d))

    @app.post("/api/action")
    def action():
        body = request.get_json(force=True)
        pid, kind = body["persona"], body["type"]
        if kind not in ("swap", "accept", "dismiss"):
            raise ValueError("type must be swap, accept or dismiss")
        data, ov = _persona(pid)
        d = _as_of(data)
        ov["events"].append({"type": kind, "date": d.isoformat(), "intervention_id": body["intervention_id"]})
        return jsonify(state_json(pid, d))

    @app.post("/api/settings")
    def settings():
        body = request.get_json(force=True)
        pid = body["persona"]
        data, ov = _persona(pid)
        for k, cast in SETTINGS_FIELDS.items():
            if k in body:
                ov["settings"][k] = cast(body[k])
        s = ov["settings"]
        if "goal_hours" in s:
            s["goal_hours"] = min(10.0, max(1.0, s["goal_hours"]))
        if s.get("language") not in (None, "en", "ar"):
            s["language"] = "en"
        for k in ("nudge_hour", "quiet_start", "quiet_end"):
            if k in s:
                s[k] = int(s[k]) % 24
        return jsonify(state_json(pid, _as_of(data)))

    @app.post("/api/coach")
    def coach_note():
        if _rate_limited():
            return jsonify(error="Too many requests — try again in a minute."), 429
        body = request.get_json(force=True)
        pid = body["persona"]
        data, _ = _persona(pid)
        r, _, _ = _result(pid, _as_of(data))
        return jsonify(coach.compose(r, get_provider(), body.get("lang")))

    @app.get("/api/care-team-summary")
    def care_team_summary():
        pid = request.args["persona"]
        data, ov = _persona(pid)
        r, _, _ = _result(pid, _as_of(data))
        if not r.profile.share_with_care_team:
            return jsonify(error="Sharing with your care team is off. Turn it on in Settings first."), 403
        o = person_outcomes(r)
        return jsonify({
            "name": r.profile.display_name, "as_of": r.as_of.isoformat(), "goal_hours": r.profile.goal_hours,
            "momentum": r.momentum, "outcomes": o, "clinician_flags": r.clinician_flags[-3:],
            "lapses": [l.to_dict() for l in r.lapses[-5:]],
            "actions_tried": [{"start": iv.start.isoformat(), "barrier": iv.barrier,
                               "action": lib.BY_ID[iv.action_id].title["en"], "status": iv.status}
                              for iv in r.interventions[-10:]],
            "note": "Generated by Nafas (prototype). Patterns only — not a diagnosis.",
        })

    @app.post("/api/upload")
    def upload():
        """Any mix of files and zips (a whole SD card, watch and ring exports). Detects, merges, reports."""
        files = request.files.getlist("files") or request.files.getlist("file")
        files = [f for f in files if f and f.filename]
        if not files:
            raise ValueError("Choose at least one file.")
        if len(files) > MAX_FILES:
            raise ValueError(f"Too many files at once (max {MAX_FILES}). Zip the folder instead.")
        try:
            paths = json.loads(request.form.get("paths") or "[]")
            pre_skipped = json.loads(request.form.get("skipped") or "[]")[:500]
            tz = int(request.form.get("tz_offset_min") or 0)
        except (ValueError, TypeError):
            raise ValueError("Bad upload form.")
        tz = max(-14 * 60, min(14 * 60, tz))
        items = []
        for i, f in enumerate(files):
            p = paths[i] if i < len(paths) and isinstance(paths[i], str) and paths[i] else f.filename
            items.append((p[:300], f.read()))
        pre = [{"file": str(s.get("file", ""))[:300], "reason": str(s.get("reason", "unknown"))[:40]}
               for s in pre_skipped if isinstance(s, dict)]
        return _store_upload(ingest_sources(items, tz_offset_min=tz, pre_skipped=pre), "Your data")

    @app.post("/api/upload-samples")
    def upload_samples():
        """Demo: the same one-click path, fed with the synthetic sample file for every source."""
        from .samples import build_all
        return _store_upload(ingest_sources(list(build_all().items()), tz_offset_min=240), "Sample files")

    def _store_upload(rep, name: str):
        lang = request.form.get("lang", "en")
        if rep.error:
            return jsonify(persona=None, report=rep.to_dict(lang)), 422
        nights = rep.nights
        s = _SESSIONS[_sid()]
        pid = f"upload{len(s['uploads']) + 1}"
        first, last = dmy(nights[0].date), dmy(nights[-1].date)
        s["uploads"][pid] = {
            "profile": Profile(id=pid, display_name=name, notes="Uploaded this session; held in memory only."),
            "nights": nights, "checkins": [], "warnings": rep.warnings,
            "story": {"en": f"{name}: {len(nights)} nights, {first} to {last}.",
                      "ar": f"{'بياناتك' if name == 'Your data' else 'ملفات نموذجية'}: {len(nights)} ليلة، من {first} إلى {last}."},
        }
        return jsonify(persona=pid, nights=len(nights), report=rep.to_dict(lang))

    @app.get("/api/csv-template")
    def csv_template():
        sample = _base("layla")["nights"][-7:]
        return app.response_class(to_csv(sample), mimetype="text/csv",
                                  headers={"Content-Disposition": "attachment; filename=nafas_template.csv"})

    @app.post("/api/forget")
    def forget():
        _SESSIONS.pop(_sid(), None)
        session.clear()
        return jsonify(ok=True, message="Everything from this session has been deleted.")

    @app.get("/api/cohort")
    def cohort():
        if "report" not in _COHORT:
            _COHORT["report"] = cohort_report(synthetic.cohort())
        return jsonify(_COHORT["report"])

    @app.get("/api/health")
    def health():
        return jsonify(ok=True, csv_columns=CSV_COLUMNS, llm=get_provider().describe())

    return app


app = create_app()
