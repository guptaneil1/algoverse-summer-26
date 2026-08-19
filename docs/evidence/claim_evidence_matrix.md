# Claim-to-Evidence Matrix for Planned Abstract Sentences

**Deliverable:** `docs/weekly/WEEK_2.md`, Ronit — "Update `CLAIMS.md` and build a claim-to-evidence
matrix for planned abstract sentences."

**Purpose:** every sentence that will appear in the abstract is listed *before* results exist,
together with the exact artifact that would license it. A sentence with no licensing artifact may
not be written, regardless of how confident anyone feels. This is the operational form of
`PROTOCOL.md` §5.

**Status:** structure complete; all result-dependent rows are correctly unlicensed.

## How to read the status column

| Status | Meaning |
|---|---|
| `WRITABLE NOW` | Licensing artifact exists and was checked. Sentence may enter the abstract today. |
| `BLOCKED — <artifact>` | Sentence may not be written until that artifact exists and validates. |
| `CONDITIONAL` | Sentence's *content* depends on the outcome; use the matching template in `docs/outcome_templates.md`. |

## Matrix

| # | Planned abstract sentence (paraphrase) | Claim | Licensing artifact required | Status |
|---|---|---|---|---|
| S1 | Language models are increasingly trained on text produced by earlier models, and controlled studies show this can degrade fit, diversity, or tail coverage in some workflows. | C-001 | Audited primary literature: `sources.yaml`, `closest_work.csv` | **WRITABLE NOW** |
| S2 | Outcomes depend on the data workflow; accumulation, fixed real fractions, and detector resampling stabilize some recursive procedures. | C-001 | Same, plus the scope qualifiers in `CLAIMS.md` Threat 1 and Threat 3 | **WRITABLE NOW** |
| S3 | We treat human-origin data as a finite lifetime resource measured in optimizer-consumed tokens. | Definitional | `PROTOCOL.md` §3 token accounting; `data/token_accounting.py` | **WRITABLE NOW** |
| S4 | We formalize allocation of that budget jointly across recursive generations and monitored human-distribution modes. | Definitional | `paper/sections/04_problem.tex`; **frozen** method definition | **BLOCKED — Aarav's frozen joint allocation rule (U-007 / `05_method.tex`)** |
| S5 | We define budget-matched random, schedule-only, selection-only, and joint treatment families. | Definitional | `policies/`; **frozen** `configs/policy/*.json` (`week2-fixture-v1`); `tests/policies/test_treatment_decomposition.py` | **WRITABLE** — see F-005 |
| S6 | Complete recursive chains are the experimental units. | D-005 | `DECISIONS.md` D-005; `PROTOCOL.md` §4 | **WRITABLE NOW** |
| S7 | We reproduce a published positive control before running novel comparisons. | Method integrity | Stage A reproduction report **or** truthful failure package | **BLOCKED — Stage A unexecuted** |
| S8 | We evaluate on one licensed domain with a 124M–160M screening model over ten generations. | Design | Frozen `configs/data/*`; frozen model config; real manifests | **BLOCKED — U-001, U-002; `data/manifests/` empty** |
| S9 | Primary outcomes are held-out human NLL regret aggregated over the horizon and a frozen tail-retention measure. | D-006 | Frozen tail metric definition | **BLOCKED — U-004 (two candidates implemented, neither frozen)** |
| S10 | *Statement of what the joint policy did relative to the strongest non-joint baseline.* | C-002 | Validated paired chains + `results/aggregates/` + analysis command | **CONDITIONAL — use `docs/outcome_templates.md`** |
| S11 | *Statement of the monitoring-omission stress test outcome.* | C-003 | Predeclared monitoring-bias intervention results | **CONDITIONAL — use `docs/outcome_templates.md`** |
| S12 | The contribution is a matched chain-level test of allocation, not a claim that collapse is prevented. | C-004 | `CLAIMS.md` contribution paragraph + external novelty review | **BLOCKED — external review not obtained** (the scoping half is writable; the novelty half is not) |

## Audit against the written abstract, 2026-08-19

The abstract is now written, and every sentence in it was checked against this matrix.
The rows below cover the sentences added after the pilot executed; S1-S12 are re-scored
above them because the artifacts several were blocked on now exist.

| ID | Sentence (abbreviated) | Licensing artifact | Status |
|---|---|---|---|
| S13 | We execute the pilot: 25 chains over 5 seeds and 10 generations. | `results/runs/primary_pilot_2026-08-18/`, 25 tracked `chain_result.json`; `ARTIFACT_HASHES.json` | **WRITABLE — verified** |
| S14 | The fairness constraint requires equal human tokens *and* equal total optimizer tokens. | `PROTOCOL.md` §4, quoted directly | **WRITABLE — definitional** |
| S15 | This run satisfies neither: one policy under-spent by 10.1%, totals span 2.26%. | `FAILURE_LOG.md` F-020, F-021; `run_pilot --check-only` output; both figures generated into `pilot_macros.tex` from chain artifacts | **WRITABLE — verified** |
| S16 | We report the primary contrast as invalid rather than repairing or reweighting it. | `PREREGISTRATION.md` exclusions; `CLAIMS.md` C-002 falsification clause ("not supported if budget equality fails"); `docs/runs/primary_pilot_2026-08-18_results.md` | **WRITABLE — verified** |
| S17 | We decline the secondary comparison that would have read more favourably. | `PREREGISTRATION.md`: "other comparisons ... cannot replace a failed primary analysis". The declined comparison and its confound are recorded in the results document | **WRITABLE — verified** |
| S18 | One comparison survives both constraints and is a null. | `schedule_only` vs `random`, matched on both axes (human -0.00%, total +0.02%); interval contains zero | **WRITABLE — verified** |
| S19 | Between-chain variance is small enough that the frozen seed set is already powered. | `docs/decisions/powered_design_sizing_2026-08-19.md`, derived from the chain artifacts | **WRITABLE — verified** |
| S20 | We make no claim about allocation policy. | `CLAIMS.md` C-002 status; the absence of any such claim in §7 | **WRITABLE — verified** |
| S21 | The contribution is the design, a validated apparatus, and a record of the checks. | `docs/runs/...results.md`; `FAILURE_LOG.md` F-015 to F-021a; the positive-control package | **WRITABLE — verified.** Deliberately *not* a novelty claim, so it does not depend on the outstanding external review |

### Re-scored after execution

- **S7** (positive control reproduced) — was BLOCKED. Stage A reproduced twice with verifying hashes. **WRITABLE.**
- **S8** (one domain, screening model, ten generations) — was BLOCKED. Executed exactly as frozen. **WRITABLE.**
- **S9** (primary outcomes) — was BLOCKED on U-004. D-022 froze the metric; U-004b is closed as unreachable. **WRITABLE.**
- **S10** (what the joint policy did) — was CONDITIONAL. **Resolved to: not established.** The abstract states this and makes no performance claim, which is the outcome-contingent path for a failed fairness constraint.
- **S11** (monitoring-omission stress test) — still CONDITIONAL and **correctly absent from the abstract**. C-003 is untested; no such intervention ran.
- **S12** (contribution framing) — remains **BLOCKED on external novelty review** *as originally worded*, because it asserted a contribution relative to prior work. S21 replaces it with a statement about what was done rather than what is new, which the artifacts license without that review.

### Result

**Every sentence in the written abstract maps to a licensing artifact that exists and was
checked.** No sentence depends on the outstanding external novelty review, and none states
an outcome for C-002 or C-003.

## Sentence count check (original, pre-execution)

12 planned sentences.

- **4 writable today:** S1, S2, S3, S6.
- **6 blocked on artifacts that do not exist:** S4, S5, S7, S8, S9, S12.
- **2 outcome-conditional:** S10, S11.

**Why S5 is now writable.** It was blocked on two grounds, and both have been resolved.

`FAILURE_LOG.md` F-001 recorded the joint policy as observationally identical to selection-only,
and random to schedule-only — two distinguishable families rather than four. **F-005 supersedes
that.** F-001 described the Week-1 scaffold: commit `243f58b` reverted `policies/joint.py` to it
hours before F-001 was written. With Aarav's frozen implementation restored, the four families
produce four distinct trajectories, asserted across three seeds in
`tests/policies/test_treatment_decomposition.py`.

The second ground — that all four `configs/policy/*.json` read `TBD_BEFORE_PRIMARY_RUNS` — was also
a consequence of the same revert. They now carry `policy_version: week2-fixture-v1` and their
spending rules, with no `TBD` remaining in any of the four.

**What S5 may and may not say.** S5 is definitional, and this evidence is structural: it shows the
fixture simulator distinguishes the four families. It is not evidence that the *contrast between
them* is scientifically meaningful — that is C-002, which still needs primary chains. Budget-equality
tests passing remains weak evidence on its own.

This is the honest shape of the abstract: a third of it could be written this week, and the
remainder is correctly gated.

## Banned-wording cross-check

Every sentence above was checked against the `CLAUDE.md` hard-rule-5 banned list — "first," "optimal,"
"prevents collapse," "solves," "state of the art," and unqualified "novel." No planned sentence
uses any of them. S12 carries the required C-004 modifiers (*recursive*, *fixed lifetime
human-token budget*, *matched non-joint baselines*).

**Standing rule for S10 and S11:** when these are eventually written, they must state a direction
and an interval, never a bare direction. "The joint policy reduced regret" is not acceptable;
"the joint policy reduced regret AUC by X [CI: a, b] relative to the strongest non-joint baseline"
is. If the interval includes the practically-equivalent region, the correct sentence is the tie
template, not a softened win template.

## Maintenance

Update this file whenever a blocking artifact lands. A row moves to `WRITABLE NOW` only when the
artifact exists **and** has been read — not when it is expected to exist soon.
