"""Immutable inputs regenerate the same aggregate; bad inputs are rejected."""

import importlib.util
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _load_module():
    spec = importlib.util.spec_from_file_location(
        "aggregate_chain_results", ROOT / "scripts" / "aggregate_chain_results.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


agg = _load_module()

ChainFactory = Callable[..., dict[str, Any]]
WriteChain = Callable[..., Path]


def test_one_row_per_chain(chain_payload: ChainFactory, write_chain: WriteChain) -> None:
    paths = [
        write_chain(chain_payload("joint-1", "joint", 1)),
        write_chain(chain_payload("joint-2", "joint", 2)),
    ]
    result = agg.aggregate(paths)

    assert result["policies"]["joint"]["chain_count"] == 2
    assert result["policies"]["joint"]["chain_seeds"] == [1, 2]
    assert result["chains_supplied"] == 2


def test_same_inputs_regenerate_the_same_aggregate(
    chain_payload: ChainFactory, write_chain: WriteChain
) -> None:
    paths = [
        write_chain(chain_payload("joint-1", "joint", 1)),
        write_chain(chain_payload("random-1", "random", 1)),
    ]
    assert agg.aggregate(paths) == agg.aggregate(paths)


def test_input_hashes_are_recorded(
    chain_payload: ChainFactory, write_chain: WriteChain
) -> None:
    path = write_chain(chain_payload("joint-1", "joint", 1))
    result = agg.aggregate([path])

    record = result["inputs"][0]
    assert record["sha256"] == agg.sha256_file(path)
    assert record["run_id"] == "joint-1"


def test_duplicate_run_ids_are_rejected(
    chain_payload: ChainFactory, write_chain: WriteChain
) -> None:
    paths = [
        write_chain(chain_payload("joint-1", "joint", 1), "a.json"),
        write_chain(chain_payload("joint-1", "joint", 2), "b.json"),
    ]
    with pytest.raises(agg.RejectedInput, match="duplicate run_id"):
        agg.aggregate(paths)


def test_mismatched_budget_ids_are_rejected(
    chain_payload: ChainFactory, write_chain: WriteChain
) -> None:
    paths = [
        write_chain(chain_payload("joint-1", "joint", 1, budget_id="budget-a")),
        write_chain(chain_payload("joint-2", "joint", 2, budget_id="budget-b")),
    ]
    with pytest.raises(agg.RejectedInput, match="multiple budget ids"):
        agg.aggregate(paths)


def test_schema_invalid_input_is_rejected(tmp_path: Path) -> None:
    broken = tmp_path / "broken.json"
    broken.write_text('{"schema_version": "1.0"}', encoding="utf-8")
    with pytest.raises(agg.RejectedInput, match="schema invalid"):
        agg.aggregate([broken])


def test_unparseable_input_is_rejected(tmp_path: Path) -> None:
    broken = tmp_path / "broken.json"
    broken.write_text("{not json", encoding="utf-8")
    with pytest.raises(agg.RejectedInput, match="not valid JSON"):
        agg.aggregate([broken])


def test_empty_input_is_rejected() -> None:
    with pytest.raises(agg.RejectedInput, match="no chain results"):
        agg.aggregate([])


def test_invalid_chain_is_excluded_but_still_listed(
    chain_payload: ChainFactory, write_chain: WriteChain
) -> None:
    paths = [
        write_chain(chain_payload("joint-1", "joint", 1)),
        write_chain(
            chain_payload(
                "joint-2", "joint", 2, valid=False, exclusion_reason="budget mismatch"
            )
        ),
    ]
    result = agg.aggregate(paths)

    assert result["chains_included"] == 1
    assert result["chains_excluded"] == 1
    excluded = [record for record in result["inputs"] if not record["included"]]
    assert excluded[0]["exclusion_reason"] == "budget mismatch"


def test_classification_file_overrides_the_valid_flag(
    chain_payload: ChainFactory, write_chain: WriteChain, tmp_path: Path
) -> None:
    paths = [
        write_chain(chain_payload("joint-1", "joint", 1)),
        write_chain(chain_payload("joint-2", "joint", 2)),
    ]
    classifications = tmp_path / "classifications.csv"
    classifications.write_text(
        "run_id,classification\njoint-1,valid\njoint-2,invalid\n", encoding="utf-8"
    )

    result = agg.aggregate(paths, classifications=agg.load_classifications(classifications))
    assert result["chains_included"] == 1
    assert result["policies"]["joint"]["chain_count"] == 1


def test_valid_with_limitation_is_eligible(
    chain_payload: ChainFactory, write_chain: WriteChain, tmp_path: Path
) -> None:
    path = write_chain(chain_payload("joint-1", "joint", 1))
    classifications = tmp_path / "classifications.csv"
    classifications.write_text(
        "run_id,classification\njoint-1,valid_with_limitation\n", encoding="utf-8"
    )

    result = agg.aggregate([path], classifications=agg.load_classifications(classifications))
    assert result["chains_included"] == 1


def test_single_generation_chain_is_rejected_for_curve_summary(
    chain_payload: ChainFactory, write_chain: WriteChain
) -> None:
    path = write_chain(chain_payload("joint-1", "joint", 1, nlls=(3.0,), tails=(0.9,)))
    with pytest.raises(agg.RejectedInput, match="at least two generations"):
        agg.aggregate([path])


def test_unit_of_analysis_is_recorded(
    chain_payload: ChainFactory, write_chain: WriteChain
) -> None:
    path = write_chain(chain_payload("joint-1", "joint", 1))
    assert "chain" in agg.aggregate([path])["unit_of_analysis"]


def test_label_defaults_to_provisional(
    chain_payload: ChainFactory, write_chain: WriteChain
) -> None:
    path = write_chain(chain_payload("joint-1", "joint", 1))
    assert agg.aggregate([path])["label"] == "provisional"


def test_nll_auc_is_trapezoidal(chain_payload: ChainFactory) -> None:
    payload = chain_payload("joint-1", "joint", 1, nlls=(2.0, 4.0), tails=(0.9, 0.8))
    assert agg.nll_auc(payload) == pytest.approx(3.0)
