# PROMPTS.md — Prompt Library

Copy a template, fill the `<>` slots, paste. Every template is built on the same five
moves, which are what make the difference between Claude doing roughly what you meant
and Claude doing exactly what you meant:

1. **Point at ground truth** — name the files to read, so it doesn't reason from memory.
2. **Make "done" executable** — a command that exits 0, not a judgment call.
3. **Fence the scope** — say what must not change, or it will drift.
4. **Name the failure mode** — tell it how this task usually goes wrong here.
5. **Force an uncertainty report** — give doubt a place to go, or it gets smoothed away.

If you only remember one thing: **the "out of scope" and "how this goes wrong" lines do
more work than anything else on the list.**

---

## 1. Implement something

```
Implement <what> in <file/module>.

Read first: docs/ARCHITECTURE.md (dependency direction), docs/interfaces/<X>.md and
schemas/<X>.schema.json (the contract), the existing tests for this module, and
DECISIONS.md + FAILURE_LOG.md (check whether this was already tried).

Plan first, don't write code yet. Show me: files you'll touch and why, the contract
each change satisfies quoted from the schema, the test names you'll add and the exact
assertion each makes, and where randomness enters and how the seed reaches it.

Done means: `make lint && make test && make smoke` all pass, and <specific new test>
fails if I revert the core change.

Do not touch: <adjacent files>. Do not change any schema. Do not add a dependency.

Usual failure here: guessing a constant instead of writing TODO(owner), and importing
across the architecture boundary from policies/ or evaluation/ into runner/.

End with VERIFIED / ASSUMED / UNKNOWN.
```

**Filled example**

> Implement the frozen tail-retention metric in `src/human_data_budget/evaluation/tail.py`.
> Read first: `docs/interfaces/evaluation.md`, `schemas/evaluation.schema.json`,
> `tests/evaluation/test_metrics.py`, and `PREREGISTRATION.md` for how the metric is
> predeclared. Plan first, don't write code yet. Done means `make test` passes and a new
> test asserts the metric is computed on a partition never used for selection. Do not
> touch `runner/` or any schema. Usual failure: silently evaluating on a partition that
> also fed selection. End with VERIFIED / ASSUMED / UNKNOWN.

---

## 2. Debug something

```
<Command> fails with <paste the exact error, full traceback>.

Before proposing any fix: give me three competing hypotheses for the root cause,
ranked by likelihood, and for each, the single cheapest command or file read that
would confirm or kill it. Run those checks. Then tell me which hypothesis survived
and which died, and why.

Only then propose a fix. The fix must include a test that fails before it and passes
after.

Do not change unrelated code to make the error go away, and do not loosen an assertion
or widen a tolerance unless you can argue the original was wrong — say so explicitly
if that's what you're doing.
```

The three-hypotheses structure is the whole trick. Without it you get the first
plausible fix; with it you get the actual cause, because a model committed to three
hypotheses has to disconfirm two.

---

## 3. Verify a number before it reaches the paper

```
Trace <number/claim> back to its artifacts. Don't compute it yourself and don't accept
it because it appears in two places — propagated errors look like corroboration.

Establish each link: where it appears (all files, note any disagreement) → generating
command → analysis code + commit → aggregate file + hash → raw chain artifacts (do they
validate against schemas/chain_result.schema.json?) → run manifest → data manifest →
test-partition safety → budget matching across arms.

Verdict, stated first: TRACED / BROKEN AT LINK N / HAND-ENTERED. If hand-entered, say
so plainly with file and line — that's a no-manual-numbers violation, don't soften it.
```

Or just: `/trace <number>`

---

## 4. Research and literature

Do this in **two turns**. One message asking for both search and synthesis reliably
gives you confident synthesis built on shaky retrieval, because the retrieval never
gets examined on its own.

**Turn 1 — retrieval only:**

```
Search for work published after <date> on <exact topic>. For each result give only:
full citation, the precise claim it makes, its experimental setting, and one sentence
on how it differs from <our exact framing>.

No synthesis, no ranking, no assessment of relevance to us. If a search returns nothing
useful, say so rather than reaching for adjacent work.
```

**Turn 2 — synthesis, hard-fenced:**

```
Using only the sources above and nothing from memory: which parts of <our claim>
survive? Write the narrowest version you cannot defeat, as a paste-ready sentence with
the qualifiers recursive / fixed lifetime human-token budget / matched non-joint
baselines. Then: what would be needed to defend anything broader, and is it achievable
before August 15 or is it future work?
```

"Only the sources above and nothing from memory" is doing real work. Without it,
half-remembered papers leak in — and by the time one reaches your related-work section
it's indistinguishable from a fabricated one.

---

## 5. Write a paper section

```
Draft <section> of paper/.

Inputs, and nothing else: <exact generated files under results/aggregates/>, CLAIMS.md
for what each claim's status permits, PREREGISTRATION.md for what was predeclared.

Rules: every number comes from those files via \input or a stable filename — never
typed. Every claim carries its status qualifiers. Exploratory analyses are labeled
exploratory, every time. Banned: first, optimal, prevents collapse, solves, state of
the art, and unqualified novel.

Where evidence doesn't support a sentence you want to write, write the weaker sentence
and flag it, or write RESULT_PENDING. Don't bridge a gap with confident prose.

After the draft, list every sentence that would need a reviewer to take our word for
something, and what artifact would back it.
```

That last paragraph is the highest-value line in this whole file. It surfaces the
overclaims you'd otherwise ship.

---

## 6. Review a PR or diff

```
Review <PR/branch/diff>. Gate order, and stop at the first failure — don't spend
effort on style while validity is broken.

1. Validity: any path by which an invalid result could look valid? Leakage, budget
   matching, token accounting, seeds, test-partition influence.
2. Claims: any prose asserting more than artifacts support? Check CLAIMS.md statuses
   and the banned words.
3. Freeze: is this an allowed edit given current freeze state?
4. Contracts: schema conformance, dependency direction, interface stability.
5. Ownership: does it touch another workstream's files per CODEOWNERS?
6. Engineering: tests that actually fail if logic breaks, determinism, atomic writes.

Verdict first: BLOCK / REQUEST CHANGES / APPROVE, with the single most important
reason. Then findings by severity with file:line and a concrete fix. Separate "must fix
before merge" from "later" — a blended list gets triaged into inaction.
```

Or: `/review <PR>`

---

## 7. Analysis and statistics

```
<Analysis task>.

Binding design fact: the experimental unit is one independently seeded recursive chain.
Generations within a chain are repeated observations, not independent samples. Any
interval whose width implies generation-level n is wrong.

Read PREREGISTRATION.md first. Label every analysis predeclared or exploratory, and
carry that label into every output.

Report: the estimand, the unit, how uncertainty was computed, how many comparisons were
made, and what effect size is detectable with the number of chains that actually exist.

If the honest result is null, report it as null. "Directionally consistent" with an
interval spanning zero is a null — write it that way.
```

---

## 8. Ask before you build (the cheapest prompt here)

```
Before you do anything: what are the three questions where, if you guess wrong, we
waste the most time? Give your current best guess for each and what a wrong guess
costs. Then wait.
```

Thirty seconds of typing that regularly saves an hour. Use it whenever the task is
bigger than a single file.

---

## 9. Turn a good session into a permanent command

```
/crystallize
```

Run it after any session where you had to correct Claude two or three times. Those
corrections are the content — it turns them into a `.claude/commands/` file so nobody
on the team makes them again. This is the only prompt here that compounds.

---

## Anti-patterns, and what to say instead

| Don't | Do |
|---|---|
| "Make this better" | "Make `make test` pass without changing the assertions" |
| "Check if this is right" | "Verify against `schemas/chain_result.schema.json` and report each field" |
| "What do you think about X?" | "Argue the strongest case against X, then the strongest case for" |
| "Fix all the issues" | "Fix issue 1. Show me the diff. Then stop." |
| Long session, many topics | `/clear` between tasks; `/compact` when one task runs long |
| Asking for code and review in one turn | Two turns, or the reviewer inherits the author's assumptions |

**On session hygiene:** the most common cause of Claude "getting worse" partway through
is a context window full of three unrelated tasks. `/context` shows you what's in there.
`/clear` between tasks is free and fixes most of it.
