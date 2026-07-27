# Installing ai-standards

Read-once setup. Kept out of `AGENTS.md` because that file is loaded in full
every session and this is not needed every session.

**Per repo** — the case that matters for contributors. Commit `AGENTS.md` plus
generated adapters. A contributor clones and their tool finds its file. **Zero
install, any tool.**

**Personal / global** — inherently per-tool; no cross-vendor package manager
exists. Claude Code:

```powershell
$Root = "C:\path\to\ai-standards"          # wherever you cloned it
git clone https://github.com/jgobuilds/ai-standards-public.git $Root
foreach ($s in @("github-repo-publish","vet-idea")) {
  New-Item -ItemType Junction `
    -Path "$env:USERPROFILE\.claude\skills\$s" `
    -Target "$Root\skills\$s"
}
```

```bash
# macOS / Linux
ROOT=~/code/ai-standards                   # wherever you cloned it
for s in github-repo-publish vet-idea; do
  ln -s "$ROOT/skills/$s" ~/.claude/skills/$s
done
```

Junctions on Windows need no elevation; symlinks need Developer Mode.

**As a Claude Code plugin** — one command, skills and slash commands together:

```
/plugin marketplace add <path-to-your-clone>
/plugin install ai-standards@jgobuilds
```

Use the **local path**: this repo is private, so a GitHub-sourced marketplace
needs auth the loader may not have. The repo root *is* the plugin root, so
`skills/` is the directory the junction already points at — one source, no copy
to drift. Adds `/pii-scan`, `/install-controls`, `/mcp-smoke`, `/context-budget`.

**Review lenses** — wire a repo to them in `.engineering-standard/config.yml`:

```yaml
overlay: ../ai-standards
lenses: [pragmatic-principles, design-patterns, code-smells,
         environment-hygiene, agent-context-architecture, build-vs-adopt,
         change-safety, evidence-standard, generated-artifacts,
         diagnosability, notification-taxonomy, cost-awareness,
         concurrency-and-branching, dependency-security]
```

Precedence, highest wins: **repo profile → this overlay → base skill**, so skill
upgrades never clobber house rules.

⚠️ `overlay:` resolves as a **filesystem path**, not a URL — it works only where
this repo is on disk. Hence it is optional, and a repo's own `AGENTS.md` must
carry everything a contributor actually needs.

