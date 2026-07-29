# Licensing

**AGPL-3.0-or-later.** Copyright © 2026 Brightside Data LLC.
Relicensed from Apache-2.0 on **2026-07-28**.

## Why this repo's licence is unusual for what it is

Most standards and lens collections are permissive, on the reasoning that a
standard nobody may adopt is not a standard. That reasoning is sound and this
repo rejects it on purpose: **the method here is the differentiator, not the
code**, so it is shared on terms that keep it shared. Anyone may read it, use
it, argue with it, and build on it — what they may not do is take it into a
closed product and give nothing back.

If you want it under other terms, **ask**. A commercial licence is available,
and the copyright is deliberately held by a single entity so that offer can
exist at all. One unassigned contribution would have made it impossible
forever.

## What changed for you, in practice

**These files are designed to be copied**, not installed as a package —
`pii_scan.py`, `staged_scope_check.py`, the lenses, the skills. That is the
whole distribution model, and **copyleft follows the copy**. Under Apache-2.0
you could vendor any of it into a closed codebase with only an attribution
notice. Under AGPL you cannot, without either releasing the combined work under
AGPL or holding a commercial licence.

The AGPL network clause matters here too: if you run a modified version as a
network service, your users are entitled to the source of your modifications.
For a repo of gates and lenses this rarely bites, but it is the clause that
makes the licence worth choosing over GPL.

## What this does NOT do

- **It does not reach back.** Anything you obtained under Apache-2.0 remains
  Apache-2.0 **for that version, permanently**. Relicensing is not retraction,
  and nobody can take away rights already granted. If you copied a lens last
  week, that copy is still Apache-2.0.
- **It does not restrict reading, quoting, or disagreeing.** The lenses exist to
  be argued with. Quote them, cite them, publish a rebuttal. Copyright covers
  copying the work, not following the advice — **applying a practice you read
  here creates no obligation whatsoever.**
- **It does not apply to your own repos** merely because you read this one.
  The obligation attaches to *copied files*, not to ideas.

## For contributors

Contributions require a copyright assignment, for the same reason the
commercial licence can exist: relicensing requires a single rights holder, and
it cannot be collected retroactively. If you would rather not assign, open an
issue describing the change instead — a clear bug report is often worth more
than the patch and costs you nothing.

## Related repositories

`ai-control-plane` is AGPL-3.0-or-later on the same reasoning and with the same
assignment policy. The two are consistent by design: it would be incoherent to
publish the implementation under copyleft and the method under a licence that
lets a competitor close it.
