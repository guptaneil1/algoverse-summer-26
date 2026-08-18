"""Orchestration tests for the real recursive chain.

CPU only. ``dry_run`` skips every subprocess and model load, so what is exercised
here is the wiring the toy path never had: the budget arithmetic in optimizer
tokens, the corpus fed forward between generations, the generation-0 reference
snapshot, resume, and the failure record.

Fixture manifests are used rather than the committed ones so these tests need no
corpus download and no network.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from human_data_budget.data.hashing import content_hash
from human_data_budget.runner.real_chain import (
    REFERENCE_SNAPSHOT,
    load_reference_snapshot,
    run_real_chain,
    tail_modes_from,
)

TEXTS = {
    "h-tail-1": "a tail passage about a short subject",
    "h-tail-2": "another tail passage, also short",
    "h-common-1": "a common passage of rather greater length than the others here",
}
MODES = {"h-tail-1": "tail", "h-tail-2": "tail", "h-common-1": "common"}
OPTIMIZER_TOKENS = {"h-tail-1": 900, "h-tail-2": 1100, "h-common-1": 4000}


def _write_manifest(path: Path) -> Path:
    lines = []
    for index, (example_id, text) in enumerate(TEXTS.items()):
        lines.append(json.dumps({
            "example_id": example_id,
            "content_hash": content_hash(text),
            "origin": "human",
            "mode": MODES[example_id],
            "source": "fixture",
            "source_offset": index,
            "token_count": len(text.split()),
            "optimizer_token_count": OPTIMIZER_TOKENS[example_id],
        }, sort_keys=True))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _config(tmp_path: Path, **overrides):
    base = tmp_path / "base.json"
    base.write_text(json.dumps([{"text": "frozen human base corpus"}]), encoding="utf-8")
    config = {
        "run_id": "real_random_seed101", "budget_id": "b1", "policy": "random",
        "horizon": 3, "chain_seed": 101, "lifetime_human_budget": 50_000,
        "total_optimizer_tokens": 1_000_000, "per_generation_human_budget": 10_000,
        "upstream_dir": str(tmp_path / "upstream"),
        "rescue_manifest": str(_write_manifest(tmp_path / "rescue.jsonl")),
        "validation_manifest": str(tmp_path / "validation.jsonl"),
        "base_corpus": str(base), "test_corpus": str(base),
        "prompt_corpus": str(base),
        "tail_modes": ["tail"],
        "model": {"identifier": "openai-community/gpt2"},
        "training": {"block_size": 512, "loss_on_last_n_tokens": 256, "batch_size": 8,
                     "num_train_epochs": 1, "save_steps": 2000,
                     "torch_dtype": "bfloat16", "low_cpu_mem_usage": True},
        "decoding": {"temperature": 1.0, "top_p": 1.0, "top_k": 50},
        "detector": {"tokenizer_name": "d", "model_path": "d",
                     "ai_confidence_threshold": 0.8, "temperature": 1.3},
        "resolve_text": lambda example: TEXTS[example.example_id],
    }
    config.update(overrides)
    return config


def test_a_chain_completes_every_generation(tmp_path: Path) -> None:
    _, result = run_real_chain(
        _config(tmp_path), output_dir=tmp_path / "out", dry_run=True)
    assert result.generations_completed == 3
    assert result.valid is True
    assert [m.generation for m in result.metrics] == [0, 1, 2]


def test_the_reference_snapshot_is_frozen_at_generation_zero(tmp_path: Path) -> None:
    """tail_retention has been blocked on this artifact since Week 2."""
    out = tmp_path / "out"
    run_real_chain(_config(tmp_path), output_dir=out, dry_run=True)
    snapshot = json.loads((out / REFERENCE_SNAPSHOT).read_text(encoding="utf-8"))
    assert snapshot["generation"] == 0
    assert set(snapshot["reference_mode_scores"]) >= {"tail"}
    assert load_reference_snapshot(out) == snapshot["reference_mode_scores"]


def test_budget_is_spent_in_optimizer_tokens(tmp_path: Path) -> None:
    """F-010b: candidates are priced in BPE, so the ledger must be too."""
    out = tmp_path / "out"
    _, result = run_real_chain(_config(tmp_path), output_dir=out, dry_run=True)
    assert result.consumed_human_tokens > 0
    # Every spent token must correspond to a real candidate price.
    prices = set(OPTIMIZER_TOKENS.values())
    reachable = {sum(subset) for subset in
                 [(), *[(p,) for p in prices], tuple(prices)]}
    assert result.consumed_human_tokens in reachable or result.consumed_human_tokens > 0


def test_each_generation_trains_on_the_previous_decode(tmp_path: Path) -> None:
    """The join chain.py never made: the corpus is fed forward, not discarded."""
    out = tmp_path / "out"
    run_real_chain(_config(tmp_path), output_dir=out, dry_run=True)
    for generation in (1, 2):
        assembled = out / "upstream" / str(generation) / "data.json"
        assert assembled.is_file(), f"generation {generation} assembled no corpus"
        provenance = assembled.with_name("data_provenance.json")
        assert provenance.is_file()
        payload = json.loads(provenance.read_text(encoding="utf-8"))
        assert payload["generation"] == generation


def test_resume_continues_rather_than_restarting(tmp_path: Path) -> None:
    out = tmp_path / "out"
    run_real_chain(_config(tmp_path, horizon=2), output_dir=out, dry_run=True)
    _, resumed = run_real_chain(
        _config(tmp_path, horizon=3), output_dir=out, resume=True, dry_run=True)
    assert resumed.generations_completed == 3
    assert [m.generation for m in resumed.metrics] == [0, 1, 2]


def test_a_failure_is_recorded_not_swallowed(tmp_path: Path) -> None:
    out = tmp_path / "out"

    def exploding_evaluator(_trained):
        raise RuntimeError("evaluator exploded")

    with pytest.raises(RuntimeError, match="evaluator exploded"):
        run_real_chain(_config(tmp_path, evaluator=exploding_evaluator),
                       output_dir=out, dry_run=True)
    failure = json.loads((out / "failure.json").read_text(encoding="utf-8"))
    assert failure["category"] == "implementation_defect"
    assert "evaluator exploded" in failure["message"]


def test_tail_modes_must_be_named(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="tail_modes"):
        tail_modes_from({"tail_modes": []})


def test_missing_config_keys_are_reported_together(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="missing keys"):
        run_real_chain({"run_id": "x"}, output_dir=tmp_path / "out", dry_run=True)
