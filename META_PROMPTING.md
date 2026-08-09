# Meta-Prompting for the Human Data Budget Project

## The idea in one paragraph

A meta-prompt is a prompt whose output is another prompt, or a prompt that shapes every
future prompt. The leverage runs in that order: `CLAIMS.md`-style standing constraints
beat slash commands, slash commands beat clever one-off typing. Most people invest
their effort in exactly the reverse order and then wonder why every session starts from
zero. The point of this setup is to move your effort up the stack.

## Install

```bash
cp CLAUDE.md /path/to/algoverse-summer-26/
cp -r .claude /path/to/algoverse-summer-26/
cd /path/to/algoverse-summer-26 && git add CLAUDE.md .claude && git commit -m "Add Claude Code project memory and commands"
```

Commit it. `.claude/` is shared team infrastructure — when Neil improves `/validity`,
Aarav gets the improvement. That is the actual return on this: a prompt library that
accrues instead of living in four people's shell histories.

Then in Claude Code: `/memory` to review what loaded, `/context` when a session gets
long, `/compact` before it gets too long, `/plan` before anything touching `runner/`,
`schemas/`, or `paper/`.

## The four principles these files encode

**1. Ground truth beats recall.** Every command names the exact files to read first.
A model reasoning from memory about your repo is guessing fluently, and fluent guessing
is the specific danger in a project where a plausible-looking number can end up in a
paper. `CLAUDE.md` makes "I have not opened that file" a sayable answer.

**2. Definition of done must be executable.** "Implement the tail metric well" cannot
be checked. "`make test` passes, `tests/evaluation/test_tail.py::test_frozen_partition`
asserts the metric is computed on a partition never used for selection" can be. Every
command here converts judgment criteria into commands that exit 0.

**3. Name the failure modes in the prompt.** Telling a model what usually goes wrong on
this task in this repo is worth more than telling it what to do. `/implement` names
architecture-boundary imports and guessed constants; `/validity` asks directly for the
three ways the code could be wrong while passing every existing test. Adversarial
framing surfaces things that "please check carefully" never will.

**4. Give uncertainty somewhere to go.** The VERIFIED / ASSUMED / UNKNOWN split appears
throughout. Without a designated slot, uncertainty gets smoothed into confident prose,
which is how a scaffold quietly becomes a "result."

## What each command is for

| Command | Use when |
|---|---|
| `/metaprompt <rough task>` | Before any task big enough to be worth doing right. Compiles a vague ask into a spec, asks up to three blocking questions, does not start work. |
| `/harden <prompt>` | You have a prompt and want it attacked before you spend a session on it. |
| `/crystallize` | End of a session that went well. Converts what happened into a reusable command, agent, or `CLAUDE.md` line. **This is the one that compounds.** |
| `/trace <number>` | Any number headed for the paper. Establishes or breaks the provenance chain. |
| `/validity <scope>` | Auditing PROTOCOL.md §3 invariants on a module, run, or PR. |
| `/implement <task>` | Contract-governed code, plan-first. |
| `/review <PR>` | Protocol-aware review with validity gated ahead of style. |
| `/status-truth` | Reconciling `docs/STATUS.md` against what artifacts actually prove. Run this today. |

Subagents (`/agents` to view) run with their own clean context, which is the point —
`evidence-auditor` cannot inherit the main thread's assumptions, so its independence is
structural rather than a matter of instructions. Invoke by asking: *"Have the
evidence-auditor verify the tail-retention number in Table 2."*

## Given the date, run these first

It is August 8. Week 4 started today; the August 13 internal deadline is five days out.

```
/status-truth
```

That produces the honest baseline: what is on track, what is at risk, and what the
critical path to a truthful August 15 submission actually is — including the branch
where the truthful submission reports a scaffold plus a positive control rather than a
novel result. Under PROTOCOL.md that is a legitimate outcome, and the plan is better
for naming it early than for discovering it on the 14th.

Then, per workstream: Ronit `/harden` on the claims-to-evidence mapping and the
`novelty-adversary` agent on every contribution sentence; Khantushig `/implement` and
a clean-environment reproduction; Neil `/validity` across primary manifests plus
`evidence-auditor` on each headline; Aarav the `stats-referee` on the analysis plan
before regenerating anything.

## Writing your own commands

The frontmatter `description` is a trigger condition, not a title — write "use when a
novelty claim is being defended," not "novelty tool." That description is what makes
the command discoverable months later and what lets Claude Code surface it at the right
moment.

Arguments: `$ARGUMENTS` captures everything after the command; `$1`, `$2` capture
positionally. Keep commands under roughly 100 lines. A command that tries to be a
manual gets skimmed by the model the same way it gets skimmed by you.

The best source of new commands is not imagination — it is `/crystallize` after a
session where you had to correct Claude three times. Those three corrections are the
content. Encode them, and the next person never makes them.

## Research prompting outside Claude Code

For literature and synthesis work in the chat interface, the same principles apply,
with one addition: **separate the search turn from the synthesis turn.** Asking for
findings and interpretation in a single message reliably produces confident synthesis
built on shaky retrieval, because there is no point at which the retrieval gets
examined on its own.

A pattern that works for the novelty and related-work sections:

> Search for work published after [date] on [exact topic]. For each result, give only:
> full citation, the precise claim it makes, its experimental setting, and one sentence
> on how it differs from [our exact framing]. No synthesis, no ranking, no assessment
> of relevance to us. If a search returns nothing useful, say so rather than reaching
> for adjacent work.

Then, in the next turn:

> Using only the sources above and nothing from memory: which parts of [claim] survive?
> Write the narrowest version you cannot defeat. Then name what would be needed to
> defend anything broader.

The constraint "only the sources above and nothing from memory" is doing real work
there. Without it, half-remembered papers leak into the synthesis, and a
half-remembered paper is indistinguishable from a fabricated one by the time it reaches
your related-work section.
