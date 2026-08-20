---
name: claim-licence
description: Check that a sentence stating a result is licensed by the evidence before it is written or kept. Use when writing, editing or defending any claim about what the experiment showed. Refuses unlicensed claims rather than softening them.
---

# Is this sentence licensed?

This project separates *what is true* from *what may be asserted*. A number can be correct
and the sentence containing it still not permitted, because the sentence implies something
the design cannot support. This skill is the check.

## The three authorities, in precedence order

1. **`CLAIMS.md`** — the claim contracts. C-002's "Allowed wording now" block carries the
   exact permitted sentence and an explicit **Not permitted** list. It wins over everything.
2. **`docs/evidence/claim_evidence_matrix.md`** — sentence-level licensing. Every abstract
   sentence has an ID and a licensing artifact. Includes **retirements**: sentences that were
   licensed once and are now false.
3. **`paper/outcome_contingent_language.md`** — precommitted templates. Which one is in force
   is recorded at the top of the file and must not be chosen to fit the result.

## Procedure

For the sentence in front of you:

**Step 1 — What does it assert?** Strip the hedging and write the bare claim. "Our results
suggest joint allocation may not offer benefits" asserts *joint is not better*. Hedging does
not change what is asserted; it changes how deniable it is, which is worse.

**Step 2 — Which claim does it touch?** C-002, C-003, C-004, or none. If none, it is not a
result sentence and this skill does not apply.

**Step 3 — Is it on the Not-permitted list?** Check verbatim. The current C-002 list:

- joint is *worse* than selection-only — **no**, the interval covers zero
- selection-only is near a ceiling — **no**, unmeasured, comparator 7 absent
- timing never matters — **no**, the confirmatory outcome disagrees

**Step 4 — Does it carry its mandatory companion?** A timing claim needs the confirmatory
disagreement or explicit scoping to the primary outcome. A statement of the null needs the
three unimplemented comparators. Both are in `claim_evidence_matrix.md` as rules, not
suggestions.

**Step 5 — Is it scoped?** One budget, one horizon, one corpus, one model. If the sentence
would still read as true about a 70B model, it is unscoped.

**Step 6 — Does an existing S-number cover it, and is that S-number retired?** Check the
retirement lists in every audit section, not only the newest.

## Verdicts

**LICENSED** — cite the S-number or the `CLAIMS.md` line that licenses it.

**LICENSED WITH REQUIRED COMPANION** — name the companion and confirm it is present in the
same paragraph, not merely somewhere in the paper.

**NOT LICENSED** — say which authority forbids it and **what the licensed version would be**.
Do not soften an unlicensed claim into a hedged one; a hedged unlicensed claim is still
unlicensed and is harder to catch on the next pass.

**NEEDS A NEW S-NUMBER** — the claim is defensible but nothing licenses it yet. Say what
artifact would license it. Adding an S-number is an audit entry, not a formality.

## The failure this exists to prevent

S20 — "we make no claim about allocation policy" — was licensed, true, and audited. Then the
run produced a result and the sentence became false, in four sections, while every check
still passed because each one verified that sentences trace to artifacts rather than that
they remain true. **Licensing is not permanent.** When the evidence changes, re-audit the
retirements first and the additions second.
