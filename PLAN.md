# Collapse Rescue Data — Master Plan (Batch 1 of 2)

**Covers:** Abstract (Output 1), Claims Map (Output 2), Week-by-Week Plan (Output 3), Figure Plan (Output 4), Pilot Spec (Output 9), Positioning Memo (Output 10), and THE ONE THING.

**Deferred to Batch 2** (better drafted after the pilot exists, or at least after you've read the calibration section): Adversarial reviews (5), Related Work prose (6), Repo blueprint (7), Methods prose (8).

---

## Calibration, before anything else

Two things in the prompt need correcting or the rest of the plan is built on sand.

**1. The venue target.** The prompt says NeurIPS Main. With Pythia-160M, one model scale, 5 generations, Colab Pro compute, and 5 weeks of runway, NeurIPS Main is not a realistic bar — not because the idea is weak (it isn't), but because Main-track reviewers on training-dynamics papers reliably ask for (a) multiple model scales to show the effect isn't a small-model artifact, (b) 3+ seeds on every headline number, and (c) some mechanistic account of *why* the winning composition wins. You can't buy all three with this compute and calendar. The plan below is built to the bar that is actually winnable: **a genuinely strong NeurIPS/EMNLP workshop paper, with COLM or EMNLP Findings as the stretch.** Everything that makes a Main paper good — clean claims, real statistics, honest baselines — also maximizes those odds, so nothing is wasted. The positioning memo (Output 10) spells out exactly what would have to be true to re-aim at Main.

**2. Seeds.** This is the biggest technical hole in the current design, bigger than the venue question. 27 conditions × 1 run each gives you 27 numbers and zero error bars. Any reviewer, workshop or otherwise, will ask whether the heatmap gradient exceeds seed noise. The plan below fixes this by shrinking the grid and spending the recovered compute on seeds. The full 27-cell × 3-domain sweep does not survive contact with a Colab budget anyway.

---

## OUTPUT 1: The Abstract

Target: 150–200 words. Ideal-case results are labeled; replace with real numbers in Week 9.

> Language models trained recursively on their own outputs undergo model collapse: output diversity narrows, rare knowledge disappears, and perplexity on human text rises. Mixing real human data into the training stream is known to prevent collapse, but the field cannot yet say *which properties* of that data do the rescuing. The closest prior work (Kovač et al., 2025) found that the semantic diversity of rescue data matters more than its lexical diversity — on short-form social media text — and explicitly cautioned that the finding may not generalize. We test that caution directly. Using a five-generation recursive training loop with Pythia-160M on long-form formal text (WikiText-103, with Reddit comments as a replication control), we independently manipulate three properties of a fixed-budget rescue set — dose (1–10% of training tokens), document length, and character-level noise — and map the dose × composition surface. **[IDEAL CASE]** We find composition dominates dose: a 5% rescue set of long, clean documents preserves more semantic diversity and tail knowledge at generation five than a 10% random set, while 1% character noise is harmless and 5% is not. For practitioners, the scarce resource is not the volume of human data but its selection.

(196 words.)

---

## OUTPUT 2: The Load-Bearing Claims Map

Six claims. Each one has a single experiment that proves or kills it. C4 is the safest claim in the paper; C1 is the headline; C5 is the one to be ready to cut.

### C1 — Composition beats dose (the headline)
- **Claim:** A 5% rescue set with favorable composition (long documents, 0% CER) produces less collapse at generation 5 than a 10% random rescue set, on semantic diversity and tail retention.
- **Proved by:** Direct cell comparison: (dose=5%, long, clean) vs. the 10% random-rescue baseline, ≥3 seeds each, on cosine diversity, SelfBLEU, PPL, tail retention.
- **Killed by:** 10% random matches or beats 5% curated on all primary metrics.
- **Risk:** MEDIUM-HIGH. Dose is a known strong lever (Gerstgrasser); composition beating a 2× dose is a real ask.
- **If null:** Reframe headline as "dose dominates composition in long-form formal text" — a clean, quantified answer to the title question ("how much human data is enough?") and a direct, publishable contrast with Kovač et al.'s domain.

### C2 — Document length is an active ingredient
- **Claim:** Holding dose (5%) and noise (0%) fixed, token-matched long-document rescue sets preserve diversity and tail knowledge better than short-document sets.
- **Proved by:** The length ablation column: three cells differing only in length bucket, ≥3 seeds.
- **Killed by:** Flat metrics across length buckets (differences within seed noise).
- **Risk:** MEDIUM. Plausible mechanism (long documents carry long-range structure and rarer content), but nobody has tested it, which is precisely why it could be flat.
- **If null:** Still the first test of this axis in the collapse-rescue literature. A tight null ("length doesn't matter, so don't pay for long documents") is a publishable practitioner takeaway.

### C3 — Noise has a threshold, not a slope
- **Claim:** 1% CER rescue data rescues as well as clean data; 5% CER measurably degrades quality and PPL.
- **Proved by:** Noise ablation column at dose 5%, long documents: {0%, 1%, 5%} CER, ≥3 seeds.
- **Killed by:** Either monotone degradation from 0→1% (noise always hurts) or no effect at 5% (noise never matters at these doses). Note the interesting third outcome: noise *helps* diversity metrics by acting as a regularizer — watch for it, it would be the most surprising finding in the paper.
- **Risk:** LOW that the axis shows *something*; MEDIUM for the specific threshold shape.
- **If null:** "Realistic OCR-level noise does not disqualify rescue data" is directly useful — it means practitioners can use cheap uncleaned corpora.

### C4 — The Kovač transfer test (the safest claim)
- **Claim:** Kovač et al.'s optimal composition either does or does not transfer from short-form social media to long-form formal text; either answer is a contribution.
- **Proved by:** Baseline 3 (their recipe applied to WikiText-103) vs. our best cell, PLUS the Reddit-subset replication as positive control. **The replication is load-bearing:** if you can't reproduce their result on their own domain, the transfer test is uninterpretable. Run the Reddit replication early, not last.
- **Killed by:** Only by a failed replication on Reddit — which would mean a pipeline bug, not a finding.
- **Risk:** LOW, *conditional on the replication working.*
- **If replication fails:** Stop and debug; do not proceed to the transfer claim.

### C5 — Dose × composition interaction (be ready to cut)
- **Claim:** The marginal value of additional dose depends on composition — the heatmap has curvature, not just two independent gradients.
- **Proved by:** Interaction term in a two-way ANOVA on generation-5 endpoints; interaction plot.
- **Killed by:** Non-significant interaction (very possible — interactions need statistical power you may not have with 2–3 seeds).
- **Risk:** HIGH.
- **If null:** Report main effects as the story, move the interaction surface to the appendix as descriptive. Do not let the paper's framing depend on this claim.

### C6 — Composition changes collapse *rate*, not just endpoint
- **Claim:** Favorable rescue composition slows the per-generation decay of diversity, visible in trajectory slopes across generations 1–5, not only in generation-5 values.
- **Proved by:** Per-generation trajectories (Figure 2); slope comparison between best and worst cells.
- **Killed by:** All conditions decay at the same rate and differ only in intercept.
- **Risk:** LOW. Trajectories will exist regardless; this claim is mostly descriptive and cheap.
- **If null:** Fold into results as an observation; costs nothing.

---

## OUTPUT 3: Week-by-Week Execution Plan

Today is **Thursday, July 9** — Week 6 is already half over, so the Week 6 plan starts now. Persons A–D; given Aarav is away July 19–23, Aarav should be Person D (writing-weighted load, front-loaded before the 19th).

### Week 6 (Thu Jul 9 – Mon Jul 13): Close the loop
- **Thu Jul 9**
  - A: Repo skeleton + single-generation training script on a 1M-token slice. *Done =* loss decreases, checkpoint saves and reloads.
  - B: WikiText-103 download/preprocess + length-bucket constructor. *Done =* three token-matched buckets (short/medium/long) exist on disk with documented token counts.
  - C: Metrics module — SelfBLEU, cosine diversity (all-MiniLM-L6-v2), PPL on a held-out human split. *Done =* all three run on dummy text and return sane values.
- **Fri Jul 10**
  - A: Sampling/generation step + generation-to-generation handoff (gen N's outputs become gen N+1's training data). Fix sampling params globally (see pilot spec — this is a confound if it drifts).
  - B: Noise injector (char swap/delete/insert at target CER). *Done =* measured CER on output within ±0.1% of target.
  - C: Tail-retention tracker — build the rare n-gram/entity list from the human corpus, count survival in generated text.
- **Sat Jul 11 — Integration day.** Full closed loop, 2 generations, tiny token budget. *Done =* one JSON of all metrics for gens 0–2. Team meeting: sanity-check the numbers against gen-0 human reference values.
- **Sun Jul 12**
  - Freeze pilot configs. Run a 1-generation timing test on both T4 and A100 to replace the runtime estimates below with measured numbers.
  - D (Aarav, back today): onboard; own the GPT-4 judge script + start the Related Work skeleton (due before Jul 19).
- **Mon Jul 13:** Launch pilot runs overnight. Buffer/debug day.
- **Known blockers to pre-empt:** Colab session timeouts (checkpoint-resume is mandatory, not optional), HF rate limits (cache datasets to Drive once), judge API budget (100 samples/gen/condition adds up — price it now).

### Week 7 (Jul 14–20): Pilot results + go/no-go
- Pilot results in hand by **Thu Jul 16**. Go/no-go meeting **Fri Jul 17** using the decision tree in Output 9.
- If GO: A builds the sweep runner (config-driven, resumable, one results CSV per run synced to Drive). B prepares all rescue sets for the reduced grid. C starts the **Reddit replication of Kovač et al. immediately** — it's the positive control for C4 and you want its answer before the full sweep finishes, not after.
- D: Related Work full draft done by Jul 18 (leaves the 19th).

### Week 8 (Jul 21–27): The sweep (reduced) + statistics
- **Run this grid, not the full 27×3:**
  - WikiText-103: all 27 cells at 1 seed (the descriptive surface) **plus** the 8 corner cells + 3 baselines at 3 seeds (the inferential backbone).
  - Reddit: composition axis only (length × noise at dose 5%, 9 cells, 1 seed) + Kovač-recipe cell at 3 seeds.
  - C4: cut it, or run only the best/worst/random triplet as an appendix generalization check. Two domains done well beat three done thin.
- **Statistics plan:** two-way ANOVA (dose × composition) on generation-5 endpoints for each primary metric; report effect sizes (η²) alongside p-values since n is small; Benjamini-Hochberg FDR across the metric family; seed-level SD as error bars on every figure. If ANOVA assumptions look shaky at n=3, fall back to a linear model with condition factors and say so plainly.
- Owners: A runs WikiText sweep, C runs Reddit + stats scripts, B does the analysis notebooks/heatmaps.

### Week 9 (Jul 28–Aug 3): Writing
- Order and owners: Methods (A, Mon–Tue) → Results (C, Tue–Thu) → Related Work polish (D, Mon–Wed) → Intro (B, Wed–Fri) → Abstract rewritten last, together (Sat).
- Figures final by **Fri Jul 31**.
- Main paper: Figures 2, 3, 4+5 (combined panel), 6, and the stats table. Appendix: per-domain trajectories, judge-score details, noise-injection examples, full 27-cell tables.
- Send full draft to mentor/PI **Sun Aug 2** — this is the deadline that actually matters, because their feedback loop needs a week.

### Week 10 (Aug 4–10): Polish + submit
- Aug 4–5: incorporate mentor/PI feedback; run any small patch experiments they demand.
- Aug 6: adversarial-review pass (this is when Batch 2's Output 5 gets written — against real results, where it's actually useful).
- Aug 7: OpenReview accounts for all authors; confirm the two workshop targets + one backup and their exact deadlines/formats (workshop CFPs differ on page limits — check now, not Aug 9).
- Aug 8–9: freeze, format check, reproducibility statement, camera-ready hygiene.
- Aug 10: submit with buffer. Never submit on the deadline day itself.

---

## OUTPUT 4: The Figure Plan

Six figures + one table. Read in order, they tell the whole story without the text.

**Figure 1 — Pipeline schematic** (diagram). The recursive loop: human corpus → gen-0 model → synthetic corpus → (+ rescue set, annotated with the three manipulated axes) → gen-1 model → … → gen-5, with metric probes at each generation. Proves nothing; buys reviewer comprehension in 10 seconds. *Caption:* "Recursive training with fixed-budget rescue injection. At each generation, the model trains on the previous generation's synthetic output plus a rescue set whose dose, document length, and character-level noise we manipulate independently. Total training tokens per generation are constant across conditions."

**Figure 2 — Collapse trajectories** (line plot, 2 panels). X: generation (0–5). Y: panel (a) embedding cosine diversity, panel (b) SelfBLEU. Four lines: no-rescue control, 10% random, best cell, worst cell; shaded seed SD bands. *Positive result:* fanning curves — control plunges, best cell stays near-flat, worst cell tracks closer to control than to random. *Null:* all rescue lines overlap inside the bands. *Proves:* C6, and visually previews C1. *Caption:* "Collapse trajectories over five generations. Without rescue data, diversity decays monotonically; rescue composition determines how much of that decay is prevented. Bands show ±1 SD over 3 seeds."

**Figure 3 — THE MAIN FIGURE: dose × composition heatmap** (heatmap, gen-5 endpoint). X: composition, ordered worst→best (short+noisy → long+clean). Y: dose (1%, 5%, 10%). Cell value: cosine diversity (or a z-scored composite of the primary metrics — decide once, early). *Positive result:* the gradient runs left→right (vertical banding: composition dominates), and the (5%, best) cell is brighter than the (10%, random) reference cell marked on the plot. *Null:* horizontal banding — brightness tracks dose only. *Proves:* C1 (and C5 if there's visible curvature). *Caption:* "Generation-5 semantic diversity across the dose × composition grid. [IDEAL CASE] A 5% dose of long, clean rescue data (starred) exceeds the 10% random baseline (circled), indicating composition can substitute for dose."

**Figure 4 — Length ablation** (bar chart with seed error bars). X: length bucket (short/medium/long). Y: gen-5 cosine diversity and tail retention (grouped bars), at dose 5%, 0% CER. *Positive:* monotone rise with length, gaps exceed error bars. *Null:* flat within error bars. *Proves:* C2. *Caption:* "Effect of rescue-document length at fixed dose and zero noise. Error bars: ±1 SD over 3 seeds."

**Figure 5 — Noise ablation** (line plot, two y-axes or two panels). X: CER {0%, 1%, 5%}. Y: LLM-judge quality and held-out PPL. *Positive:* flat 0→1%, visible drop at 5% — a threshold, not a slope. *Null:* flat throughout, or monotone from zero. *Proves:* C3. *Caption:* "Effect of character-level noise in rescue data. [IDEAL CASE] Light corruption (1% CER) is harmless; heavy corruption (5%) degrades output quality without improving diversity."

**Figure 6 — The Kovač transfer test** (grouped bars). Groups: Reddit vs. WikiText-103. Bars within group: Kovač-optimal recipe, our best recipe, random rescue, no rescue. Y: gen-5 cosine diversity. *Positive control:* Kovač recipe clearly wins on Reddit (replication holds). *The question:* whether it still wins on WikiText-103. Either answer is the C4 result. *Caption:* "Domain transfer of Kovač et al.'s optimal rescue composition. Replication on short-form social media (left) validates our pipeline; long-form formal text (right) tests their stated generalization caution."

**Table 1 — Statistical summary.** ANOVA main effects and interaction per primary metric: F, p (BH-corrected), η². Proves the figures aren't seed noise.

---

## OUTPUT 9: The Pilot Spec (run this next week)

**Purpose:** validate that the corner-to-corner effect exists before spending the sweep budget.

**Conditions (6 runs, not 4):**
1. Dose 1%, short docs, 5% CER — worst corner
2. Dose 1%, long docs, 0% CER
3. Dose 10%, short docs, 5% CER
4. Dose 10%, long docs, 0% CER — best corner
5. No-rescue control — run at **2 seeds** (this pair is your noise-floor estimate; without it the go/no-go criterion is meaningless)
6. Random 5% rescue — the Gerstgrasser anchor

**Why corners:** they maximize expected effect size. If the extreme corners don't separate, the interior 27-cell grid has nothing to find, and you learn that for 6 runs instead of 27.

**Token budget:** 10M tokens/generation for the pilot [VERIFY this is enough for measurable collapse by gen 3 — Shumailov saw drift early at small scale, but confirm on your gen-0→2 integration run before committing].

**Runtime (replace with Sunday's measured numbers):** Pythia-160M training at 10M tokens is the cheap part (~20–40 min/gen on T4 at fp16 [VERIFY]); autoregressive *generation* of the next 10M-token synthetic corpus is the expensive part (~2–4 h/gen on T4, ~45–75 min on A100, heavily dependent on batch size and max length [VERIFY with the timing run]). Ballpark: **12–20 h/condition on T4, 4–7 h on A100.** Six conditions ≈ 1 A100-Colab week. This is why the full 27×3 grid was never going to happen.

**Data prep checklist:** wikitext-103-raw-v1 via HF datasets, cached to Drive → strip section headers, dedupe → carve a 5M-token held-out PPL split that never touches training → build the rare n-gram/entity list (bottom-decile frequency, appearing ≥3 times) → construct token-matched length buckets → apply noise at the character level *pre-tokenization*.

**Code validation checklist (before any overnight run):**
- Overfit sanity run: 1k steps on 100k tokens, loss must crater.
- Verify the realized rescue fraction by counting tokens, not by trusting the config.
- **Fix sampling parameters (temperature, top-p, max length) once, globally, matched to Kovač et al. where possible** — if sampling params drift across conditions, they confound everything downstream.
- Checkpoint-resume actually resumes (kill a run mid-generation and restart it).
- Compute all metrics on gen-0 human text first; these are your reference values and your bug detector.

**Decision tree (Fri Jul 17 meeting):**
- **Corners separate by gen 3** (Δ > 2× the seed SD from the control pair, on ≥2 primary metrics) → GO: full reduced sweep per Week 8.
- **Separation on some metrics only** → GO, but promote the separating metrics to primary and demote the rest; adjust the figure plan.
- **No separation by gen 3** → do NOT run to gen 5 and hope. Instead: (a) extend two conditions to 8 generations at a smaller token budget — collapse may just be slow on formal text (itself a finding); if still nothing, (b) pivot to a fine-grained dose-only sweep (0.5%–20%, 7 levels, 3 seeds) answering "how much human data is enough?" — which is literally the paper's title, is cheaper than the grid, and has no published answer for this domain.

---

## OUTPUT 10: The Positioning Memo

Team —

Straight answer on the venue question, because the plan depends on it. This paper, executed perfectly, is a very strong workshop paper and a plausible COLM or EMNLP Findings paper. It is not a NeurIPS Main paper, and it's worth being honest about why: Main reviewers on training-dynamics work will ask for multiple model scales, three-plus seeds on everything, and a mechanism. We have one 160M model, a Colab budget, and five weeks. Pretending otherwise would push us toward the classic failure mode — an over-scoped grid, run once, with no error bars, that a reviewer at *any* venue can dismiss in one sentence: "how do I know this isn't seed noise?"

So we optimize for the version of rigor we can actually afford: fewer cells, more seeds, real statistics, and one replication that bulletproofs the framing. The Kovač replication on Reddit is the single most important experiment we run that isn't the headline result — it's what turns "we tried a different domain" into "we validated our pipeline on their domain, then showed their recipe does/doesn't transfer." That sentence is the paper.

The most important finding, if we get it, is the Figure 3 star-vs-circle comparison: 5% well-chosen beats 10% random. If that holds with error bars, we have a practitioner-relevant, quotable result. If it doesn't hold, the fallback is genuinely fine — a quantified "dose dominates in formal text, contra the social-media picture" answers our own title and still fills the Kovač gap.

Biggest risk, ranked: (1) the pipeline isn't closed yet and it's Thursday of Week 6 — every day without a running loop is a day subtracted from experiments, not from writing; (2) effects smaller than seed noise, which the pilot exists to catch cheaply; (3) the Reddit replication failing, which would mean a bug we need to find before anything else matters.

Next 14 days: close the loop, run the pilot, run the replication. That's it.

Do NOT spend time on: repo aesthetics, CI, badge collections, the C4 domain, prose for Methods or Intro before pilot numbers exist, or debating venue further. Writing before results is how you end up rewriting everything in Week 9 anyway.

If — and only if — the pilot shows corner separation at >4× seed SD and the mentor can find real GPU hours, we revisit adding Pythia-410M as a second scale. That's the one upgrade that meaningfully moves us toward the stretch venues. Everything else is polish.

— (mentor-facing draft; edit tone to taste)

---

## THE ONE THING

Get one complete recursive generation to run end-to-end **by Saturday**: one condition, one generation, tiny token budget, all five metrics computed and written to a JSON. Not the pilot, not the grid — one closed loop. Every artifact in this document, every figure, every claim, every statistical test, is downstream of a pipeline that does not yet exist, and it is Thursday of Week 6. Until train → generate → retrain → measure runs without a human touching it, this project has a proposal and a plan but no experiment. Close the loop first.
