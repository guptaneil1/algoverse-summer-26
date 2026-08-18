# Screening run: real recursive chain, pipeline validation

**Date:** 2026-08-18
**Stage:** `screening` — **not a primary result, not a pilot**
**Config:** `configs/experiment/screening_pipeline_validation.json`
**Host:** 1× RTX 4090
**Decision:** the apparatus executes end to end. No scientific claim is made or implied.

## 1. What this establishes, and what it does not

**Establishes.** The recursive chain runs: real GPT-2 training, real top-k decoding, real
policy allocation over hash-verified human text, and real per-mode evaluation, with the
recursion carried through data across three generations. Before this run, `training/` and
`generation/` contained only `toy.py` and no `src/` file called a model at all.

**Does not establish** anything about allocation policy. Seed 9001 is deliberately outside
the frozen primary set (101, 202, 303, 404, 505); the corpus is 200 articles; the horizon is
3, not 10; the policy is `random` alone, with no comparison. `PROTOCOL.md` §5 applies: no
number here may enter `README.md`, `CLAIMS.md`, an abstract, or a presentation.

## 2. Observed

| Generation | `human_nll` | `tail_retention` |
|---:|---:|---:|
| 0 | 3.2237 | 1.0000 |
| 1 | 3.3260 | 0.9688 |
| 2 | 3.3881 | 0.9496 |

Human-origin optimizer tokens consumed: **17,222**. Total optimizer tokens: **2,435,072**.

Generation-0 reference snapshot (`reference_mode_scores.json`), checkpoint
`517f4ad7e32f3806…`:

| Mode | mean NLL | reference score |
|---|---:|---:|
| common | 3.223015 | 0.310268 |
| mid | 3.235674 | 0.309055 |
| tail | 3.127379 | 0.319757 |

## 3. Three properties worth recording

**P-001 is confirmed empirically.** `tail_retention` falls across generations — 1.0000,
0.9688, 0.9496. Generation 0 is 1.0 by construction, being the reference. Under the metric
freeze's original wording, which specified raw mean NLL, a degrading model would have
produced a ratio above 1 clipped to 1.0 and reported *perfect* retention at every generation.
The predicted failure was stated in advance of this run and did not occur after the
correction. See `FAILURE_LOG.md` F-011.

**Both metrics move in the degradation direction.** `human_nll` rises as the model retrains
on its own output. That is the same direction the positive control found, on a different
corpus and a different horizon. It is consistency of direction, not a replication.

**Budget arithmetic is deterministic across simulated and real execution.** The dry run and
this run consumed an identical 17,222 human-origin optimizer tokens under the same policy and
seed. The allocation path does not depend on whether a model was loaded.

## 4. What this unblocks

**U-004b now has its input.** `DECISIONS.md` names the evidence as "the baseline NLL
distribution on the validation partition from a real generation-0 model", which did not
exist. §2 above is that distribution. Setting `nll_threshold_candidate` is now a decision
rather than a blocked one.

`tail_retention`'s reference-snapshot contract (`docs/evaluation/tail_retention_freeze.md`
§3) is satisfiable: the artifact it requires exists and is produced automatically at
generation 0, persisted before generation 1 can overwrite it.

## 5. Defects this run surfaced

Eight, none of which any CPU test could have caught. In order: a config carrying a host
path; a relative path the precheck and the subprocess resolved differently; a stale output
directory (twice previously, in Stage A); the corpus contract not being raw text (F-012); the
evaluation corpus carrying training columns (F-013); and generation prompts drawn from the
training corpus rather than the frozen prompts partition (F-014).

F-014 is the one that matters. It surfaced as a crash only because `generate.py` requires a
`context` field the training corpus lacks. Had it tolerated the absence, the run would have
produced numbers while drawing prompts from the training set, violating `PROTOCOL.md` §3
partition disjointness silently.

## 6. What this run is not evidence for

It is not evidence that the pilot will complete, that any policy outperforms another, that
the horizon or budget figures are appropriate, or that the frozen primary configurations are
correct. Those remain `AWAITING_JULY_31_FREEZE` and were untouched.
