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


# --- repetition: an example presented across multiple epochs ---


def test_repeated_presentation_across_epochs_accumulates() -> None:
    """If an example is presented in N epochs it must contribute N x its count."""
    single_epoch = [batch()]
    three_epochs = [batch(), batch(), batch()]
    assert consumed_tokens(three_epochs) == consumed_tokens(single_epoch) * 3
    single_human = consumed_tokens(single_epoch, origin="human")
    assert consumed_tokens(three_epochs, origin="human") == single_human * 3


def test_repeated_identical_batch_object_still_counted_each_presentation() -> None:
    """Re-presenting the exact same batch object N times counts N separate presentations."""
    one = batch()
    assert consumed_tokens([one, one, one]) == 15


# --- batching: multiple batches of different shapes combine correctly ---


def test_multiple_differently_shaped_batches_sum_independently() -> None:
    batches = [
        {"attention_mask": [[1, 1, 0]], "origins": ["human"]},
        {"attention_mask": [[1, 1, 1, 1], [0, 0, 1, 1]], "origins": ["synthetic", "human"]},
        {"attention_mask": [[1]], "origins": ["human"]},
    ]
    assert consumed_tokens(batches) == 2 + (4 + 2) + 1
    assert consumed_tokens(batches, origin="human") == 2 + 2 + 1


# --- gradient accumulation: micro-batch grouping must not change the total ---


def test_gradient_accumulation_split_matches_equivalent_combined_batch() -> None:
    """Splitting one logical batch into accumulation micro-batches must not change the count.

    Gradient accumulation changes when the optimizer step happens, not how
    many examples were presented, so regrouping the same examples into
    smaller micro-batches must leave consumed_tokens unchanged.
    """
    combined = {
        "attention_mask": [[1, 1, 1, 0], [1, 1, 0, 0], [1, 1, 1, 1]],
        "origins": ["human", "synthetic", "human"],
    }
    micro_batches = [
        {"attention_mask": [[1, 1, 1, 0]], "origins": ["human"]},
        {"attention_mask": [[1, 1, 0, 0]], "origins": ["synthetic"]},
        {"attention_mask": [[1, 1, 1, 1]], "origins": ["human"]},
    ]
    assert consumed_tokens([combined]) == consumed_tokens(micro_batches)
    combined_human = consumed_tokens([combined], origin="human")
    assert combined_human == consumed_tokens(micro_batches, origin="human")


# --- resume: accounting must split additively across a crash/resume boundary ---


def test_accounting_splits_additively_across_a_resume_boundary() -> None:
    """Pre-crash batches plus post-resume batches must equal one uninterrupted run's count.

    consumed_tokens has no state of its own; resume-safety depends entirely on
    the caller never re-passing a batch that was already counted before the
    crash. This fixture simulates that contract directly: an uninterrupted
    five-batch run split at an arbitrary point into "already accounted before
    the crash" and "presented after resume" must sum to the uninterrupted total.
    """
    all_batches = [batch(), batch(), batch(), batch(), batch()]
    crash_after = 2
    before_crash = all_batches[:crash_after]
    after_resume = all_batches[crash_after:]

    uninterrupted_total = consumed_tokens(all_batches)
    resumed_total = consumed_tokens(before_crash) + consumed_tokens(after_resume)
    assert resumed_total == uninterrupted_total

    uninterrupted_human = consumed_tokens(all_batches, origin="human")
    resumed_human = consumed_tokens(before_crash, origin="human")
    resumed_human += consumed_tokens(after_resume, origin="human")
    assert resumed_human == uninterrupted_human


def test_resume_boundary_holds_at_every_split_point() -> None:
    """The additive split property must hold no matter where the crash lands."""
    all_batches = [batch() for _ in range(6)]
    uninterrupted_total = consumed_tokens(all_batches)
    for split_point in range(len(all_batches) + 1):
        before, after = all_batches[:split_point], all_batches[split_point:]
        assert consumed_tokens(before) + consumed_tokens(after) == uninterrupted_total


def test_matched_budgets_hold_across_a_resume_boundary() -> None:
    """validate_matched_budgets gives the same answer whether or not a run was interrupted."""
    uninterrupted = {"joint": [batch(), batch()], "random": [batch(), batch()]}
    resumed = {
        "joint": [batch()] + [batch()],  # pre-crash batch, then post-resume batch
        "random": [batch(), batch()],
    }
    assert validate_matched_budgets(uninterrupted) == validate_matched_budgets(resumed)
