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


### F-010b — root cause: the manifest counts words, not tokens (2026-08-18)

Supersedes the speculative parts of F-010 and F-010a. Those described a mismatch of
accounting bases and suspected concatenation and remainder-dropping as the cause. Measured,
the dominant term is simpler and fixable.

**Root cause.** `scripts/build_wikitext103_manifests.py:285`:

    token_count = len(text.split())

That is a whitespace word count. No tokenizer is imported anywhere in the builder.

**Measured, CPU only, no optimizer steps.** GPT-2 BPE tokens versus manifest `token_count`
over 25 rescue candidates: mean **1.1727**, min **1.0963**, max **1.3184**. Per-example
examples: `train-77f0ac40398e1a78` 3,772 words / 4,400 BPE (1.1665);
`train-8891cb789c796497` 799 / 1,027 (1.2854); `train-db04714210274cb8` 2,315 / 2,542
(1.0981).

**Independent corpus-level cross-check.** Assembling a fixed 200-record synthetic base plus
rescue selections of 0, 3, 6, 12 and 24 examples, then running upstream's
`group_texts_and_tokenize_data` and comparing block counts, gives realised
optimizer-per-manifest-token ratios of 1.1786, 1.1504, 1.1484 and 1.1708. Those agree with
the per-example BPE ratio, which establishes that **the unit error dominates and
remainder-dropping is a second-order effect**, correcting F-010a's emphasis.

**Four consequences.**

1. **Budget matching does not hold.** Two policies selecting different example sets with
   identical `token_count` totals can differ by up to roughly 20% in tokens the optimizer
   actually consumes, because the word-to-BPE ratio varies per example over 1.096-1.318.
2. **`PROTOCOL.md` §3 is violated as written**: "Counts must come from tokenized batches
   actually consumed by the optimizer, not estimated character or document counts." A word
   count is an estimate.
3. **`models.Candidate`'s docstring is false.** It states `human_token_count` means
   "non-padding tokens consumed per optimizer presentation under the frozen
   tokenizer/preprocessing definition". It is words under no tokenizer.
4. **Mode assignment inherits the unit.** `_assign_mode` thresholds at
   `tail_cutoff = 1106.0` and `common_cutoff = 2661` word counts, so "tail" currently means
   short by word count. That may still be a defensible mode definition, but it is not the
   one the field name implies, and the frozen cutoffs would move under a recount.

**The fix, and why it is not applied here.** The builder should tokenize with the frozen
GPT-2 tokenizer and record BPE counts. That changes `token_count` on every example, which
changes the tail and common cutoffs, which changes mode assignment, which changes the
partition summary hashes. It is a re-freeze of Neil's Week 2 deliverable, not a patch, and
`data/` is his. Doing it downstream would leave two disagreeing definitions in the tree.

**Scientific consequence.** None yet: no Stage B chain has run. Discovering it after chains
ran would have invalidated their budget matching silently, since nothing in the current test
suite compares the two units.

### F-011 — tail_retention's orientation contradicts the metric freeze (2026-08-18)

| Field | Value |
|---|---|
| Stage | B, pre-execution. Found while wiring the real evaluator |
| Classification | **Specification conflict (this repository)** — two frozen documents disagree about what the primary metric consumes |
| The conflict | `evaluation/tail.py` computes `clip(current / reference, 0, 1)` and documents "1.0 means the model preserves all tail coverage". That holds only if the scores rise as the model improves. The toy path satisfies it: `chain.py` passes `1.0 - undercoverage`. But `docs/evaluation/tail_retention_freeze.md` §3 specifies `reference_mode_scores` as each mode's **mean held-out NLL**, which rises as the model degrades |
| Consequence if taken literally | A degraded model produces `current_nll / reference_nll > 1`, which clips to **1.0** — reporting perfect tail retention for the worst case, and monotonically *rewarding* degradation up to the clip. The primary outcome would be inverted and bounded in the wrong direction |
| Demonstrated | `tests/evaluation/test_real_evaluation.py::test_a_degraded_model_scores_below_one_after_transform` asserts the raw-NLL path returns exactly 1.0 for a model whose tail NLL doubled, and 0.5 once the orientation is corrected |
| Not silently resolved | `evaluation/real.py` emits raw per-mode NLL, which is unambiguous, and exposes `mode_nll_to_retention_scores` (the reciprocal) as a separate explicit call. Nothing converts implicitly |
| Owner | Evaluation definition is Neil's. Either `tail.py`'s inputs are coverage-like and the freeze document's wording is wrong, or the freeze is right and `tail.py` needs an inversion. One of the two is incorrect as written |
| Scientific consequence | None yet — no chain has evaluated through this path. Discovering it after a pilot ran would have inverted the confirmatory outcome, and no existing test would have caught it: the toy path only ever supplies coverage-like scores, so `tail.py` is exercised exclusively in the orientation that works |


### F-012 — the chain corpus contract is not raw text (2026-08-18)

| Field | Value |
|---|---|
| Stage | B screening, generation 0. Found by the first real chain execution |
| Classification | **Implementation (this repository)** -- a defect in `scripts/build_base_corpus.py` as first written |
| Failure | Generation 0 trained successfully, then `src/generate.py` exited 1 with `KeyError: 'context'` |
| Cause | The corpus builder wrote bare `{"text": ...}` records. Upstream prompts from a `context` field and classifies a `cls_text` field, both produced by `load_data.py::process_dataset(train=True)`: block-group and tokenize, decode back to `text`, slice the leading `input_token_length` tokens into `context`, and the trailing remainder into `cls_text` |
| Why it survived every earlier check | Training reads only `text`, so generation 0 completed and the fault surfaced one step later. The dry-run path never invokes upstream at all, and the Stage A shakedown used `load_data.py`'s own output, which already carried the fields |
| Resolution | The builder now imports upstream's `group_texts_and_tokenize_data`, `decode`, `get_context` and `get_text_to_classify` and mirrors `process_dataset` step for step, rather than reimplementing the format. Verified: five test-partition examples produce 39 blocks carrying `text`, `context` and `cls_text`, with `context` the first 256 tokens |
| Deliberately omitted | The detector pass. `cls_score` is read only under `data_selection=importance_sampling`, which this project overrides to `no-selection` (deviation 1), so omitting it saves a GPU pass over the corpus. Available behind `--classify` |
| Scientific consequence | None. No chain completed, and the defect was in corpus preparation rather than in any computed quantity |


### F-013 — evaluation corpora must not carry the training columns (2026-08-18)

| Field | Value |
|---|---|
| Stage | B screening, generation 1. Continues F-012 |
| Failure | `DatasetGenerationCastError`: "1 new columns ({'context'}) and 3 missing columns ({'cls_confidence', 'cls_score', 'diversity'})", raised while reading `screening_test.json` |
| Cause | Upstream loads `--train_file` and `--test_file` in one `load_dataset` call, which requires a consistent schema. Generation 0 passed because both corpora carried `text`/`context`/`cls_text`. From generation 1 the train file is a *generated* corpus carrying `cls_score`/`cls_confidence`/`diversity` and no `context`, so the test file's `context` became an unexpected extra column |
| What upstream does | `load_data.py` calls `process_dataset(train=False)` for the validation and test splits, which skips `get_context` and `get_text_to_classify` entirely. Its `test.json` carries **only** `text`. Columns missing from the test file are tolerated; columns present only in the test file are not |
| Resolution | `build_base_corpus.py --eval` mirrors `process_dataset(train=False)` and emits `text` alone. Verified: three test-partition examples produce 18 blocks whose only field is `text` |
| Why generation 0 hid it | A schema mismatch cannot appear until the train file stops being the human base corpus, which happens exactly once, at the first recursive generation |
| Scientific consequence | None. No chain completed, and the defect is in corpus preparation |
