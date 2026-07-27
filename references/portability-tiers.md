# Portability tiers — what "this repo stands alone" actually requires

Extracted from a fleet-adoption plan on 2026-07-26. The plan named specific
repositories and belonged elsewhere; the model underneath it is a standard.

## The failure it exists to prevent

We wrote a lens saying personal and ancestor context is invisible to everyone
else, and then broke it ourselves. Every repo in the fleet inherited its
conventions from a `CLAUDE.md` at the *workspace* root — a file that is in no
repository. **Anyone who cloned a repo got none of the standards.** Not the venv
discipline, not the review lenses, not the naming rule. An agent they ran
inherited nothing, and nothing announced that.

Three couplings did it, and they recur in any multi-repo setup:

| Coupling | Breaks for a cloner because |
|---|---|
| `overlay: ../<standards-repo>` in a config | there is no such sibling, and it may be private |
| An ancestor instruction file above the repo | ancestor files are outside the repo and never cloned |
| A relative link like `../../other-repo/DOC.md` | resolves only in one exact directory layout |

## Two layers

**Layer 1 — a self-contained root instruction file. Every repo, no exceptions.**
Carries what *this* repo needs and depends on nothing outside itself. This is
what makes a repo work for someone else.

**Layer 2 — the optional overlay.** Deeper review lenses, reachable only where
the standards repo is on disk. Optional, and **never load-bearing** for a
contributor.

## Two tiers

- **Tier I (internal)** — private, one team. A relative-path overlay is fine.
- **Tier P (portable)** — public, or has outside contributors. **Everything the
  repo needs is in the repo.** No private siblings, no ancestor assumptions, no
  relative links escaping the repo.

| | Tier I | Tier P |
|---|---|---|
| Root instruction file, self-contained | required | required |
| No secrets in context files; `.mcp.json` uses `${VAR}` | required | required |
| `workspace_doctor` clean at `--fail-on high` | required | required |
| Nothing referenced outside the repo | — | required |
| `AGENTS.md` for cross-vendor contributors | — | required |
| `CONTRIBUTING.md` covers agent use | — | required |

## Install burden is a separate constraint from portability

Conflating the two audiences produces a bad answer.

**Outside contributor — zero extra installs. Non-negotiable.** Clone the repo;
it works. If a contributor needs a second clone to understand the project, that
is a defect in the repo, not a setup step.

**The maintainers, across machines — one install, not N clones.** Cloning a
standards repo, creating junctions, and wiring an overlay per repo is
fragmentation that grows with every repo added. Distribution options, ranked:

| Option | Contributor cost | Maintainer cost | Verdict |
|---|---|---|---|
| Publish the standards repo, reference by URL | zero | still a clone + per-repo wiring | **Weaker than it looks.** `overlay:` resolves as a filesystem path, so a URL makes the lenses *readable* without making the tooling load them. |
| One plugin + marketplace | zero | one `marketplace add` | **Recommended.** Ships skills and lenses together, namespaced, versioned, and it works in cloud/scheduled runs where personal skill directories are not read. |
| Vendor copies into each repo | zero | drift | **No.** Violates one-canonical-copy. |

## The duplication this accepts, and why it is not drift

Self-contained root files sit in tension with one-canonical-copy. The resolution:

- The repo's root file carries **repo-specific** content — setup, architecture,
  gotchas — plus only the few universal rules a contributor actually needs.
- Deep lenses stay in the installable unit and are never restated per repo.

Most of a workspace-root file is wiring that means nothing to an outsider, so
what genuinely repeats is a handful of stable lines. That is a deliberate,
bounded duplication, not the wholesale copying the lens forbids.
