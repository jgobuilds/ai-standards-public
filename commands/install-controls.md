---
description: Install and verify the PII commit gates in one repo, or sweep every repo in a workspace.
argument-hint: "<repo> | --all [dir] [--with-ci]"
---

Install the PII controls for `$ARGUMENTS`.

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/install_controls.py" $ARGUMENTS
```

What it does, and what to check afterwards:

- Installs a native **pre-commit** gate and a **commit-MESSAGE** gate. The message
  one matters most: it is the only control that reads the prose written *about*
  the protected files, and narrative leaks are what it was written for.
- **It verifies its own work.** Configured is not installed; installed is not
  verified. A repo that reports `FAILED` is not protected.
- **`--all` resolves visibility per repo** and defaults to *public* — the stricter
  setting — when it cannot tell. Under-gating a world-readable repo is not
  recoverable; over-reporting on a private one is merely annoying.
- **`--with-ci`** also vendors the scanner and installs a CI workflow, because the
  hooks are `--no-verify`-bypassable by design and CI is the gate that holds.
- Repos with **no remote are skipped for CI** — a workflow GitHub never sees is
  decoration, not enforcement.

Afterwards, remind the user that the shared vocabulary (`~/.pii-terms`) is what
catches employer, client and codename nouns. Patterns cannot detect those, and an
empty file protects nothing.
