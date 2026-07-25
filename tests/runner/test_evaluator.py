from pathlib import Path

from human_data_budget.runner.evaluator import NullEvaluator, load_toy_eval_corpus
from human_data_budget.runner.schema import validate_json

ROOT = Path(__file__).resolve().parents[2]


def test_load_toy_eval_corpus_has_expected_shape() -> None:
    corpus = load_toy_eval_corpus()
    assert "target_log_probabilities" in corpus
    assert "reference_mode_scores" in corpus
    assert len(corpus["target_log_probabilities"]) > 0


def test_null_evaluator_output_matches_schema() -> None:
    corpus = load_toy_eval_corpus()
    evaluator = NullEvaluator()
    result = evaluator.evaluate(
        run_id="fixture_run",
        generation=0,
        checkpoint_sha256="fixture-checkpoint",
        evaluation_manifest_sha256="fixture-manifest",
        current_mode_scores={"common": 0.9, "tail": 0.8},
        reference_mode_scores=corpus["reference_mode_scores"],
        tail_modes={"tail"},
        target_log_probabilities=corpus["target_log_probabilities"],
    )
    validate_json(result, ROOT / "schemas/evaluation.schema.json")


def test_null_evaluator_is_deterministic() -> None:
    corpus = load_toy_eval_corpus()
    evaluator = NullEvaluator()
    kwargs = dict(
        run_id="fixture_run",
        generation=1,
        checkpoint_sha256="fixture-checkpoint",
        evaluation_manifest_sha256="fixture-manifest",
        current_mode_scores={"common": 0.9, "tail": 0.8},
        reference_mode_scores=corpus["reference_mode_scores"],
        tail_modes={"tail"},
        target_log_probabilities=corpus["target_log_probabilities"],
    )
    assert evaluator.evaluate(**kwargs) == evaluator.evaluate(**kwargs)
