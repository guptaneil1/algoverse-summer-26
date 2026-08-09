---
description: Reconcile documented status against what the repository can actually prove
---

Scope (default: whole repo): $ARGUMENTS

Compare what the documents assert against what the artifacts prove. The failure mode
this defends against is a repository that drifts into believing its own scaffolding.

## Evidence pass

For each row of `docs/STATUS.md` and each claim in `CLAIMS.md`, find the artifact that
would justify the stated status: a merged PR, a tag, a validating run manifest, a
report, a passing test. Record what you actually found — not what the file says exists.

Rules for this pass:

- Code existing is not evidence that a thing was run.
- A test passing is not evidence that a scientific result holds.
- A file being present is not evidence that its contents were validated.
- A `TODO` is evidence of absence, and should be counted as such.

## Drift report

Three lists:

- **Overstated** — status claims more than the artifacts support. Give the corrected
  status verbatim, ready to paste.
- **Understated** — artifacts support more than the status claims. Rarer, but it
  matters, because understated status hides finished work from the deadline plan.
- **Unevidenced** — no artifact either way; the honest status is unknown.

## Deadline reality

Today's date against `docs/weekly/WEEK_4.md`. Which August 13 deliverables are on
track, at risk, or not started, judged only by artifacts that exist. Then the critical
path: the smallest set of things that must happen, in order, for a truthful submission
on August 15 — including the possibility that the truthful submission reports a
scaffold and a positive control rather than a novel result. That is a legitimate
outcome under this protocol, and the plan should say so plainly rather than assuming
the pilot lands.
