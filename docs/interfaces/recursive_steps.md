# Interface proposal — real recursive train and generate steps

**Status: PROPOSAL. Nothing here is implemented.** `src/human_data_budget/training/`,
`generation/`, and `runner/` are `@Khantushig` per `.github/CODEOWNERS`. This document
exists so the design can be agreed or redirected before code is written against that module,
as `CONTRIBUTING.md` and `CLAUDE.md` require.

**What it closes:** the Week 2 deliverable *"Prepare the real pilot runner adapter against
frozen Week 1 contracts"* (`docs/weekly/WEEK_2.md`). That item was never built, and Week 3's
*"Operate no-rescue and fresh-random conditions"* depends on it.

**What it does not do:** decide U-001 through U-006. Those stay open and stay with their
owners. This is the executable path they will eventually be executed *through*.

## 1. The gap, stated precisely

Verified 2026-08-17 across all 25 remote branches: no file under `src/` contains
`from_pretrained` or `AutoModelFor`. `training/` and `generation/` each contain only
`toy.py`.

Two distinct problems, and the second is easy to miss:

**(a) The steps are simulated.** `toy_train_step` returns a `weight_signature` from
`random.Random(seed)`. `toy_generate_step` returns strings sampled from an eight-word
vocabulary. `NullEvaluator` scores a fixture corpus.

**(b) The recursion is not wired.** In `runner/chain.py` the two calls are

```python
toy_train_step(train_state, policy_seed)      # return value discarded
toy_generate_step(generate_state, policy_seed) # return value discarded
```

Neither result is bound. Generation *g*'s synthetic output never reaches generation *g+1*'s
training input. The loop exercises checkpoint, resume, manifest, and allocation ordering —
which it was built to do and does correctly — but no data flows between generations. Wiring
that flow is part of this work, not a consequence of it.

## 2. Proposed interfaces

Mirror the toy signatures so real and toy are swappable behind one call site, keeping every
existing test valid.

```python
# training/real.py
def real_train_step(state: TrainState, seed: int) -> TrainResult: ...

# generation/real.py
def real_generate_step(state: GenerateState, seed: int) -> GenerateResult: ...
```

`TrainState` carries: base model identifier and pinned revision, the training corpus for this
generation (previous synthetic output plus policy-allocated human examples), block size,
epochs, dtype, and output directory. `TrainResult` carries: checkpoint path, checkpoint
SHA-256, and **`optimizer_consumed_tokens` read from the batches actually consumed**, never
estimated — `PROTOCOL.md` §3.

`GenerateState` carries: checkpoint path from this generation's `TrainResult`, decoding
configuration, prompt source, and sample count. `GenerateResult` carries: corpus path, corpus
SHA-256, and example count.

Selection between toy and real belongs in config, not in an import, so `configs/training/`
and `configs/generation/` gain a `mode: toy | real` key.

## 3. Reuse the validated path

Do not write a training loop. `runner/positive_control_adapter.py` already drives real GPT-2
training and generation by invoking upstream's `train.py` and `generate.py` one generation at
a time, and on 2026-08-17 it reproduced published values with all hashes verified. Its
argument lists are pinned by test against upstream `main.py`.

Stage B is the same recursion with one addition: a policy chooses which human examples join
each generation's training corpus. The proposal is therefore to factor the subprocess-driving
core out of `positive_control_adapter.py` and have both callers use it.

Consequence worth stating: this inherits upstream's regime, in which every generation
fine-tunes the pretrained base rather than continuing from the previous checkpoint
(`docs/evidence/stage_b_freeze_evidence.md`, U-001). If U-001 resolves the other way, the
train step needs a `resume_from` path and the positive control no longer covers Stage B's
training path.

## 4. Evaluator

`NullEvaluator` is replaced by a real evaluator over the frozen held-out human partition.
Both metrics already exist: `evaluation/nll.py` and `evaluation/tail.py`. What is missing is
the wiring and one number — `nll_threshold_candidate` (U-004b), which needs a validation-set
NLL distribution from a real generation-0 model. That is roughly fifty seconds of GPU.

## 5. What stays toy

`toy.py` stays and stays tested. It is the only path that runs on CPU in CI, it backs
`make smoke`, and the determinism and resume tests depend on it. Real mode must be
opt-in, never the default in tests.

## 6. Test plan

- Same seed, same config, real mode twice on one host, bitwise-identical
  `optimizer_consumed_tokens` and identical metric sequence.
- Resume at generation *k* reaches the same final result as an uninterrupted run.
- Token accounting from a known-size corpus equals `train_samples` x `block_size`, matching
  the method used for the positive control.
- Budget matching: two policies over the same seed set consume identical lifetime
  human-origin and total optimizer tokens.
- Generation *g*'s corpus hash appears as generation *g+1*'s training input hash — the
  regression test for problem (b) above.
- Every existing toy test continues to pass unchanged.

## 7. Cost

At the measured positive-control rate on one RTX 4090, roughly 23 accelerator-hours for a
30-chain pilot at WikiText-2 token scale, about $17. At full WikiText-103 it is roughly 40x
that. See `docs/evidence/stage_b_freeze_evidence.md`; the subsample choice dominates.

## 8. Open questions for the owner

1. Factor the driver out of `positive_control_adapter.py`, or write a parallel one? Factoring
   couples Stage B to a validated path but touches code with committed reproduction evidence.
2. `mode: toy | real` in config, or separate entry points?
3. Does the real evaluator run every generation, or only at frozen checkpoints? Every
   generation is simpler; frozen checkpoints are cheaper.
4. Who runs U-004b's generation-0 job, and does its output land in `docs/evaluation/`?
