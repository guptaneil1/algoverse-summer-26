# How This Repository Works, End to End

Written so a newcomer can follow the path from frozen data to a paper claim
without reading the source. Every step names the artifact it produces, because
the artifact — not the code — is what a reviewer can check.

## The question in one paragraph

Human-written text is finite. If you train a model, generate text with it, train
the next model partly on that text, and repeat, quality can drift. Suppose you
have a fixed lifetime budget of human-written tokens to spend across that whole
chain. **When** in the chain should you spend them, and **which** kinds of human
text should you buy? Four policies spend the same budget differently: at random,
scheduled over time only, targeted at under-covered modes only, or jointly over
both.

## The pipeline

```
frozen data + configs
        |
        v
  recursive run  ------------------> immutable run artifacts
   (runner/)                          run_manifest.json
        |                             chain_result.json
        |                             checkpoints, logs, hashes
        v
  policy allocation
   (policies/)  decides when and what to spend at each generation
        |
        v
  evaluation                          held-out human NLL
   (evaluation/)                      tail retention
        |
        v
  independent validator ------------> valid | invalid | valid_with_limitation
   (validation/)                      certificate + reason codes
        |
        v
  chain-level aggregate  ----------->  one row per chain
   (scripts/aggregate_chain_results.py)
        |
        v
  generated table/figure ----------->  paper/  (never typed by hand)
```

## Each stage

**1. Frozen data.** Five disjoint partitions: base human training, per-generation
rescue candidates, generation prompts, validation, and the final human test.
Splitting happens on a stable content hash *before* anything is used, so an
example cannot drift between partitions. The final test partition may never
influence prompting, selection, thresholds, early stopping, or hyperparameters.

**2. The recursive run.** One *chain* is one independently seeded experiment: train,
generate, mix, train again, for a fixed horizon. A chain is the experimental
unit. The generations inside it are repeated observations of the same chain, not
independent samples — which is why every interval in the paper is computed
across chains, and why three chains of ten generations is `n = 3`, not `n = 30`.

**3. Policy allocation.** At each rescue opportunity the policy sees only
policy-visible state: generation index, remaining human and total budget,
horizon remaining, allowed monitored statistics, and its seed. It never sees the
final test set. It decides how much of the human budget to spend now and which
candidates to buy. Every decision is logged.

**4. Token accounting.** Budget is counted in tokens the optimizer actually
consumed, taken from realized batches — never estimated from characters or
document counts. Padding does not count. Showing the same example twice costs
twice. Two policies are comparable only if both consumed identical lifetime
human-origin tokens and identical total tokens.

**5. Evaluation.** Held-out NLL on human text, and tail retention: the mean
clipped ratio of current to reference coverage over frozen tail modes, in
`[0, 1]`. Tail retention is deliberately computed from a frozen reference and not
from the policy's own undercoverage score, so a policy cannot score well on the
metric by gaming its own selection signal.

**6. Independent validation.** `scripts/validate_run.py` reads a completed run and
returns exactly one of `valid`, `invalid`, or `valid_with_limitation`, with
machine-readable reason codes. It only reads: it never repairs a run, rewrites a
manifest, or replaces a hash. Crucially, a *bad scientific outcome is still
valid* — poor NLL or zero tail retention is a finding. Only protocol and
integrity failures make a chain invalid.

**7. Aggregation.** `scripts/aggregate_chain_results.py` consumes schema-valid
chain results and emits one row per chain, recording every input run ID and
SHA-256 so the aggregate regenerates exactly. It rejects duplicate run IDs and
chains spanning different budgets.

**8. Generated outputs.** `scripts/generate_tables.py` turns the aggregate into
LaTeX carrying a DO-NOT-EDIT banner. With no results it emits `RESULT_PENDING`
rather than a plausible number.

## Why the process looks so heavy

Every rule exists because a specific failure would otherwise be invisible:

| Rule | The failure it prevents |
|---|---|
| Hash before splitting | The same example silently in train and test |
| Tokens from realized batches | Two arms that look matched but aren't |
| Chain is the unit | Intervals ~3x too narrow, from `n=30` |
| Validator can only read | Repairing a run until it passes |
| Numbers only from aggregates | A typo becoming a published result |
| Failures stay in the index | A quiet retry until the answer is nice |

## Current status

As of the last truthful update, no primary experiment has been run in this
repository. The scaffold, contracts, tests, and validator exist; the results do
not. `docs/STATUS.md` is authoritative and outranks the presence of code —
if code exists but STATUS says not reproduced, the answer is not reproduced.
