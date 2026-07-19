# Evaluation Interface Contract

Input:

- checkpoint reference and SHA-256;
- frozen evaluation manifest and SHA-256;
- generation and run ID;
- frozen evaluation configuration and seed.

Output:

- schema version;
- run ID and generation;
- held-out human NLL;
- frozen tail-retention metric;
- evaluated non-padding token count;
- checkpoint/manifest/config hashes;
- evaluation environment metadata.

Rules:

- Final test data is evaluation-only.
- Evaluation does not call policy code.
- Policy selection score cannot be the only tail-retention metric.
- Paper analysis consumes recorded outputs rather than re-evaluating different checkpoints silently.
