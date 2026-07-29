# Change safety (house lens)

A lens for how an agent *makes changes* — the operating discipline, not the code.
Every item here was written after the agent violated it in a real session; the
failures are named so the rule has teeth.

Each item: the risk, what to check, the fix.

## Verify the outcome — never report a result you have not confirmed

- **Risk:** the most common failure mode is claiming success from the command
  you *ran*, not the state that *resulted*. A real instance: a multi-file
  `git add` failed atomically on a missing file, nothing staged, `git commit`
  printed "nothing to commit", and the run was reported as "pushed" — showing the
  **old** hash. Five repos were silently not committed.
- **Check:** after any state-changing operation, did the state actually change?
  - commit → `git rev-parse HEAD` moved, and `git status` is clean
  - push → `git rev-list origin/main..HEAD` is empty
  - delete → the thing is gone *and* nothing still references it
  - install → the artifact exists and runs (`--verify`, not "the installer exited 0")
- **Fix:** confirm the post-state, then report it. "I ran X" and "X happened" are
  different claims; only make the second one after checking.

## Non-destructive by default

- **Risk:** `git reset --hard`, `git checkout -- .`, `push --force`, `rm -rf`
  destroy uncommitted or unpushed work with no undo. A real instance: a
  `reset --hard HEAD~1` to undo a test commit also discarded an unrelated
  uncommitted `.gitignore` edit.
- **Check:** before any destructive command — is there uncommitted or unpushed
  work in the tree it will touch? (`git status --porcelain`, `git stash list`,
  `git rev-list @{u}..`)
- **Fix:** prefer the reversible form. `git revert` over `reset --hard`; move a
  file aside over deleting it; `git stash` before a hard operation you still want.
  If a destructive op is genuinely necessary, snapshot first and say what you
  are about to lose.

### The safety-snapshot net (turns the rule into a mechanism)

Discipline fails; a mechanism does not. `scripts/safety_snapshot.sh` snapshots
the working tree to a **shadow ref** (`refs/safety/auto`) that never touches your
branch, index, or HEAD — a pure undo layer under normal git. Wired as a Claude
Code **PostToolUse hook**, it fires after every edit, so any state is one command
back even after a `reset --hard`:

```jsonc
// ~/.claude/settings.json (or a project .claude/settings.json)
"hooks": {
  "PostToolUse": [{
    "matcher": "Write|Edit|MultiEdit|NotebookEdit",
    "hooks": [{ "type": "command",
      // Windows: give the full path to Git-Bash's bash.exe — cmd.exe launches
      // the hook and won't find `sh`/`bash` on PATH. macOS/Linux: just
      // "sh /abs/path/to/ai-standards/scripts/safety_snapshot.sh".
      "command": "\"C:\\Program Files\\Git\\bin\\bash.exe\" \"C:/path/to/ai-standards/scripts/safety_snapshot.sh\"" }]
  }]
}
```

The script reads the tool payload on stdin and snapshots the repo of the
**edited file**, not of the process cwd — so it works even when Claude Code runs
from a workspace root that isn't itself a git repo, with the real repos as
subfolders. Run manually (no stdin) it falls back to cwd.

Recover with `safety_snapshot.sh --restore <file>` / `--list` / `--diff`. It
respects `.gitignore`, so gitignored real data (`personal/`, `.env`) is never
captured — the PII model holds. The shadow ref lives under `refs/safety/`, never
`refs/heads/`, so `git push` never sends it anywhere. No network.

The idea is borrowed from **ai-work-harness** (auto-commit-every-write); the
shadow-ref adaptation is ours, so it doesn't bury real history in per-write
commits. *This is the mechanism that would have prevented the incident above.*

## Stage explicitly — a broad add takes work that is not yours

- **Risk:** `git add -A` / `git add .` stages everything in the tree, including
  another agent's in-flight work, a colleague's uncommitted edits, and generated
  junk. Two real instances in one session: a `git add docs/` swept 660 lines of
  another agent's untracked ADR and plans into a commit whose message described
  neither, and it was pushed before anyone noticed; later a `git add -A` in a
  different repo swept in an unrelated CI tool — that one was **caught only
  because the PII gate blocked it**, its test fixtures containing synthetic AWS
  keys. Nothing was lost either time, but the second was luck, not process.
- **Check:** before every commit — `git diff --cached --name-only`. Is every path
  yours, and does the commit message describe all of them? A shared working tree
  is the normal case, not the exception: other agents, other sessions, and the
  human all write here.
- **Fix (the mechanism):** `scripts/staged_scope_check.py`, installed as a
  pre-commit gate by `install_controls.py`. It refuses two things and nothing
  else: a staged file that was already modified when the agent started and that
  the agent never edited (someone else's in-flight work), and a staged file that
  `.gitignore` matches but git tracks anyway. Override explicitly with
  `SCOPE_CHECK_ALLOW=<paths>`, which is reported in the output rather than
  silently honoured. Advisory — never blocking — when no agent ledger exists, so
  a human at a terminal is unaffected.

  **It is a backstop, not the fix.** The FOREIGN half only arises when two
  writers share one working tree — which `concurrency-and-branching.md` already
  forbids, and which the fan-out lane already solves with a worktree per agent.
  Isolation removes the failure; this only notices it. Reach for the worktree
  first; keep the gate for the un-isolated case, which is the common shape when
  a human and an agent write in the same tree.

  The full review of why it took four instances is kept internally, in
  `references/rcps-broad-add.md` — not linked here because that file is
  excluded from the public snapshot, and a link that dangles for every
  outside reader is worse than a sentence they can act on.

  **This rule needed a mechanism because it kept being broken by the person who
  wrote it.** Four recorded instances, two on the same day, one of them breaking
  another agent's build — while the rule sat in this file, which had been read
  that session. Every other recurring failure here was fixed by becoming a gate;
  this was the last one running on intention. Discipline is not a control.

- **Fix (the habit):** stage paths explicitly, and never `-A` in a repo you might share. If
  you have already committed someone else's files, do **not** rewrite pushed
  history to fix provenance — `git rm --cached` the ones that were untracked and
  restore the ones that were tracked to their prior blob, then commit that as a
  correction. The content is safe either way; what you are repairing is the
  record.

## Publishing is a list, not a side effect

- **Risk:** a file placed in a directory that gets deployed is public whether or
  not anything links to it — publicly reachable and undiscoverable at once, which
  is the worst of both. A real instance: a marketing PDF moved into a site's
  source tree would have shipped unlinked to a live domain.
- **Check:** does the deploy copy a *directory* or an *enumerated list*? If a
  directory — what is in it that nobody chose to publish?
- **Fix:** make publication an explicit allowlist the deploy script reads, so
  adding something to the site is a deliberate edit rather than a consequence of
  where a file was saved. Publishing a thing is a fine decision; publishing it
  *accidentally* is not.

## Check blast radius before deleting or moving

- **Risk:** removing or renaming a shared thing leaves dangling references
  elsewhere. A real instance: deleting `org-standard` left six references across
  the workspace, one of them a functional break (`overlay:` pointing at a path
  that no longer existed).
- **Check:** before `rm`/`mv`/rename of anything referenced elsewhere —
  `grep -rn "<name>"` across the workspace first. Who points at this?
- **Fix:** update or remove every inbound reference in the same change. A move is
  not done when the file lands; it is done when nothing points at where it was.

## Apply our own standards to our own next action

- **Risk:** writing a standard and then not following it on the very next task. A
  real instance: hand-writing a PII scanner immediately after authoring the
  `build-vs-adopt` lens — for PII detection, a solved-problem domain that lens
  names explicitly.
- **Check:** does the thing I am about to do trigger one of our own lenses?
  Building something → `build-vs-adopt`. Committing → the PII gate. Moving a
  repo → portability. The standards apply to the author, not only the reviewed.
- **Fix:** run the lens on your own work before proceeding. The habit is the
  control; skipping it "just this once" is how every one of these happened.

## A heuristic without a labeled corpus is unshipped

- **Risk:** shipping a detector or classifier and discovering its false
  positives/negatives in production. A real instance: a regex PII scanner shipped
  with five false-positive classes, each found only by running it against live
  repos.
- **Check:** is there a test that feeds known-good and known-bad inputs and
  asserts the verdict? Does breaking the detector make that test fail?
- **Fix:** build the corpus first, or alongside. Every false positive found in
  the wild becomes a permanent regression case. Verify the test actually fails
  when the guard is removed — a test that passes both ways tests nothing.

## Verify facts from the source, not a summary or memory

- **Risk:** acting on a rendered page, a search snippet, or recall. Real
  instances caught in the act: a summary calling an abandoned library
  "maintained"; another misreporting a license; a claim that a tool was a
  "drop-in replacement" that its own README never makes.
- **Check:** for a maintenance/license/capability claim, did it come from the
  authoritative source (the API, the primary doc, the actual file) or a
  secondary description?
- **Fix:** go to the source. GitHub API over stars-and-READMEs; the flag
  registration over the docs prose; the file over the memory of the file.

## A harness error is not a code error until proven

- **Risk:** blaming the code for a failure in the tooling around it. A real
  instance: a 400 read as a router bug that was actually nested-shell quoting
  mangling the JSON payload.
- **Check:** before debugging the target, is the harness itself sound? Did the
  input arrive intact? Deeply-nested quoting, here-strings, and multi-level shell
  escaping are the usual culprits.
- **Fix:** write the payload to a file rather than quoting it through three
  shells. Reproduce the failure the simplest possible way before concluding the
  code is wrong.

---

Most of these are enforced by tooling where they can be: `workspace_doctor`
flags committed absolute paths (blast-radius / portability), `pii_scan` has a
labeled corpus, the PII gate runs on every commit. The rest are judgment, which
is why they are written down — a rule you have read is easier to keep than one
you have to rediscover.
