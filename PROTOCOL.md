# Verification and Experimental Protocol

> **Status: active verification protocol. The novel-study portion remains a draft until the positive control passes.**

## 1. Purpose

The protocol prevents an invalid recursive-training pipeline from producing persuasive-looking but scientifically unusable results.

## 2. Stage A: published positive control

### Primary source

- Paper: George Drayson, Emine Yilmaz, and Vasileios Lampos, “Machine-generated text detection prevents language model collapse,” EMNLP 2025.
- Official code: `https://github.com/GeorgeDrayson/model_collapse`
- Exact upstream commit: `feb8511479a2e2dc868e1caf3f63cb99f1fcc746` (`Update README.md to reflect EMNLP 2025 acceptance and correct citation format`, authored 2026-03-13, resolved as `HEAD` of the default branch on 2026-08-03 and pinned here).
- Published record: <https://aclanthology.org/2025.emnlp-main.1506/>.

Every value in this section was read out of that commit's working tree. Each row below names the
upstream file it came from; nothing here is inferred from the paper text alone.

### Initial environment identifiers

- Python (this scaffold's dev environment): `3.12.1`; `pyproject.toml` requires `>=3.10`.
- Upstream dependency declaration (`requirements.txt` at the pinned commit): `datasets>=2.14.0`,
  `evaluate`, `accelerate>=0.12.0`, `torch>=1.3`, `sentencepiece!=0.1.92`, `protobuf`,
  `scikit-learn`, `wandb`, `tqdm`, `hydra-core`, `matplotlib`, `nltk`, `textstat`, `mauve-text`,
  `seaborn`.
- `transformers` is installed from git source, not from a pinned release
  (upstream `README.md`, "Installation" step 2: `pip install git+https://github.com/huggingface/transformers`).
  Upstream therefore pins no `transformers` version. The executing environment **must** record the
  resolved `transformers` version at run time; that resolved value, not this paragraph, is the frozen
  identifier for the run.

  **Resolved 2026-08-05.** Following that instruction now installs `transformers 5.15.0.dev0`, under
  which upstream cannot run: `src/train.py:48` imports `send_example_telemetry`, removed in v5, and
  `src/train.py:53` declares `check_min_version("4.48.0.dev0")`. Upstream's own minimum-version call
  is the strongest statement it makes about which major version it expects, so the frozen resolution
  is `transformers==4.48.3`, with `datasets==3.2.0` and `accelerate==1.2.1` matched to the same
  release window and `torch` taken from the host. This resolves an ambiguity upstream left open
  rather than departing from a pin it made; the observed failure is logged as `PC-2026-08-05-D` in
  `FAILURE_LOG.md`, and the resolved versions must appear in the report beside the model and dataset
  revisions.
- Model and tokenizer revisions are likewise unpinned upstream (`config/model/gpt2.yaml` names
  `openai-community/gpt2` with no `revision`). The configs in `configs/experiment/` carry the
  sentinel `resolve_at_runtime`, and
  `human_data_budget.runner.positive_control_adapter` refuses to move a manifest out of `planned`
  while that sentinel is unresolved. Hugging Face is unreachable from the authoring environment
  (network policy denies `huggingface.co`), so the revisions must be resolved and recorded on the
  accelerator host.

### Reproduction conditions

Frozen 2026-08-03, before either arm was executed. The "source" column is the file at the pinned
upstream commit that supplies the value.

| Setting | Frozen value | Source |
|---|---|---|
| Model | `openai-community/gpt2` (124M-class) | `config/model/gpt2.yaml` |
| Dataset | WikiText-2 raw v1, prepared by `python src/load_data.py` into `./data/wikitext2/{train,test}.json` — see the reproducibility note below | `config/dataset/wikitext2.yaml`, `src/load_data.py` |
| Decoding | top-k: `temperature=1.0`, `top_p=1.0`, `top_k=50`, `beam_search=false` | `config/decoding/top_k.yaml` |
| Training | `block_size=512`, `loss_on_last_n_tokens=256`, `batch_size=8`, `num_train_epochs=1`, `save_steps=2000` | `config/train/default.yaml` |
| Seed | `42` | `config/config.yaml` |
| Recursive horizon | `num_iterations=10`, i.e. an initial generation 0 plus iterations 1–10 = **11 trained models, generation indices 0–10** | `config/config.yaml`, `main.py` loop `range(1, num_iterations+1)` |
| Detector | `GeorgeDrayson/modernbert-ai-detection`, `temperature=1.359828233718872`, `ai_confidence_threshold=0.8674598932266235` | `config/detector/modernbert_mage.yaml` |
| Precision / device | `torch_dtype=bfloat16`, `low_cpu_mem_usage=true`, `cuda_device=0` | `config/config.yaml` |

**Dataset reproducibility, stated because it constrains what the recorded hash means.**
`src/load_data.py:150` does not merely tokenize: it runs the ModernBERT detector over the
training split and saves the *classified* result as `train.json`. The prepared dataset is
therefore a function of the framework stack and of GPU inference, not of WikiText-2 alone.

Two consequences, both verified on 2026-08-06 (`FAILURE_LOG.md` `PC-2026-08-06-F`):

- **Within one session it is deterministic.** Re-running `load_data.py` a second time in
  the same session, on the same allocated GPU under the frozen `transformers 4.48.3` /
  `datasets 3.2.0`, reproduced a byte-identical file. That is what the pinned
  `train_manifest_sha256` checks: that both arms of a chain were prepared from the same
  bytes, which is the property the comparison actually depends on.
- **Across stacks it is not.** The same command under `transformers 5.15.0.dev0` /
  `datasets 5.0.0` produced a different file.
- **Across sessions it is not established either.** The verification above was performed
  within a single session and does not license the stronger claim that a fixed version set
  reproduces the same bytes on a freshly allocated host; detector inference makes the file
  a function of the physical accelerator as well as the software. An earlier draft of this
  section claimed stack-level determinism and overstated the evidence; it is corrected
  here. A reproduction attempt on other hardware, other framework versions, or a later
  session must re-derive and re-pin the hash and say so, rather than assume the recorded
  value transfers. Every generation of both arms must be prepared under one stack, and any
  chain continued in a later session must carry its prepared `train.json` forward rather
  than regenerate it.

**Recorded deviation from this document's own earlier draft.** Sections above previously stated a
horizon of "generations 0 through 9". Upstream's default `num_iterations: 10` produces generation
indices 0–10 inclusive. The upstream default is authoritative and the horizon is frozen at **11
generations (indices 0–10)**. The earlier text was a drafting estimate made before the upstream
commit was pinned; it never governed an executed run.

**Recorded deviation from the upstream default configuration.** `config/config.yaml` defaults to
`data_selection: importance_sampling`, which is the paper's *proposed mitigation*, not the collapse
baseline. Both positive-control arms therefore override it to
`data_selection=no-selection` (`config/data_selection/no-selection.yaml`: `strategy: None`,
`upsample_factor: 1.0`, `bias_factor: 1.0`, `max_repeats: 1`). This is a deliberate, pre-registered
deviation: a positive control must reproduce the *uncorrected* degradation the paper reports, and
leaving importance sampling on would confound the arm contrast with the paper's intervention.

### Recorded deviation in execution mechanics

Upstream's `main.py` runs an arm as one uninterruptible process: it trains generation 0,
then loops through every remaining generation with no resume. On a session-capped host an
interrupted arm is lost entirely. `scripts/run_positive_control_arm.py` issues the
identical `src/train.py` and `src/generate.py` commands, in the same order with the same
arguments, one generation at a time, recording each completion. The commands are pinned
against upstream by `tests/runner/test_positive_control_driver.py`.

This changes the process boundary, not the computation. Two further options build on it,
each justified by a property read from the upstream source rather than assumed:

- **Shared generation 0** (default on). `main.py`'s initial training command passes
  neither `--human_data_alpha` nor `--data_selection_strategy`, and `--ai_beta` is `1.0`
  in both arms, so the two arms would compute an identical generation-0 model twice.
  It is computed once and shared. Beyond halving that cost, this *removes* a source of
  nondeterminism: both arms then start from a bit-identical baseline rather than two
  independently trained models that ought to match but need not, given nondeterministic
  CUDA kernels. Disable with `--no-shared-generation-zero` to recover upstream's exact
  process structure; the arm contrast is unaffected either way.
- **Model pruning** (default off; `--prune-models`). Every generation retrains from base
  GPT-2 — `main.py` passes `--model_name_or_path model_name` at every iteration, never the
  previous checkpoint — so generation *i-1*'s weights are needed only to decode generation
  *i* and are scientifically spent once generation *i*'s `data.json` exists. With pruning
  on, each superseded model directory is hashed, recorded in a sidecar, then deleted; peak
  storage falls from roughly 11 GB to roughly 1.5 GB.

  **Limitation, stated because it is real:** a pruned model's SHA-256 is preserved but its
  bytes are not, so that hash can never be re-verified. `pruned_artifacts()` lists every
  such artifact with its reason, and any report produced from a pruned run must disclose
  which artifacts are no longer re-checkable. Metrics and generated data are never pruned.
- **`wandb` suppression.** Upstream requests `wandb_disabled=true`, but `main.py:25` guards
  initialisation with `if not bool(str(cfg.wandb_disabled))`, and `bool("False")` is `True`,
  so `wandb.init` is never called — while `train.py:683` calls `wandb.log` unconditionally,
  killing the process after every scientific artifact has been written (`PC-2026-08-05-E`).
  Upstream source is never edited. wandb logging touches no scientific computation; it
  reports metrics to a dashboard.

  **What the executed run used:** the driver committed on this branch sets `WANDB_DISABLED`
  and `WANDB_MODE=disabled` in the subprocess environment and nothing more, and all 22
  generation-arm pairs completed and were recorded under it. **This contradicts
  `PC-2026-08-05-E`, which states that environment variables do not prevent the crash
  because wandb's pre-init stub raises regardless of mode.** Both observations are recorded;
  neither is deleted to make the other consistent. The discrepancy is unresolved and is
  flagged in `docs/positive_control/report.md` §6. It has no bearing on any frozen quantity.

  A `sitecustomize.py` shim performing the disabled-mode `wandb.init` was written in
  response to `PC-2026-08-05-E` and is **not** part of the executed driver.

- **`--self_bleu_n_sample 50`** instead of upstream's default of 1000. The default drives an
  O(n²) NLTK BLEU sweep of roughly a million pair comparisons per generation, several times
  the cost of the decoding it describes. Self-BLEU is computed *after* `data.json` is
  written and is read only by a `wandb.log` (disabled) and a diagnostic file, so the cap
  cannot affect any generation's training data or any frozen metric. Applied identically to
  both arms.

### The two arms

The paper describes the fully synthetic mixture as `(alpha=0, beta=1, gamma=0)` and a human-mixed
condition as `(alpha=1, beta=1, gamma=0)`. The executable upstream configuration is authoritative if
labels differ. At the pinned commit those parameters are `human_data_alpha` and `ai_beta` in
`config/config.yaml`, and their executable meaning is:

- `ai_beta` (`src/train.py:453`) — when below `1.0`, the synthetic training set is truncated to
  `round(len * ai_beta)` examples. At `1.0` the full synthetic set is used.
- `human_data_alpha` (`src/train.py:506`, `src/train.py:548`) — when `0.0`, no human data is mixed
  into recursive training at all. When above `0.0`, `round(human_data_size * human_data_alpha)`
  human examples are appended to that generation's training set.

| Arm | Frozen overrides | Executable meaning |
|---|---|---|
| Fully synthetic | `human_data_alpha=0.0 ai_beta=1.0` | Generations 1–10 train on synthetic text only. Generation 0 trains on human WikiText-2 in both arms. |
| Human mixed | `human_data_alpha=1.0 ai_beta=1.0` | Generations 1–10 train on the full synthetic set plus the full human training set appended. |

`accumulate_ai_data` is `false` in both arms (`config/config.yaml`): each generation trains on its
own synthetic data, not on the union of all prior generations.

### Frozen endpoint, ordering, and tolerance

Frozen before execution. Nothing below may be revised after either arm's numbers are observed.

- **Primary endpoint.** Held-out test perplexity at the final generation (index 10), read from
  `{experiment_path}/10/model/eval_results.json` — the file `main.py` collects for its own
  `perplexity` plot. The paired quantity is the same field at generation 0, so each arm's endpoint is
  reported both as an absolute value and as a degradation ratio `perplexity_10 / perplexity_0`.
- **Expected ordering.** The fully synthetic arm degrades more than the human-mixed arm:
  `degradation_ratio(fully_synthetic) > degradation_ratio(human_mixed)`, with both ratios above
  `1.0`. This direction — recursive training on model output degrades a model, and retaining human
  data slows that degradation — is the qualitative result the positive control exists to recover.
- **Primary criterion (ordering).** The reproduction passes its ordering test only if the strict
  inequality above holds at generation 10 and is not an artifact of a single generation: the
  fully-synthetic curve must be at or above the human-mixed curve for the majority of generations
  1–10.
- **Numerical tolerance.** The upstream repository publishes no per-generation uncertainty for these
  arms, and a single seeded chain per arm provides no within-arm variance estimate. Therefore, per
  the rule already stated below, a **5% relative difference against the published values is used as
  an internal engineering tolerance only**. It is not evidence of exact replication, and no report
  produced from this protocol may describe it as such. A run that recovers the ordering but misses
  the 5% band is recorded as `valid_with_limitation`, not `valid`.
- **Rerun rule.** A rerun under the identical frozen configuration is permitted only for a failure
  classified as `infrastructure_failure` (host preemption, OOM, disk exhaustion, network loss during
  asset download). An `implementation_defect` requires the defect to be fixed, logged in
  `FAILURE_LOG.md`, and *both* arms re-run from generation 0 — never one arm alone. A
  `scientific_divergence` — the run completes and the ordering does not appear — may **not** be
  rerun for a better result; it is reported as a reproduction failure in
  `docs/positive_control/failure_report.md`.
- **Endpoint generation.** The comparison table in `docs/positive_control/expected_vs_observed.md`
  is generated from saved `eval_results.json` artifacts by
  `scripts/reproduce_positive_control.sh`, never transcribed by hand.

### Pre-run record

Before execution, record:

- upstream repository URL and commit;
- model and tokenizer identifiers plus revisions;
- dataset identifier, revision, license, and preprocessing hash;
- operating system, Python, CUDA, framework, and dependency lock;
- hardware type and memory;
- all seeds;
- generation and optimization configurations;
- expected source figure/table and extracted values;
- tolerance and reason for choosing it.

### Acceptance criteria

The reproduction passes only when:

1. both arms complete every planned generation;
2. the expected arm ordering and degradation/rescue direction are recovered;
3. the primary endpoint falls within the criterion frozen before execution;
4. a clean rerun reaches the same scientific conclusion;
5. all deviations from upstream are listed;
6. exact commands regenerate the report from saved metrics.

If the paper provides suitable uncertainty, use it for the endpoint criterion. If it does not, a 5% relative difference may be used as an internal engineering tolerance only; it must not be described as proof of exact replication.

## 3. Blocking pipeline invariants

### Data separation

Each example receives a stable content hash before splitting. These partitions must be disjoint:

- base human training data;
- per-generation rescue candidates;
- generation prompts;
- validation data;
- final human test data.

No final test example may be used for prompting, selection, threshold tuning, early stopping, or hyperparameter selection.

### Token accounting

Record both:

- total optimizer-consumed training tokens; and
- human-origin optimizer-consumed tokens.

Counts must come from tokenized batches actually consumed by the optimizer, not estimated character or document counts. Padding tokens must be treated consistently and documented.

### Provenance

Every training example retains:

- stable ID;
- content hash;
- source dataset and revision;
- human or synthetic origin;
- recursive generation;
- selection policy and score;
- whether it was selected;
- number of optimizer presentations.

### Reproducibility

- Seeds propagate through data sampling, generation, model initialization, dropout, and evaluation.
- Resuming from a frozen checkpoint must preserve the predeclared conclusion.
- Manifests and aggregate results are immutable inputs to analysis.
- Tables and figures are generated by scripts and receive content hashes.

## 4. Stage B: novel pilot contract

Stage B remains blocked until Stages A and the invariant tests pass.

### Experimental unit

One independently seeded recursive chain.

### Proposed treatment families

- no rescue;
- fresh random rescue;
- matched schedule-only allocation;
- matched selection-only allocation;
- proposed joint time-and-mode policy;
- oracle upper bound.

### Fairness constraint

Every policy in a budget-matched comparison consumes exactly the same lifetime number of human-origin optimizer tokens and the same total optimizer-token budget unless an explicitly labeled sensitivity analysis changes that constraint.

### Proposed primary outcomes

1. Area under the generation-wise held-out human NLL-regret curve.
2. Frozen tail-retention measure evaluated on a partition never used for selection.

### Statistical principle

Uncertainty is calculated across independent chains. Multiple generations within one chain are repeated observations, not additional independent samples.

## 5. No-result rule

No experimental value enters `README.md`, `CLAIMS.md`, an abstract, or a presentation until the run is complete, the manifest is valid, blocking tests pass, and the analysis is regenerated from immutable artifacts.
