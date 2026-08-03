"""The reproduction script uses explicit configs and refuses a missing or dirty state.

Every case below asserts a *specific* exit code, not merely "non-zero". A script that
fails for the wrong reason is as misleading as one that wrongly succeeds, and the exit
codes are the contract that lets a failure be classified in ``FAILURE_LOG.md``.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/reproduce_positive_control.sh"

CONFIG_NAMES = {
    "fully_synthetic": "configs/experiment/positive_control_fully_synthetic.json",
    "human_mixed": "configs/experiment/positive_control_human_mixed.json",
}

UPSTREAM_COMMIT = "feb8511479a2e2dc868e1caf3f63cb99f1fcc746"

EXIT_USAGE = 2
EXIT_DIRTY_TREE = 10
EXIT_UNFROZEN_PROTOCOL = 11
EXIT_BAD_CONFIG = 12
EXIT_BAD_UPSTREAM = 13
EXIT_UNRESOLVED = 15


def _git(repo: Path, *args: str) -> None:
    subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "-c",
            "user.email=test@example.invalid",
            "-c",
            "user.name=test",
            *args,
        ],
        check=True,
        capture_output=True,
    )


def _make_project(tmp_path: Path, *, resolve_identifiers: bool = False) -> Path:
    """Build a minimal committed stand-in for the project repository."""

    project = tmp_path / "project"
    (project / "configs/experiment").mkdir(parents=True)
    shutil.copy(ROOT / "PROTOCOL.md", project / "PROTOCOL.md")

    for relative in CONFIG_NAMES.values():
        config = json.loads((ROOT / relative).read_text(encoding="utf-8"))
        if resolve_identifiers:
            config["model"]["revision"] = "0" * 40
            config["model"]["tokenizer_revision"] = "0" * 40
            config["data"]["revision"] = "1" * 40
            config["data"]["train_manifest_sha256"] = "2" * 64
        (project / relative).write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")

    _git(project, "init", "--quiet")
    _git(project, "add", ".")
    _git(project, "commit", "--quiet", "-m", "fixture project state")
    return project


def _run_script(
    project: Path, *extra: str, upstream: Path | None = None
) -> subprocess.CompletedProcess:
    environment = dict(os.environ)
    environment["PYTHONPATH"] = os.pathsep.join(
        [str(ROOT / "src"), environment.get("PYTHONPATH", "")]
    ).rstrip(os.pathsep)

    command = [
        "bash",
        str(SCRIPT),
        "--repo-root",
        str(project),
        "--upstream-dir",
        str(upstream if upstream is not None else project / "no_such_upstream"),
        "--config-fully-synthetic",
        str(project / CONFIG_NAMES["fully_synthetic"]),
        "--config-human-mixed",
        str(project / CONFIG_NAMES["human_mixed"]),
        "--precheck-only",
        *extra,
    ]
    return subprocess.run(command, capture_output=True, text=True, env=environment)


# ----------------------------------------------------------------------------------
# static contract: the script must not be able to guess what to run
# ----------------------------------------------------------------------------------


def test_script_exists_and_is_executable() -> None:
    assert SCRIPT.is_file()
    assert os.access(SCRIPT, os.X_OK), "the reproduction script must be executable"


def test_script_fails_fast_on_error() -> None:
    assert "set -euo pipefail" in SCRIPT.read_text(encoding="utf-8")


def test_starting_guard_was_replaced() -> None:
    """Week 1 shipped a stub that always exited 3. It must be gone."""

    body = SCRIPT.read_text(encoding="utf-8")
    assert "not implemented in this starting scaffold" not in body
    assert "exit 3" not in body


def test_script_pins_the_protocol_upstream_commit() -> None:
    assert UPSTREAM_COMMIT in SCRIPT.read_text(encoding="utf-8")


def test_script_requires_both_configs_explicitly() -> None:
    body = SCRIPT.read_text(encoding="utf-8")
    assert "--config-fully-synthetic" in body
    assert "--config-human-mixed" in body


def test_script_refuses_to_run_without_arguments() -> None:
    result = subprocess.run(["bash", str(SCRIPT)], capture_output=True, text=True)
    assert result.returncode == EXIT_USAGE
    assert "usage" in result.stderr.lower()


def test_script_refuses_a_partially_specified_invocation(tmp_path: Path) -> None:
    """Naming one arm is not enough: a one-armed comparison is not the protocol."""

    project = _make_project(tmp_path)
    result = subprocess.run(
        [
            "bash",
            str(SCRIPT),
            "--repo-root",
            str(project),
            "--upstream-dir",
            str(tmp_path / "upstream"),
            "--config-fully-synthetic",
            str(project / CONFIG_NAMES["fully_synthetic"]),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == EXIT_USAGE


# ----------------------------------------------------------------------------------
# refusals: dirty scientific state
# ----------------------------------------------------------------------------------


def test_script_refuses_a_dirty_working_tree(tmp_path: Path) -> None:
    project = _make_project(tmp_path, resolve_identifiers=True)
    (project / "uncommitted_scratch.txt").write_text("in progress\n", encoding="utf-8")

    result = _run_script(project)

    assert result.returncode == EXIT_DIRTY_TREE
    assert "dirty" in result.stderr


def test_script_refuses_a_non_repository(tmp_path: Path) -> None:
    not_a_repo = tmp_path / "loose_files"
    (not_a_repo / "configs/experiment").mkdir(parents=True)
    shutil.copy(ROOT / "PROTOCOL.md", not_a_repo / "PROTOCOL.md")
    for relative in CONFIG_NAMES.values():
        shutil.copy(ROOT / relative, not_a_repo / relative)

    result = _run_script(not_a_repo)

    assert result.returncode == EXIT_DIRTY_TREE
    assert "no git repository" in result.stderr


def test_script_refuses_an_unfrozen_protocol(tmp_path: Path) -> None:
    project = _make_project(tmp_path, resolve_identifiers=True)
    protocol = project / "PROTOCOL.md"
    protocol.write_text(
        protocol.read_text(encoding="utf-8")
        + "\nExact upstream commit: TODO(khantushig): decide later\n",
        encoding="utf-8",
    )
    _git(project, "add", ".")
    _git(project, "commit", "--quiet", "-m", "unfreeze the protocol")

    result = _run_script(project)

    assert result.returncode == EXIT_UNFROZEN_PROTOCOL
    assert "TODO(khantushig)" in result.stderr


def test_script_refuses_a_protocol_pinning_a_different_commit(tmp_path: Path) -> None:
    project = _make_project(tmp_path, resolve_identifiers=True)
    protocol = project / "PROTOCOL.md"
    protocol.write_text(
        protocol.read_text(encoding="utf-8").replace(UPSTREAM_COMMIT, "a" * 40), encoding="utf-8"
    )
    _git(project, "add", ".")
    _git(project, "commit", "--quiet", "-m", "repin the protocol")

    result = _run_script(project)

    assert result.returncode == EXIT_UNFROZEN_PROTOCOL
    assert "does not pin upstream commit" in result.stderr


# ----------------------------------------------------------------------------------
# refusals: missing or invalid assets
# ----------------------------------------------------------------------------------


def test_script_refuses_a_missing_config(tmp_path: Path) -> None:
    project = _make_project(tmp_path, resolve_identifiers=True)
    result = _run_script(project, "--config-human-mixed", str(project / "absent.json"))

    assert result.returncode == EXIT_BAD_CONFIG
    assert "missing arm config" in result.stderr


def test_script_refuses_an_invalid_config(tmp_path: Path) -> None:
    project = _make_project(tmp_path, resolve_identifiers=True)
    target = project / CONFIG_NAMES["human_mixed"]
    config = json.loads(target.read_text(encoding="utf-8"))
    del config["chain_seed"]
    target.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    _git(project, "add", ".")
    _git(project, "commit", "--quiet", "-m", "break a config")

    result = _run_script(project)

    assert result.returncode == EXIT_BAD_CONFIG


def test_script_refuses_unresolved_runtime_identifiers(tmp_path: Path) -> None:
    """The committed configs defer revisions; the script must not run past that."""

    project = _make_project(tmp_path, resolve_identifiers=False)
    result = _run_script(project)

    assert result.returncode == EXIT_UNRESOLVED
    assert "resolve_at_runtime" in result.stderr


def test_script_refuses_a_missing_upstream_checkout(tmp_path: Path) -> None:
    project = _make_project(tmp_path, resolve_identifiers=True)
    result = _run_script(project, upstream=tmp_path / "nowhere")

    assert result.returncode == EXIT_BAD_UPSTREAM
    assert "no upstream checkout" in result.stderr


def test_script_refuses_an_upstream_checkout_at_the_wrong_commit(tmp_path: Path) -> None:
    project = _make_project(tmp_path, resolve_identifiers=True)

    wrong_upstream = tmp_path / "wrong_upstream"
    wrong_upstream.mkdir()
    (wrong_upstream / "main.py").write_text("# not the pinned commit\n", encoding="utf-8")
    _git(wrong_upstream, "init", "--quiet")
    _git(wrong_upstream, "add", ".")
    _git(wrong_upstream, "commit", "--quiet", "-m", "some other commit")

    result = _run_script(project, upstream=wrong_upstream)

    assert result.returncode == EXIT_BAD_UPSTREAM
    assert UPSTREAM_COMMIT in result.stderr


@pytest.mark.skipif(
    "POSITIVE_CONTROL_UPSTREAM_DIR" not in os.environ,
    reason=(
        "needs a real upstream checkout at the pinned commit; "
        "set POSITIVE_CONTROL_UPSTREAM_DIR to exercise the dataset preflight"
    ),
)
def test_script_refuses_a_missing_prepared_dataset(tmp_path: Path) -> None:
    project = _make_project(tmp_path, resolve_identifiers=True)
    upstream = Path(os.environ["POSITIVE_CONTROL_UPSTREAM_DIR"])

    result = _run_script(project, upstream=upstream)

    if (upstream / "data/wikitext2/train.json").is_file():
        pytest.skip("upstream dataset is already prepared, nothing to refuse")
    assert result.returncode == 14
    assert "prepared dataset missing" in result.stderr
