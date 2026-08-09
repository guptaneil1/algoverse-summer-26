---
description: Find which lines of a prompt actually earn their place, by ablation
---

Prompt file to ablate: $ARGUMENTS

Do not rewrite the prompt. Measure it.

## 1. Preview the blocks

```bash
python promptlab/ablate.py $ARGUMENTS --blocks
```

Report the block list. Flag any block that looks like two rules fused together — those
ablate poorly, because removing them tests two things at once. Suggest the split.

## 2. Check the eval covers this prompt's claims

For each block, name the promptlab task that would detect its absence. Any block with no
corresponding task is currently **unfalsifiable** — ablation will show it doing nothing,
because nothing measures it. List those separately; either write the task or accept that
the block is unmeasured.

## 3. Run

```bash
python promptlab/ablate.py $ARGUMENTS --reps 5
```

## 4. Report

Three lists, using the intervals rather than the point estimates:

- **Earned its place** — removal lowered the score, intervals separated. Keep, and name
  the specific failure each one prevents.
- **Dead weight** — removal changed nothing. Recommend deletion. Say plainly that this
  is an improvement and not a loss.
- **Harmful** — removal raised the score. Delete, and hypothesize what it was pulling
  against.
- **Undetermined** — intervals overlap. Say so; do not guess a direction.

## 5. Emit the reduced prompt

Output the prompt with dead weight and harmful blocks removed, in a fenced block. Then
state what it costs: which blocks you removed that had no covering task, and are
therefore removed on absence of evidence rather than evidence of absence.
