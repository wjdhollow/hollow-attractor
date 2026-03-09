# Migrating to Hollow Attractor

Already tracking tasks somewhere else? This guide helps you bring your existing system into Hollow Attractor.

Works for any source: Notion, Todoist, plain text files, a custom Claude memory system, sticky notes, or just a mental backlog.

---

## Before you start

1. Install Hollow Attractor and complete `hollow init` — see [README](README.md#install)
2. Configure Claude Desktop and confirm the MCP server is connected
3. Gather your existing tasks — open the doc, app, or file you've been using

---

## Migration prompt

Once Hollow Attractor is running in Claude Desktop, paste this prompt to begin:

---

```
hollow, I want to migrate my existing tasks and projects into Hollow Attractor.
I'll share what I have and I'd like your help mapping it across.

Here's my existing system:
[paste or describe your tasks, projects, notes, or backlog here]

Please help me:
1. Identify natural worldline boundaries from what I've shared — each worldline
   should be one coherent scope (a project, a life area, a relationship, etc.)
2. For each worldline, map my existing items to the correct states:
   - Actionable: things I can act on right now
   - Waiting: blocked on someone or something external
   - Open questions: things I need to decide or find out
   - Decisions: choices already made, worth remembering
   - References: links, contacts, or facts to keep handy
3. Create each worldline and populate it with my items
4. Update the Ship Log to reflect the new worldlines
5. Commit everything

Take it one worldline at a time and confirm with me before moving to the next.
```

---

## Tips

**Be liberal with worldlines.** Work, home, a side project, a specific relationship — each gets its own worldline. It's cheaper to merge later than to untangle a cluttered one.

**Don't over-map.** Not everything in your old system needs to come across. Migration is a good time to drop stale tasks you were never going to do.

**Decisions are valuable.** If your old system has notes like "we decided to use X" or "went with Y approach" — bring those in as decisions. They're easy to lose and hard to reconstruct.

**Completed items can stay completed.** If you want a historical record, ask Claude to add them to the Completed section. If you'd rather start fresh, skip them.

---

## Migrating from another machine

If you already have a Hollow Attractor installation on another machine, use the **Imprint** export instead of this guide:

1. On the old machine, ask Claude: *hollow, write an imprint*
2. Copy the resulting `imprint-*.txt` file to the new machine
3. On the new machine (after `hollow init`), ask Claude: *hollow, restore from imprint* and provide the file contents

This preserves your full state — worldlines, items, decisions, Ship Log, and git history.
