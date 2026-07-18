# Reproducibility Standard

Every reported result must link:

1. frozen protocol and preregistration version;
2. full Git commit and clean/dirty state;
3. model/tokenizer identifiers and revisions;
4. dataset manifest paths and SHA-256 hashes;
5. full configs and hashes;
6. all seeds;
7. hardware/software environment;
8. raw chain artifacts;
9. objective validity classification;
10. exact analysis command;
11. generated table/figure hash;
12. failure and limitation records.

## Determinism

Seeds must propagate through data sampling, generation, model initialization, dropout, training, and evaluation. A deterministic smoke condition must reproduce exactly. GPU primary runs may be conclusion-reproducible rather than byte-identical when nondeterministic kernels are documented.

## Data

Record stable IDs, content hashes, dataset/revision/license, partition, origin, generation, policy score/selection, and optimizer presentations. Hash and near-duplicate checks cover all forbidden partition pairs.

## Budgets

Count tokenized non-padding items in optimizer-consumed batches. Validate human-origin tokens and total optimizer tokens independently. Estimated document or character counts are not accepted for the primary comparison.

## Results

Analysis consumes immutable schema-valid `chain_result.json` files only. Generations remain repeated observations inside chains. Tables and figures are regenerated through scripts; paper source contains no hand-entered experimental values.

## Environment

Use a locked Python environment and record OS, Python, CUDA, GPU, PyTorch, Transformers, model/tokenizer revision, and upstream code commit. Secrets stay in local environment variables or GitHub Secrets and never enter manifests.

## Clean-room check

Before submission, an uninvolved teammate follows the README from a clean checkout and regenerates tests plus the headline table. Differences are recorded rather than manually reconciled.
