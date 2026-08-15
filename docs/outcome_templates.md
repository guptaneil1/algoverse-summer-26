# Precommitted Interpretation Templates

**Deliverable:** `docs/weekly/WEEK_2.md` and `WEEK_3.md`, Ronit — outcome-contingent language for
favorable, null, harmful, and uncertain results.

**Why this file exists and why it is written now:** these templates must be authored *before* any
result is observed. Writing interpretation language after seeing an outcome is where motivated
reasoning enters. Authoring all four in advance makes the eventual choice mechanical: compute the
frozen contrast, read the decision rule, use the matching template.

**Status:** COMPLETE as structure. Two placeholders remain and are marked `{...}` — they cannot be
filled until the corresponding decisions are frozen.

## Placeholders

| Placeholder | Resolved by | Currently |
|---|---|---|
| `{MDE}` | Smallest scientifically meaningful effect | **U-006 — open** |
| `{CONTRAST}` | Frozen primary contrast: joint vs. strongest eligible non-joint baseline | Named in `PREREGISTRATION.md`, not numerically frozen |

Do not fill these by choosing values that make a template fit an observed result. That inverts the
entire purpose of this file.

## Decision rule — apply in order, stop at first match

Let `Δ` be the paired chain-level difference on the primary outcome for `{CONTRAST}`, with its
uncertainty interval `[L, U]`, sign convention: **negative Δ = joint policy is better** (lower
regret AUC).

| Order | Condition | Template |
|---|---|---|
| 1 | Any blocking validity failure — budget equality violated, leakage detected, manifest invalid, post-hoc exclusion required | **§5 Invalid** (overrides everything) |
| 2 | `U < -{MDE}` — entire interval favors joint by at least the meaningful effect | **§1 Favorable** |
| 3 | `L > +{MDE}` — entire interval favors the non-joint baseline by at least the meaningful effect | **§3 Harmful** |
| 4 | `[L, U]` lies entirely within `±{MDE}` — precise, and the effect is practically negligible | **§2 Null** |
| 5 | Interval spans `{MDE}` in either direction — underpowered | **§4 Uncertain** |

Note that §2 and §4 are different results. A tight interval around zero is *informative*: it says
adaptivity does not pay in this regime. A wide interval is *uninformative*. Reporting the second as
though it were the first would be a misrepresentation.

## §1 Favorable

**Applies when:** rule 2.

> **Abstract.** Under a fixed lifetime human-origin optimizer-token budget and matched total
> optimizer tokens, joint allocation across recursive generations and monitored human-distribution
> modes reduced chain-level held-out NLL regret relative to the strongest eligible non-joint
> baseline by {Δ} [{L}, {U}] across {n} paired chains in one licensed domain at the 124M–160M scale.

> **Results.** The joint policy's advantage over `{CONTRAST}` exceeded the preregistered smallest
> meaningful effect. Budget equality held exactly for every chain in the comparison.

> **Conclusion.** In the tested regime, *where* and *on which modes* a fixed human-data budget is
> spent affected chain-level outcomes, and the effect was not reproduced by either allocation axis
> alone.

**Mandatory scope sentence — include verbatim, do not soften:**

> This result is from one domain, one model scale, and one horizon. It does not establish that
> joint allocation prevents recursive-training degradation, that it is optimal, or that it
> generalizes to other domains, scales, or model families.

**Claim ledger:** C-002 → `SUPPORTED BY RUN ARTIFACTS`, scoped to the tested configuration. C-004
remains `unverified` regardless — a favorable empirical result does not establish novelty.

## §2 Null

**Applies when:** rule 4.

> **Abstract.** At matched lifetime human-token and total-token budgets, joint allocation did not
> measurably outperform the strongest eligible non-joint baseline: {Δ} [{L}, {U}], an interval
> contained within the preregistered practical-equivalence region.

> **Results.** The comparison was adequately precise to exclude an effect of meaningful size.

> **Conclusion.** In this regime the added adaptivity of joint allocation was not justified. A
> simpler fixed schedule or untargeted mixture achieved equivalent chain-level outcomes at the same
> cost, which is a useful negative result for practitioners choosing between them.

**Framing instruction:** present this as a finding, not a disappointment. `CLAIMS.md` states
explicitly that failure to beat a strong fixed schedule falsifies the practical motivation — that
falsification is a legitimate contribution and the introduction already commits to reporting it.

**Claim ledger:** C-002 → `NOT SUPPORTED` with the scope recorded. Entry added to `FAILURE_LOG.md`
as a null result, not a failure.

## §3 Harmful

**Applies when:** rule 3.

> **Abstract.** Joint allocation performed worse than the strongest eligible non-joint baseline at
> matched budgets: {Δ} [{L}, {U}].

> **Results.** The direction of the preregistered primary contrast was opposite to the hypothesized
> direction and exceeded the smallest meaningful effect.

> **Conclusion.** Targeting under-covered modes while also concentrating spend in time was actively
> counterproductive in this setting. The mechanism analysis in §{sec} examines whether this is
> consistent with over-fitting a biased monitor (C-003) or with concentration of human tokens away
> from modes carrying most held-out mass.

**Instruction:** do not bury this. A harmful result is reported in the abstract with the same
prominence a favorable one would receive. Do not add post-hoc exclusions, do not re-cut the
analysis, do not promote a secondary outcome to primary. If the harmful direction is suspected to
arise from an implementation defect, that requires *independent evidence of a defect*
(`FAILURE_LOG.md` entry rules) — suspicion alone does not license a rerun.

**Claim ledger:** C-002 → `CONTRADICTED`. C-003 gains supporting or non-supporting evidence
depending on the monitoring-omission arm.

## §4 Uncertain

**Applies when:** rule 5.

> **Abstract.** The paired comparison between joint and `{CONTRAST}` was inconclusive at the seed
> count achievable within the pilot's compute budget: {Δ} [{L}, {U}], an interval spanning the
> preregistered meaningful effect in {one/both} direction(s).

> **Results.** The pilot did not achieve the precision needed to separate the hypotheses. The
> observed chain-to-chain variance implies approximately {n_required} paired chains for a
> {power}-powered test, reported in the power analysis.

> **Conclusion.** This pilot establishes the pipeline, the budget-matching accounting, and the
> variance estimate needed to design a powered study. It does not answer the research question.

**Instruction:** an uncertain result may **not** be described using directional language. "Trended
toward," "suggests," "showed promise," and "directionally favorable" are prohibited here — they
convert an uninformative interval into an implied finding. State the interval and stop.

**Claim ledger:** C-002 remains `untested`. The pilot's contribution is the variance estimate and
the compute forecast.

## §5 Invalid

**Applies when:** rule 1, and it overrides every other template.

> No primary result is reported. Validation of {artifact} failed for {reason}; per `PROTOCOL.md` §5,
> no experimental value derived from it enters the abstract, claims, or presentation.

**Instruction:** the paper still ships, describing the design, the pipeline, the validation
machinery, and the failure honestly. `FAILURE_LOG.md` receives a full entry classifying the cause
as implementation, infrastructure, protocol, or scientific, with supporting evidence for the
classification.

## Figure and table captions

Write captions now; they do not depend on outcomes.

- **Table 1** — "Chain-level primary outcomes by treatment family. Each row is one budget-matched
  policy; each value aggregates {n} independently seeded recursive chains. Uncertainty is computed
  across chains, not across generations."
- **Figure 1** — "Generation-wise held-out human NLL by treatment family. Bands show chain-level
  uncertainty. Generations within a chain are repeated observations and are not independent."
- **Figure 2** — "Allocation of the lifetime human-token budget across generations and monitored
  modes, by policy. Every policy consumes an identical lifetime total by construction."
- **Figure 3** — "Monitoring-omission stress test: primary contrast when the monitored partition
  excludes a globally important mode."

Each caption must additionally carry the generating command and artifact hash, per `PROTOCOL.md`
§3 reproducibility.
