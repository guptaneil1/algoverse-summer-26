# Current Project Status

**Last truthful update:** July 18, 2026
**Deadline:** August 15, 2026
**Current week:** Week 1 — independent component construction

| Area | Owner | Status | Current evidence | Blocking issue |
|---|---|---|---|---|
| Literature and novelty | Ronit | Planned/in progress | Original claim ledger | External novelty review pending |
| Paper | Ronit | Scaffold provided | `paper/` placeholders | Results correctly pending |
| Positive control | Khantushig | Not reproduced | Protocol only | Environment and compute benchmark |
| Recursive runner | Khantushig | Contract toy runner provided | Tests/fixtures | Real training not implemented |
| Data manifests | Neil | Frozen (real corpus) | `data/manifests/MANIFEST_HASHES.json`, `docs/data/week2_audit_report.md`, branch `week-2/neil-frozen-data-metrics` | None for the freeze itself; tokenizer-dependent optimizer token counts still pending the training config's tokenizer |
| Evaluation | Neil | Primary metric frozen | `docs/evaluation/tail_retention_freeze.md`, unit tests | `nll_threshold_candidate` still needs a real generation-0 baseline (`DECISIONS.md` U-004b) |
| Policies | Aarav | Contract baselines provided | Toy simulator | Joint policy not scientifically frozen |
| Statistics | Aarav | Contract analysis provided | Fake chain results | No real primary runs |

## Scientific claim state

- Recursive-training motivation: literature-grounded with scope qualifiers.
- Exact novelty: unverified.
- Positive control: not reproduced in this repository.
- Pipeline correctness: scaffolded, not validated on real assets.
- Novel pilot: not run.
- Experimental results: none.
- Broad or main-conference claim: unsupported.

## Meaning of scaffolded

The repository includes interfaces, schemas, toy fixtures, tests, CI, and collaboration documentation so independent development can begin. These artifacts do not constitute a completed training system or experimental evidence.

## Updating this file

Update only at a weekly integration freeze or a major evidence gate. Link the relevant merged PR, tag, run manifest, or report. Never change `Not reproduced` to `Complete` because code exists; the corresponding immutable run evidence must exist and validate.
