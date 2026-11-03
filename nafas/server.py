"""Flask API + single-page UI.

State lives in memory, per browser session, and disappears when the server stops. Nothing is written to disk.
"""

from __future__ import annotations

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
from .ingest import CSV_COLUMNS, load_bytes, to_csv
from .llm import get_provider
from .loop import run
from .models import CheckIn, Profile
from .outcomes import cohort_report, person_outcomes
from .safety import crisis_check
from .weekly import weekly_view

STATIC = Path(__file__).parent / "static"
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


def _persona(pid: str) -> tuple[dict, dict]:
    """Return (persona data, this session's overlay for it)."""
    s = _SESSIONS[_sid()]
    if pid in s["uploads"]:
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
        "persona": {"id": pid, "display_name": r.profile.display_name, "story": data.get("story", ""),
                    "notes": r.profile.notes, "mask_type": r.profile.mask_type,
                    "uploaded": pid in _SESSIONS[_sid()]["uploads"]},
        "profile": r.profile.to_dict(),
        "range": {"first": data["nights"][0].date.isoformat(), "last": data["nights"][-1].date.isoformat()},
        "as_of": r.as_of.isoformat(),
        "last_night": {**last.to_dict(), "status": status_of(last, goal_min), "hours": round(last.usage_min / 60, 1)},
        "momentum": r.momentum,
        "detections": [d.to_dict() for d in r.detections],
        "barriers": [b.to_dict(lang) for b in r.barriers],
        "intervention": iv.to_dict(lang) if iv else None,
        "recovery": {"active": True, **rec.to_dict(), "goal_text": lib.COMEBACK.get(lang, lib.COMEBACK["en"]),
                     "goal_min": lib.COMEBACK_GOAL_MIN} if rec else {"active": False},
        "clinician_flag": flag,
        "nudge": r.nudge,
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
    }


def create_app() -> Flask:
    app = Flask(__name__, static_folder=None)
    app.secret_key = os.getenv("NAFAS_SECRET") or secrets.token_hex(32)
    app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024
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
        for pid in synthetic.PERSONAS:
            d = _base(pid)
            out.append({"id": pid, "display_name": d["profile"].display_name, "story": d["story"],
                        "nights": len(d["nights"]), "synthetic": True})
        for pid, d in _SESSIONS[_sid()]["uploads"].items():
            out.append({"id": pid, "display_name": d["profile"].display_name, "story": d["story"],
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
        f = request.files.get("file")
        if not f or not f.filename:
            raise ValueError("Choose a file to upload.")
        nights = fill_gaps(load_bytes(f.filename, f.read()))
        s = _SESSIONS[_sid()]
        pid = f"upload{len(s['uploads']) + 1}"
        s["uploads"][pid] = {
            "profile": Profile(id=pid, display_name="Your data", notes="Uploaded this session; held in memory only."),
            "nights": nights, "checkins": [],
            "story": f"Your upload: {len(nights)} nights, {nights[0].date:%d-%b-%Y} to {nights[-1].date:%d-%b-%Y}.",
        }
        return jsonify(persona=pid, nights=len(nights))

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
