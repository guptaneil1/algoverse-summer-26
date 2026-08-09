# Week 3 Significance Review

> **STATUS: NOT CONDUCTED.**
> This file is the prepared record, not a completed review. No reviewer has
> assessed the contribution. Nothing here may be cited as evidence that a
> significance review happened. Delete this banner only when a real reviewer has
> completed the sections below.

A significance review requires someone with enough domain familiarity to name
prior work you did not cite. The `novelty-adversary` subagent can rehearse this
argument, but it is **not** a substitute — the packet requires an outside
reviewer, and an agent cannot be the outside reviewer of record.

---

## Reviewer

| Field | Value |
|---|---|
| Identity or role | TODO(ronit) |
| Relevant expertise | TODO(ronit): must be able to evaluate recursive training / data selection |
| Relationship to project | Must be external to the four workstreams |
| Date of review | TODO(ronit) |
| Materials provided | TODO(ronit): commit, PDF, CLAIMS.md, `docs/evidence/closest_work.csv` |

## Questions the reviewer must answer

**1. Is the contribution meaningful at pilot scope?**

Pilot scale, one domain, one model size, few chains. Given that, is the work
worth reading?

- TODO(ronit)

**2. Which claim is overstated?**

Point the reviewer at CLAIMS.md C-004 and the contribution paragraph. Ask them to
name the single most overstated sentence.

- TODO(ronit)

**3. What prior work or alternative explanation most threatens significance?**

The team's own logged threats are Threat 3 (detection-based importance
resampling, `drayson_2025`) and Threat 4 (dynamic mixture optimization,
`zhao_2026_regmixd`, `wang_2026_tikmix`). Ask specifically whether the reviewer
knows work these miss — the value is in what is *not* already in
`closest_work.csv`.

- TODO(ronit)

**4. What evidence would change your judgement?**

The most useful answer in the review. It names the experiment worth running next.

- TODO(ronit)

## Verdict on C-004 as written

Circle one and record the reviewer's reasoning:

- ☐ **Survives** as written, with the recursive / fixed-lifetime-budget /
  matched-non-joint-baselines qualifiers
- ☐ **Must narrow** — record the narrowest defensible sentence, paste-ready
- ☐ **Must drop** — record which prior work defeats it

Narrowest claim the reviewer could not defeat:

> TODO(ronit): paste-ready sentence

## Response

| Objection | Exact change made (file + section) | Or: why not changed |
|---|---|---|
| TODO | TODO | TODO |

## Unresolved

- TODO(ronit)

---

### Novelty stop rule

Per CLAIMS.md: if primary-source review finds a method that already jointly
allocates a fixed lifetime human-origin optimizer-token budget across recursive
generations and monitored human-distribution modes under comparable feedback and
matched baselines, **withdraw or rewrite C-004 before implementing the proposed
method.** Record that decision here if it is triggered.
