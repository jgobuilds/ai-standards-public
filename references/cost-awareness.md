# Cost awareness (house lens)

A lens for **weighing cost at decision time**, not discovering it at invoice time.

The rule: **any decision that adds a dependency, a service, or a scheduled workload
states its cost model *before* it is chosen — as a column in the options table.**
Cost that lives in a separate paragraph gets read after the decision; cost that sits
in the comparison gets weighed during it.

## The four cost classes

Name which one each option is. The class matters more than the number, because the
class tells you *how it behaves as you grow*.

| Class | Behaviour | The question to answer |
|---|---|---|
| **Free / unmetered** | No charge at any volume | Is it really unmetered, or quota-limited? |
| **Quota-limited free** | Free until a limit — then it **fails**, or silently starts billing | What is the limit, and which happens at it? |
| **Metered** | Pay per unit (request, GB, GB-month, token) | What is the unit, and our volume at expected cadence? |
| **Fixed / licensed** | Per seat, per month, per instance | Does it scale with team size or with usage? |

"Free until it fails" and "free until it bills" are very different risks. Say which.

## State the trigger, not just the number

Prices change; thresholds and units are stable. Write:

> Free under 1 GB/day inspected; **metered per GB above that**.

not "about $3/month" — a figure that is stale the moment a rate card moves, and that
tells a future reader nothing about what makes it grow. Where a number genuinely
helps, give the **order of magnitude and the date it was checked**, and link the rate
card rather than transcribing it.

## Never conflate notional cost with real money

Some "cost" is a *yardstick*, not spend. Agent runners on subscription auth produce a
**notional** cost — what the work would have cost at metered API rates. It is the
right way to compare tiers and prompts; it is **not** money leaving the account, and
must never be summed into a budget or a finance report. Cloud bills are real money.
**Label which kind every figure is** (see `AIOPS.md` for the notional-cost rules).

Mixing them produces both failure modes: panicking over a notional number nobody pays,
and ignoring a real one because it sat next to notional ones.

## Non-dollar costs are still costs

A thing can be free and still expensive. Count these explicitly:

- **Operational toil** — anything a human must redo on a schedule.
- **Constraints the free tier imposes** — rate limits, retention caps, feature gates.
- **Verification / compliance effort** — review processes, audits, attestations.
- **Storage that grows** — free today because the data is small; retention policy is a
  cost control, not just a privacy control.
- **Egress** — usually the surprise line on a cloud bill.
- **The cost of leaving** — proprietary formats, no export, one-way migrations.

> **Worked example.** Wiring Google Drive lanes cost **$0** in GCP: the Drive API is
> quota-limited-free, a project and an OAuth client are free, and no billing account
> is required. A dollars-only review would have stopped there. But an OAuth app with
> an *external* user type in **Testing** status is issued a refresh token that
> **expires every 7 days** — so an unattended scheduled lane silently dies weekly
> until someone re-consents. Free in money, expensive in toil, and a reliability
> defect on top. The fix (a Workspace account with an Internal app type, or narrower
> non-sensitive scopes) is a *cost* decision that no price list would have surfaced.

## Where this lands

- **Every ADR** — the `Considered` table gets a **Cost** column alongside the verdict.
  An option comparison without cost is incomplete.
- **`build-vs-adopt` surveys** — cost-to-run sits beside license and maintenance. A
  free library with a metered hosted dependency is not free.
- **Scheduled workloads** — state cost *at cadence*: per-run × frequency. Something
  trivial per run is not trivial every 5 minutes.
- **Anything requiring a billing account** — say so plainly. "Needs billing enabled"
  is a decision input, not a footnote.

## Enforcement

This is judgment, not tooling — there is no linter for a rate card. What makes it
stick is the **column**: a `Considered` table with an empty Cost cell is visibly
unfinished, which is the point. When cost genuinely cannot be known yet, write
"unpriced — needs a costed spike" rather than leaving it blank or guessing.
