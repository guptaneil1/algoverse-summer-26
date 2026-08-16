# Week 3 Runner Integrity Report

> **STATUS: PARTIAL — no primary chain has run.**
> The determinism, resume, and atomic-write behaviours below are covered by tests
> that pass today, and the positive control is verified by recomputation
> (`docs/positive_control/week3_verification.md`). Nothing here reflects a primary
> reference chain, because none has run. Sections marked NOT PERFORMED require
> execution.
>
> Against the six-clause completion gate: **clauses 2, 3, 4, 5 and 6 are met or
> honestly bounded; clause 1 is unmet and blocked** — see §9.

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
| Resume equivalence on all five frozen dimensions | `tests/runner/test_resume_equivalence.py` | ✅ passing |
| Whole smoke chain is byte-identical across runs | `tests/runner/test_determinism.py` | ✅ passing |

At the last full run: **235 tests pass, 14 skipped**, ruff is clean, and the strict
repository audit passes. The 14 skips are the reference-config assertions in
`tests/runner/test_reference_configs.py`, which activate when the primary configs
leave `AWAITING_JULY_31_FREEZE`.

The last four rows are new on `week-3/khantushig-reference-runs`. Until the
validator row existed, every test stopped either at the manifest or at the
validator and none joined the two — which is why the defect in section 2 survived
a passing suite. Until the determinism row existed, only the individual step
functions were checked, never the assembled chain.

## 2. Resolved defect — certification was blocked for every chain

**`run_manifest.json` emitted no `data.partitions` block.** Found by running the
finished validator against the toy smoke chain, and fixed on
`week-3/khantushig-reference-runs`.

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

## 4. Resume equivalence — PERFORMED on the smoke condition

The frozen procedure, and its state:

1. **Preserve an uninterrupted deterministic smoke run and its final scientific
   state.** ✅ `tests/runner/test_resume_equivalence.py`, fixture
   `interrupted_and_uninterrupted`.
2. **Stop the same frozen seed and config at an approved checkpoint, resume once,
   finish.** ✅ The resumed chain is seeded with generation 0's checkpoint only,
   simulating a crash immediately after it was written, then run with
   `resume=True`.
3. **Compare cumulative token ledgers, generation state, manifest history, metric
   outputs, and deterministic hashes.** ✅ Each dimension is asserted separately,
   so a regression names the invariant it broke rather than surfacing as an opaque
   dict inequality:

| Dimension | Test | Result |
|---|---|---|
| Cumulative token ledgers continue exactly once | `test_cumulative_token_ledgers_continue_exactly_once` | ✅ human and total ledgers equal the uninterrupted run and stay inside the frozen budget |
| Generation state | `test_generation_state_matches` | ✅ generations completed, current generation, horizon |
| Manifest history | `test_manifest_status_history_matches_and_is_terminal` | ✅ identical history, append-only, terminal `complete` |
| Metric outputs | `test_metric_outputs_match_generation_by_generation` | ✅ generation-by-generation |
| Deterministic hashes | `test_persisted_artifact_hashes_match` | ✅ `chain_result.json`, `run_manifest.json`, every checkpoint |

4. **Document unavoidable nondeterminism and its frozen tolerance.** See §5 and
   the scope statement below.

- Token ledger continues exactly once: ☑
- Equivalence level achieved: ☑ byte-identical **(smoke condition only)** ☐ conclusion-level only

The ledger dimension is called out separately because it is the one that fails
quietly. The classic resume defect re-adds the tokens of the generation resumed
from, which inflates consumption past the frozen budget and turns a good chain
into a budget-mismatched one rather than an obviously broken one.

### 4.1 Scope of the byte-identity claim

Byte identity is claimed **only** for the toy CPU smoke condition, which is what
the packet's test table specifies (*"interrupted and uninterrupted smoke
chains"*, *"the deterministic smoke condition"*). That path runs no model and no
accelerator.

It is **not** claimed for real training. Resuming a real chain from a checkpoint
involves GPU kernel nondeterminism, dataloader ordering, and mixed precision
(§5), none of which the toy path exercises. When a real chain runs, the honest
expectation is conclusion-level reproducibility with a stated tolerance, not byte
identity — and the tolerance must be frozen before the comparison, not chosen
after seeing the mismatch. `tests/runner/test_real_checkpoint_resume.py` on
`week-2/khantushig-positive-control` takes the same care: it tests the adapter's
ingest resume, which *is* a pure function of artifacts on disk, and explicitly
disclaims any bit-identical-weights claim.

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
3. **Resume equivalence is proven only on the toy chain** (§4.1). Real training
   resume is a weaker, separate claim and is not made.
4. **No primary-chain compute exists.** `COMPUTE.md` now carries the
   positive-control split (training and evaluation measured, generation a
   residual) and the toy fixture cost, but no reference chain has consumed
   anything.
5. **Artifact retention is a live trap for the real runner.** `validation/audit.py`
   re-hashes every entry in `manifest["artifacts"]` from bytes on disk and
   `ARTIFACT_MISSING` is invalidating. Nothing populates `artifacts[]` today, and
   `positive_control_adapter.py` deliberately keeps it empty with hashes in a
   pre-pruning sidecar. A real chain runner that lists prunable checkpoints in
   `artifacts[]` and then prunes them to fit ephemeral storage will classify
   `invalid`. The convention is recorded in `docs/interfaces/run_manifest.md`.

## 7. Artifact traceability

The gate asks that *every artifact is traceable*. Split by what exists:

| Scope | Artifacts | Hashed | Bytes retained | Re-verifiable |
|---|---:|---|---|---|
| Positive control (Week 2) | 64 | all 64, before pruning | 22 of 64 | 22 of 64 |
| Toy fixture chain | manifest, chain result, checkpoints | yes | yes | yes |
| Primary chains | — | — | — | none exist |

**Positive control.** Every artifact was hashed at run time into each generation's
`artifact_record.json` *before* any pruning, and the unretained set is enumerated in
`measurements/artifact_retention.json` with SHA-256 and recorded path. The
provenance chain is therefore complete — nothing is unaccounted for — but 42 of 64
hashes are **permanently unverifiable**, because the Kaggle container holding the
model directories and generated corpora was reclaimed at session end. This is not
recoverable by any future work.

What survived is the part that carries the science: all 22 `eval_results.json`
files are committed to git, and every number in
`docs/positive_control/week3_verification.md` §4 was recomputed from them.

**Consequence for Week 3.** Do not repeat this. Runbook §12.3 preserves state
across Kaggle sessions via *Add Data → Your Work → Notebook Output*, but that
carries only what the next session needs, not an immutable archive. Before a
primary chain runs, an external immutable destination must be chosen and recorded
in the run manifest — see §6.5 and `docs/interfaces/run_manifest.md`.

## 8. Determinism evidence for the toy chain

Two consecutive runs of the frozen toy config, same seed, separate output
directories:

| Artifact | Run 1 | Run 2 |
|---|---|---|
| `chain_result.json` | `75a3607e53d3…` | `75a3607e53d3…` |
| `run_manifest.json` | `97ea999a42b1…` | `97ea999a42b1…` |

Byte-identical, and both certify `valid`. This is CPU-only fixture evidence: it
demonstrates seed propagation and stable serialisation, and says nothing about GPU
kernel nondeterminism, dataloader ordering, or mixed precision (section 5).

## 9. Completion gate — clause by clause

The gate: *"The frozen no-rescue and fresh-random conditions have complete
immutable chains or complete failure packages; the positive control is cleanly
verified or honestly mismatched; every artifact is traceable;
generation/training/evaluation compute is recorded separately; runner determinism
and resume behavior are tested; and no result was used to tune the protocol."*

| # | Clause | State | Evidence |
|---|---|---|---|
| 1 | No-rescue + fresh-random chains or failure packages | **Unmet — blocked** | Zero chains. Not a failure package either: a failure package requires a launched run, and nothing was launched |
| 2 | Positive control cleanly verified or honestly mismatched | **Met** | `docs/positive_control/week3_verification.md` — all four frozen ordering claims recomputed from raw artifacts; `valid_with_limitation` |
| 3 | Every artifact traceable | **Met, bounded** | §7 — 64 of 64 hashed and accounted for; 42 unverifiable, disclosed not hidden |
| 4 | Gen/training/evaluation compute recorded separately | **Met** | `COMPUTE.md` — training and evaluation measured, generation a residual with stated uncertainty |
| 5 | Determinism and resume tested | **Met as specified** | §4 — all five resume dimensions asserted separately; §8 — whole-chain determinism byte-identical. Smoke condition, which is what the packet's test table specifies. Real-hardware nondeterminism remains uncharacterised (§4.1, §5) |
| 6 | No result used to tune the protocol | **Met** | Nothing has run that could tune anything. The post-hoc numeric comparison in the positive control is labelled post-hoc rather than presented as pre-registered |

### What clause 1 actually needs

Not runner work. Four steps, none of them code:

1. **Merge `cd73d39`** (`week-2/neil-frozen-data-metrics`) into
   `integration/week-2-jul25-jul31`. It is the only Week 2 branch not integrated,
   and it carries the frozen data: `configs/data/wikitext103.json` at
   `status: frozen`, `mode_definition: article_length_quantile`, the overlap
   report, the tail-retention freeze, and `scripts/build_wikitext103_manifests.py`.
2. **Build the partition manifests** — `python scripts/build_wikitext103_manifests.py`.
   They are generated, not committed; `data/manifests/` holds only a README.
3. **Approve real budgets.** `configs/experiment/primary_pilot.json` carries
   `scientific_status: "fixture_frozen_real_run_blocked"` and an explicit
   `real_run_blocker` requiring tokenizer-counted human and total token budgets.
   No code change removes this.
4. **Tag the freeze**, then fill `primary_no_rescue.json` and
   `primary_fresh_random.json` from it and set `_freeze_status: "FROZEN"`. The 14
   skipped tests in `tests/runner/test_reference_configs.py` activate on their own
   and enforce identical budgets and seed sets across the two arms.

Clause 5 is met at the level the packet specifies (§4). What clause 1 would add is
the *real-hardware* characterisation in §5 — run a real chain, stop it at an
approved checkpoint, resume once, and record the achieved equivalence level and
its frozen tolerance.

Clause 3's unverifiable 42 hashes never close. That evidence is gone.
