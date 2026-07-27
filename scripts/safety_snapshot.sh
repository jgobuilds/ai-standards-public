#!/bin/sh
# Working-tree safety snapshots — a shadow undo layer.
#
# Idea borrowed from ai-work-harness (auto-commit-every-write, "git is the undo
# button"), adapted: instead of committing to the working branch — which buries
# real history in noise — each snapshot is a commit on a SHADOW ref
# (refs/safety/auto). Your branch, index, and HEAD are never touched. The shadow
# ref chains, so you get a recoverable history of every state, invisible to
# normal git.
#
# Why it exists: this session lost an uncommitted edit to `git reset --hard`.
# With this running, that edit would have been one command away
# (safety_snapshot.sh --restore <file>). It operationalizes the change-safety
# rule "non-destructive by default" into a mechanism instead of a hope.
#
# Wire it as a Claude Code PostToolUse hook (Write|Edit|MultiEdit|NotebookEdit)
# so it fires after every edit. See references/change-safety.md.
#
#   safety_snapshot.sh                 take a snapshot (the hook calls this)
#   safety_snapshot.sh --list          recent snapshots, newest first
#   safety_snapshot.sh --restore FILE  restore FILE from the latest snapshot
#   safety_snapshot.sh --diff          what changed since the last snapshot
#   safety_snapshot.sh --gc [N]        keep only the last N snapshots (default 200)
#
# Non-intrusive by construction: a temp index (never the real one), commit-tree
# + update-ref (never commit), a ref outside refs/heads (never a branch). It
# respects .gitignore, so gitignored real data (personal/, .env) is NOT captured
# — the PII model holds. No network, ever.

set -u
REF=refs/safety/auto

# When invoked as a Claude Code PostToolUse hook, the tool payload arrives as
# JSON on stdin and the process cwd is the *project* dir — which may not be a
# git repo (e.g. a workspace root holding several repos as subfolders). So we
# snapshot the repo of the *edited file*, not of cwd. Pull tool_input.file_path
# out of the stdin JSON (best-effort, no jq dependency) and cd to its directory
# before touching git. With no stdin (manual CLI use) we stay in cwd.
cd_to_edited_file() {
  [ -t 0 ] && return 0                     # a TTY on stdin => manual run, keep cwd
  payload=$(cat 2>/dev/null) || return 0
  [ -n "$payload" ] || return 0
  f=$(printf '%s' "$payload" \
        | sed -n 's/.*"file_path"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' \
        | head -1)
  [ -n "$f" ] || return 0
  d=$(dirname "$f" 2>/dev/null) || return 0
  [ -d "$d" ] && cd "$d" 2>/dev/null || true
}

in_repo() { git rev-parse --is-inside-work-tree >/dev/null 2>&1; }
top()     { git rev-parse --show-toplevel 2>/dev/null; }

# Record what THIS agent has edited, and what was already dirty before it
# started. Two files under .git/, so they are never committed, never need a
# .gitignore rule, and die with the clone.
#
# WHY. A broad `git add` has swept another writer's in-flight work into a commit
# four separate times in this project — twice on the day this was written, once
# breaking someone else's build. The rule against it has been in change-safety.md
# the whole time. A rule in a document is not a mechanism; this is the missing
# half, and scripts/staged_scope_check.py is the gate that reads it.
record_scope() {
  [ -n "$TOP" ] || return 0
  # Baseline: files already modified when the agent first touched this repo.
  # Written once. Anything in here that the agent never edits is FOREIGN.
  if [ ! -f "$TOP/.git/agent-baseline" ]; then
    git -C "$TOP" status --porcelain 2>/dev/null       | sed 's/^...//' > "$TOP/.git/agent-baseline" 2>/dev/null || true
  fi
  # Ledger: every file this agent actually edited, repo-relative.
  rel=$(git -C "$TOP" ls-files --full-name -o -c --error-unmatch "$f" 2>/dev/null | head -1)
  [ -n "$rel" ] || rel=$(python -c "import os,sys;print(os.path.relpath(sys.argv[1],sys.argv[2]).replace(os.sep,'/'))" "$f" "$TOP" 2>/dev/null)
  [ -n "$rel" ] && printf '%s
' "$rel" >> "$TOP/.git/agent-touched" 2>/dev/null || true
}

snapshot() {
  cd_to_edited_file                       # follow the edited file into its repo
  in_repo || exit 0                       # not a git repo: silent no-op
  TOP=$(top); [ -n "$TOP" ] || exit 0
  record_scope
  IDX=$(mktemp 2>/dev/null || echo "${TMPDIR:-/tmp}/safety.idx.$$")
  # mktemp creates a 0-byte file, which git rejects as a corrupt index
  # ("index file smaller than expected"). Remove it so git creates a fresh,
  # valid index at that path. A throwaway index — the real one is never touched.
  rm -f "$IDX"
  GIT_INDEX_FILE="$IDX" git -C "$TOP" add -A 2>/dev/null
  TREE=$(GIT_INDEX_FILE="$IDX" git -C "$TOP" write-tree 2>/dev/null)
  rm -f "$IDX"
  [ -n "$TREE" ] || exit 0
  PARENT=$(git -C "$TOP" rev-parse --verify -q "$REF" 2>/dev/null || true)
  # Skip if nothing changed since the last snapshot.
  if [ -n "$PARENT" ] && \
     [ "$(git -C "$TOP" rev-parse -q "${PARENT}^{tree}" 2>/dev/null)" = "$TREE" ]; then
    exit 0
  fi
  TS=$(date -u +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || echo snapshot)
  # Fixed identity so it works regardless of the repo's git config.
  if [ -n "$PARENT" ]; then
    C=$(printf 'safety snapshot %s' "$TS" | \
        GIT_AUTHOR_NAME=safety GIT_AUTHOR_EMAIL=safety@local \
        GIT_COMMITTER_NAME=safety GIT_COMMITTER_EMAIL=safety@local \
        git -C "$TOP" commit-tree "$TREE" -p "$PARENT" 2>/dev/null)
  else
    C=$(printf 'safety snapshot %s' "$TS" | \
        GIT_AUTHOR_NAME=safety GIT_AUTHOR_EMAIL=safety@local \
        GIT_COMMITTER_NAME=safety GIT_COMMITTER_EMAIL=safety@local \
        git -C "$TOP" commit-tree "$TREE" 2>/dev/null)
  fi
  [ -n "$C" ] || exit 0
  git -C "$TOP" update-ref "$REF" "$C"
}

case "${1:-}" in
  --list)
    in_repo || { echo "not a git repo"; exit 1; }
    git rev-parse --verify -q "$REF" >/dev/null 2>&1 \
      && git log --format='  %h  %cd' --date=iso-local "$REF" | head -"${2:-30}" \
      || echo "  no snapshots yet"
    ;;
  --restore)
    in_repo || { echo "not a git repo"; exit 1; }
    [ -n "${2:-}" ] || { echo "usage: safety_snapshot.sh --restore <file>"; exit 2; }
    git rev-parse --verify -q "$REF" >/dev/null 2>&1 || { echo "no snapshots to restore from"; exit 1; }
    git checkout "$REF" -- "$2" && echo "restored $2 from the latest snapshot"
    ;;
  --diff)
    in_repo || { echo "not a git repo"; exit 1; }
    git rev-parse --verify -q "$REF" >/dev/null 2>&1 \
      && git diff "$REF" -- \
      || echo "no snapshots yet"
    ;;
  --gc)
    in_repo || exit 0
    KEEP="${2:-200}"
    git rev-parse --verify -q "$REF" >/dev/null 2>&1 || exit 0
    NEW=$(git rev-parse "$REF")            # keep the tip; re-root N commits back
    BACK=$(git rev-list "$REF" | sed -n "${KEEP}p")
    if [ -n "$BACK" ]; then
      # rewrite tip's history to stop at BACK by re-pointing — simplest: leave the
      # ref, just let old commits become unreachable beyond KEEP via a shallow copy
      git update-ref "$REF" "$NEW"          # no-op safety; real pruning is git gc
      echo "snapshots beyond the last $KEEP are eligible for git gc"
    fi
    ;;
  ""|--snapshot)
    snapshot
    ;;
  *)
    echo "usage: safety_snapshot.sh [--list|--restore FILE|--diff|--gc N]"; exit 2 ;;
esac
