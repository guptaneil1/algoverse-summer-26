# Run Manifest Contract

A run manifest is created before execution and links the run to:

- full Git commit and clean/dirty state;
- model/tokenizer identifiers and revisions;
- dataset manifest paths/hashes;
- policy/training/generation/evaluation config paths/hashes;
- lifetime human-token and total-token budgets;
- chain/data/generation/training/evaluation seeds;
- environment and hardware;
- planned horizon and status.

Scientific settings are immutable after `running`. Status transitions and artifact references may be appended without erasing earlier state. The JSON Schema in `schemas/run_manifest.schema.json` is authoritative for machine validation.

## `data.partitions` — per-example provenance

`validation/audit.py` requires a `data.partitions` block to verify partition
disjointness and per-example provenance. Without it, a run classifies **`invalid`**
with `SEPARATION_MISSING_PROVENANCE`, regardless of how well the chain ran.

Each of the five partitions maps to a list of records carrying all four of
`stable_id`, `content_hash`, `source_dataset`, `origin`. A missing field is
invalidating, so `runner/manifest.py` raises `ManifestProvenanceError` at manifest
creation — before a chain launches — rather than after compute is spent. The frozen
rules do not permit back-filling provenance after a run.

A run config declares exactly one provenance source under `data`:

| Source | Shape | Used by |
|---|---|---|
| `partitions` | records already in the canonical form above | callers holding provenance in memory |
| `partition_manifests` | `{canonical_partition: jsonl_path}` | real chains and the toy fixture |

Declaring neither omits the block — deliberately, so a run without provenance keeps
classifying `invalid` instead of silently passing. Declaring both is an error.

### Vocabulary translation — flagged for @Neil

The two `data/`-owned modules disagree, and the runner translates rather than editing
either one:

| Canonical (`validation/audit.py`) | `data/manifest.py` | Canonical field | `Example` attribute |
|---|---|---|---|
| `base_human_train` | `base_train` | `stable_id` | `example_id` |
| `rescue_candidates` | `rescue_candidates` | `content_hash` | `content_hash` |
| `generation_prompts` | `prompts` | `source_dataset` | `source` |
| `validation` | `validation` | `origin` | `origin` |
| `final_human_test` | `test` | | |

The canonical column wins because it is the vocabulary already documented in
`docs/evaluation/week3_data_evaluation_appendix.md` and covered by the validator's
adversarial tests. `data/manifest.py:12-19` is the outlier. Reconciling the two is
@Neil's call; until then `runner/manifest.py` holds the mapping in
`_DATA_MODULE_PARTITIONS` and `_load_partition_manifests`.

## Artifact references and pruning

`validation/audit.py` re-hashes every entry in `artifacts[]` from bytes on disk, and
`ARTIFACT_MISSING` is an **invalidating** code. Any artifact listed there must still
exist at audit time.

Model and checkpoint directories are therefore **not** listed in `artifacts[]` when
they may be pruned to fit ephemeral storage. Hash them into a pre-pruning sidecar
carrying `path`, `sha256`, and a `pruned` flag instead — the convention
`runner/positive_control_adapter.py` already established. If an artifact must be
referenced but cannot be retained, make the reference optional so it lands on
`LIMIT_MISSING_OPTIONAL_ARTIFACT` (`valid_with_limitation`) rather than
`ARTIFACT_MISSING` (`invalid`), and decide that before launching.
