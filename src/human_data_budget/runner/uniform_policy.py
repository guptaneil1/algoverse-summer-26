"""Runner-owned uniform policy: a mode-blind allocation mock.

`docs/TEAM.md` lists Khantushig's permanent mock inputs as "toy corpus, uniform
policy, and null evaluator". The toy corpus and null evaluator exist; this
supplies the third.

**Why the runner owns a policy at all.** `docs/TEAM.md`'s independence rule says
no member may need another's current branch to finish their own work. Runner
tests that used `policies/` would couple orchestration correctness to Aarav's
in-flight scientific decisions — and `FAILURE_LOG.md` F-001 shows exactly how
that goes wrong: two of the four scientific policies are currently degenerate, so
a runner test built on them could pass for reasons that have nothing to do with
the runner.

``UniformPolicy`` is deliberately the dullest correct policy: it spends the same
number of tokens every generation and ignores mode entirely. It has no scientific
opinion, so when a runner test moves, the runner moved.

**This is not a baseline.** `RandomPolicy` and `ScheduleOnlyPolicy` in
``policies/`` are the scientific comparators. This class must never appear in a
treatment comparison, and ``name`` is ``"uniform_fixture"`` so it is obvious in
any manifest if it ever does.

Dependency direction (``docs/ARCHITECTURE.md``): ``runner/`` may import from
``policies/``; the reverse is forbidden. Importing ``policies.base`` here is
therefore allowed, and keeps this class a genuine ``Policy``.
"""

from __future__ import annotations

from human_data_budget.models import Allocation, PolicyState
from human_data_budget.policies.base import Policy, build_allocation, select_with_budget


class UniformPolicy(Policy):
    """Spend an equal share of the lifetime budget in every remaining generation."""

    name = "uniform_fixture"

    def __init__(self, horizon: int, lifetime_human_budget: int) -> None:
        if horizon <= 0:
            raise ValueError("horizon must be positive")
        if lifetime_human_budget < 0:
            raise ValueError("lifetime_human_budget must not be negative")
        self.horizon = horizon
        self.lifetime_human_budget = lifetime_human_budget

    def allocate(self, state: PolicyState, seed: int) -> Allocation:
        """Allocate this generation's even share, mode-blind and seed-independent.

        The per-generation share is recomputed from *remaining* budget and
        *remaining* generations rather than fixed up front. If an earlier
        generation underspends — because no candidate was small enough to fit —
        the shortfall is redistributed instead of silently vanishing, which keeps
        the lifetime total exact.

        Candidates are taken in stable ``example_id`` order. Nothing consults
        ``mode_statistics`` or ``undercoverage_score``: selection must not depend
        on mode, or this stops being a neutral control.
        """
        remaining_generations = max(1, self.horizon - state.generation)
        share = state.remaining_human_tokens // remaining_generations

        # Final generation spends whatever is left, so integer division cannot
        # strand tokens at the end of the chain.
        if remaining_generations == 1:
            share = state.remaining_human_tokens

        ordered = sorted(state.candidates, key=lambda candidate: candidate.example_id)
        presentations = select_with_budget(ordered, min(share, state.remaining_human_tokens))
        return build_allocation(
            name=self.name,
            state=state,
            seed=seed,
            presentations=presentations,
            scores={},
        )
