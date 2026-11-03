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
    # ── data checks ──
    "q_usage_missing": {"en": "{src}: {n} nights have no usage value, so we can't tell used from not used. They're left out.",
                        "ar": "{src}: لا توجد قيمة استخدام في {n} ليلة، فلا يمكن معرفة إن استُخدم الجهاز أم لا. تُركت جانباً."},
    "q_usage_hours": {"en": "{src}: every nightly-use value is 24 or less. If they're hours, rename the column usage_hours. "
                             "Until then they're read as minutes, so most nights look short.",
                      "ar": "{src}: كل قيم الاستخدام 24 أو أقل. إن كانت بالساعات فغيّر اسم العمود إلى usage_hours. "
                            "حتى ذلك الحين تُقرأ بالدقائق فتبدو معظم الليالي قصيرة."},
    "q_leak_lps": {"en": "{src}: leak values are all very low. If they're litres per second, rename the column leak95_lps. "
                         "Until then leak checks may miss a problem.",
                   "ar": "{src}: كل قيم التسرب منخفضة جداً. إن كانت باللتر في الثانية فغيّر اسم العمود إلى leak95_lps. "
                         "حتى ذلك الحين قد تفوت فحوص التسرب مشكلة."},
    "q_impossible_usage": {"en": "{src}: nightly use was impossible on {n} nights (over 24 h or negative). They count as not used.",
                           "ar": "{src}: كانت مدة الاستخدام مستحيلة في {n} ليلة (أكثر من 24 ساعة أو سالبة)، فتُحسب بلا استخدام."},
    "q_impossible": {"en": "{src}: {field} was impossible on {n} nights (out of range). Those values were ignored.",
                     "ar": "{src}: قيمة {field} مستحيلة في {n} ليلة (خارج المدى)، فتم تجاهلها."},
    "q_bad_rows": {"en": "{src}: {n} rows had an unreadable date and were left out.",
                   "ar": "{src}: {n} صفوف بتاريخ غير مقروء تُركت جانباً."},
    "q_duplicates": {"en": "{src}: {n} nights appeared twice. We kept the more complete record for each.",
                     "ar": "{src}: ظهرت {n} ليلة مرتين، فاحتفظنا بالسجل الأكمل لكل منها."},
    "q_conflict": {"en": "{n} nights came from two CPAP files with different values. We kept the SD card's.",
                   "ar": "جاءت {n} ليلة من ملفين مختلفين بقيم مختلفة، فاحتفظنا بقيم بطاقة SD."},
    "q_gap": {"en": "No record for {n} nights ({a} to {b}). They count as not used; if you did use CPAP, the card copy may be incomplete.",
              "ar": "لا يوجد سجل لـ {n} ليلة (من {a} إلى {b}). تُحسب كليالٍ بلا استخدام؛ إن كنت استخدمت الجهاز فقد تكون نسخة البطاقة ناقصة."},
    "q_no_ahi": {"en": "No AHI in your data, so the check that flags high residual events for your care team is off.",
                 "ar": "لا يوجد مؤشر AHI في بياناتك، لذا فحص الأحداث المتبقية المرتفعة لفريق الرعاية متوقف."},
    "q_no_leak": {"en": "No leak values, so the mask-leak and worn-cushion checks are off.",
                  "ar": "لا توجد قيم للتسرب، لذا فحوص تسرب القناع واهتراء الوسادة متوقفة."},
    "q_no_start": {"en": "No start times, so the changed-bedtime check is off.",
                   "ar": "لا توجد أوقات بدء، لذا فحص تغيّر موعد النوم متوقف."},
    "q_no_events": {"en": "No mask on/off counts, so the mask-off-at-night check is off.",
                    "ar": "لا يوجد عدد لمرات نزع القناع، لذا فحص نزعه أثناء الليل متوقف."},
    "q_no_wearable": {"en": "No watch or ring data, so Nafas can't tell a trip from a skipped night.",
                      "ar": "لا توجد بيانات ساعة أو خاتم، لذا لا يميّز نَفَس بين السفر والليلة الفائتة."},
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
    for k in ("field", "src"):          # codes that have a human label
        if k in shown and shown[k] in LABELS:
            shown[k] = LABELS[shown[k]].get(lang) or LABELS[shown[k]]["en"]
    return tpl.format(**shown)


LABELS: dict[str, dict[str, str]] = {
    "usage_min": {"en": "nightly use", "ar": "مدة الاستخدام"},
    "ahi": {"en": "AHI", "ar": "مؤشر AHI"},
    "leak95_lpm": {"en": "leak", "ar": "التسرب"},
    "pressure95": {"en": "pressure", "ar": "الضغط"},
    "mask_events": {"en": "mask on/off count", "ar": "عدد مرات نزع القناع"},
    "session_start": {"en": "start time", "ar": "وقت البدء"},
    "wearable_sleep_min": {"en": "watch/ring sleep", "ar": "نوم الساعة/الخاتم"},
    "wearable_rhr": {"en": "resting heart rate", "ar": "نبض الراحة"},
    "wearable_hrv_ms": {"en": "HRV", "ar": "HRV"},
    "resmed_str": {"en": "SD card", "ar": "بطاقة SD"},
    "nafas_csv": {"en": "CSV", "ar": "CSV"},
    "nafas_json": {"en": "JSON", "ar": "JSON"},
    "garmin_fit": {"en": "Garmin", "ar": "Garmin"},
    "gadgetbridge": {"en": "Gadgetbridge", "ar": "Gadgetbridge"},
    "collector": {"en": "ring", "ar": "الخاتم"},
    "apple_health": {"en": "Apple Health", "ar": "Apple Health"},
    "fitbit": {"en": "Fitbit", "ar": "Fitbit"},
}


def tr(x, lang: str = "en"):
    """Render a Msg (or a list of them) in `lang`; leave anything else as it is."""
    if isinstance(x, Msg):
        return x.render(lang)
    if isinstance(x, list):
        return [tr(i, lang) for i in x]
    return x
