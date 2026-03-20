# Hollow Attractor — Schema Reference

These are the canonical file templates used when bootstrapping worldlines and managing state.
This document is referenced by the system prompt. It is not part of the protocol itself.

---

## attractor/ship-log.md

```markdown
# Ship Log
last_updated: {YYYY-MM-DD}

## Active Worldlines
- {slug} (ACTIVE, last active: {YYYY-MM-DD})
- {slug} (MONITORING, last active: {YYYY-MM-DD})
- {slug} (DEFERRED, last active: {YYYY-MM-DD})

## Closed Worldlines
(none)

## Active Divergences
- div-{slug}: {worldline-a} <-> {worldline-b} (since {YYYY-MM-DD})

## Resolved Divergences
(none)

## Recent Meaningful Updates (rolling 14 days)
- {YYYY-MM-DD}: [{worldline}] {one-line description}

## Reminders
- {YYYY-MM-DD}: {description} — {worldline}

## Anneal History
(none)
```

---

## worldlines/{slug}/state.md

```markdown
# Worldline: {slug}
created: {YYYY-MM-DD}
status: ACTIVE
okr: []
tags: []
last_anneal: null
last_updated: {YYYY-MM-DD}

## Summary
(not yet written)

## Current Focus
(not yet set)

## Open Questions
(none)

## Key Decisions
(none)

## References
(none)

## Ingestion Log
(none)

## Divergences
(none)
```

When a worldline is CLOSED, append this section:

```markdown
## Closing Summary
closed: {YYYY-MM-DD}

### Accomplished
- {bullet summarizing what was done}

### Unanswered
- {Q-N}: {question text} (since {date})

### Follow-up Issues Filed
- [{target-worldline}] {item-id or description}
```

---

## worldlines/{slug}/items.md

```markdown
# Items: {slug}
last_updated: {YYYY-MM-DD}

## Inbox
(none)

## Actionable
(none)

## Waiting
(none)

## Completed
(none)
```

---

## worldlines/{slug}/archive/recent.md

```markdown
# Archive — Recent (last 7 days): {slug}
last_updated: {YYYY-MM-DD}

(none)
```

---

## worldlines/{slug}/preferences.yaml

```yaml
# Per-worldline preferences — all fields optional, override global
# anneal_threshold_days: 14
# stale_question_days: 21
```

---

## attractor/tag-index.md

```markdown
# Tag Index
last_updated: {YYYY-MM-DD}

| tag | worldlines |
|-----|------------|
| {tag} | {slug}, {slug} |
```

Tags are free-form lowercase strings defined at the worldline level.
The tag index is derived — updated by the protocol whenever worldline tags change.
Use it for cross-worldline discovery: `hollow, find worldlines tagged {tag}`.

---

## attractor/okr.md

```markdown
# OKR Index
last_updated: {YYYY-MM-DD}

## Active OKRs

| slug | description |
|------|-------------|
| {okr-slug} | {one-line description of the objective} |

## Archived OKRs
(none)
```

OKR slugs should be short, hyphen-separated, and scoped to a cycle if useful (e.g. `q1-growth`, `reliability-2026`).
Worldlines reference OKR slugs in their `okr:` frontmatter field.

---

## attractor/preferences.yaml

```yaml
hollow_version: 0.2.0
reminder_surfacing: on_invocation   # on_invocation | disabled
anneal_threshold_days: 7
stale_question_days: 14
git_auto_commit: true
default_worldline: null
theme: default                      # default | kurisu | custom
```

---

## .gitignore

```
# (Imprint files are written to ~/hollow-backups/ outside this repo — no gitignore entry needed)
```

---

## attractor/divergences/div-{slug}.md

```markdown
# Divergence: {worldline-a} <-> {worldline-b}
id: div-{slug}
worldlines: [{worldline-a}, {worldline-b}]
created: {YYYY-MM-DD}
status: active

## What caused this divergence
{One paragraph.}

## Divergence point
Trigger: {event} — {YYYY-MM-DD}
  - {worldline-a}: {how it manifests here}
  - {worldline-b}: {how it manifests here}

## Linked items
- {worldline-a}: [{ID}] {title}
- {worldline-b}: [{ID}] {title}

## Notes
{Cross-worldline reasoning or shared blockers.}

## Resolution
(open)
```

---

## Item format (within items.md)

```markdown
- [ ] [{PREFIX}-{N}] {title}
  type: {task|question|decision|update|reference}
  state: {inbox|actionable|waiting|completed}
  created: {YYYY-MM-DD}
  updated: {YYYY-MM-DD}
  due: {YYYY-MM-DD or null}
  waiting_on: {person or event, if waiting}
  waiting_detail: {what is fully blocked vs what can continue}
  next_action: {one sentence}
  cross_worldline: {div-slug or null}
  notes: {optional free-text context, observations, or detail that does not fit other fields}
  correction_log:
    - {YYYY-MM-DD}: {field changed — old value → new value}
```

**ID prefix conventions:**
- `INB` — inbox
- `ACT` — actionable
- `WAI` — waiting
- `CMP` — completed (before archiving, rare)
- `Q` — question
- `DEC` — decision
- `REF` — reference

Use only these prefixes. IDs never change when state changes. The prefix reflects creation-time state for traceability.

**Ordering:** Within each section, items are ordered by creation date ascending (oldest first).

**Correction log:** Always use arrow format: `{field} — old value → new value`.

---

## ~/hollow-backups/imprint-{YYYY-MM-DD}.txt

Plain text. Human-readable. Semi-structured for parsing.
Stored outside ~/.hollow-attractor — never committed, not gitignored (not in the repo at all).

```
HOLLOW ATTRACTOR — IMPRINT
Generated: {YYYY-MM-DD}
Source version: {hollow_version}

This file captures the current state of all worldlines and can be used to
restore a Hollow Attractor installation without losing context. Git history
does not transfer. Provide this file to a new installation with:
  hollow, restore from imprint [path]

================================================================================
WORLDLINE: {slug}
Status: active

Summary: {state.md Summary content}

Current focus: {state.md Current Focus content}

Open items:
  [{ID}] {title}
    State: {state} — {waiting_on or next_action}
    Next action: {next_action}
    Notes: {notes if present}

  (repeat for each open item — inbox, actionable, waiting)

Open questions:
  {Q-N}: {question text} (since {date})

Key decisions:
  {date}: {decision text}

References:
  {label} — {identifier or path}

Ingestion history:
  {YYYY-MM-DD HH:MM}: {source description} ({source_type})
    Items created: {N} | Questions: {N} | References: {N}

Recent completions (last 30 days):
  [{ID}] {title} — completed {date}
    {2-4 sentence summary}

Archived completions ({YYYY}):
  {Month}: {yearly one-liner}

================================================================================
(repeat WORLDLINE block for each worldline)

================================================================================
DIVERGENCES

Active:
  div-{slug}: {worldline-a} <-> {worldline-b} (since {date})
    Summary: {what caused it and current state}

Resolved:
  div-{slug}: {worldline-a} <-> {worldline-b} (resolved {date})
    Outcome: {resolution summary}

================================================================================
END OF IMPRINT
```

**Parsing rules for restore:**
- Each `WORLDLINE:` block becomes one worldline directory.
- Items under "Open items" are re-classified by the current schema.
- "Key decisions" become entries in `state.md ## Key Decisions`.
- "References" become entries in `state.md ## References`.
- "Ingestion history" is reproduced verbatim in `state.md ## Ingestion Log`.
- "Recent completions" go into `archive/recent.md`.
- "Archived completions" go into `archive/{YYYY}.md`.
- Divergences are noted in each worldline's `state.md ## Divergences` but detail files are not reconstructed.

---

## archive/{YYYY-MM}.md

```markdown
# Archive — {Month YYYY}: {slug}

## {Month YYYY}
- [{ID}] {title} — completed {YYYY-MM-DD}
  {2–4 sentence summary. What was done, outcome, any references worth keeping.}
```

---

## archive/{YYYY}.md

```markdown
# Archive — {YYYY}: {slug}

- {Month}: {one-line summary of what was completed this month}
- {Month}: {one-line summary}
```
