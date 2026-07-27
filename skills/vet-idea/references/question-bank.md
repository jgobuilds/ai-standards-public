# Question bank

Questions that are easy to skip and expensive to skip. Run the idea against
these before finishing. Answer the ones that are unanswered *and* material;
list the rest in the research backlog.

Each is here because it commonly goes unasked, not because every idea needs it.

---

## Naming and identity

Full treatment in `naming-playbook.md`. The questions that must not be skipped:

**Is the name already used by a live product in this exact category?**
Disqualifying, not a hurdle. Check before any public artifact exists.

**Did you vet a batch, or fall for one candidate?** Expect direct expressions of
the category's core virtue to be taken. Survivors are oblique or invented.

**Does the name plus its descriptor clear too?** Not just the bare word.

## Licensing and compliance

Full treatment in `license-obligations.md`. The questions that cause real damage
when skipped:

**Is any dependency copyleft, and does it reach the whole work?** One GPL library
can subject an entire distributed product to GPL. Check the transitive tree.

**Is this a network service with an AGPL dependency?** Serving over a network
does not avoid copyleft — AGPL §13 exists precisely to close that gap.

**Is any "free" data source actually non-commercial?** CC-BY-NC data is free to
download and unusable in anything you monetize, including free products funded
by ads or referrals. The classic trap in a "free sources only" project.

**For database sources, is the output a Derivative Database or a Produced Work?**
Under ODbL the answer determines whether share-alike applies to what you ship.

**Is silence being treated as permission?** An unlicensed academic or
institutional dataset is not permission. Ask; a written yes costs one email.

**Does the product handle regulated data?** Personal, location-at-residence,
health, financial, or minors' data brings statutory duties independent of any
license. Does aggregation make the combined record more sensitive than its parts?

**Can every marketing claim be substantiated** from the dossier?

## Market

**Size it properly, and don't use the adjacent industry's number.** The revenue
of the industry you sell *near* is not your addressable market. Build the funnel:
total population → those reachable by this business model → those winnable in
18–24 months. Rough thresholds in circulation: >$10 M serviceable market for an
indie business, $1 B+ total for a venture-scale bet.

**Is the market growing or consolidating?** A shrinking business count with flat
sales is a materially different bet from a growing one, and it changes who can
afford to partner with you.

**How fragmented is the buyer?** Thousands of single-location operators with no
procurement function is a brutal sales motion regardless of product quality.

**Who is the buyer vs. who is the user?** When they differ, the buyer's
incentives decide the product.

## Timing — "why now"

**What changed recently that makes this possible or necessary now?** An idea
equally possible five years ago and five years hence usually is not a good one.
Look for a forcing function: a dataset that became free or newly complete, a
regulation, a cost curve, a cultural shift, a crisis.

**If nothing changed, why has nobody done it?** Sometimes the answer is genuine
oversight. More often there is a reason, and finding it is the whole point.

## Competition and defensibility

**Does an expensive professional tool already do this?** Highest-information
question available. Validates value, disproves novelty, relocates the
opportunity to packaging and audience.

**Is any single component of this already a mature standalone category?** If so,
integrate rather than build, and stop marketing that component as the
differentiator.

**Would the moat survive a well-funded competitor deciding to build it?**
Distinguish *hard to understand* from *hard to replicate* — they are routinely
conflated, and the inference from one to the other is wrong more often than
right. Data-integration pipelines are usually replicable; accumulated proprietary
data, authored expert content, and network effects usually are not.

**What is the durable asset?** Name it explicitly. If it's "we did the
integration work," that's a head start, not a moat.

## Validation signals

**Has anyone independently converged on the same architecture?** When separate
teams arrive at the same core principles without contact, those choices are
principled rather than idiosyncratic. This is about as much design validation as
an unbuilt product can obtain, and it is worth stating explicitly.

**Does a competitor publish real outcome numbers?** A published conversion or
performance figure is the bar to beat and is worth more than any feature
comparison. Record it.

**What did the closest competitor try and abandon?** Often visible in changelogs,
blog posts, or founder interviews. Cheaper than learning it yourself.

## Willingness to pay

**What do people currently pay for an imperfect version of this?** The single
strongest signal. If they already pay professionals real money, WTP is proven and
the risk is about price point and segment, not existence of demand. If the
current workaround is free, monetization is roughly 10× harder.

**Who has budget, and what line does it come from?** Marketing budget, cost of
goods, and someone else's compliance budget behave completely differently. Check
the payer's margin structure before proposing any revenue share — the number
frequently makes the model impossible on its own.

**Is there a higher-margin adjacent party?** The money often sits upstream
(manufacturers, breeders, wholesalers) or in an adjacent service with better
unit economics than the one you first considered.

## Business model

**Transactional or recurring?** If users need the product once, there is no
recurring revenue and the business shape changes fundamentally. Have an explicit
answer for what brings them back, or accept the transactional model deliberately.

**Seasonality.** Does demand concentrate in part of the year? This drives cash
flow, hiring, CAC efficiency, and whether engagement dies for months at a time.
Very commonly ignored in consumer categories.

**Does monetization conflict with the product's core claim?** If the product's
value is impartial recommendation, paid placement corrodes it. Where a conflict
exists, define the firewall explicitly — what money may influence and what it
may never influence.

## Regulatory, legal, data

**What is the liability exposure when the advice is wrong?** Especially for
anything touching property, health, safety, money, or infrastructure.

**Data licensing.** For every third-party source: is it public domain, open
licensed, non-commercial only, or unlicensed scraping? Resolve before shipping,
not after. Government data is usually the safe core.

**Privacy.** Does the product aggregate sensitive information about a person,
household, or address? Aggregation itself can create sensitivity that no single
field has.

**Sector-specific regulation** that applies to the customer even if not to you.

## Distribution

**How do the first thousand users arrive?** Named channel, not "marketing."

**Is there a free wedge with independent value?** Something genuinely useful and
cheap to run, that also generates traffic and validates the risky assumption.
Usually the strongest opening move.

**Can the obvious competitor become a channel?** Professionals threatened by a
consumer tool often become its best distribution if the product feeds them work
instead of replacing them.

## Execution

**What does the riskiest phase cost, and can it be validated more cheaply?**

**What is the ground truth for correctness?** For anything modeled or predicted,
how do you know it's right? Design the validation before building on top of the
model — everything downstream inherits its errors invisibly.

**Geographic or segment rollout order,** where data quality or coverage varies.

## Kill criteria

**What would have to be true for this to be a bad idea — and how would you find
out cheaply?** Write it down in advance, before attachment sets in.

Standard decision frame:
- **Proceed** — strong problem validation, solution resonates, market is real
- **Pivot** — problem is real but the solution doesn't land, or the market is too small
- **Abandon** — problem validation is weak; the pain isn't intense enough

**Which single risk is load-bearing?** Name one. If everything is a risk, the
analysis hasn't finished.
