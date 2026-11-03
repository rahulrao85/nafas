/* Nafas — single-page UI. No framework; talks to the Flask API. */
(() => {
  'use strict';

  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => [...el.querySelectorAll(s)];
  const esc = (v) => String(v ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  // Dates are always DD-Mon-YYYY, isolated left-to-right so Arabic layout doesn't reorder them.
  const fmt = (iso) => { if (!iso) return '—'; const [y, m, d] = iso.split('-'); return `\u2066${d}\u2011${MON[+m - 1]}\u2011${y}\u2069`; };   // non-breaking hyphens
  const addDays = (iso, n) => { const d = new Date(iso + 'T00:00:00Z'); d.setUTCDate(d.getUTCDate() + n); return d.toISOString().slice(0, 10); };
  const daysBetween = (a, b) => Math.round((new Date(b + 'T00:00:00Z') - new Date(a + 'T00:00:00Z')) / 864e5);

  const STR = {
    en: {
      tagline: 'CPAP habits that survive bad weeks', asof: 'Morning of', play: 'Play', pause: 'Pause', latest: 'Latest',
      tab_today: 'Today', tab_weekly: 'Weekly', tab_outcomes: 'Outcomes', tab_about: 'How it works',
      coach_title: 'Coach note', coach_help: 'The rules engine picks the step. AI only words it, and every draft is checked before you see it.',
      coach_btn: "Write tonight's note", checkin_title: 'What got in the way?', checkin_help: 'One tap. What you tell us outranks what the data guesses.',
      note_label: 'Anything else? (optional)', chart_title: 'Last 90 nights', met: 'Goal met', partial: 'Short', leak: 'Large leak',
      weekly_title: 'Week by week', history_title: 'What we tried, and what helped', learner_title: 'What works for you',
      learner_help: 'Each step is judged on the three nights after it. Better-scoring steps get offered first; others still get tried.',
      person_outcomes: 'This person', cohort_title: 'Synthetic cohort (150 people, 180 nights)', cohort_btn: 'Run measurement',
      cohort_help: 'Tests the outcome pipeline Challenge 09 asks for: persistence, recovery after lapses, retention, biomarker change and equity. Synthetic people, so not evidence of effect.',
      footer: 'Prototype. Not medical advice and not a medical device. Demo data is synthetic.',
      settings: 'Settings', settings_help: 'Your goals, your data, your notifications.', goal: 'Nightly goal (hours)', language: 'Language',
      nudge_hour: 'Nudge time', quiet: 'Quiet hours (from–to)', nudges: 'Evening nudges (max one a day)', use_llm: 'Let AI word my notes',
      share: 'Allow a care-team summary', save: 'Save', summary_btn: 'Preview care-team summary',
      upload: 'Try your own data (ResMed STR.edf, CSV or JSON)', upload_btn: 'Load', template: 'CSV template',
      upload_help: 'Read in memory for this session only, never saved to disk. Names, birth dates and device serials are dropped.', forget: 'Delete everything from this session',
      last_night: 'Last night', banked: 'Banked good nights', banked_sub: 'Never resets', adh30: '30-night adherence', adh_sub: 'Nights at goal',
      run: 'Current run', run_sub: (g) => g ? `${g} short night${g > 1 ? 's' : ''} forgiven` : 'One short night a week is forgiven', comebacks: 'Comebacks',
      comebacks_sub: 'Lapses you came back from', hours: 'h', step_title: 'One small step', ontrack: "You're on track. Nothing to change tonight.",
      try: "I'll try it", swap: 'Swap for another', notnow: 'Not now', why: 'Why this might help', limits: 'Where it stops helping',
      care_team: 'Care team', escalated: 'Two tries on this didn’t help, so this step brings in your care team.',
      accepted: 'You said you’ll try this.', dismissed: 'Skipped — we’ll check again tomorrow.',
      noticed: 'What we noticed', nothing_noticed: 'Nothing unusual in the last few nights.', likely: 'Likely in the way',
      you_told: 'You told us', from_data: 'From the data', comeback_title: 'Comeback mode', clinician_title: 'For your care team',
      clinician_body: 'This is a pattern for a clinician to review. The app does not change your therapy.',
      nudge_title: "Tonight's nudge", no_nudge: 'No nudge', thanks: 'Thanks — your plan is updated.', saved: 'Saved.',
      week: 'Week', nights: 'Nights', used: 'Used', at_goal: 'At goal', avg: 'Avg', leaks: 'Leak nights', ahi: 'AHI', events: 'Lapses / comebacks', tried: 'Steps',
      date: 'Date', trigger: 'Trigger', barrier: 'Barrier', step: 'Step', bct: 'BCT', outcome: 'Outcome',
      st_open: 'In progress', st_helped: 'Helped', st_not_helped: "Didn't help", st_replanned: 'Replanned',
      no_history: 'No steps yet.', no_learn: 'Nothing judged yet.', loading: 'Loading…', source_template: 'Template', checked: 'Checked',
      kinds: { lapse: 'Lapse', decline: 'Use is dropping', leak: 'Large leak', leak_creep: 'Leak creeping up', clinical: 'Residual events high' },
      add_data: 'Add your data', data_help: 'Drop everything at once: your CPAP SD card, watch and ring exports. Nafas works out what each file is.',
      drop_title: 'Drop files, a folder or a zip here', drop_hint: 'or tap to choose files', choose_files: 'Choose files',
      choose_folder: 'Choose a folder', try_samples: 'Try sample files', what_works: 'What can I add?',
      src_resmed: 'the whole card folder, a zip of it, or just STR.edf', src_garmin: '.fit sleep files, or a Gadgetbridge export zip',
      src_ring: "the Collector app's export (JSON)", src_apple: 'export.zip from the Health app', src_fitbit: 'sleep-….json from Takeout',
      uploading: 'Reading your files…', found_n: (n, a, b) => `${n} nights, ${a} to ${b}`, open_data: 'Open my data',
      cpap_used: (n) => `${n} nights with CPAP use`, wear_n: (n) => `${n} nights with watch or ring sleep`,
      source: 'Source', from_file: 'From', nights_col: 'Nights', range: 'Dates', skipped_title: 'Skipped',
      too_big: 'That is more than 64 MB. Zip the folder, or add fewer files at a time.',
      no_cpap: 'We found watch or ring data but no CPAP data. Add your ResMed SD card (STR.edf) or a CSV as well: Nafas compares the two.',
      reasons: {
        datalog: 'Breath-by-breath detail (not needed: the nightly summary is in STR.edf)',
        device_identity: 'Device identity or settings (skipped on purpose, for privacy)',
        unknown: 'Not a format Nafas reads', apple_cda: 'Clinical documents (not needed)',
        zip_nested: 'Zip inside a zip inside a zip', zip_bad: 'Damaged or unreadable zip', zip_too_many: 'Zip with too many files',
        unsafe_path: 'Unsafe file path inside the zip', encrypted: 'Password-protected file', too_large: 'Too large',
        zip_bomb: 'Suspicious compression (safety check)', fit_no_sleep: 'Watch file with no sleep or heart data (e.g. an activity)',
        unreadable: 'Could not be read', wearable_outside_cpap: 'Watch or ring nights outside your CPAP dates',
      },
      o_adh_first: 'Adherence, first 30 nights', o_adh_last: 'Adherence, last 30 nights', o_goal_nights: 'Nights at goal',
      o_persisting: 'Persisting (≥70%)', o_below: 'Below 70%', o_lapses: 'Lapses', o_recovered: (n) => `${n} recovered`,
      o_days: 'Median days to recover', o_days_sub: 'Lapse start → 3 of 4 nights at goal', o_hours: 'Hours a night',
      o_first_last: 'First vs last 30 nights', o_ahi: 'Residual AHI', o_helped: 'Steps that helped', o_judged: (n) => `${n} judged`,
      c_persist: 'Persisting at 6 months', c_persist_sub: '≥70% of last 30 nights at goal', c_retained: 'Retained',
      c_retained_sub: 'Used ≥4 of last 28 nights', c_lapses: 'Lapses per person', c_days_sub: 'Across recovered lapses',
      c_ahi_sub: 'Biomarker, first vs last 30', c_helped_sub: 'Judged on next 3 nights', c_group: 'Group', c_people: 'People',
      c_ci: '95% CI', c_recovery: 'Recovery rate', c_gap: 'gap', c_sig: 'intervals don’t overlap', c_noise: 'within noise',
      c_small: 'small n', c_note: (m) => `Equity gaps count only groups of ${m}+ people. Attributes here are assigned at random, so any gap is chance — which is why a pilot must pre-register comparisons and correct for multiple testing.`,
      groups: { language: 'Language', age_band: 'Age band', shift_worker: 'Shift worker' },
      watch: 'Watch/ring', rhr: 'RHR', hrv: 'HRV',
      src: {},
    },
    ar: {
      tagline: 'عادات CPAP تصمد أمام الأسابيع الصعبة', asof: 'صباح يوم', play: 'تشغيل', pause: 'إيقاف', latest: 'الأحدث',
      tab_today: 'اليوم', tab_weekly: 'أسبوعي', tab_outcomes: 'النتائج', tab_about: 'كيف يعمل',
      coach_title: 'ملاحظة المساء', coach_help: 'محرك القواعد يختار الخطوة، والذكاء الاصطناعي يصوغها فقط، وتُفحص كل مسودة قبل عرضها.',
      coach_btn: 'اكتب ملاحظة الليلة', checkin_title: 'ما الذي أعاقك؟', checkin_help: 'نقرة واحدة. ما تخبرنا به يتقدّم على تخمين البيانات.',
      note_label: 'شيء آخر؟ (اختياري)', chart_title: 'آخر 90 ليلة', met: 'تحقق الهدف', partial: 'قصيرة', leak: 'تسرب كبير',
      weekly_title: 'أسبوعاً بأسبوع', history_title: 'ما جرّبناه وما نجح', learner_title: 'ما ينجح معك',
      learner_help: 'تُقيَّم كل خطوة على الليالي الثلاث التالية. الخطوات الأنجح تُعرض أولاً، وتُجرَّب غيرها أيضاً.',
      person_outcomes: 'هذا الشخص', cohort_title: 'مجموعة اصطناعية (150 شخصاً، 180 ليلة)', cohort_btn: 'تشغيل القياس',
      cohort_help: 'يختبر مسار قياس النتائج: الاستمرار، والتعافي بعد الانقطاع، والبقاء، وتغيّر المؤشر الحيوي، والعدالة. بيانات اصطناعية وليست دليلاً على الأثر.',
      footer: 'نموذج أولي. ليس نصيحة طبية ولا جهازاً طبياً. بيانات العرض اصطناعية.',
      settings: 'الإعدادات', settings_help: 'أهدافك وبياناتك وتنبيهاتك.', goal: 'الهدف الليلي (ساعات)', language: 'اللغة',
      nudge_hour: 'وقت التذكير', quiet: 'ساعات الهدوء (من–إلى)', nudges: 'تذكير مسائي (مرة واحدة يومياً كحد أقصى)', use_llm: 'اسمح للذكاء الاصطناعي بصياغة ملاحظاتي',
      share: 'السماح بملخص لفريق الرعاية', save: 'حفظ', summary_btn: 'معاينة ملخص فريق الرعاية',
      upload: 'جرّب بياناتك (ResMed STR.edf أو CSV أو JSON)', upload_btn: 'تحميل', template: 'نموذج CSV',
      upload_help: 'تُقرأ في الذاكرة لهذه الجلسة فقط ولا تُحفظ. تُحذف الأسماء وتواريخ الميلاد والأرقام التسلسلية للأجهزة.', forget: 'احذف كل ما في هذه الجلسة',
      last_night: 'الليلة الماضية', banked: 'ليالٍ جيدة محسوبة', banked_sub: 'لا تُصفَّر أبداً', adh30: 'الالتزام في 30 ليلة', adh_sub: 'ليالٍ حققت الهدف',
      run: 'السلسلة الحالية', run_sub: (g) => g ? `سُومح في ${g} ليلة قصيرة` : 'تُسامَح ليلة قصيرة واحدة أسبوعياً', comebacks: 'مرات العودة',
      comebacks_sub: 'انقطاعات عدت منها', hours: 'س', step_title: 'خطوة صغيرة واحدة', ontrack: 'أنت على المسار. لا شيء يتغير الليلة.',
      try: 'سأجربها', swap: 'استبدلها بأخرى', notnow: 'ليس الآن', why: 'لماذا قد تساعد', limits: 'حدودها',
      care_team: 'فريق الرعاية', escalated: 'لم تنجح محاولتان، لذا تُشرك هذه الخطوة فريق الرعاية.',
      accepted: 'قلت إنك ستجربها.', dismissed: 'تم التخطي — سنتحقق غداً.',
      noticed: 'ما لاحظناه', nothing_noticed: 'لا شيء غير معتاد في الليالي الأخيرة.', likely: 'العائق المرجح',
      you_told: 'أخبرتنا', from_data: 'من البيانات', comeback_title: 'وضع العودة', clinician_title: 'لفريق الرعاية',
      clinician_body: 'هذا نمط يراجعه الطبيب. التطبيق لا يغيّر علاجك.',
      nudge_title: 'تذكير الليلة', no_nudge: 'لا تذكير', thanks: 'شكراً — تم تحديث خطتك.', saved: 'تم الحفظ.',
      week: 'الأسبوع', nights: 'ليالٍ', used: 'استخدام', at_goal: 'بالهدف', avg: 'المتوسط', leaks: 'ليالي التسرب', ahi: 'AHI', events: 'انقطاع / عودة', tried: 'خطوات',
      date: 'التاريخ', trigger: 'السبب', barrier: 'العائق', step: 'الخطوة', bct: 'BCT', outcome: 'النتيجة',
      st_open: 'جارية', st_helped: 'ساعدت', st_not_helped: 'لم تساعد', st_replanned: 'أُعيد التخطيط',
      no_history: 'لا خطوات بعد.', no_learn: 'لم يُقيَّم شيء بعد.', loading: 'جارٍ التحميل…', source_template: 'قالب', checked: 'تم الفحص',
      kinds: { lapse: 'انقطاع', decline: 'الاستخدام يتراجع', leak: 'تسرب كبير', leak_creep: 'التسرب يزداد', clinical: 'أحداث متبقية مرتفعة' },
      add_data: 'أضف بياناتك', data_help: 'أضف كل شيء مرة واحدة: بطاقة SD لجهاز CPAP، وملفات الساعة والخاتم. يتعرّف نَفَس على كل ملف.',
      drop_title: 'أفلت الملفات أو مجلداً أو ملف zip هنا', drop_hint: 'أو انقر لاختيار الملفات', choose_files: 'اختر ملفات',
      choose_folder: 'اختر مجلداً', try_samples: 'جرّب ملفات نموذجية', what_works: 'ماذا يمكنني أن أضيف؟',
      src_resmed: 'مجلد البطاقة كاملاً، أو ملف zip منه، أو STR.edf وحده', src_garmin: 'ملفات النوم ‎.fit، أو ملف تصدير Gadgetbridge',
      src_ring: 'ملف التصدير من تطبيق Collector ‏(JSON)', src_apple: 'ملف export.zip من تطبيق الصحة', src_fitbit: 'ملفات sleep-….json من Takeout',
      uploading: 'جارٍ قراءة ملفاتك…', found_n: (n, a, b) => `${n} ليلة، من ${a} إلى ${b}`, open_data: 'افتح بياناتي',
      cpap_used: (n) => `${n} ليلة استُخدم فيها الجهاز`, wear_n: (n) => `${n} ليلة فيها نوم من الساعة أو الخاتم`,
      source: 'المصدر', from_file: 'من', nights_col: 'الليالي', range: 'التواريخ', skipped_title: 'تم التخطي',
      too_big: 'الحجم أكبر من 64 ميغابايت. اضغط المجلد بصيغة zip أو أضف ملفات أقل في كل مرة.',
      no_cpap: 'وجدنا بيانات الساعة أو الخاتم ولكن لا توجد بيانات CPAP. أضف بطاقة ResMed ‏(STR.edf) أو ملف CSV أيضاً، فنَفَس يقارن بينهما.',
      reasons: {
        datalog: 'تفاصيل كل نفَس (غير لازمة: الملخص الليلي في STR.edf)',
        device_identity: 'هوية الجهاز أو إعداداته (تُتخطى عمداً حفاظاً على الخصوصية)',
        unknown: 'صيغة لا يقرؤها نَفَس', apple_cda: 'مستندات سريرية (غير لازمة)',
        zip_nested: 'ملف zip متداخل أكثر من اللازم', zip_bad: 'ملف zip تالف', zip_too_many: 'ملف zip فيه ملفات كثيرة جداً',
        unsafe_path: 'مسار غير آمن داخل ملف zip', encrypted: 'ملف محمي بكلمة مرور', too_large: 'كبير جداً',
        zip_bomb: 'ضغط مريب (فحص أمان)', fit_no_sleep: 'ملف ساعة بلا بيانات نوم أو قلب (مثل نشاط رياضي)',
        unreadable: 'تعذّرت قراءته', wearable_outside_cpap: 'ليالٍ من الساعة أو الخاتم خارج تواريخ CPAP',
      },
      o_adh_first: 'الالتزام في أول 30 ليلة', o_adh_last: 'الالتزام في آخر 30 ليلة', o_goal_nights: 'ليالٍ حققت الهدف',
      o_persisting: 'مستمر (70% أو أكثر)', o_below: 'أقل من 70%', o_lapses: 'الانقطاعات', o_recovered: (n) => `عاد من ${n}`,
      o_days: 'وسيط أيام التعافي', o_days_sub: 'من بداية الانقطاع حتى 3 من 4 ليالٍ بالهدف', o_hours: 'ساعات في الليلة',
      o_first_last: 'أول 30 ليلة مقابل آخر 30', o_ahi: 'AHI المتبقي', o_helped: 'خطوات ساعدت', o_judged: (n) => `${n} قُيّمت`,
      c_persist: 'مستمرون بعد 6 أشهر', c_persist_sub: '70% أو أكثر من آخر 30 ليلة بالهدف', c_retained: 'باقون',
      c_retained_sub: 'استخدام 4 من آخر 28 ليلة على الأقل', c_lapses: 'انقطاعات لكل شخص', c_days_sub: 'عبر الانقطاعات المستعادة',
      c_ahi_sub: 'مؤشر حيوي، أول 30 مقابل آخر 30', c_helped_sub: 'تُقيَّم على الليالي الثلاث التالية', c_group: 'المجموعة', c_people: 'الأشخاص',
      c_ci: 'فاصل ثقة 95%', c_recovery: 'معدل التعافي', c_gap: 'الفجوة', c_sig: 'الفواصل لا تتداخل', c_noise: 'ضمن التذبذب',
      c_small: 'عدد صغير', c_note: (m) => `تُحسب فجوات العدالة للمجموعات التي تضم ${m} شخصاً أو أكثر فقط. الصفات هنا موزعة عشوائياً، فأي فجوة هي صدفة، ولهذا يجب أن تحدد التجربة الفعلية مقارناتها مسبقاً وتصحح للاختبارات المتعددة.`,
      groups: { language: 'اللغة', age_band: 'الفئة العمرية', shift_worker: 'عامل مناوبات' },
      watch: 'الساعة/الخاتم', rhr: 'نبض الراحة', hrv: 'HRV',
      src: { resmed_str: 'بطاقة ResMed ‏(STR.edf)', nafas_csv: 'CSV', nafas_json: 'JSON', garmin_fit: 'ساعة Garmin ‏(.fit)',
             gadgetbridge: 'تصدير Gadgetbridge', collector: 'خاتم ذكي (تصدير Collector)', apple_health: 'تصدير Apple Health',
             fitbit: 'نوم Fitbit / Google' },
    },
  };

  const S = { personas: [], persona: 'layla', state: null, dates: [], idx: 0, playing: null, lang: 'en', cohort: null };
  const t = (k) => (STR[S.lang] && STR[S.lang][k] !== undefined ? STR[S.lang][k] : STR.en[k]);

  // ── Theme ──────────────────────────────────────────────────────────────
  const store = { get(k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
                  set(k, v) { try { localStorage.setItem(k, v); } catch (e) { /* private mode */ } } };
  function applyTheme(dark) {
    document.body.classList.toggle('dark-theme', dark);
    document.documentElement.classList.remove('pre-dark');
  }
  const saved = store.get('nafas-theme');
  applyTheme(saved ? saved === 'dark' : window.matchMedia('(prefers-color-scheme: dark)').matches);
  $('#themeBtn').addEventListener('click', () => {
    const dark = !document.body.classList.contains('dark-theme');
    applyTheme(dark); store.set('nafas-theme', dark ? 'dark' : 'light');
    if (S.state) renderChart();
  });

  // ── API ────────────────────────────────────────────────────────────────
  async function api(path, opts = {}) {
    const res = await fetch(path, { credentials: 'same-origin', ...opts,
      headers: opts.body && !(opts.body instanceof FormData) ? { 'Content-Type': 'application/json' } : undefined });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw Object.assign(new Error(data.error || res.statusText), { status: res.status, data });
    return data;
  }
  const post = (path, body) => api(path, { method: 'POST', body: JSON.stringify(body) });
  const asOf = () => S.dates[S.idx];

  function toast(msg) {
    const el = $('#toast'); el.textContent = msg; el.hidden = false;
    clearTimeout(toast._t); toast._t = setTimeout(() => { el.hidden = true; }, 2600);
  }

  // ── i18n chrome ───────────────────────────────────────────────────────
  function applyLang(lang) {
    S.lang = lang === 'ar' ? 'ar' : 'en';
    document.documentElement.lang = S.lang;
    document.documentElement.dir = S.lang === 'ar' ? 'rtl' : 'ltr';
    $$('[data-i18n]').forEach((el) => { const v = t(el.dataset.i18n); if (typeof v === 'string') el.textContent = v; });
    $('#langBtn').textContent = S.lang === 'ar' ? 'EN' : 'ع';
    $('#playBtn').textContent = S.playing ? t('pause') : t('play');
    if (S.cohort) renderCohort();
  }

  // ── Load ───────────────────────────────────────────────────────────────
  async function loadPersonas(select) {
    const r = await api('/api/personas');
    S.personas = r.personas;
    $('#persona').innerHTML = r.personas.map((p) =>
      `<option value="${esc(p.id)}">${esc(p.display_name)} · ${p.nights}</option>`).join('');
    if (select) S.persona = select;
    $('#persona').value = S.persona;
  }

  async function loadState(date) {
    const q = new URLSearchParams({ persona: S.persona });
    if (date) q.set('as_of', date);
    const st = await api('/api/state?' + q);
    setState(st, true);
  }

  function setState(st, resetRange) {
    const first = st.range.first, last = st.range.last;
    if (resetRange || !S.dates.length || S.dates[0] !== first || S.dates[S.dates.length - 1] !== last) {
      const n = daysBetween(first, last);
      S.dates = Array.from({ length: n + 1 }, (_, i) => addDays(first, i));
      $('#dayRange').max = String(n);
    }
    S.idx = Math.max(0, S.dates.indexOf(st.as_of));
    $('#dayRange').value = String(S.idx);
    S.state = st;
    if (st.profile.language !== S.lang) applyLang(st.profile.language);
    render();
  }

  // ── Render ─────────────────────────────────────────────────────────────
  function render() {
    const st = S.state;
    $('#asofLabel').textContent = fmt(addDays(st.as_of, 1));
    $('#story').textContent = st.persona.story;
    $('#dataTag').textContent = st.persona.uploaded ? 'Your upload' : 'Synthetic data';
    $('#dataTag').className = 'tag ' + (st.persona.uploaded ? 'tag-warning' : 'tag-info');
    const llm = st.llm || {};
    $('#llmTag').textContent = llm.provider === 'offline' ? t('source_template') : `${llm.provider} · ${llm.model}`;
    $('#llmTag').title = llm.note || '';
    renderStats(); renderBanners(); renderStep(); renderNoticed(); renderChips(); renderNudge();
    renderChart(); renderWeekly(); renderHistory(); renderLearner(); renderPersonOutcomes();
  }

  function stat(label, value, sub, cls = '') {
    return `<div class="stats-card ${cls}"><div class="stat-label">${esc(label)}</div><div class="stat-value">${esc(value)}</div><div class="stat-sub">${esc(sub)}</div></div>`;
  }

  function statusTag(s) {
    const map = { met: ['tag-success', t('met')], partial: ['tag-warning', t('partial')], missed: ['tag-danger', '0 ' + t('hours')] };
    const [c, l] = map[s] || ['', s];
    return `<span class="tag ${c}">${esc(l)}</span>`;
  }

  function renderStats() {
    const st = S.state, m = st.momentum, ln = st.last_night;
    const comebacks = st.lapses.filter((l) => l.comeback).length;
    const cpapSub = ln.usage_min > 0
      ? [ln.leak95_lpm != null ? `leak ${ln.leak95_lpm} L/min` : '', ln.ahi != null ? `AHI ${ln.ahi}` : ''].filter(Boolean).join(' · ')
      : '—';
    const wearSub = ln.wearable_sleep_min != null
      ? [`${t('watch')} ${(ln.wearable_sleep_min / 60).toFixed(1)} ${t('hours')}`,
         ln.wearable_rhr != null ? `${t('rhr')} ${Math.round(ln.wearable_rhr)}` : '',
         ln.wearable_hrv_ms != null ? `${t('hrv')} ${Math.round(ln.wearable_hrv_ms)} ms` : ''].filter(Boolean).join(' · ')
      : '';
    const lastSub = wearSub ? `${cpapSub}\n${wearSub}` : cpapSub;
    $('#stats').innerHTML =
      `<div class="stats-card"><div class="stat-label">${esc(t('last_night'))} ${statusTag(ln.status)}</div><div class="stat-value">${ln.hours} ${esc(t('hours'))}</div><div class="stat-sub" style="white-space:pre-line">${esc(lastSub)}</div></div>` +
      stat(t('banked'), m.banked_nights, t('banked_sub'), 'accent') +
      stat(t('adh30'), m.adherence_30 + '%', t('adh_sub')) +
      stat(t('run'), m.run, t('run_sub')(m.run_grace_used)) +
      stat(t('comebacks'), comebacks, t('comebacks_sub'));
  }

  function renderBanners() {
    const st = S.state; let h = '';
    if (st.recovery.active) {
      h += `<div class="alert alert-info"><h3>${esc(t('comeback_title'))}</h3><p>${esc(st.recovery.goal_text)}</p></div>`;
    }
    if (st.clinician_flag) {
      h += `<div class="alert alert-danger"><h3>${esc(t('clinician_title'))} · ${esc(fmt(st.clinician_flag.date))}</h3><p>${esc(st.clinician_flag.evidence[0])}</p></div>`;
    }
    $('#banners').innerHTML = h;
  }

  function renderStep() {
    const iv = S.state.intervention;
    if (!iv) {
      $('#stepCard').innerHTML = `<h2>${esc(t('step_title'))}</h2><div class="ontrack"><div class="big" aria-hidden="true">✓</div><p>${esc(t('ontrack'))}</p></div>`;
      return;
    }
    const a = iv.action;
    const state = iv.accepted === true ? `<p class="small" style="color:var(--success)">${esc(t('accepted'))}</p>`
      : iv.accepted === false ? `<p class="small muted">${esc(t('dismissed'))}</p>` : '';
    $('#stepCard').innerHTML = `
      <div class="card-head"><h2>${esc(t('step_title'))}</h2><span class="small muted">${esc(fmt(iv.start))}</span></div>
      <div class="tags">
        <span class="tag tag-primary">${esc(t('likely'))}: ${esc(iv.barrier_label)}</span>
        <span class="tag">${esc(iv.barrier_source === 'self-report' ? t('you_told') : t('from_data'))}</span>
        <span class="tag tag-info" title="${esc(a.bct_name)}">BCT ${esc(a.bct)} · ${esc(a.bct_name)}</span>
        ${a.care_team ? `<span class="tag tag-warning">${esc(t('care_team'))}</span>` : ''}
      </div>
      <div class="step-title" lang="${esc(a.lang)}">${esc(a.title)}</div>
      <p class="step-body" lang="${esc(a.lang)}">${esc(a.step)}</p>
      ${iv.escalated ? `<p class="small muted">${esc(t('escalated'))}</p>` : ''}
      <details><summary>${esc(t('why'))}</summary><p>${esc(a.rationale)}</p></details>
      <details><summary>${esc(t('limits'))}</summary><p>${esc(a.limits)}</p></details>
      ${state}
      <div class="btn-row">
        <button class="btn btn-primary" data-act="accept" type="button">${esc(t('try'))}</button>
        <button class="btn btn-secondary" data-act="swap" type="button">${esc(t('swap'))}</button>
        <button class="btn btn-secondary" data-act="dismiss" type="button">${esc(t('notnow'))}</button>
      </div>`;
    $$('#stepCard [data-act]').forEach((b) => b.addEventListener('click', async () => {
      b.disabled = true;
      try {
        const st = await post('/api/action', { persona: S.persona, as_of: asOf(), type: b.dataset.act, intervention_id: iv.id });
        setState(st); toast(t('thanks'));
      } catch (e) { toast(e.message); b.disabled = false; }
    }));
  }

  function renderNoticed() {
    const st = S.state;
    const dets = st.detections.map((d) => `
      <div class="det ${esc(d.severity)}"><div class="det-kind">${esc(t('kinds')[d.kind] || d.kind)}</div>
      <ul>${d.evidence.map((e) => `<li>${esc(e)}</li>`).join('')}</ul></div>`).join('');
    const bars = st.barriers.map((b) => `
      <div class="barrier"><span>${esc(b.label)}</span><span class="tag ${b.source === 'self-report' ? 'tag-primary' : ''}">${esc(b.source === 'self-report' ? t('you_told') : t('from_data'))}</span>
      <div class="bar" role="img" aria-label="confidence ${Math.round(b.confidence * 100)}%"><span style="width:${Math.round(b.confidence * 100)}%"></span></div>
      <div class="ev">${esc(b.evidence.join(' '))}</div></div>`).join('');
    $('#noticedCard').innerHTML = `<h2>${esc(t('noticed'))}</h2>${dets || `<p class="muted">${esc(t('nothing_noticed'))}</p>`}
      ${bars ? `<h3>${esc(t('likely'))}</h3>${bars}` : ''}`;
  }

  function renderChips() {
    const st = S.state;
    const today = st.checkins.find((c) => c.date === st.as_of);
    $('#chips').innerHTML = st.barrier_options.map((b) =>
      `<button type="button" class="chip ${today && today.barrier === b.code ? 'on' : ''}" data-b="${esc(b.code)}">${esc(b.label)}</button>`).join('');
    $$('#chips .chip').forEach((c) => c.addEventListener('click', async () => {
      try {
        const r = await post('/api/checkin', { persona: S.persona, as_of: asOf(), barrier: c.dataset.b, note: $('#noteInput').value });
        const u = $('#urgent'); u.hidden = !r.urgent; u.textContent = r.urgent || '';
        $('#noteInput').value = '';
        setState(r.state); toast(t('thanks'));
      } catch (e) { toast(e.message); }
    }));
  }

  function renderNudge() {
    const n = S.state.nudge;
    $('#nudgeCard').innerHTML = `<h2>${esc(t('nudge_title'))}</h2>` + (n.send
      ? `<p><span class="tag tag-primary">${esc(n.at)}</span> ${esc(n.text)}</p><p class="small muted">${esc(n.reason)}</p>`
      : `<p><span class="tag">${esc(t('no_nudge'))}</span></p><p class="small muted">${esc(n.reason)}</p>`);
  }

  function cssVar(name) { return getComputedStyle(document.body).getPropertyValue(name).trim(); }

  function renderChart() {
    const st = S.state, s = st.series;
    const W = 900, H = 230, P = { l: 34, r: 8, t: 14, b: 26 }, maxH = 10;
    const iw = W - P.l - P.r, ih = H - P.t - P.b, bw = iw / Math.max(s.length, 1);
    const y = (h) => P.t + ih - (Math.min(h, maxH) / maxH) * ih;
    const col = { met: cssVar('--success'), partial: cssVar('--warning'), missed: cssVar('--danger') };
    let g = '';
    [0, 4, 8].forEach((h) => {
      g += `<line x1="${P.l}" x2="${W - P.r}" y1="${y(h)}" y2="${y(h)}" stroke="${cssVar('--border-color')}" stroke-width="1"/>`;
      g += `<text x="${P.l - 6}" y="${y(h) + 4}" text-anchor="end" font-size="11" fill="${cssVar('--text-muted')}">${h}h</text>`;
    });
    s.forEach((n, i) => {
      const x = P.l + i * bw + bw * 0.15, w = Math.max(1, bw * 0.7);
      if (n.hours > 0) g += `<rect x="${x}" y="${y(n.hours)}" width="${w}" height="${y(0) - y(n.hours)}" rx="1.5" fill="${col[n.status]}"><title>${fmt(n.date)}: ${n.hours} h</title></rect>`;
      else g += `<rect x="${x}" y="${y(0) - 3}" width="${w}" height="3" fill="${col.missed}" opacity="0.6"><title>${fmt(n.date)}: not used</title></rect>`;
      if (n.leak != null && n.leak > 24) g += `<circle cx="${x + w / 2}" cy="${P.t + 4}" r="3" fill="${cssVar('--danger')}"><title>${fmt(n.date)}: leak ${n.leak} L/min</title></circle>`;
    });
    const goal = st.profile.goal_hours;
    g += `<line x1="${P.l}" x2="${W - P.r}" y1="${y(goal)}" y2="${y(goal)}" stroke="${cssVar('--primary-color')}" stroke-dasharray="5 4" stroke-width="1.5"/>`;
    g += `<text x="${P.l + 4}" y="${y(goal) - 5}" text-anchor="start" font-size="11" font-weight="600" fill="${cssVar('--primary-color')}" paint-order="stroke" stroke="${cssVar('--bg-secondary')}" stroke-width="3">goal ${goal}h</text>`;
    [0, Math.floor(s.length / 2), s.length - 1].forEach((i) => {
      if (!s[i]) return;
      const anchor = i === 0 ? 'start' : i === s.length - 1 ? 'end' : 'middle';
      g += `<text x="${P.l + i * bw + bw / 2}" y="${H - 6}" text-anchor="${anchor}" font-size="11" fill="${cssVar('--text-muted')}">${fmt(s[i].date)}</text>`;
    });
    $('#chart').innerHTML = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Nightly CPAP use, last 90 nights">${g}</svg>`;
  }

  function renderWeekly() {
    const rows = [...S.state.weekly].reverse();
    const head = `<thead><tr><th>${esc(t('week'))}</th><th>${esc(t('used'))}</th><th>${esc(t('at_goal'))}</th><th>${esc(t('avg'))}</th><th>${esc(t('leaks'))}</th><th>${esc(t('ahi'))}</th><th>${esc(t('events'))}</th><th>${esc(t('tried'))}</th></tr></thead>`;
    const body = rows.map((w) => `<tr>
      <td data-label="${esc(t('week'))}"><div><div class="small">${esc(fmt(w.week_start))}</div><div class="week">${w.days.map((d) =>
        `<span class="cell ${esc(d.status)} ${d.high_leak ? 'leak' : ''}" title="${esc(fmt(d.date))}${d.hours != null ? ': ' + d.hours + ' h' : ''}"></span>`).join('')}</div></div></td>
      <td data-label="${esc(t('used'))}">${w.nights_used}/${w.nights_recorded}</td>
      <td data-label="${esc(t('at_goal'))}">${w.nights_met}</td>
      <td data-label="${esc(t('avg'))}">${w.avg_hours} ${esc(t('hours'))}</td>
      <td data-label="${esc(t('leaks'))}">${w.high_leak_nights || '—'}</td>
      <td data-label="${esc(t('ahi'))}">${w.avg_ahi ?? '—'}</td>
      <td data-label="${esc(t('events'))}">${w.lapses_started || 0} / ${w.comebacks || 0}</td>
      <td data-label="${esc(t('tried'))}">${w.actions.length ? w.actions.map((a) => statusPill(a.status)).join(' ') : '—'}</td></tr>`).join('');
    $('#weeklyTable').innerHTML = head + `<tbody>${body}</tbody>`;
  }

  function statusPill(s) {
    const c = { helped: 'tag-success', not_helped: 'tag-danger', open: 'tag-info', replanned: '' }[s] || '';
    return `<span class="tag ${c}">${esc(t('st_' + s))}</span>`;
  }

  function renderHistory() {
    const h = S.state.history;
    if (!h.length) { $('#historyTable').innerHTML = `<tbody><tr><td>${esc(t('no_history'))}</td></tr></tbody>`; return; }
    $('#historyTable').innerHTML = `<thead><tr><th>${esc(t('date'))}</th><th>${esc(t('barrier'))}</th><th>${esc(t('step'))}</th><th>${esc(t('outcome'))}</th></tr></thead><tbody>` +
      h.map((iv) => `<tr>
        <td data-label="${esc(t('date'))}">${esc(fmt(iv.start))}</td>
        <td data-label="${esc(t('barrier'))}">${esc(iv.barrier_label)}<div class="small muted">${esc(iv.trigger_label)}</div></td>
        <td data-label="${esc(t('step'))}" class="wide">${esc(iv.action.title)} <span class="tag">BCT ${esc(iv.action.bct)}</span>${iv.action.care_team ? ` <span class="tag tag-warning">${esc(t('care_team'))}</span>` : ''}</td>
        <td data-label="${esc(t('outcome'))}">${statusPill(iv.status)}<div class="small muted">${esc(iv.outcome_note)}</div></td></tr>`).join('') + '</tbody>';
  }

  function renderLearner() {
    const l = S.state.learner;
    $('#learner').innerHTML = l.length ? l.map((r) => `<div class="learn-row"><span>${esc(r.title)} <span class="tag">BCT ${esc(r.bct)}</span></span>
      <span class="small"><span style="color:var(--success)">${r.helped}✓</span> · <span style="color:var(--danger)">${r.not_helped}✗</span></span>
      <div class="bar" style="grid-column:1/-1"><span style="width:${Math.round(r.score * 100)}%"></span></div></div>`).join('')
      : `<p class="muted">${esc(t('no_learn'))}</p>`;
  }

  function renderPersonOutcomes() {
    const o = S.state.outcomes;
    const v = (x, suf = '') => (x == null ? '—' : x + suf);
    $('#personOutcomes').innerHTML =
      stat(t('o_adh_first'), v(o.adherence_first_30, '%'), t('o_goal_nights')) +
      stat(t('o_adh_last'), v(o.adherence_last_30, '%'), o.persisting ? t('o_persisting') : t('o_below')) +
      stat(t('o_lapses'), o.lapses, t('o_recovered')(o.lapses_recovered)) +
      stat(t('o_days'), v(o.median_days_to_recover), t('o_days_sub')) +
      stat(t('o_hours'), `${v(o.usage_h_first_30)} → ${v(o.usage_h_last_30)}`, t('o_first_last')) +
      stat(t('o_ahi'), `${v(o.ahi_first_30)} → ${v(o.ahi_last_30)}`, t('o_first_last')) +
      stat(t('o_helped'), v(o.actions_helped_pct, '%'), t('o_judged')(o.actions_judged));
  }

  function renderCohort() {
    const c = S.cohort; if (!c) return;
    const o = c.overall, v = (x, s = '') => (x == null ? '—' : x + s);
    const H = [t('c_group'), t('c_people'), t('c_persist'), t('c_ci'), t('c_retained'), t('c_recovery'), t('o_helped')];
    const groups = Object.entries(c.by).map(([key, grp]) => `
      <h3>${esc(t('groups')[key] || key)} <span class="tag ${c.equity_gap_significant[key] ? 'tag-warning' : ''}">${esc(t('c_gap'))} ${c.equity_gaps[key] == null ? 'n/a' : c.equity_gaps[key] + ' pts · ' + (c.equity_gap_significant[key] ? t('c_sig') : t('c_noise'))}</span></h3>
      <div class="table-wrap"><table class="table rtable"><thead><tr>${H.map((h) => `<th>${esc(h)}</th>`).join('')}</tr></thead><tbody>
      ${Object.entries(grp).map(([g, s]) => `<tr><td data-label="${esc(H[0])}">${esc(g)}${s.people < c.min_group ? ` <span class="tag">${esc(t('c_small'))}</span>` : ''}</td><td data-label="${esc(H[1])}">${s.people}</td>
        <td data-label="${esc(H[2])}">${v(s.persisting_pct, '%')}</td><td data-label="${esc(H[3])}">${s.persisting_ci95 ? s.persisting_ci95.join('–') + '%' : '—'}</td><td data-label="${esc(H[4])}">${v(s.retained_pct, '%')}</td>
        <td data-label="${esc(H[5])}">${v(s.recovery_rate, '%')}</td><td data-label="${esc(H[6])}">${v(s.actions_helped_pct, '%')}</td></tr>`).join('')}
      </tbody></table></div>`).join('');
    $('#cohort').innerHTML = `<div class="stats-grid">
      ${stat(t('c_persist'), v(o.persisting_pct, '%'), t('c_persist_sub'))}
      ${stat(t('c_retained'), v(o.retained_pct, '%'), t('c_retained_sub'))}
      ${stat(t('c_lapses'), v(o.lapses_per_person), t('o_recovered')(v(o.recovery_rate, '%')))}
      ${stat(t('o_days'), v(o.median_days_to_recover), t('c_days_sub'))}
      ${stat(t('o_ahi'), `${v(o.ahi_first_30)} → ${v(o.ahi_last_30)}`, t('c_ahi_sub'))}
      ${stat(t('o_helped'), v(o.actions_helped_pct, '%'), t('c_helped_sub'))}
      </div>${groups}<p class="small muted">${esc(c.caveat)} ${esc(t('c_note')(c.min_group))}</p>`;
  }

  // ── Controls ───────────────────────────────────────────────────────────
  let rangeTimer;
  $('#dayRange').addEventListener('input', (e) => {
    S.idx = +e.target.value; $('#asofLabel').textContent = fmt(addDays(asOf(), 1));
    clearTimeout(rangeTimer); rangeTimer = setTimeout(() => loadState(asOf()), 180);
  });
  const step = (n) => { S.idx = Math.min(S.dates.length - 1, Math.max(0, S.idx + n)); return loadState(asOf()); };
  $('#prevDay').addEventListener('click', () => step(-1));
  $('#nextDay').addEventListener('click', () => step(1));
  $('#todayBtn').addEventListener('click', () => { stopPlay(); loadState(); });
  function stopPlay() { clearInterval(S.playing); S.playing = null; $('#playBtn').textContent = t('play'); }
  $('#playBtn').addEventListener('click', () => {
    if (S.playing) return stopPlay();
    if (S.idx >= S.dates.length - 1) S.idx = Math.max(0, S.dates.length - 60);
    $('#playBtn').textContent = t('pause');
    S.playing = setInterval(async () => {
      if (S.idx >= S.dates.length - 1) return stopPlay();
      await step(1);
    }, 700);
  });
  $('#persona').addEventListener('change', (e) => { stopPlay(); S.persona = e.target.value; $('#coachOut').textContent = ''; loadState(); });
  $$('.tab').forEach((b) => b.addEventListener('click', () => {
    $$('.tab').forEach((x) => x.classList.toggle('active', x === b));
    $$('.panel').forEach((p) => p.classList.toggle('active', p.id === 'panel-' + b.dataset.tab));
    if (b.dataset.tab === 'weekly') renderChart();
  }));
  $('#langBtn').addEventListener('click', async () => {
    const lang = S.lang === 'ar' ? 'en' : 'ar';
    applyLang(lang);
    setState(await post('/api/settings', { persona: S.persona, as_of: asOf(), language: lang }));
  });
  $('#coachBtn').addEventListener('click', async () => {
    const out = $('#coachOut'); const btn = $('#coachBtn');
    btn.disabled = true; out.textContent = t('loading');
    try {
      const r = await post('/api/coach', { persona: S.persona, as_of: asOf(), lang: S.lang });
      out.innerHTML = `<div lang="${esc(r.lang)}">${esc(r.text)}</div>` +
        (r.clinician_note ? `<p class="small" style="color:var(--danger);margin-top:var(--space-3)">${esc(r.clinician_note)}</p>` : '') +
        `<div class="tags" style="margin-top:var(--space-3)"><span class="tag ${r.source.startsWith('llm') ? 'tag-success' : ''}">${esc(r.source.startsWith('llm') ? r.source.replace('llm:', 'AI · ') + ' · ' + t('checked') : t('source_template'))}</span>
         ${r.fallback_reason ? `<span class="small muted">${esc(r.fallback_reason)}</span>` : ''}</div>`;
    } catch (e) { out.textContent = e.message; }
    btn.disabled = false;
  });
  $('#cohortBtn').addEventListener('click', async () => {
    const b = $('#cohortBtn'); b.disabled = true; $('#cohort').innerHTML = `<p class="muted">${esc(t('loading'))}</p>`;
    try { S.cohort = await api('/api/cohort'); renderCohort(); } catch (e) { $('#cohort').textContent = e.message; }
    b.disabled = false;
  });

  // Settings modal
  const modal = $('#settingsModal');
  function openSettings() {
    const p = S.state.profile, f = $('#settingsForm');
    ['goal_hours', 'nudge_hour', 'quiet_start', 'quiet_end'].forEach((k) => { f.elements[k].value = p[k]; });
    f.elements.language.value = p.language;
    ['nudges_enabled', 'use_llm', 'share_with_care_team'].forEach((k) => { f.elements[k].checked = !!p[k]; });
    $('#summaryOut').hidden = true;
    modal.hidden = false; modal.querySelector('.modal-close').focus();
  }
  const closeSettings = () => { modal.hidden = true; $('#settingsBtn').focus(); };
  $('#settingsBtn').addEventListener('click', openSettings);
  modal.addEventListener('click', (e) => { if (e.target === modal || e.target.hasAttribute('data-close')) closeSettings(); });
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && !modal.hidden) closeSettings(); });
  $('#settingsForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const f = e.target, body = { persona: S.persona, as_of: asOf() };
    ['goal_hours', 'nudge_hour', 'quiet_start', 'quiet_end'].forEach((k) => { body[k] = Number(f.elements[k].value); });
    body.language = f.elements.language.value;
    ['nudges_enabled', 'use_llm', 'share_with_care_team'].forEach((k) => { body[k] = f.elements[k].checked; });
    try { applyLang(body.language); setState(await post('/api/settings', body)); toast(t('saved')); closeSettings(); }
    catch (err) { toast(err.message); }
  });
  $('#summaryBtn').addEventListener('click', async () => {
    const out = $('#summaryOut'); out.hidden = false;
    try {
      const r = await api('/api/care-team-summary?' + new URLSearchParams({ persona: S.persona, as_of: asOf() }));
      out.textContent = JSON.stringify(r, null, 2);
    } catch (e) { out.textContent = e.message; }
  });

  // ── Add your data: one button, a drop zone, files / folder / zip, from phone or PC ──
  const MAX_UPLOAD = 64 * 1024 * 1024;
  const dataModal = $('#dataModal');
  const openData = () => { $('#dataResult').innerHTML = ''; $('#uploadProgress').hidden = true; dataModal.hidden = false; $('#dropzone').focus(); };
  const closeData = () => { dataModal.hidden = true; $('#addDataBtn').focus(); };
  $('#addDataBtn').addEventListener('click', openData);
  dataModal.addEventListener('click', (e) => { if (e.target === dataModal || e.target.hasAttribute('data-close')) closeData(); });
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && !dataModal.hidden) closeData(); });
  // Folder picking only where the browser supports it (desktop); phones pick files or a zip.
  const coarse = window.matchMedia('(pointer: coarse)').matches;
  if (coarse || !('webkitdirectory' in document.createElement('input'))) $('#pickFolderLabel').hidden = true;

  // Skip, before sending, what we would skip anyway: per-breath DATALOG files and the card's identity files.
  function precheck(path, size) {
    const p = path.toLowerCase().replace(/\\/g, '/'), name = p.split('/').pop();
    if (name.endsWith('.edf') && !name.endsWith('str.edf')) return 'datalog';
    if (/^identification\.|\.tgt$|\.crc$/.test(name) || p.includes('/settings/')) return 'device_identity';
    if (size > MAX_UPLOAD) return 'too_large';
    return null;
  }

  async function collectEntries(items) {
    const out = [];
    const walk = async (entry, prefix) => {
      if (entry.isFile) {
        const f = await new Promise((res, rej) => entry.file(res, rej));
        out.push({ file: f, path: prefix + f.name });
      } else if (entry.isDirectory) {
        const reader = entry.createReader();
        let batch;
        do {
          batch = await new Promise((res, rej) => reader.readEntries(res, rej));
          for (const e of batch) await walk(e, prefix + entry.name + '/');
        } while (batch.length);
      }
    };
    for (const it of items) { const e = it.webkitGetAsEntry && it.webkitGetAsEntry(); if (e) await walk(e, ''); }
    return out;
  }

  function sendFiles(list) {
    const send = [], skipped = [];
    for (const { file, path } of list) {
      const why = precheck(path, file.size);
      if (why) skipped.push({ file: path, reason: why }); else send.push({ file, path });
    }
    const total = send.reduce((a, x) => a + x.file.size, 0);
    if (!send.length) return showResult({ report: { found: [], skipped, skipped_counts: countBy(skipped), summary: { nights: 0 } } }, false);
    if (total > MAX_UPLOAD) return showError(t('too_big'));
    const fd = new FormData();
    send.forEach(({ file }) => fd.append('files', file, file.name));
    fd.append('paths', JSON.stringify(send.map((x) => x.path)));
    fd.append('skipped', JSON.stringify(skipped.slice(0, 500)));
    fd.append('tz_offset_min', String(-new Date().getTimezoneOffset()));
    upload('/api/upload', fd);
  }

  function upload(url, fd) {
    const bar = $('#uploadProgress'), fill = bar.querySelector('span');
    bar.hidden = false; fill.style.width = '2%';
    $('#dataResult').innerHTML = `<p class="muted">${esc(t('uploading'))}</p>`;
    const xhr = new XMLHttpRequest();
    xhr.open('POST', url);
    xhr.upload.onprogress = (e) => { if (e.lengthComputable) fill.style.width = Math.max(2, Math.round(95 * e.loaded / e.total)) + '%'; };
    xhr.onload = () => {
      fill.style.width = '100%';
      let data = {};
      try { data = JSON.parse(xhr.responseText); } catch (e) { /* not JSON */ }
      if (xhr.status === 413) return showError(t('too_big'));
      if (xhr.status === 200 || xhr.status === 422) return showResult(data, xhr.status === 200);
      showError(data.error || xhr.statusText);
    };
    xhr.onerror = () => showError('Network error');
    xhr.send(fd);
  }

  const countBy = (arr) => arr.reduce((m, x) => ((m[x.reason] = (m[x.reason] || 0) + 1), m), {});
  const showError = (msg) => { $('#uploadProgress').hidden = true; $('#dataResult').innerHTML = `<div class="alert alert-danger">${esc(msg)}</div>`; };

  function showResult(data, ok) {
    const r = data.report || {}, sum = r.summary || {};
    const rows = (r.found || []).map((f) => `<tr><td data-label="${esc(t('source'))}">${esc((t('src') || {})[f.source] || f.label)}</td>
      <td data-label="${esc(t('from_file'))}" class="wide">${esc(f.file)}${f.files > 1 ? ` <span class="tag">${f.files}</span>` : ''}</td>
      <td data-label="${esc(t('nights_col'))}">${f.nights}</td>
      <td data-label="${esc(t('range'))}">${f.first ? esc(fmt(f.first)) + '<br>' + esc(fmt(f.last)) : '—'}</td></tr>`).join('');
    const skips = Object.entries(r.skipped_counts || {}).map(([k, n]) =>
      `<li>${n} × ${esc((t('reasons') || {})[k] || k)}</li>`).join('');
    let head = '';
    if (ok) {
      head = `<div class="alert alert-success"><div class="found-summary">${esc(t('found_n')(sum.nights, fmt(sum.first), fmt(sum.last)))}</div>
        <div class="small">${esc(t('cpap_used')(sum.cpap_nights_used))}${sum.wearable_nights ? ' · ' + esc(t('wear_n')(sum.wearable_nights)) : ''}</div>
        <div class="btn-row"><button class="btn btn-primary" id="openDataBtn" type="button">${esc(t('open_data'))}</button></div></div>`;
    } else if (r.error === 'no_cpap') {
      head = `<div class="alert alert-warning">${esc(t('no_cpap'))}</div>`;
    }
    $('#uploadProgress').hidden = true;
    $('#dataResult').innerHTML = head +
      (rows ? `<div class="table-wrap"><table class="table rtable"><thead><tr><th>${esc(t('source'))}</th><th>${esc(t('from_file'))}</th><th>${esc(t('nights_col'))}</th><th>${esc(t('range'))}</th></tr></thead><tbody>${rows}</tbody></table></div>` : '') +
      (skips ? `<details><summary>${esc(t('skipped_title'))} (${(r.skipped || []).length})</summary><ul class="skip-list">${skips}</ul></details>` : '');
    if (ok) $('#openDataBtn').addEventListener('click', async () => { await loadPersonas(data.persona); await loadState(); closeData(); });
  }

  const dz = $('#dropzone');
  dz.addEventListener('click', () => $('#pickFiles').click());
  dz.addEventListener('keydown', (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); $('#pickFiles').click(); } });
  ['dragenter', 'dragover'].forEach((ev) => dz.addEventListener(ev, (e) => { e.preventDefault(); dz.classList.add('over'); }));
  ['dragleave', 'drop'].forEach((ev) => dz.addEventListener(ev, () => dz.classList.remove('over')));
  dz.addEventListener('drop', async (e) => {
    e.preventDefault();
    const items = [...(e.dataTransfer.items || [])];
    const list = items.length && items[0].webkitGetAsEntry ? await collectEntries(items)
      : [...e.dataTransfer.files].map((f) => ({ file: f, path: f.name }));
    sendFiles(list);
  });
  $('#pickFiles').addEventListener('change', (e) => { sendFiles([...e.target.files].map((f) => ({ file: f, path: f.name }))); e.target.value = ''; });
  $('#pickFolder').addEventListener('change', (e) => { sendFiles([...e.target.files].map((f) => ({ file: f, path: f.webkitRelativePath || f.name }))); e.target.value = ''; });
  $('#sampleBtn').addEventListener('click', () => {
    const fd = new FormData(); fd.append('tz_offset_min', '240'); upload('/api/upload-samples', fd);
  });
  $('#forgetBtn').addEventListener('click', async () => {
    const r = await post('/api/forget', {});
    toast(r.message); S.persona = 'layla'; await loadPersonas('layla'); await loadState(); closeSettings();
  });

  // Boot
  (async () => {
    applyLang('en');
    try { await loadPersonas(); await loadState(); }
    catch (e) { $('#story').textContent = 'Could not load: ' + e.message; }
  })();
})();
