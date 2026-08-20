# Precommitted Interpretation Templates

Written before any primary result exists. Each template is the wording the paper
will use if that outcome occurs. Committing to the sentences in advance is what
stops the interpretation from being chosen after the numbers are seen.

**Rule:** pick the template the evidence selects. Do not blend two templates, and
do not soften an unfavourable one. Every `<placeholder>` is filled from a
generated file, never typed.

The primary contrast is C-002: joint versus the strongest eligible non-joint
baseline, at matched lifetime human-origin and total optimizer tokens, on
chain-level regret. `n` is always the number of independently seeded chains.

## Which templates the evidence selected, 2026-08-20

Recorded here so a reader of this file knows which sentences are in force and which
remain hypothetical. The templates below are unedited — the point of writing them in
advance is lost if they are revised once the numbers are known.

| Template | Applies? |
|---|---|
| **2. Null** | **Yes, to the primary contrast.** The interval lies inside the frozen practically equivalent region, so this is the governing template for `07_results.tex` and the abstract |
| **5. Mixed across metrics** | **Yes, to the *timing* contrast.** The primary outcome shows no detectable effect and the confirmatory tail-retention outcome shows a small one whose interval excludes zero. Per this template the primary conclusion follows the primary outcome and the disagreement is reported, not resolved in the convenient direction |
| **8. `valid_with_limitation`** | **Yes.** All 25 chains, on two standing grounds |
| 1. Favourable | No |
| 3. Harmful | No |
| 4. Uncertain or underpowered | **No, and the distinction matters.** The design is sized for three chains per arm at the preregistered threshold and ran five. The interval is inside the equivalence region rather than merely wide. Template 2 applies, not this one |
| 6. Reduced seed set | No. All 25 chains completed |
| 7. Excluded chain | No. `aggregate.json` records 25 included, 0 excluded |
| **9. No primary result at all** | **No longer.** It governed the 2026-08-18 grid, which no chain-level contrast survived. There is now a primary result |
| 10. Positive control mismatch | No |

---

## 1. Favourable

The interval for the primary contrast excludes the frozen practically
equivalent region in the direction favouring joint allocation.

> Across `<n>` independently seeded recursive chains at matched lifetime
> human-origin and total optimizer-token budgets, joint time-and-mode allocation
> reduced chain-level regret relative to the strongest non-joint baseline
> (`<paired mean difference>`, `<interval>`). The effect is estimated at pilot
> scale on one domain and one model size, and we do not claim it generalises
> beyond that setting.

Required alongside: the same contrast against every eligible baseline in the
C-002 contract, and the monitoring-omission result if it ran. Banned even here:
*first*, *optimal*, *prevents collapse*, *solves*, *state of the art*.

---

## 2. Null

The interval includes the frozen practically equivalent region.

> At matched budgets across `<n>` chains, we did not detect a difference between
> joint allocation and the strongest non-joint baseline (`<paired mean
> difference>`, `<interval>`). With `<n>` chains this design is powered to detect
> differences of approximately `<detectable effect>`; smaller effects remain
> possible. We report this as a null result, not as a trend.

Do not write "directionally consistent", "promising", or "approaching
significance". An interval spanning the equivalence region is a null.

---

## 3. Harmful

The interval excludes the equivalent region in the direction favouring the
baseline.

> Joint allocation performed worse than the strongest non-joint baseline at
> matched budgets (`<paired mean difference>`, `<interval>`). Under the
> preregistered falsification rule this outcome does not support C-002. We report
> the negative result and record it in `FAILURE_LOG.md`.

State this in the abstract, not only the discussion.

---

## 4. Uncertain or underpowered

Chains completed but too few for the preregistered minimum, or intervals too wide
to separate any hypothesis.

> `<n>` of `<planned n>` planned chains completed within the compute budget. The
> resulting interval (`<interval>`) is too wide to distinguish the preregistered
> hypotheses, so we draw no conclusion about C-002. We report the scaffold, the
> completed chains, and their validity classifications.

---

## 5. Mixed across metrics

Regret AUC and tail retention disagree in direction.

> The two preregistered outcomes disagree: `<outcome A>` on chain-level regret
> and `<outcome B>` on tail retention. We do not select the more favourable
> metric. Because the preregistration names `<primary metric>` as primary, the
> primary conclusion follows it and the disagreement is reported as a limitation.

---

## 6. Reduced seed set

Fewer chains than planned, from documented failures rather than selection.

> The primary analysis uses `<n included>` of `<n attempted>` chains. Excluded
> chains and their reason codes are listed in `<classification file>`; every
> exclusion follows a rule frozen before the results freeze. Excluded chains
> remain in the run index.

Never drop a chain because its outcome is inconvenient.

---

## 7. Excluded chain

One or more chains classified `invalid`.

> `<k>` chains were classified invalid by the independent validator for
> `<reason codes>` and are excluded from the primary aggregate. The exclusion
> rule was frozen before the audit. Their artifacts are preserved.

---

## 8. valid_with_limitation

Chains analysable, but a documented issue limits interpretation.

> `<k>` of `<n>` chains carry the limitation `<limitation category>`. They are
> included in the primary aggregate because the limitation does not affect the
> central comparison; we report the sensitivity analysis excluding them as
> `<sensitivity result>`.

If the sensitivity analysis reverses the conclusion, the conclusion is the
sensitivity result, not the primary one.

---

## 9. No primary result at all

No chain completed by the freeze.

> No primary chain completed before the results freeze. This paper reports the
> preregistered design, the validated scaffold, the positive-control status, and
> the validity tooling. C-002 and C-003 remain untested. We make no empirical
> claim about allocation policy.

This is a legitimate outcome. It is not a failure of honesty; concealing it
would be.

---

## 10. Positive control mismatch

The reference reproduction does not match its published comparison.

> The positive-control reproduction `<matched / did not match>` its published
> reference (`<observed>` versus `<expected>`). `<If mismatched:>` Because the
> pipeline does not reproduce a known result, we do not interpret any primary
> contrast as evidence about allocation policy, and we report the mismatch as the
> principal limitation.

A positive-control failure caps every downstream claim. It cannot be reported as
a footnote.
