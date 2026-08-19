"""Corpus paths must reach upstream as absolute paths.

FAILURE_LOG.md F-017. Upstream subprocesses run with ``cwd=upstream_dir``, so a
repo-relative corpus path in a config resolves against the upstream checkout rather
than this repository. Every chain then dies at generation 0 with a FileNotFoundError
naming a path under the upstream directory.

The dry-run path could not catch this. It prints the command instead of executing it,
so a path that will never resolve still reads as correct -- which is what happened:
the pilot's dry run reported budget matching holding, and all 25 chains then failed on
the first real training step.

These tests assert the property the dry run did not: that what lands on the command
line is absolute. They read the command the dry run prints, which is the same string
the driver would execute.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from human_data_budget.runner.real_chain import run_real_chain

CORPUS_FLAGS = ("--train_file", "--test_file", "--dataset_filepath")


@pytest.fixture
def chain_config(tmp_path, monkeypatch):
    """A minimal real-chain config using repo-relative corpus paths."""
    repo = tmp_path / "repo"
    corpora = repo / "data" / "corpora"
    corpora.mkdir(parents=True)
    for name in ("base", "prompts", "test"):
        (corpora / f"pilot_{name}.json").write_text(
            json.dumps([{"text": "example text", "context": "ctx"}]), encoding="utf-8"
        )

    (repo / "rescue.jsonl").write_text(
        "\n".join(
            json.dumps({
                "example_id": f"train-{index}",
                "content_hash": f"{index:064x}",
                "mode": "tail",
                "origin": "human",
                "source": "wikitext-103-v1",
                "source_offset": index,
                "token_count": 100,
                "optimizer_token_count": 120,
            })
            for index in range(4)
        ) + "\n",
        encoding="utf-8",
    )

    # The launcher is documented as running from the repository root, which is what
    # makes a relative path in a config resolvable at all.
    monkeypatch.chdir(repo)

    return {
        "run_id": "path_test",
        "budget_id": "path_test_budget",
        "policy": "no_rescue",
        "horizon": 1,
        "chain_seed": 101,
        "lifetime_human_budget": 1000,
        "total_optimizer_tokens": 10_000,
        "upstream_dir": "/nonexistent/upstream",
        "rescue_manifest": "rescue.jsonl",
        "base_corpus": "data/corpora/pilot_base.json",
        "prompt_corpus": "data/corpora/pilot_prompts.json",
        "test_corpus": "data/corpora/pilot_test.json",
        "per_generation_human_budget": 100,
        "tail_modes": ["tail"],
        "model": {"identifier": "openai-community/gpt2", "revision": "abc123"},
        "training": {
            "block_size": 512,
            "loss_on_last_n_tokens": 256,
            "batch_size": 8,
            "num_train_epochs": 1,
            "save_steps": 2000,
            "torch_dtype": "bfloat16",
            "low_cpu_mem_usage": True,
        },
        "decoding": {"temperature": 1.0, "top_p": 1.0, "top_k": 50},
        "detector": {
            "tokenizer_name": "detector",
            "model_path": "detector",
            "ai_confidence_threshold": 0.5,
            "temperature": 1.0,
        },
    }


def corpus_arguments(printed: str) -> list[tuple[str, str]]:
    """Extract every corpus path the dry run put on a command line."""
    found: list[tuple[str, str]] = []
    for flag in CORPUS_FLAGS:
        for match in re.finditer(rf"{re.escape(flag)}\s+(\S+)", printed):
            found.append((flag, match.group(1)))
    return found


def test_corpus_paths_on_the_command_line_are_absolute(chain_config, tmp_path, capsys):
    """The regression: relative paths here resolved against the upstream checkout."""
    run_real_chain(chain_config, output_dir=tmp_path / "out", dry_run=True)
    arguments = corpus_arguments(capsys.readouterr().out)

    assert arguments, "the dry run printed no corpus arguments to check"
    for flag, value in arguments:
        assert Path(value).is_absolute(), (
            f"{flag} was passed {value!r}, which upstream resolves against its own "
            "working directory -- this is F-017"
        )


def test_corpus_paths_do_not_resolve_into_the_upstream_checkout(chain_config, tmp_path,
                                                               capsys):
    """The failure mode itself: a path landing under upstream_dir."""
    run_real_chain(chain_config, output_dir=tmp_path / "out", dry_run=True)
    upstream = Path(chain_config["upstream_dir"])

    for flag, value in corpus_arguments(capsys.readouterr().out):
        resolved = Path(value)
        assert upstream not in resolved.parents, (
            f"{flag} resolves under the upstream checkout: {value}"
        )


def test_configured_corpora_are_the_files_that_get_passed(chain_config, tmp_path,
                                                          capsys):
    """Absolutising must not silently point somewhere else."""
    run_real_chain(chain_config, output_dir=tmp_path / "out", dry_run=True)
    printed = capsys.readouterr().out

    for key in ("base_corpus", "test_corpus", "prompt_corpus"):
        expected = str(Path(chain_config[key]).resolve())
        assert expected in printed, f"{key} does not appear as {expected}"


def test_caller_config_is_not_mutated(chain_config, tmp_path):
    """The caller's dict must survive unchanged; run_pilot reuses it across chains."""
    before = dict(chain_config)
    run_real_chain(chain_config, output_dir=tmp_path / "out", dry_run=True)
    for key in ("base_corpus", "prompt_corpus", "test_corpus"):
        assert chain_config[key] == before[key]
        assert not Path(chain_config[key]).is_absolute()


def test_absolute_paths_are_left_alone(chain_config, tmp_path, capsys):
    """An already-absolute path must survive unchanged."""
    absolute = str(Path("data/corpora/pilot_base.json").resolve())
    chain_config["base_corpus"] = absolute
    run_real_chain(chain_config, output_dir=tmp_path / "out", dry_run=True)
    assert absolute in capsys.readouterr().out
