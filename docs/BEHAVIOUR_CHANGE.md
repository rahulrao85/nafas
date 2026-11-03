# Behaviour-change design

Challenge 09 asks for evidence-based behaviour support "with the rationale and limits of each approach visible". This page is the reviewer's view of that. In the app, each step shows its technique, why it should help, and where it stops helping.

## Principles

1. **One small action at a time.** Each step fits in one evening or one message. No to-do lists.
2. **No reset to zero.** Banked nights only go up. One short night a week doesn't break the run. A lapse starts a comeback goal of one hour (graded task, BCT 8.7), not a restart from day one.
3. **No blame.** Lapses are named as facts ("no CPAP for 3 nights"). The coach can't use words like *fail*, *lazy* or *should have*; drafts that do are rejected (see `nafas/safety.py`).
4. **The person's word beats the data.** A one-tap self-report outranks any data guess and re-plans the open step.
5. **Learn per person.** Each step is judged on the three nights after it (seven for care-team steps, because a refit or a part takes days). Thompson sampling over Beta(helped, not helped) offers better-scoring steps first but keeps trying others.
6. **Escalate, don't repeat.** Two misses in a row on the same barrier move to a care-team step (equipment provider or clinician).
7. **Clinical lines stay clinical.** Pressure, medication and diagnosis are out of scope. High residual AHI goes to the care team in fixed wording that never passes through the LLM.
8. **Autonomy.** The person can swap any step, skip it, turn nudges off, set quiet hours, turn AI wording off, and choose whether a care-team summary can be made.
9. **No manipulative engagement.** At most one nudge a day, only when there's something to do. If the person passes on three steps in a row, nudges drop to every other day. There are no streak-loss warnings, no countdowns and no rewards for opening the app.

## Techniques used (BCT Taxonomy v1, Michie et al. 2013)

Generated from `nafas/actions.py`. Arabic text exists for every title and step (first draft; needs native clinical review).

| Barrier | Detected from | Action | BCT | Care team |
|---|---|---|---|---|
| Mask fit or seal | data + self-report | Re-seat the mask lying down | 4.1 Instruction on how to perform the behaviour |  |
| Mask fit or seal | data + self-report | Run a one-minute fit check | 2.2 Feedback on behaviour |  |
| Mask fit or seal | data + self-report | Ask for a mask refit | 3.2 Social support (practical) | yes |
| Worn cushion or headgear | data + self-report | Wash the cushion this morning | 4.1 Instruction on how to perform the behaviour |  |
| Worn cushion or headgear | data + self-report | Swap in a spare cushion | 12.5 Adding objects to the environment |  |
| Worn cushion or headgear | data + self-report | Order a replacement | 3.2 Social support (practical) | yes |
| Taking the mask off mid-night | data + self-report | Make an if-then plan for waking up | 1.4 Action planning (implementation intention) |  |
| Taking the mask off mid-night | data + self-report | Note what woke you | 2.3 Self-monitoring of behaviour |  |
| Taking the mask off mid-night | data + self-report | Use the ramp when you put it back on | 4.1 Instruction on how to perform the behaviour |  |
| Away from home / travel | data + self-report | First night back: one hour counts | 8.7 Graded tasks |  |
| Away from home / travel | data + self-report | Pack the CPAP first next time | 12.1 Restructuring the physical environment |  |
| Changed sleep schedule | data + self-report | Tie the mask to your new bedtime | 8.3 Habit formation |  |
| Changed sleep schedule | data + self-report | Use it for every main sleep — day or night | 1.4 Action planning |  |
| Motivation dipping | data + self-report | Look at what you've already banked | 15.3 Focus on past success |  |
| Motivation dipping | data + self-report | Write your one reason | 1.9 Commitment |  |
| Motivation dipping | data + self-report | Ask one person to check in | 3.1 Social support (unspecified) |  |
| Pressure feels too strong | data + self-report | Practise 10 minutes awake | 8.1 Behavioural practice / rehearsal |  |
| Pressure feels too strong | data + self-report | Tell your care team the air feels too strong | 3.2 Social support (practical) | yes |
| Dry mouth or nose | self-report | Try one step more humidity | 4.1 Instruction on how to perform the behaviour |  |
| Dry mouth or nose | self-report | Ask about mouth leak | 3.2 Social support (practical) | yes |
| Feeling closed in | self-report | Get used to it in small steps | 8.7 Graded tasks |  |
| Feeling closed in | self-report | Ask about a lighter mask | 3.2 Social support (practical) | yes |
| Blocked nose or unwell | self-report | While you're unwell, any use counts | 8.7 Graded tasks |  |
| Forgot / fell asleep without it | self-report | Leave the mask on your pillow | 7.1 Prompts / cues |  |
| Forgot / fell asleep without it | self-report | Get one nudge at your bedtime | 7.1 Prompts / cues |  |
| Noise or bed partner | self-report | Route the hose away from your partner | 12.1 Restructuring the physical environment |  |
| Noise or bed partner | self-report | Ask your partner how they slept | 3.1 Social support (unspecified) |  |
| Felt fine without it | self-report | Feeling fine is the therapy working | 5.1 Information about health consequences |  |
| Felt fine without it | self-report | Try a two-week check | 1.5 Review behaviour goal(s) |  |

Lapse comeback (any barrier): "wear it for one hour tonight" — 8.7 Graded tasks.

## Limits we state openly

- The action library is written by the team, not yet reviewed by a sleep clinician or a behavioural scientist. Review is planned before any real-user exposure (see FHC_MASTER.md).
- "Helped" means the next three nights improved. That is a short, noisy signal; it can credit an action for a recovery that would have happened anyway. A pilot needs a comparison arm (see EVALUATION.md).
- Barrier guesses from data are heuristics with evidence shown, not diagnoses. Several barriers (dryness, claustrophobia, noise) can only come from self-report.
