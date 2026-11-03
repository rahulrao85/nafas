/* Nafas — single-page UI. No framework; talks to the Flask API. */
(() => {
  'use strict';

  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => [...el.querySelectorAll(s)];
  const esc = (v) => String(v ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  // Dates are always DD-Mon-YYYY, isolated left-to-right so Arabic layout doesn't reorder them.
  const fmt = (iso) => { if (!iso) return '—'; const [y, m, d] = iso.split('-'); return `⁦${d}-${MON[+m - 1]}-${y}⁩`; };
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
      upload_help: 'Parsed in memory for this session only. Never saved to disk.', forget: 'Delete everything from this session',
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
      upload_help: 'تُعالج في الذاكرة لهذه الجلسة فقط ولا تُحفظ.', forget: 'احذف كل ما في هذه الجلسة',
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
    const lastSub = ln.usage_min > 0
      ? [ln.leak95_lpm != null ? `leak ${ln.leak95_lpm} L/min` : '', ln.ahi != null ? `AHI ${ln.ahi}` : ''].filter(Boolean).join(' · ')
      : '—';
    $('#stats').innerHTML =
      `<div class="stats-card"><div class="stat-label">${esc(t('last_night'))} ${statusTag(ln.status)}</div><div class="stat-value">${ln.hours} ${esc(t('hours'))}</div><div class="stat-sub">${esc(lastSub)}</div></div>` +
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
        <td data-label="${esc(t('barrier'))}">${esc(iv.barrier_label)}<div class="small muted">${esc(iv.trigger)}</div></td>
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
      stat('Adherence, first 30 nights', v(o.adherence_first_30, '%'), 'Nights at goal') +
      stat('Adherence, last 30 nights', v(o.adherence_last_30, '%'), o.persisting ? 'Persisting (≥70%)' : 'Below 70%') +
      stat('Lapses', o.lapses, `${o.lapses_recovered} recovered`) +
      stat('Median days to recover', v(o.median_days_to_recover), 'Lapse start → 3 of 4 nights at goal') +
      stat('Hours a night', `${v(o.usage_h_first_30)} → ${v(o.usage_h_last_30)}`, 'First vs last 30 nights') +
      stat('Residual AHI', `${v(o.ahi_first_30)} → ${v(o.ahi_last_30)}`, 'First vs last 30 nights') +
      stat('Steps that helped', v(o.actions_helped_pct, '%'), `${o.actions_judged} judged`);
  }

  function renderCohort() {
    const c = S.cohort; if (!c) return;
    const o = c.overall, v = (x, s = '') => (x == null ? '—' : x + s);
    const groups = Object.entries(c.by).map(([key, grp]) => `
      <h3>${esc(key.replace('_', ' '))} <span class="tag ${c.equity_gap_significant[key] ? 'tag-warning' : ''}">gap ${c.equity_gaps[key] == null ? 'n/a' : c.equity_gaps[key] + ' pts' + (c.equity_gap_significant[key] ? ' · intervals don’t overlap' : ' · within noise')}</span></h3>
      <div class="table-wrap"><table class="table rtable"><thead><tr><th>Group</th><th>People</th><th>Persisting</th><th>95% CI</th><th>Retained</th><th>Recovery rate</th><th>Steps helped</th></tr></thead><tbody>
      ${Object.entries(grp).map(([g, s]) => `<tr><td data-label="Group">${esc(g)}${s.people < c.min_group ? ' <span class="tag">small n</span>' : ''}</td><td data-label="People">${s.people}</td>
        <td data-label="Persisting">${v(s.persisting_pct, '%')}</td><td data-label="95% CI">${s.persisting_ci95 ? s.persisting_ci95.join('–') + '%' : '—'}</td><td data-label="Retained">${v(s.retained_pct, '%')}</td>
        <td data-label="Recovery rate">${v(s.recovery_rate, '%')}</td><td data-label="Steps helped">${v(s.actions_helped_pct, '%')}</td></tr>`).join('')}
      </tbody></table></div>`).join('');
    $('#cohort').innerHTML = `<div class="stats-grid">
      ${stat('Persisting at 6 months', v(o.persisting_pct, '%'), '≥70% of last 30 nights at goal')}
      ${stat('Retained', v(o.retained_pct, '%'), 'Used ≥4 of last 28 nights')}
      ${stat('Lapses per person', v(o.lapses_per_person), `${v(o.recovery_rate, '%')} recovered`)}
      ${stat('Median days to recover', v(o.median_days_to_recover), 'Across recovered lapses')}
      ${stat('Residual AHI', `${v(o.ahi_first_30)} → ${v(o.ahi_last_30)}`, 'Biomarker, first vs last 30')}
      ${stat('Steps that helped', v(o.actions_helped_pct, '%'), 'Judged on next 3 nights')}
      </div>${groups}<p class="small muted">${esc(c.caveat)} Equity gaps count only groups of ${c.min_group}+ people. Attributes here are assigned at random, so any gap is chance — which is why a pilot must pre-register comparisons and correct for multiple testing.</p>`;
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
  $('#uploadForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    if (!fd.get('file') || !fd.get('file').name) return toast('Choose a file first.');
    try {
      const r = await api('/api/upload', { method: 'POST', body: fd });
      await loadPersonas(r.persona); await loadState(); closeSettings(); toast(`${r.nights} nights loaded.`);
    } catch (err) { toast(err.message); }
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
