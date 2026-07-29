# The solutions log (house lens)

A problem you solved once and cannot reconstruct is a problem you will pay for
twice. This is where the second payment stops.

Format borrowed from [`EveryInc/compound-engineering-plugin`](https://github.com/EveryInc/compound-engineering-plugin)
(MIT), whose `/ce-compound` skill put it well: *the first time you solve a
problem takes research; document it, and the next time is free.* The plugin was
assessed and declined — 32 skills against a context budget that exists because
instruction bloat measurably reduces adherence — but the shape was worth taking,
and citing.

## The one rule that decides where something goes

We already had a promotion loop: a **known-cause table** of CI failure
signatures, matched deterministically before any model is asked. It works, and it
has a hard boundary — it can only hold things that announce themselves in a log
line.

> **Does the problem announce itself in a LOG LINE?**
>
> **Yes** → a known-cause **row**. Matchable, deterministic, gated. The machine
> finds it for you.
>
> **No** → a **solution**. Read by a human, or by an agent that went looking.
> Nothing can match it, so it has to be *findable* instead.

Some problems earn both: the row matches it, the solution explains it. The
`signature:` field carries the link.

**The failure that produced this lens:** six entries in one repo's known-cause
table were not CI causes at all — an n8n schedule that would not register, a
container serving stale code, a null that broke the branch testing for it. They
were filed as rows because there was nowhere else, and a row with no matchable
signature can never fire. A record whose shape is wrong is one nobody trusts to
be complete.

## The sections, and why each is there

`scripts/solution.py --dir <dir> new "<title>"` writes the template.

| Section | Why |
|---|---|
| **What happened** | The symptom as it presented. What did someone *see*? This is what a future search matches on |
| **Why it happened** | The actual cause. Ask why past the first answer, but **stop when you leave the evidence** — two grounded steps beat five speculative ones |
| **What was tried that did NOT work** | The most valuable section, and the one always skipped |
| **The fix** | What was actually done |
| **Prevention** | The **mechanism**. Not an intention |
| **How we would know it came back** | If the answer is "nothing", that is itself a finding |

### The section people skip is the one worth most

**"What was tried that did not work"** is the only part nobody can reconstruct
later. The fix survives in the commit; the cause is usually inferable from the
fix. The three plausible hypotheses that were wrong — and *why* each looked right
— exist nowhere else, and they are exactly what the next person will try.

A solution without this section is a changelog entry.

### Prevention must name a mechanism

"Be more careful" is not prevention. Neither is "remember to check X". If no
mechanism is apparent, **say so plainly** rather than writing a wish — an honest
"no mechanism found" is a standing invitation to find one, and a wish is a
closed ticket that changed nothing.

## What is gated, and what deliberately is not

```bash
python scripts/solution.py --dir docs/solutions check   # CI
python scripts/solution.py --dir docs/solutions index   # regenerate INDEX.md
python scripts/solution.py --dir docs/solutions stale --days 365
```

**Gated:** frontmatter present, ids unique, `status` from a fixed set,
`last_verified` a real date, and the generated index not drifted.

**Not gated:** the prose. A gate that argues about writing quality is one that
gets switched off, and then nothing is checked at all. Shape is checkable;
usefulness is not, and pretending otherwise costs you the checks that work.

**Staleness is reported, never failed.** A build that reddens because a date
passed teaches people to back-date the field, which is worse than no field.

## Where it goes

`docs/solutions/` in the repo the problem happened in. Per-repo, like the local
known-cause table — a solution about one project's container layout is noise in
another's. The *format* is shared; the content is local.

## The honest limitation

Nothing makes anyone write these. The failure mode is a log that is thorough for
a week and empty thereafter, and no gate can detect the solution nobody wrote.

The only real mitigation is to write it **at the moment of resolution**, while
the wrong hypotheses are still in your head — which is why the template's first
line back says so. If the log has fewer entries than the month had incidents,
that is the assumption failing, and the fix is a prompt at the moment of
resolution rather than more discipline.
