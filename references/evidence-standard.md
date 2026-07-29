# Evidence standard (house lens)

How a **published claim** carries its provenance. `change-safety.md` covers
verifying a fact before you *act* on it; this covers what a fact must carry once
you *ship* it — in a kit, an ADR, a market analysis, an idea dossier, a naming
register, or a report a client reads.

The test: **a reader who distrusts you should be able to check any claim without
asking you.** Everything below follows from that.

## Rank every source, and say which rank it is

A four-point scale, stated wherever sources are listed:

| Rank | Meaning |
|---|---|
| **1** | Primary / authoritative — the originator's own publication, first-party research, the API, the spec, the file itself |
| **2** | Practitioner-credible — a recognized practitioner publishing openly; experience, not research |
| **3** | Secondary / synthesized — someone else's summary of 1 or 2 |
| **4** | Weak — consensus, recollection, "everyone knows", an unattributed forum post |

**Rank 3–4 does not ship as evidence.** It can motivate a search; it cannot
support a claim. An artifact sold on being checkable is destroyed by one
uncheckable citation in it, because the reader cannot tell which others are also
soft.

## Fetch it. Do not remember it.

Every source gets a **`Pulled:` date**, and the pull actually happened. Recall is
rank 4 wearing rank 1's clothes: it is confident, specific, and unverifiable.

This is not pedantry — it is the step that catches things. Two real instances
from one afternoon of sourcing: a widely-cited Google research page was expected
to have been retired and had not been, but carried an editor's note about its
vintage that changed how it should be cited; and a capability catalog turned out
to describe a framework **without naming the researcher** the citation was about
to attribute it to. Both would have been wrong from memory, and both looked fine.

Re-verify on a cadence. A `Pulled:` date is also a staleness clock.

## Community signal is a lead, not a citation

A forum, chat community, or conference hallway tells you **what to go read**. It
is not the thing you cite.

```
community signal → LEAD → resolve to a rank 1–2 primary source → claim
                            ↓ cannot resolve
                          record "checked, not adopted" and stop
```

Three reasons, and the first is usually the expensive one:

1. **It degrades the artifact.** A rank-4 citation in something sold on rank-1
   sourcing removes the property it is bought for.
2. **Licensing.** Ideas and facts are not copyrightable and can be re-expressed
   with attribution. That reasoning covers a published work whose author chose to
   publish. It does not transfer to identifiable people talking in a semi-private
   space who did not.
3. **Trust.** Harvesting a practitioner community to feed something you sell is a
   breach of it, and small fields remember.

The cost of this rule is **speed** — community discussion runs ahead of published
work, so you lag the leading edge by roughly a publication cycle. Accept it
deliberately, and say so.

## Name the assumption most likely to be wrong

Every estimate, model, or projection names its own softest term — the one that,
if wrong, moves the answer most. Not buried in a caveats section: attached to the
number.

This is the difference between a model someone can argue with and a model they
can only believe or dismiss. It also protects you: a stated weak assumption that
turns out wrong is a known limitation; an unstated one is a credibility event.

Corollaries for anything with money in it:

- **Present a range, not a point.** A point estimate claims a precision the
  method does not have.
- **State attribution honestly.** "The size of the prize if this moves" is a
  different claim from "we will deliver this", and only one of them is defensible
  when the counterfactual is unavailable.
- **Never count the same saving twice.** Overlapping drivers get an explicit
  overlap discount, stated.
- **A credible small number beats an incredible large one.** If unsure, halve it
  and show the calculation.

## Make the reference graph machine-checkable

Where claims cite identifiers (`SRC-01`, `CAP-02`, an ADR number), a build step
should resolve every reference and **fail on a dangling one**. Prose review will
not catch the citation that quietly stopped resolving three edits ago.

Two consequences worth stating:

- **Do not cite an identifier that does not exist yet** to reserve it. Write the
  claim self-contained and wire the reference when the target lands.
- **A stale link is a broken claim.** Treat link-checking and reference-checking
  as the same gate.

## What this looks like in practice

A source entry carries: an **ID**, a **title**, a **URL**, a **`Pulled:` date**, a
**rank**, a one-line **credibility** note saying *why* that rank, any **caveat**,
and what it **backs**. If you cannot fill the rank or the date, you do not have a
source yet — you have a lead.
