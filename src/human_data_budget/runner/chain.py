"""Executable toy chain proving that frozen component contracts connect.

This module deliberately does not train a language model. Khantushig replaces
the toy transition behind the same artifact contracts during implementation.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from human_data_budget.generation.toy import toy_generate_step
from human_data_budget.models import Candidate, ChainResult, GenerationMetric, PolicyState
from human_data_budget.policies import (
    JointPolicy,
    NoRescuePolicy,
    RandomPolicy,
    ScheduleOnlyPolicy,
    SelectionOnlyPolicy,
)
from human_data_budget.policies.base import Policy, validate_allocation
from human_data_budget.runner.checkpoint import (
    checkpoint_path,
    latest_checkpoint,
    load_checkpoint,
    save_checkpoint,
)
from human_data_budget.runner.evaluator import NullEvaluator, load_toy_eval_corpus
from human_data_budget.runner.failure import FailureState, write_failure
from human_data_budget.runner.manifest import (
    attach_failure,
    new_manifest,
    record_generation,
    transition_status,
    write_manifest_atomic,
)
from human_data_budget.training.toy import toy_train_step


def policy_from_config(config: dict[str, Any]) -> Policy:
    name = config["policy"]
    per_generation = config["per_generation_human_budget"]
    if name == "no_rescue":
        return NoRescuePolicy()
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


def _tail_modes(config: dict[str, Any], mode_statistics: dict[str, float]) -> set[str]:
    configured = config.get("tail_modes")
    if configured is not None:
        return set(configured)
    return {mode for mode in mode_statistics if "tail" in mode}


def _write_chain_result(result: ChainResult, path: Path) -> None:
    # newline="\n": the auditor records sha256(chain_result.json), and
    # Path.write_text would emit CRLF on Windows, so the same logical run
    # hashed differently per operating system. See write_manifest_atomic.
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    with tmp_path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(result.as_dict(), indent=2) + "\n")
    tmp_path.replace(path)


def run_directory(config: dict[str, Any], base_dir: Path = Path("runs")) -> Path:
    """Return the canonical run directory for this config's run_id.

    Matches ``docs/ARCHITECTURE.md``'s ``runs/<run_id>/`` artifact layout: one
    directory per run_id, deterministic across repeated invocations (not
    random or timestamped), so a restarted process can find it again by
    run_id alone to resume.
    """

    return base_dir / config["run_id"]


def run_toy_chain(
    config: dict[str, Any],
    *,
    output_dir: Path | None = None,
    resume: bool = False,
) -> tuple[dict[str, Any], ChainResult]:
    """Run the toy train/generate/allocate/evaluate chain.

    With ``output_dir`` unset the run is a pure function of ``config``: no
    filesystem writes, matching the original fixture contract used by
    ``tests/runner/test_toy_chain.py`` and ``tests/contracts/test_schemas.py``.

    With ``output_dir`` set, the run atomically persists the manifest and a
    per-generation checkpoint as it progresses. Passing ``resume=True``
    restores from the latest checkpoint under ``output_dir`` (if any) instead
    of starting at generation zero, and reaching the same final result as an
    uninterrupted run for the same seed.
    """

    candidates = tuple(Candidate(**candidate) for candidate in config["candidates"])
    policy = policy_from_config(config)
    eval_corpus = load_toy_eval_corpus()
    evaluator = NullEvaluator()

    manifest = new_manifest(config, policy_name=policy.name)
    checkpoint: dict[str, Any] | None = None
    if output_dir is not None:
        if resume:
            found = latest_checkpoint(output_dir)
            checkpoint = load_checkpoint(found) if found is not None else None
        manifest = transition_status(manifest, "running")
        write_manifest_atomic(manifest, output_dir / "run_manifest.json")

    if checkpoint is not None:
        start_generation = checkpoint["generation"] + 1
        remaining = checkpoint["remaining_human_tokens"]
        consumed_human = checkpoint["consumed_human_tokens"]
        mode_statistics = dict(checkpoint["mode_statistics"])
        allocations: list[dict[str, Any]] = list(checkpoint["allocations"])
        metrics: list[GenerationMetric] = [
            GenerationMetric(**metric) for metric in checkpoint["metrics"]
        ]
    else:
        start_generation = 0
        remaining = config["lifetime_human_budget"]
        consumed_human = 0
        mode_statistics = dict(config["mode_statistics"])
        allocations = []
        metrics = []

    active_generation: int | None = None
    try:
        for generation in range(start_generation, config["horizon"]):
            active_generation = generation
            policy_seed = config["chain_seed"] * 1000 + generation

            # 1. train: toy, no real model -- trains on the budget consumed by
            #    prior generations, deterministic under policy_seed.
            train_state = {"generation": generation, "consumed_tokens": consumed_human}
            toy_train_step(train_state, policy_seed)

            # 2. generate: toy synthetic examples from the just-trained checkpoint.
            generate_state = {"generation": generation, "examples_per_generation": 2}
            toy_generate_step(generate_state, policy_seed)

            # 3. allocate: policy decides this generation's human rescue.
            state = PolicyState(
                generation=generation,
                remaining_human_tokens=remaining,
                mode_statistics=mode_statistics,
                candidates=candidates,
                history=tuple(allocations),
            )
            allocation = policy.allocate(state, policy_seed)
            validate_allocation(allocation, state)
            remaining -= allocation.selected_human_tokens
            consumed_human += allocation.selected_human_tokens
            allocations.append(allocation.as_dict())

            rescued_modes = set(allocation.mode_allocations)
            mode_statistics = {
                mode: max(0.0, score + 0.08 - (0.12 if mode in rescued_modes else 0.0))
                for mode, score in mode_statistics.items()
            }
            current_coverage = {
                mode: max(1e-6, 1.0 - undercoverage)
                for mode, undercoverage in mode_statistics.items()
            }

            # 4. evaluate: frozen null evaluator against the held-out toy fixture.
            evaluation = evaluator.evaluate(
                run_id=config["run_id"],
                generation=generation,
                checkpoint_sha256=f"toy-checkpoint-generation-{generation}",
                evaluation_manifest_sha256="fixture",
                current_mode_scores=current_coverage,
                reference_mode_scores=eval_corpus["reference_mode_scores"],
                tail_modes=_tail_modes(config, mode_statistics),
                target_log_probabilities=eval_corpus["target_log_probabilities"],
            )
            metrics.append(
                GenerationMetric(
                    generation=generation,
                    human_nll=evaluation["human_nll"],
                    tail_retention=evaluation["tail_retention"]["primary"],
                )
            )

            # 5. checkpoint: atomically persist this generation's full state.
            if output_dir is not None:
                save_checkpoint(
                    {
                        "generation": generation,
                        "remaining_human_tokens": remaining,
                        "consumed_human_tokens": consumed_human,
                        "mode_statistics": mode_statistics,
                        "allocations": allocations,
                        "metrics": [metric.as_dict() for metric in metrics],
                    },
                    checkpoint_path(output_dir, generation),
                )
                manifest = record_generation(manifest, generation)
                write_manifest_atomic(manifest, output_dir / "run_manifest.json")
    except Exception as error:
        if output_dir is not None:
            failure = FailureState(
                run_id=config["run_id"],
                category="implementation_defect",
                message=str(error),
                generation=active_generation,
                evidence={"error_type": type(error).__name__},
            )
            write_failure(failure, output_dir / "failure.json")
            manifest = attach_failure(manifest, failure.as_dict())
            manifest = transition_status(manifest, "failed")
            write_manifest_atomic(manifest, output_dir / "run_manifest.json")
        raise

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

    if output_dir is not None:
        manifest = transition_status(manifest, "complete")
        write_manifest_atomic(manifest, output_dir / "run_manifest.json")
        _write_chain_result(result, output_dir / "chain_result.json")

    return manifest, result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument(
        "--output-dir", type=Path, help="override the default runs/<run_id> directory"
    )
    parser.add_argument(
        "--resume", action="store_true", help="resume from the latest checkpoint in --output-dir"
    )
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    output_dir = args.output_dir or run_directory(config)
    output_dir.mkdir(parents=True, exist_ok=True)
    _, result = run_toy_chain(config, output_dir=output_dir, resume=args.resume)
    (output_dir / "allocation_note.txt").write_text(
        "Fixture output only; not scientific evidence.\n", encoding="utf-8"
    )
    print(f"completed toy chain: {result.run_id} -> {output_dir}")


if __name__ == "__main__":
    main()
