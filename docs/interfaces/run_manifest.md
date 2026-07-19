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
