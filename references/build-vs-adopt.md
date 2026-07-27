# Build vs adopt (house lens)

A lens for the moment **before** code gets written: has someone already solved
this, and is their solution better than the one we're about to start?

The default is **survey first**. Not because building is bad, but because the
decision should be made with knowledge of the alternatives rather than in
ignorance of them. A twenty-minute search is cheap against a component you will
maintain for years.

Applies at **component granularity** — the thing you're about to spend a day or
more on. Not every function; see the skip list below.

> **Scope seam.** This is the lightweight, frequent check during architecture and
> implementation planning. For a *product or business* idea — market viability,
> competitors, naming, positioning — use the `vet-idea` skill, which owns the
> `idea-dossier/` and runs as an engagement, not an inline step. For license
> analysis of anything that will actually ship, defer to that skill's
> `references/license-obligations.md` rather than reasoning about licenses here.

## Survey before building

- **Risk:** rebuilding a solved problem, badly. The homegrown version starts
  smaller and ships sooner, then slowly acquires the edge cases the mature
  package already handles — except now they're yours to find in production.
  The cost is invisible because it arrives as maintenance, never as a line item.
- **Check:** was any alternative named before implementation began? Can the
  author say what exists and why it was rejected? "I didn't look" is the finding.
- **Fix:** search before writing. Package registries, GitHub topic search, and
  "awesome-X" lists get you 80% of the way in minutes. Name at least one
  alternative and one reason it lost, even when building is correct.

## The opposite failure is equally real

- **Risk:** adopting reflexively produces dependency bloat, a supply-chain
  surface, and a component you cannot fix when it breaks. "There's a package for
  it" is not a reason. An abandoned dependency is worse than code you wrote,
  because you don't understand it *and* nobody is fixing it.
- **Check:** does the dependency earn its place — is it solving a hard problem,
  or wrapping something the standard library does? What is the cost of removing
  it later? How much of it do we actually use?
- **Fix:** adopt for hard problems with real edge cases (parsing, crypto,
  protocol implementations, format handling). Build for glue, for anything
  encoding a house rule, and for the small tail of a package you'd use 5% of.

## Judge on five axes, not on stars

- **Risk:** popularity is a lagging, gameable signal. Stars measure attention,
  not fitness — and say nothing about whether the project is maintained *now*.
- **Check:**
  1. **License** — is it compatible with how this ships? AGPL/SSPL/BSL are
     decisions, not details. Defer to `vet-idea`'s license reference.
  2. **Maintenance** — last release, commit recency, open-issue response. A
     project with 30k stars and no commits in 18 months is a liability.
     **Check this from the registry or API, not from stars, the README, or a
     search summary.** In a survey run from this workspace, a web summary
     asserted a caching library was "actively maintained as of 2026"; the GitHub
     API showed its last push was over a year earlier and its own README said it
     had stopped adding support for new models. A second summary reported a
     gateway's license as Apache-2.0 when the API said MIT. Both errors would
     have survived into a decision record.
  3. **Fit** — how much of it do we need, and how much adaptation is required?
     A perfect fit for 60% of the problem may cost more than building 100%.
  4. **Exit cost** — how deeply does it sit in the request path? What does
     removal look like in a year?
  5. **Trust boundary** — what does it see? A library that processes data is a
     smaller decision than a proxy that sits in the request path with access to
     everything flowing through it.
- **Fix:** write the five answers down (below). An adoption decision with no
  recorded reasoning cannot be revisited when one of the axes changes.

## Record the decision, not just the outcome

- **Risk:** undocumented decisions get re-litigated, or worse, silently inherited
  by someone who assumes they were considered when they weren't. "Why do we use
  this?" is a question with a real cost when nobody knows.
- **Check:** does a durable record exist near the code — ADR, README section, or
  a `## Alternatives considered` block?
- **Fix:** a short record at the point of decision:

```markdown
## Build vs adopt: <component>
- **Considered:** <package> (license, last release), <package>, build
- **Chose:** <decision>
- **Because:** <the one or two axes that decided it>
- **Revisit if:** <the condition that would change the answer>
```

The **revisit-if** line is the one that ages well. "Revisit if we need X" or
"revisit if the project goes unmaintained" turns a frozen decision into one with
a trigger.

## Skip the check when it would be ceremony

- **Risk:** a gate applied to everything gets routed around entirely. A survey
  requirement on a 20-line helper trains people to skip surveys.
- **Check / skip when any of these hold:**
  - Under a day of work and self-contained.
  - It encodes a **house rule** — a linter for our own standard, a config
    validator for our own schema. No package can know our conventions.
  - It's glue between two things we already chose.
  - It's a throwaway spike whose output is knowledge, not code.
- **Fix:** apply the check to components you'll maintain, dependencies in the
  request path, and anything touching a solved problem domain (parsing, auth,
  crypto, compression, retries, scheduling, diffing, date handling).

## Surveys expire

- **Risk:** "we looked into this" is often years old. The landscape moves fast
  enough that a two-year-old build decision was made against a different set of
  options — and the thing you built may now be strictly worse than a package
  that didn't exist then.
- **Check:** does the decision record carry a date? Has any load-bearing
  homegrown component never been re-examined since it was written?
- **Fix:** date every record. Re-survey when the `revisit if` trigger fires, when
  a component starts costing real maintenance, or during a scheduled review.

---

### Worked example — a miss from this workspace

While extending an orchestration framework, ~500 lines of Python
(`workspace_doctor.py`, `model_policy_check.py`) were written with **no market
check at all**. Both turned out to be defensible builds under the skip rules —
they encode house-specific standards, which is exactly the "no package can know
our conventions" carve-out.

But the check wasn't *run*; it happened not to matter. The very next item
considered was **context compression** — a solved problem where a homegrown
version would have been pure waste. The habit is what protects you, not the
outcome of any single instance: skipping the survey worked twice and would have
failed badly on the third.

The survey that followed also demonstrates why the axes beat the headline. It
found one strong candidate — and, in the same sweep, an abandoned library that a
search summary called maintained, a "self-hostable" memory platform whose
community edition had been discontinued a year earlier, a source-available
license (ELv2) presented as open source, and two projects whose adoption claims
could not be verified anywhere. Every one of those would have looked fine from
the star count alone.
