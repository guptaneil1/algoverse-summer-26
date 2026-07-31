"""Null evaluator: a runner-owned evaluation stand-in.

Satisfies ``docs/interfaces/evaluation.md`` and
``schemas/evaluation.schema.json`` without a real checkpoint or held-out
corpus, so runner orchestration can be exercised end to end independently of
Neil's real evaluation implementation. Evaluation never calls policy code
and never touches final-test data.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from human_data_budget.evaluation.nll import negative_log_likelihood
from human_data_budget.evaluation.tail import tail_retention

_FIXTURE_PATH = Path(__file__).parent / "fixtures" / "toy_eval_corpus.json"


def load_toy_eval_corpus(path: Path = _FIXTURE_PATH) -> dict[str, Any]:
    """Return the runner-owned frozen held-out fixture (fake logits, mode scores)."""

    return json.loads(path.read_text(encoding="utf-8"))


class NullEvaluator:
    """A fixed, non-learned evaluator standing in for a real checkpoint evaluation."""

    def evaluate(
        self,
        *,
        run_id: str,
        generation: int,
        checkpoint_sha256: str,
        evaluation_manifest_sha256: str,
        current_mode_scores: dict[str, float],
        reference_mode_scores: dict[str, float],
        tail_modes: set[str],
        target_log_probabilities: list[float],
    ) -> dict[str, Any]:
        """Return a schema-valid evaluation result computed from fixture inputs."""

        human_nll = negative_log_likelihood(target_log_probabilities)
        retention = tail_retention(current_mode_scores, reference_mode_scores, tail_modes)
        return {
            "schema_version": "1.0",
            "run_id": run_id,
            "generation": generation,
            "human_nll": human_nll,
            "tail_retention": {
                "primary": retention,
                "nll_gap": 0.0,
            },
            "tokens_evaluated": len(target_log_probabilities),
            "evaluation_manifest_sha256": evaluation_manifest_sha256,
            "checkpoint_sha256": checkpoint_sha256,
        }
