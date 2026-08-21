# Message to mentors - copy from the line below

Written for readers who have not been following the technical detail. It says where the
project stands, what the result is in plain terms, what we need from them, and asks about
submission paperwork. The long technical version is in `docs/HANDOVER_2026-08-20.md`; the
earlier detailed draft of this message is in git history if it is ever wanted back.

Plain ASCII on purpose. Typographic characters do not survive a paste into most mail
clients, and nobody types them by hand.

---

Hi Laryn, Charlotte,

An update on where we've landed, plus a few things I need from you.

**The experiment is finished.** All 25 training runs completed on 20 August, none failed,
and the results passed the fairness checks we committed to in advance. The paper is written.
Nothing left needs more compute, and the GPU budget is spent and closed out.

**Our main hypothesis didn't pan out.** The idea was that being smart about *when* you spend
a limited budget of human-written training data, on top of being smart about *which* data
you spend it on, would beat doing just the second. It doesn't. The two come out equivalent,
and we designed the study well enough to say "genuinely equivalent" rather than "we couldn't
tell the difference" - which is a real result, just not the one we were hoping for.

What did show up underneath is solid. Using human data at all clearly helps. Choosing which
human data to use helps quite a bit more. Timing barely registers. So the paper reports an
honest negative on our headline question and a clear positive on the part beneath it.

**What I need from you**

1. **A statistics read. This is the main one.** The result rests on a threshold for what
   counts as "close enough to call equal". We fixed that threshold before looking at any
   outcomes, but nobody outside the project has reviewed it, and it's the most likely thing
   a reviewer goes after.
2. **Sign-off on twelve design decisions** I made as owner that the team never formally
   ratified. A few sit in other people's areas.
3. **Someone who didn't run the experiment to sign the validity certificate.** All the
   mechanical evidence is already gathered, so what's left is judgement and a signature.
4. **A venue call.** We're aimed at EvoRobust, due 29 August. My own read is that AXIOM fits
   our topic better, same deadline. Happy to be overruled, but you should know we didn't
   pick on fit.

**And one logistics question: when can we get the forms for sending it out?** The deadline
is 29 August and I'd rather not have paperwork be the thing that stops us.

The paper is attached if you want the detail, and the limitations are written up honestly in
it rather than tucked away - including one earlier version of this experiment that we ran,
found invalid, and threw out. Happy to walk through any of it live.

Ronit
