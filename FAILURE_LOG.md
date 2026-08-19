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


### F-014 — generation prompts must come from the frozen prompts partition (2026-08-18)

| Field | Value |
|---|---|
| Stage | B screening, generation 2. Generations 0 and 1 both trained and decoded successfully first |
| Failure | `src/generate.py` exit 1 at iteration 2, reading the assembled generation-1 corpus |
| Immediate cause | The chain passed `--dataset_filepath` as the *current training corpus*. From generation 1 that corpus is generated output plus rescued text, which carries no `context` field, so the prompt slice upstream needs is absent |
| The larger error | Upstream never prompts from the evolving corpus. `run_positive_control_arm.py:150` passes `data_dir / "train.json"` for **every** generation -- a fixed prompt source. The recursion lives in the model, which is retrained on synthetic data each generation, not in the prompts, which stay constant so successive generations are compared on the same completions task |
| Why this was a correctness bug, not only a crash | `PROTOCOL.md` §3 holds five partitions disjoint, and lists generation prompts separately from training data. Prompting from `train_file` would have drawn prompts from the training set. Had `generate.py` tolerated a missing `context` instead of raising, this would have produced numbers rather than an error |
| Resolution | `prompt_corpus` is now a required config key, built from the frozen `prompts` partition and passed unchanged for every generation. The launcher resolves and prechecks it alongside the other assets |
| Scientific consequence | None realised -- the run crashed rather than completing. Recorded because the failure mode it would have caused is silent |


### F-015 — realised human spend differs 24% across arms; budget matching does not hold (2026-08-18)

| Field | Value |
|---|---|
| Stage | B pilot, **pre-execution**. Found by a dry run of the frozen config, before any GPU time |
| Classification | **Method design defect** -- not implementation. The policies behave as specified; the specification does not equalise spend |
| Observation | Against a 750,000-token lifetime budget, realised lifetime human-origin spend was: `no_rescue` 0 (by design), `schedule_only` ~517,000, `selection_only` 574,731, `random` ~580,000, `joint` 641,002. The ordering and magnitudes are identical at every one of the five frozen seeds |
| Magnitude | Joint consumes **23.7-24.3% more** human-origin optimizer tokens than schedule_only, at every seed |
| Why | Policies stop when the next indivisible candidate does not fit the remaining per-generation allowance, and they differ in how many generations they can spend in at all. `schedule_only`'s frozen back-loaded schedule gives it five spending generations; `joint` spends adaptively across all ten. Neither reaches the 750,000 ceiling, and they fall short by different amounts |
| Consequence | `PROTOCOL.md` §4 requires every policy in a budget-matched comparison to consume "exactly the same lifetime number of human-origin optimizer tokens". It does not hold. A joint-versus-schedule_only contrast is confounded by data quantity: if joint wins, the cause cannot be separated from its extra ~124,000 tokens. `CLAIMS.md` C-002's contract is unmet as configured |
| Not a discretisation artifact | Candidates average 4,082 tokens, so rounding could explain a spread of a few thousand. 124,000 is thirty times that, and the gap is stable across seeds rather than varying with them |
| Options, none chosen here | (1) Require every policy to spend its full lifetime budget by the final generation, with a terminal top-up, making the constraint hold by construction. (2) Re-specify the constraint as an equal *ceiling* rather than equal realised spend, and report realised spend as a reported covariate. (3) Equalise post hoc by truncating every arm to the minimum realised spend, which discards data and changes what each policy did. (4) Accept and state the confound, which forfeits C-002 |
| Owner | Budget definition and the joint allocation rule are Aarav's (`DECISIONS.md` U-003, U-007) |
| Cost of finding it here | Zero. A dry run of the frozen grid on CPU. Discovering it after the pilot would have cost the run and produced a comparison that could not support its primary claim |
| Scientific consequence | None yet. No chain has run. The pilot should not launch for a C-002 contrast until this is resolved, though it could still legitimately launch as a **variance-estimation** exercise if that limitation is stated in advance |

### F-015a — F-015 closed; the residual is an indivisibility floor (2026-08-18)

| Field | Value |
|---|---|
| Stage | B pilot, still **pre-execution**. No chain has run |
| Relation to F-015 | **Closure.** F-015 is not edited. This entry records what changed, which of its four options was taken, and what the constraint now asserts |
| What was fixed | Two defects, both in commit `2626483`. (1) `data/corpus.py` summed `token_count` for its human ledger while policies priced candidates in `optimizer_token_count`, so a fully-allocated budget read as under-spent by the BPE ratio — F-010b resurfacing in the ledger after being fixed in the pricing. (2) Terminal reconciliation fired one generation too late: an allocation at generation *g* is assembled into generation *g+1*'s corpus, so the final generation's allocation was never consumed, and `schedule_only`'s back-loaded schedule placed a full 150,000 allowance exactly there |
| Option taken | F-015's **option 2** — re-specify the constraint as an equal *ceiling* reached up to indivisibility, rather than equal realised spend. Recorded as `DECISIONS.md` P-008 |
| Measured after the fix | Dry run of the frozen grid, 25/25 chains, 2026-08-18: `no_rescue` 0 at every seed; `random` 749,757–749,970; `schedule_only` 749,709–749,995; `selection_only` 749,866 at every seed; `joint` 749,844 at every seed. Spread across the four spending arms **0.0381%** against a 750,000 ceiling |
| Why this is a floor, not a defect | Candidates are indivisible. The largest in the frozen rescue pool costs **26,902** optimizer tokens (4,235 candidates, mean 4,082.4, measured from `data/manifests/rescue_candidates.jsonl`). An arm stops when the next candidate does not fit, so a shortfall of up to one candidate is arithmetic rather than policy. The largest observed shortfall is **291** |
| Not claimed | That realised spend is equal. It is not, and cannot be over indivisible examples. What is asserted is that every spending arm reaches its ceiling to within one candidate, and that the residual spread stays an order of magnitude below the practical effect threshold |
| Scientific consequence | The 24% confound recorded in F-015 does not hold at the frozen configuration. `CLAIMS.md` C-002's contract is met as configured. This closes the confound, not the pilot's inference limits: the run remains a variance-estimation exercise under five frozen seeds |

### F-016 — the budget-matching guard could never pass, and nothing tested it (2026-08-18)

| Field | Value |
|---|---|
| Stage | B pilot, **pre-execution**. Found by the dry run that F-015 established as the pre-launch gate |
| Observation | `scripts/run_pilot.py` asserted budget matching as `len({consumed_human_tokens}) > 1` — exact set equality over every completed chain. Run against the frozen grid it printed `BUDGET MATCHING VIOLATED` on a 0.0381% spread: the very state commit `2626483` had recorded as F-015's closure |
| Classification | **Implementation defect in the guard**, not in the policies. The measured spend was correct and within its intended bound; the assertion over it was unsatisfiable |
| Two independent reasons it was unsatisfiable | (1) `no_rescue` consumes 0 by construction, so 0 was always in the set beside ~749,000 — no configuration containing the control arm could ever pass. (2) Indivisible candidates make exact equality unreachable across seeds even among the spending arms |
| Why the suite missed it | Nothing exercised the guard's **pass** condition. The string `BUDGET MATCHING` occurred in `scripts/run_pilot.py` and nowhere else in the repository. 706 tests passed against a launcher that would have flagged every physically possible run |
| Second defect, same guard | A violation only printed. The exit code keyed off failed chains, so an unequal comparison exited **0** and appeared below the results rather than stopping the run |
| Third defect, sharded path | Each shard evaluated only the ~6 chains it ran, so no process ever assessed the whole grid. The launch command in `docs/HANDOVER_2026-08-18.md` shards four ways, so this was the path the pilot was about to take |
| Fixed | `src/human_data_budget/runner/budget_matching.py` asserts the three conditions P-008 specifies; violations exit non-zero; `--check-only` reassembles every shard summary into a whole-grid verdict. `tests/runner/test_budget_matching.py` (13 tests) pins both directions, including that F-015's historical numbers still fail the replacement check |
| Cost of finding it here | Zero. It would not have been free later: the run would have completed, exited 0, and printed a fairness violation under 25 chains of otherwise valid results, with no way to tell from the exit code that anything was wrong |
| Scientific consequence | None. No chain has run. Had it gone unfound, the pilot's own fairness check would have been uninformative in both directions — unable to pass when the constraint held, and unable to stop the run when it did not |

### F-017 — corpus paths resolved against the upstream checkout, killing all 25 chains (2026-08-18)

| Field | Value |
|---|---|
| Stage | B pilot, **first real launch**. Found on GPU, after the dry run passed |
| Observation | All 25 chains failed within seconds of launch, every one at generation 0's training step: `FileNotFoundError: Unable to find '/workspace/model_collapse/data/corpora/pilot_base.json'`. GPU utilisation never left 0% and memory never left 1 MiB, so no training ever began |
| Cause | `runner/upstream_driver.run_upstream_step` runs each subprocess with `cwd=upstream_dir`. The three corpus paths a config supplies — `base_corpus`, `prompt_corpus`, `test_corpus` — were passed through to the command line unchanged. They are repo-relative (`data/corpora/pilot_base.json`), so upstream resolved them against `/workspace/model_collapse`, where they do not exist. The corpora were present and correct in the repository the whole time |
| Why the dry run did not catch it | The dry-run path *prints* the command rather than executing it, so a path that can never resolve renders identically to one that will. The dry run reported `budget matching: HOLDS` with the expected figures minutes before the launch failed. This is a real limit on what a dry run certifies: it exercises allocation, manifests and budget arithmetic, not the filesystem the subprocess will actually see |
| Why the test suite did not catch it | 719 tests passed. Nothing asserted a property of the corpus arguments on the command line. The builders were pinned for their *flags*, never for whether their path values would resolve from the working directory upstream runs in |
| Why screening did not catch it | The screening run of 2026-08-18 used corpora at paths that happened to resolve, so the defect was latent until the pilot config's relative paths met a real subprocess |
| Fixed | `runner/real_chain.run_real_chain` absolutises the three corpus paths against the process working directory before any reaches a command line, on a copy of the config so the caller's dict is untouched. `tests/runner/test_corpus_paths_are_absolute.py` (5 tests) asserts the command line itself; 2 of the 5 fail if the fix is reverted, verified by reverting it |
| Cost of finding it here | Roughly a minute of 4-GPU time and the operator's attention. No compute was consumed: every chain died before loading a model. Nothing scientific was lost, and no artifact needs discarding |
| Scientific consequence | None. No chain produced a result, valid or otherwise. The `pilot_summary*.json` files from this launch record 25 failures and no chain results |
| Lesson recorded | A passing dry run is necessary and not sufficient. It cannot certify anything that depends on the subprocess's working directory, its filesystem, or its environment — F-007 and F-014 were the same class. The cheap check that *would* have caught this is a single real chain (`--only-arm no_rescue` at one seed) before the full grid |

### F-018 — the certification path carried two more copies of the guard F-016 fixed (2026-08-18)

| Field | Value |
|---|---|
| Stage | B pilot, **after the first real chain, before the grid**. Found by checking the validator against a measured chain rather than by running it |
| Observation | With one real chain complete (`no_rescue` seed 101: 0 human tokens, 16,678,912 total), `scripts/validate_run.py` blocks it twice: `lifetime human-token budget violated: manifest declares 750000, chain consumed 0` and `total optimizer-token budget violated: manifest declares 16100000, chain consumed 16678912`. `validation/audit.py` raises `BUDGET_HUMAN_MISMATCH` and `BUDGET_TOTAL_MISMATCH` on the same chain |
| Consequence had it not been found | Every one of the 25 chains would have been certified **invalid** after roughly seven hours and the project's remaining budget. The chains themselves would have been sound; only the certification of them was wrong. `docs/RUNBOOK_PILOT_LAUNCH.md` step 11 would have reported a total failure of a successful run |
| Cause, human axis | Identical to F-016. Both files asserted realised spend *equals* the declared budget. A control arm spends zero by construction, and a spending arm stops one indivisible candidate short, so neither can satisfy exact equality. F-016 corrected `scripts/run_pilot.py` and left these two untouched — three independent implementations of one constraint, only one of which was fixed |
| Cause, total axis | Different, and not indivisibility. `total_optimizer_tokens` = 16,100,000 is P-005's **projection** of training volume, not a budget any policy spends against. The measured value is 16,678,912 on the arm that spends *nothing*, so the projection is 3.6% low before any rescue data is added. Asserting equality against a projection makes every chain fail regardless of policy |
| Fixed | One shared implementation, `runner/budget_matching.check_chain_budget`, used by `scripts/validate_run.py` and `validation/audit.py`; the grid-level check in `scripts/run_pilot.py` already used the same module. Human axis follows P-008. Total axis follows P-009: reported rather than asserted, inside a band the human budget explains |
| Verified | The measured chain now certifies, and a rescue arm at its residual certifies. F-015's shape (517,000 against 750,000) still blocks, as does a control arm that consumed anything. Checked by running `_check_budget_matching` against the measured numbers directly, not only through unit tests |
| Guard tests re-pointed, not deleted | `test_human_budget_violation_is_invalid` asserted 59-against-60 and `test_total_budget_violation_is_invalid` asserted 301-against-300 — both violations only under exact equality. They now assert violations that are real under the replacement, and new tests pin the cases that must now pass. The two re-pointed tests are named as such in their docstrings so the change is visible rather than silent |
| Left strict deliberately | `analysis/simulator.py` still asserts exact equality. It constructs its own divisible fixture candidates and excludes `no_rescue`, so exact spend is achievable there and the assertion catches simulator defects. Relaxing it would remove a working check |
| Cost of finding it here | Zero. One measured chain and a reading of the validator |
| Scientific consequence | None. One chain has run and it is sound; what was wrong was the rule used to certify it. No result is affected, and the smoke chain's artifacts remain usable |
| Lesson | A constraint implemented three times is a constraint that will be fixed once. The launcher, the validator and the auditor now share one function; adding a fourth copy is the failure mode to watch for |

### F-019 — F-004 recurring: the pilot config's partitions were declared but unrecognised (2026-08-18)

| Field | Value |
|---|---|
| Stage | B pilot, **after one real chain, during the grid launch**. The grid was killed roughly two minutes in |
| Observation | `scripts/validate_run.py` on the completed smoke chain returned `"classification": "invalid"`, `checks_failed: ["separation_partitions_recorded", "token_ledger_recomputed"]`, `SEPARATION_MISSING_PROVENANCE`. Fourteen checks passed, including all three budget checks fixed under F-018 |
| Relation to F-004 | The same defect, on a different code path. F-004 recorded it for the toy chain in August and was closed by `build_partitions` resolving provenance from a declared source. That fix was never exercised by an experiment config, so it did not cover the one the pilot uses |
| Cause | `build_partitions` accepts provenance from `data.partitions` (inline records) or `data.partition_manifests` (canonical name → JSONL path). `configs/experiment/primary_pilot.json` declares its five partitions under **`data.manifests`**, keyed by the `data/` module's vocabulary (`base_train`, `prompts`, `test`) and carrying `{path, manifest_hash}`. Three names and one shape apart, so the builder recognised nothing and returned `None`. The config was not missing provenance; it was declaring it in a vocabulary the builder did not read. F-002 recorded that exact two-vocabulary split as an open interface defect |
| Consequence had it not been found | All 25 chains would have completed and every one classified `invalid`. The compute would not have been recoverable by re-validating: `data.partitions` is written into `run_manifest.json` at chain start, and F-004 already records that provenance cannot be back-filled after a run |
| Why the dry run missed it | The dry run builds a manifest and would have written the same empty `data` block. Nothing in the dry-run path validates the manifest it produces, so a manifest that cannot certify still reads as a clean dry run |
| Why the suite missed it | Every manifest test supplied its own fixture `data` block. No test asked whether *the config about to be launched* yields a certifiable manifest. 740 tests passed against a frozen, executable config that could not produce one |
| Fixed | `runner/manifest.build_partitions` accepts `data.manifests` as a third provenance source, at lowest precedence, mapping the data-module vocabulary to the canonical one through the existing `_DATA_MODULE_PARTITIONS` table. No config was edited: the frozen config already carried the information, hash-pinned. Verified against it — 22,637 / 4,235 / 1,359 / 60 / 60 records resolved, disjointness asserted, manifest 4.9 MB per chain |
| Pinned by | `tests/runner/test_frozen_configs_are_certifiable.py`, which asks of every executable partitioned-stage config whether it resolves all five partitions, plus a guard test that fails if the filter ever stops covering `primary_pilot`. `positive_control` is excluded by stage and the reason is recorded in the file: Stage A drives WikiText-2 through its own adapter and never used these partitions |
| Cost of finding it here | About two minutes of four-GPU time, plus the ~57-minute smoke chain that surfaced it. That chain paid for itself twice: it caught F-017's successor and this |
| Scientific consequence | None. No certified result existed and none was lost. The smoke chain's artifacts remain uncertifiable for this reason and are not used for any claim |
| Lesson | Three defects in a row (F-017, F-018, F-019) were invisible to both the dry run and the test suite, and all three were caught by running one real chain and validating it. The single-chain-then-validate step is now in the runbook ahead of the grid; it is the only step that exercises the subprocess, the artifacts, and the certification path together |

### F-019a — the F-019 fix was verified against the wrong object (2026-08-18)

| Field | Value |
|---|---|
| Stage | B pilot, between the second smoke chain and the grid |
| Relation to F-019 | **Correction, appended not edited.** F-019 records the cause correctly and its fix was necessary; it was not sufficient, and the verification that accompanied it did not test the path that matters |
| Observation | With F-019's fix committed, a second real chain still returned `SEPARATION_MISSING_PROVENANCE`, and its `run_manifest.json` hash was **byte-identical** to the first: `f607ca6d...`. The operator had not pulled the fix, which is how it was noticed; but the fix would not have worked either |
| Cause | `run_pilot.chain_config` flattens the pilot config into per-chain keys — `rescue_manifest`, `base_corpus`, `model`, and so on — and carried **no `data` key at all**. `new_manifest` therefore read `config.get("data", _DEFAULT_DATA)` and got the default, so the corrected `build_partitions` was never handed the `manifests` block it had just been taught to read |
| Why the F-019 verification missed it | It called `new_manifest(pilot_config)` with the config **as it exists on disk**, and `test_pilot_manifest_carries_partitions` did the same. Neither exercised `chain_config`, so both confirmed a property of a file rather than a property of the runner. The config on disk was never the object in question |
| Fixed | `chain_config` passes the pilot's `data` block through. Confirmed by a dry run — free, no GPU — whose `run_manifest.json` now carries 22,637 / 4,235 / 1,359 / 60 / 60 records |
| Verified against certification | The dry-run artifacts were patched with the chain's *measured* token counts (16,678,912 total, 0 human) and validated: `classification: valid_with_limitation`, reason codes `LIMIT_NEAR_DUPLICATE_NOT_CHECKED` and `LIMIT_TOKEN_LEDGER_NOT_RECOMPUTABLE` only, exit 0. `SEPARATION_MISSING_PROVENANCE` is gone |
| Pinned by | `test_the_launcher_passes_provenance_through_to_the_manifest`, which builds a manifest from `chain_config`'s output for **every arm**, not from the file |
| Cost | Zero. Caught by a dry run and an artifact patch, both free, before a third paid chain |
| Lesson | Verifying a fix against the object you edited proves the edit; it does not prove the behaviour. The manifest is written from a config the runner *constructs*, and no test had ever built that object. Two of the three checks written for F-019 shared the defect they were written to catch |

### F-020 — terminal reconciliation raised joint's cap but not its floor (2026-08-19)

| Field | Value |
|---|---|
| Stage | B pilot, **after the full grid ran**. 25/25 chains complete, 0 failed |
| Observation | `--check-only` over the completed grid exits 1: realised spend across spending arms spans 674,193 to 749,995 against a 750,000 ceiling, a **10.1070%** spread. `joint` consumed 674,193 at *every* seed — 75,807 short, where one indivisible candidate is at most 26,902 |
| Consequence | The primary contrast is **invalid**, not null. `joint` received 10.1% less human data than the arm it is compared against, so `PROTOCOL.md` §4's fairness condition fails and `CLAIMS.md` C-002's contract is unmet by this run. F-015's confound, returning through a different mechanism at one tenth the magnitude |
| Cause | `terminal.policy_for_final_generation` rebuilds `JointPolicy` with `base = allowance // 2`, raising its cap to the whole remainder. But `JointPolicy` is the only arm whose spend is gated by an internal rule rather than by its allowance: `_feasible_budget` floors the allocation at `remaining - maximum * future_generation_count`, and that floor equals the remainder only when the policy believes no spending generation follows. Reconciliation fires at `horizon - 2` = 8, where the chain's horizon of 10 leaves `future_generation_count == 1`, so the floor collapsed to **1** token. Measured directly. The urgency rule, not the reconciliation, then decided the spend — and at low urgency `_desired_budget` returns 0 |
| The comment was wrong, not just the code | `terminal.py` stated the clamp "floors it at the reserve, which at the last generation is the whole remainder". True at generation 9; reconciliation runs at generation 8. The claim and the call site disagreed and nothing checked |
| Why the dry run missed it | `JointPolicy` allocates from `mode_statistics`, which the dry run simulates. The simulated grid reached a different urgency and recorded `joint` at 749,844 — matching the other arms and passing the check. The real grid recorded 674,193. **Budget matching for score-dependent policies is not testable by simulation.** `random` and `schedule_only`, which do not score, reproduced their dry-run spends to the token |
| Why the suite missed it | `terminal.py` had tests, but none asserted the property the module exists for: that after reconciliation a spending arm has actually spent its remainder. The tests checked that reconciliation was *applied*, not that it *bound* |
| Fixed | `policy_for_final_generation` now rebuilds `JointPolicy` with horizon `last_spending_generation(horizon) + 1`, so at the reconciliation generation it sees no future generation and the floor becomes the whole remainder. `tests/policies/test_terminal_reconciliation_binds.py` (19 tests) asserts every spending arm lands within one candidate of its ceiling across four urgency levels; 4 fail if the fix is reverted, verified by reverting it |
| Cost | The full grid, ~7.7 hours and the session's remaining GPU budget. The run is not wasted — it delivers the variance estimate the pilot was commissioned for — but the contrast it was also meant to inform must be re-run |
| Scientific consequence | No invalid claim was published: the guard caught this before any result was read, which is what P-008 was built to do. `docs/runs/primary_pilot_2026-08-18_results.md` records the contrast as NOT ESTABLISHED and the variance estimate as sound |
| Lesson | Three of this session's five defects (F-016, F-018, F-020) were the same shape: a check whose *intent* was documented and whose *implementation* did not achieve it, with no test asserting the intent. A guard that has never been observed to bind is a guard whose binding is unverified |

### F-020a — the grid's wall time was overstated (2026-08-19)

| Field | Value |
|---|---|
| Relation to F-020 | **Correction, appended not edited.** F-020's cause, fix and scientific consequence stand; one of its cost figures was wrong |
| What was wrong | F-020 records the cost as "the full grid, ~7.7 hours". That figure was the span between launch (21:40) and the operator *observing* completion (05:24). It is not the run's duration |
| Measured | From the shard summaries: shard 0 ran **6.75 h** over 7 chains; shards 1-3 ran 5.80, 5.81 and 5.80 h over 6 chains each. Wall time for the grid is the longest shard, **6.75 h**, so the run finished near 04:25 and about an hour of pod time was billed idle afterwards |
| Why it matters | The overstatement propagated into `docs/STATUS.md`, `docs/runs/primary_pilot_2026-08-18_results.md` and the cost estimate for a re-run, inflating it by roughly 15%. Anyone sizing the powered experiment from these documents would have over-budgeted |
| How it happened | The figure was computed from timestamps in the operator's terminal rather than read from `wall_seconds` in the artifacts, which is the same class of error the project's "no invented numbers" rule exists to prevent: a number that was inferred rather than read, and that nothing checked |
| Fixed | Corrected in both documents. The manuscript now cites `\PilotWallHours`, generated from the shard summaries by `scripts/generate_pilot_outputs.py`, so the figure cannot be typed by hand again |
| Scientific consequence | None. No result depends on wall time; only cost planning did |

### F-021 — total optimizer tokens were never matched, and 10 chains certify invalid (2026-08-19)

| Field | Value |
|---|---|
| Stage | B pilot, post-run analysis. Found while running the submission checklist's mechanical checks, not by the run's own gates |
| Observation | Running `scripts/validate_run.py` over all 25 retained chains returns **10 `invalid`, 15 `valid_with_limitation`** — not the uniform `valid_with_limitation` recorded in `docs/runs/primary_pilot_2026-08-18_results.md`, `docs/STATUS.md` and `paper/sections/07_results.tex`. The five `joint` chains fail on `BUDGET_HUMAN_MISMATCH` and `BUDGET_TOTAL_MISMATCH`; the five `selection_only` chains fail on `BUDGET_TOTAL_MISMATCH` alone |
| How the wrong claim was made | The pod run reported `VALIDATE_EXIT=2` for the whole set, and 2 was read as "every chain is `valid_with_limitation`". It is the aggregate exit code, not a per-chain classification, and it does not distinguish "all limited" from "some limited, some invalid". The per-chain report was written to `validation.json` and never read |
| The substantive defect | `PROTOCOL.md` §4 requires matched lifetime human-origin tokens **and matched total optimizer tokens**. Only the human axis was ever asserted — by `run_pilot --check-only`, by `runner/budget_matching`, and by every statement made about this run. Realised totals: `no_rescue` 16,678,912; `schedule_only` 16,773,427; `random` 16,777,421; `joint` 17,025,024; `selection_only` 17,063,936. **Cross-arm spread 2.26%, above the 2% practical effect threshold** |
| What this costs the secondary analysis | The claim that the twenty non-`joint` chains are "budget-matched" is true on the human axis (0.038%) and **false on the total axis**. Pairwise, only **`random` vs `schedule_only`** is matched on both (human −0.00%, total +0.02%). Every contrast involving `selection_only` carries a **1.7%** total-token gap in the same direction as its measured advantage |
| What survives | The `schedule_only` vs `random` null — timing does not detectably help — is matched on both axes and stands as the one clean contrast this run supports. Its interval already contained zero |
| What does not | The `selection_only` advantage (8.4–10.1% depending on comparator) is **confounded by 1.7% more total training volume**. The effect is roughly five times the confound and same-signed, so it is suggestive rather than nothing, but it is no longer a budget-matched result and must not be reported as one |
| Also violated | `docs/SUBMISSION_CHECKLIST.md`: "No chain classified `invalid` is included in any analysis." Ten invalid chains were included in the secondary analysis before this was found |
| Mechanism, not yet root-caused | Human spend matches to 0.038% while totals differ by up to 2.26%, so the divergence is not in the rescue accounting. The likely path is block packing: examples are tokenized into fixed-size blocks, so selecting a different set of examples changes how they pack and therefore how many optimizer tokens the same nominal budget consumes. Unconfirmed — the per-generation batch records needed to settle it were not retained |
| Fixed | Not fixed. The measurement is recorded and the affected claims are corrected. Matching totals is a design change, not a patch: it requires either equalising realised total tokens by construction or re-specifying the constraint, which is an owner decision of the same kind as F-015's four options |
| Scientific consequence | Material. One reported finding is withdrawn to "suggestive but confounded", one is retained as clean, and the run's certification status is corrected from uniformly limited to 10 invalid. No claim survives that was not restated |
| Lesson | The run had a budget guard and it passed, because it asserted one of the two axes the protocol names. A guard that checks half a constraint reports success for the half it checks. `--check-only` should assert both axes; that it does not is why three documents carried a false statement for a day |

### F-021a — a re-run would not fix the total-token axis (2026-08-19)

| Field | Value |
|---|---|
| Relation to F-021 | **Analysis, appended.** F-021 records the defect; this records what does and does not repair it, because the difference decides whether to spend on a re-run |
| The question | F-020 is fixed, so a re-run would give `joint` its full human budget. Does that also close the 2.26% total-token spread F-021 found? |
| Answer: no | `selection_only` and `random` consumed 749,827 and 749,869 human tokens — matched to 0.04% — and their **totals differ by 1.71%** regardless. The divergence is therefore not caused by `joint`'s underspend and is untouched by fixing it. A re-run at the current design would reproduce it |
| What that means for the money | Re-running now buys a valid *human* axis and leaves the *total* axis violated, so the primary contrast would still fail `PROTOCOL.md` §4 and still certify invalid. **Spending on a re-run before the total axis is decided buys a differently-broken run, not a fixed one** |
| Mechanism, still unconfirmed | Human spend matches while totals do not, so the difference is not in rescue volume. Candidates are block packing (different examples pack differently into fixed-size blocks) or the generated corpus (arms train differently, generate differently, and the synthetic corpus tokenizes to different lengths). The per-generation batch records that would settle it were not retained — `chain_result.json` carries only chain totals |
| Options, none chosen here | The same shape as F-015's four. (1) Equalise realised total tokens by construction, e.g. truncating each generation's assembled corpus to a fixed token count. (2) Re-specify the constraint so total tokens are a reported covariate rather than an asserted equality, as P-009 did for the projection. (3) Match on totals post hoc by truncation, which discards data and changes what each policy did. (4) Accept and state the confound, which forfeits the `PROTOCOL.md` §4 guarantee for every contrast |
| Owner | The budget definition is Aarav's (`DECISIONS.md` U-003). This is a design decision of the same weight as F-015's, not a patch |
| Cheap and worth doing first | Retain per-generation token accounting in the next run. `runner/real_chain` already knows each generation's assembled corpus; emitting its token count per generation would have made this diagnosable in minutes instead of unresolvable. That change costs nothing and is the difference between finding the cause and speculating about it |
| Scientific consequence | The pilot's usable outputs are unchanged — variance, feasibility, the timing null, the apparatus. What changes is the plan: a re-run is **not** the next step, and deciding the total axis is |

### F-022 — the dry run cannot validate displacement either (2026-08-19)

| Field | Value |
|---|---|
| Stage | Pre-launch for the corrected grid. Found while dry-running `primary_pilot_v2.json`, before any paid step |
| Observation | The v2 dry run reports `budget matching: HOLDS` and 25/25 chains, and its assembled corpora hold 11-72 records against a `corpus_record_budget` of 400. Displacement did not take effect and the dry run did not notice |
| Cause | Not a defect in displacement. A dry run performs no decode, so `prev_corpus` is empty and there are no synthetic records to displace; the assembled corpus is the rescued human examples alone. Displacement equalises training volume only when there is volume to displace |
| Why it matters | P-011 exists to close F-021, and **the free check cannot confirm it worked**. Launching the grid on a green dry run would have repeated the exact pattern of F-017 and F-020: a passing dry run followed by a paid run that reproduces the defect it was supposed to have fixed. Third occurrence of the same shape |
| Fixed | `assemble_training_corpus` now returns `corpus_record_shortfall`, so a corpus that could not be filled is visible per generation rather than silently small. Three tests in `tests/data/test_corpus_displacement.py` pin it, including the generation-0 and dry-run case |
| The check that does work | One real chain of `selection_only` -- the arm whose totals ran 1.7% high under additive assembly -- then reading the assembled corpus sizes directly. Every generation after the first must hold exactly 400 records. `docs/RUNBOOK_V2_CORRECTED_GRID.md` step 3 |
| Cost | Zero. Caught by inspecting the dry run's output rather than trusting its verdict |
| Scientific consequence | None yet; no chain has run under P-011. The consequence avoided was launching a $20 grid whose central correction was unverified |
| Lesson, third time | The dry run's coverage boundary is now enumerated three ways: it cannot see the subprocess environment (F-017), it cannot check budget matching for score-dependent policies (F-020), and it cannot exercise anything that consumes the decoded corpus (F-022). Each was discovered by a paid or nearly-paid failure. The general rule -- **a simulation cannot validate a property of the thing it simulates away** -- is now stated in the runbook rather than rediscovered |
