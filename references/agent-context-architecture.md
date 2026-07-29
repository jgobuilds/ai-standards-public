# Agent context architecture (house lens)

A lens for how a repo **presents itself to an AI agent**: instruction files,
skills, tool config, and working-set boundaries. Most review lenses ask whether
the code is right; this one asks whether an agent reading the repo will be told
the right things — and *only* the right things.

Applies to every repo an agent works in. Weight it higher for repos with many
packages, shared tooling across projects, or agents running unattended.

Each item: the risk, what to check, the fix. Full rationale and sources:
[AGENT-WORKSPACE.md](https://github.com/jgobuilds/ai-control-plane/blob/main/docs/design/AGENT-WORKSPACE.md) — a worked
application of this lens. Linked by URL, not by a relative path that resolves in
only one directory layout; the repo may be private, in which case this is a
pointer for us and the lens above stands on its own.

## Always-loaded context has a hard budget

- **Risk:** instruction files are loaded **in full, every session**, and every
  ancestor directory's file loads eagerly. A bloated file in a parent folder
  taxes every project underneath it, forever. Longer files measurably *reduce*
  adherence — the rules compete with each other for attention.
- **Check:** `wc -l` every `CLAUDE.md` on the path from repo to filesystem root.
  Over ~200 lines is a finding. Is a parent-workspace file carrying rules that
  are true for only some children?
- **Fix:** move sometimes-needed material into skills (loaded on demand); keep
  only always-true rules in the instruction file. Push per-project rules down
  into the project.

## Don't spend tokens on what the agent can derive

- **Risk:** directory trees, dependency inventories, and architecture overviews
  in an instruction file cost tokens on every run *and* go stale — the agent can
  read the actual tree, but it can't tell that your description of it is now
  wrong.
- **Check:** does the instruction file contain a file listing, a dependency
  table, or a module inventory? Could the agent answer it by looking?
- **Fix:** delete it. Keep what is *not* derivable: rationale, gotchas, and
  conventions that differ from the tool's defaults.

## One canonical copy of shared context

- **Risk:** shared rules copy-pasted across repos diverge silently. Nobody
  notices until an agent acts on the stale copy.
- **Check:** does the same guidance exist verbatim in two repos? Is a shared
  folder vendored, copied, or pulled in as a submodule?
- **Fix:** one real directory, referenced — symlinked into `.claude/rules/` or
  `.claude/skills/`, or packaged as a plugin when it needs its own version
  history. Avoid submodules for this: updating one shared folder means updating
  every consumer, and versions drift.

## Unattended runs can't see personal skills

- **Risk:** cloud, scheduled, and Cowork sessions do **not** read
  `~/.claude/skills/`. A setup that works on your machine fails in automation —
  and reports the skill missing rather than degrading gracefully.
- **Check:** does any scheduled job, CI step, or unattended agent depend on a
  skill or rule that exists only in a personal folder or a local symlink target?
- **Fix:** commit it to the repo or ship it as a plugin. Personal folders are
  for interactive convenience only.

## Contradictions survive — they don't resolve

- **Risk:** instruction files are **concatenated, not overridden**. Two
  conflicting rules both reach the model, which may then pick one arbitrarily.
  Different runs can behave differently for reasons no one can see.
- **Check:** read the merged set as a whole — ancestors plus repo plus nested
  files. Do any two rules disagree? Do any contradict the code's actual
  behavior?
- **Fix:** reconcile explicitly. Exclude irrelevant ancestor files where the
  tooling allows it. Review instruction-file edits in PRs like any other doc.

## Stale context is worse than none

- **Risk:** the agent *trusts* the instruction file. Confidently wrong guidance
  is more damaging than silence. Rules written to work around an older model's
  limitation become pure overhead once the limitation is gone.
- **Check:** does anything describe behavior, tooling, or paths that no longer
  exist? Anything justified by "the model can't handle X"?
- **Fix:** fix or delete on sight. Re-review after major model releases, not
  just after code changes.

## Secrets never live in context files

- **Risk:** instruction files, rules, and skills get **no secret scrubbing** —
  whatever is written there is loaded verbatim into every session, and committed
  for everyone.
- **Check:** grep the context files for tokens, keys, connection strings, and
  internal hostnames. Check `.mcp.json` for literal credentials.
- **Fix:** never place secrets in context files at all. Use `${VAR}` expansion
  in `.mcp.json`; keep non-shareable content in gitignored `CLAUDE.local.md`.
  **Note the footgun:** an unset variable with no default loads with a *warning*,
  not an error — verify explicitly rather than trusting it to fail loudly.

## Working set is blast radius

- **Risk:** launching an agent at a parent folder grants write access to every
  project beneath it and loads context from all of them. The wide default is
  rarely what the task needed.
- **Check:** where is the agent actually launched? Does a repo need read access
  to a sibling, and is that granted as read-only or as a full working directory?
- **Fix:** launch at the narrowest directory that covers the task. Grant
  read-only sibling access via access-only mechanisms (which don't import that
  sibling's instructions or skills); deny reads of vendored and generated trees.
  Where data sensitivity justifies it, make the boundary structural — a mount
  or container the agent cannot traverse out of — rather than a setting.

## Agents split by context boundary, not by job title

- **Risk:** decomposing an agentic system into roles that mirror an org chart
  (writer / tester / reviewer of the *same* change) splits work that shares
  context. The agents then make conflicting implicit decisions no one can see,
  and coordination overhead buys nothing. Inter-agent misalignment is ~32% of
  observed multi-agent failures and is the category **least** fixable by better
  prompting.
- **Check:** for each pair of agents, do they need the same context to do their
  jobs? Does more than one of them write to the same artifact? Are their outputs
  required to cohere with each other?
- **Fix:** merge them. Split only where subtasks are genuinely parallel, exactly
  one agent writes, context is cleanly separable, and each output is cheaply
  verifiable on its own. Otherwise one agent, and let the extra capability come
  from a higher effort setting rather than more agents.

## Every agent needs a termination condition

- **Risk:** the two most frequent multi-agent failures are both loops — step
  repetition (~16%) and being unaware of termination conditions (~12%). An agent
  with no stop condition and a delegation path with no hop ceiling will burn
  budget until a human notices.
- **Check:** does each agent define when it is done? Does each delegation path
  carry a hop limit? Is there a budget/rate circuit breaker independent of the
  agent's own judgment?
- **Fix:** explicit `stopWhen` + `maxTurns` per agent, a `maxHops` ceiling on
  handoffs, and a circuit breaker outside the agent that trips on volume. The
  agent must not be the only thing deciding when to stop.

## Verify objectives, not just steps

- **Risk:** task-verification failures are ~24% of multi-agent failures. Adding
  high-level objective verification was the single highest-yield mitigation
  measured (+15.6% success rate) — larger than fixing design issues.
- **Check:** is there a check that the *goal* was met, distinct from checks that
  each step ran? For high-blast-radius work, does a fresh-context reviewer see
  the output?
- **Fix:** define success as something checkable without re-running the producer,
  and verify with a clean context. Self-review by the agent that did the work is
  worth much less than a reviewer that never saw the working trace.

## Model choice is dated, not permanent

- **Risk:** a tier map written once silently describes last year's models. Models
  get deprecated and retired on published dates; intro pricing expires; a new
  mid-tier often absorbs work from the tier above it. Prompt scaffolding written
  to work around an older model's limitation becomes pure overhead — and can
  actively reduce quality on a newer one.
- **Check:** is the model choice recorded somewhere machine-checkable with a
  review date, or is it prose in a doc? Is any routed model deprecated? Does any
  workaround in a prompt name a limitation that no longer exists?
- **Fix:** keep model selection as data with a `reviewBy` date and a check that
  **fails** when it passes. Prefer raising effort over raising tier. Re-test
  scaffolding after any tier change.

## One source of truth across agent vendors

- **Risk:** parallel `AGENTS.md` and `CLAUDE.md` files drift, and the two
  families resolve conflicts differently — Claude Code concatenates all files,
  while Codex-family tools let the closest file override. Guidance whose meaning
  depends on which tool read it is a latent bug.
- **Check:** do both files exist with independent content? Does any rule rely on
  being overridden by a nearer file?
- **Fix:** keep one file and reference the other (`@AGENTS.md` import, or a
  symlink). Don't write rules that depend on override semantics if the repo
  serves both toolchains.
