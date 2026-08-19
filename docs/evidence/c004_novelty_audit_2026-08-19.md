# C-004 — novelty position, audited internally

**Date:** 2026-08-19
**Scope:** an audit of the novelty evidence already recorded, against C-004's own contract.
**This is not the external review C-004 requires**, and does not satisfy it. It is the
strongest statement the project can make without one, and it names exactly what is missing.

## Why this is not an external review

C-004's contract calls for primary-source review by someone outside the work. Everyone who
has examined this novelty claim is inside it. An internal party cannot supply the thing an
external review provides — an adversarial reader with no stake in the answer — and calling
this document an external review would be the kind of overclaim that costs more credibility
than the review itself would have bought.

What follows is therefore: does the recorded evidence, taken at face value, satisfy the
contract's own stop rule? That question is answerable internally because the stop rule is
mechanical.

## The recorded evidence

`docs/evidence/closest_work.csv`: **23 entries, all `audit_status = reviewed_primary`** —
none accepted on abstract alone. Threat levels: 12 high, 11 medium. Supporting material in
`docs/evidence/hostile_novelty_review.md` (five written novelty threats with responses) and
`docs/evidence/domain_audit.md`.

The contract names eight required search families: recursive learning with fresh human
data; finite budget scheduling across iterations; dynamic mixtures over training time;
active/surprise/tail/semantic/importance selection; adaptive coverage sampling; selection
bias under corrupted references; verification and synthetic-data filtering; and
accumulation/replacement protocols. The recorded entries span all eight.

## The stop rule, applied

> If primary-source review finds a method that already jointly allocates a fixed lifetime
> human-origin optimizer-token budget across recursive generations and monitored
> human-distribution modes under comparable feedback and matched baselines, withdraw or
> rewrite C-004.

Four conditions must hold together. Across all 23 entries, **no entry satisfies all four**,
and none satisfies even three cleanly. The pattern in the recorded differences is
consistent:

- **Recursive, but no lifetime budget.** The collapse literature establishes degradation
  and tail loss without treating human data as a finite stock to allocate. Fresh-data
  fractions are set as ratios, not spent from a budget.
- **Budgeted, but not recursive.** Data-selection and mixture work fixes token budgets
  within a single training run; there is no generation-over-generation recursion for a
  schedule to act across.
- **Scheduled, but not mode-targeted.** Where a schedule varies over time it is static or
  ratio-based, not responsive to monitored per-mode coverage.
- **Mode-aware, but not budget-allocating.** Where rare modes appear they are *analyzed*
  rather than *targeted* — the recurring phrase in the difference column is "analyzed, not
  targeted" or "tracked, not selected". Domain-level mixture work targets domains, not
  monitored distribution modes, and does not spend a human-origin budget to do it.

**The stop rule is not triggered by the recorded evidence.** C-004 stands as a provisional
novelty claim.

## What this does and does not license

**Licensed:** stating the problem framing as distinguishable from the 23 reviewed works,
with the difference column as the basis, and describing the search as primary-source across
eight named families.

**Not licensed:** any unqualified novelty claim. The banned-words rule applies and the
paper must not assert being the only or the earliest work of its kind. Two limits are
material and belong in the text:

1. **No external review has taken place.** A reader should be told that the novelty
   assessment is internal.
2. **The search has a date horizon.** It was assembled during this project and has not been
   refreshed. Recursive-training work moves quickly, and a paper submitted months later
   should re-run the search before asserting the position holds.

A third limit is structural rather than bibliographic: the oracle upper bound
(`PROTOCOL.md`'s sixth treatment family) is not implemented, so even a fully valid result
would leave the headroom above these policies unmeasured. That bounds the contribution
independently of what prior work exists.

## Disposition

C-004 moves from `Unverified` to **`Internally audited; external review outstanding`**.
That is a real change — the stop rule has now been applied on record rather than assumed —
and it is not the verification the contract asks for.

Obtaining an external read remains the cheapest available improvement to the submission: it
costs nothing but someone else's attention, and it is the one open item that would convert
a hedged novelty position into a checked one.
