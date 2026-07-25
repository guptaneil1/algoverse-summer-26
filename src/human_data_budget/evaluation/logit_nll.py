"""NLL from raw logits with numerically stable log-sum-exp and padding exclusion."""

from __future__ import annotations

import math
from collections.abc import Sequence


def token_nll(logits: Sequence[float], token_id: int) -> float:
    """Cross-entropy loss for a single token position from raw (unnormalized) logits."""
    max_l = max(logits)
    log_sum_exp = max_l + math.log(sum(math.exp(v - max_l) for v in logits))
    return log_sum_exp - logits[token_id]


def sequence_nll(
    logits_seq: Sequence[Sequence[float]],
    token_ids: Sequence[int],
    padding_id: int = 0,
) -> tuple[float, int]:
    """Sum NLL and non-padding token count for one example.

    Returns (total_nll, count) so callers can compute a token-weighted mean
    across examples without double-averaging.
    """
    total = 0.0
    count = 0
    for logit_vec, tid in zip(logits_seq, token_ids, strict=False):
        if tid == padding_id:
            continue
        total += token_nll(logit_vec, tid)
        count += 1
    return total, count
