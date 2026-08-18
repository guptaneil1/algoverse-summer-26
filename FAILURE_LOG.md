# Failure Log

> No primary experimental chain has been attempted in this repository. The entries
> below are implementation and protocol defects found in the pipeline itself.

Failures, null results, contradictory evidence, and protocol violations must be retained. They may not be deleted because they weaken the preferred conclusion.

## Entries

> **ID collision resolved on merge.** Two entries were independently created as
> `F-001` on diverged branches: the joint-policy degeneracy (2026-08-15, on `main`)
> and the missing `data.partitions` block (2026-08-12, on
> `week-3/khantushig-reference-runs`). Neither may be deleted. `main`'s keeps the ID
> because six documents cite it (`DECISIONS.md` U-007, `docs/STATUS.md`,
> `docs/SUBMISSION_CHECKLIST.md`, `docs/evidence/claim_evidence_matrix.md`,
> `docs/method/hyperparameters.md`); the provenance entry is renumbered **F-004**,
> and its one citation in `docs/runs/week3_reference_run_index.md` is updated.
> Renumbering, not deletion — the entry and its text are unchanged otherwise.

| ID | Date | Stage | Run/claim | Failure | Evidence | Cause status | Resolution | Scientific consequence |
|---|---|---|---|---|---|---|---|---|
| F-001 | 2026-08-15 | Fixture / method contract | C-002 treatment decomposition | `JointPolicy` is observationally identical to `SelectionOnlyPolicy`, and `RandomPolicy` to `ScheduleOnlyPolicy`, under every configuration the fixture simulator permits. The time-allocation axis is inert. | `tests/policies/test_joint_degeneracy.py` (5 tests, passing); `results/figures/nll_by_generation.png` shows two visible curves where four are plotted | **Implementation** — see analysis below. Not a scientific result. | Open. Assigned to Aarav; blocked on the frozen joint allocation rule (`05_method.tex`, U-007). | The fixture cannot currently distinguish the four treatment families. Budget-matching tests pass **trivially** and must not be cited as evidence that the decomposition is valid. |
| F-002 | 2026-08-12 | Pipeline | Partition vocabulary contract | `validation/audit.py` and `data/manifest.py` disagree on 3 of 5 partition names and 2 of 4 provenance fields | `validation/audit.py:29-37` (`base_human_train`/`generation_prompts`/`final_human_test`, `stable_id`/`source_dataset`) vs `data/manifest.py:12-19` (`base_train`/`prompts`/`test`, `example_id`/`source`) | Protocol/interface defect, both modules @Neil-owned | **Open.** Runner translates in `_DATA_MODULE_PARTITIONS`; contract recorded in `schemas/run_manifest.schema.json` and `docs/interfaces/run_manifest.md`. Not fixed at source — cross-owner edit needs @Neil | A rename on either side breaks the translation silently. No result affected yet |
| F-003 | 2026-08-12 | Process | Week 2 integration | Week 2 is integrated on `integration/week-2-jul25-jul31` (PRs #15/#16/#17) but never promoted to `main`, the repo has zero tags, and Neil's freeze commit `cd73d39` was never merged. `docs/STATUS.md` on `main` still says the positive control is "Not reproduced" | `git ls-remote --tags origin` → 0 tags; `cd73d39` not an ancestor of the integration branch; `main` merge history contains no Week 2 PR | Protocol/process, not implementation | **Open** — integrator decision. Reported in `docs/audits/week2_merge_gap.md`; no branch merged, tagged, or rewritten | `cd73d39` holds the frozen WikiText-103 manifests, mode definition, and tail metric, so the reference chains have no frozen data to consume. `week-2-freeze-2026-07-31` names no commit, so the `AWAITING_JULY_31_FREEZE` configs have no legitimate source |
| F-003a | 2026-08-12 | Process | This audit | An earlier version of `docs/audits/week2_merge_gap.md` claimed Week 2 was "pushed but unmerged". It checked only ancestry against `main` and reported the result as if it covered integration generally | PRs #15/#16/#17 merged three Week 2 branches into `integration/week-2-jul25-jul31` | Analysis error by the audit author | **Corrected** in place, with the superseded claim retained as a visible correction note rather than deleted | No downstream artifact depended on the wrong claim; the corrected finding (Neil's `cd73d39` outstanding) is narrower and more actionable |
| F-004 | 2026-08-12 | Pipeline | Toy smoke chain `fixture_joint_seed1` | `run_manifest.json` emitted no `data.partitions` block, so every chain classified `invalid` with `SEPARATION_MISSING_PROVENANCE` — 14 checks passing and the run still uncertifiable | `scripts/validate_run.py runs/fixture_joint_seed1` → `invalid`, exit 2, `checks_failed: ["separation_partitions_recorded"]` | Implementation defect (`runner/manifest.py:54` copied the config `data` block, which carries no partitions) | Fixed on `claude/week-3-assignments-boq852`: `build_partitions` resolves provenance from a declared source; validator now returns `valid`, exit 0, 20 checks. Pinned by `tests/runner/test_validate_toy_chain.py` | None to any result — no primary chain had run. Had it not been found first, every primary chain would have been uncertifiable and the accelerator time unrecoverable, since provenance cannot be back-filled after a run |
| F-005 | 2026-08-16 | Process / method contract | F-001 itself | **F-001 is an artifact of a revert, not a property of the method.** `243f58b` reverted `policies/joint.py` to the Week-1 scaffold hours before F-001 was written; the degeneracy F-001 records belongs to that scaffold. With Aarav's frozen implementation (`46d2cbf`) restored, all four treatment families separate. | `git diff --stat c7eee5c 243f58b -- src/human_data_budget/policies/joint.py` -> empty (revert target was the Week-1 scaffold). Measured this session on the restored tree, seed 1, horizon 10: 4/4 distinct `human_nll` trajectories; `random != schedule_only` (3.18 vs 3.22 at generation 0) and `selection_only != joint`. `tests/policies/test_treatment_decomposition.py` (7 tests) | **Process** — a revert, not an implementation or scientific defect | F-001 is **not edited or withdrawn** (append-only). `tests/policies/test_joint_degeneracy.py` is replaced by `test_treatment_decomposition.py`, per F-001's own instruction that those tests "should be deleted" once the real rule lands | C-002's treatment decomposition is **not** blocked. Every document that cites F-001 as a blocker overstates the problem and needs review: `docs/STATUS.md` ("two pairs are degenerate"), `docs/SUBMISSION_CHECKLIST.md` ("F-001 is a submission blocker"), `docs/evidence/claim_evidence_matrix.md` (S5 "BLOCKED — F-001"), `DECISIONS.md` U-007. Correcting those is an owner's call, not made here |


### F-001 analysis


`policies/joint.py` computes:

```python
budget = min(
    state.remaining_human_tokens,
    max(self.base_per_generation_budget, reserve_safe_budget),
    adaptive_budget,
)
```

where `reserve_safe_budget = remaining_human_tokens // remaining_generations`.

The load-bearing invariant is **not** the divisibility guard. It is that
`analysis/simulator.py:88-101` pins every candidate's `human_token_count` to exactly
`per_generation_budget`, so at most one candidate is ever affordable in a generation and each
generation spends exactly `base_per_generation_budget`. Remaining budget and remaining generations
therefore stay in lockstep, and `reserve_safe_budget == base_per_generation_budget` at every step.
(The divisibility guard is what makes that lockstep exact rather than drifting; it is a necessary
condition, not the cause.)

Given that, the `max(...)` term collapses to `base_per_generation_budget` and caps the whole
expression. Because `time_multiplier >= 1.0` always, `adaptive_budget >= base_per_generation_budget`
and is never the binding term. The urgency signal is computed, then discarded.

**The `random`/`schedule_only` pair has a separate, unrelated cause.** `build_policy`
(`analysis/simulator.py:42-56`) constructs `ScheduleOnlyPolicy` with a *uniform* schedule —
`{g: per_generation_budget for g in range(horizon)}` — which is exactly the fixed per-generation
spend `RandomPolicy` already uses. With only two candidates of equal cost, the two policies then
select identically. This is a property of the fixture's schedule, not of `joint.py`, and it means
the fixture cannot currently distinguish a scheduled policy from an unscheduled one either.

**Consequence for the claim ledger.** C-002 requires the joint policy to be compared
against the *strongest* schedule-only and selection-only baselines. A joint policy that
reduces to selection-only cannot test that hypothesis at all. `05_method.tex` already
requires the method owner to give "a clear explanation of how the joint method differs
from combining two tuned baselines" — F-001 is direct evidence that the provisional
implementation does not yet differ from one of them.

**Why it was not fixed on discovery.** Choosing the time-allocation rule is a frozen
scientific decision under `PREREGISTRATION.md`, owned by Aarav. Changing the allocation
arithmetic to make the axes distinct would freeze a method by side effect. The
degeneracy is pinned by tests instead, so it fails visibly rather than passing silently.
Those tests are expected to fail when the real rule lands, and should be deleted then.

### F-005 analysis — why F-001 was written in good faith and is still wrong

F-001's reasoning is sound *about the code it read*. It quotes
`budget = min(state.remaining_human_tokens, max(base, reserve_safe_budget), adaptive_budget)`
and `reserve_safe_budget`. Those identifiers exist only in the 49-line scaffold. The
frozen 150-line implementation has no such expression; it computes
`_scores`, `_desired_budget`, and `_feasible_budget`, matching the pseudocode in
`docs/method/week2_method_freeze.md:82-108` line for line.

That document is the load-bearing evidence: it was **never reverted**
(`git diff 967b2ab HEAD -- docs/method/week2_method_freeze.md` is empty). The method
stayed frozen and published on `main` the whole time; only the code beneath it was
replaced. `main` therefore shipped an implementation that contradicted its own frozen
method, and a failure log entry describing that contradiction as a property of the
method.

Two consequences worth stating plainly:

- **An overstated negative is still an overstated claim.** `CLAUDE.md` rule 1 is usually
  read as a guard against flattering numbers. F-001 shows the same rule catching the
  opposite error — a repository describing its own work as more broken than it is.
- **The tests were doing their job.** `test_joint_degeneracy.py` pinned the degeneracy so
  it "fails visibly rather than passing silently". It failed visibly the moment the frozen
  rule returned, which is exactly what it was built to do.

Not corrected here, because it is an owner's decision: `DECISIONS.md` U-007 scopes the
open question as "resolution of the F-001 degeneracy". The genuinely open part of U-007 is
the under-coverage **score definition**, which `docs/method/hyperparameters.md:46` records
as having no computation defined anywhere. That remains open and unaffected by this entry.

## Entry rules

For every failure, record:

- exact run or claim identifier;
- code and configuration commit;
- manifest and log location;
- whether the cause is implementation, infrastructure, protocol, or scientific;
- evidence supporting that classification;
- whether rerunning is allowed under the frozen rules;
- effect on claims and future stages.

An unfavorable treatment result is not an implementation failure without independent evidence of a defect.


### F-006 — upstream wandb crash on rerun (2026-08-17)

| Field | Value |
|---|---|
| Stage | A (positive control), arm `fully_synthetic`, generation 0 |
| Failure | `scripts/reproduce_positive_control.sh` exit 16; upstream `src/train.py` exit 1 |
| Error | `wandb.errors.errors.Error: You must call wandb.init() before wandb.log()` at `train.py:683` |
| Cause status | **Implementation (upstream)** — `main.py:25` guards `wandb.init` with `bool(str(cfg.wandb_disabled))`, always truthy, so init never runs while `wandb.log` is called unconditionally |
| Environment | torch 2.8.0+cu128, transformers 4.48.3, datasets 3.2.0, accelerate 1.2.1, RTX 4090 (cc 8.9, native bf16), Python 3.12.3 |
| Evidence | `runs/positive_control/fully_synthetic/stdout_stderr.log` |
| Important | Training and evaluation COMPLETED before the crash: train_runtime 33.7898 s, perplexity 29.5885, eval_accuracy 0.388, eval_loss 3.3874, checkpoint written |
| Note | `WANDB_DISABLED` / `WANDB_MODE` were **not** set for this invocation, so this observation does not by itself confirm or refute `PC-2026-08-05-E`'s claim that env vars are insufficient |
| Resolution | Retry with `WANDB_DISABLED=true` and `WANDB_MODE=disabled` exported. If the crash persists, apply the disabled-mode init shim described in `docs/positive_control/report.md` §6 |
| Scientific consequence | None on results. wandb is dashboard reporting and touches no scientific computation |


### F-007 — stale output dir, and sitecustomize shadowing (2026-08-17)

| Field | Value |
|---|---|
| Follows | F-006 |
| Observation A | The retry with `WANDB_DISABLED`/`WANDB_MODE`/`WANDB_SILENT` exported did NOT reproduce the wandb crash. It failed earlier at `train.py:313`: `ValueError: Output directory ... already exists and is not empty` |
| Correction to F-006 | F-006 proposed env vars as the fix. **That test never actually ran** — the retry died before reaching `wandb.log`. Whether env-var suppression alone suffices is **UNRESOLVED**; `docs/positive_control/report.md` §6 stays open |
| Observation B | `wandb.init(mode='disabled')` returns a `NoopRun` and `wandb.log` succeeds under all three tested env configurations (no vars / `WANDB_MODE` only / `WANDB_DISABLED` only), on wandb 0.28.2 |
| Observation C | A shim written to `/usr/local/lib/python3.12/dist-packages/sitecustomize.py` never executed: Debian ships `/usr/lib/python3.12/sitecustomize.py`, and `/usr/lib/python3.12` precedes `dist-packages` in `sys.path`, so the distro file shadowed it |
| Resolution | Shim placed at `/workspace/shim/sitecustomize.py`, reached via `PYTHONPATH` (which precedes all site dirs). It chain-loads the distro sitecustomize first, then calls `wandb.init(mode='disabled')` when `STAGE_A_WANDB_SHIM=1`. Deleted `runs/positive_control/` (gitignored, failed-attempt output only) |
| Upstream source | Unmodified. The shim is environment-level only |
| Scientific consequence | None. Both failures were infrastructure, occurring before or after the scientific computation |


### F-008 — `--prune-models` destroys the shared generation 0 (2026-08-17)

| Field | Value |
|---|---|
| Stage | A, arm `human_mixed`, generation 0 |
| Failure | exit 16: `cannot record model_dir, nothing at runs/positive_control/human_mixed/upstream/0/model/final_model` |
| Cause status | **Implementation (this repository's harness)** — not upstream |
| Mechanism | `run_positive_control_arm.py:373-376` guards generation 0 from pruning only when `--shared-generation-zero` is set. `reproduce_positive_control.sh:249` passes that flag only to arms other than `fully_synthetic`. So the synthetic arm prunes its own generation 0, which the mixed arm then needs |
| Evidence | `run.log`: synthetic arm completed generations 0-10, logged `pruning generation 9 model directory`; mixed arm then failed reusing shared generation 0 |
| Scope | `--prune-models` is incompatible with the default shared generation 0. No warning is emitted |
| Resolution | Re-run with `--no-shared-generation-zero` so `human_mixed` computes its own generation 0 |
| Deviation | The arms no longer share a bit-identical generation 0. Both compute it under upstream's identical iteration-0 command with seed 42, so the values are expected to agree; bit-identity is no longer guaranteed by construction |
| Scientific consequence | Minor. Generation 0 is recomputed under the same config and seed. `report.md` for the 2026-08-07 run noted the shared baseline as one number computed once; this run has two |
| Recommended fix | Set `keep_shared` from whether generation 0 will be shared by any arm, not from whether the current arm consumes it |


### F-009 — stale generation-0 record blocked the F-008 retry (2026-08-17)

| Field | Value |
|---|---|
| Follows | F-008 |
| Failure | exit 16: `generation 1 needs runs/positive_control/human_mixed/upstream/0/model/final_model, which is absent` |
| Cause status | **Implementation (this repository's harness)** |
| Mechanism | The F-008 attempt recorded `human_mixed` generation 0 as complete when it entered the shared-baseline path, then failed before any model was written. On retry the driver reported `generation 0: already complete, skipping` and advanced to generation 1, which requires the absent checkpoint |
| Scope | A generation is marked complete before its artifacts are verified present, so a mid-generation failure leaves a record that cannot be satisfied |
| Resolution | Deleted `runs/positive_control/human_mixed/` (gitignored, failed-attempt records only) and re-ran with `--no-shared-generation-zero`. `fully_synthetic` untouched and still complete |
| Scientific consequence | None. No scientific computation occurred in either failed attempt of this arm |
| Recommended fix | Write the completion record only after the generation's required artifacts are confirmed on disk |


### F-010 — the policy's budget currency is not the optimizer's (2026-08-18)

| Field | Value |
|---|---|
| Stage | B, pre-execution. Found by the real-step shakedown, not by a chain run |
| Classification | **Design defect (this repository)** — surfaced by execution, invisible on CPU and in the toy path |
| Observation | Upstream `train.py` reported 2,390,528 optimizer-consumed tokens for the WikiText-2 train split (4,669 blocks x 512) and 2,392,064 for a corpus assembled from the decoded generation-1 output plus three rescued human examples (4,672 blocks). The three rescued examples carry 6,082 tokens by their manifest `token_count` |
| The mismatch | These are two different accounting bases. `token_count` is per-example under the frozen tokenizer. The optimizer's count comes from upstream `group_texts_and_tokenize_data`, which concatenates every text and re-chunks into `block_size` blocks. **Concatenation dissolves example boundaries**: after grouping, no block is cleanly attributable to one example, and a single block can span the tail of a synthetic record and the head of a human one |
| Why the two numbers above do not simply decompose | The 1,536-token difference is 3 blocks, but it is not attributable to the three human examples alone: A5's synthetic base was the *decoded* generation-1 corpus, not the original train split, so two changes moved at once. The entry records the mismatch of bases, not a measured per-example delta |
| Consequence | `PROTOCOL.md` §3 and the Stage B fairness constraint require every policy in a budget-matched comparison to consume "exactly the same lifetime number of human-origin optimizer tokens". The policy budgets in manifest tokens; the optimizer consumes in post-concatenation blocks. Two policies selecting different example sets with identical manifest-token totals can consume different optimizer tokens, and nothing currently detects it |
| Blocking | The chain runner tracks `remaining_human_tokens` and decrements by `allocation.selected_human_tokens`. Which currency that is cannot be decided by implementation, so `chain.py` real-mode wiring is blocked until it is |
| Options, none chosen here | (1) Budget in optimizer blocks -- make the policy's currency the quantity actually consumed. (2) Preserve example boundaries in training -- forgo concatenation, pay padding cost. (3) Accept the mismatch, measure it, and declare a bounded tolerance in `PROTOCOL.md` before any run |
| Owner | Budget definition is Aarav's (`DECISIONS.md` U-003); the grouping behaviour is upstream's and not modifiable without deviating from the validated path |
| Scientific consequence | None yet -- no Stage B chain has run. Fixing it after chains ran would invalidate their budget matching |


### F-010a — mechanism confirmed from upstream source (2026-08-18)

Clarifies F-010. Appended rather than editing it, per the append-only rule.

**Correction to a claim made in passing.** On seeing `train_samples` move 4,669 -> 4,672
for three added examples, it was suggested that upstream truncates each record to one
block. **That is not what happens**, and the inference was drawn from a coincidence of
counts rather than from the code.

**What the source actually does.** `src/utils/utils.py:73` `group_texts_and_tokenize_data`:

- `block_size -= 1` before use, so chunking is at 511, not 512.
- `group_texts` concatenates every record in the batch (`chain(*examples[k])`), floors the
  total to a multiple of `block_size`, and splits into fixed chunks.
- Both maps run with `batched: True` and no explicit `batch_size`, so concatenation happens
  **within each default-sized batch**, not across the whole split, and each batch's
  remainder is dropped -- the code comments say so.

**Three consequences, all supporting F-010's original framing:**

1. Example boundaries do not survive into blocks. A block can span two records, so
   per-example human-origin optimizer tokens are not recoverable after grouping.
2. Remainder dropping means some tokens are **discarded** rather than consumed. A policy
   can therefore pay manifest tokens for text that never reaches the optimizer at all.
3. Because batching is by record count, the discarded fraction depends on record ordering
   and batch composition, so it is not a fixed per-corpus constant.

**What remains unmeasured.** The realised relationship between manifest `token_count` and
optimizer-consumed tokens for a given selection. The 4,669 -> 4,672 observation does not
establish it: the WikiText-2 records were already block-shaped by `load_data.py`, which
runs the same grouping and decodes back to text, while the three WikiText-103 articles were
raw. Two different input shapes moved at once.

**The measurement that would settle it**, and it is cheap: assemble corpora from an
identical synthetic base with rescue selections of known, differing manifest-token totals,
run only the tokenization and grouping (no training), and record `train_samples` for each.
That isolates the mapping without spending a single optimizer step.
