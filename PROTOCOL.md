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
  resolved `transformers` commit at run time; that resolved value, not this paragraph, is the frozen
  identifier for the run.
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
| Dataset | WikiText-2 raw v1, prepared by `python src/load_data.py` into `./data/wikitext2/{train,test}.json` | `config/dataset/wikitext2.yaml`, `src/load_data.py` |
| Decoding | top-k: `temperature=1.0`, `top_p=1.0`, `top_k=50`, `beam_search=false` | `config/decoding/top_k.yaml` |
| Training | `block_size=512`, `loss_on_last_n_tokens=256`, `batch_size=8`, `num_train_epochs=1`, `save_steps=2000` | `config/train/default.yaml` |
| Seed | `42` | `config/config.yaml` |
| Recursive horizon | `num_iterations=10`, i.e. an initial generation 0 plus iterations 1–10 = **11 trained models, generation indices 0–10** | `config/config.yaml`, `main.py` loop `range(1, num_iterations+1)` |
| Detector | `GeorgeDrayson/modernbert-ai-detection`, `temperature=1.359828233718872`, `ai_confidence_threshold=0.8674598932266235` | `config/detector/modernbert_mage.yaml` |
| Precision / device | `torch_dtype=bfloat16`, `low_cpu_mem_usage=true`, `cuda_device=0` | `config/config.yaml` |

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
