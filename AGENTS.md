# ai-standards

Shared engineering standards, review lenses, and skills for AI coding agents —
vendor-neutral: any tool that reads `AGENTS.md` (Codex, Cursor, Copilot, Gemini
CLI, …), plus generated pointers for those that don't.

**Apache-2.0.** Copyright © 2026 Brightside Data LLC. Licensed so it can be
adopted into anyone's tooling — which is the entire point of it.

## The rule that makes everything else work

**A repo must stand alone.** Clone it, and it works — no second clone, no
private sibling, no assumption about the parent directory. Everything here is
*optional enhancement*, never a prerequisite for contributing to a repo using it.

**One exception: PII controls.** Every repo gets the commit gate, the
commit-MESSAGE gate, and the CI scan — personal data in git history cannot be
taken back, and a commit message is history too. See `references/pii-controls.md`.

## One source, many pointers

`AGENTS.md` is the cross-vendor standard, governed under the Linux Foundation's
Agentic AI Foundation. Most agents read it natively. **Claude Code is the
exception** — it reads `CLAUDE.md` and needs an explicit `@AGENTS.md` import.

So: write `AGENTS.md`, then generate thin pointers for every other tool.

`AGENTS.md` is the only file you edit. Generated pointers: `CLAUDE.md`
(an `@AGENTS.md` import — load-bearing), `.github/copilot-instructions.md`,
`.cursor/rules/standards.mdc` (`alwaysApply`), `.windsurfrules`, `.clinerules`,
`GEMINI.md`.

```bash
python scripts/apply_adapters.py <repo>          # write them
python scripts/apply_adapters.py <repo> --check  # fail if drifted
```

Pointers, not copies. A copy per tool would drift silently — the exact failure
`references/build-vs-adopt.md` warns about. `--check` belongs in CI.

## What's here

Each row is enough to decide whether to open the file; the depth is inside it.

| Path | What |
|---|---|
| `references/pii-controls.md` + `scripts/pii_scan.py` + `scripts/install_controls.py` | **Not optional.** Data class (P0–P3) × visibility → required mechanism. Commit gate, commit-**message** gate, CI scan, history audit. Installs *and verifies* both hooks — configured is not installed. |
| `references/environment-hygiene.md` | Never install into a shared interpreter. Dependency + environment safety. |
| `references/agent-context-architecture.md` | How a repo presents itself to an agent: instruction budgets, shared context without drift, splitting by context boundary, termination conditions, model choice as dated. |
| `references/change-safety.md` | Verify outcomes, non-destructive git, **stage explicitly**, publish by allowlist, blast-radius-before-delete. Each rule written after a real failure. Includes `scripts/safety_snapshot.sh`. |
| `references/evidence-standard.md` | What a published claim carries: rank 1–4, a `Pulled:` date, community-as-lead-not-citation, name your softest assumption, checked refs. |
| `references/generated-artifacts.md` | Derivatives drift silently. Regenerate in the build, mark the file, never hand-edit, gate drift in CI, commit-or-ignore on purpose. |
| `references/diagnosability.md` | Build so an agent can self-diagnose: log the inputs that decided the outcome, no silent empty results, honest progress, transient ≠ permanent, fallbacks that survive the failure. |
| `references/dependency-security.md` | Privileged-path principle (the bar scales with position, not popularity), digest-pin + dated review gate, scan on a schedule, containment over patch cadence. |
| `references/concurrency-and-branching.md` | Parallel agents without contention: the isolation ladder (serialize → worktrees → clones → containers), partition ownership, leases, pruning. |
| `references/cost-awareness.md` | Cost at decision time, not invoice time: four classes, state the *trigger* not the number, count non-dollar costs. Lands as a Cost column in every ADR options table. |
| `references/notification-taxonomy.md` | Awareness without alert fatigue: interrupt / digest / on-demand tiers, the BLUF message contract, six-line cap, detail behind a link. |
| `references/ticketing.md` + `scripts/ticket.py` | The third tier: durable state. Four verbs over a swappable backend (GitHub Issues by default, file, none). Stable-key idempotency so a re-run updates instead of duplicating. Says why NOT to add a wiki. |
| `references/ci-notifications.md` | CI failure alerts (Slack/Teams/webhook) — the per-repo setup manifest. |
| `references/build-vs-adopt.md` | Survey the market before building. NIH and dependency bloat are both real. |
| `references/naming-standard.md` | Endorsed-house architecture, product + repo naming, findability levers, collision-check rule. One org's dated register belongs with its brand assets, not here. |
| `references/solutions-log.md` + `scripts/solution.py` | Problems solved once, written while the context was fresh. One rule splits it from the known-cause table: does it announce itself in a log line? Its best section is *what was tried that did NOT work* — the only part nobody can reconstruct. Shape gated, prose deliberately not. |
| `references/knowledge-for-agents.md` | Markdown as source of truth + a generated machine index; the retrieval ladder (grep → keyword → vector, each step earned); progressive disclosure and what a catalog actually buys; freshness as a field, not a vibe. |
| `references/portability-tiers.md` | Tier I vs Tier P: what "stands alone" requires, the three couplings that break a cloner, install burden as a separate constraint. |
| `scripts/context_budget.py` | Aggregate budget — ALWAYS-LOADED vs ON-DEMAND, in chars, WARN/FAIL bands. Per-file limits cannot see the sum. |
| `skills/build-mcp-server/` + `scripts/mcp_smoke.py` | Adopt/generate/write decision, tool-surface conventions, egress declaration, conformance gate. Never register a tool until the whole round trip is proven. |
| `skills/instance-onboarding/` + `scripts/instance_scaffold.py` | Interview an org and stand up its private overlay — goals, who it serves, how success is measured, stack, org design, data posture — then propose the STARTING FLEET: first agent, capabilities, knowledge resources. Unanswered fields are machine-checked, so a half-filled overlay cannot read as complete. |
| `skills/github-repo-publish/` | Local folder → GitHub repo. Private by default. |
| `skills/vet-idea/` | Vet a product idea against the market. Built to disconfirm. |

## Install

Per repo — the case that matters — commit `AGENTS.md` plus its generated
adapters and a contributor needs no install at all. Global install, the Claude
plugin, and wiring the review lenses into `.engineering-standard/config.yml`:
see [`INSTALL.md`](INSTALL.md).

## Known limits

- **Distribution can't be cross-vendor.** Content generalises; packaging does
  not. A Claude plugin won't install into Cursor. Per-repo adapters are the
  portable answer; global install stays per-tool.
- **Personal skills are invisible to unattended runs.** Cloud, scheduled and
  Cowork sessions don't read `~/.claude/skills/` — an invoked skill is reported
  *missing*, not degraded. Anything that must run unattended has to be committed
  to the repo or packaged as a plugin.
- **Adapter coverage is a snapshot.** Tools change where they look. `--check`
  catches drift in content, not a tool inventing a new path. Re-verify when
  adding a tool.

## Working on this repo

Edit `AGENTS.md`, never the generated adapters — they are overwritten. After
changing it, re-run `apply_adapters.py .` and commit both.

Loaded in full every session, and longer files measurably reduce adherence.
Gate with `python scripts/context_budget.py .` — ALWAYS-LOADED under 12,000
chars — not a line count; lines are a poor proxy. Depth belongs in
`references/`, read on demand.
