# U-006 — practical effect threshold, reviewed against measurement

**Date:** 2026-08-19
**Decides:** U-006, open since Week 2. Supersedes P-007's stopgap status.
**Conclusion:** **Keep 2%.** Not because it was already there, but because measurement
shows it is a defensible bar — and because the window in which it could legitimately be
changed has closed.
**Reviewed by:** the project owner, working from measured pilot data. **This is not the
mentor/statistics review `DECISIONS.md` names**, and does not discharge it. What it does
is replace "adopted because it was already written down" with "checked against data and
found defensible", and record why the figure is now fixed regardless.

## The question

P-007 adopted a 2% relative practical effect threshold because it was frozen in the Week 2
method freeze before any primary outcome existed, and inventing a new figure after seeing
pipeline behaviour would have been worse. It was recorded as the weakest decision in the
log. Until the pilot ran there was nothing to check it against.

## Anchors, from the executed pilot

All from `results/runs/primary_pilot_2026-08-18/`, in AUC-regret units (lower is less
degradation):

| quantity | value | relative |
|---|---|---|
| `no_rescue` — spend nothing | 2.63738 | — |
| `random` — spend, unselectively | 2.52454 | — |
| `selection_only` — best observed | 2.31320 | — |
| **A.** total span, nothing → best observed | 0.32417 | 12.29% |
| **B.** value of spending at all | 0.11284 | 4.28% |
| **C.** value of selecting well | 0.21133 | 8.37% |
| **2% threshold** | **0.05049** | — |

The threshold expressed against each anchor:

- **15.6% of the total span (A).** An effect must be at least a sixth of everything the
  intervention achieves, end to end, before it counts as practically meaningful.
- **44.7% of the value of spending at all (B).** This is the least comfortable reading: an
  effect nearly half as large as the entire rescue intervention could be declared
  practically equivalent.
- **23.9% of the value of selecting well (C).** For the contrast that matters —
  joint against the strongest baseline — joint must beat selection-only by about a quarter
  of the selection effect to clear the bar.

## Assessment

**2% is a defensible bar and is not gamed in either direction.** It is not so small that
noise clears it: measured variance puts it at roughly three paired chains for 80% power,
so it is comfortably detectable rather than aspirational. It is not so large that nothing
could ever reach it: the selection effect alone is four times it. A threshold that lands
between "trivially detectable" and "unreachable" is doing its job.

The reading against anchor B is the honest weakness and should be stated in the paper
rather than buried: an effect worth almost half of the whole rescue intervention would be
reported as practically equivalent. A future preregistration may reasonably set a tighter
bar for that reason.

## Why it cannot be changed now

The trigger on U-006 and the logic of P-007 both point the same way. Primary outcomes are
open — the pilot's AUC figures are computed and recorded. **Any change to the threshold
made now is a change made with knowledge of the results**, and the direction of the change
would determine whether a future joint-versus-baseline interval falls inside or outside the
equivalent region. That is precisely the degree of freedom preregistration exists to
remove.

So the threshold is fixed at 2% for this line of work, and this document is the record of
why: not because it is optimal, but because it was frozen before the data existed, it
survives a check against the data, and the opportunity to revise it honestly has passed.

## What would justify a different figure

For a **future, separately preregistered** experiment, and set before its outcomes are
opened:

- A mentor or statistics review with domain grounding this document does not have.
- A stated decision context — what a reader would do differently at 1% versus 2% — which
  the project has never written down and which is the proper basis for a practical
  threshold.
- Anchor B above, if the team judges that an effect worth half the rescue intervention
  should not be called equivalent.

## Consequences to carry forward

- `docs/decisions/powered_design_sizing_2026-08-19.md` scales every row with this figure.
  It stands unchanged.
- P-008's budget-matching margin is one tenth of this threshold and inherits it directly.
  It stands unchanged.
- The paper should state the threshold, its provenance (frozen pre-outcome, checked
  post-hoc, never externally reviewed), and the anchor-B weakness. A reviewer who works out
  the anchor themselves and finds it unacknowledged will trust the rest less.
