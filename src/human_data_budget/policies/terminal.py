"""Terminal budget reconciliation: every policy spends its full lifetime budget.

``FAILURE_LOG.md`` F-015: with per-generation allowances and indivisible candidates,
policies strand different amounts of budget. Measured on the frozen pilot grid,
`joint` ended 641,002 tokens spent against `schedule_only`'s ~517,000 -- a 24% gap
at every seed, from the same 750,000 ceiling. `PROTOCOL.md` §4 requires equal
lifetime human-origin spend, so that contrast is confounded by data quantity.

**What this changes, and what it does not.** The research question is *when* a fixed
budget is spent and *which* modes it targets -- not how much is spent. A policy that
strands 31% of its budget is not answering that question, it is answering a
different one with less data. At the final generation the allowance is therefore
raised to the entire remaining lifetime budget, so every arm converges on the same
total.

Each policy still chooses **which** examples with its own rule: the top-up runs
through the same policy object, not a shared fallback. Timing is unchanged for
every generation but the last.

**Exact equality remains impossible.** Candidates are indivisible and average 4,082
tokens, so an arm stops when the next one does not fit. The residual is bounded by
one candidate rather than by an accumulated per-generation remainder -- the
difference between a ~2% spread and the measured 24%.

``no_rescue`` is exempt. It spends nothing by definition, and topping it up would
convert the control arm into a random-rescue arm.
"""

from __future__ import annotations

from typing import Any

from human_data_budget.models import Allocation, PolicyState
from human_data_budget.policies.base import Policy
from human_data_budget.policies.joint import JointPolicy
from human_data_budget.policies.no_rescue import NoRescuePolicy
from human_data_budget.policies.random import RandomPolicy
from human_data_budget.policies.schedule_only import ScheduleOnlyPolicy
from human_data_budget.policies.selection_only import SelectionOnlyPolicy

#: Arms exempt from reconciliation, by design rather than by omission.
NEVER_RECONCILED = frozenset({"no_rescue"})


def last_spending_generation(horizon: int) -> int:
    """The last generation whose allocation is actually consumed.

    An allocation made at generation *g* is assembled into generation *g+1*'s
    training corpus, so the allocation at the final generation has no successor to
    train on and is discarded. Reconciling there would top a policy up with tokens
    that never reach the optimizer -- which is exactly how `schedule_only` appeared
    to under-spend by 150,000: its frozen back-loaded schedule places a full
    allowance on the final generation, where it evaporates.
    """
    return max(0, horizon - 2)


def is_final_generation(generation: int, horizon: int) -> bool:
    return generation == last_spending_generation(horizon)


def policy_for_final_generation(
    policy: Policy, config: dict[str, Any], remaining_human_tokens: int
) -> Policy:
    """Return a policy of the same kind whose allowance is the remaining budget.

    Rebuilt rather than mutated so the original object is unchanged and a caller
    cannot accidentally carry a raised allowance into an earlier generation.
    """
    if policy.name in NEVER_RECONCILED or remaining_human_tokens <= 0:
        return policy

    horizon = int(config["horizon"])
    allowance = int(remaining_human_tokens)

    if isinstance(policy, RandomPolicy):
        return RandomPolicy(allowance)
    if isinstance(policy, SelectionOnlyPolicy):
        return SelectionOnlyPolicy(allowance)
    if isinstance(policy, ScheduleOnlyPolicy):
        # Its schedule is what defines the arm, so only the final entry moves.
        schedule = dict(policy.schedule)
        schedule[last_spending_generation(horizon)] = allowance
        return ScheduleOnlyPolicy(schedule)
    if isinstance(policy, JointPolicy):
        # JointPolicy caps its maximum at 2x base, so half the remainder as base
        # leaves the cap at the remainder itself. Its urgency rule still decides
        # how much of that it wants; the feasibility clamp then floors it at the
        # reserve, which at the last generation is the whole remainder.
        return JointPolicy(horizon, max(1, allowance // 2))
    if isinstance(policy, NoRescuePolicy):  # pragma: no cover - covered by name check
        return policy
    raise TypeError(f"no terminal reconciliation defined for {type(policy).__name__}")


def allocate_with_reconciliation(
    policy: Policy,
    state: PolicyState,
    seed: int,
    *,
    config: dict[str, Any],
) -> tuple[Allocation, bool]:
    """Allocate, raising the allowance to the full remainder at the final generation.

    Returns the allocation and whether reconciliation was applied, so the caller can
    record it per generation rather than inferring it later.
    """
    horizon = int(config["horizon"])
    if not is_final_generation(state.generation, horizon):
        return policy.allocate(state, seed), False
    if policy.name in NEVER_RECONCILED or state.remaining_human_tokens <= 0:
        return policy.allocate(state, seed), False

    final = policy_for_final_generation(policy, config, state.remaining_human_tokens)
    return final.allocate(state, seed), True
