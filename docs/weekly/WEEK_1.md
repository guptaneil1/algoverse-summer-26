# Week 1 — Independent Component Construction

**Dates:** July 18–24
**Integration branch:** `integration/week-1-jul18-jul24`
**Freeze tag:** `week-1-freeze-2026-07-24`

## Shared outcome

Four standalone subsystems work against fixtures. No member requires code, data, results, or approval from another Week 1 branch.

## Ronit — `week-1/ronit-research-context`

Tasks:

- Review recursive collapse, fresh mixing, accumulation, scheduling, active/surprise/semantic sampling, tail preservation, importance resampling, and monitoring bias.
- Record at least 15 directly relevant and 10 adjacent primary sources.
- Complete `docs/evidence/closest_work.csv` and `sources.yaml`.
- Identify the five strongest novelty threats and write the strongest counterargument.
- Freeze a provisional one-paragraph contribution and allowed/forbidden wording.
- Build compiling paper sections for introduction, related work, problem definition, and limitations.
- Use `RESULT_PENDING` inputs rather than invented values.

Complete deliverable: reviewable research packet and a compiling 40–50% result-free manuscript.

Independent inputs: literature sources and paper placeholders only.

## Khantushig — `week-1/khantushig-recursive-runner`

Tasks:

- Pin upstream positive-control commit and initial Python/framework/model/tokenizer identifiers.
- Implement toy train/generate/allocate/evaluate chain orchestration.
- Implement atomic generation checkpoint, resume, manifest, seed recording, and structured failure state.
- Use toy corpus, uniform policy, and null evaluator.
- Complete two recursive CPU generations.
- Benchmark one real positive-control generation by July 21 and forecast required accelerator hours/storage.
- Test fresh run, resume, same-seed toy determinism, and manifest creation.

Complete deliverable: standalone toy runner plus compute benchmark/report.

Independent inputs: runner-owned toy corpus, policy, and evaluator.

## Neil — `week-1/neil-data-evaluation`

Tasks:

- Audit at least two licensed candidate domains and recommend primary/fallback choices.
- Implement stable IDs, SHA-256 content hashes, partitioning, provenance, and token-presentation accounting.
- Support base train, rescue candidate, prompt, validation, and final-test partitions.
- Write exact and near-duplicate overlap tests, including deliberately corrupted fixtures.
- Implement NLL from fake logits and two candidate tail-retention metrics.
- Test padding, repeated examples, incomplete provenance, and forbidden overlap.

Complete deliverable: standalone data validator and fixture-based evaluation package.

Independent inputs: Neil-owned toy examples, fake logits, and corrupt manifests.

## Aarav — `week-1/aarav-policies-analysis`

Tasks:

- Formalize generation, mode, monitored state, remaining budget, allocation, and budget constraint.
- Implement random, schedule-only, selection-only, and provisional joint policies through one interface.
- Build a simulator with different mode degradation rates, rescue response, and monitoring omission.
- Test exact budget equality and deterministic seed behavior.
- Implement chain-level regret AUC, paired differences, interval calculation, seed-pair validation, and fake-result tables.
- Clearly label simulation output as an implementation test, not scientific evidence.

Complete deliverable: standalone policy/simulation/analysis package with generated fake-result tables.

Independent inputs: Aarav-owned simulated states and fake chain results.

## Friday definition of done

- Four draft PR checklists are complete.
- Each subsystem runs without another member's branch.
- Unit tests pass.
- Contract schemas validate.
- Paper compiles with pending markers.
- Missing work keeps a mock rather than blocking integration.
