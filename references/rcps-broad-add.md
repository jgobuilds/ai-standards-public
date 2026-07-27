# RCPS — a broad `git add` kept taking work that wasn't ours

Root-cause and preventive-solution review, 2026-07-26. Written because the same
failure happened twice in one day and it had already happened twice before.

## What actually happened

Four recorded instances, all the same shape: `git add -A` or `git add <dir>`
staged files the agent had never touched.

| # | What was staged | Consequence | How it was caught |
|---|---|---|---|
| 1 | 660 lines of another agent's untracked ADR and plans | committed under a message describing neither, **pushed** | noticed afterwards |
| 2 | an unrelated CI tool | would have been committed | **the PII gate blocked it** — its fixtures held synthetic AWS keys |
| 3 | two `.pyc` files | contributed to a render-drift gate failing 7 consecutive commits | a separate root-cause review |
| 4 | half of another agent's in-flight change — their new test, without the source function it calls | **broke their build** | CI, on the next push |

Note what caught each one. Instance 2 was caught by a gate that exists for an
entirely different purpose. Instances 1, 3 and 4 were caught after the fact, by
a person or by a red build. **None was caught by the control that governs this
failure, because there wasn't one.**

## Root cause

The proximate cause is a broad `git add` in a shared working tree, where other
agents, other sessions and the human all write.

The root cause is one level up: **the rule existed only as prose.**

`change-safety.md` has said "stage paths explicitly, and never `-A` in a repo you
might share" since instance 1. That file was read in the same session that
produced instances 3 and 4. Reading it did not prevent them.

Which exposes the real pattern. Every other recurring failure in this project
was fixed by turning a rule into a gate:

| Rule | Mechanism |
|---|---|
| No personal data in history | PII pre-commit + commit-message gate, CI scan |
| The public engine stays brand-neutral | `check_public_hygiene.py --tree` in CI |
| A move must not dangle a link | `check_links.py` in CI |
| Decisions weigh cost | `adr_check.py` fails on a missing Cost column |
| Workflows must be valid | `workflow_lint.py` |
| **Don't stage what isn't yours** | **— nothing —** |

It was the last house rule enforced by intention alone, and it was the one that
kept failing. That is not a coincidence to note in passing; it is the finding.

## Why it wasn't caught sooner

Two separate gaps, and the second is worse.

**No gate.** Covered above.

**No signal.** Instances 1, 3 and 4 produced no immediate feedback. A commit
containing someone else's file looks exactly like a commit that doesn't — the
only tell is reading `git diff --cached --name-only` and recognising a path as
foreign, which requires knowing what you touched, which nothing recorded.

Instance 4 is the sharp version: it committed **half** a change. Taking all of
someone's work is rude and recoverable. Taking half of it produces a state that
never existed in anyone's tree — a test calling a function that isn't there —
and the resulting failure belongs to nobody and reproduces for everyone.

## The fix

`scripts/staged_scope_check.py`, installed as a pre-commit gate by
`install_controls.py`, reading a ledger written by the existing PostToolUse hook.

The hook already receives the edited file's path on every `Write`/`Edit`, so the
missing information was already flowing through it — it just wasn't recorded. It
now writes two files under `.git/` (never committed, no ignore rule needed, dies
with the clone):

- `agent-touched` — every file this agent edited
- `agent-baseline` — what was already dirty when it first arrived

The gate refuses exactly two things:

| | Refused when |
|---|---|
| **FOREIGN** | staged, dirty at baseline, never edited by the agent — someone else's in-flight work |
| **IGNORED** | staged, matched by `.gitignore`, but tracked anyway, so the ignore rule does nothing |

### The design constraints that matter more than the checks

**It must not fire on ordinary work.** Files created by a generator or a shell
heredoc are legitimate and constant here, and are deliberately *not* flagged. A
gate with false positives gets switched off, and a switched-off gate protects
nothing — which is how this rule ended up as prose in the first place.

**It must not block a human.** With no ledger it is advisory and says so.
"Checked" and "nothing to check with" must never look the same.

**The override is visible.** `SCOPE_CHECK_ALLOW=<paths>` permits an intentional
commit of someone else's file, and prints `WAIVED` rather than `all yours`. A
gate that reports success after being overridden lies in the transcript, and the
transcript is what someone reads later to find out what happened.

## The correction to this review

Asked whether the gate was best practice or over-engineering, the honest answer
is **partly the latter**, and the evidence was in our own files:

- `concurrency-and-branching.md` says *"Never two agents in one working tree."*
  The FOREIGN failure is exactly that condition. The industry answer to
  concurrent writers is **isolation** — worktree, clone, container — not
  detection. This project already implements it in the fan-out lane, and the
  agent platform offers it directly.
- So a detector was built for a state our own standard says must not exist. The
  gate is now documented as a **backstop** for the un-isolated case, which is
  real and common, rather than as the answer.
- The IGNORED half stands on its own and is not a symptom of anything else — but
  it was reimplementing `git ls-files -i -c --exclude-standard` through
  `check-ignore` plumbing. Replaced with git's own idiom.

This is the fifth instance of the same meta-failure the lens names as *"apply
our own standards to our own next action"*: the relevant lens existed, and was
not run against the work in front of us.

## What generalises

- **A rule you have written down and still break is not a rule, it is a wish.**
  Count the instances. At two, ask what mechanism would have caught it; at four,
  stop discussing discipline.
- **Look at what actually caught each failure.** If the answer is "a gate for
  something else" or "a person, afterwards", the control you think you have does
  not exist.
- **Prefer the narrow gate.** Two precise checks that never fire spuriously beat
  one broad check that fires often enough to be disabled.
- **Partial capture is worse than total capture.** Any mechanism that splits an
  atomic change across a commit boundary can manufacture a state no author ever
  had.
