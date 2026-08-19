"""Budget-matched policy contracts and toy reference implementations."""

from human_data_budget.policies.base import Policy
from human_data_budget.policies.joint import JointPolicy
from human_data_budget.policies.no_rescue import NoRescuePolicy
from human_data_budget.policies.random import RandomPolicy
from human_data_budget.policies.schedule_only import ScheduleOnlyPolicy
from human_data_budget.policies.selection_only import SelectionOnlyPolicy

#: Every implemented policy, keyed by the arm name a config uses. Kept here rather
#: than in a runner so that a check needing only a policy's declared properties --
#: whether it spends at all, say -- does not have to construct one, which would
#: require a schedule, a horizon and a budget it has no reason to know.
POLICY_CLASSES: dict[str, type[Policy]] = {
    cls.name: cls
    for cls in (
        JointPolicy,
        NoRescuePolicy,
        RandomPolicy,
        ScheduleOnlyPolicy,
        SelectionOnlyPolicy,
    )
}


def spends_human_tokens(policy_name: str) -> bool:
    """Return whether ``policy_name`` can consume human-origin tokens at all.

    Raises for an unknown name rather than defaulting. Defaulting either way is
    wrong: True would fail a legitimate new control arm, and False would quietly
    exempt a spending arm from the realised budget-matching constraint.
    """
    try:
        return POLICY_CLASSES[policy_name].spends_human_tokens
    except KeyError:
        known = ", ".join(sorted(POLICY_CLASSES))
        raise ValueError(f"unknown policy {policy_name!r}; known policies: {known}") from None


__all__ = ["POLICY_CLASSES", "JointPolicy", "NoRescuePolicy", "Policy", "RandomPolicy",
           "ScheduleOnlyPolicy", "SelectionOnlyPolicy", "spends_human_tokens"]
