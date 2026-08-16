"""The run manifest is byte-identical and location-independent across platforms.

Companion to `tests/runner/test_manifest_provenance.py`, which covers what the
`data.partitions` block contains. This file covers two properties of *how* it is
produced, both of which made the same logical run differ by machine:

- the manifest's own bytes, because the auditor records `sha256(run_manifest.json)`
  as the run's provenance hash;
- where partition manifests are resolved from, because they are declared
  repository-relative.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from human_data_budget.runner import manifest as manifest_module
from human_data_budget.runner.manifest import new_manifest, write_manifest_atomic

ROOT = Path(__file__).resolve().parents[2]
TOY_CONFIG = ROOT / "configs" / "experiment" / "toy_cpu.json"

BASE_CONFIG: dict[str, Any] = {
    "run_id": "fixture_portability_test",
    "horizon": 3,
    "chain_seed": 1,
    "lifetime_human_budget": 60,
    "total_optimizer_tokens": 300,
}


# --- manifest bytes are hashed, so they must not depend on the OS -------------


def test_manifest_is_written_with_lf_endings(tmp_path: Path) -> None:
    """`Path.write_text` translates \\n to \\r\\n on Windows.

    Measured before this was fixed: 47 CRLF and 0 bare LF in a manifest written on
    Windows. The auditor records sha256 of this file, so the same logical run
    hashed to two different values depending on the machine that produced it.
    """
    path = tmp_path / "run_manifest.json"
    write_manifest_atomic(new_manifest(BASE_CONFIG, policy_name="joint"), path)

    raw = path.read_bytes()
    assert raw.count(b"\r\n") == 0
    assert raw.count(b"\n") > 0


def test_manifest_round_trips_and_leaves_no_temp_file(tmp_path: Path) -> None:
    path = tmp_path / "nested" / "run_manifest.json"
    built = new_manifest(BASE_CONFIG, policy_name="joint")
    write_manifest_atomic(built, path)

    assert json.loads(path.read_text(encoding="utf-8")) == built
    assert not (path.parent / "run_manifest.json.tmp").exists()


# --- partition sources resolve against the repository, not the caller's cwd ---


def _toy_config() -> dict[str, Any]:
    return json.loads(TOY_CONFIG.read_text(encoding="utf-8"))


def test_provenance_does_not_depend_on_the_working_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A run's recorded provenance must not change with the launch directory.

    Partition manifests are declared repository-relative. Resolved against the
    process working directory, every chain-running test failed when pytest was
    invoked from anywhere but the repository root, and the failure surfaced as an
    uncaught error from `new_manifest` — which `chain.py` calls before the
    try/except that would have written a failure record.
    """
    from_root = new_manifest(_toy_config(), policy_name="joint")

    monkeypatch.chdir(tmp_path)
    from_elsewhere = new_manifest(_toy_config(), policy_name="joint")

    assert from_elsewhere["data"]["partitions"] == from_root["data"]["partitions"]
    assert from_root["data"]["partitions"]["final_human_test"]


def test_project_root_requires_this_packages_source_tree(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A consumer project's pyproject.toml must not be mistaken for this repo's.

    An installed copy under `<consumer>/.venv/Lib/site-packages/human_data_budget`
    sits beneath the consumer's `pyproject.toml`. Accepting that root would resolve
    partition paths against an unrelated project's files and silently place another
    project's examples into this run's provenance block.
    """
    consumer = tmp_path / "consumer_project"
    installed = consumer / ".venv" / "Lib" / "site-packages" / "human_data_budget" / "runner"
    installed.mkdir(parents=True)
    (consumer / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
    fake_module = installed / "manifest.py"
    fake_module.write_text("", encoding="utf-8")

    monkeypatch.setattr(manifest_module, "__file__", str(fake_module))
    assert manifest_module._project_root() is None


def test_project_root_finds_this_repository() -> None:
    assert manifest_module._project_root() == ROOT


def test_an_absolute_source_path_is_used_verbatim(tmp_path: Path) -> None:
    """An absolute declaration must not be re-rooted at the repository."""
    absolute = (ROOT / "src/human_data_budget/runner/fixtures/partitions").resolve()
    config = _toy_config()
    config["data"]["partition_manifests"] = {
        name: str(absolute / f"{name}.jsonl")
        for name in config["data"]["partition_manifests"]
    }

    built = new_manifest(config, policy_name="joint")
    assert set(built["data"]["partitions"]) == set(config["data"]["partition_manifests"])
