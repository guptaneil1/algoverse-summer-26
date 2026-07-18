import pytest

from human_data_budget.data.hashing import content_hash
from human_data_budget.data.separation import assert_disjoint


def test_normalized_content_hash_is_stable() -> None:
    assert content_hash("hello   world") == content_hash("hello world")


def test_disjoint_partitions_pass() -> None:
    assert_disjoint({"train": ["a", "b"], "test": ["c"]})


def test_overlap_is_blocking() -> None:
    with pytest.raises(ValueError, match="overlap detected"):
        assert_disjoint({"prompts": ["a"], "final_test": ["a"]})
