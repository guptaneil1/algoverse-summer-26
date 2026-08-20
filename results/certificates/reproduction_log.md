# Independent reproduction log

`docs/SUBMISSION_CHECKLIST.md` requires the headline table to be reproduced by a person, not
only by CI. This file records each time a human has run it, what they saw, and — because it
matters more than the pass — **how independent that person actually was**.

`scripts/reproduce_pilot_table.py` recomputes every published per-arm value from the
committed `chain_result.json` files using arithmetic written deliberately separately from
`scripts/generate_pilot_outputs.py`. It shares no code with the generator, so a defect in
the generator cannot hide by being reused. It runs on any machine with the repository
checked out: no GPU, no pod, no network.

---

## 2026-08-20 — project owner

| Field | Value |
|---|---|
| Run by | The project owner, on the project workstation (Windows, PowerShell) |
| Command | `.\.venv\Scripts\python.exe scripts\reproduce_pilot_table.py` |
| Run directory | `results/runs/primary_pilot_v2_2026-08-20` (the script's default) |
| Chains read | 25 |
| Result | **`every published value reproduced from the artifacts.`** Exit 0 |
| Budget axes, as recomputed by the script | cross-arm total spread 0.00%, joint human shortfall 0.0%, each inside the 0.2% the guard permits |

Recomputed values, as printed:

```
arm                AUC regret         SD      human        total
no_rescue             2.64314    0.01401          0   16,678,912
random                2.53644    0.00801    749,869   16,678,912
schedule_only         2.52612    0.01939    749,878   16,678,912
selection_only        2.29314    0.02502    749,827   16,678,912
joint                 2.30340    0.02207    749,827   16,678,912
```

### How independent this was, stated plainly

**Partially.** The checklist's intent is a second pair of eyes on the analysis, and this run
satisfies part of that and not all of it.

- **What it does establish.** A human, not CI, executed the check on a machine outside the
  run environment, and the arithmetic that produced every published number was reproduced by
  an independently written implementation. The person who ran it did not write either
  implementation.
- **What it does not establish.** The project owner directed the analysis and operated the
  run. They are not a disinterested party, and `docs/SUBMISSION_CHECKLIST.md` assigns this
  item to Neil precisely so that the person running it has no stake in the outcome.

**The item is therefore advanced, not closed.** A run by Neil, or by anyone outside the
project, would supersede this entry. It should be appended below rather than replacing it —
the value of this log is the sequence, and an entry that gets overwritten records nothing.

### What it deliberately does not check

The script says so itself in its closing output, and it is worth repeating where a reader
will find it: **reproducing the numbers is silent on whether the run was valid.** That is
answered by the budget guard and `scripts/validate_run.py`, not by arithmetic. A grid can
reproduce perfectly and still be inadmissible — the 2026-08-18 grid does exactly that, and
`python scripts/reproduce_pilot_table.py --run-dir results/runs/primary_pilot_2026-08-18`
passes on it while the same script reports that one of its budget axes fails.

Nor does it close the validity certificate. See
`primary_pilot_v2_2026-08-20_EVIDENCE_PACK.md` §8 for what a certifier still owes, including
recomputing a metric from raw evaluator outputs rather than from `chain_result.json`, which
is one level downstream and is where this script starts.
