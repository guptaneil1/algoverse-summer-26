# Dataset Datasheet

**Owner:** Neil (data, evaluation, and validity lead)
**Status:** Primary domain selected — Week 2 freeze adds hashes, partition manifests, and frozen mode definition.

---

## Primary Domain: WikiText-103

**Source:** Merity et al., *Pointer Sentinel Mixture Models* (2016).
Available at `wikitext` on the Hugging Face Hub (`wikitext-103-v1`).

**License:** Creative Commons Attribution-ShareAlike 3.0 Unported (CC-BY-SA-3.0).
This license permits use for ML training and academic publication, provided attribution is given and derivative works share under the same license.

**Version:** `wikitext-103-v1` (canonical tokenized train/valid/test splits).

**Size:** approximately 103 million training tokens, 218k validation tokens, 246k test tokens (whitespace-split estimates; optimizer-consumed counts depend on the frozen tokenizer).

---

## Why WikiText-103

| Criterion | Assessment |
|---|---|
| License | CC-BY-SA — permits ML training and publication |
| Size | ~103M tokens fits a 124M–160M screening model on available compute |
| Mode diversity | Articles span broad categories (politics, science, arts, sports) enabling principled tail/common split |
| Reproducibility | Canonical release on Hugging Face; SHA-256 of the dataset card is stable |
| Benchmark standing | Widely used; positive-control reproduction against published NLL is straightforward |
| Personal data | None — Wikipedia content is encyclopedic, not personal |

**Fallback:** OpenWebText2 (Reddit-upvoted link corpus, permissive license). Activated only if WikiText-103 licensing or access is blocked at Week 2.

---

## Mode Definition (Candidate — to be frozen at Week 2)

Two candidate definitions will be evaluated on the validation partition before Week 2 freeze:

1. **Wikipedia article category** — Each article's top-level category (e.g., Politics, Science, Sports) defines its mode. Tail modes are categories with < 5% of total training tokens.
2. **Article length quantile** — Bottom decile of articles by token count defines the tail; top 50% defines common. Simpler and does not require category metadata.

The frozen definition will be selected based on which produces cleaner tail/common separation under the validation NLL distribution. The choice must be made before primary outcomes are opened.

---

## Data Partitions

All five partitions are constructed from the WikiText-103 canonical release using a deterministic stable-ID hash split. Disjointness is enforced by the `assert_disjoint` function in `data/separation.py` and verified by the overlap tests in `tests/data/`.

| Partition | Source split | Purpose |
|---|---|---|
| `base_train` | wiki-103 train (~80%) | Initial model training |
| `rescue_candidates` | wiki-103 train (~15%) | Pool for human-data rescue allocation |
| `prompts` | wiki-103 train (~5%) | Generation conditioning; never for training or evaluation |
| `validation` | wiki-103 valid | Early stopping and configuration decisions |
| `test` | wiki-103 test | **Final held-out evaluation only** |

Exact article assignments, SHA-256 hashes of each manifest file, and the frozen tokenizer identifier will be recorded here and in `configs/data/wikitext103.json` at the Week 2 integration gate.

---

## Token-Counting Rule

Optimizer-consumed tokens are counted using the frozen tokenizer with the following rule:

- Padding tokens (ID = 0 under the frozen tokenizer) are excluded.
- If an example is presented in N epochs, it contributes N × non-padding-token-count to the lifetime budget.

This rule is implemented in `data/token_accounting.py` (`consumed_tokens`) and tested in `tests/data/test_token_accounting.py`.

---

## Known Limitations and Biases

- WikiText-103 covers only English Wikipedia articles that reached Good or Featured status. It overrepresents topics with active Wikipedia editor communities (technology, sports, entertainment) and underrepresents others.
- The article-category mode definition inherits Wikipedia's own category system, which is editorially constructed and may not reflect linguistic diversity.
- Token counts are tokenizer-dependent. The frozen tokenizer must be specified before partition SHA-256 hashes are computed.

---

## Access and Reconstruction

```bash
# Hugging Face datasets library
from datasets import load_dataset
ds = load_dataset("wikitext", "wikitext-103-v1")
```

SHA-256 of the dataset card and each partition manifest file will be recorded here at Week 2. Anyone with a Hugging Face account can reconstruct the dataset; the deterministic hash-split ensures identical partitions.
