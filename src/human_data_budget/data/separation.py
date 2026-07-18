"""Partition-separation validation."""

from collections.abc import Iterable


def assert_disjoint(partitions: dict[str, Iterable[str]]) -> None:
    """Raise when any stable ID or content hash occurs in two partitions."""

    seen: dict[str, str] = {}
    for partition_name, values in partitions.items():
        for value in values:
            previous = seen.get(value)
            if previous is not None:
                raise ValueError(
                    f"overlap detected: {value!r} appears in {previous!r} and {partition_name!r}"
                )
            seen[value] = partition_name
