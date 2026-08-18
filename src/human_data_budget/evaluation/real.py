"""Real held-out evaluation: per-mode NLL from a trained checkpoint.

Replaces ``runner.evaluator.NullEvaluator`` for real chains. Computes mean
negative log-likelihood on the frozen held-out partition, broken down by mode,
which is the input both frozen metrics need and which Stage A never produced --
upstream reports aggregate perplexity with no mode breakdown, which is why
``positive_control_adapter.build_chain_result`` refuses.

``torch`` and ``transformers`` are imported lazily inside the scoring function so
this module stays importable on CPU with no model stack, like the rest of the
real-mode code.

**Orientation warning.** ``evaluation.tail.tail_retention`` computes
``clip(current / reference, 0, 1)`` and documents 1.0 as "preserves all tail
coverage", which is only true if higher scores are better. The toy path satisfies
that, passing ``1.0 - undercoverage``. The metric freeze
(``docs/evaluation/tail_retention_freeze.md`` §3) instead specifies the scores as
**mean held-out NLL**, where lower is better -- under which a degraded model
produces a ratio above 1 that clips to 1.0, reporting perfect retention for the
worst case. See ``FAILURE_LOG.md`` F-011. This module therefore emits the raw
per-mode NLL, which is unambiguous, and offers the orientation-correcting
transform separately rather than choosing silently.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

DEFAULT_MAX_LENGTH = 512


def mode_nll_to_retention_scores(
    mode_nll: Mapping[str, float], *, floor: float = 1e-6
) -> dict[str, float]:
    """Convert mean per-mode NLL into scores ordered so that higher is better.

    ``tail_retention`` clips ``current / reference`` into ``[0, 1]``, so it needs
    scores that fall as the model degrades. NLL rises. The reciprocal restores the
    orientation while leaving the ranking intact.

    This is a presentation transform, not a redefinition of the frozen metric. It is
    exposed separately so a caller must choose it explicitly -- see F-011.
    """
    return {mode: 1.0 / max(float(value), floor) for mode, value in mode_nll.items()}


def score_examples(
    checkpoint_path: str | Path,
    examples: Sequence[tuple[str, str]],
    *,
    max_length: int = DEFAULT_MAX_LENGTH,
    device: str | None = None,
    batch_size: int = 8,
) -> dict[str, Any]:
    """Mean NLL per mode over ``(mode, text)`` pairs, plus the pooled figure.

    Returns raw measurements only. Every value is a mean over non-padding target
    tokens actually scored, and ``tokens_evaluated`` counts those tokens, so the
    figure is comparable to the optimizer-side accounting rather than to a
    document or character estimate.
    """
    # Validate before importing: bad input should fail the same way whether or not a
    # model stack is installed, and CPU callers should not hit an ImportError first.
    if not examples:
        raise ValueError("no examples to score")

    import torch  # noqa: PLC0415 - lazy: CPU-only callers must not need a model stack
    from transformers import AutoModelForCausalLM, AutoTokenizer  # noqa: PLC0415

    resolved = device or ("cuda" if torch.cuda.is_available() else "cpu")
    tokenizer = AutoTokenizer.from_pretrained(str(checkpoint_path))
    model = AutoModelForCausalLM.from_pretrained(str(checkpoint_path)).to(resolved)
    model.eval()

    totals: dict[str, list[float]] = {}
    token_counts: dict[str, int] = {}

    with torch.no_grad():
        for start in range(0, len(examples), batch_size):
            for mode, text in examples[start : start + batch_size]:
                ids = tokenizer(text, return_tensors="pt", truncation=True,
                                max_length=max_length).input_ids.to(resolved)
                if ids.shape[1] < 2:
                    continue
                logits = model(ids).logits[:, :-1, :]
                targets = ids[:, 1:]
                losses = torch.nn.functional.cross_entropy(
                    logits.reshape(-1, logits.size(-1)), targets.reshape(-1),
                    reduction="none",
                )
                totals.setdefault(mode, []).append(float(losses.sum()))
                token_counts[mode] = token_counts.get(mode, 0) + int(targets.numel())

    if not token_counts:
        raise ValueError("every example was too short to score")

    mode_nll = {mode: sum(totals[mode]) / token_counts[mode] for mode in token_counts}
    pooled = sum(sum(v) for v in totals.values()) / sum(token_counts.values())
    return {
        "mode_nll": mode_nll,
        "mode_tokens_evaluated": dict(token_counts),
        "human_nll": pooled,
        "tokens_evaluated": sum(token_counts.values()),
        "checkpoint_path": str(checkpoint_path),
    }
