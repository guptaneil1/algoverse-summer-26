# Validity Certificate — `<run_id>`

One certificate per audited run. Generated from the validator's machine-readable
report; no field is filled in by judgement. Produce the report with:

```bash
python scripts/validate_run.py <run_directory> --report <destination>.json
```

Copy the values below straight from that JSON. If a field is unknown, write
`TODO(neil)` — never a plausible substitute.

---

## Run identity

| Field | Value | Source field |
|---|---|---|
| Run ID | `<run_id>` | `run_id` |
| Condition / policy | `<policy>` | manifest `policy.name` |
| Chain seed | `<seed>` | manifest `randomness.chain_seed` |
| Project commit | `<40-hex>` | manifest `git_commit` |
| Working tree clean | `<true/false>` | manifest `working_tree_clean` |
| Status | `<complete/failed/invalid>` | manifest `status` |
| External artifact location | `<path or URI>` | run index |

## Frozen inputs

| Input | Hash |
|---|---|
| `run_manifest.json` | `<input_hashes.run_manifest>` |
| `chain_result.json` | `<input_hashes.chain_result>` |
| Train manifest | `<data.train_manifest_sha256>` |
| Policy config | `<policy.config_sha256>` |
| Model / tokenizer revision | `<model.revision>` / `<model.tokenizer_revision>` |

## Budgets

| Quantity | Planned | Consumed | Equal |
|---|---|---|---|
| Lifetime human-origin optimizer tokens | `<planned>` | `<consumed>` | ☐ |
| Total optimizer tokens | `<planned>` | `<consumed>` | ☐ |
| Horizon (generations) | `<horizon>` | `<completed>` | ☐ |

## Checks performed

Copy `checks_passed` and `checks_failed` verbatim. Do not summarise.

**Passed:** `<checks_passed>`

**Failed:** `<checks_failed>`

Coverage areas, all of which must appear:

- ☐ Data separation — forbidden partition pairs disjoint, provenance complete
- ☐ Token accounting — consumed totals match the frozen budget
- ☐ Artifact integrity — every reference present, every hash matching
- ☐ Protocol compliance — seed, horizon, policy, terminal status
- ☐ Evaluator reliability — NLL finite, tail retention within `[0, 1]`

## Classification

> **`<valid | invalid | valid_with_limitation>`**

**Reason codes:** `<reason_codes>`

Each code's frozen meaning is in
`src/human_data_budget/validation/classification.py`. Reason codes are fixed
before batch audit; none may be invented at audit time.

## Limitations

`<limitations>`

Only categories predeclared in `LIMITING_CODES` may appear. If a run needs a
limitation category that does not exist yet, **stop and report** — do not add a
permissive category at the freeze.

## Auditor

| Field | Value |
|---|---|
| Auditor | TODO(neil) |
| Date | `<audited_at>` |
| Validator commit | `<validator_commit>` |
| Command | `python scripts/validate_run.py <run_directory>` |

---

### What this certificate does not say

- It does **not** say the scientific result is good. Poor NLL, weak tail
  retention, or divergence is a valid outcome when protocol and artifacts are
  intact.
- It does **not** choose the paper's conclusion.
- It does **not** authorise a rerun. Replacement follows the frozen rerun rule.

### What the validator may never do

Read and certify only. It may not repair a run, rewrite a manifest, replace a
hash, recompute a missing scientific choice, or convert an invalid chain into a
valid one. Corrections require a separately documented rerun under frozen rules.
