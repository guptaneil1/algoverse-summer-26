# CLAUDE.md — The Human Data Budget

You are working inside a research repository operating under a strict verification
protocol with a hard submission deadline of **August 15, 2026**. The cost of a
fabricated number, an invented citation, or an overstated claim in this repo is
higher than the cost of slow progress. Read this file as binding constraints, not
as style preferences.

## What this project is

Under a fixed lifetime budget of human-origin optimizer tokens, when should those
tokens be spent during recursive training, and which under-covered modes of a human
reference distribution should they target? Four budget-matched strategies are
compared: random rescue, schedule-only, selection-only, and joint time-and-mode.

Experimental unit = one independently seeded recursive chain. Generations within a
chain are repeated observations, **not** independent samples.

## Ground truth files — read before answering, do not reason from memory

| Question | Authoritative file |
|---|---|
| What actually exists / what is done | `docs/STATUS.md` |
| What we are allowed to claim | `CLAIMS.md` |
| Verification rules, invariants, acceptance criteria | `PROTOCOL.md` |
| Frozen hypotheses and analysis plan | `PREREGISTRATION.md` |
| Why a past decision was made | `DECISIONS.md` |
| What already failed | `FAILURE_LOG.md` |
| Component boundaries, dependency direction | `docs/ARCHITECTURE.md` |
| Cross-workstream contracts | `docs/interfaces/*.md`, `schemas/*.json` |
| Who owns what | `docs/TEAM.md`, `.github/CODEOWNERS` |
| This week's assignments | `docs/weekly/WEEK_4.md` |
| Branch, PR, freeze rules | `docs/WORKFLOW.md` |

`docs/STATUS.md` outranks the code. If code exists but STATUS says "Not reproduced,"
the correct answer is "not reproduced."

## Hard rules

1. **No invented numbers.** Never write a metric, effect size, p-value, token count,
   commit hash, or runtime into any file, message, or answer unless you read it from
   a frozen artifact in this session. If you don't have it, write
   `TODO(owner): awaiting value from <source>` — never a plausible placeholder that
   could be mistaken for a measurement.
2. **No invented citations.** Papers, authors, years, and venues come from
   `docs/evidence/sources.yaml` or a fetched source. Never reconstruct a reference
   from memory.
3. **No paper-facing number is entered by hand.** Numbers reach the manuscript only
   through generated files under `results/aggregates/` and `paper/`.
4. **The no-result rule** (PROTOCOL.md §5): nothing enters `README.md`, `CLAIMS.md`,
   an abstract, or slides until the run completed, the manifest validated, blocking
   tests passed, and the analysis was regenerated from immutable artifacts.
5. **Banned words** in any claim about this work: "first," "optimal," "prevents
   collapse," "solves," "state of the art." Also avoid unqualified "novel" — novelty
   claims carry the modifiers *recursive*, *fixed lifetime human-token budget*, and
   *matched non-joint baselines* (see CLAIMS.md C-004).
6. **Test data is radioactive.** Final human test data may not influence prompts,
   selection, thresholds, early stopping, or hyperparameters. If a proposed change
   touches the test partition, stop and say so.
7. **Budget matching is the fairness constraint.** Any policy comparison must consume
   identical lifetime human-origin optimizer tokens and identical total optimizer
   tokens, unless explicitly labeled a sensitivity analysis.
8. **Frozen means frozen.** After a results freeze tag, allowed edits are clarity,
   citations, formatting, packaging, and removal of unsupported claims. Adding a seed,
   metric, subgroup, exclusion, budget, or redesigned method is not allowed.
9. **Failures stay recorded.** Null results, exclusions, and contradictions go in
   `FAILURE_LOG.md`. Do not quietly delete a failing branch of work.

## Epistemic status protocol

End any non-trivial answer with an explicit split:

```
VERIFIED (read this session): ...
ASSUMED (not checked): ...
UNKNOWN (blocking): ...
```

If the UNKNOWN section contains anything that changes the recommendation, say that
directly instead of hedging in prose. Uncertainty in this repo is information, not
weakness. "I do not know and here is the one command that would tell us" is a better
answer than a confident guess.

## Commands

```bash
make setup                 # locked, hash-checked install
make lint                  # ruff
make test                  # pytest -q
make smoke                 # toy CPU chain, no model or dataset download
make audit                 # scripts/audit_repository.py --strict-structure
make reproduce-headline    # guarded; exits 3 until results freeze
make submission            # scripts/build_submission.sh
```

Python >= 3.10. Package is `src/human_data_budget/`, installed editable.

## Code conventions

- Dependency direction follows `docs/ARCHITECTURE.md`. `policies/`, `data/`,
  `evaluation/`, and `training/` must not import from `runner/` or `analysis/`.
- Anything crossing a workstream boundary is governed by `schemas/*.json`. Change the
  schema and the interface doc in the same commit, or don't change it.
- Determinism is a test, not an aspiration. Seeds propagate through sampling,
  generation, initialization, dropout, and evaluation. New randomness needs a seed
  path and a determinism test.
- Writes to artifact paths are atomic (see `tests/runner/test_atomic_write.py`).
- Token counts come from tokenized batches actually consumed by the optimizer, never
  from character or document estimates.

## Working style here

- **Read before writing.** Cite file paths and line numbers for claims about this
  codebase. If you haven't opened the file, say so.
- **Plan mode for anything touching `runner/`, `schemas/`, or `paper/`.** Propose the
  diff and wait.
- **Small, owned diffs.** Check `.github/CODEOWNERS` before editing outside the
  current branch's workstream; cross-owner edits need a flag, not a fait accompli.
- **When the request conflicts with these rules, say so and stop.** Do not find a
  clever reading of the request that makes it permissible.
