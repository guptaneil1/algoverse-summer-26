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

At the last full run: **215 tests pass** across the suite, ruff is clean, and the
strict repository audit passes.

## 2. Open defect — blocks certification of any real chain

**`run_manifest.json` emits no `data.partitions` block.**

Found by running the finished validator against the toy smoke chain:

```bash
python -m human_data_budget.runner.chain --config configs/experiment/toy_cpu.json
python scripts/validate_run.py runs/fixture_joint_seed1
# -> invalid, SEPARATION_MISSING_PROVENANCE
```

Fourteen checks passed; one failed. Without partition records the auditor cannot
verify that the five partitions are disjoint, nor that any training example
carries `stable_id`, `content_hash`, `source_dataset`, and `origin`.

**Consequence:** a real chain will be classified `invalid` for the same reason.
Fix before spending accelerator hours. `schemas/run_manifest.schema.json` already
permits the block (`additionalProperties: true`), so no contract change is
needed — `new_manifest` in `src/human_data_budget/runner/manifest.py` must
populate `data.partitions` from the frozen data manifests.

This is recorded as an open item, not a resolved one.

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

1. **Partition provenance missing from the manifest** (section 2) — highest
   severity; blocks certification.
2. **Real training is not implemented.** `docs/STATUS.md`: *"Contract toy runner
   provided … real training not implemented."* Every test above exercises the
   toy path.
3. **Resume tested only on the toy chain.**
4. **No compute records exist** — `COMPUTE.md` has no measured accelerator hours
   because nothing has been run.
