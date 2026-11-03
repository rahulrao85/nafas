"""Translatable engine messages.

The engine emits `Msg` objects instead of plain strings. A `Msg` *is* a str (its English text), so logs,
tests and the care-team summary keep working. `Msg.render("ar")` gives the Arabic. Arabic is a first draft
for native clinical review (see docs/ASSUMPTIONS_LIMITATIONS.md).
"""

from __future__ import annotations

from datetime import date

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def dmy(d: date) -> str:
    return f"{d.day:02d}-{MONTHS[d.month - 1]}-{d.year}"


T: dict[str, dict[str, str]] = {
    # ── detections ──
    "lapse_missed": {"en": "No CPAP use for the last {n} nights.",
                     "ar": "لم يُستخدم الجهاز في آخر {n} ليالٍ."},
    "lapse_short": {"en": "{n} of the last 5 nights were under 4 hours.",
                    "ar": "{n} من آخر 5 ليالٍ كانت أقل من 4 ساعات."},
    "decline": {"en": "Average use fell from {b} h to {r} h a night (last {recent} nights vs the {base} before).",
                "ar": "انخفض متوسط الاستخدام من {b} إلى {r} ساعة في الليلة (آخر {recent} ليلة مقارنة بالـ {base} التي قبلها)."},
    "leak": {"en": "Large leak on {n} of the last {m} nights used (worst {worst} L/min; line is {line}).",
             "ar": "تسرب كبير في {n} من آخر {m} ليالٍ استُخدم فيها الجهاز (الأعلى {worst} لتر/دقيقة؛ الحد {line})."},
    "leak_creep": {"en": "Typical leak has crept up from {p} to {r} L/min over two weeks — often a cushion or headgear wearing out.",
                   "ar": "ارتفع التسرب المعتاد تدريجياً من {p} إلى {r} لتر/دقيقة خلال أسبوعين، وغالباً يعني ذلك اهتراء الوسادة أو الأحزمة."},
    "clinical": {"en": "Residual AHI was {line} or more on {n} of the last {m} nights. This is for your care team to review — "
                       "the app does not change therapy.",
                 "ar": "كان مؤشر AHI المتبقي {line} أو أكثر في {n} من آخر {m} ليالٍ. هذا لمراجعة فريق الرعاية، "
                       "والتطبيق لا يغيّر العلاج."},
    # ── barrier evidence ──
    "you_told": {"en": "You told us on {date}.", "ar": "أخبرتنا في {date}."},
    "leak_recent": {"en": "Large leak on recent nights.", "ar": "تسرب كبير في الليالي الأخيرة."},
    "leak_short": {"en": "{n} leaky night(s) were also short — a poor seal often wakes people.",
                   "ar": "{n} من ليالي التسرب كانت قصيرة أيضاً، فضعف الإحكام يوقظ كثيرين."},
    "removal": {"en": "On {n} recent nights the mask came off and on 3+ times and use stayed under 4 h.",
                "ar": "في {n} ليالٍ أخيرة نُزع القناع وأُعيد 3 مرات أو أكثر وبقي الاستخدام أقل من 4 ساعات."},
    "away": {"en": "No CPAP on {n} nights your watch recorded normal sleep — maybe you were away?",
             "ar": "لم يُستخدم الجهاز في {n} ليالٍ سجّلت فيها ساعتك نوماً طبيعياً. هل كنت مسافراً؟"},
    "bedtime_shift": {"en": "Bedtime moved by about {h} h compared with your usual.",
                      "ar": "تغيّر موعد نومك بنحو {h} ساعة عن المعتاد."},
    "weekend": {"en": "{n} of your short nights in 4 weeks were Friday/Saturday nights.",
                "ar": "{n} من لياليك القصيرة خلال 4 أسابيع كانت ليالي الجمعة أو السبت."},
    "pressure_high": {"en": "Pressure ran near its upper limit on short nights. Only your care team should change settings.",
                      "ar": "كان الضغط قريباً من حده الأعلى في الليالي القصيرة. فريق الرعاية وحده يغيّر الإعدادات."},
    "motivation": {"en": "Use is dropping and the data shows no mask or schedule problem.",
                   "ar": "الاستخدام يتراجع، ولا تُظهر البيانات مشكلة في القناع أو في المواعيد."},
    # ── outcomes of a step ──
    "judge_leak": {"en": "Leak under {line} L/min on {n} of the next {m} nights.",
                   "ar": "التسرب أقل من {line} لتر/دقيقة في {n} من الليالي الـ {m} التالية."},
    "judge_comeback": {"en": "Used on {n} of the next {m} nights (comeback).",
                       "ar": "استُخدم في {n} من الليالي الـ {m} التالية (عودة)."},
    "judge_goal": {"en": "Goal met on {n} of the next {m} nights.",
                   "ar": "تحقق الهدف في {n} من الليالي الـ {m} التالية."},
    "replanned": {"en": "You told us something else was in the way.",
                  "ar": "أخبرتنا أن شيئاً آخر كان العائق."},
    # ── nudges ──
    "nudge_off": {"en": "Nudges are off (your choice).", "ar": "التذكيرات متوقفة (باختيارك)."},
    "nudge_quiet": {"en": "Your nudge time falls inside quiet hours.", "ar": "وقت التذكير يقع ضمن ساعات الهدوء."},
    "nudge_ontrack": {"en": "On track — no nudge needed tonight.", "ar": "أنت على المسار، لا حاجة لتذكير الليلة."},
    "nudge_reduced": {"en": "You passed on the last three suggestions, so we've cut nudges to every other day.",
                      "ar": "تجاوزت آخر ثلاثة اقتراحات، لذا قلّلنا التذكير إلى يوم بعد يوم."},
    "nudge_one": {"en": "One nudge, at the time you chose.", "ar": "تذكير واحد في الوقت الذي اخترته."},
    "nudge_one_reduced": {"en": "One nudge, at the time you chose. Reduced frequency.",
                          "ar": "تذكير واحد في الوقت الذي اخترته، بتكرار أقل."},
    # ── triggers (history column) ──
    "trigger_lapse": {"en": "lapse", "ar": "انقطاع"},
    "trigger_decline": {"en": "decline", "ar": "تراجع"},
    "trigger_leak": {"en": "leak", "ar": "تسرب"},
    "trigger_leak_creep": {"en": "leak creep", "ar": "تسرب متزايد"},
    "trigger_self-report": {"en": "you told us", "ar": "أخبرتنا"},
}


class Msg(str):
    """A message that is its English text, and can render itself in another language."""

    key: str
    params: dict

    def __new__(cls, key: str, **params):
        obj = super().__new__(cls, _fmt(key, "en", params))
        obj.key, obj.params = key, params
        return obj

    def render(self, lang: str = "en") -> str:
        return _fmt(self.key, lang, self.params)

    def __reduce__(self):   # keep copy/pickle working for a str subclass with extra state
        return (_rebuild, (self.key, self.params))


def _rebuild(key, params):
    return Msg(key, **params)


def _fmt(key: str, lang: str, params: dict) -> str:
    tpl = T[key].get(lang) or T[key]["en"]
    shown = {k: (dmy(v) if isinstance(v, date) else v) for k, v in params.items()}
    return tpl.format(**shown)


def tr(x, lang: str = "en"):
    """Render a Msg (or a list of them) in `lang`; leave anything else as it is."""
    if isinstance(x, Msg):
        return x.render(lang)
    if isinstance(x, list):
        return [tr(i, lang) for i in x]
    return x
