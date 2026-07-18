"""Executable toy chain proving that frozen component contracts connect.

This module deliberately does not train a language model. Khantushig replaces
the toy transition behind the same artifact contracts during implementation.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from human_data_budget.models import Candidate, ChainResult, GenerationMetric, PolicyState
from human_data_budget.policies import (
    JointPolicy,
    RandomPolicy,
    ScheduleOnlyPolicy,
    SelectionOnlyPolicy,
)
from human_data_budget.policies.base import Policy, validate_allocation


def policy_from_config(config: dict[str, Any]) -> Policy:
    name = config["policy"]
    per_generation = config["per_generation_human_budget"]
    if name == "random":
        return RandomPolicy(per_generation)
    if name == "schedule_only":
        schedule = {int(key): value for key, value in config["schedule"].items()}
        return ScheduleOnlyPolicy(schedule)
    if name == "selection_only":
        return SelectionOnlyPolicy(per_generation)
    if name == "joint":
        return JointPolicy(config["horizon"], per_generation)
    raise ValueError(f"unknown policy: {name}")


def run_toy_chain(config: dict[str, Any]) -> tuple[dict[str, Any], ChainResult]:
    candidates = tuple(Candidate(**candidate) for candidate in config["candidates"])
    policy = policy_from_config(config)
    remaining = config["lifetime_human_budget"]
    consumed_human = 0
    metrics: list[GenerationMetric] = []
    allocations: list[dict[str, Any]] = []
    mode_statistics = dict(config["mode_statistics"])

    for generation in range(config["horizon"]):
        state = PolicyState(
            generation=generation,
            remaining_human_tokens=remaining,
            mode_statistics=mode_statistics,
            candidates=candidates,
            history=tuple(allocations),
        )
        allocation = policy.allocate(state, config["chain_seed"] * 1000 + generation)
        validate_allocation(allocation, state)
        remaining -= allocation.selected_human_tokens
        consumed_human += allocation.selected_human_tokens
        allocations.append(allocation.as_dict())

        rescued_modes = set(allocation.mode_allocations)
        mode_statistics = {
            mode: max(0.0, score + 0.08 - (0.12 if mode in rescued_modes else 0.0))
            for mode, score in mode_statistics.items()
        }
        mean_undercoverage = sum(mode_statistics.values()) / len(mode_statistics)
        metrics.append(
            GenerationMetric(
                generation=generation,
                human_nll=3.0 + mean_undercoverage,
                tail_retention=max(0.0, 1.0 - mean_undercoverage),
            )
        )

    result = ChainResult(
        run_id=config["run_id"],
        policy=policy.name,
        chain_seed=config["chain_seed"],
        budget_id=config["budget_id"],
        generations_completed=config["horizon"],
        valid=True,
        metrics=tuple(metrics),
        consumed_human_tokens=consumed_human,
        consumed_total_tokens=config["total_optimizer_tokens"],
    )
    manifest = {
        "schema_version": "1.0",
        "run_id": config["run_id"],
        "stage": "fixture",
        "git_commit": "0000000000000000000000000000000000000000",
        "working_tree_clean": True,
        "model": {
            "identifier": "toy-model",
            "revision": "fixture-v1",
            "tokenizer_revision": "fixture-v1",
        },
        "data": {
            "train_manifest": "data/fixtures/toy_corpus.jsonl",
            "train_manifest_sha256": "fixture",
        },
        "policy": {"name": policy.name, "config": "toy_cpu.json", "config_sha256": "fixture"},
        "budget": {
            "lifetime_human_optimizer_tokens": config["lifetime_human_budget"],
            "total_optimizer_tokens": config["total_optimizer_tokens"],
        },
        "randomness": {"chain_seed": config["chain_seed"]},
        "environment": {"python": ">=3.10", "hardware": "cpu-fixture"},
        "horizon": config["horizon"],
        "status": "complete",
    }
    return manifest, result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    output_dir = args.output_dir or Path(config.get("output_dir", "tmp/toy_run"))
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest, result = run_toy_chain(config)
    (output_dir / "run_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    (output_dir / "chain_result.json").write_text(
        json.dumps(result.as_dict(), indent=2) + "\n", encoding="utf-8"
    )
    (output_dir / "allocation_note.txt").write_text(
        "Fixture output only; not scientific evidence.\n", encoding="utf-8"
    )
    print(f"completed toy chain: {result.run_id} -> {output_dir}")


if __name__ == "__main__":
    main()
