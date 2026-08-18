"""Contract tests for the real recursive train and generate steps.

CPU only. No model stack, no GPU, no upstream checkout: every test here either
builds an argument list or exercises a pure helper. Anything requiring real
execution belongs in a GPU job, not in CI.

The argument-list tests exist for the same reason the positive control pins its
builders by test -- the invocation *is* the reproduction. A silent change to a
decoding flag would alter results while every other test kept passing.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from human_data_budget.generation.real import build_generate_command, real_generate_step
from human_data_budget.runner.upstream_driver import (
    UpstreamStepError,
    optimizer_consumed_tokens,
    sha256_file,
    sha256_tree,
    step_environment,
)
from human_data_budget.training.real import build_train_command, real_train_step

TRAIN_STATE = {
    "upstream_dir": "/tmp/upstream", "generation": 3,
    "model_identifier": "openai-community/gpt2", "train_file": "/tmp/g3/data.json",
    "test_file": "/tmp/data/test.json", "output_dir": "/tmp/exp/3/model",
    "block_size": 512, "loss_on_last_n_tokens": 256, "batch_size": 8,
    "num_train_epochs": 1, "save_steps": 2000, "torch_dtype": "bfloat16",
    "low_cpu_mem_usage": True,
}

GENERATE_STATE = {
    "upstream_dir": "/tmp/upstream", "generation": 4,
    "model_identifier": "openai-community/gpt2",
    "checkpoint_path": "/tmp/exp/3/model/final_model", "experiment_path": "/tmp/exp",
    "dataset_filepath": "/tmp/data/train.json", "block_size": 512,
    "loss_on_last_n_tokens": 256, "torch_dtype": "bfloat16", "low_cpu_mem_usage": True,
    "temperature": 1.0, "top_p": 1.0, "top_k": 50,
    "detector_tokenizer_name": "GeorgeDrayson/modernbert-ai-detection",
    "detector_path": "GeorgeDrayson/modernbert-ai-detection",
    "detector_threshold": 0.8674598932266235, "detector_temperature": 1.359828233718872,
}


def _flag(command: list[str], name: str) -> str:
    return command[command.index(name) + 1]


def test_train_command_carries_the_frozen_training_settings() -> None:
    command = build_train_command(TRAIN_STATE, seed=42)
    assert command[1] == "src/train.py"
    assert _flag(command, "--model_name_or_path") == "openai-community/gpt2"
    assert _flag(command, "--block_size") == "512"
    assert _flag(command, "--loss_on_last_n_tokens") == "256"
    assert _flag(command, "--seed") == "42"
    assert _flag(command, "--torch_dtype") == "bfloat16"
    assert _flag(command, "--iteration") == "3"
    assert "--do_train" in command and "--do_eval" in command


def test_train_command_pins_human_alpha_to_zero() -> None:
    """The policy assembles the mixture; upstream must not add to it.

    If this ever becomes nonzero, upstream blends human data by proportion on top of
    the corpus the policy selected, and the budget-matching guarantee is void.
    """
    assert _flag(build_train_command(TRAIN_STATE, seed=42), "--human_data_alpha") == "0.0"


def test_generate_command_carries_the_frozen_decoding_settings() -> None:
    command = build_generate_command(GENERATE_STATE, seed=42)
    assert command[1] == "src/generate.py"
    assert _flag(command, "--top_k") == "50"
    assert _flag(command, "--temperature") == "1.0"
    assert _flag(command, "--top_p") == "1.0"
    assert _flag(command, "--input_token_length") == "256"
    assert _flag(command, "--model_path") == "/tmp/exp/3/model/final_model"
    assert _flag(command, "--iteration") == "4"


def test_generate_command_caps_self_bleu_sampling() -> None:
    """Deviation 9 in expected_vs_observed.md. Stage A and Stage B must match."""
    assert _flag(build_generate_command(GENERATE_STATE, seed=42), "--self_bleu_n_sample") == "50"


@pytest.mark.parametrize("builder,state", [
    (build_train_command, TRAIN_STATE), (build_generate_command, GENERATE_STATE)])
def test_builders_refuse_incomplete_state(builder, state) -> None:
    for key in ("upstream_dir", "block_size"):
        broken = {k: v for k, v in state.items() if k != key}
        with pytest.raises(UpstreamStepError, match="missing keys"):
            builder(broken, seed=42)


def test_dry_run_returns_the_command_without_executing(tmp_path: Path) -> None:
    state = dict(TRAIN_STATE, dry_run=True, log_path=str(tmp_path / "log.txt"))
    result = real_train_step(state, seed=42)
    assert result["dry_run"] is True and result["command"][1] == "src/train.py"

    gen = dict(GENERATE_STATE, dry_run=True, log_path=str(tmp_path / "log.txt"))
    assert real_generate_step(gen, seed=42)["dry_run"] is True


def test_shim_is_opt_in_and_prepends_to_pythonpath(tmp_path: Path) -> None:
    """F-007: a shim on the default sys.path is shadowed by the distro sitecustomize."""
    plain = step_environment(0)
    assert "STAGE_A_WANDB_SHIM" not in plain
    assert plain["WANDB_MODE"] == "disabled"

    shimmed = step_environment(1, shim_dir=tmp_path)
    assert shimmed["STAGE_A_WANDB_SHIM"] == "1"
    assert shimmed["PYTHONPATH"].startswith(str(tmp_path))
    assert shimmed["CUDA_VISIBLE_DEVICES"] == "1"


def test_token_accounting_counts_blocks_not_characters(tmp_path: Path) -> None:
    """PROTOCOL.md section 3: counts come from batches the optimizer consumed."""
    results = tmp_path / "train_results.json"
    results.write_text(json.dumps({"train_samples": 4669}), encoding="utf-8")
    assert optimizer_consumed_tokens(results, 512) == 2390528


def test_token_accounting_refuses_to_estimate(tmp_path: Path) -> None:
    results = tmp_path / "train_results.json"
    results.write_text(json.dumps({"train_runtime": 33.79}), encoding="utf-8")
    with pytest.raises(UpstreamStepError, match="train_samples"):
        optimizer_consumed_tokens(results, 512)


def test_tree_hash_is_order_stable_and_content_sensitive(tmp_path: Path) -> None:
    root = tmp_path / "model"
    (root / "nested").mkdir(parents=True)
    (root / "b.bin").write_bytes(b"second")
    (root / "a.bin").write_bytes(b"first")
    (root / "nested" / "c.bin").write_bytes(b"third")
    first = sha256_tree(root)
    assert first == sha256_tree(root)

    (root / "a.bin").write_bytes(b"changed")
    assert sha256_tree(root) != first


def test_file_hash_matches_known_digest(tmp_path: Path) -> None:
    target = tmp_path / "corpus.json"
    target.write_bytes(b"")
    empty = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    assert sha256_file(target) == empty
