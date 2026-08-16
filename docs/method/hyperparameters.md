# Hyperparameter and Selection-Rule Registry

**Deliverable:** `docs/weekly/WEEK_2.md`, Aarav — "Document every hyperparameter and selection rule."

**Purpose.** Every tunable value in the project appears here exactly once, with the file and line
it currently lives at, its current value, who may freeze it, and which `DECISIONS.md` question
governs it. A knob that is not in this table is a knob nobody is accountable for.

**Reading the Status column.**

| Status | Meaning |
|---|---|
| `FIXTURE` | A value chosen to make contract tests run. Carries no scientific commitment and must not be inherited by a primary run. |
| `OPEN` | Must be frozen before primary outcomes are opened. Blocked on the named decision. |
| `UPSTREAM` | Fixed by the published positive control. Changing it is a documented deviation, not a tuning choice. |
| `FROZEN` | Committed. Changing it after a results freeze is prohibited by `CLAUDE.md` rule 8. |

**Nothing in this registry is currently `FROZEN`.** That is the accurate state of the project, not
an omission.

Verified against the working tree on 2026-08-15; line numbers are from that reading.

## 1. Experimental design

| Knob | Source | Current value | Status | Freezes | Decision |
|---|---|---|---|---|---|
| Recursive horizon `G` | `analysis/simulator.py:66`; `configs/experiment/toy_cpu.json` | 10 (fixture uses 3) | `OPEN` | Aarav | Drafted in `PREREGISTRATION.md`, banner-marked not frozen |
| Lifetime human budget `B` | `analysis/simulator.py:67` | 100 | `OPEN` | Aarav | **U-003** |
| Total optimizer tokens | `analysis/simulator.py:68` | 10,000 | `OPEN` | Aarav | **U-003** |
| Number of paired chain seeds | not yet declared anywhere | — | `OPEN` | Aarav | Power analysis; `PREREGISTRATION.md` promises "a predeclared ordered seed list" that does not yet exist |
| Seed order | not yet declared anywhere | — | `OPEN` | Aarav | Must be fixed before the first primary chain |
| Smallest meaningful effect | `docs/outcome_templates.md` `{MDE}` placeholder | unfilled | `OPEN` | Aarav + mentors | **U-006** |
| Training regime (continued fine-tune vs from scratch) | — | — | `OPEN` | Team | **U-001** |
| Screening model scale | `PROTOCOL.md` §2 | GPT-2 124M | `UPSTREAM` | Khantushig | Matches upstream default |

## 2. Policy knobs

| Knob | Source | Current value | Status | Freezes | Decision |
|---|---|---|---|---|---|
| `RandomPolicy.per_generation_budget` | `policies/random.py:12` | constructor arg | `FROZEN` (`week2-fixture-v1`) | Aarav | `configs/policy/random.json`: uniform 10 tokens/generation, lifetime 100. No longer reads `TBD` — that text described the stub `243f58b` reverted it to |
| `ScheduleOnlyPolicy.schedule` | `policies/schedule_only.py:12` | `dict[generation, tokens]` | `FROZEN` (`week2-fixture-v1`) | Aarav | `configs/policy/schedule_only.json`: back-loaded `0,0,0,0,0,20,20,20,20,20`, matching `week2_method_freeze.md`. This is what makes it distinguishable from `random` — the uniform schedule it was reverted to is why F-001 saw them as identical |
| `SelectionOnlyPolicy.per_generation_budget` | `policies/selection_only.py:10` | constructor arg | `FROZEN` (`week2-fixture-v1`) | Aarav | `configs/policy/selection_only.json`: uniform 10 tokens/generation, lifetime 100. Spends like `random`; differs in *what* it selects, which is the selection axis |
| Selection score function | `policies/selection_only.py` reads `state.mode_statistics` | mode statistic, falling back to `candidate.undercoverage_score` | `OPEN` | Aarav | `selection_only.json` reads `"selection_score": "TBD"` |
| `JointPolicy.base_per_generation_budget` | `policies/joint.py:15` | constructor arg | `FIXTURE` | Aarav | — |
| **Joint allocation rule** | `policies/joint.py` `_desired_budget` / `_feasible_budget` | thresholded 0/10/20 spend with feasibility clamp, per `docs/method/week2_method_freeze.md` §"Joint-policy pseudocode" | `FROZEN` (`week2-fixture-v1`) | Aarav | `configs/policy/joint.json` records the rule and no longer reads `TBD`. See **F-005**: the earlier "inert time term" was the Week-1 scaffold that `243f58b` reverted to, not this rule |
| Under-coverage score definition | `models.py` `Candidate.undercoverage_score`, default `0.0` | field exists; **no computation is defined anywhere** | `OPEN` | Aarav | **U-007** |

**F-001 / F-005 note.** The joint rule and the under-coverage score are the two knobs the entire
C-002 hypothesis rests on. **One of them is now closed and one is not.**

The joint allocation rule is frozen at `week2-fixture-v1` and implemented to match
`week2_method_freeze.md`. `FAILURE_LOG.md` F-001 recorded it as observationally identical to
`SelectionOnlyPolicy`; F-005 supersedes that — F-001 described the Week-1 scaffold that commit
`243f58b` reverted to, and with the frozen rule restored the four families are distinguishable.

The **under-coverage score definition remains open**, and it is the load-bearing half. The field
`Candidate.undercoverage_score` still defaults to `0.0` with no computation defined anywhere, so a
selection policy reading it has nothing to rank by on real data. U-007 stays open on that basis
alone.

## 3. Evaluation knobs

| Knob | Source | Current value | Status | Freezes | Decision |
|---|---|---|---|---|---|
| Evaluation seed | `configs/evaluation/primary.json` | 42 | `FIXTURE` | Neil | Matches upstream seed |
| Padding token id | `configs/evaluation/primary.json` | 0 | `FIXTURE` | Neil | Must match the frozen tokenizer |
| `nll_threshold_candidate` | `configs/evaluation/primary.json` | 3.0 | `OPEN` | Neil | Config states it will be frozen from the **validation** partition — never the test partition |
| Primary tail-retention metric | `evaluation/tail.py` `tail_retention` | ratio-based | `OPEN` | Neil | **U-004**. Both candidates implemented; neither chosen |
| Secondary tail metric | `evaluation/tail.py` `nll_gap` | NLL gap | `OPEN` | Neil | **U-004** |
| Test partition name | `configs/evaluation/primary.json` | `"test"` | `FIXTURE` | Neil | — |
| Bootstrap samples | `analysis/metrics.py` `paired_bootstrap_interval` | 5000 | `FIXTURE` | Aarav | Default; should be declared in the analysis plan |
| Confidence level | `analysis/metrics.py` `paired_bootstrap_interval` | 0.95 | `FIXTURE` | Aarav | Default; should be declared in the analysis plan |

## 4. Data knobs

| Knob | Source | Current value | Status | Freezes | Decision |
|---|---|---|---|---|---|
| Primary domain | `configs/data/wikitext103.json` | WikiText-103 (recommended, not selected) | `OPEN` | Neil | **U-002**; `docs/evidence/domain_audit.md` recommends |
| Dataset Hub revision SHA | `configs/data/wikitext103.json` | **not recorded** | `OPEN` | Neil | Must be pinned before any experimental download |
| Mode definition | `configs/data/wikitext103.json` | two candidates, `pending_week2_freeze` | `OPEN` | Neil | Article-category vs length-quantile; pick one |
| Tail-mode cut point | `configs/data/wikitext103.json` | "bottom decile by token count" | `OPEN` | Neil | Only meaningful if the length-quantile definition is chosen |
| Partition strategy | `configs/data/wikitext103.json` | `stable_id_hash_modulo` | `FIXTURE` | Neil | — |
| Near-duplicate Jaccard threshold | `data/overlap.py:26,42` | `0.8` | `OPEN` | Neil | Must be declared before the overlap report |
| Shingle size for near-duplicate detection | `data/overlap.py:8,27` | `5` | `OPEN` | Neil | Changes what counts as a duplicate; freeze with the threshold |

## 5. Upstream positive-control settings

Fixed by `docs/evidence/upstream_pin.md` §3 at commit `feb8511479a2e2dc868e1caf3f63cb99f1fcc746`.
Changing any of these makes the reproduction a non-replication and requires a documented deviation
recorded **before** running.

| Knob | Upstream value |
|---|---|
| Model | `gpt2` |
| Dataset | `wikitext2` (**not** WikiText-103 — see the deviation note in `upstream_pin.md` §3) |
| Decoding | `top_k` |
| Detector | `modernbert_mage` |
| Data selection | `importance_sampling` |
| Seed | 42 |
| Iterations | 10 |
| Torch dtype | `bfloat16` |
| Device | `cuda:0` |

## 6. Fixture simulator constants

These govern `analysis/simulator.py` only. **They are not scientific parameters** — they are chosen
numbers that make the fixture produce a legible trajectory. No result may be reported from them,
and they must never be copied into a real experiment config.

| Constant | Source | Value |
|---|---|---|
| Initial under-coverage, common / tail | `simulator.py:115-116` | 0.10 / 0.20 |
| Degradation rate, common / tail | `simulator.py:121-122` | 0.04 / 0.10 |
| Rescue effect, common / tail | `simulator.py:126-127` | 0.08 / 0.14 |
| Candidate `undercoverage_score` | `simulator.py:97,103` | 0.0 |

The tail degrades 2.5× faster than the common mode and rescue is 1.75× more effective on it. Those
two ratios are what make targeting appear to win in every fixture figure — which is exactly why
fixture output is watermarked and may not be cited.

## 7. Maintenance rule

Adding a tunable value to the codebase without adding a row here is a review-blocking omission. When
a knob is frozen, change its Status to `FROZEN`, record the value, and link the `DECISIONS.md` entry
that froze it. After a results freeze, `CLAUDE.md` rule 8 applies: no knob may be added, removed, or
retuned.
