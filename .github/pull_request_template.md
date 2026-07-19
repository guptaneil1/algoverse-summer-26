## Purpose

Closes #

## Week and owner

- Week: `W1 / W2 / W3 / W4 / shared`
- Owner: `Ronit / Khantushig / Neil / Aarav`
- Target integration branch:

## Complete deliverable

What self-contained weekly outcome does this PR provide?

## Files owned

List the directories/files changed. Explain any cross-owned change.

## Independent inputs

Which frozen tag and fixtures allowed this work to finish without another current branch?

## Exact verification commands

```bash
ruff check .
pytest
python -m human_data_budget.runner.chain --config configs/experiment/toy_cpu.json
```

## Scientific impact

Which claim, protocol choice, metric, baseline, exclusion, or experiment can this affect?

## Checklist

- [ ] The PR has one clear weekly/shared outcome.
- [ ] Owned directories only, or affected-owner review requested.
- [ ] No planned work is described as implemented.
- [ ] Tests pass locally.
- [ ] No final-test information enters selection or tuning.
- [ ] Human and total token accounting remain exact where applicable.
- [ ] Config/schema changes are versioned.
- [ ] Experimental numbers, if any, come from linked run artifacts.
- [ ] Failures/invalidations are retained and logged.
- [ ] `CLAIMS.md` changed if scientific wording changed.
- [ ] `DECISIONS.md` changed if a protocol decision changed.
- [ ] Reproduction instructions are sufficient for another teammate.

## Current status and risks

Update this section during the week. Do not hide blockers in private chat.
