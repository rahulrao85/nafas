"""Action library: barrier -> one small action, each tagged with a behaviour-change technique.

BCT codes refer to the BCT Taxonomy v1 (Michie et al., 2013). Every action states why it should help
and where it stops helping, so the person (and a reviewer) can see the reasoning and its limits.

Rules the library keeps:
- Never tell anyone to change prescribed pressure. Pressure problems go to the care team.
- Comfort settings (humidity, ramp) only "if your care team has made them adjustable".
- Small: each action fits in one evening or one message.

Arabic text is a first draft and needs review by a native speaker with clinical vocabulary
before any real-user exposure (see docs/ASSUMPTIONS_LIMITATIONS.md).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Action:
    id: str
    barrier: str
    title: dict          # {"en": ..., "ar": ...}
    step: dict           # the one small action
    bct: str             # e.g. "4.1"
    bct_name: str
    rationale: str
    limits: str
    care_team: bool = False   # involves contacting the care team / equipment provider

    def render(self, lang: str = "en") -> dict:
        lang = lang if lang in self.title else "en"
        return {
            "id": self.id, "barrier": self.barrier,
            "title": self.title[lang], "step": self.step[lang],
            "bct": self.bct, "bct_name": self.bct_name,
            "rationale": self.rationale, "limits": self.limits,
            "care_team": self.care_team, "lang": lang,
        }


def A(id, barrier, title_en, title_ar, step_en, step_ar, bct, bct_name, rationale, limits, care_team=False):
    return Action(id, barrier, {"en": title_en, "ar": title_ar}, {"en": step_en, "ar": step_ar},
                  bct, bct_name, rationale, limits, care_team)


LIBRARY: list[Action] = [
    # ── Mask fit / seal ─────────────────────────────────────────────────────
    A("fit_lie_down", "MASK_FIT",
      "Re-seat the mask lying down", "أعد ضبط القناع وأنت مستلقٍ",
      "Tonight, put the mask on lying in your sleep position, start the machine, then loosen or shift the straps "
      "until the hissing stops. Looser usually seals better than tighter.",
      "الليلة، ضع القناع وأنت مستلقٍ في وضعية نومك، شغّل الجهاز، ثم أرخِ الأحزمة أو حرّكها حتى يتوقف صوت التسرب. "
      "الشد الخفيف يُحكم الإغلاق غالباً أفضل من الشد القوي.",
      "4.1", "Instruction on how to perform the behaviour",
      "Faces change shape lying down, and over-tightening folds the cushion and causes leaks.",
      "Won't fix a mask that is the wrong size or style; if leaks persist after 3 nights we suggest a refit."),
    A("fit_mask_check", "MASK_FIT",
      "Run a one-minute fit check", "أجرِ فحص ملاءمة لمدة دقيقة",
      "Before sleep, use your machine's mask-fit test (if it has one) and adjust until it shows a good seal.",
      "قبل النوم، استخدم اختبار ملاءمة القناع في جهازك (إن وُجد) واضبطه حتى يُظهر إحكاماً جيداً.",
      "2.2", "Feedback on behaviour",
      "Immediate feedback turns a vague 'it leaks' into something you can fix in the moment.",
      "Not every device has a fit test; the check is done awake, and seals can shift during sleep."),
    A("fit_refit", "MASK_FIT",
      "Ask for a mask refit", "اطلب إعادة ملاءمة القناع",
      "Send your equipment provider one line: \"I'm getting large leaks most nights — can I try a different size or style?\"",
      "أرسل إلى مزوّد الجهاز سطراً واحداً: \"لديّ تسرب كبير معظم الليالي، هل يمكنني تجربة مقاس أو نوع آخر؟\"",
      "3.2", "Social support (practical)",
      "Mask choice is the most common fixable cause of leak; a fitter has sizes you can try.",
      "Needs an appointment or message to your provider; the app does not contact anyone for you.",
      care_team=True),

    # ── Worn cushion ────────────────────────────────────────────────────────
    A("wear_wash", "MASK_WEAR",
      "Wash the cushion this morning", "اغسل وسادة القناع هذا الصباح",
      "Wash the cushion with mild soap and warm water and let it air-dry before tonight.",
      "اغسل وسادة القناع بصابون لطيف وماء دافئ واتركها تجف في الهواء قبل الليل.",
      "4.1", "Instruction on how to perform the behaviour",
      "Skin oils soften silicone and break the seal; a clean cushion often seals again.",
      "Washing won't revive a cushion that has torn or lost its shape."),
    A("wear_swap", "MASK_WEAR",
      "Swap in a spare cushion", "استبدل الوسادة بأخرى احتياطية",
      "If you have a spare cushion, put it on tonight and see if the leak line drops. If not, add 'order cushion' to your list.",
      "إذا كانت لديك وسادة احتياطية، ركّبها الليلة ولاحظ إن انخفض التسرب. وإن لم تكن، أضف \"طلب وسادة\" إلى قائمتك.",
      "12.5", "Adding objects to the environment",
      "A slow rise in leak over weeks is the typical signature of a cushion wearing out.",
      "Replacement schedules depend on your provider or insurer; we don't set one."),
    A("wear_order", "MASK_WEAR",
      "Order a replacement", "اطلب قطعة بديلة",
      "Message your equipment provider to order a new cushion (and headgear if the straps feel stretched).",
      "راسل مزوّد الجهاز لطلب وسادة جديدة (وأحزمة جديدة إن شعرت أنها ارتخت).",
      "3.2", "Social support (practical)",
      "Worn parts are a supply problem, not a willpower problem.",
      "Depends on your provider's process and coverage.", care_team=True),

    # ── Taking it off mid-night ─────────────────────────────────────────────
    A("mid_if_then", "MIDNIGHT_REMOVAL",
      "Make an if-then plan for waking up", "ضع خطة \"إذا… فإنني…\" للاستيقاظ ليلاً",
      "Say it once tonight: \"If I wake up and the mask is off, I put it back on before I check my phone.\" "
      "Leave the mask on the pillow, not the floor.",
      "قلها مرة الليلة: \"إذا استيقظت ووجدت القناع منزوعاً، أعيده قبل أن أنظر إلى هاتفي.\" "
      "واترك القناع على الوسادة لا على الأرض.",
      "1.4", "Action planning (implementation intention)",
      "If-then plans tie the action to the moment it's needed, which is when willpower is lowest.",
      "Doesn't address why the mask came off (dryness, leak, heat); pair with a morning note if it keeps happening."),
    A("mid_note", "MIDNIGHT_REMOVAL",
      "Note what woke you", "سجّل ما أيقظك",
      "Tomorrow morning, tap what woke you (dry, leak, hot, bathroom, don't know). After three mornings we'll know which fix to try.",
      "صباح الغد، اختر ما أيقظك (جفاف، تسرب، حرارة، دورة المياه، لا أعرف). بعد ثلاثة صباحات سنعرف أي حل نجرّب.",
      "2.3", "Self-monitoring of behaviour",
      "The cause of mid-night removal varies by person; three data points beat a guess.",
      "Needs you to answer in the morning; skipping it is fine — we fall back to the data."),
    A("mid_ramp", "MIDNIGHT_REMOVAL",
      "Use the ramp when you put it back on", "استخدم خاصية التدرّج عند إعادة القناع",
      "If your care team has enabled the ramp comfort setting, press it when you put the mask back on so the air starts gentle.",
      "إذا فعّل فريق الرعاية خاصية التدرّج المريحة، اضغطها عند إعادة القناع ليبدأ الهواء خفيفاً.",
      "4.1", "Instruction on how to perform the behaviour",
      "Going back to sleep against full pressure is a common reason people give up at 3 a.m.",
      "Only if ramp is enabled on your device; the app never changes prescribed pressure."),

    # ── Away / travel ───────────────────────────────────────────────────────
    A("travel_first_hour", "TRAVEL_AWAY",
      "First night back: one hour counts", "أول ليلة بعد العودة: ساعة واحدة تكفي",
      "Tonight, wear it for an hour. That counts as a comeback — the habit restarts with any use.",
      "الليلة، ارتدِه لمدة ساعة. هذا يُحتسب عودة، فالعادة تبدأ من جديد بأي استخدام.",
      "8.7", "Graded tasks",
      "A small, certain win restarts a routine faster than an all-or-nothing goal.",
      "One hour is a restart, not the therapy goal; we raise the bar as nights come back."),
    A("travel_pack_first", "TRAVEL_AWAY",
      "Pack the CPAP first next time", "ضع جهاز CPAP في الحقيبة أولاً في المرة القادمة",
      "Add 'CPAP + plug adapter' to the top of your packing list now, while you remember.",
      "أضف \"جهاز CPAP + محوّل كهرباء\" إلى أعلى قائمة السفر الآن وأنت تتذكر.",
      "12.1", "Restructuring the physical environment",
      "Most travel lapses happen because the machine stayed home, not because of a decision to skip.",
      "Won't help if you can't use it where you're staying (power, shared room)."),

    # ── Schedule changes (shift work, Ramadan, late nights) ─────────────────
    A("routine_anchor", "ROUTINE_SHIFT",
      "Tie the mask to your new bedtime", "اربط القناع بموعد نومك الجديد",
      "Pick something you do before every sleep, whatever the hour (brushing teeth, wudu, lights off), and put the mask on right after it.",
      "اختر شيئاً تفعله قبل كل نوم مهما كانت الساعة (تنظيف الأسنان، الوضوء، إطفاء الأنوار)، وضع القناع مباشرة بعده.",
      "8.3", "Habit formation",
      "Anchoring to an action, not a clock time, survives shift changes, Ramadan nights and travel.",
      "Habits take weeks; expect a few misses while the anchor sets."),
    A("routine_every_sleep", "ROUTINE_SHIFT",
      "Use it for every main sleep — day or night", "استخدمه في كل نوم رئيسي، نهاراً أو ليلاً",
      "When your main sleep moves (day sleep after a night shift, sleep after suhoor), use CPAP for that sleep too, and for naps over an hour.",
      "عندما يتغير موعد نومك الرئيسي (نوم النهار بعد مناوبة ليلية، النوم بعد السحور)، استخدم الجهاز في ذلك النوم أيضاً، وفي القيلولة الأطول من ساعة.",
      "1.4", "Action planning",
      "Apnoeas happen whenever you sleep, not only at night.",
      "Daytime sleep may need a darker, quieter room; the app can't fix the environment."),

    # ── Motivation ──────────────────────────────────────────────────────────
    A("mot_past_success", "MOTIVATION_FADE",
      "Look at what you've already banked", "انظر إلى ما أنجزته حتى الآن",
      "Open the weekly view and look at your banked nights and your best run. That's yours; a dip doesn't erase it.",
      "افتح العرض الأسبوعي وانظر إلى لياليك المحسوبة وأفضل سلسلة لديك. هذا إنجازك، والتراجع لا يمحوه.",
      "15.3", "Focus on past success",
      "Seeing earlier success raises confidence to repeat it; no-reset progress keeps that evidence visible.",
      "Works best when there is a history; on week one there's little to look back on."),
    A("mot_reason", "MOTIVATION_FADE",
      "Write your one reason", "اكتب سببك الوحيد",
      "Write one line: why you started (energy at work, safer driving, your partner's sleep). We'll show it with your evening nudge.",
      "اكتب سطراً واحداً: لماذا بدأت (طاقة في العمل، قيادة أكثر أماناً، نوم شريكك). سنعرضه مع تذكير المساء.",
      "1.9", "Commitment",
      "A reason in your own words is more persuasive than any message we could write.",
      "Your reason stays on your device in this prototype; it is never shared."),
    A("mot_buddy", "MOTIVATION_FADE",
      "Ask one person to check in", "اطلب من شخص واحد أن يذكّرك",
      "Ask a partner, family member or friend to ask \"mask on?\" at bedtime this week.",
      "اطلب من شريكك أو أحد أفراد عائلتك أو صديق أن يسألك \"هل لبست القناع؟\" وقت النوم هذا الأسبوع.",
      "3.1", "Social support (unspecified)",
      "Support from people around you is one of the stronger predictors of CPAP use.",
      "Only if you want to involve someone; nothing is sent from the app."),

    # ── Pressure (care team only) ───────────────────────────────────────────
    A("press_awake_practice", "PRESSURE_DISCOMFORT",
      "Practise 10 minutes awake", "تدرّب 10 دقائق وأنت مستيقظ",
      "Wear the mask with the machine on for 10 minutes while reading or watching TV, breathing slowly through your nose.",
      "ارتدِ القناع والجهاز يعمل لمدة 10 دقائق أثناء القراءة أو مشاهدة التلفاز، وتنفّس ببطء من أنفك.",
      "8.1", "Behavioural practice / rehearsal",
      "Getting used to the airflow while relaxed makes it feel less forceful at night.",
      "If the pressure still feels too strong after a few sessions, that's a settings question for your care team."),
    A("press_care_team", "PRESSURE_DISCOMFORT",
      "Tell your care team the air feels too strong", "أخبر فريق الرعاية أن الهواء قوي جداً",
      "Send one line: \"The air pressure feels too strong and I'm taking the mask off. Can we look at comfort settings?\"",
      "أرسل سطراً واحداً: \"ضغط الهواء قوي جداً وأنزع القناع. هل يمكننا مراجعة إعدادات الراحة؟\"",
      "3.2", "Social support (practical)",
      "Pressure and comfort settings are a clinical decision; your care team can adjust them safely.",
      "The app never suggests a pressure number.", care_team=True),

    # ── Self-report-only barriers ───────────────────────────────────────────
    A("dry_humidity", "DRYNESS",
      "Try one step more humidity", "جرّب زيادة الترطيب درجة واحدة",
      "If your care team has made humidity adjustable on your machine, raise it one step tonight.",
      "إذا جعل فريق الرعاية الترطيب قابلاً للتعديل في جهازك، ارفعه درجة واحدة الليلة.",
      "4.1", "Instruction on how to perform the behaviour",
      "Dry air is a common, fixable reason people pull the mask off.",
      "Too much humidity causes water in the tube; if it's locked, ask your provider."),
    A("dry_mouth_care_team", "DRYNESS",
      "Ask about mouth leak", "اسأل عن التسرب من الفم",
      "If you wake with a dry mouth, ask your provider whether a chin strap or a full-face mask would suit you.",
      "إذا استيقظت وفمك جاف، اسأل مزوّدك إن كان حزام الذقن أو قناع الوجه الكامل مناسباً لك.",
      "3.2", "Social support (practical)",
      "A dry mouth usually means air escaping through the mouth.",
      "Equipment changes go through your provider.", care_team=True),
    A("claus_practice", "CLAUSTROPHOBIA",
      "Get used to it in small steps", "تعوّد عليه بخطوات صغيرة",
      "Hold the mask to your face (no straps) for 2 minutes while watching TV. Tomorrow, straps on for 5. Then machine on for 10.",
      "أمسك القناع على وجهك (دون أحزمة) لمدة دقيقتين أثناء مشاهدة التلفاز. غداً مع الأحزمة لمدة 5 دقائق. ثم مع تشغيل الجهاز لمدة 10.",
      "8.7", "Graded tasks",
      "Gradual exposure while relaxed is the standard approach to mask-related anxiety.",
      "If anxiety is strong or getting worse, talk to your clinician; this isn't a treatment for panic."),
    A("claus_lighter_mask", "CLAUSTROPHOBIA",
      "Ask about a lighter mask", "اسأل عن قناع أخف",
      "Ask your provider whether nasal pillows (a much smaller mask) would work for you.",
      "اسأل مزوّدك إن كانت الوسائد الأنفية (قناع أصغر بكثير) مناسبة لك.",
      "3.2", "Social support (practical)",
      "Less mask on the face often means less closed-in feeling.",
      "Not every pressure or breathing pattern suits nasal pillows.", care_team=True),
    A("cong_any_use", "CONGESTION_ILLNESS",
      "While you're unwell, any use counts", "أثناء مرضك، أي استخدام يُحتسب",
      "Wear it as long as it's comfortable. If you can't breathe through your nose, rest and try again when it clears. "
      "If you feel very unwell or breathing is hard, contact a doctor.",
      "ارتدِه ما دام مريحاً. إذا لم تستطع التنفس من أنفك، استرح وحاول مجدداً عندما ينفتح. "
      "إذا شعرت بتعب شديد أو صعوبة في التنفس، تواصل مع طبيب.",
      "8.7", "Graded tasks",
      "Sick days are a common start of a long lapse; lowering the bar keeps the habit alive.",
      "Not medical advice for the illness itself."),
    A("forgot_pillow", "FORGOT",
      "Leave the mask on your pillow", "اترك القناع على وسادتك",
      "This morning, put the mask on your pillow so it's the first thing you see at bedtime.",
      "هذا الصباح، ضع القناع على وسادتك ليكون أول ما تراه وقت النوم.",
      "7.1", "Prompts / cues",
      "A visible cue at the right place works without needing to remember.",
      "Cues fade as you get used to them; we'll check in if it stops working."),
    A("forgot_nudge", "FORGOT",
      "Get one nudge at your bedtime", "احصل على تذكير واحد في موعد نومك",
      "Turn on one evening nudge at the time you usually go to bed (Settings). One a day at most.",
      "فعّل تذكيراً مسائياً واحداً في موعد نومك المعتاد (الإعدادات). تذكير واحد يومياً كحد أقصى.",
      "7.1", "Prompts / cues",
      "A timed prompt bridges the gap until the habit runs on its own.",
      "Notifications are easy to ignore; we cap them and reduce them if you don't open them."),
    A("noise_hose", "NOISE_PARTNER",
      "Route the hose away from your partner", "وجّه الأنبوب بعيداً عن شريكك",
      "Run the hose over the headboard and check for hissing — most noise is a leak, not the machine.",
      "مرّر الأنبوب فوق رأس السرير وتحقق من صوت الصفير، فمعظم الضجيج سببه تسرب لا الجهاز.",
      "12.1", "Restructuring the physical environment",
      "Less hose drag means fewer leaks and less noise.",
      "Won't help if the noise bothering your partner is something else."),
    A("noise_ask_partner", "NOISE_PARTNER",
      "Ask your partner how they slept", "اسأل شريكك كيف نام",
      "Ask your partner tomorrow whether they slept better on the nights you used it.",
      "اسأل شريكك غداً إن كان نومه أفضل في الليالي التي استخدمت فيها الجهاز.",
      "3.1", "Social support (unspecified)",
      "Partners often notice the snoring stopping before the patient notices any benefit.",
      "Only relevant if you share a room."),
    A("fine_consequences", "FELT_FINE",
      "Feeling fine is the therapy working", "الشعور بالتحسن يعني أن العلاج يعمل",
      "Apnoeas come back the first night without CPAP, even when you feel fine. One night off rarely shows the next day — it adds up.",
      "انقطاع التنفس يعود من أول ليلة دون الجهاز، حتى لو شعرت بأنك بخير. ليلة واحدة نادراً ما تظهر في اليوم التالي، لكنها تتراكم.",
      "5.1", "Information about health consequences",
      "People stop when they feel better; the benefit only lasts while the therapy continues.",
      "Information alone rarely changes behaviour; we pair it with a small action next time."),
    A("fine_two_weeks", "FELT_FINE",
      "Try a two-week check", "جرّب مراجعة لمدة أسبوعين",
      "Keep using it for two weeks, then compare your energy on used and unused days in the weekly view.",
      "استمر في استخدامه لمدة أسبوعين، ثم قارن طاقتك في أيام الاستخدام وعدمه في العرض الأسبوعي.",
      "1.5", "Review behaviour goal(s)",
      "A short, defined trial respects your choice and gives you your own evidence.",
      "The app can't measure daytime energy yet; this relies on how you feel."),
]

BY_ID = {a.id: a for a in LIBRARY}


def for_barrier(code: str, include_care_team: bool = True) -> list[Action]:
    return [a for a in LIBRARY if a.barrier == code and (include_care_team or not a.care_team)]


# During a lapse the first goal is a comeback, not the full goal (BCT 8.7, graded tasks).
COMEBACK_GOAL_MIN = 60
COMEBACK = {
    "en": "Comeback goal for tonight: wear it for one hour. Any use counts, and your banked nights are still yours.",
    "ar": "هدف العودة الليلة: ارتدِه لمدة ساعة واحدة. أي استخدام يُحتسب، ولياليك المحسوبة ما زالت لك.",
}
