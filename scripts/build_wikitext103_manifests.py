"""Build the frozen WikiText-103 partition manifests (Neil, Week 2).

Downloads the pinned WikiText-103-v1 revision from the Hugging Face Hub,
reconstructs articles from the line-based release, applies the frozen
article_length_quantile mode definition, splits the corpus into the five
required disjoint partitions with deterministic stable IDs, validates
disjointness and near-duplicate overlap, and writes text-free (hash-only)
manifest files under data/manifests/ — raw text is never written to a
committed path, per data/README.md.

Build-time only. Requires ``pip install huggingface_hub pyarrow`` (not part
of the package's runtime dependencies). Re-running reproduces byte-identical
manifests because the dataset revision, parsing rule, ID scheme, and
partition/mode thresholds are all pinned below.

Usage: python scripts/build_wikitext103_manifests.py
"""

from __future__ import annotations

import hashlib
import json
import re
import statistics
import time
from pathlib import Path

from human_data_budget.data.hashing import content_hash
from human_data_budget.data.manifest import Example, PartitionManifest
from human_data_budget.data.separation import assert_disjoint

REPO_ID = "Salesforce/wikitext"
CONFIG = "wikitext-103-v1"
# Resolved once from the `main` ref on 2026-08-08 and pinned so re-running this
# script always reads the same bytes regardless of upstream changes later.
FROZEN_REVISION = "b08601e04326c79dfdd32d625aee71d232d685c3"
SOURCE_NAME = "wikitext-103-v1"

SPLIT_FILES = {
    "train": [
        f"{CONFIG}/train-00000-of-00002.parquet",
        f"{CONFIG}/train-00001-of-00002.parquet",
    ],
    "validation": [f"{CONFIG}/validation-00000-of-00001.parquet"],
    "test": [f"{CONFIG}/test-00000-of-00001.parquet"],
}

CACHE_DIR = Path(__file__).resolve().parent.parent / ".cache" / "wikitext103"
MANIFEST_DIR = Path(__file__).resolve().parent.parent / "data" / "manifests"

# A top-level article title line looks like "= Title =". Section/subsection
# headings have two or more "=" on each side ("= = Section = =") and are
# intentionally excluded so they stay inside their parent article's text.
TOP_HEADING = re.compile(r"^= ([^=].*[^=]) =$")

# Deterministic train-split partition split: 80% base_train / 15%
# rescue_candidates / 5% prompts, assigned by hashing the stable example ID.
TRAIN_PARTITION_BOUNDARIES = [("base_train", 80), ("rescue_candidates", 95), ("prompts", 100)]


def _download_split(split: str) -> list[str]:
    from huggingface_hub import hf_hub_download

    rows: list[str] = []
    for filename in SPLIT_FILES[split]:
        path = hf_hub_download(
            repo_id=REPO_ID,
            repo_type="dataset",
            filename=filename,
            revision=FROZEN_REVISION,
            cache_dir=str(CACHE_DIR),
        )
        import pyarrow.parquet as pq

        table = pq.read_table(path)
        rows.extend(table.column("text").to_pylist())
    return rows


def _is_article_title_row(rows: list[str], i: int) -> bool:
    """A genuine article title is a lone top-level heading isolated by blank rows.

    ``= Foo = Bar =``-shaped legend/glossary lines inside infobox tables (e.g.
    ``= Position ; GP = \n`` in sports-roster articles) also match
    ``TOP_HEADING`` but sit directly between content rows with no blank-line
    isolation, so the blank-neighbor check is required to avoid shredding one
    real article into hundreds of spurious one-line "articles".
    """
    if not TOP_HEADING.match(rows[i].strip()):
        return False
    prev_blank = i == 0 or rows[i - 1].strip() == ""
    next_blank = i + 1 >= len(rows) or rows[i + 1].strip() == ""
    return prev_blank and next_blank


def _parse_articles(rows: list[str]) -> list[tuple[int, int, str]]:
    """Return (start_row, end_row, text) for each top-level article in split order."""
    articles: list[tuple[int, int, str]] = []
    cur_lines: list[str] = []
    cur_start: int | None = None
    for i, line in enumerate(rows):
        if _is_article_title_row(rows, i):
            if cur_start is not None:
                articles.append((cur_start, i, "".join(cur_lines)))
            cur_lines = [line]
            cur_start = i
        else:
            cur_lines.append(line)
    if cur_start is not None:
        articles.append((cur_start, len(rows), "".join(cur_lines)))
    return articles


def _stable_id(split: str, start_row: int) -> str:
    digest = hashlib.sha256(
        f"wikitext103-v1:{FROZEN_REVISION}:{split}:{start_row}".encode()
    ).hexdigest()[:16]
    return f"{split}-{digest}"


def _train_partition(example_id: str) -> str:
    bucket = int(hashlib.sha256(example_id.encode()).hexdigest(), 16) % 100
    for name, upper in TRAIN_PARTITION_BOUNDARIES:
        if bucket < upper:
            return name
    raise AssertionError("unreachable: boundaries must cover [0, 100)")


def _assign_mode(token_count: int, tail_cutoff: float, common_cutoff: float) -> str:
    """Frozen article_length_quantile definition (see docs/data/mode_definition_audit.md).

    tail: bottom decile of train-article token counts.
    common: top 50% of train-article token counts.
    mid: the remaining middle band — retained, excluded from the frozen
    primary tail/common contrast.
    """
    if token_count <= tail_cutoff:
        return "tail"
    if token_count > common_cutoff:
        return "common"
    return "mid"


def _dedup_exact(
    parsed: dict[str, list[tuple[int, int, str]]],
) -> tuple[dict[str, list[tuple[int, int, str]]], list[dict]]:
    """Drop exact-duplicate articles (by normalized content hash), test/validation/train priority.

    The canonical WikiText-103-v1 release contains exact-duplicate articles,
    including at least one that appears in both train and test ("The Hustler
    (film)" at train row 239010 / test row 4303) — real train/test leakage in
    the upstream release. Processing splits in this priority order means the
    held-out splits always keep their copy and any duplicate is dropped from
    train, so no partition this project builds can leak an eval article into
    training. See docs/data/overlap_report.md.
    """
    seen: dict[str, tuple[str, int]] = {}
    deduped: dict[str, list[tuple[int, int, str]]] = {split: [] for split in parsed}
    dropped_records: list[dict] = []
    for split in ("test", "validation", "train"):
        for start, end, text in parsed[split]:
            h = content_hash(text)
            prior = seen.get(h)
            if prior is not None:
                dropped_records.append(
                    {
                        "dropped_split": split,
                        "dropped_row": start,
                        "kept_split": prior[0],
                        "kept_row": prior[1],
                        "cross_split": split != prior[0],
                    }
                )
                continue
            seen[h] = (split, start)
            deduped[split].append((start, end, text))
    for split in parsed:
        count = sum(1 for d in dropped_records if d["dropped_split"] == split)
        if count:
            print(f"{split}: dropped {count} exact-duplicate article(s)")
    return deduped, dropped_records


NEAR_DUP_THRESHOLD = 0.8
NEAR_DUP_SHINGLE_WORDS = 8
TRAIN_FAMILY = ("base_train", "rescue_candidates", "prompts")
EVAL_FAMILY = ("validation", "test")
NEAR_DUP_LENGTH_BAND = 0.2  # compare only articles within +/-20% token count


def _word_shingles(text: str, n: int = NEAR_DUP_SHINGLE_WORDS) -> frozenset[str]:
    words = text.split()
    if len(words) < n:
        return frozenset({" ".join(words)}) if words else frozenset()
    return frozenset(" ".join(words[i : i + n]) for i in range(len(words) - n + 1))


def _scan_near_duplicates(examples_by_partition: dict[str, list[Example]]) -> list[dict]:
    """Approximate near-duplicate scan between the train family and the eval family.

    Full O(n*m) pairwise Jaccard is intractable at real-corpus scale (tens of
    thousands of train articles). This scopes the scan to the leakage-critical
    boundary — any train-family article resembling a validation/test article —
    and prefilters by token-count band before computing exact word-8-gram
    Jaccard, so it stays exact (not sampled) within score, just bounded in
    scope. within-train-family near-duplication (base_train vs
    rescue_candidates vs prompts) is not a leakage risk and is out of scope
    here; see docs/data/overlap_report.md for the documented limitation.
    """
    import bisect

    eval_examples = [(p, e) for p in EVAL_FAMILY for e in examples_by_partition[p]]
    train_examples = sorted(
        ((p, e) for p in TRAIN_FAMILY for e in examples_by_partition[p]),
        key=lambda pe: pe[1].token_count,
    )
    train_counts = [pe[1].token_count for pe in train_examples]

    shingle_cache: dict[str, frozenset[str]] = {}

    def shingles_of(ex: Example) -> frozenset[str]:
        cached = shingle_cache.get(ex.example_id)
        if cached is None:
            cached = _word_shingles(ex.text)
            shingle_cache[ex.example_id] = cached
        return cached

    results: list[dict] = []
    for eval_partition, eval_ex in eval_examples:
        lo = int(eval_ex.token_count * (1 - NEAR_DUP_LENGTH_BAND))
        hi = int(eval_ex.token_count * (1 + NEAR_DUP_LENGTH_BAND))
        lo_idx = bisect.bisect_left(train_counts, lo)
        hi_idx = bisect.bisect_right(train_counts, hi)
        if lo_idx == hi_idx:
            continue
        eval_shingles = shingles_of(eval_ex)
        for train_partition, train_ex in train_examples[lo_idx:hi_idx]:
            train_shingles = shingles_of(train_ex)
            union = len(eval_shingles | train_shingles)
            if union == 0:
                continue
            jaccard = len(eval_shingles & train_shingles) / union
            if jaccard >= NEAR_DUP_THRESHOLD:
                results.append(
                    {
                        "eval_id": eval_ex.example_id,
                        "eval_partition": eval_partition,
                        "train_id": train_ex.example_id,
                        "train_partition": train_partition,
                        "jaccard": jaccard,
                    }
                )
    return results


def build() -> dict:
    t0 = time.time()
    raw_rows = {split: _download_split(split) for split in SPLIT_FILES}
    print(f"downloaded 3 splits in {time.time() - t0:.1f}s")

    parsed = {split: _parse_articles(rows) for split, rows in raw_rows.items()}
    for split, articles in parsed.items():
        print(f"{split}: {len(articles)} articles from {len(raw_rows[split])} rows")

    parsed, dedup_dropped = _dedup_exact(parsed)

    train_token_counts = sorted(len(text.split()) for _, _, text in parsed["train"])
    tail_cutoff = statistics.quantiles(train_token_counts, n=10)[0]  # 10th percentile
    common_cutoff = statistics.median(train_token_counts)  # 50th percentile
    print(
        f"mode thresholds (from train): tail<={tail_cutoff:.0f} tokens, "
        f"common>{common_cutoff:.0f} tokens"
    )

    examples_by_partition: dict[str, list[Example]] = {
        "base_train": [],
        "rescue_candidates": [],
        "prompts": [],
        "validation": [],
        "test": [],
    }

    for split, articles in parsed.items():
        for start_row, _end_row, text in articles:
            token_count = len(text.split())
            example_id = _stable_id(split, start_row)
            mode = _assign_mode(token_count, tail_cutoff, common_cutoff)
            partition = _train_partition(example_id) if split == "train" else split
            example = Example.from_dict(
                {
                    "example_id": example_id,
                    "text": text,
                    "origin": "human",
                    "mode": mode,
                    "source": SOURCE_NAME,
                    "source_offset": start_row,
                    "token_count": token_count,
                }
            )
            examples_by_partition[partition].append(example)

    manifests = {
        partition: PartitionManifest.from_examples(partition, examples)
        for partition, examples in examples_by_partition.items()
    }

    assert_disjoint({p: [e.example_id for e in m.examples] for p, m in manifests.items()})
    assert_disjoint({p: [e.content_hash for e in m.examples] for p, m in manifests.items()})
    print("exact-overlap check passed: all five partitions disjoint by ID and content hash")

    t1 = time.time()
    near_dup_pairs = _scan_near_duplicates(examples_by_partition)
    print(
        f"near-duplicate scan (train-family vs eval-family): {len(near_dup_pairs)} "
        f"pair(s) >= {NEAR_DUP_THRESHOLD} in {time.time() - t1:.1f}s"
    )
    for pair in near_dup_pairs:
        print(
            f"  near-dup: {pair['train_partition']}/{pair['train_id']} ~ "
            f"{pair['eval_partition']}/{pair['eval_id']} (jaccard={pair['jaccard']:.3f})"
        )

    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    summary: dict = {
        "dataset_revision": FROZEN_REVISION,
        "tail_cutoff_tokens": tail_cutoff,
        "common_cutoff_tokens": common_cutoff,
        "exact_duplicates_dropped": len(dedup_dropped),
        "exact_duplicates_cross_split": [d for d in dedup_dropped if d["cross_split"]],
        "near_duplicate_pairs": near_dup_pairs,
        "partitions": {},
    }
    for partition, manifest in manifests.items():
        out_path = MANIFEST_DIR / f"{partition}.jsonl"
        with out_path.open("w", encoding="utf-8") as f:
            for record in manifest.to_dict()["examples"]:
                f.write(json.dumps(record, sort_keys=True) + "\n")
        mode_counts: dict[str, int] = {}
        total_tokens = 0
        for e in manifest.examples:
            mode_counts[e.mode] = mode_counts.get(e.mode, 0) + 1
            total_tokens += e.token_count
        summary["partitions"][partition] = {
            "manifest_hash": manifest.manifest_hash,
            "example_count": len(manifest.examples),
            "total_tokens": total_tokens,
            "mode_counts": mode_counts,
            "manifest_file_sha256": hashlib.sha256(out_path.read_bytes()).hexdigest(),
        }
        print(
            f"wrote {out_path} ({len(manifest.examples)} examples, "
            f"hash {manifest.manifest_hash[:12]}...)"
        )

    summary_path = MANIFEST_DIR / "MANIFEST_HASHES.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {summary_path}")

    return {"manifests": manifests, "summary": summary, "dedup_dropped": dedup_dropped}


if __name__ == "__main__":
    build()
