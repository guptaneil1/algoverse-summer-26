# Claim Ledger

No claim in this file is a result unless its status is explicitly `SUPPORTED BY RUN ARTIFACTS`.

## Current claims

| ID | Type | Exact statement | Evidence needed | Status |
|---|---|---|---|---|
| C-000 | Fact about this repository | No Human Data Budget experiment has been run or verified in this repository | Repository audit | Verified |
| C-001 | Literature-grounded motivation | Recursive training on generated data can degrade model fit, diversity, or tail coverage in studied settings, while the outcome depends strongly on the data workflow and source distribution | Audited primary literature | Supported with scope qualifiers |
| C-002 | Hypothesis | At equal lifetime human-token budget and total optimizer-token budget, joint allocation across time and under-covered modes reduces chain-level regret relative to the strongest schedule-only and selection-only baselines | Powered recursive-chain experiment | Untested |
| C-003 | Hypothesis | The advantage of targeted allocation decreases or reverses when the monitoring reference omits globally important modes | Predeclared monitoring-bias intervention | Untested |
| C-004 | Provisional novelty claim | The exact joint problem of allocating one fixed lifetime stock of human-origin optimizer tokens across recursive generations and monitored human-distribution modes is distinguishable from the closest audited work | Saturated search, external expert review, and continuing 2026 search | Unverified and deliberately narrow |
| C-005 | Proposed mechanism | Under-covered modes with high projected future regret may have greater marginal value for human anchors | Theory or mechanism intervention plus experiment | Untested |

## Provisional contribution paragraph

This project formulates a result-free experimental question about **resource allocation**, not a claim that a new collapse-prevention method already works. Given a recursive horizon, a frozen monitored partition of a human reference distribution, and one fixed lifetime budget of human-origin optimizer-consumed tokens, the study will compare policies that allocate the same budget randomly, only across generations, only across modes, or jointly across generation and mode. The intended empirical contribution is a matched chain-level test of whether joint allocation changes held-out human-distribution regret and tail retention, together with a predeclared monitoring-omission stress test. The contribution is provisional because closely related work already studies accumulation, fixed real-data fractions, importance resampling, dynamic domain mixtures, and tail-aware robustness; the remaining distinction is the conjunction of recursion, exact lifetime human-token accounting, time allocation, mode allocation, and matched non-joint baselines.

## Five strongest novelty threats and honest responses

### Threat 1 — Accumulation may already solve the practical problem

**Closest work:** `gerstgrasser_2024` and `kazdan_2025` show that accumulating real and synthetic data can avoid or substantially slow collapse in several settings, and Kazdan et al. also study fixed-size subsets sampled from accumulated data.

**Strongest honest response:** This work must not claim that human data is the only way to prevent collapse or that accumulation is inadequate. Its narrower question assumes human-origin tokens are scarce and exactly budgeted, then asks how to spend that fixed stock. Accumulation remains a required baseline or design alternative where feasible. If accumulation under matched optimizer-token accounting dominates all budgeted rescue policies, the correct result is that the proposed allocation problem offers no benefit in the tested setting.

### Threat 2 — Fresh-real schedules and biased sampling may already combine time and distribution

**Closest work:** `alemohammad_2024` varies fixed or fresh real data across generations and studies biased synthetic sampling that trades quality against diversity.

**Strongest honest response:** The paper combines two relevant axes, so it is a high threat. The residual distinction is that its fresh-real quantity is specified per generation rather than drawn from one fixed lifetime human-token stock, and its sampling bias is not an allocation over frozen monitored human modes. We may claim only that the exact constrained optimization and matched schedule-only/selection-only decomposition differs, not that time-aware or distribution-aware recursive sampling is new.

### Threat 3 — Detection-based importance resampling may already be the strongest practical selector

**Closest work:** `drayson_2025` trains a machine-generated-text detector and importance-resamples likely human content during recursive language-model training.

**Strongest honest response:** Detection-based resampling should be treated as a serious selection baseline, not dismissed. It targets likely origin rather than under-covered human modes and does not allocate a finite lifetime human-origin token budget across generations. A joint policy is scientifically interesting only if it improves over a detector/resampling baseline under exact token matching; otherwise the simpler detector method wins.

### Threat 4 — Dynamic mixture optimization already allocates data across both time and domain

**Closest work:** `zhao_2026_regmixd` and `wang_2026_tikmix` learn time-varying or periodic domain mixtures during language-model pretraining; `ye_2025_mixinglaws` explicitly points toward dynamic schedules.

**Strongest honest response:** These papers substantially weaken any broad claim to “joint time-and-mode allocation.” The allowed distinction is contextual and accounting-based: their setting is one pretraining run over domains, not a recursive model-data chain, and the constrained resource is not a fixed stock of human-origin optimizer tokens mixed with synthetic data. The manuscript must always include the modifiers **recursive**, **fixed lifetime human-token budget**, and **matched non-joint baselines** when describing novelty.

### Threat 5 — Tail-aware or high-loss selection may already identify the same examples

**Closest work:** `xie_2023_dsir`, `liu_2021_jtt`, `sohoni_2020`, `sagawa_2020`, `ash_2020`, and `chang_2017` select target-matching, high-loss, uncertain, diverse, or hidden-subclass examples.

**Strongest honest response:** The proposed mode score is not inherently novel and may reduce to a known selector. These methods should motivate strong frozen selection-only baselines. The project may contribute a recursive resource-allocation comparison even if its selector is conventional, but it may not claim a novel active-learning or tail-learning principle unless the implemented scoring rule and evidence genuinely support that separate claim.

### Additional threat — Fixed real/synthetic mixture thresholds may make adaptive allocation unnecessary

**Closest work:** `seddik_2024`, `dohmatob_2024_tails`, `zhu_2026_reflow`, and `kang_2025` identify regimes in which a fixed real-data fraction or mixture ratio stabilizes performance.

**Strongest honest response:** A fixed-fraction policy is a required schedule-only baseline. Joint allocation is useful only if it improves a prespecified chain-level outcome at the same lifetime human and total token budgets. Failure to beat a strong fixed schedule falsifies the practical motivation.

## Allowed wording before results

- “We study” or “we will test” a fixed-lifetime human-data allocation problem.
- “The audited literature leaves a narrower, provisional distinction” followed by the full qualifiers.
- “Budget-matched schedule-only, selection-only, and joint policies are planned.”
- “The monitoring-omission experiment is designed to test a failure boundary.”
- “Prior work shows collapse in some recursive workflows and stability in others.”
- “Human-origin tokens are counted by optimizer presentations in this protocol.”

## Wording that is not allowed before validated results

- “Our method prevents model collapse.”
- “Our method is optimal” or “efficient” without a frozen comparison and result.
- “This is the first time-and-mode data allocation method.”
- “No prior work schedules or targets data.”
- “A small amount of targeted human data beats a larger random amount.”
- “The method preserves rare modes” or “reduces regret.”
- “Accumulation fails,” “fixed mixing fails,” or “detector resampling fails.”
- Any numerical performance, effect-size, or scaling claim not linked to immutable run artifacts.

## Claim C-002 contract

### Allowed wording now

> The project will test whether joint allocation improves human-rescue efficiency under a fixed lifetime budget.

### Required comparison

At the same total number of human-origin optimizer-consumed tokens and total optimizer-consumed tokens, compare the joint policy with:

1. no rescue;
2. fresh random human mixing;
3. strongest schedule-only allocation;
4. strongest selection-only allocation;
5. accumulation or a fixed-fraction baseline where scientifically applicable;
6. detector/importance-resampling selection where implementable;
7. oracle mode information as a non-deployable upper bound.

### Falsification

C-002 is not supported if the powered interval for the joint-versus-strongest-eligible-non-joint contrast includes the frozen practically equivalent or harmful region, if budget equality fails, if leakage occurs, or if the conclusion depends on post-hoc exclusions.

## Claim C-004 novelty contract

### Required search families

- recursive learning plus fresh real/human data;
- finite data-budget scheduling across iterations;
- dynamic data mixtures over training time;
- active, surprise, tail, semantic, or importance-based selection;
- adaptive center/edge or coverage sampling;
- selection bias under partial or corrupted references;
- verification and synthetic-data filtering;
- accumulation and replacement protocols.

### Novelty stop rule

If primary-source review finds a method that already jointly allocates a fixed lifetime human-origin optimizer-token budget across recursive generations and monitored human-distribution modes under comparable feedback and matched baselines, withdraw or rewrite C-004 before implementing the proposed method.

## Result promotion rule

A hypothesis can become a result only when the following are linked:

- frozen protocol version;
- code commit;
- environment and asset revisions;
- run manifests;
- raw chain-level outcomes;
- exact analysis command;
- uncertainty calculation;
- generated table or figure hash;
- limitations and failed robustness checks.
