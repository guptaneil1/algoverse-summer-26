---
description: Turn the work just completed in this session into a reusable command
---

Focus (optional): $ARGUMENTS

The session above contains work worth repeating. Extract the reusable procedure from
it. This is how the team's prompt library grows — from things that actually worked,
not from things that sounded good in the abstract.

## 1. Reconstruct what actually happened

Walk the session and write the real sequence: files read, in what order; commands run;
decisions made and why; corrections I issued and what they fixed. Be honest about the
detours — the corrections are the most valuable signal, because they mark where a
naive first attempt goes wrong.

## 2. Separate procedure from specifics

- **Procedure** — the steps that would apply to the next instance of this task.
- **Specifics** — the values, paths, and names that were particular to this run.
  These become `$ARGUMENTS` or explicit inputs.

## 3. Decide the right artifact

Recommend exactly one, with reasoning:

- **`.claude/commands/<name>.md`** — an explicit procedure I invoke by name.
- **`.claude/agents/<name>.md`** — an independent reviewer or investigator that should
  run with its own clean context and report back, so the main thread stays uncluttered.
- **A line in `CLAUDE.md`** — a standing constraint that should apply to every session,
  not a procedure.
- **None of these** — the work was genuinely one-off. Say so rather than manufacturing
  an artifact.

## 4. Write it

Produce the file contents, including the frontmatter `description` — that description
is what makes the command findable later, so write it as a trigger condition ("use
when ..."), not as a title.

Bake in the corrections from step 1 as explicit instructions, so the next run does not
repeat the detour.

## 5. Test it on paper

Give one example invocation and the first three actions it should produce. If those
three actions do not obviously beat just typing the request in plain English, the
command is not worth adding — say that.
