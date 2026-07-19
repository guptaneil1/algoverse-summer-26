# System Architecture

## Dependency direction

```text
configs + frozen manifests
          ↓
data → policies → runner → checkpoint/evaluation → chain results → analysis
  \________________ provenance and token accounting ________________/
                                                        ↓
                                             generated paper artifacts
```

Dependencies point toward stable interfaces. Analysis never imports the training implementation; it reads versioned result artifacts. Evaluation never asks a policy which score should count as success.

## Components

### Data

Creates stable identifiers, hashes, partitions, provenance records, and token-accounting records. It owns truth about example origin and optimizer consumption.

### Policies

Receive a monitored state, candidate metadata, generation, remaining budget, history, and seed. They return selected example IDs/presentation counts plus a declared exact human-token count.

### Runner

Coordinates training, generation, policy allocation, checkpointing, evaluation, and manifest state. It does not contain policy logic or evaluation definitions.

### Evaluation

Evaluates a checkpoint against a frozen manifest and returns schema-valid metrics. The final test partition is evaluation-only.

### Analysis

Reads completed validated chain results, computes chain-level outcomes and uncertainty, and generates all paper-facing tables and figures.

## Independence fixtures

- Runner: toy corpus + uniform policy + null evaluator.
- Data/evaluation: toy examples + fake logits/checkpoints.
- Policies/analysis: simulated mode states + fake results.
- Paper: placeholder generated files with explicit pending markers.

## Artifact flow

Each primary chain creates:

```text
runs/<run_id>/
├── run_manifest.yaml
├── environment.txt
├── configs/
├── allocation.jsonl
├── metrics.jsonl
├── checkpoints/        # external artifact store
├── generated/          # external artifact store
├── stdout.log
├── failure.json        # only when applicable
└── chain_result.json
```

Large artifacts stay outside Git and are referenced by immutable location, SHA-256, byte size, run ID, and producing commit.

## Scientific boundaries

- No config mutation after a run starts.
- No manual correction of metrics.
- No analysis of invalid manifests.
- No test-set information in policy state.
- No result enters paper source except through generated tables/figures.
