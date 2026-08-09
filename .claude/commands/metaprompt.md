---
description: Compile a rough task into a spec-grade prompt before doing any work
---

Rough task: $ARGUMENTS

You are acting as a **prompt compiler**, not as an implementer. Do not start the task.
Your only output this turn is a better prompt for the task, plus the questions needed
to write it.

## Step 1 — Orient (do this with real reads, not memory)

Read whichever of these bear on the task, and note what you actually opened:
`docs/STATUS.md`, `PROTOCOL.md`, `CLAIMS.md`, `PREREGISTRATION.md`,
`docs/ARCHITECTURE.md`, `docs/weekly/WEEK_4.md`, the relevant `docs/interfaces/*.md`
and `schemas/*.json`, plus the specific source files the task names.

## Step 2 — Ask blocking questions

List **at most three** questions, and only ones where a wrong guess would waste more
than an hour or produce an invalid artifact. Rank them. For each, give your current
best guess and what it would cost if that guess is wrong. If nothing is blocking, say
"no blocking questions" and continue.

Do not ask about things the repo already answers. Go look instead.

## Step 3 — Emit the compiled prompt

Output it in a fenced block so I can copy, edit, and re-issue it. Structure:

```
## Objective
One sentence. The observable end state, not the activity.

## Context to load first
Exact file paths, and what each is authoritative for.

## Constraints
- Which PROTOCOL.md invariants this task can violate if done carelessly
- Which schema or interface contract governs the output shape
- Ownership: whose workstream this touches (docs/TEAM.md, CODEOWNERS)
- Freeze status: is the touched artifact frozen, and what does that permit

## Definition of done
A checklist of verifiable conditions. Every item must be checkable by running a
command or reading a file — never "looks correct" or "is well designed".
Include the exact commands that prove it.

## Explicitly out of scope
The adjacent things that must NOT be changed in the same diff.

## Failure modes to avoid
The two or three specific ways this task usually goes wrong here — e.g. inventing a
number for a placeholder, widening a claim beyond its evidence, adding an unpre-
registered analysis, importing across an architecture boundary, touching the test
partition.

## Required self-check before reporting done
- Re-read the diff against Definition of done, item by item
- State VERIFIED / ASSUMED / UNKNOWN
- Name anything discovered mid-task that changes the plan
```

## Step 4 — Grade your own compiled prompt

In two or three lines: which part of it is weakest, and what information would let you
strengthen it. Then stop and wait for me.
