# Message to mentors - copy from the line below

Short and conversational on purpose: a message, not a letter. It assumes the mentors already
have access to the Overleaf project and the GitHub repository, and frames this as the final
review before submission. The one question it asks is about submission paperwork.

Earlier drafts asked for a statistics review, ratification of the open decisions, and a
certificate signature. Those asks were dropped at the owner's direction on 2026-08-20.
**They remain open work** - see `docs/SUBMISSION_CHECKLIST.md` and
`docs/HANDOVER_2026-08-20.md`. Not asking here does not close them. Longer drafts, including
a full technical version, are in git history.

Plain ASCII on purpose. Typographic characters do not survive a paste into most mail and
chat clients, and nobody types them by hand.

---

Hi Laryn, Charlotte,

Quick one - the experiment's finished, so this is basically the final review before we
submit.

All 25 training runs completed on 20 August, none failed, and the whole thing came in around
$18 of GPU time. The paper's written, and every number in it is generated straight from the
run data rather than typed in.

Short version of the result: our main hypothesis didn't hold. We thought that being smart
about *when* you spend a limited budget of human-written training data, on top of being
smart about *which* data you spend it on, would beat just doing the second. It doesn't - the
two come out equivalent. What does clearly matter is which data you pick. Timing barely
registers. Not the result we were hoping for, but it's a clean one.

It's all in the Overleaf project and the GitHub repo you both have access to, so have a look
whenever you get a chance. The one soft spot I'd point you at: the result rests on a
threshold for calling two things "equivalent". We set it before seeing any outcomes, but
it's the thing a reviewer would go after first.

Main thing I need from you - when can we get the forms for sending it out? We're aiming at
EvoRobust, deadline 29 August. We're done on our end and I'd rather paperwork wasn't what
costs us.

Thanks both.

Ronit
