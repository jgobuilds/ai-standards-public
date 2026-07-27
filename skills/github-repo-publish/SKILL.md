---
name: github-repo-publish
description: >-
  Create a brand-new GitHub repository from a local folder and push its contents
  in one step. Use this whenever the user wants to "create a GitHub repo for this
  folder", "put this on GitHub", "publish/push this directory to GitHub", "make a
  repo out of X", or otherwise turn a local folder into a hosted GitHub repo — even
  if they don't say the words "git" or "repository". Handles locating the gh CLI
  when it isn't on PATH, checking auth, initializing git, the first commit, repo
  creation, and the push. Defaults to a PRIVATE repo. On Windows gh is commonly
  off PATH at "C:\Program Files\GitHub CLI\gh.exe"; the script finds it and
  checks auth rather than assuming any particular account.
---

# Publish a folder to GitHub

Turn a local folder into a new GitHub repository and push it, in one shot.

## When to use

The user wants a local folder to become a new repo on GitHub. Phrases: "create a
repo for this folder", "publish this to GitHub", "push this directory up", "make a
GitHub repo out of X". This is for **creating a new repo**, not pushing to one that
already exists on GitHub.

## The fast path (do this first)

Run the bundled script — it does everything (locate gh, verify auth, `git init`,
first commit, `gh repo create … --push`) and is safe to re-run:

```powershell
& "$env:USERPROFILE\.claude\skills\github-repo-publish\scripts\publish.ps1" -Path '<folder>'
```

Options:
- `-Name <repo-name>` — defaults to the folder's name.
- `-Visibility public` — defaults to `private`.
- `-Message "<text>"` — initial commit message (only used if there are no commits yet).

Example (what this skill was built from):

```powershell
& "$env:USERPROFILE\.claude\skills\github-repo-publish\scripts\publish.ps1" `
    -Path 'C:\path\to\your\folder' -Visibility private
```

When it finishes it prints `Done -> https://github.com/<user>/<name>`. Relay that
URL to the user.

## Decisions to confirm before running

These are quick and worth getting right, but don't over-ask — pick sensible
defaults and state them:

- **Visibility**: default **private**. Only go public if the user says so. For
  unpublished/personal material, private is the safe default.
- **Name**: default to the folder name. Confirm only if the folder name is awkward
  as a repo slug.

If the user already answered (or clearly doesn't care), just run with defaults and
tell them what you chose.

## Why the script exists (gotchas it handles)

These bit during the manual run this skill was distilled from — the script
absorbs them so you don't rediscover them:

- **gh is often not on PATH** in this environment even though it's installed. The
  script searches `C:\Program Files\GitHub CLI\`, the WinGet Links shim, and the
  WinGet Packages tree before giving up.
- **gh/git write normal progress to stderr.** In PowerShell that stderr gets
  rendered as scary red `NativeCommandError` text even on success. Judge success by
  exit code, not by the presence of red text. A line like
  `* [new branch] HEAD -> main` means the push worked.
- **GPG signing** can block a commit if a key is configured but unavailable. The
  script commits with `-c commit.gpgsign=false` to stay unblocked.
- **Idempotency**: if the folder is already a git repo, has commits, or already has
  an `origin` remote, the script skips those steps and just pushes.

## If gh is not authenticated

The script stops with a clear message. Auth is a one-time interactive step the
**user** must complete (browser/device flow) — you can't do it for them:

```powershell
& "C:\Program Files\GitHub CLI\gh.exe" auth login
```

After they finish, re-run the script.

## If gh is not installed

```powershell
winget install --id GitHub.cli --source winget --accept-source-agreements --accept-package-agreements
```

The install may not refresh PATH in the current session — that's fine, the script
finds `gh` by absolute path regardless.

## Manual fallback (if the script can't be used)

```powershell
$gh = "C:\Program Files\GitHub CLI\gh.exe"
cd '<folder>'
git init -b main
git add -A
git -c commit.gpgsign=false commit -m "Initial commit"
& $gh repo create <name> --private --source='<folder>' --remote=origin --push
```
