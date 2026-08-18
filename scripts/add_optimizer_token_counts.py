#!/usr/bin/env python3
"""Populate ``optimizer_token_count`` on the frozen partition manifests.

``FAILURE_LOG.md`` F-010b: ``token_count`` is ``len(text.split())``, a whitespace
word count. The frozen ``article_length_quantile`` mode definition is built on that
and stays as it is (``docs/data/mode_definition_audit.md`` explicitly names the
"whitespace-split rule" as frozen). But ``PROTOCOL.md`` §3 requires budget
accounting in tokens the optimizer actually consumes, and
``models.Candidate.human_token_count`` documents exactly that. One field cannot be
both, so this adds a second.

**Partition identity is preserved.** ``_manifest_hash`` digests only
``[example_id, content_hash]`` pairs, so populating a new field cannot change a
manifest hash. The script asserts that rather than trusting it.

Build-time only; needs ``transformers`` and the pinned corpus cache.
Usage: python scripts/add_optimizer_token_counts.py [partition ...]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from human_data_budget.data.manifest import load_manifest_from_jsonl
from human_data_budget.data.wikitext_source import resolve_text

MANIFEST_DIR = Path("data/manifests")
TOKENIZER = "openai-community/gpt2"
DEFAULT_PARTITIONS = ("rescue_candidates", "validation", "test", "prompts", "base_train")


def augment(partition: str) -> dict[str, float]:
    from transformers import AutoTokenizer  # noqa: PLC0415 - build-time only

    path = MANIFEST_DIR / f"{partition}.jsonl"
    manifest = load_manifest_from_jsonl(path, partition)
    before = manifest.manifest_hash
    tokenizer = AutoTokenizer.from_pretrained(TOKENIZER)

    records, words, tokens = [], 0, 0
    for index, example in enumerate(manifest.examples, 1):
        text = resolve_text(example)
        count = len(tokenizer(text, add_special_tokens=False)["input_ids"])
        record = example.to_dict() if hasattr(example, "to_dict") else None
        record = {
            "example_id": example.example_id, "content_hash": example.content_hash,
            "origin": example.origin, "mode": example.mode, "source": example.source,
            "source_offset": example.source_offset, "token_count": example.token_count,
            "optimizer_token_count": count,
        }
        if example.source_revision is not None:
            record["source_revision"] = example.source_revision
        records.append(record)
        words += example.token_count
        tokens += count
        if index % 2000 == 0:
            print(f"  {partition}: {index}/{len(manifest.examples)}", flush=True)

    tmp = path.with_suffix(".jsonl.tmp")
    tmp.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in records),
                   encoding="utf-8")
    tmp.replace(path)

    after = load_manifest_from_jsonl(path, partition).manifest_hash
    if before != after:
        raise SystemExit(f"{partition}: manifest hash changed {before} -> {after}")
    ratio = tokens / words if words else float("nan")
    print(f"{partition}: {len(records)} examples, {words:,} words -> {tokens:,} tokens "
          f"(x{ratio:.4f}), hash unchanged {after[:16]}")
    return {"words": words, "tokens": tokens, "ratio": ratio}


def main() -> None:
    partitions = sys.argv[1:] or list(DEFAULT_PARTITIONS)
    summary = {p: augment(p) for p in partitions}
    out = MANIFEST_DIR / "OPTIMIZER_TOKEN_COUNTS.json"
    out.write_text(json.dumps({"tokenizer": TOKENIZER, "partitions": summary},
                              indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
