"""Frozen fixture implementation of joint time-and-mode allocation."""

from __future__ import annotations

import math
import random

from human_data_budget.models import Allocation, PolicyState
from human_data_budget.policies.base import (
    Policy,
    build_allocation,
    select_with_budget,
)


class JointPolicy(Policy):
    """Adapt both spending time and candidate selection."""

    name = "joint"

    def __init__(
        self,
        horizon: int,
        base_per_generation_budget: int,
        *,
        low_urgency_threshold: float = 0.25,
        high_urgency_threshold: float = 0.50,
    ) -> None:
        if horizon <= 0:
            raise ValueError("horizon must be positive")

        if base_per_generation_budget <= 0:
            raise ValueError(
                "base_per_generation_budget must be positive"
            )

        if not 0.0 <= low_urgency_threshold < high_urgency_threshold:
            raise ValueError("urgency thresholds must be ordered")

        self.horizon = horizon
        self.base_per_generation_budget = (
            base_per_generation_budget
        )
        self.maximum_generation_budget = (
            2 * base_per_generation_budget
        )
        self.low_urgency_threshold = low_urgency_threshold
        self.high_urgency_threshold = high_urgency_threshold

    def _scores(
        self,
        state: PolicyState,
    ) -> dict[str, float]:
        scores: dict[str, float] = {}

        for candidate in state.candidates:
            score = state.mode_statistics.get(candidate.mode, 0.0)

            if not math.isfinite(score):
                raise ValueError(
                    "joint policy received a nonfinite mode score"
                )

            scores[candidate.example_id] = max(
                0.0,
                min(1.0, score),
            )

        return scores

    def _desired_budget(
        self,
        urgency: float,
    ) -> int:
        if urgency < self.low_urgency_threshold:
            return 0

        if urgency < self.high_urgency_threshold:
            return self.base_per_generation_budget

        return self.maximum_generation_budget

    def _feasible_budget(
        self,
        state: PolicyState,
        desired_budget: int,
    ) -> int:
        future_generation_count = max(
            0,
            self.horizon - state.generation - 1,
        )

        lower_bound = max(
            0,
            state.remaining_human_tokens
            - self.maximum_generation_budget
            * future_generation_count,
        )

        upper_bound = min(
            self.maximum_generation_budget,
            state.remaining_human_tokens,
        )

        return max(
            lower_bound,
            min(desired_budget, upper_bound),
        )

    def allocate(
        self,
        state: PolicyState,
        seed: int,
    ) -> Allocation:
        scores = self._scores(state)

        monitoring_available = bool(state.mode_statistics)

        if monitoring_available:
            urgency = max(state.mode_statistics.values())
            desired_budget = self._desired_budget(urgency)

            ordered = sorted(
                state.candidates,
                key=lambda candidate: (
                    -scores[candidate.example_id],
                    candidate.example_id,
                ),
            )
        else:
            desired_budget = self.base_per_generation_budget
            ordered = list(state.candidates)
            random.Random(seed).shuffle(ordered)

        budget = self._feasible_budget(
            state,
            desired_budget,
        )

        presentations = select_with_budget(
            list(ordered),
            budget,
        )

        return build_allocation(
            name=self.name,
            state=state,
            seed=seed,
            presentations=presentations,
            scores=scores,
        )