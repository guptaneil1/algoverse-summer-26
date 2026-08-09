"""Every artifact reference must carry a hash that matches the bytes on disk."""

import hashlib
import json
from pathlib import Path

import pytest

from human_data_budget.validation.audit import check_artifacts, sha256_file


def write_artifact(directory: Path, name: str, text: str) -> str:
    (directory / name).write_text(text, encoding="utf-8")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def manifest_with(artifacts: list[dict[str, str]]) -> dict[str, object]:
    return {"working_tree_clean": True, "artifacts": artifacts}


def core_files(directory: Path) -> None:
    (directory / "run_manifest.json").write_text("{}", encoding="utf-8")
    (directory / "chain_result.json").write_text("{}", encoding="utf-8")


def failed_codes(checks) -> set[str]:
    return {check.code for check in checks if not check.passed}


def test_sha256_matches_hashlib(tmp_path: Path) -> None:
    target = tmp_path / "blob.bin"
    target.write_bytes(b"some-bytes")
    assert sha256_file(target) == hashlib.sha256(b"some-bytes").hexdigest()


def test_sha256_is_stable_across_calls(tmp_path: Path) -> None:
    target = tmp_path / "blob.bin"
    target.write_bytes(b"repeatable")
    assert sha256_file(target) == sha256_file(target)


def test_large_file_hashes_in_blocks(tmp_path: Path) -> None:
    """The reader streams in 64 KiB blocks; a larger file must still be exact."""
    payload = b"x" * (64 * 1024 * 3 + 17)
    target = tmp_path / "large.bin"
    target.write_bytes(payload)
    assert sha256_file(target) == hashlib.sha256(payload).hexdigest()


def test_matching_checkpoint_hash_passes(tmp_path: Path) -> None:
    core_files(tmp_path)
    digest = write_artifact(tmp_path, "checkpoint.pt", "weights")
    checks = check_artifacts(tmp_path, manifest_with([{"path": "checkpoint.pt", "sha256": digest}]))
    assert not failed_codes(checks)


def test_tampered_checkpoint_is_caught(tmp_path: Path) -> None:
    core_files(tmp_path)
    digest = write_artifact(tmp_path, "checkpoint.pt", "weights")
    (tmp_path / "checkpoint.pt").write_text("tampered", encoding="utf-8")

    checks = check_artifacts(tmp_path, manifest_with([{"path": "checkpoint.pt", "sha256": digest}]))
    assert "ARTIFACT_HASH_MISMATCH" in failed_codes(checks)


def test_every_reference_type_is_hash_checked(tmp_path: Path) -> None:
    core_files(tmp_path)
    artifacts = []
    for name, text in (
        ("checkpoint.pt", "weights"),
        ("generated_data.jsonl", '{"text": "synthetic"}'),
        ("metrics.json", json.dumps({"human_nll": 1.0})),
        ("policy_config.json", json.dumps({"name": "joint"})),
    ):
        artifacts.append({"path": name, "sha256": write_artifact(tmp_path, name, text)})

    checks = check_artifacts(tmp_path, manifest_with(artifacts))
    assert not failed_codes(checks)

    (tmp_path / "metrics.json").write_text(json.dumps({"human_nll": 99.0}), encoding="utf-8")
    recheck = check_artifacts(tmp_path, manifest_with(artifacts))
    assert "ARTIFACT_HASH_MISMATCH" in failed_codes(recheck)


def test_referenced_but_absent_artifact_is_caught(tmp_path: Path) -> None:
    core_files(tmp_path)
    checks = check_artifacts(tmp_path, manifest_with([{"path": "ghost.pt", "sha256": "0" * 64}]))
    assert "ARTIFACT_MISSING" in failed_codes(checks)


def test_reference_without_a_hash_is_a_limitation(tmp_path: Path) -> None:
    core_files(tmp_path)
    write_artifact(tmp_path, "notes.txt", "unhashed")
    checks = check_artifacts(tmp_path, manifest_with([{"path": "notes.txt"}]))
    assert "LIMIT_MISSING_OPTIONAL_ARTIFACT" in failed_codes(checks)


def test_dirty_working_tree_is_caught(tmp_path: Path) -> None:
    core_files(tmp_path)
    manifest = {"working_tree_clean": False, "artifacts": []}
    assert "COMMIT_DIRTY" in failed_codes(check_artifacts(tmp_path, manifest))


def test_unknown_clean_state_is_caught(tmp_path: Path) -> None:
    core_files(tmp_path)
    assert "COMMIT_DIRTY" in failed_codes(check_artifacts(tmp_path, {"artifacts": []}))


def test_missing_file_cannot_be_hashed(tmp_path: Path) -> None:
    with pytest.raises(OSError):
        sha256_file(tmp_path / "absent.bin")
