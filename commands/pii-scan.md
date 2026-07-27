---
description: Scan a repo for PII — working tree, staged changes, or full git history.
argument-hint: "[path] [--tree|--staged|--history] [--visibility public|private] [--max-tier P0..P3]"
---

Run the PII scanner over `$ARGUMENTS` (default: the current repo, `--tree`).

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/pii_scan.py" $ARGUMENTS
```

Then interpret the result for the user:

- **The scan never prints a matched value** — only type, file and line. If you
  need to see the value, open the file yourself; do not echo it into the
  conversation, and never into a commit message or CI log.
- **Treat a clean scan as "no known pattern found", not "no PII present".**
  Structured data (SSN, cards, email, phone) is caught reliably; names and street
  addresses are not. The primary control is architectural — PII absent by
  construction — and scanning is the backstop.
- **`engine:` tells you how much you actually got.** "built-in only (gitleaks not
  installed)" means secret detection fell back to two hand-written patterns.
  Install gitleaks for the real ruleset.
- If findings exceed the repo's max tier, the fix order is: **remove the value,
  externalize it, or tokenize it** — in that order. Adding an allow-regex is the
  last resort and needs a stated reason.
