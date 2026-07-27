# Concurrency & branching for parallel agents (house lens)

A lens for running **several agents at once without them contending** — and for
knowing which isolation to reach for as the fleet grows.

Parallel agents contend on more than files. The full list, because people fix the
first one and get bitten by the rest:

| They contend on | Symptom |
|---|---|
| The **working tree** | Two agents editing the same file; one clobbers the other |
| The **index / HEAD** | Git state is per working tree — concurrent `add`/`commit` interleave |
| A **branch** | Two agents committing to one branch produce an incoherent history |
| **Ignored build dirs** | `node_modules/`, `.venv/`, `target/` — shared, mutated, corrupted |
| **Runtime resources** | Ports, daemons, globally-installed tools |
| **Shared state** | One ledger, one database, one vault |
| **Rate limits** | A fleet multiplies request rate against a *shared* quota |

## The isolation ladder — take the cheapest rung that removes the contention you have

1. **Serialize.** One agent at a time. No isolation machinery, no parallelism. For
   small or highly-coupled work this is the right answer; don't build a fan-out to
   avoid admitting the work is serial.
2. **Git worktrees — the default for parallel agents on one repo.** Each agent gets
   its own working directory, index and HEAD, while **sharing one object store**. No
   re-clone, no duplicated history, full file-level isolation.
   `git worktree add ../wt/<id> -b agent/<id>`
3. **Separate clones.** When tooling assumes it owns the repo root, or when agents
   need different remotes or credentials.
4. **Separate containers / VMs.** When the **runtime** contends — ports, daemons,
   global installs — not just the files. File isolation cannot fix a port collision.

Most teams jump to 4 when 2 would do, or stay at 1 long after it hurts. Diagnose
*which* resource is contended, then pick the rung that isolates that resource.

## The rule: one agent = one worktree = one branch

- **Never** two agents in one working tree. **Never** two agents on one branch.
- Namespace the branches — `agent/<task-id>` — so they are greppable, reviewable and
  bulk-prunable, and never collide with human branches.
- **Nothing auto-merges.** Fan-out produces *candidates*; a human integrates.

## Parallel work, serial integration

Fan out wide; integrate one at a time. A merge queue of one keeps conflict resolution
comprehensible — resolving N-way conflicts between machine-generated branches is far
worse than resolving them one at a time against a moving trunk.

Conflicts are resolved by the **owner of the change**, not by whichever agent merges
second. An agent that did not write the code should not be reconciling its intent.

## Minimize conflicts by partitioning ownership, not by locking

The cheapest conflict is the one that cannot happen. Give concurrent agents **disjoint
file ownership**. This is the same rule the persona contract already enforces: *two
agents whose "owns" overlap are one agent*. Overlapping scope guarantees conflicts no
branching strategy can fix.

## The gotcha worktrees do not solve: ignored files

A new worktree shares the object store but **not ignored files**. `node_modules/`,
`.venv/`, `__pycache__/`, `target/` **do not exist** in a fresh worktree, and a build
that assumes them fails in a way that looks like a code error.

So budget for it: each worktree needs its own install, or a **shared content-addressed
cache** (pnpm store, uv/pip cache, Gradle cache) that is safe for concurrent readers.
Install time and disk are the real per-agent cost of fan-out — the thing that decides
how wide you can actually go. Measure it before promising parallelism.

## Resources that cannot be duplicated need a lease

Some state is singular by design — an append-only audit ledger, a token vault, a
production database. For these:

- **Serialize writes** at the owner (a queue in the writing service), so concurrent
  callers cannot interleave and fork the state.
- Where a true lock is needed, give it an **owner, a timeout, and a stale-lock path**.
  A lease with no expiry becomes a deadlock the first time an agent dies mid-task.
- Treat **shared rate limits** as a contended resource too: N agents against one API
  key is one bucket, not N. Cap fleet width by the limit, not by CPU.

## Lifecycle — cleanup is part of the task

`create → work → self-verify in-tree → hand off → human merges → prune`

Self-verification happens **inside the agent's own worktree** (its own tests, its own
install), so a branch arrives already known-green. After merge: delete the branch and
`git worktree prune`. Worktrees and `agent/*` branches accumulate silently otherwise,
and a tree full of stale worktrees is indistinguishable from active work.

## Already true here

The parallel fan-out lane implements the core of this: a worktree per agent, an
`agent/<id>` branch each, self-verification in-tree, and **nothing merged or pushed** —
branches are reviewed and merged by a human. This lens is that pattern written down,
plus the failure modes around it (ignored files, leases, shared rate limits, pruning).

The working-tree safety net (`scripts/safety_snapshot.sh`) is per-repository and
operates per worktree, so each parallel agent keeps its own undo history.
