# promptlab — measured prompt engineering

## The problem with the prompts you already have

They are hand-written guesses. So is every prompt template on the internet, including
the good-looking ones. Nobody has evidence they beat plain English on *your* tasks,
because nobody measured.

Your `PROTOCOL.md` already forbids this pattern. An unmeasured intervention, a
predeclared-sounding rationale, no control arm, no uncertainty. You would reject that
methodology in an experiment. It is the same methodology when the artifact is a prompt.

So: hyper-engineering a prompt is not writing a longer prompt. It is this loop.

```
write a grader  →  run a control  →  run variants  →  read the failures
      ↑                                                      ↓
      └──────  ablate: delete every line that didn't earn it  ┘
```

## Why measurement changes the answer

Untested prompts fail in a specific direction: they grow. Every time something goes
wrong you add a line. Nothing is ever removed, because removal feels risky and you have
no way to check. After a month you have 800 words of accumulated superstition, and the
three rules that actually matter are buried among forty that don't.

That is not a neutral cost. Attention is finite — a rule sitting in a list of forty is
followed less reliably than the same rule in a list of five. **A bloated prompt is worse
than a short one, not merely more expensive.** Ablation is the only tool that gets lines
back out, which is why it, and not clever phrasing, is the core of this directory.

## Install

```bash
cp -r promptlab /path/to/algoverse-summer-26/
cd /path/to/algoverse-summer-26
python promptlab/run.py --dry-run     # check wiring, no API calls
```

Requires the `claude` CLI on PATH and a git repo (runs are isolated in worktrees).
Stdlib only.

## Run it

```bash
python promptlab/run.py --reps 5       # all variants x all tasks
python promptlab/score.py              # pass rates, paired deltas, failure taxonomy
python promptlab/score.py --failures   # the actual transcripts that failed
```

Roughly `variants x tasks x reps` calls. Six tasks, four variants, five reps = 120 runs.
Start with `--reps 3` and two variants while you're calibrating.

## The tasks

Six, all deterministically graded, all drawn from real failure modes in your repo:

| Task | Catches |
|---|---|
| `no_invented_hash` | Fabricating a commit hash for a value that is still a TODO |
| `status_over_code` | Treating existing code as evidence something was run |
| `claim_discipline` | Banned words and dropped novelty qualifiers in abstract prose |
| `unit_of_analysis` | n=30 instead of n=3 — generations counted as independent |
| `refuse_violation` | Editing README with an unvalidated number under social pressure |
| `leakage_detection` | Approving a threshold tuned on the test partition |

Graders are keyword and regex checks plus a git-status check, so a response can't pass
on wording while doing the forbidden thing. **No LLM judge.** A judge adds variance to
the quantity whose variance you are trying to measure, and on a six-task eval that noise
swamps the effect.

Grading this way constrains what you can ask. That constraint is doing work: if you
cannot write a grader for a task, you cannot tell whether a prompt improved it, so any
prompt line aimed at it is decoration. **Write the grader first.**

## The variants

| Variant | What it is |
|---|---|
| `baseline.md` | Just `{{TASK}}` — plain English. **The control. Never delete it.** |
| `baseline_bare.md` | Same, with `--bare`: CLAUDE.md and skills not loaded |
| `v1_minimal.md` | Three rules |
| `v2_full.md` | Nine rules |

A file containing `{{TASK}}` is a user-prompt template. Anything else is treated as an
appended system prompt — the CLAUDE.md-shaped intervention. Put `bare` in the filename
to run it with `--bare`.

`baseline` vs `baseline_bare` is the experiment most teams skip: it measures whether
your `CLAUDE.md` is doing anything at all. Run it before writing another line of it.

## Ablation — the part that matters

```bash
python promptlab/ablate.py promptlab/variants/v2_full.md --blocks   # preview
python promptlab/ablate.py promptlab/variants/v2_full.md --reps 5
```

Splits the prompt into blocks, removes one at a time, runs all of them, scores against
the intact prompt. Bulleted lists split per-item, because a single bad rule inside a list
is the common case and paragraph-level ablation would hide it.

Reading the output:

- **Removal doesn't change the score** → dead weight. Delete it. This will be most of
  your prompt, and deleting it is the improvement.
- **Removal raises the score** → actively harmful. Delete it first, then work out what
  it was doing; usually it pulled toward a behaviour that conflicts with another rule.
- **Removal lowers the score** → earned its place. Keep it, and record which failure it
  prevents.
- **Intervals overlap** → you learned nothing about that block. More reps, or accept it.

## Statistical honesty

The same discipline your `stats-referee` enforces, applied here:

- **n≥5 per cell.** Below that you cannot separate a real difference from sampling
  noise. A prompt that worked once is an anecdote.
- **Wilson intervals, not normal approximation.** At n=5 the normal approximation is
  wrong, and it's degenerate at 0/5 and 5/5 — which is exactly where prompt evals sit.
- **Paired comparison.** Variants run the same tasks; that's paired data. Comparing
  marginal pass rates discards the pairing and most of your power.
- **Overlapping intervals means no result.** `score.py` prints `NOT DISTINGUISHABLE`
  and you should believe it. "Directionally better" with overlapping intervals is a
  null, in prompts as in chains.
- **Six tasks detects large effects only.** Most prompt tweaks are small effects. This
  is the argument for subtraction: you can reliably detect "this whole block does
  nothing," which is the finding you can act on.

## Overfitting

With six tasks you will overfit fast. Countermeasures:

1. **Hold out.** Write ten tasks, tune on six, check the final prompt on four you never
   looked at. If it doesn't hold, you tuned to the eval.
2. **New failures become new tasks, not new prompt lines.** When Claude does something
   wrong in real work, the first move is a task that reproduces it — then a prompt line,
   then ablation to confirm the line earns its place. A prompt line added without a task
   is untestable forever after.
3. **Re-ablate quarterly and after any model change.** Blocks that earned their place
   against one model may be dead weight against the next.

## The rule that replaces all the advice

> Every line in a prompt must trace to a logged failure, and must survive ablation.

Lines that fail either test get deleted, no matter how sensible they sound. That is the
whole method. Everything else in this directory is tooling to make the two tests cheap.

## Honest limits

- Six tasks is small. It measures protocol compliance, not general coding quality.
- The graders are keyword-based, so they can be gamed by a response that says the right
  words. The `no_file_changes` check exists to catch the worst version of that, but a
  verbose non-answer can still pass. Read `--failures` transcripts periodically rather
  than trusting the number.
- Nothing here measures whether the *work* was good, only whether the guardrails held.
  Those are different questions and the second one is much harder to grade.
- Cost is real. 120 runs is not free. Check `cost_usd` in the score output before
  scaling reps.
