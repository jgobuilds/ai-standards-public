# Contributing

Issues and patches both welcome. One thing to read first, because it is an
unusual ask and declining it is a legitimate choice.

## Contributions require a copyright assignment

By submitting a contribution you **assign copyright in it to Brightside Data
LLC**, and receive back a perpetual, worldwide, royalty-free licence to use your
own contribution for any purpose, under any licence. You keep full use of your
own work; the project gains a single, unambiguous rights holder.

Add this to each commit, using your commit-author name and email:

```
Copyright-Assignment: I assign copyright in this contribution to Brightside Data
LLC, and confirm I have the right to do so.  <your name> <your@email>
```

If your employer owns your work output, get their sign-off *before* the line is
true rather than after review.

## Why — stated plainly, because it is a real ask

This project is **AGPL-3.0-or-later** (relicensed from Apache-2.0 on
2026-07-28 — see [`LICENSING.md`](LICENSING.md)). AGPL is unworkable for some
organisations, so a commercial licence on different terms is available on
request. **Offering that depends on one entity holding all the copyright.**

Merge a single unassigned contribution and the project can never be relicensed
again — not by agreement, not by paying, not ever, short of tracking down every
contributor. That is not hypothetical: it is why several well-known projects are
permanently stuck on a licence they have outgrown. The assignment is collected at
the door because it cannot be collected retroactively.

**If you would rather not assign**, that is entirely reasonable and you are
still welcome. Open an issue describing the change instead. A clear bug report
or a well-argued objection to a lens is often worth more than the patch, and
costs you nothing.

## What actually helps

- **Argue with a lens.** Every rule in `references/` was written after a real
  failure. If one is wrong, or right for the wrong reason, say so — that is the
  most valuable contribution here and it requires no assignment.
- **A false positive in a detector.** `pii_scan.py` has a labeled corpus
  precisely so that every false positive found in the wild becomes a permanent
  regression case. Send the input that fooled it.
- **A portability break.** Everything here must work in a repo cloned on its own
  (`references/portability-tiers.md`). If something assumed a sibling directory
  or a global install, that is a bug.

## Before you send a change

- **Edit `AGENTS.md`, never the generated adapters** — `CLAUDE.md`,
  `.cursor/rules/`, `GEMINI.md` and the rest are overwritten. Re-run
  `python scripts/apply_adapters.py .` and commit both.
- **Mind the context budget.** `AGENTS.md` loads every session, and longer files
  measurably reduce adherence. `python scripts/context_budget.py .` must stay
  under target — it currently has very little headroom, so new prose usually
  means depth moves into `references/`.
- **No secrets, ever** — including in commit messages, which are permanent. The
  PII gate scans both the diff and the message.
- **A new rule needs a mechanism where one is possible.** A standard that runs
  on intention gets broken by the person who wrote it; that is recorded in
  `references/change-safety.md`, more than once.

## Security

Do **not** open a public issue for a vulnerability. Report it privately via
[brightsidedata.co](https://brightsidedata.co).
