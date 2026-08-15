# Licensed Domain Audit

**Deliverable:** `docs/weekly/WEEK_1.md`, Neil — "Audit at least two licensed candidate domains and
recommend primary/fallback choices."

**Retrieved:** 2026-08-15. License and configuration facts below were read from the Hugging Face
dataset API in that session and are cited inline. Facts not verified in that session are marked
**UNVERIFIED** and must not be relied on without checking.

**Status:** RECOMMENDATION ONLY. This audit does not resolve `DECISIONS.md` U-002. Selecting the
final domain is a team decision and must be recorded in `DECISIONS.md` before any dataset download
used for experiments (see §6).

## 1. Requirements a candidate must satisfy

Derived from `PROTOCOL.md` §3 and `docs/PROJECT_CONTEXT.md`:

1. **License permits ML training, derivative distribution, and publication.**
2. **Five disjoint partitions are constructible** — base train, rescue candidates, prompts,
   validation, final test (`PROTOCOL.md` §3, data separation).
3. **A principled mode partition exists** — the project requires a frozen monitored partition of the
   human reference into modes, including identifiable tail modes.
4. **Size fits a 124M–160M screening model** across 10 recursive generations on modest compute.
5. **Provenance is stable and hashable** — a fixed revision that will not shift underneath us.
6. **No personal-data or consent problems.**

## 2. Candidate A — WikiText-103 (RECOMMENDED PRIMARY)

| Field | Value |
|---|---|
| Hub ID | `Salesforce/wikitext` |
| Config | `wikitext-103-v1` (raw variant `wikitext-103-raw-v1` also available) |
| License | **CC-BY-SA-3.0 and GFDL** (verified via Hub API, 2026-08-15) |
| Source | Verified Good and Featured English Wikipedia articles |
| Scale | ~103M tokens |

**Against the requirements:**

1. **License — PASS.** CC-BY-SA-3.0 permits training, derivatives, and redistribution. ShareAlike
   obligations attach to redistributed *derivative text*. Our releases distribute manifests, hashes,
   metrics, and aggregates rather than corpus text, which keeps the obligation light — but if any
   generated-text sample is published as an appendix, the ShareAlike and attribution terms must be
   honored. Record attribution in `data/datasheet.md`.
2. **Partitions — PASS.** Canonical train/valid/test splits already exist. Per
   `configs/data/wikitext103.json`, the canonical train split re-partitions into base_train and
   rescue_candidates, and the canonical test split is held out as final test. Prompts must be carved
   from train or validation, never test.
3. **Modes — PASS, and this is the deciding advantage.** Article-level structure supports two
   defensible mode definitions, both already listed in `configs/data/wikitext103.json`:
   article-category (broad topic label) and article-length quantile (tail = bottom decile by token
   count). Both are computable from the corpus without external annotation, and both are
   independent of any policy selection score — which `PROTOCOL.md` §4 requires of the tail measure.
4. **Scale — PASS.** ~103M tokens against a 124M–160M model over 10 generations is the intended
   screening regime.
5. **Provenance — PASS.** Pin the Hub revision SHA at download and hash every partition.
6. **Personal data — PASS.** Encyclopedic content, already public, no consent issues.

**Relationship to the positive control:** upstream Drayson defaults to `wikitext2`, the smaller
sibling from the same family and the same Hub repository (see `docs/evidence/upstream_pin.md` §3).
Running Stage A on `wikitext2` and Stage B on WikiText-103 keeps the positive control a faithful
replication while giving the pilot more tokens, and the shared preprocessing lineage means
tokenization and cleaning behavior carry over. This is the strongest argument for WikiText-103 over
any unrelated corpus.

## 3. Candidate B — C4 `realnewslike` (RECOMMENDED FALLBACK)

| Field | Value |
|---|---|
| Hub ID | `allenai/c4` |
| Config | `realnewslike` (~15GB); other configs `en` ~305GB, `en.noclean` ~2.3TB, `en.noblocklist` ~380GB |
| License | **ODC-BY** (verified via Hub API, 2026-08-15) |
| Source | Cleaned Common Crawl web text; each record carries `text`, `timestamp`, `url` |

**Against the requirements:**

1. **License — PASS with a caveat.** ODC-BY is permissive for training and derivative works.
   However, ODC-BY governs the *database*; it does not grant rights in the underlying third-party
   web pages. Fine for internal training and metric publication, weaker if raw excerpts are
   republished.
2. **Partitions — PASS.** Large enough that all five partitions can be sampled disjointly with room
   to spare.
3. **Modes — PASS, with a different flavor.** The `url` field enables source-domain modes
   (publisher-level strata) and `timestamp` enables temporal modes. Domain-based modes are arguably
   a *better* match for the project's "under-covered mode" framing than length quantiles, because
   they correspond to real distributional strata rather than a proxy. This is C4's main advantage.
4. **Scale — PASS but requires subsampling.** Even `realnewslike` at ~15GB vastly exceeds what a
   160M model needs for 10 generations. A frozen subsample with a recorded seed and hash becomes a
   required extra preprocessing step, and that step is an additional place for leakage to enter.
5. **Provenance — PASS.** Pin the revision; hash the subsample.
6. **Personal data — WEAKER.** Web-scraped text can contain personal information. `en.noblocklist`
   in particular removes safety filtering and should not be used. `realnewslike` is the safest
   configuration on this axis.

**Why fallback rather than primary:** the mandatory subsampling step adds preprocessing risk and
consumes time the schedule does not have, and it breaks the lineage with the positive control.

## 4. Candidates deliberately not audited

Listed so the omission is visible rather than silent. **UNVERIFIED** — if any of these is
reconsidered, it must receive a full §2-style audit first.

| Candidate | Reason for deprioritization |
|---|---|
| The Pile | Composite corpus; component licenses are heterogeneous and at least one component has attracted copyright dispute. Clearing it would consume more time than the schedule allows. |
| OpenWebText | Reddit-outbound scrape with no clear upstream license grant. Fails requirement 1 on its face. |
| BookCorpus | Well-documented provenance and licensing problems. Should not be used. |
| Dolma | Plausible on license and scale, but its size and custom license terms need real review; not attempted here. |

## 5. Recommendation

| Role | Choice |
|---|---|
| **Stage A positive control** | `wikitext2` — upstream default, unchanged, no deviation |
| **Stage B pilot primary** | **WikiText-103** (`Salesforce/wikitext`, config `wikitext-103-v1`) |
| **Stage B fallback** | C4 `realnewslike` (`allenai/c4`) |

The primary recommendation matches the choice already provisionally encoded in
`configs/data/wikitext103.json`, so adopting it requires no rework of Neil's existing partition
code.

**One correction to that config:** its `source_url` reads
`https://huggingface.co/datasets/wikitext`. The canonical location is now
`https://huggingface.co/datasets/Salesforce/wikitext`. Update before freezing.

## 6. What still requires a human decision

This audit **recommends**; it does not **freeze**. Before any experimental download:

1. Team accepts or rejects the primary/fallback recommendation.
2. The decision is recorded in `DECISIONS.md`, closing U-002 with date, alternatives, and what
   evidence would reverse it.
3. Neil pins the exact Hub revision SHA and records it in `configs/data/wikitext103.json`.
4. Neil chooses **one** mode definition — article-category or length-quantile — and freezes it.
   Both are viable; picking both and choosing later after seeing outcomes would violate
   `PREREGISTRATION.md`.
5. The mode choice is checked for independence from the policy's `undercoverage_score`, per the
   Week 2 reliability-and-independence audit.
