# Week 3 Runner Integrity Report

> **STATUS: PARTIAL — unit evidence only.**
> The determinism, resume, and atomic-write behaviours below are covered by
> tests that pass today. Nothing here reflects a primary chain, because none has
> run. Sections marked NOT PERFORMED require execution.

Reproduce the unit evidence with:

```bash
pytest tests/runner -q
```

---

## 1. What is actually tested today

| Property | Test | State |
|---|---|---|
| Deterministic smoke condition reproduces identical outputs | `tests/runner/test_determinism.py` | ✅ passing |
| Interrupted and uninterrupted chains agree under the resume rule | `tests/runner/test_checkpoint_resume.py` | ✅ passing |
| Checkpoint write/read round-trip | `tests/runner/test_checkpoint.py` | ✅ passing |
| Manifest creation, append-only status history | `tests/runner/test_manifest.py` | ✅ passing |
| Illegal status transitions rejected | `tests/runner/test_manifest.py` | ✅ passing |
| Artifact writes are atomic | `tests/runner/test_atomic_write.py` | ✅ passing |
| Failed runs cannot be promoted to valid completion | `tests/runner/test_failure.py` | ✅ passing |
| Every artifact reference carries a matching hash | `tests/runner/test_artifact_hashes.py` | ✅ passing |
| Primary configs contain no hidden defaults | `tests/runner/test_reference_configs.py` | ✅ passing (guard mode) |
| Two-generation chain completes | `tests/runner/test_two_generation_chain.py` | ✅ passing |
| Manifest emits complete partition provenance | `tests/runner/test_manifest_provenance.py` | ✅ passing |
| Toy chain certifies end-to-end as `valid` | `tests/runner/test_validate_toy_chain.py` | ✅ passing |

At the last full run: **228 tests pass, 14 skipped**, ruff is clean, and the strict
repository audit passes. The 14 skips are the reference-config assertions in
`tests/runner/test_reference_configs.py`, which activate when the primary configs
leave `AWAITING_JULY_31_FREEZE`.

The last two rows are new on `claude/week-3-assignments-boq852`. Until they existed,
every test stopped either at the manifest or at the validator and none joined the
two — which is why the defect in section 2 survived a passing suite.

## 2. Resolved defect — certification was blocked for every chain

**`run_manifest.json` emitted no `data.partitions` block.** Found by running the
finished validator against the toy smoke chain, and fixed on
`claude/week-3-assignments-boq852`.

Before:

```
$ python scripts/validate_run.py runs/fixture_joint_seed1
"classification": "invalid",
"reason_codes": ["SEPARATION_MISSING_PROVENANCE"],
"checks_failed": ["separation_partitions_recorded"]     # 14 checks passed
EXIT=2
```

After:

```
$ python scripts/validate_run.py runs/fixture_joint_seed1
"classification": "valid",
"reason_codes": [],
"checks_failed": []                                     # 20 checks passed
EXIT=0
```

`runner/manifest.py` now resolves `data.partitions` from one of two declared
sources — inline canonical records, or `partition_manifests` mapping each canonical
partition to a JSONL file loaded through `data/manifest.py:load_manifest_from_jsonl`.
Declaring neither omits the block, so a run without provenance still classifies
`invalid`; that behaviour is pinned by
`tests/runner/test_manifest_provenance.py::test_no_provenance_source_still_classifies_invalid`.

Three properties matter for real chains:

- **Failure is loud and early.** A missing manifest file, an incomplete provenance
  record, an empty partition, or an unknown partition name raises
  `ManifestProvenanceError` at manifest creation — before a chain launches, not
  after compute is spent. Provenance cannot be back-filled after a run.
- **Leakage stops the run.** `data/separation.py:assert_disjoint` runs as a
  pre-launch preflight, so a forbidden partition overlap fails before any
  accelerator time is consumed.
- **The contract is recorded.** `schemas/run_manifest.schema.json` now declares the
  block explicitly and `docs/interfaces/run_manifest.md` documents it.

### 2.1 Vocabulary conflict found while fixing this — open, @Neil

Two `data/`-owned modules disagree on partition and field names:

| | Partitions | Fields |
|---|---|---|
| `validation/audit.py:29-37` | `base_human_train`, `generation_prompts`, `final_human_test` | `stable_id`, `source_dataset` |
| `data/manifest.py:12-19` | `base_train`, `prompts`, `test` | `example_id`, `source` |

The validator's vocabulary is canonical — it is the one documented in
`docs/evaluation/week3_data_evaluation_appendix.md` and covered by the validator's
adversarial tests. The runner translates in `_DATA_MODULE_PARTITIONS` rather than
editing a module it does not own. Reconciling the two is @Neil's call; until then the
mapping is a runner-side workaround, and a rename on either side breaks it silently.

## 3. Preflight results — NOT PERFORMED

Schema, leakage, and budget preflights against real frozen assets. Blocked: the
primary configs are skeletons marked `AWAITING_JULY_31_FREEZE`.

- Schema preflight: TODO(khantushig)
- Leakage preflight: TODO(khantushig)
- Budget equality preflight: TODO(khantushig)

## 4. Resume equivalence on a real chain — NOT PERFORMED

The frozen procedure, once chains exist:

1. Preserve an uninterrupted deterministic smoke run and its final scientific state.
2. Stop the same frozen seed and config at an approved checkpoint, resume once, finish.
3. Compare cumulative token ledgers, generation state, manifest history, metric
   outputs, and deterministic hashes where the framework allows.
4. Document unavoidable nondeterminism and its frozen tolerance.

- Uninterrupted final state: TODO(khantushig)
- Resumed final state: TODO(khantushig)
- Token ledger continues exactly once: ☐
- Equivalence level achieved: ☐ byte-identical ☐ conclusion-level only

**Do not claim byte identity when only conclusion-level reproducibility holds.**

## 5. Known nondeterminism — NOT CHARACTERISED

Sources and their frozen tolerance, on real hardware.

| Source | Present | Tolerance | Evidence |
|---|---|---|---|
| GPU kernel nondeterminism | TODO | TODO | TODO |
| Dataloader ordering | TODO | TODO | TODO |
| Mixed precision | TODO | TODO | TODO |

The toy chain runs on CPU and exercises none of these.

## 6. Unresolved runner limitations

1. **The partition vocabulary conflict is unreconciled** (section 2.1). The runner
   translates; a rename on either side breaks it silently. @Neil.
2. **Real training is not implemented.** `docs/STATUS.md`: *"Contract toy runner
   provided … real training not implemented."* Every test above exercises the
   toy path.
3. **Resume tested only on the toy chain.**
4. **No compute records exist on this branch** — `COMPUTE.md` has no measured
   accelerator hours here. The positive-control compute *was* measured, on
   `week-2/khantushig-positive-control`, which is unmerged; see
   `docs/audits/week2_merge_gap.md`.
5. **Artifact retention is a live trap for the real runner.** `validation/audit.py`
   re-hashes every entry in `manifest["artifacts"]` from bytes on disk and
   `ARTIFACT_MISSING` is invalidating. Nothing populates `artifacts[]` today, and
   `positive_control_adapter.py` deliberately keeps it empty with hashes in a
   pre-pruning sidecar. A real chain runner that lists prunable checkpoints in
   `artifacts[]` and then prunes them to fit ephemeral storage will classify
   `invalid`. The convention is recorded in `docs/interfaces/run_manifest.md`.

## 7. Determinism evidence for the toy chain

Two consecutive runs of the frozen toy config, same seed, separate output
directories:

| Artifact | Run 1 | Run 2 |
|---|---|---|
| `chain_result.json` | `75a3607e53d3…` | `75a3607e53d3…` |
| `run_manifest.json` | `97ea999a42b1…` | `97ea999a42b1…` |

Byte-identical, and both certify `valid`. This is CPU-only fixture evidence: it
demonstrates seed propagation and stable serialisation, and says nothing about GPU
kernel nondeterminism, dataloader ordering, or mixed precision (section 5).
