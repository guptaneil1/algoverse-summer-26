#!/usr/bin/env python3
"""Run one positive-control arm generation-at-a-time, resumably.

Why this exists
---------------
Upstream's ``main.py`` runs an arm as one monolithic job: it trains generation 0, then
loops through every remaining generation in a single process with no resume. On a host
with a session cap (Kaggle: 12 h; Colab: shorter) an interrupted arm is lost entirely and
must restart from generation 0.

This driver issues *exactly the same* ``src/train.py`` and ``src/generate.py`` commands, in
exactly the same order, with exactly the same arguments — but one generation at a time,
recording completion as it goes. Stopping and restarting resumes at the first incomplete
generation. The science is unchanged; only the process boundary moves.

Two properties of the upstream code at the pinned commit make this sound, and both were
read from the source rather than assumed:

1. **Generation 0 is identical across arms.** ``main.py``'s initial training command passes
   neither ``--human_data_alpha`` nor ``--data_selection_strategy``, and ``--ai_beta`` is
   ``1.0`` in both arms, so the two arms would compute the same thing twice. ``--shared-
   generation-zero`` computes it once and points both arms at it. That also removes a real
   source of nondeterminism: both arms then share a bit-identical baseline rather than two
   independently trained models that merely ought to match.

2. **Every generation retrains from base GPT-2**, not from the previous checkpoint
   (``main.py`` passes ``--model_name_or_path model_name`` for every iteration). Generation
   *i-1*'s model is therefore needed only to decode generation *i*. Once generation *i*'s
   ``data.json`` exists, that model is scientifically spent, which is what makes
   ``--prune-models`` safe: hashes are written first, and the deletion is recorded.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from human_data_budget.runner.positive_control_adapter import (  # noqa: E402
    UPSTREAM_COMMIT,
    MissingUpstreamArtifactError,
    PositiveControlError,
    artifact_record_path,
    assert_resolved,
    assert_upstream_checkout,
    load_arm_config,
    mark_pruned,
    upstream_artifact_paths,
    write_artifact_record,
)

STATE_NAME = "arm_state.json"


# ----------------------------------------------------------------------------------
# state
# ----------------------------------------------------------------------------------


def load_state(work_dir: Path) -> dict[str, Any]:
    path = work_dir / STATE_NAME
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"generations": {}}


def save_state(work_dir: Path, state: dict[str, Any]) -> None:
    path = work_dir / STATE_NAME
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def generation_is_complete(experiment_path: Path, generation: int) -> bool:
    """A generation counts as done only when all of its artifacts were recorded.

    Deliberately keyed on the sidecar rather than on the model directory: with pruning
    enabled the model may be gone, and its absence must not look like unfinished work.
    """

    if not artifact_record_path(experiment_path, generation).is_file():
        return False
    paths = upstream_artifact_paths(experiment_path, generation)
    return paths["eval_results"].is_file()


# ----------------------------------------------------------------------------------
# command construction — mirrors upstream main.py exactly
# ----------------------------------------------------------------------------------


def train_command_generation_zero(config: dict[str, Any], *, experiment_path: Path,
                                  data_dir: Path) -> list[str]:
    training = config["training"]
    return [
        sys.executable, "src/train.py",
        "--model_name_or_path", config["model"]["identifier"],
        "--output_dir", f"{experiment_path}/0/model/",
        "--per_device_train_batch_size", str(training["batch_size"]),
        "--per_device_eval_batch_size", str(training["batch_size"]),
        "--train_file", str(data_dir / "train.json"),
        "--test_file", str(data_dir / "test.json"),
        "--do_train",
        "--do_eval",
        "--ai_beta", str(config["mixture"]["ai_beta"]),
        "--block_size", str(training["block_size"]),
        "--loss_on_last_n_tokens", str(training["loss_on_last_n_tokens"]),
        "--num_train_epochs", str(training["num_train_epochs"]),
        "--save_steps", str(training["save_steps"]),
        "--seed", str(config["chain_seed"]),
        "--torch_dtype", training["torch_dtype"],
        "--low_cpu_mem_usage", str(training["low_cpu_mem_usage"]),
        "--run_name", "train_iteration_0",
        "--iteration", "0",
        "--preprocessing_num_workers", "1",
    ]


def generate_command(config: dict[str, Any], *, experiment_path: Path, data_dir: Path,
                     generation: int, previous_model: Path) -> list[str]:
    training, decoding, detector = config["training"], config["decoding"], config["detector"]
    return [
        sys.executable, "src/generate.py",
        "--model_name", config["model"]["identifier"],
        "--model_path", str(previous_model),
        "--input_token_length",
        str(training["block_size"] - training["loss_on_last_n_tokens"]),
        "--block_size", str(training["block_size"]),
        "--iteration", str(generation),
        "--experiment_path", str(experiment_path),
        "--dataset_filepath", str(data_dir / "train.json"),
        "--seed", str(config["chain_seed"]),
        "--temperature", str(decoding["temperature"]),
        "--top_p", str(decoding["top_p"]),
        "--top_k", str(decoding["top_k"]),
        "--torch_dtype", training["torch_dtype"],
        "--low_cpu_mem_usage", str(training["low_cpu_mem_usage"]),
        "--classify_text", "1",
        "--detector_tokenizer_name", detector["tokenizer_name"],
        "--detector_path", detector["model_path"],
        "--detector_threshold", str(detector["ai_confidence_threshold"]),
        "--detector_temperature", str(detector["temperature"]),
    ]


def train_command_recursive(config: dict[str, Any], *, experiment_path: Path,
                            data_dir: Path, generation: int) -> list[str]:
    training, selection = config["training"], config["data_selection"]
    return [
        sys.executable, "src/train.py",
        "--model_name_or_path", config["model"]["identifier"],
        "--output_dir", f"{experiment_path}/{generation}/model",
        "--per_device_train_batch_size", str(training["batch_size"]),
        "--per_device_eval_batch_size", str(training["batch_size"]),
        "--train_file", f"{experiment_path}/{generation}/data.json",
        "--test_file", str(data_dir / "test.json"),
        "--experiment_path", str(experiment_path),
        "--human_data_filepath", str(data_dir / "train.json"),
        "--human_data_alpha", str(config["mixture"]["human_data_alpha"]),
        "--ai_beta", str(config["mixture"]["ai_beta"]),
        "--do_train",
        "--do_eval",
        "--block_size", str(training["block_size"]),
        "--loss_on_last_n_tokens", str(training["loss_on_last_n_tokens"]),
        "--num_train_epochs", str(training["num_train_epochs"]),
        "--save_steps", str(training["save_steps"]),
        "--seed", str(config["chain_seed"]),
        "--torch_dtype", training["torch_dtype"],
        "--low_cpu_mem_usage", str(training["low_cpu_mem_usage"]),
        "--run_name", f"train_iteration_{generation}",
        "--iteration", str(generation),
        "--data_selection_strategy", selection["strategy"],
        "--accumulate_ai_data", str(config["mixture"]["accumulate_ai_data"]),
        "--preprocessing_num_workers", "2",
        "--upsample_factor", str(selection.get("upsample_factor", 1.0)),
        "--bias_factor", str(selection.get("bias_factor", 1.0)),
        "--max_repeats", str(selection.get("max_repeats", 1)),
    ]


# ----------------------------------------------------------------------------------
# execution
# ----------------------------------------------------------------------------------


def run_step(command: list[str], *, upstream_dir: Path, log_path: Path,
             cuda_device: int, dry_run: bool) -> float:
    """Run one upstream subprocess, returning its wall time in seconds."""

    printable = " ".join(command)
    print(f"  $ {printable}", flush=True)
    if dry_run:
        return 0.0

    environment = dict(os.environ)
    # Mirrors main.py:33. The child sees exactly one device, so Trainer reports n_gpu 1.
    environment["CUDA_VISIBLE_DEVICES"] = str(cuda_device)
    # main.py:25 guards wandb.init with bool(str(...)), which is always truthy, so init
    # never runs while train.py still calls wandb.log. Disable it at the environment level.
    environment["WANDB_DISABLED"] = "true"
    environment["WANDB_MODE"] = "disabled"

    log_path.parent.mkdir(parents=True, exist_ok=True)
    start = time.perf_counter()
    with open(log_path, "a", encoding="utf-8") as log:
        log.write(f"\n===== {printable}\n")
        log.flush()
        result = subprocess.run(command, cwd=upstream_dir, stdout=log,
                                stderr=subprocess.STDOUT, env=environment)
    elapsed = time.perf_counter() - start

    if result.returncode != 0:
        raise PositiveControlError(
            f"upstream step failed (exit {result.returncode}); full log: {log_path}"
        )
    return elapsed


def prune_previous_model(experiment_path: Path, generation: int, *, dry_run: bool) -> None:
    """Delete generation ``generation``'s model directory, after its hash was recorded."""

    if generation < 0:
        return
    model_dir = upstream_artifact_paths(experiment_path, generation)["model_dir"]
    parent = model_dir.parent
    if not parent.is_dir():
        return

    reason = (
        "pruned to fit host storage quota; the model was hashed before deletion and is "
        "no longer needed because every generation retrains from base GPT-2"
    )
    print(f"  pruning generation {generation} model directory ({parent})", flush=True)
    if dry_run:
        return

    mark_pruned(experiment_path, generation, "model_dir", reason)
    for child in parent.iterdir():
        # Keep the metrics; drop weights and intermediate Trainer checkpoints.
        if child.name in ("eval_results.json", "train_results.json", "all_results.json"):
            continue
        shutil.rmtree(child) if child.is_dir() else child.unlink()


def run_arm(args: argparse.Namespace) -> int:
    config = load_arm_config(args.config)
    assert_resolved(config)
    assert_upstream_checkout(args.upstream_dir)

    experiment_path = args.work_dir / "upstream"
    experiment_path.mkdir(parents=True, exist_ok=True)
    data_dir = args.upstream_dir / "data" / "wikitext2"
    for split in ("train", "test"):
        if not (data_dir / f"{split}.json").is_file():
            raise MissingUpstreamArtifactError(
                f"prepared dataset missing: {data_dir / f'{split}.json'}; "
                f"run (cd {args.upstream_dir} && python src/load_data.py)"
            )

    state = load_state(args.work_dir)
    horizon = config["horizon"]
    log_path = args.work_dir / "stdout_stderr.log"
    started = time.perf_counter()
    completed_now: list[int] = []

    print(f"arm={config['arm']} horizon={horizon} upstream={UPSTREAM_COMMIT[:12]}")

    for generation in range(horizon):
        if args.stop_after_generation is not None and generation > args.stop_after_generation:
            print(f"\nstopping: --stop-after-generation {args.stop_after_generation} reached")
            break

        if generation_is_complete(experiment_path, generation):
            print(f"generation {generation}: already complete, skipping")
            continue

        if args.time_budget_seconds is not None:
            spent = time.perf_counter() - started
            if spent >= args.time_budget_seconds:
                print(
                    f"\nstopping cleanly: {spent:.0f}s spent meets the "
                    f"{args.time_budget_seconds:.0f}s budget. "
                    f"Re-run this command to continue at generation {generation}."
                )
                break

        print(f"\ngeneration {generation}: running")
        timings: dict[str, float] = {}

        if generation == 0:
            if args.shared_generation_zero is not None:
                source = args.shared_generation_zero
                if not generation_is_complete(source, 0):
                    raise MissingUpstreamArtifactError(
                        f"--shared-generation-zero {source} has no completed generation 0"
                    )
                print(f"  reusing shared generation 0 from {source}")
                if not args.dry_run:
                    target = experiment_path / "0"
                    if target.exists():
                        shutil.rmtree(target)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.symlink_to((source / "0").resolve(), target_is_directory=True)
            else:
                timings["train"] = run_step(
                    train_command_generation_zero(
                        config, experiment_path=experiment_path, data_dir=data_dir
                    ),
                    upstream_dir=args.upstream_dir, log_path=log_path,
                    cuda_device=args.cuda_device, dry_run=args.dry_run,
                )
        else:
            previous_model = upstream_artifact_paths(experiment_path, generation - 1)["model_dir"]
            if not previous_model.is_dir() and not args.dry_run:
                raise MissingUpstreamArtifactError(
                    f"generation {generation} needs {previous_model}, which is absent. "
                    "If it was pruned, that generation must be re-run: pruning is only "
                    "safe once the next generation's data.json exists."
                )
            timings["generate"] = run_step(
                generate_command(
                    config, experiment_path=experiment_path, data_dir=data_dir,
                    generation=generation, previous_model=previous_model,
                ),
                upstream_dir=args.upstream_dir, log_path=log_path,
                cuda_device=args.cuda_device, dry_run=args.dry_run,
            )
            timings["train"] = run_step(
                train_command_recursive(
                    config, experiment_path=experiment_path, data_dir=data_dir,
                    generation=generation,
                ),
                upstream_dir=args.upstream_dir, log_path=log_path,
                cuda_device=args.cuda_device, dry_run=args.dry_run,
            )

        if args.dry_run:
            print(f"generation {generation}: dry run, nothing executed")
            continue

        # Hash while everything still exists. Pruning after this point loses bytes,
        # never evidence.
        write_artifact_record(experiment_path, generation)
        state["generations"][str(generation)] = {
            "status": "complete",
            "timings_seconds": timings,
            "completed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        save_state(args.work_dir, state)
        completed_now.append(generation)
        print(f"generation {generation}: complete {timings}")

        if args.prune_models and generation >= 1:
            keep_shared = args.shared_generation_zero is not None and generation - 1 == 0
            if not keep_shared:
                prune_previous_model(experiment_path, generation - 1, dry_run=args.dry_run)

    remaining = [g for g in range(horizon) if not generation_is_complete(experiment_path, g)]
    state["horizon"] = horizon
    state["remaining_generations"] = remaining
    save_state(args.work_dir, state)

    print(f"\ncompleted this session: {completed_now or 'none'}")
    if remaining:
        print(f"remaining: {remaining} — re-run this exact command to continue")
        return 20
    print("arm complete: every generation recorded")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path, help="arm config JSON")
    parser.add_argument("--upstream-dir", required=True, type=Path)
    parser.add_argument("--work-dir", required=True, type=Path)
    parser.add_argument("--cuda-device", type=int, default=0,
                        help="physical GPU index; upstream cannot be steered by env var")
    parser.add_argument("--time-budget-seconds", type=float, default=None,
                        help="stop cleanly between generations once this much time is spent")
    parser.add_argument("--prune-models", action="store_true",
                        help="delete each superseded model directory after hashing it")
    parser.add_argument("--shared-generation-zero", type=Path, default=None,
                        help="reuse a generation 0 computed once for both arms")
    parser.add_argument("--stop-after-generation", type=int, default=None,
                        help=(
                            "stop once this generation is complete. Use "
                            "--stop-after-generation 0 to produce the shared generation 0 "
                            "before launching both arms concurrently on separate GPUs."
                        ))
    parser.add_argument("--dry-run", action="store_true",
                        help="print the exact upstream commands without running them")
    args = parser.parse_args()

    try:
        return run_arm(args)
    except (PositiveControlError, MissingUpstreamArtifactError) as error:
        print(f"\npositive-control arm FAILED: {error}", file=sys.stderr)
        return 16


if __name__ == "__main__":
    raise SystemExit(main())
