---
name: vet-idea
description: >-
  Vet a product, app, business, or feature idea against the real market before
  building it — scope the concept, survey competitors (paid and open source),
  test commercial viability, clear every source and dependency for licensing and
  compliance risk, then land a short, memorable name plus positioning and
  messaging. Use whenever the user wants to plan a new product or app, asks
  "does this already exist", "is this a good idea", "who else is doing this",
  "can this be monetized", "what am I missing", "is this name taken", "what
  should we call it", wants a market assessment, competitive landscape,
  enhancement backlog, naming, positioning, taglines or marketing copy, or asks
  whether a data source or library is safe to use commercially (MIT, Apache,
  GPL/AGPL, ODbL, CC-BY-NC, scraping/ToS). Also run proactively after drafting a
  spec and before any code is written. Owns the `idea-dossier/` knowledge base.
  Run early, and revisit whenever the concept shifts. Not for products already
  shipped with real usage data — measurement beats research once traffic exists.
---

# Vet an idea

Turn an idea into a decision, backed by research rather than enthusiasm — then
give it a name people remember and a claim you are legally allowed to make.

## The point of this skill

Most idea evaluation is motivated reasoning with citations. This skill is built
to **disconfirm**.

The scoring is meant to be *unflattering*. A vetting pass that returns nothing
but validation is telling the user what they want to hear, and they will stop
trusting it — exactly as a job-scoring system that only produces 8s and 9s
becomes worthless. If a pass produces no corrections, assume the research was
too shallow, not that the idea was flawless.

The valuable findings change the plan: the thing already exists, the moat is
commoditized, the business model is blocked by margin structure, the name is
taken, or a dependency's license quietly forces the whole product open.

## What this is *not*

Not a pitch deck and not a validation exercise. It will not produce a
market-size number designed to look big.

Not a substitute for talking to real buyers. Research narrows what to test.

**Not legal advice.** Job 4 surfaces licensing and compliance risk so a lawyer
can be pointed at the real questions. Where money, copyleft, or personal data
are involved, say plainly that counsel should confirm.

Not financial advice. Present trade-offs; never guarantee an outcome.

## How it works

**All research artifacts go in `idea-dossier/` in the project folder** — never
loose at the project root, where they get confused with product documentation.
The folder is self-documenting: `00-index.md` opens by stating what the folder
is and that it is decision support, not product spec.

Each file has one owning Job that writes it; every other Job reads it. The
dossier is the single source of truth, so work can stop, resume, and be revised
when the concept shifts.

| File | Owner | Contents |
|---|---|---|
| `00-index.md` | Job 0 | Folder intent, status table, append-only decisions log, verified-vs-assumed register |
| `01-concept.md` | Job 1 | What it is, who for, constraints, differentiating claim, what it is *not* |
| `02-landscape.md` | Job 2 | Competitor clusters and entries, "why now" |
| `03-viability.md` | Job 3 | Counterparty economics, willingness to pay, business models, kill criteria |
| `04-clearance.md` | Job 4 | Source register — every dependency and data source, its license, obligation, verdict |
| `05-positioning.md` | Job 5 | Name, collision check, positioning statement, messaging, taglines |
| `06-backlog.md` | Job 6 | Ranked enhancement backlog, open research questions |

A technical spec lives *outside* the dossier as a normal `SPEC.md` at the
project root — the dossier vets it. For a small idea, collapse into fewer files;
don't manufacture a viability document for something with no commercial
dimension.

Work the Jobs in order. Each can invalidate an earlier one; when it does, **go
back and edit the owning file**, don't append a contradiction.

---

## Job 0 — Set up the dossier

Create `idea-dossier/00-index.md`: a one-line statement of the folder's purpose,
a status table (one row per file: Not started / Draft / Researched / Revised),
an append-only **decisions log**, and a **verified-vs-assumed register**.

The register is the spine. Every material claim is tagged *verified* (source and
date) or *assumed*. Its job is to make it impossible to quietly promote a guess
into a fact — the failure mode that makes idea documents dangerous months later.

Update the status table at the end of every Job. Log consequential decisions
with reasoning and date.

## Job 1 — Scope the concept

Write `01-concept.md`: what it does, for whom, hard constraints (budget,
geography, platform, licensing), inputs and data needed, phased build.

Two required sections:

- **The differentiating claim**, in one falsifiable sentence. Job 2 exists to
  attack it.
- **What this is *not*.** Naming the excluded adjacent product sharpens every
  later decision and prevents scope drift.

If constraints are unstated, ask before researching. "Free only" and "US only"
reshape an architecture completely.

**Collision gate:** if a working name already exists, run a quick collision
search now (see Job 5) and flag it immediately. Attachment to a name grows fast;
a five-minute check on day one prevents a rename later.

## Job 2 — Survey the landscape

Write `02-landscape.md`. **Run searches in parallel, breadth before depth.**

Head the file with a dated snapshot notice: *"Research snapshot as of
&lt;month year&gt;. Pricing and features from public sources — verify before
quoting externally."* Stamp each competitor entry with the date reviewed.

**Round 1**, one message, one search per cluster: consumer/commercial products;
adjacent products solving one *piece*; open source (`github <domain> <function>`);
professional/enterprise tools.

**Round 2** targets what Round 1 made interesting — usually the closest
competitor's actual method, and a direct search for the specific gap you believe
exists.

Search for the **gap itself**, not just the category. A specific integration
query returning nothing is a real finding; a category query returning fifty
results tells you little. Record the query when claiming white space.

Summarize as a category table: cluster, representative tools, what they do,
typical price. State for each whether to **compete, avoid, or integrate**.

### Competitor entries

For the two or three closest analogs, write a full entry:

> **&lt;Name&gt;** (reviewed YYYY-MM-DD) — link, one-line positioning, price,
> architecture, business model.
>
> **Convergence.** Where they independently reached your conclusions. Separate
> teams arriving at the same core principles without contact is about as much
> design validation as an unbuilt product can get.
>
> **Worth stealing (ranked).** What they have that you don't, by value. Name the
> mechanism, not the feature label.
>
> **Where we differ (lean in).** Real, defensible differences — as things to
> emphasize, not just contrasts.
>
> **Structural gaps we accept.** What they do better that you won't close. A
> landscape with no conceded ground is not honest.

Three findings change decisions more than any others:

- **Is a piece you think is your moat already a mature standalone category?**
  Usually not defeat but "integrate rather than build," which can collapse the
  most expensive phase.
- **Does an expensive professional tool already do all of it?** The most
  informative finding available — validates the combination, disproves its
  novelty, relocates the opportunity to packaging and audience.
- **What is genuinely unoccupied?** Usually a data source nobody integrated.

### Why now

Close with the forcing function. An idea equally possible five years ago and
five years hence usually isn't a good one. Look for a dataset that became free
or complete, a regulation, a cost curve, a cultural shift, a crisis. If nothing
changed, ask why nobody has done it — sometimes oversight, more often a reason.

This paragraph is reused directly as the trend layer in Job 5.

## Job 3 — Test viability

Write `03-viability.md`. Only meaningful once the landscape is known.

**Research the counterparty's actual economics, not your own projections.**
Margin structure decides business models. An industry running 4% net margins
cannot pay a 10% referral fee — the number is the answer, not a negotiating
position. Get the real figure from trade press or industry analysts.

**Find where the money actually sits.** Frequently not the party you first
considered: upstream of the retailer, in an adjacent higher-margin service, or
in someone else's budget — a utility, an insurer, a municipality.

**Establish willingness to pay from what people already spend on imperfect
substitutes.** If people pay professionals thousands for a worse version of the
output, WTP is proven and the risk is price point and segment, not demand. If
the current workaround is free, monetization is roughly an order of magnitude
harder. Say which this is.

**Check whether monetization conflicts with the core claim.** If the value is
impartial recommendation, paid placement corrodes it. Define the firewall: what
money may influence, and what it may never influence.

Run the idea against `references/question-bank.md`. Answer what is unanswered
*and* material; push the rest to `06-backlog.md`.

End with **kill criteria** written before attachment sets in, and name the
single load-bearing risk. If everything is a risk, the analysis isn't finished.

## Job 4 — Clear the sources

Write `04-clearance.md`. **Do this before building, not before launching** — a
copyleft dependency discovered late can force a rewrite or force the product
open.

Build a **source register**: every third-party data source, dataset, library,
API, and scraped source, with one row each.

| Source | What it gives us | License | Obligation | Commercial OK? | Verdict |
|---|---|---|---|---|---|

Fill it using `references/license-obligations.md`, which covers the obligations
and traps for MIT, Apache-2.0, GPL, AGPL, ODbL, CC variants, public domain, and
scraped/ToS-governed sources. The four that most often cause real damage:

- **Copyleft propagation.** Linking one GPL library into an otherwise permissive
  project can subject *the entire work* to GPL on distribution.
- **AGPL §13 network use.** Web products don't escape copyleft by never shipping
  a binary — AGPL was written specifically to close that gap, and a modified
  AGPL program served over a network obliges you to offer users the source.
- **Non-commercial data.** CC-BY-NC blocks commercial use outright. The moment
  money is involved you need a separate agreement with the rights holder. This
  routinely traps otherwise-free datasets that a "free sources only" constraint
  waved through.
- **Database share-alike.** ODbL permits commercial use but distinguishes a
  *Derivative Database* (share-alike applies) from a *Produced Work* (any terms
  you like, but you must offer the derived database on request). Getting this
  distinction wrong is the common OpenStreetMap-derived mistake.

Also flag: attribution/NOTICE obligations, patent and trademark clauses, license
incompatibilities between chosen dependencies, terms-of-service and scraping
exposure, and any regulated-data handling (personal data, health, financial,
minors) that brings statutory duties independent of licensing.

Close with a **verdict per source** — clear / clear with obligation / needs a
license / replace — and a shortlist of questions for actual counsel. Prefer
public-domain government data as the safe core wherever a substitute exists, and
say so when a paid license would remove a whole class of risk.

## Job 5 — Name it, position it, say it

Write `05-positioning.md`. This is the payoff Job: everything before it exists to
make these choices non-arbitrary.

### Job 5a — The name

Aim for **short, memorable, and fun**. Two or three syllables, spellable after
hearing it once, pleasant to say. Personality beats descriptive accuracy — a
name's job is to be remembered and owned, not to explain the product. The
tagline explains; the name sticks.

Use `references/naming-playbook.md` for the generation strategies, the scoring
rubric, and the screening tests. In brief:

- **Generate across strategies**, not from one idea you like: evocative (Nest,
  Kindle, Slack), invented (Kodak, Xerox), compound (Microsoft), metaphorical,
  oblique. Invented names are the holy grail of ownability and are almost always
  trademarkable.
- **Expect the obvious ones to be gone.** Every name that directly expresses a
  category's core virtue is already taken, usually by firms in that category.
  Survivors are oblique or invented. Plan for this rather than being surprised.
- **Collision-check every finalist** — live products in the category,
  trademarks, software-sector registrations, domains and handles. A live product
  in your exact space is disqualifying, not a hurdle. Check that the name plus a
  searchable descriptor is clean too, not just the bare word.
- **Screen** for pronunciation, spelling-after-hearing, and unintended meanings
  in other languages before committing.

Present a ranked shortlist with the collision status of each, and a
recommendation. Record the check and its resolution — cheap now, expensive after
launch.

### Job 5b — Positioning

Use the components of April Dunford's framework, which map onto work already
done in earlier Jobs:

| Component | Comes from |
|---|---|
| **Competitive alternatives** — what they'd do if you didn't exist, including "nothing" and "a spreadsheet" | Job 2 |
| **Unique attributes** — what you have that alternatives don't | Job 1 claim, tested by Job 2 |
| **Value themes** — the value those attributes deliver, in the customer's words | Job 3 |
| **Who cares a lot** — the segment that values it disproportionately | Job 3 |
| **Market frame of reference** — the category you ask to be judged in | Judgment call, argued here |
| **Trend (the +1)** — why this matters now | Job 2 "why now" |

The frame of reference is the highest-leverage decision. Choosing the category
you're compared against determines which strengths read as important and which
read as irrelevant. Argue for the frame that puts real strengths at the centre —
and never claim a strength Job 4 says you can't legally make.

### Job 5c — Messaging

Short, concrete, and in the customer's language:

- **One-liner** — what it is and who it's for, in a sentence a stranger repeats
  correctly.
- **Three value themes**, each with the proof point that earns it. Proof from the
  dossier, not adjectives.
- **Taglines** — draft several, keep the sharpest. Reward wit and rhythm; a
  little fun is memorable and most competitors won't risk it.
- **The one-sentence "not"** — what it deliberately isn't. Sharpens the rest.

Test the one-liner by whether someone could repeat it after hearing it once. If
it needs a preamble, it isn't finished.

## Job 6 — Consolidate

Write `06-backlog.md`, then reconcile everything.

Two ranked halves:

1. **Enhancement backlog** — what the market has that this doesn't, drawn from
   the "worth stealing" sections. The most directly actionable output.
2. **Research backlog** — questions still unanswered, prioritized. Usually the
   most valuable section, because it names what you don't know instead of
   hiding it.

Then fold findings **back into the owning files and the external spec**:

- Revise undermined claims in place, marking that they were revised and why
- Add newly discovered features to the spec, not only the landscape file
- Update the risk register, including **downgrades** — research that weakens a
  risk matters as much as research that raises one
- Sequence monetization against the build phases
- Propagate any rename through every file
- Update the status table and decisions log

## Output to the user

A short plain-language summary, not a document tour:

- What changes the plan, **first**
- The differentiating claim: survived, narrowed, or dead
- Any licensing or compliance finding that blocks or constrains
- The name, with its collision status
- The single load-bearing risk
- A recommendation — build first, skip, validate before spending

## Research method

- **Parallel searches, one message.** Four per round; two rounds is usually
  right. Serial searching wastes the user's time.
- **Search the negative.** Absence of results for a specific integration is
  evidence of white space. State it with the query.
- **Numbers over adjectives.** "Low margin" is an opinion; "4% net margin,
  &lt;source&gt;" is a finding.
- **Find the benchmark to beat.** A competitor's published outcome number is the
  bar, and beats any feature comparison.
- **Prefer trade press and industry bodies** over listicle SEO farms.
- **Cite everything**, inline as markdown links, with dates.

## A note on honesty

Markets are uncertain and you cannot promise outcomes. Be candid about risk and
saturation rather than optimistic by default — a clear-eyed assessment that
finds a real gap is worth more than reassurance. Frame commercial claims as
informed reasoning, not guarantees.

**Correct yourself out loud.** When research contradicts something said earlier,
say so directly and revise the owning file. A quietly edited claim is worse than
no research at all; unflagged reversals destroy the value.

**Report disconfirming findings first.** Lead with what changes the plan.

**Don't inflate a gap.** "Nobody combines X and Y" is only meaningful if
combining them is hard or valuable. Say which, or say neither.

**Separate technical risk from business risk,** and say which is load-bearing.
It is usually the business one, and it usually gets less attention.

**Never let marketing outrun the evidence.** Job 5 sells what Jobs 1–4 proved.
A tagline that claims more than the dossier supports is the fastest way to make
the whole document untrustworthy — and, where the claim is about legal
compliance or performance, actionable.
