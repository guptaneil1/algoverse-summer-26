# Week 2 — Frozen Scientific Subsystems

**Dates:** July 25–31
**Base tag:** `week-1-freeze-2026-07-24`
**Integration branch:** `integration/week-2-jul25-jul31`
**Freeze tag:** `week-2-freeze-2026-07-31`

## Shared outcome

The positive control, data/evaluation definition, method/configs, and complete result-free paper are individually finished before primary treatment outcomes.

## Ronit — `week-2/ronit-paper-novelty`

Tasks:

- Finish all result-independent paper sections.
- Complete backward/forward citation review and obtain one hostile external novelty review.
- Update `CLAIMS.md` and build a claim-to-evidence matrix for planned abstract sentences.
- Write method/experiment text only from the frozen Week 1 interface and mark unresolved decisions.
- Create correct placeholder tables/figure captions and outcome-contingent language for win/tie/loss/uncertain results.
- Create five- and ten-minute presentation outlines.

Complete deliverable: fully compiling manuscript requiring only generated results and their interpretation.

No current-week dependency: uses Week 1 interfaces and explicit placeholders.

## Khantushig — `week-2/khantushig-positive-control`

Tasks:

- Run official fully synthetic and human-mixed positive-control arms through the frozen horizon.
- Save configs, manifests, checkpoints, generated hashes, metrics, logs, environment, and actual compute.
- Implement checkpoint-resume equivalence and exact reproduction command.
- Compare expected versus observed ordering/endpoint against the predeclared criterion.
- Produce either a clean positive-control report or a complete reproduction-failure report.
- Prepare the real pilot runner adapter against frozen Week 1 contracts.

Complete deliverable: self-contained positive-control reproduction package or truthful failure package.

No current-week dependency: uses official upstream assets and runner-owned adapters.

## Neil — `week-2/neil-frozen-data-metrics`

Tasks:

- Select the final licensed domain from Week 1 audit.
- Freeze dataset revision, preprocessing, stable IDs, hashes, and five disjoint manifests.
- Write data card, license record, split statistics, mode summary, and overlap report.
- Freeze NLL implementation and one primary tail-retention definition after reliability/independence audit.
- Test token accounting under padding, repetition, batching, gradient accumulation, and resume fixtures.
- Produce final data/evaluation audit report.

Complete deliverable: immutable manifest bundle plus frozen evaluator and validation report.

No current-week dependency: works from dataset assets and saved/fake logits.

## Aarav — `week-2/aarav-method-preregistration`

Tasks:

- Finalize mathematical definitions, mode representation, under-coverage score, and joint allocation rule.
- Freeze all four policy configs and demonstrate exact lifetime/total budget matching on fixtures.
- Freeze primary horizon, budget, seed order, exclusion rules, primary contrast, and meaningful-effect threshold.
- Complete draft preregistration before viewing primary outcomes.
- Generate final-format tables and figures from fake schema-valid results.
- Document every hyperparameter and selection rule.

Complete deliverable: frozen method/baseline/analysis package and preregistration.

No current-week dependency: uses simulator and fake result artifacts.

## Friday definition of done

- Positive control is reproduced or honestly failed with evidence.
- Real data manifests and evaluator are frozen.
- Method and analysis configs are frozen.
- Result-free manuscript is complete.
- Interface integration tests pass.
- No primary outcome has influenced the protocol.
