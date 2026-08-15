# Failure Log

> No experimental run has been attempted in this repository. The entries below are
> implementation findings, not experimental outcomes.

Failures, null results, contradictory evidence, and protocol violations must be retained. They may not be deleted because they weaken the preferred conclusion.

## Entries

| ID | Date | Stage | Run/claim | Failure | Evidence | Cause status | Resolution | Scientific consequence |
|---|---|---|---|---|---|---|---|---|
| F-001 | 2026-08-15 | Fixture / method contract | C-002 treatment decomposition | `JointPolicy` is observationally identical to `SelectionOnlyPolicy`, and `RandomPolicy` to `ScheduleOnlyPolicy`, under every configuration the fixture simulator permits. The time-allocation axis is inert. | `tests/policies/test_joint_degeneracy.py` (5 tests, passing); `results/figures/nll_by_generation.png` shows two visible curves where four are plotted | **Implementation** — see analysis below. Not a scientific result. | Open. Assigned to Aarav; blocked on the frozen joint allocation rule (`05_method.tex`, U-007). | The fixture cannot currently distinguish the four treatment families. Budget-matching tests pass **trivially** and must not be cited as evidence that the decomposition is valid. |

### F-001 analysis

`policies/joint.py` computes:

```python
budget = min(
    state.remaining_human_tokens,
    max(self.base_per_generation_budget, reserve_safe_budget),
    adaptive_budget,
)
```

where `reserve_safe_budget = remaining_human_tokens // remaining_generations`.

The load-bearing invariant is **not** the divisibility guard. It is that
`analysis/simulator.py:88-101` pins every candidate's `human_token_count` to exactly
`per_generation_budget`, so at most one candidate is ever affordable in a generation and each
generation spends exactly `base_per_generation_budget`. Remaining budget and remaining generations
therefore stay in lockstep, and `reserve_safe_budget == base_per_generation_budget` at every step.
(The divisibility guard is what makes that lockstep exact rather than drifting; it is a necessary
condition, not the cause.)

Given that, the `max(...)` term collapses to `base_per_generation_budget` and caps the whole
expression. Because `time_multiplier >= 1.0` always, `adaptive_budget >= base_per_generation_budget`
and is never the binding term. The urgency signal is computed, then discarded.

**The `random`/`schedule_only` pair has a separate, unrelated cause.** `build_policy`
(`analysis/simulator.py:42-56`) constructs `ScheduleOnlyPolicy` with a *uniform* schedule —
`{g: per_generation_budget for g in range(horizon)}` — which is exactly the fixed per-generation
spend `RandomPolicy` already uses. With only two candidates of equal cost, the two policies then
select identically. This is a property of the fixture's schedule, not of `joint.py`, and it means
the fixture cannot currently distinguish a scheduled policy from an unscheduled one either.

**Consequence for the claim ledger.** C-002 requires the joint policy to be compared
against the *strongest* schedule-only and selection-only baselines. A joint policy that
reduces to selection-only cannot test that hypothesis at all. `05_method.tex` already
requires the method owner to give "a clear explanation of how the joint method differs
from combining two tuned baselines" — F-001 is direct evidence that the provisional
implementation does not yet differ from one of them.

**Why it was not fixed on discovery.** Choosing the time-allocation rule is a frozen
scientific decision under `PREREGISTRATION.md`, owned by Aarav. Changing the allocation
arithmetic to make the axes distinct would freeze a method by side effect. The
degeneracy is pinned by tests instead, so it fails visibly rather than passing silently.
Those tests are expected to fail when the real rule lands, and should be deleted then.

## Entry rules

For every failure, record:

- exact run or claim identifier;
- code and configuration commit;
- manifest and log location;
- whether the cause is implementation, infrastructure, protocol, or scientific;
- evidence supporting that classification;
- whether rerunning is allowed under the frozen rules;
- effect on claims and future stages.

An unfavorable treatment result is not an implementation failure without independent evidence of a defect.
