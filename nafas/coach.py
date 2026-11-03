"""Coach note: the rules engine picks the action; the LLM (if allowed) only phrases it.

Flow: build a fact brief → ask the provider → run safety checks → show it, or fall back to the
fixed template. Clinician flags are never sent through the LLM; they use fixed wording.
"""

from __future__ import annotations

import json

from . import actions as lib
from .i18n import tr
from .llm import LLMError, LLMProvider
from .loop import LoopResult
from .safety import check_output

SYSTEM = """You write a short evening note for someone using CPAP therapy for sleep apnoea.
You receive a JSON brief prepared by a rules engine. Turn it into 2–4 short, warm sentences.

Rules:
- Write in the language given by "lang" ("en" English, "ar" Modern Standard Arabic). Plain text only.
- Acknowledge progress first using the numbers in the brief (banked nights never reset).
- If there's a setback, name it without blame. Never use words like fail, lazy or should have.
- Offer exactly the one action in the brief, in your own words. Add no other advice.
- Never mention pressure numbers or suggest changing pressure, medication, or stopping therapy.
- Never diagnose. You are not a clinician.
- Keep it under 90 words. No links, no emojis, no headings."""

UI = {
    "en": {"hi": "Hi {name}.", "banked": "You've banked {banked} good nights so far — that doesn't reset.",
           "run": "You're on a {run}-night run.", "noticed": "We noticed: {what}",
           "step": "Tonight's one small step: {title}. {step}",
           "ontrack": "Nothing to fix tonight. Same routine as last night.",
           "clinician": "One thing for your care team: {ev} Consider sharing your weekly view with them."},
    "ar": {"hi": "مرحباً {name}.", "banked": "لقد حققت {banked} ليلة جيدة حتى الآن، وهذا لا يُمحى.",
           "run": "أنت في سلسلة من {run} ليالٍ.", "noticed": "لاحظنا: {what}",
           "step": "خطوتك الصغيرة الليلة: {title}. {step}",
           "ontrack": "لا شيء يحتاج إلى إصلاح الليلة. استمر على روتين الليلة الماضية.",
           "clinician": "أمر لفريق الرعاية: {ev} يمكنك مشاركة العرض الأسبوعي معهم."},
}


def brief(r: LoopResult, lang: str) -> dict:
    iv = r.open_intervention
    rec = r.in_recovery
    last = r.nights[-1]
    b = {
        "lang": lang,
        "first_name": r.profile.display_name.split(" ")[0],
        "last_night_hours": round(last.usage_min / 60, 1),
        "banked_good_nights": r.momentum["banked_nights"],
        "current_run_nights": r.momentum["run"],
        "adherence_last_30_pct": r.momentum["adherence_30"],
        "situation": [d.kind for d in r.detections if d.kind != "clinical"] or ["on_track"],
        "in_comeback": bool(rec),
    }
    if rec:
        b["comeback_goal"] = lib.COMEBACK.get(lang, lib.COMEBACK["en"])
    if iv:
        act = lib.BY_ID[iv.action_id].render(lang)
        b["likely_barrier"] = {"label": iv.barrier.replace("_", " ").lower(), "source": iv.barrier_source}
        b["noticed"] = tr(iv.evidence[:2], lang)
        b["action"] = {"title": act["title"], "step": act["step"]}
    return b


def template(r: LoopResult, lang: str) -> str:
    t = UI.get(lang, UI["en"])
    bf = brief(r, lang)
    parts = [t["hi"].format(name=bf["first_name"]), t["banked"].format(banked=bf["banked_good_nights"])]
    if bf["current_run_nights"] >= 3:
        parts.append(t["run"].format(run=bf["current_run_nights"]))
    if bf["in_comeback"]:
        parts.append(bf["comeback_goal"])
    if "action" in bf:
        if bf.get("noticed"):
            parts.append(t["noticed"].format(what=bf["noticed"][0]))
        parts.append(t["step"].format(title=bf["action"]["title"], step=bf["action"]["step"]))
    elif not bf["in_comeback"]:
        parts.append(t["ontrack"])
    return " ".join(parts)


def clinician_note(r: LoopResult, lang: str) -> str | None:
    if not any(d.kind == "clinical" for d in r.detections):
        return None
    ev = tr(next(d.evidence[0] for d in r.detections if d.kind == "clinical"), lang)
    return UI.get(lang, UI["en"])["clinician"].format(ev=ev)


def compose(r: LoopResult, provider: LLMProvider, lang: str | None = None) -> dict:
    lang = lang or r.profile.language
    out = {"lang": lang, "clinician_note": clinician_note(r, lang), "llm": provider.describe()}
    if not r.profile.use_llm:
        return {**out, "text": template(r, lang), "source": "template",
                "fallback_reason": "You turned AI wording off in Settings."}
    try:
        text = provider.generate(SYSTEM, json.dumps(brief(r, lang), ensure_ascii=False))
    except LLMError as e:
        return {**out, "text": template(r, lang), "source": "template", "fallback_reason": str(e)}
    problems = check_output(text)
    if problems:
        return {**out, "text": template(r, lang), "source": "template",
                "fallback_reason": "AI draft failed safety checks: " + ", ".join(problems)}
    return {**out, "text": text, "source": f"llm:{provider.name}", "checks": "passed"}
