# Week 3 Adversarial Audit of the Validator

The validator is developed against synthetic attacks, never against another
person's unfinished branch or a real experimental artifact. This file records
which attacks exist, what each should produce, and what it actually produced.

**Observed decisions below are real**: they come from running the test suite, not
from expectation. Reproduce with:

```bash
pytest tests/validation tests/runner/test_artifact_hashes.py -q
```

**Status:** the validator is complete and passes every attack listed. It has
**not** been applied to a primary chain, because none exists yet
(`docs/STATUS.md`). It has been run once against the toy smoke chain — see
section 7, which records a real finding. Section 8 lists the blind spots.

---

## 1. Data separation

| # | Attack | Fixture | Expected | Observed | Pass |
|---|---|---|---|---|---|
| 1.1 | Generation prompts duplicated from the final human test partition | `test_prompt_to_final_test_overlap_is_invalid` | `invalid` / `SEPARATION_OVERLAP` | as expected | ✅ |
| 1.2 | A rescue candidate copied from the final human test partition | `test_rescue_candidate_to_final_test_overlap_is_invalid` | `invalid` / `SEPARATION_OVERLAP` | as expected | ✅ |
| 1.3 | Training example with a blank stable ID | `test_missing_stable_id_is_invalid` | `invalid` / `SEPARATION_MISSING_ID` | as expected | ✅ |
| 1.4 | Provenance field (`source_dataset`) deleted | `test_missing_provenance_field_is_invalid` | `invalid` / `SEPARATION_MISSING_PROVENANCE` | as expected | ✅ |
| 1.5 | Manifest records no partitions at all | `check_separation` guard | `invalid` / `SEPARATION_MISSING_PROVENANCE` | as expected | ✅ |

Pairs checked: base-train/final-test, rescue/final-test, prompts/final-test,
validation/final-test, base-train/rescue. Comparison is on normalized content
hash, so a re-serialised duplicate is still caught.

## 2. Token accounting and budgets

| # | Attack | Fixture | Expected | Observed | Pass |
|---|---|---|---|---|---|
| 2.1 | Consumed human tokens exceed the frozen budget | `test_human_budget_mismatch_is_invalid` | `invalid` / `BUDGET_HUMAN_MISMATCH` | as expected | ✅ |
| 2.2 | Consumed total tokens exceed the frozen budget | `test_total_budget_mismatch_is_invalid` | `invalid` / `BUDGET_TOTAL_MISMATCH` | as expected | ✅ |
| 2.3 | Negative token count | `check_budgets` guard | `invalid` / `BUDGET_NEGATIVE` | as expected | ✅ |
| 2.4 | Padding counted as a consumed token | `test_padding_is_never_counted_as_a_consumed_token` | padding excluded | as expected | ✅ |
| 2.5 | Repeated human exposure omitted from the ledger | `test_repeated_human_exposure_counts_every_presentation` | counted twice | as expected | ✅ |
| 2.6 | Gradient accumulation changes totals | `test_split_batches_accumulate_like_one_batch` | split == single | as expected | ✅ |
| 2.7 | Human/synthetic ledger mismatch | `test_synthetic_tokens_are_excluded_from_the_human_ledger` | ledgers separate | as expected | ✅ |
| 2.8 | Corrupt attention mask value | `test_invalid_mask_value_is_rejected` | `ValueError` | as expected | ✅ |

## 3. Artifact integrity

| # | Attack | Fixture | Expected | Observed | Pass |
|---|---|---|---|---|---|
| 3.1 | Checkpoint bytes altered after hashing | `test_corrupt_checkpoint_hash_is_detected` | `invalid` / `ARTIFACT_HASH_MISMATCH` | as expected | ✅ |
| 3.2 | Referenced artifact deleted | `test_missing_referenced_artifact_is_detected` | `invalid` / `ARTIFACT_MISSING` | as expected | ✅ |
| 3.3 | `chain_result.json` absent | `test_missing_chain_result_is_detected` | `invalid` / `ARTIFACT_MISSING` | as expected | ✅ |
| 3.4 | Manifest is unparseable | `test_unparseable_manifest_is_schema_invalid` | `invalid` / `ARTIFACT_SCHEMA_INVALID` | as expected | ✅ |
| 3.5 | Schema-invalid field type | `test_schema_violation_is_reported_and_invalid` | `invalid` + `schema_failures` | as expected | ✅ |
| 3.6 | Artifact referenced without a hash | `test_artifact_without_recorded_hash_is_a_limitation` | `valid_with_limitation` | as expected | ✅ |
| 3.7 | Dirty or unknown working tree | `test_dirty_working_tree_is_invalid`, `test_unknown_clean_state_is_caught` | `invalid` / `COMMIT_DIRTY` | as expected | ✅ |
| 3.8 | Multi-block file hashed incorrectly | `test_large_file_hashes_in_blocks` | matches `hashlib` | as expected | ✅ |

## 4. Protocol compliance

| # | Attack | Fixture | Expected | Observed | Pass |
|---|---|---|---|---|---|
| 4.1 | Chain seed differs from the manifest seed | `test_seed_mismatch_is_invalid` | `invalid` / `PROTOCOL_SEED_MISMATCH` | as expected | ✅ |
| 4.2 | Generations exceed the frozen horizon | `test_horizon_exceeded_is_invalid` | `invalid` / `PROTOCOL_HORIZON_MISMATCH` | as expected | ✅ |
| 4.3 | Result policy differs from manifest policy | `test_policy_mismatch_is_invalid` | `invalid` / `PROTOCOL_POLICY_MISMATCH` | as expected | ✅ |
| 4.4 | Run still `running` at audit time | `test_non_terminal_status_is_invalid` | `invalid` / `PROTOCOL_STATUS_NOT_TERMINAL` | as expected | ✅ |
| 4.5 | Fewer generations than the horizon | `test_reduced_generations_is_valid_with_limitation` | `valid_with_limitation` | as expected | ✅ |

## 5. Evaluator reliability

| # | Attack | Fixture | Expected | Observed | Pass |
|---|---|---|---|---|---|
| 5.1 | Tail retention outside `[0, 1]` | `test_out_of_range_tail_retention_is_invalid` | `invalid` / `EVALUATION_TAIL_OUT_OF_RANGE` | as expected | ✅ |
| 5.2 | Non-finite NLL | `test_non_finite_nll_is_invalid` | `invalid` / `EVALUATION_NLL_NOT_FINITE` | as expected | ✅ |
| 5.3 | No metrics recorded | `check_evaluation` guard | `invalid` / `EVALUATION_NO_METRICS` | as expected | ✅ |
| 5.4 | Tail metric contaminated by the policy's own score | `test_common_modes_do_not_affect_the_tail_score` | score unchanged | as expected | ✅ |
| 5.5 | Tail metric not directional | `test_metric_is_directional_on_controlled_fixtures` | worse < better | as expected | ✅ |

## 6. Behaviour the validator must NOT have

| # | Property | Fixture | Observed | Pass |
|---|---|---|---|---|
| 6.1 | A poor scientific outcome is still `valid` | `test_poor_scientific_outcome_stays_valid` | `valid` | ✅ |
| 6.2 | Auditing never mutates the run directory | `test_audit_does_not_mutate_the_run_directory`, `test_cli_does_not_mutate_the_audited_directory` | hashes unchanged | ✅ |
| 6.3 | Identical inputs give identical reports | `test_classification_is_deterministic` | byte-identical | ✅ |
| 6.4 | An invalidating code outranks a limiting code | `test_invalidating_code_outranks_limiting_code` | `invalid` | ✅ |
| 6.5 | Unknown reason codes cannot be introduced | `test_classify_rejects_unknown_reason_code` | `ValueError` | ✅ |

6.1 is the most important row in this document. A validator that marks
unfavourable results invalid would silently launder the experiment.

---

## 7. First run against a real artifact directory — a finding

The validator was run once against output from the committed toy smoke chain:

```bash
python -m human_data_budget.runner.chain --config configs/experiment/toy_cpu.json
python scripts/validate_run.py runs/fixture_joint_seed1
```

**Result: `invalid`, reason code `SEPARATION_MISSING_PROVENANCE`.**

Fourteen checks passed — budgets matched the plan, seed and policy and horizon
agreed with the manifest, status was terminal, NLL was finite, tail retention was
in range, both core artifacts were present and the working tree clean. One check
failed: the toy runner's `run_manifest.json` records **no `data.partitions`
block**, so the auditor cannot verify that the five partitions are disjoint or
that any training example carries a stable ID, content hash, source dataset, and
origin.

This is correct behaviour, not a validator bug. The protocol requires per-example
provenance and the toy manifest does not emit it, so separation is unverifiable
and the run cannot be certified.

**Consequence for the runner (Khantushig):** a real chain will be classified
`invalid` for the same reason unless `run_manifest.json` gains a
`data.partitions` block with the four required provenance fields per example.
This should be fixed before any expensive primary run, not after — a full chain
that cannot be certified is wasted compute. The manifest schema permits the block
already (`additionalProperties: true`), so no schema change is needed.

### 7a. Resolved — recorded rather than rewritten

The finding above is left as it was written on 2026-08-09. It was correct then,
and an audit that edits its own history is not an audit.

It is now fixed. `runner/manifest.py` emits `data.partitions` from a declared
provenance source (`build_partitions`), refusing at manifest creation — before a
chain spends compute — if a partition is empty, a name is unrecognised, or a
required field is missing. The same command now returns:

```
valid_with_limitation
  LIMIT_NEAR_DUPLICATE_NOT_CHECKED
  LIMIT_TOKEN_LEDGER_NOT_RECOMPUTABLE
```

`SEPARATION_MISSING_PROVENANCE` is gone. The two remaining codes are not the old
defect returning: they are the checks added for blind spots 2 and 3 below
correctly reporting what they could **not** verify, rather than passing silently.
Neither downgrade is a property of the runner, and §8 states what each needs.

---

## 8. Remaining blind spots

Stated plainly, because an audit that claims full coverage is not credible.

1. **Only ever run against the toy chain.** Section 7 is the sole real-artifact
   invocation. No primary chain exists, so behaviour at real scale is untested.
2. **Near-duplicate detection — implemented, with a smaller reach than the name
   suggests.** `check_near_duplicate_separation` now calls
   `overlap.py`'s `find_near_duplicate_pairs` at that module's own 0.8 threshold.
   A reworded cross-partition leak is caught. Four limits remain, all pinned by
   tests in `tests/validation/test_near_duplicate_separation.py`:
   - **Semantic paraphrase is not caught.** Character 5-gram Jaccard is surface
     overlap. Measured: a reworded leak scores 0.9483 and is caught; the same
     sentence restated in different words scores 0.1667 and is not.
   - **A padded verbatim copy is not caught.** Jaccard is symmetric and measures
     no containment, so wrapping a stolen test example in filler defeats it. No
     paraphrasing skill is required. Closing this needs a containment measure —
     new detection logic, and a threshold that is the data owner's to choose.
   - **Five of ten partition pairs are unchecked.** `PROTOCOL.md` §3 requires all
     five partitions mutually disjoint; `FORBIDDEN_PARTITION_PAIRS` enumerates
     five pairs. Widening it would reclassify runs, so it is an owner decision.
   - **Two operating points ship with the same number.** `docs/data/overlap_report.md`
     §3 records the corpus-scale scan as **word-8-gram** Jaccard at 0.8; the
     auditor reuses `overlap.py`'s **character-5-gram** at 0.8. On the same
     one-word edit these score 0.9308 and 0.3846. Which is the intended audit-time
     definition needs @Neil.

   It also depends on the manifest carrying example text. The runner emits the
   four required provenance fields without text, so a real run reports
   `LIMIT_NEAR_DUPLICATE_NOT_CHECKED` rather than a false clean pass. Whether
   manifests should carry text, or the auditor should resolve partition sources
   itself, is a @Neil / @Khantushig decision.
3. **Token accounting — recomputed, but inert on any run this repository can
   currently produce.** `check_token_ledger` recomputes human and total tokens
   from realized batch records via `data/token_accounting.py`, so a ledger that is
   wrong but internally consistent is rejected. Honours the frozen rules: padding
   excluded, repeated presentations counted per presentation, gradient
   accumulation per micro-batch, resume counted once.
   - **Nothing emits `batch_records.jsonl`.** No runner, script, or schema
     produces it, so every real run takes the explicit
     `LIMIT_TOKEN_LEDGER_NOT_RECOMPUTABLE` branch. The check is closed in code and
     in tests; it is **closed pending a producer** end to end.
   - **A forged ledger still passes.** The auditor can only compare artifacts the
     run author wrote. Deleting the records downgrades to
     `valid_with_limitation` rather than certifying, which is the strongest thing
     it can do — it cannot compel an artifact to exist.
4. **Resume double-counting is untested end to end.** Covered at unit level in
   `tests/runner/test_checkpoint_resume.py`, not through the validator.
5. **Evaluator determinism on identical inputs is not asserted here.** Nothing
   detects a nondeterministic evaluator producing different NLLs for the same
   input.
6. **No cross-run comparison.** The validator audits one run at a time and cannot
   see that two arms consumed different budgets. Budget matching *across* arms is
   enforced only in `validate_matched_budgets` and the aggregator.
7. **Limitation categories are frozen but untested against a real limitation.**

Blind spots 2 and 3 are the highest severity: both let an invalid chain be
classified `valid`. Neither may be closed by relaxing a rule at the freeze — per
the packet, stop and report instead.
