# Validity Certificate — Template

**Deliverable:** `docs/weekly/WEEK_3.md` and `WEEK_4.md`, Neil — "Finalize data card, evaluation
appendix, and per-result validity certificate" / "signed-style validity report classifying each
headline result."

**How to use:** copy this file to `results/certificates/<run_id>.md`, fill every field, and leave no
field blank. A blank field is not a pass — it is an unfilled check, and the certificate cannot be
issued with one. Machine-checkable rows are produced by `python scripts/validate_run.py <run_dir>`;
the remainder require Neil's independent inspection.

**Independence requirement:** the certificate is issued by someone who did not produce the run. The
whole point is a second pair of eyes on artifacts, so a self-certified run carries no more weight
than an uncertified one.

---

## Certificate header

| Field | Value |
|---|---|
| Run ID | `<run_id>` |
| Artifact location | `<immutable path or storage URI>` |
| Certifying member | `<name — must not be the run operator>` |
| Run operator | `<name>` |
| Certificate date | `<YYYY-MM-DD>` |
| Code commit | `<40-char sha>` |
| Protocol version | `<tag or commit of PROTOCOL.md>` |
| **Classification** | `valid` / `valid_with_limitation` / `invalid` |

## 1. Automated verdict

Run and paste verbatim:

```bash
python scripts/validate_run.py <run_dir> --json
```

| Check | Result |
|---|---|
| Exit code (0 valid, 2 limitation, 1 invalid) | |
| Blocking failures reported | |
| Limitations reported | |

The automated verdict is necessary, not sufficient. It checks contracts and accounting; it cannot
check whether a manifest's declared dataset is the dataset that was actually read.

## 2. Asset provenance

| Check | Method | Result |
|---|---|---|
| Dataset identifier and revision match the frozen config | Compare manifest `data` block to `configs/data/*.json` | |
| Train manifest SHA-256 recomputed and matches | Rehash the manifest file | |
| Model identifier, revision, tokenizer revision recorded and resolvable | Manifest `model` block | |
| Policy config SHA-256 recomputed and matches | Rehash `configs/policy/*.json` | |
| Code commit exists and working tree was clean | Manifest `git_commit`, `working_tree_clean` | |
| Environment record complete (OS, Python, framework, hardware) | Manifest `environment` block | |

## 3. Data separation — blocking

Any failure here makes the result `invalid`. No exceptions, no partial credit.

| Check | Result |
|---|---|
| Base train, rescue candidates, prompts, validation, and final test partitions are pairwise disjoint by stable content hash | |
| No exact duplicate spans partitions | |
| No near-duplicate above the frozen threshold spans prompt/test or candidate/test | |
| No final-test example appears in any prompt | |
| No final-test example influenced selection, thresholds, early stopping, or hyperparameters | |
| Partition assignment is reproducible from the recorded seed | |

**Evidence:** `<path to overlap report>`

## 4. Token accounting — blocking

| Check | Result |
|---|---|
| Counts derive from tokenized batches actually consumed by the optimizer, not document estimates | |
| Padding treated consistently and documented | |
| Repeated presentations counted once per presentation | |
| Gradient accumulation counted per micro-batch, not per optimizer step | |
| Resume neither double-counts nor drops the checkpoint-straddling batch | |
| Lifetime human-origin total matches the manifest budget exactly | |
| Total optimizer-token count matches the manifest budget exactly | |
| Budget equality holds across every condition in the comparison | |

**Evidence:** `tests/data/test_token_accounting.py` covers all six conditions on fixtures; this
section certifies the same properties on the real run.

## 5. Provenance retention

Every training example retains, after shuffling and batching:

| Field | Retained? |
|---|---|
| Stable ID | |
| Content hash | |
| Source dataset and revision | |
| Human or synthetic origin | |
| Recursive generation | |
| Selection policy and score | |
| Selected flag | |
| Number of optimizer presentations | |

## 6. Reproducibility

| Check | Result |
|---|---|
| Seeds propagate through sampling, generation, initialization, dropout, and evaluation | |
| Resume from checkpoint preserves the predeclared conclusion | |
| Metrics recomputed independently from raw outputs agree with the reported values | |
| Aggregates regenerate byte-identically from immutable artifacts | |
| Figure and table content hashes match those recorded at generation time | |

**Independent recomputation is required, not optional.** Recompute the primary NLL and tail metrics
from the frozen raw outputs with your own invocation and compare to the reported chain values.
Record both numbers even when they agree.

## 7. Scope limitations

List every limitation that applies. A run can be `valid` and still carry limitations that constrain
what the paper may say about it.

- [ ] Chain incomplete (fewer generations than horizon)
- [ ] Fixture-stage artifact, not scientific evidence
- [ ] Working tree dirty at run time
- [ ] Run resumed after an infrastructure failure
- [ ] Excluded under a frozen exclusion rule (state which)
- [ ] Metric count disagrees with `generations_completed`
- [ ] Other: `<describe>`

## 8. Classification rationale

State in two or three sentences why the classification was chosen, referencing the specific rows
above. If any blocking row failed, the classification is `invalid` regardless of everything else.

> `<rationale>`

## 9. Consequence for claims

| Claim | Effect of this run |
|---|---|
| C-002 | |
| C-003 | |

If the classification is `invalid`, the correct entry is "no effect — excluded from all analysis,"
and a `FAILURE_LOG.md` entry is required with the cause classified as implementation,
infrastructure, protocol, or scientific.

## 10. Certifying statement

> I inspected the artifacts named above on `<date>`. Every check recorded as passing was checked by
> me against the artifact, not inferred from the pipeline's own reporting. I did not operate this
> run.
>
> `<certifying member>`

---

## Batch certification

At a results freeze, classify every run at once and retain the output:

```bash
python scripts/validate_run.py runs/* --json > results/certificates/batch_verdicts.json
```

The process exits with the worst state observed across all runs, so a non-zero exit at freeze time
means at least one run needs individual attention before the freeze can be tagged. Failed and
incomplete chains are preserved and certified as such — they are not deleted.
