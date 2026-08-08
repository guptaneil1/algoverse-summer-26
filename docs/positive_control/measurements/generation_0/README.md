# Generation 0 measurement — fully synthetic arm

Measured on Kaggle, Tesla T4, 2026-08-05. Upstream commit feb8511479a2e2dc868e1caf3f63cb99f1fcc746, transformers 4.48.3.

Compute measurement and generation-0 baseline. NOT a positive-control result: generations 1-10 have not been run (PROTOCOL.md section 5).

The run crashed in wandb.log after every artifact was written; see FAILURE_LOG.md entry PC-2026-08-05-E. Model weights are not committed (253.7 MB) but their SHA-256 is recorded in artifact_record.json.
