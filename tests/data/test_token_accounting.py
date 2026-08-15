import pytest

from human_data_budget.data.token_accounting import consumed_tokens, validate_matched_budgets


def batch() -> dict[str, object]:
    return {
        "attention_mask": [[1, 1, 1, 0], [1, 1, 0, 0]],
        "origins": ["human", "synthetic"],
    }


def test_counts_realized_non_padding_tokens() -> None:
    assert consumed_tokens([batch()]) == 5
    assert consumed_tokens([batch()], origin="human") == 3


def test_matched_conditions_pass() -> None:
    assert validate_matched_budgets({"joint": [batch()], "random": [batch()]}) == (3, 5)


def test_mismatched_conditions_fail() -> None:
    short = {"attention_mask": [[1]], "origins": ["human"]}
    with pytest.raises(ValueError, match="budget mismatch"):
        validate_matched_budgets({"joint": [batch()], "random": [short]})


# ---------------------------------------------------------------------------
# WEEK_2.md, Neil: "Test token accounting under padding, repetition, batching,
# gradient accumulation, and resume fixtures."
#
# Padding is covered by test_counts_realized_non_padding_tokens above (the
# attention mask carries zeros). The four remaining conditions follow.
# ---------------------------------------------------------------------------


def example(length: int, origin: str = "human", pad_to: int | None = None) -> tuple[list[int], str]:
    """One example's attention-mask row and origin label."""
    mask = [1] * length
    if pad_to is not None:
        mask += [0] * (pad_to - length)
    return mask, origin


def pack(rows: list[tuple[list[int], str]]) -> dict[str, object]:
    """Assemble mask/origin rows into one batch record."""
    return {
        "attention_mask": [mask for mask, _ in rows],
        "origins": [origin for _, origin in rows],
    }


def test_repeated_presentation_is_counted_once_per_presentation() -> None:
    """PROTOCOL.md §3: presenting a human example three times costs three times.

    This is the invariant that stops a policy looking cheap by replaying a small
    human archive across epochs.
    """
    single = pack([example(10)])
    replayed = [single, single, single]

    assert consumed_tokens([single], origin="human") == 10
    assert consumed_tokens(replayed, origin="human") == 30
    assert consumed_tokens(replayed) == 30


def test_epoch_replay_breaks_budget_matching() -> None:
    """A condition that replays its archive must fail matching against one that does not."""
    single = pack([example(10)])
    with pytest.raises(ValueError, match="budget mismatch"):
        validate_matched_budgets(
            {"schedule_only": [single], "selection_only": [single, single]}
        )


def test_batching_does_not_change_totals() -> None:
    """The same examples counted as one large batch or several small ones agree."""
    rows = [example(4), example(6, "synthetic"), example(5), example(3, "synthetic")]

    one_batch = [pack(rows)]
    two_batches = [pack(rows[:2]), pack(rows[2:])]
    four_batches = [pack([row]) for row in rows]

    assert consumed_tokens(one_batch) == 18
    assert consumed_tokens(two_batches) == 18
    assert consumed_tokens(four_batches) == 18

    for batches in (one_batch, two_batches, four_batches):
        assert consumed_tokens(batches, origin="human") == 9


def test_ragged_batching_with_padding_agrees_with_unpadded() -> None:
    """Padding to a common width must not inflate the count."""
    unpadded = [pack([example(4)]), pack([example(7)])]
    padded = [pack([example(4, pad_to=7), example(7, pad_to=7)])]

    assert consumed_tokens(unpadded) == consumed_tokens(padded) == 11


def test_gradient_accumulation_counts_every_micro_batch() -> None:
    """Micro-batches accumulated into one optimizer step are all consumed.

    Accumulation changes when the optimizer steps, not how many tokens were
    presented. Counting per step rather than per micro-batch would undercount
    the budget by the accumulation factor.
    """
    micro = pack([example(8)])
    accumulation_steps = 4
    step_batches = [micro] * accumulation_steps

    assert consumed_tokens(step_batches) == 32
    assert consumed_tokens(step_batches, origin="human") == 32


def test_accumulation_matched_against_equivalent_large_batch() -> None:
    """Four micro-batches of 8 and one batch of four 8-token rows are equal."""
    accumulated = [pack([example(8)]) for _ in range(4)]
    single_large = [pack([example(8) for _ in range(4)])]

    assert validate_matched_budgets(
        {"accumulated": accumulated, "single_large": single_large}
    ) == (32, 32)


def test_resume_preserves_exact_totals() -> None:
    """Tokens before and after a checkpoint resume sum to the uninterrupted total.

    PROTOCOL.md §3 requires resume equivalence. Double-counting the batch that
    straddles the checkpoint, or dropping it, both corrupt the lifetime budget.

    The resumed run is rebuilt from independently constructed batch records
    rather than sliced out of ``full_run``. Slicing and re-concatenating the same
    list is the identity operation, so the assertion would hold no matter how
    ``consumed_tokens`` behaved.
    """
    full_run = [
        pack([example(5), example(4, "synthetic")]),
        pack([example(6), example(3, "synthetic")]),
        pack([example(2), example(7, "synthetic")]),
    ]

    # Independently reconstructed: same content, different objects.
    before_checkpoint = [
        pack([example(5), example(4, "synthetic")]),
        pack([example(6), example(3, "synthetic")]),
    ]
    after_resume = [pack([example(2), example(7, "synthetic")])]
    resumed_run = before_checkpoint + after_resume

    assert all(
        original is not resumed
        for original, resumed in zip(full_run, resumed_run, strict=True)
    ), "the resumed run must not alias the uninterrupted run"

    assert consumed_tokens(resumed_run) == consumed_tokens(full_run) == 27
    assert consumed_tokens(resumed_run, origin="human") == 13
    assert validate_matched_budgets(
        {"uninterrupted": full_run, "resumed": resumed_run}
    ) == (13, 27)


# ---------------------------------------------------------------------------
# Regression tests for defects found by adversarial review on 2026-08-15.
# ---------------------------------------------------------------------------


def test_single_pass_iterables_do_not_silently_pass_matching() -> None:
    """Budget matching counted each condition twice, exhausting generators.

    The second count then returned zero, so two conditions with genuinely
    different budgets both reported ``(n, 0)`` and compared equal — the fairness
    constraint passed vacuously on exactly the input shape a streaming pipeline
    would supply.
    """
    big = [pack([example(10), example(10, "synthetic")])]
    small = [pack([example(1), example(1, "synthetic")])]

    with pytest.raises(ValueError, match="budget mismatch"):
        validate_matched_budgets({"big": iter(big), "small": iter(small)})


def test_generator_inputs_produce_the_same_totals_as_lists() -> None:
    batches = [pack([example(4)]), pack([example(6)])]
    assert validate_matched_budgets(
        {"a": iter(list(batches)), "b": iter(list(batches))}
    ) == (10, 10)


def test_a_single_condition_cannot_match_itself() -> None:
    """One condition compared nothing and still reported success."""
    with pytest.raises(ValueError, match="at least two"):
        validate_matched_budgets({"only": [pack([example(5)])]})


def test_no_conditions_is_rejected() -> None:
    with pytest.raises(ValueError, match="at least two"):
        validate_matched_budgets({})


def test_malformed_mask_is_caught_even_on_filtered_out_rows() -> None:
    """Mask validation used to sit inside the origin filter.

    A corrupt synthetic row was therefore invisible to a human-origin count, so
    the human budget could be certified from a batch known to be malformed.
    """
    corrupt = {
        "attention_mask": [[1, 1], [1, 7]],
        "origins": ["human", "synthetic"],
    }
    with pytest.raises(ValueError, match="must be zero or one"):
        consumed_tokens([corrupt], origin="human")


def test_resume_that_replays_a_batch_is_detected() -> None:
    """Replaying the checkpoint batch on resume must break budget equality."""
    full_run = [pack([example(5)]), pack([example(6)]), pack([example(2)])]
    double_counted = full_run[:2] + full_run[1:]

    assert consumed_tokens(double_counted) > consumed_tokens(full_run)
    with pytest.raises(ValueError, match="budget mismatch"):
        validate_matched_budgets({"clean": full_run, "resumed": double_counted})


def test_resume_that_drops_a_batch_is_detected() -> None:
    """Losing work on resume must also break budget equality, not pass silently."""
    full_run = [pack([example(5)]), pack([example(6)]), pack([example(2)])]
    dropped = [full_run[0], full_run[2]]

    assert consumed_tokens(dropped) < consumed_tokens(full_run)
    with pytest.raises(ValueError, match="budget mismatch"):
        validate_matched_budgets({"clean": full_run, "resumed": dropped})
