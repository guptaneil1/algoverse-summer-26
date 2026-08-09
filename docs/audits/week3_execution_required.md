# Week 3 — What Still Requires Execution

Companion to the result-independent backfill. Everything in this file needs
somebody to **run something, decide something, or ask a real person something**.
None of it can be written from a desk, and writing it anyway would fabricate
evidence.

Audited against `main` on 2026-08-09. The Week 3 packet prescribes 53 artifacts;
22 existed, and the result-independent backfill added the rest of what can be
built without runs. What remains is listed here.

---

## 0. Process prerequisites — blocking everything below

The packet's start gate is *"do not begin a primary Week 3 chain until accepted
Week 2 work is merged, main points to the tested Week 2 snapshot, and tag
`week-2-freeze-2026-07-31` exists."* None of that exists.

| Required | State | Who |
|---|---|---|
| Tag `week-2-freeze-2026-07-31` | **Absent** — the repository has zero tags | Integrator |
| Branch `integration/week-3-aug01-aug07` | **Absent** | Integrator |
| Four `week-3/*` personal branches | **Absent** | Each owner |
| Tag `week-3-results-freeze-2026-08-07` | **Absent** | Integrator |

**Do first:** decide, as a team, whether Week 2 actually completed. If it did,
tag the commit that represents it and say which commit that is. If it did not,
say so in `docs/STATUS.md` — which currently reads *"Last truthful update: July
18 / Current week: Week 1"* and is three weeks stale.

Until a July 31 freeze exists there is no frozen design to execute, and every
config below has no legitimate source for its scientific values.

---

## 1. Khantushig — reference runs

### 1.1 Frozen configs — blocked on the freeze, not on effort

`configs/experiment/primary_no_rescue.json`, `configs/experiment/primary_fresh_random.json`

Deliberately **not** created. Every field is a frozen scientific choice —
model, tokenizer revision, data manifests, horizon, ordered seed list, lifetime
human-token budget, total-token budget — and the packet says those come from the
July 31 freeze. Inventing them would look identical to a real config while
committing the project to numbers nobody chose.

When the freeze exists, each config needs:

```jsonc
{
  "experiment_id": "primary_no_rescue",
  "model": {"identifier": "...", "revision": "...", "tokenizer_revision": "..."},
  "data": {"train_manifest": "...", "train_manifest_sha256": "..."},
  "policy": {"name": "no_rescue", "config": "configs/policy/....json"},
  "horizon": 0,
  "budget": {"lifetime_human_optimizer_tokens": 0, "total_optimizer_tokens": 0},
  "seeds": [],
  "artifact_destination": "..."
}
```

Fill every value from the freeze. No hidden defaults — `scripts/run_chain.sh`
must fail loudly on a missing key rather than substituting one.

Then write `tests/runner/test_reference_configs.py` asserting: both configs
parse, every key above is present, budgets are positive integers, seeds are an
ordered list of the frozen length, and the two arms declare **identical**
`lifetime_human_optimizer_tokens` and `total_optimizer_tokens`. That last
assertion is the budget-matching guarantee at config level.

### 1.2 Fix the manifest before spending compute — found by running the validator

Running the finished validator against the toy smoke chain returns **`invalid`**
with `SEPARATION_MISSING_PROVENANCE`: `run_manifest.json` carries no
`data.partitions` block, so per-example provenance and partition disjointness
cannot be verified. Fourteen other checks passed.

A real chain will fail the same way. Add to the manifest, per partition
(`base_human_train`, `rescue_candidates`, `generation_prompts`, `validation`,
`final_human_test`), one entry per example with `stable_id`, `content_hash`,
`source_dataset`, and `origin`. The schema already allows it
(`additionalProperties: true`); no contract change is required.

Do this **before** launching an expensive run. A completed chain that cannot be
certified is wasted accelerator time, and the frozen rules do not permit
back-filling provenance after the fact.

### 1.3 The runs themselves

```bash
python scripts/validate_run.py <run_directory>   # after each chain
bash scripts/run_chain.sh configs/experiment/primary_no_rescue.json
bash scripts/run_chain.sh configs/experiment/primary_fresh_random.json
```

Before launching anything expensive: confirm the code commit is frozen and the
tree clean, run the schema/leakage/budget preflights, create the manifest with
status `planned`, and record expected accelerator hours and artifact
destination. Never edit an active config; never change a setting after seeing an
intermediate metric.

### 1.4 Records that follow from the runs

- `docs/runs/week3_reference_run_index.md` — one row per chain: run ID,
  condition, seed, commit, config and manifest hashes, external artifact
  location, status, validity classification, failure reference. **Failed and
  incomplete chains stay in the index.**
- `docs/positive_control/week3_verification.md` — the frozen expected
  comparison, the exact command, observed status, deviations, artifact hashes,
  and the scientific consequence. A mismatch is recorded, never tuned away.
  Note: `docs/STATUS.md` still says the positive control is *not reproduced*, and
  the upstream commit to reproduce is an unfilled TODO — pin it first.
- `docs/runner/week3_integrity_report.md` — preflight results,
  determinism/resume evidence, checkpoint behaviour, manifest history, hash
  checks, known nondeterminism, unresolved limitations.
- `COMPUTE.md` — generation, training, and evaluation time recorded
  **separately**, plus accelerator-hours, peak memory, storage, aborted-run cost.
- `FAILURE_LOG.md` — every failure with its class, log paths, rerun permission,
  replacement-seed rule, and consequence. Never erase an earlier entry.

---

## 2. Aarav — policy runs

### 2.1 `configs/experiment/primary_pilot.json`

Same reasoning as 1.1: frozen horizon, budget, total-token match, ordered seeds,
outcomes, contrast, and exclusions all come from the July 31 freeze.

### 2.2 The three policy chains

Execute `schedule_only`, `selection_only`, and `joint` from the frozen configs
and ordered seeds. Before each chain, run the exact lifetime-human-token and
total-optimizer-token equality preflight against the eligible comparator set, and
confirm the final-test partition is absent from monitoring, scoring, selection,
thresholds, early stopping, and hyperparameters.

Every generation must preserve pre-action state, scores and decisions,
post-action ledger, and outcome references — see packet page 18 for the exact
field groups.

### 2.3 Records and the provisional aggregate

- `docs/policy/week3_policy_run_index.md` — as 1.3, per policy chain.
- `docs/policy/week3_policy_behavior_report.md` — generation-wise spending,
  monitored state, mode scores, selected candidates and modes, allocation
  history, fallback and tie events, deviations. Record surprising allocations;
  **do not adjust a hyperparameter after seeing them.**
- `results/aggregates/provisional_week3.json` — now generatable, because
  `scripts/aggregate_chain_results.py` exists:

```bash
python scripts/aggregate_chain_results.py runs/*/chain_result.json \
    --output results/aggregates/provisional_week3.json --label provisional
```

  It refuses duplicate run IDs, chains spanning different budgets, and
  schema-invalid inputs, and records every input hash. It cannot be run today
  because no `chain_result.json` exists.

- `results/figures/` — generated only, each with its input aggregate hash and
  generation command. Paper-facing figures wait for the August 7 immutable
  aggregate.

### 2.4 Monitoring-bias stress test

Only after the primary jobs are secure, under a separately labelled config and
output. Secondary or exploratory unless the preregistration says otherwise.

---

## 3. Neil — the Friday batch audit

The validator itself is **done** and passes 41 adversarial tests
(`docs/validity/week3_adversarial_audit.md`). What remains needs real artifacts.

### 3.1 `results/validity/week3_classifications.csv`

One row per frozen chain. The aggregator already reads this format:

```csv
run_id,condition,chain_seed,manifest_sha256,chain_result_sha256,classification,reason_codes,limitation,certificate_path
```

Produce it by running the finished validator over every completed, failed, and
incomplete package:

```bash
python scripts/validate_run.py <run_directory> --report results/validity/<run_id>.json
```

Exit codes: 0 valid, 1 valid_with_limitation, 2 invalid. Run the **same
validator version** against every package and preserve stdout/stderr.

### 3.2 One certificate per run

Fill `docs/validity/validity_certificate_template.md` from each JSON report.
Failed and incomplete chains still get a certificate or an explicit
missing-artifact entry.

### 3.3 `docs/evaluation/week3_data_evaluation_appendix.md`

Needs the final data identity, which is unresolved — `docs/STATUS.md` records the
licensed domain as undecided and manifests as fixture-only. Once the data is
frozen, document partitions, overlap rules, token accounting, NLL definition,
the primary tail metric, reliability evidence, and known limitations.

### 3.4 Close the two severe blind spots

From the adversarial audit, both let an invalid chain pass as valid:

1. **Near-duplicate overlap is not detected.** `overlap.py` has the logic; the
   auditor calls only exact-hash comparison. Wire it in and add a fixture with a
   paraphrased leak.
2. **Token ledgers are compared, not recomputed.** An internally consistent but
   wrong ledger passes. Recompute from realized batches where the artifacts allow.

---

## 4. Ronit — the two outside reviews

`docs/reviews/week3_clarity_review.md` and `week3_significance_review.md` exist as
prepared records, both marked **NOT CONDUCTED**.

These need actual people who are not on the team. A teammate explaining the paper
to another teammate is not a clarity review, and the `novelty-adversary` subagent
can rehearse the significance argument but cannot be the reviewer of record.

Reviewers need: the exact commit, a compiled PDF, `CLAIMS.md`, and
`docs/evidence/closest_work.csv`. For the significance review, press hardest on
logged Threats 3 and 4 (detection-based resampling; dynamic mixture
optimization) — the team's own analysis calls those the strongest.

Record the strongest criticism verbatim, the exact wording changed, and every
unresolved concern. Do not summarise a negative review as approval.

### Also blocked: the paper build

The packet's check sequence includes `pdflatex`/`bibtex`. That was not run here —
no LaTeX toolchain is installed on this machine, so whether `paper/main.tex`
compiles is **unverified**.

```bash
cd paper
pdflatex -interaction=nonstopmode main.tex && bibtex main
pdflatex -interaction=nonstopmode main.tex && pdflatex -interaction=nonstopmode main.tex
```

---

## 5. The freeze itself

Cannot happen until chains exist. When they do, in order:

1. Stop adding primary seeds at the declared time.
2. Hash every completed artifact; freeze the artifact index.
3. Run Neil's validator against every available package.
4. Preserve all failed and incomplete chains.
5. Apply only frozen exclusion and replacement rules.
6. Generate and hash one immutable chain-level aggregate from eligible classified
   chains (`--label frozen`).
7. Label every later run, repair, sensitivity check, or added seed exploratory.
8. Tag `week-3-results-freeze-2026-08-07` on the tested integrated snapshot.

---

## 6. The honest position today

It is 2026-08-09. The Week 3 deadline (August 7) has passed; Week 4 runs
August 8–14, and every Week 4 task takes the August 7 frozen aggregate as input.
That aggregate does not exist, so Week 4 as written cannot start.

Two defensible paths, and the team should pick one deliberately rather than
drift:

**A. Compress and execute.** Pin the freeze, run a reduced set of chains at a
smaller horizon or fewer seeds, classify, aggregate, and write results against
whatever comes out. Requires deciding today what to cut. The preregistered
minimum chain count governs whether the result is interpretable at all.

**B. Submit the scaffold honestly.** Report the design, the validated pipeline,
the validator with its measured adversarial coverage, and the positive-control
status. Use template 9 in `paper/outcome_contingent_language.md`: *"No primary
chain completed before the results freeze."* C-002 and C-003 stay untested.

Path B is a legitimate outcome. What is not legitimate is presenting scaffold as
result, or backfilling records for runs that never happened. Nothing in this
backfill does either.
