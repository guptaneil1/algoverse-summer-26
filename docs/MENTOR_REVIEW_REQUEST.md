# Message to mentors - copy from the line below

A status read for people who have not been following the detail: what the project asked,
what we built, what came out, and where it stands now. It is deliberately not a list of
requests. The one question it asks is about submission paperwork.

Earlier drafts of this message asked the mentors for a statistics review, ratification of
the open decisions, and a certificate signature. Those asks were dropped from the message on
2026-08-20 at the owner's direction. **They are still open work** - see
`docs/SUBMISSION_CHECKLIST.md` and `docs/HANDOVER_2026-08-20.md` - and dropping them from
this message does not close them. The longer draft is in git history.

Plain ASCII on purpose. Typographic characters do not survive a paste into most mail
clients, and nobody types them by hand.

---

Hi Laryn, Charlotte,

Wanted to give you a proper picture of where this project has ended up, since neither of you
has had the running commentary.

**The question we set out to answer.** When language models get trained on text produced by
earlier language models, quality drifts over generations and the rarer corners of human
writing start to disappear. The obvious fix is to keep feeding in real human-written text.
But human text is the scarce, expensive input, so the practical question is how to spend a
limited supply of it well. We narrowed that to two decisions: *when* across the training
generations you spend your budget, and *which* under-represented kinds of writing you spend
it on.

**What we built and ran.** A full recursive training pipeline: train a model, have it
generate text, mix in a controlled amount of human data, train the next generation on that,
and repeat ten times over. We ran that 25 times - five different spending strategies across
five fixed random seeds - on GPT-2 with WikiText-103. It finished on 20 August. All 25 runs
completed, none was thrown out, and it cost about $18 of GPU time.

The hard part wasn't the training, it was fairness. If one strategy gets to see more data
than another, any difference you measure afterwards is meaningless. Getting every strategy
onto exactly the same total training volume and the same human-data budget took two
attempts: the first version of the grid failed its own fairness check, so we discarded it
and rebuilt.

**What we found.** Our headline hypothesis was that doing both things well, choosing when
*and* choosing what, would beat choosing what on its own. It doesn't. They come out
equivalent. We were careful enough with the design to tell "these are genuinely the same"
apart from "our experiment was too noisy to detect a difference", which matters, because
those two look identical in a sloppy study.

The result underneath it is the more useful one. Spending human data at all helps. Choosing
*which* human data helps considerably more. Timing barely moves the needle. So the practical
takeaway is to worry about what you buy, not when you buy it.

**Where it stands now.** The paper is written and builds. Every number in it is generated
straight from the run data rather than typed in by hand, so the text can't drift out of sync
with the results. The raw artifacts are archived on GitHub with checksums, so anyone can
verify them rather than take our word for it. The compute is released and the budget is
closed. Nothing left on this needs a machine.

**Two things I'd flag honestly.** A negative result leans harder than a positive one would
on the threshold for what counts as "close enough to call equal". We fixed ours in advance
and documented it, but it's the part I'd expect a reviewer to press on. Separately, a few
comparisons we originally planned were never implemented, so we can't say how far any of
these strategies sits from the best achievable. Both are written into the paper rather than
left out of it.

**One thing I need to know:** when can we get the forms for sending it out? We're aiming at
EvoRobust and the deadline is 29 August. Everything on our end is finished, and I'd rather
paperwork wasn't the thing that costs us the deadline.

Paper attached. Happy to walk through any of it.

Ronit
