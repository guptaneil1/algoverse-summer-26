# Current Project Status

**Last truthful update:** August 9, 2026
**Deadline:** August 15, 2026
**Current week:** Week 4 — independent finalization and submission (August 8–14)

> **Week 3 did not complete.** The August 7 results freeze did not happen: the
> repository contains zero tags, no `integration/week-3-aug01-aug07` branch, no
> `week-3/*` personal branches, and `results/aggregates/` holds only a README.
> Week 4 as written takes the August 7 immutable aggregate as its input, so it
> cannot start as specified. See `docs/audits/week3_execution_required.md`.
>
> **This file understates the Week 2 positive control.** The row below still reads
> *Not reproduced*, but Week 2 **was** integrated on
> `integration/week-2-jul25-jul31` (PRs #15/#16/#17), and it holds a completed
> two-arm reproduction with per-generation measurements and pinned upstream
> revisions — re-verified by recomputation in
> `docs/positive_control/week3_verification.md`. What did not happen: promotion to
> `main`, the freeze tag, and Neil's `cd73d39` (the frozen WikiText-103 manifests,
> mode definition, and tail metric). Correcting the row requires the integrator to
> promote and tag, so it is flagged here rather than edited unilaterally.
> Evidence: `docs/audits/week2_merge_gap.md`.

| Area | Owner | Status | Current evidence | Blocking issue |
|---|---|---|---|---|
| Literature and novelty | Ronit | Planned/in progress | Original claim ledger; `docs/evidence/claim_evidence_matrix.csv` | External novelty review pending |
| Paper | Ronit | Scaffold provided | `paper/` placeholders; precommitted outcome templates | Results correctly pending |
| Outside reviews | Ronit | Not conducted | Prepared records under `docs/reviews/` | Needs reviewers external to the team |
| Presentation | Ronit | Layout complete, result-independent | `docs/presentation/final_layout.md` | Slide 9 awaits a generated aggregate |
| Positive control | Khantushig | Not reproduced | Protocol only | Environment and compute benchmark; upstream commit still unpinned |
| Recursive runner | Khantushig | Contract toy runner provided | Tests/fixtures | Real training not implemented |
| Run manifest provenance | Khantushig | Implemented, not exercised on a real chain | Toy chain certifies `valid` (exit 0, 20 checks); `tests/runner/test_manifest_provenance.py`, `test_validate_toy_chain.py` | Partition vocabulary conflict between `validation/audit.py` and `data/manifest.py` is unreconciled (`FAILURE_LOG.md` F-002) |
| Data manifests | Neil | Fixture only | Toy manifests | Final licensed domain unresolved |
| Evaluation | Neil | Contract utilities provided | Unit tests incl. `tests/evaluation/test_tail_metric.py` | Real tail metric unresolved |
| Validity audit | Neil | Validator implemented and adversarially tested | `src/human_data_budget/validation/`; 41 tests; `docs/validity/week3_adversarial_audit.md` | Never applied to a primary chain; near-duplicate and ledger-recompute blind spots open |
| Policies | Aarav | Contract baselines provided | Toy simulator | Joint policy not scientifically frozen |
| Statistics | Aarav | Contract analysis provided | Fake chain results | No real primary runs |
| Chain aggregation | Aarav | Implemented | `scripts/aggregate_chain_results.py`; `tests/analysis/` | No `chain_result.json` files exist to aggregate |

## Scientific claim state

- Recursive-training motivation: literature-grounded with scope qualifiers.
- Exact novelty: unverified.
- Positive control: not reproduced in this repository.
- Pipeline correctness: scaffolded, not validated on real assets.
- Novel pilot: not run.
- Experimental results: none.
- Broad or main-conference claim: unsupported.

None of the above changed in this update. Only tooling and documentation
advanced; no experiment was run.

## Meaning of scaffolded

The repository includes interfaces, schemas, toy fixtures, tests, CI, an
independent validity auditor, chain-level aggregation, and collaboration
documentation so independent development can begin. These artifacts do not
constitute a completed training system or experimental evidence.

## Verification behind this update

Checked on August 9, 2026 against `main`, then on `shared/week3-result-independent`:
`git ls-remote` (no tags, no week-3 refs), `results/` contents, `ruff check .`
clean, `pytest -q` 199 passed, `scripts/audit_repository.py --strict-structure`
passed, toy smoke chain completes. The paper LaTeX build was **not** verified —
no TeX toolchain was available.

## Updating this file

Update only at a weekly integration freeze or a major evidence gate. Link the
relevant merged PR, tag, run manifest, or report. Never change `Not reproduced`
to `Complete` because code exists; the corresponding immutable run evidence must
exist and validate.
