---
description: Audit pipeline invariants — leakage, provenance, accounting, determinism
---

Scope (file, module, run, or PR): $ARGUMENTS

Run the PROTOCOL.md §3 blocking invariants against the scope. This is an audit, not a
code review — you are looking for ways the pipeline could produce persuasive but
scientifically unusable results.

For each invariant: **PASS / FAIL / NOT COVERED**, the evidence you read, and for
anything not passing, the smallest change that fixes it.

## Data separation
Stable content hash before splitting. Disjoint: base human training, per-generation
rescue candidates, generation prompts, validation, final human test. No test example
influencing prompting, selection, thresholds, early stopping, or hyperparameters.

## Token accounting
Total optimizer-consumed tokens and human-origin optimizer-consumed tokens both
recorded, both from tokenized batches actually consumed by the optimizer. Padding
handled consistently and documented. Budget matching holds across compared arms.

## Provenance
Every training example carries: stable ID, content hash, source dataset and revision,
human/synthetic origin, recursive generation, selection policy and score, whether
selected, number of optimizer presentations.

## Reproducibility
Seeds propagate through sampling, generation, initialization, dropout, evaluation.
Resume from a frozen checkpoint preserves the predeclared conclusion. Manifests and
aggregates are immutable inputs. Tables and figures are script-generated and hashed.

## Silent-failure sweep

Beyond the checklist: name the three most likely ways this scope could be *wrong while
passing every existing test*. Be specific to the code you read — an off-by-one in
generation indexing, a padding token counted as human-origin, a seed set after the
first sample is drawn, an aggregate rebuilt from a stale cache. For each, say whether
a test exists, and if not, write the test name and assertion that would catch it.

## Verdict

Does the audited scope currently support a headline claim? Yes / No / Yes with stated
scope limits. If the honest answer is that the evidence supports something narrower
than what is written in `CLAIMS.md`, say exactly which narrower statement it supports.
