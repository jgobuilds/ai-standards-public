# Naming standard (house lens)

How apps built here get named, how repos get named, and how the portfolio
hangs together as one brand. The generation strategies, scoring rubric, and
screening tests live in the `vet-idea` skill's
[`naming-playbook.md`](../skills/vet-idea/references/naming-playbook.md) —
this file is the *standing policy* that playbook runs inside.

> **Scope seam.** Naming a new product → run `vet-idea` Job 5 (it owns the
> collision check and positioning). This file governs what the result must
> look like and where it lands: architecture, repo names, and findability.

## Brand architecture: endorsed house

We use the **endorsed-brand** model — the HashiCorp shape, not the Apple shape:

- **Products get their own evocative names** — two or three syllables, spellable after hearing once, memorable over descriptive.
  The tagline explains; the name sticks.
- **One maker brand endorses them all**: "<product>, by <maker brand>" in the
  README footer, repo description, site, and social cards. The endorsement is
  the compounding asset — trust earned by one product transfers to the next.
- **The maker brand owns the GitHub org.** Public product repos live in the
  org; the personal account keeps profile/config repos. Repos under an org
  carry the brand name as their URL prefix, which is the only place most
  visitors ever see the umbrella.

Why not a branded house (everything named `<Brand> X`): the products span
unrelated audiences (career tools, gardening, publishing) — a gardener gains
nothing from career-tool branding in the product name itself. Why not a pure
house of brands: with no shared endorsement, each launch starts from zero.

## Product names

- **2–3 syllables, evocative, fun.** Personality beats descriptive accuracy.
- **Generate 5–10 candidates across strategies** (evocative, invented,
  compound, metaphorical, oblique) — never adopt the first idea. Judge on
  recognizability, SEO, readability, fun.
- **Collision-check every finalist before adopting.** A live product in the
  same category is disqualifying, not a hurdle. Check the bare name *and*
  name-plus-descriptor, trademarks, domains, and handles. Expect the obvious
  names to be gone; survivors are oblique or invented.
- **Record the check** (queries, date, verdict) in the product's
  `idea-dossier/05-positioning.md`.

## Repo names

- **Lowercase, hyphenated, never underscores or capitals.** `book-os`, not
  `book_os`; `wick`, not `Wick`.
- **Public repos: `<product>-<category-descriptor>`.** The product name alone
  is meaningless to search; the descriptor is the keyword. A product called
  Ember shipping a job-search tool becomes `ember-career-system`, not `ember`.
  Pick the descriptor from what a stranger would type, not from internal
  vocabulary.
- **Private repos: plain descriptive names**, no branding required —
  findability by others is not a goal for a repo others cannot see. Rename
  only for hygiene (case, underscores), and check blast radius first: local
  clones, added-working-directory configs, CI references.
- **Never put version numbers or years in repo names.**

## Findability is mostly not the name

GitHub search ranks on name, description, topics, and engagement. For a repo
that already has a keyword descriptor in its name, the remaining levers in
order of cheapness:

1. **Description** — one sentence, front-loaded with the search terms a
   stranger would use.
2. **Topics** — up to 20; specific beats generic (`ats-resume` over `career`).
   An empty topic list is a zero on a real ranking factor.
3. **README first screen** — restates the keywords naturally; search engines
   index it.
4. **The name** — last, because renames are the most disruptive lever.
   (GitHub does redirect old repo URLs after a rename, so the cost is
   confusion and stale docs, not broken links.)

## Hard constraints

- A repo whose git history contains PII **never goes public and never gets a
  "findable" name** — renaming it is polishing a repo that must stay dark.
  See [`pii-controls.md`](pii-controls.md).
- The endorsement line ("by <maker brand>") appears only on repos that are
  public or intended to become public. Private scaffolding does not carry
  brand dressing.

## The dated register lives with the brand, not here

Collision findings, candidate slates and entity decisions are **one
organisation's** dated record — they change, they name real companies, and they
are worthless to anyone else reading this standard. Keep them next to that
organisation's brand assets and cite the date on every finding.

What belongs here is the *method*: endorsed-house architecture, the naming
levers, and the rule that **every finalist is collision-checked before adoption,
with a live product in the same category treated as disqualifying**.
