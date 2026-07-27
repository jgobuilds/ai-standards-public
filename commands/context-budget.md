---
description: Measure a repo's agent-context budget — what is loaded every session vs on demand.
argument-hint: "[path]"
---

Measure the context budget for `$ARGUMENTS` (default: current repo).

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/context_budget.py" $ARGUMENTS
```

Interpret it for the user:

- **ALWAYS-LOADED is the number that matters.** The ancestor `CLAUDE.md` chain
  plus its `@imports` is paid on every session, in every project — a broken link
  or a bloated table there costs continuously.
- **Per-file limits are necessary and not sufficient.** Every file can pass its
  own budget while the sum grows past what an agent uses well. That is the whole
  reason this measures the aggregate.
- **WARN is a prompt to decide, not to panic.** The honest responses are: move
  depth into an on-demand reference, merge two files that are always read
  together, or raise the target deliberately and say why. Silently raising the
  target whenever it goes red turns the check into decoration.
