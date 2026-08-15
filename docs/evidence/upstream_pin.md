# Upstream Positive-Control Pin Record

**Purpose:** close the `TODO(khantushig)` markers in `PROTOCOL.md` §2 by recording the exact
upstream artifact identifiers for the Stage A positive control.

**Retrieved:** 2026-08-15, via the public GitHub REST API and `raw.githubusercontent.com` at the
pinned commit. Every value below was read from the upstream repository in that session. No value
here is reconstructed from memory.

**Status of this document:** VERIFIED FACTS about upstream. It is *not* evidence that a
reproduction has been attempted. Stage A remains unexecuted — see `docs/STATUS.md`.

## 1. Repository identity

| Field | Value |
|---|---|
| URL | `https://github.com/GeorgeDrayson/model_collapse` |
| Default branch | `main` |
| **Pinned commit** | **`feb8511479a2e2dc868e1caf3f63cb99f1fcc746`** |
| Commit date | 2026-03-13T20:43:11Z |
| Commit message | "Update README.md to reflect EMNLP 2025 acceptance and correct citation format" |
| Upstream license | MIT |
| Repository created | 2025-04-14 |

The pinned commit is the repository HEAD as of retrieval. The last change to executable code is
`3e974bdbad27676e2605263dc35d05dc7c332547` (2025-05-19, "Refactored codebase, added additional
sizes of SmolLM").

**Code-equivalence of the two commits — verified, not assumed.** The GitHub compare API
(`/compare/3e974bd...feb8511`, retrieved 2026-08-15) reports **exactly one changed file**:
`README.md`, modified with 8 additions and 5 deletions (arXiv badge replaced with EMNLP, paper link
pointed at the ACL Anthology, citation changed from `@article` to `@inproceedings`). No other file
differs. A reproduction run against either commit is therefore code-equivalent, and pinning HEAD is
correct because it also carries the authors' own corrected citation.

## 2. Paper of record

The upstream README supplies this citation verbatim. It matches `drayson_2025` in
`docs/evidence/sources.yaml`:

```bibtex
@inproceedings{drayson2025machine,
  title={Machine-generated text detection prevents language model collapse},
  author={Drayson, George and Yilmaz, Emine and Lampos, Vasileios},
  booktitle={Proceedings of the 2025 Conference on Empirical Methods in Natural Language Processing},
  year={2025},
  url={https://aclanthology.org/2025.emnlp-main.1506}
}
```

## 3. Frozen upstream configuration

Read from `config/config.yaml` at the pinned commit:

| Setting | Upstream default |
|---|---|
| Model | `gpt2` |
| Dataset | `wikitext2` |
| Decoding | `top_k` |
| Detector | `modernbert_mage` |
| Data selection | `importance_sampling` |
| Seed | `42` |
| Iterations (recursive generations) | `10` |
| Torch dtype | `bfloat16` |
| Device | CUDA device `0` |
| Low CPU memory mode | enabled |
| Experiment tracking | Weights & Biases, via `WANDB_API_KEY` |

Available model configs: `gpt2.yaml`, `smollm-s.yaml`, `smollm.yaml`, `smollm-xl.yaml`.
Detector: ModernBERT-base fine-tuned for machine-generated-text detection, trained on the
`yaful/MAGE` dataset. The upstream README describes it as a 150M-parameter model; that figure comes
from the README's own prose and was **not** independently confirmed against the model card, so
treat it as upstream's claim rather than a measured parameter count.

### Two confirmations and one deviation for `PROTOCOL.md` §2

- **Confirmed:** model family GPT-2 matches our stated reproduction condition.
- **Confirmed:** `iterations: 10` matches our stated horizon of generations 0 through 9.
- **DEVIATION — requires an explicit decision:** upstream defaults to **`wikitext2`**, but
  `configs/data/wikitext103.json` selects **WikiText-103** for our Stage B pilot. `PROTOCOL.md` §2
  requires Stage A to use "official pinned configurations unless a deviation is documented before
  running." The clean resolution is to run **Stage A on upstream `wikitext2`** and **Stage B on
  WikiText-103**, and to record that the two stages use different corpus sizes from the same
  family. Do not silently switch Stage A to WikiText-103 — that would make the positive control a
  non-replication of the published setting.

## 4. Reproducibility hazard — read before installing

Upstream `requirements.txt` at the pinned commit declares only lower bounds:

```
datasets >= 2.14.0
accelerate >= 0.12.0
torch >= 1.3
evaluate
sentencepiece != 0.1.92
protobuf
scikit-learn
wandb
tqdm
hydra-core
matplotlib
nltk
textstat
mauve-text
seaborn
```

and the README instructs `pip install git+https://github.com/huggingface/transformers` — an
**unpinned install from the live `main` branch**.

**Consequence:** installing today does not reproduce the authors' environment. A fresh install
resolves to whatever `transformers` main happens to be on the install date, which is not the
version the paper's results were produced with. This is the single largest threat to Stage A
acceptance criterion 4 ("a clean rerun reaches the same scientific conclusion"), and it is an
upstream defect, not a defect in our repository.

**Recommended mitigation (Khantushig's call, but do it before the first real run):**

1. Choose a `transformers` commit or release contemporaneous with the upstream code freeze
   (2025-05-19) or with EMNLP 2025 publication, and pin it explicitly rather than tracking main.
2. Verify that the chosen version actually supports ModernBERT, which the detector requires —
   ModernBERT support landed in a specific `transformers` release and older pins will fail to load
   `modernbert_mage`. **Verify the minimum version empirically; do not assume it.**
3. Record every resolved version from the first successful install with `pip freeze`, and write
   those exact pins into `requirements-lock.txt` under a clearly separated positive-control section.
4. If upstream cannot be made to run at any pinned `transformers` version, that is a legitimate
   Stage A outcome and belongs in `FAILURE_LOG.md` as a reproduction-failure package, per
   `docs/weekly/WEEK_2.md`.

## 5. Operational notes for Stage A

- **GPU required.** `device: cuda:0` and `bfloat16` in `config/config.yaml` mean this cannot run on
  the current CPU-only environment. Note also that bfloat16 has limited or no hardware support on
  older accelerator generations — **verify support on the specific card before assuming the config
  runs unmodified**. If the dtype must be changed, that is a documented deviation, recorded before
  the run rather than after.
- **W&B requires a key.** Set `WANDB_API_KEY`, or disable tracking via a Hydra override. Whichever
  is chosen must be recorded in the pre-run record.
- **Hydra overrides** are the supported way to change settings, e.g. `python main.py train.batch_size=16`.
  Record the full override string for every run; it is part of the reproduction command.
- **Run order** per upstream README: create venv → install transformers from Git → `pip install -r
  requirements.txt` → `python src/load_data.py` → `python main.py`.

## 6. What this document does not establish

It does not establish that the positive control reproduces, that our environment can run it, or
that any arm ordering has been observed. Stage A is unexecuted. `PROTOCOL.md` §5 (no-result rule)
continues to apply in full.
