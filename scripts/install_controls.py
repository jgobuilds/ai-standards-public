#!/usr/bin/env python3
"""Install PII controls into a repo — and actually turn them on.

The failure this exists to prevent was observed in this workspace: two repos
carried a `.pre-commit-config.yaml` and **neither had the hook installed**.
`pre-commit install` had never been run, so `.git/hooks/pre-commit` did not
exist and those controls had fired exactly zero times. Configured is not
installed; installed is not verified.

So this does three things and then checks its own work:

  1. ignore patterns for the usual PII-bearing paths
  2. a native `.git/hooks/pre-commit` — no framework dependency, works even
     where `pre-commit` is not installed, and chains to any existing hook
  3. a `local` entry in `.pre-commit-config.yaml` when one exists, because
     `pre-commit install` OVERWRITES the native hook and would otherwise
     silently remove the control we just added
  4. `--verify` re-checks all of the above and exits non-zero if anything is off

    python scripts/install_controls.py <repo> --visibility public --max-tier P1
    python scripts/install_controls.py <repo> --verify
"""
import os, re, sys, argparse, subprocess, stat, shutil, glob

IGNORE_BLOCK = """
# --- PII controls (ai-standards) ---
# Real personal data lives OUTSIDE the repo. These paths are conventional
# homes for it; the pre-commit hook is what actually enforces the rule.
*.local.*
*.private.*
.local/
data/private/
data/raw/
secrets/
.pii-vault/
.env
.env.*
!.env.example
# The repo's private vocabulary for the commit-msg gate: employer, client, or
# codename terms that must never appear in a message. Gitignored because a
# tracked list of the words you are hiding is itself the disclosure.
.pii-terms
# --- end PII controls ---
"""

HOOK = """#!/bin/sh
# PII pre-commit gate (ai-standards). Blocks personal data BEFORE it enters
# history — the only cheap moment, since history is effectively permanent.
# Bypassable with --no-verify by design; CI is the real gate.
#
# Deliberately NOT `set -e`: this script uses `if`/`||` for control flow, and
# under `set -e` a false test in a chained expression aborts the hook and
# blocks a perfectly clean commit. A gate with false positives gets disabled.
SCAN="{scan}"
HOOKDIR=$(dirname "$0")
REPO=$(git rev-parse --show-toplevel)
# FAIL CLOSED. This used to be `if [ -f "$SCAN" ]` with no else — so if the
# scanner path stopped resolving (ai-standards moved, renamed, cloned to another
# machine, different drive) the gate did NOTHING and the commit succeeded
# silently. A backstop that disappears without saying so is worse than no
# backstop, because the team believes it is covered.
if [ "$PII_GATE" = "off" ]; then
  echo "PII gate SKIPPED: PII_GATE=off was set deliberately." >&2
elif [ ! -f "$SCAN" ]; then
  echo "PII gate CANNOT RUN: scanner not found at $SCAN" >&2
  echo "  Blocking the commit rather than passing it unscanned." >&2
  echo "  Fix: re-run ai-standards/scripts/install_controls.py <repo>" >&2
  echo "  Or, for a genuinely toolless environment: PII_GATE=off git commit ..." >&2
  exit 1
elif ! python "$SCAN" . --staged --visibility {vis} --max-tier {tier}; then
  echo ""
  echo "  Commit blocked by the PII gate. Remove, externalize, or tokenize the"
  echo "  value (ai-standards/references/pii-controls.md). If it is genuinely"
  echo "  safe, add a reviewed regex to .pii-allow."
  exit 1
fi
# SCOPE gate — refuses files this agent never touched. Separate from the PII
# gate because it answers a different question ("is this yours?" vs "is this
# safe?") and because a shared working tree is the normal case here, not the
# exception. Advisory when no agent ledger exists, so a human at a terminal is
# never blocked by it.
SCOPE="{scope}"
if [ "$SCOPE_GATE" = "off" ]; then
  echo "Scope gate SKIPPED: SCOPE_GATE=off was set deliberately." >&2
elif [ -f "$SCOPE" ] && ! python "$SCOPE"; then
  exit 1
fi
{chain}
exit 0
"""

MSG_HOOK = """#!/bin/sh
# PII commit-MESSAGE gate (ai-standards). Every other control in this lens
# protects FILES; the message is prose written about them, is permanent and
# public, and is otherwise unscanned. The observed leak was narrative — a
# private document quoted to explain a fix — which no file-level control sees.
#
# Deliberately NOT `set -e`, for the same reason as the pre-commit gate.
SCAN="{scan}"
HOOKDIR=$(dirname "$0")
# FAIL CLOSED — see the pre-commit hook for why. This gate matters more, not
# less: the message is the one artifact nothing else scans.
if [ "$PII_GATE" = "off" ]; then
  echo "PII message gate SKIPPED: PII_GATE=off was set deliberately." >&2
elif [ ! -f "$SCAN" ]; then
  echo "PII message gate CANNOT RUN: scanner not found at $SCAN" >&2
  echo "  Blocking the commit rather than passing it unscanned." >&2
  echo "  Fix: re-run ai-standards/scripts/install_controls.py <repo>" >&2
  echo "  Or, for a genuinely toolless environment: PII_GATE=off git commit ..." >&2
  exit 1
elif ! python "$SCAN" . --message "$1" --visibility {vis} --max-tier {tier}; then
  echo ""
  echo "  Commit blocked: the MESSAGE carries private detail."
  echo "  Describe the defect class and the fix, not the specifics behind it."
  echo "  Reproduction detail belongs in a test (synthetic) or in ignored notes."
  echo "  See ai-standards/references/pii-controls.md."
  exit 1
fi
{chain}
exit 0
"""

PRECOMMIT_ENTRY = """  - repo: local
    hooks:
      - id: pii-scan
        name: PII scan (ai-standards)
        entry: python {scan} . --staged --visibility {vis} --max-tier {tier}
        language: system
        pass_filenames: false
        always_run: true
"""


def sh(root, *args):
    return subprocess.run(["git", "-C", root, *args], capture_output=True, text=True)


def hooks_dir(root):
    r = sh(root, "rev-parse", "--git-path", "hooks")
    p = (r.stdout or "").strip() or ".git/hooks"
    return p if os.path.isabs(p) else os.path.join(root, p)


def is_precommit_framework(text):
    """Is this hook the pre-commit framework's generated shim?

    Worth naming specially. Observed 2026-07-25: `pre-commit install` silently
    REPLACED this gate (moving it to <name>.legacy) so the PII scan stopped
    running, and its shim then failed on Windows with
    "ExecutableNotFoundError: Executable /bin/sh not found", blocking every
    commit. Chaining it would re-import that breakage into our hook, and
    preserving it as .pre-pii would imply it is a hook worth keeping.
    """
    return "File generated by pre-commit" in text or "-mpre_commit" in text


def write_hook(hd, name, template, scan, vis, tier, extra_gates=()):
    """Install one native hook, preserving and chaining anything already there.

    Shared by both gates: a second copy of this logic is a second chance to get
    the never-destroy-someone's-hook rule subtly wrong.
    """
    done = []
    path = os.path.join(hd, name)
    chain = ""
    if os.path.isfile(path):
        existing = open(path, encoding="utf-8", errors="replace").read()
        if is_precommit_framework(existing):
            # Do NOT chain it and do NOT keep it as a hook worth calling.
            os.replace(path, path + ".precommit-framework.bak")
            done.append(
                f"DISPLACED the pre-commit framework shim (saved as "
                f"{name}.precommit-framework.bak, NOT chained — it is broken on "
                f"Windows and it had displaced this gate)")
            # If the framework shunted OUR hook aside, that copy is now redundant.
            legacy = os.path.join(hd, name + ".legacy")
            if os.path.isfile(legacy):
                txt = open(legacy, encoding="utf-8", errors="replace").read()
                if "ai-standards" in txt:
                    os.remove(legacy)
                    done.append(f"removed {name}.legacy (our own gate, now reinstalled)")
        elif "ai-standards" not in existing:
            # Never destroy someone's hook — move it aside and call it.
            backup = path + ".pre-pii"
            os.replace(path, backup)
            b = os.path.basename(backup)
            chain = "\n".join([
                f'if [ -x "$HOOKDIR/{b}" ]; then',
                f'  "$HOOKDIR/{b}" "$@" || exit $?',
                "fi",
            ])
            done.append(f"existing {name} preserved as {b} and chained")

    # Repo-local gates run in the SAME hook, so a framework install cannot
    # displace one of them and leave the other running.
    for g in extra_gates:
        chain += "\n".join([
            "",
            f'if [ -f "$REPO/{g}" ]; then',
            f'  if ! python "$REPO/{g}"; then',
            f'    echo ""; echo "  Commit blocked by {g}."',
            "    exit 1",
            "  fi",
            "fi",
        ])
        done.append(f"repo-local gate wired into {name}: {g}")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        # The scope gate ships beside the scanner, so it resolves the same way.
        scope = os.path.join(os.path.dirname(scan), "staged_scope_check.py")
        f.write(template.format(scan=scan, vis=vis, tier=tier, chain=chain,
                                scope=scope))
    os.chmod(path, os.stat(path).st_mode | stat.S_IXUSR | stat.S_IXGRP)
    done.append(f"native .git/hooks/{name} installed AND executable")
    return done


def discover_extra_gates(root):
    """Repo-local commit gates to run inside OUR hook.

    Kept in the same hook on purpose: two separate hooks are two things a
    framework install can displace independently, and the one that goes quiet is
    the one nobody notices.
    """
    known = ["scripts/check_public_hygiene.py"]
    return [g for g in known if os.path.isfile(os.path.join(root, g))]


def install(root, scan, vis, tier, extra_gates=None):
    done = []
    gates = extra_gates if extra_gates is not None else discover_extra_gates(root)

    gi = os.path.join(root, ".gitignore")
    cur = open(gi, encoding="utf-8").read() if os.path.isfile(gi) else ""
    if "PII controls (ai-standards)" not in cur:
        with open(gi, "a", encoding="utf-8", newline="\n") as f:
            if cur and not cur.endswith("\n"):
                f.write("\n")
            f.write(IGNORE_BLOCK)
        done.append(".gitignore patterns added")
    else:
        done.append(".gitignore already carries the block")

    hd = hooks_dir(root)
    os.makedirs(hd, exist_ok=True)
    done += write_hook(hd, "pre-commit", HOOK, scan, vis, tier, gates)
    # The message gate. Separate hook because git gives the message to commit-msg
    # only; pre-commit never sees it.
    done += write_hook(hd, "commit-msg", MSG_HOOK, scan, vis, tier)

    # The .pre-commit-config.yaml is TRACKED and committed. It must never carry
    # an absolute path to a scanner outside the repo — that commits a
    # machine-specific path (a portability bug, caught by workspace_doctor's
    # local-path check). Only add the entry when the scanner lives INSIDE the
    # repo (a relative reference is portable); otherwise the native, UNTRACKED
    # .git/hooks hook is the enforcement, and the only caveat is that a later
    # `pre-commit install` clobbers it — re-run this installer if that happens.
    pc = os.path.join(root, ".pre-commit-config.yaml")
    if os.path.isfile(pc):
        inside = os.path.abspath(scan).startswith(os.path.abspath(root) + os.sep)
        text = open(pc, encoding="utf-8").read()
        if "pii-scan" in text:
            done.append(".pre-commit-config.yaml already has the entry")
        elif inside:
            rel_scan = os.path.relpath(scan, root).replace("\\", "/")
            with open(pc, "a", encoding="utf-8", newline="\n") as f:
                if not text.endswith("\n"):
                    f.write("\n")
                f.write(PRECOMMIT_ENTRY.format(scan=rel_scan, vis=vis, tier=tier))
            done.append(".pre-commit-config.yaml entry added (repo-relative)")
        else:
            done.append(".pre-commit-config.yaml left untouched — scanner is "
                        "outside the repo; a tracked absolute path would not be "
                        "portable. Native hook enforces; re-run after `pre-commit install`.")
    return done


def verify(root, scan):
    problems = []
    gi = os.path.join(root, ".gitignore")
    if not (os.path.isfile(gi) and "PII controls (ai-standards)" in open(gi, encoding="utf-8").read()):
        problems.append(".gitignore is missing the PII block")

    # Both gates are checked. They fail independently: `pre-commit install`
    # overwrites pre-commit and leaves commit-msg alone, so a repo can easily end
    # up with one gate live and the other silently gone.
    for name in ("pre-commit", "commit-msg"):
        hook = os.path.join(hooks_dir(root), name)
        if not os.path.isfile(hook):
            problems.append(f"no .git/hooks/{name} — that gate is NOT installed")
            continue
        body = open(hook, encoding="utf-8", errors="replace").read()
        if "ai-standards" not in body:
            problems.append(f"{name} hook exists but is not the PII gate "
                            "(pre-commit install may have overwritten it)")
        elif os.name != "nt" and not os.access(hook, os.X_OK):
            problems.append(f"{name} hook is not executable — git will skip it")

    # Only require the tracked entry when the scanner is repo-relative (portable
    # to commit). When it is external, the entry is intentionally absent — the
    # native hook is the enforcement — so its absence is not a problem.
    pc = os.path.join(root, ".pre-commit-config.yaml")
    if os.path.isfile(pc):
        inside = os.path.abspath(scan).startswith(os.path.abspath(root) + os.sep)
        body = open(pc, encoding="utf-8").read()
        if inside and "pii-scan" not in body:
            problems.append(".pre-commit-config.yaml has no pii-scan entry — "
                            "running `pre-commit install` would silently disable the gate")
        # (?<![A-Za-z0-9]) is load-bearing: without it the drive-letter pattern
        # matches the "s:/" inside "https://", so EVERY standard pre-commit config
        # carrying a repo URL was reported as having a machine-specific path.
        # A verifier that cries wolf on the common case gets ignored, and then the
        # real absolute path it exists to catch slips straight through.
        if re.search(r"(?<![A-Za-z0-9])[A-Za-z]:[\\/]|/(?:home|Users)/[A-Za-z0-9._-]+/", body):
            problems.append(".pre-commit-config.yaml contains a machine-specific "
                            "absolute path — not portable, will break for others")

    if not os.path.isfile(scan):
        problems.append(f"scanner not found at {scan}")
    return problems


def find_gh():
    """gh, including the common Windows install that is NOT on PATH."""
    p = shutil.which("gh")
    if p:
        return p
    for c in (r"C:\Program Files\GitHub CLI\gh.exe",
              r"C:\Program Files (x86)\GitHub CLI\gh.exe"):
        if os.path.isfile(c):
            return c
    return None


def repo_visibility(root, gh):
    """('public'|'private', how_we_know). Resolved per repo — never assumed
    uniform, because one public repo in a private fleet is the whole risk.

    When it cannot be determined we return PUBLIC, the STRICTER setting. Getting
    this wrong toward "private" under-gates a repo the world can read; getting it
    wrong toward "public" merely over-reports, and is fixed by re-running with an
    explicit --visibility. Only one of those is recoverable.
    """
    if not gh:
        return "public", "assumed public (gh not found)"
    try:
        r = subprocess.run([gh, "repo", "view", "--json", "visibility", "-q", ".visibility"],
                           cwd=root, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=60)
    except (OSError, subprocess.SubprocessError) as e:
        return "public", f"assumed public ({type(e).__name__})"
    v = (r.stdout or "").strip().lower()
    if r.returncode == 0 and v in ("public", "private", "internal"):
        # `internal` is not world-readable, but it is not just-me either; treat
        # it as public so the stricter tier applies.
        return ("private" if v == "private" else "public"), f"gh: {v}"
    return "public", "assumed public (no remote or gh error)"


def git_repos(base):
    return sorted(
        os.path.join(base, d) for d in os.listdir(base)
        if os.path.isdir(os.path.join(base, d, ".git")))


def existing_tier(root):
    """The --max-tier a repo's installed hook already uses, if any.

    A fleet sweep must not silently RE-TUNE a repo. One repo may run at P2
    deliberately; re-installing it at the P1 default would start blocking commits
    that were legitimately passing, and the sweep would get blamed for it. Read
    the setting back out of the hook rather than assuming everyone wants the
    default.
    """
    hd = hooks_dir(root)
    for name in ("commit-msg", "pre-commit"):
        p = os.path.join(hd, name)
        if not os.path.isfile(p):
            continue
        text = open(p, encoding="utf-8", errors="replace").read()
        if "ai-standards" not in text:
            continue
        m = re.search(r"--max-tier\s+(P[0-3])", text)
        if m:
            return m.group(1)
    return None


def refresh_vendored(root, scan):
    """Keep a repo's VENDORED copy of the scanner identical to this one.

    A repo that must enforce in CI cannot reach a private sibling — CI checks out
    that repo alone, which is the whole point of "a repo must stand alone". So it
    vendors the scanner. The cost of a copy is drift (build-vs-adopt.md), and a
    security control that has silently fallen behind is exactly the failure this
    lens keeps finding. The sweep already visits every repo, so it is the natural
    place to re-sync them.

    Only touches repos that ALREADY vendor it — this never adds a copy to a repo
    that did not ask for one.
    """
    dest = os.path.join(root, "scripts", "pii_scan.py")
    if not os.path.isfile(dest):
        return None
    try:
        src_b = open(scan, "rb").read()
        dst_b = open(dest, "rb").read()
    except OSError as e:
        return f"vendored scanner unreadable ({type(e).__name__})"
    if src_b == dst_b:
        return None
    with open(dest, "wb") as f:
        f.write(src_b)
    return "vendored scanner REFRESHED (it had drifted)"


def install_ci(root, scan, vis, tier):
    """Vendor the scanner and install the CI workflow. Returns a status string.

    The hooks are bypassable with --no-verify by design; CI is the real gate, and
    AGENTS.md says every repo gets all three (commit gate, message gate, CI scan).
    Measured, only ai-standards had the CI half — so the stated standard was met
    in exactly one of eight repos.
    """
    if not git_has_remote(root):
        # A workflow in a repo GitHub never sees is decoration. Say so rather
        # than reporting an install that can never run.
        return "SKIPPED CI: no remote — Actions would never run"

    existing = glob.glob(os.path.join(root, ".github", "workflows", "*.yml")) + \
               glob.glob(os.path.join(root, ".github", "workflows", "*.yaml"))
    for p in existing:
        if os.path.basename(p) == "pii-scan.yml":
            continue
        try:
            if "pii_scan" in open(p, encoding="utf-8", errors="replace").read():
                return "CI already covered by an existing workflow"
        except OSError:
            continue

    dest_scan = os.path.join(root, "scripts", "pii_scan.py")
    os.makedirs(os.path.dirname(dest_scan), exist_ok=True)
    with open(scan, "rb") as s, open(dest_scan, "wb") as d:
        d.write(s.read())

    tpl = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "templates", "pii-scan.yml")
    body = open(tpl, encoding="utf-8").read()
    # Token replacement, NOT str.format: the template is full of GitHub Actions
    # ${{ … }} expressions, and format() would treat every one of them as a
    # field and fail.
    body = body.replace("__VIS__", vis).replace("__TIER__", tier)
    wf = os.path.join(root, ".github", "workflows", "pii-scan.yml")
    os.makedirs(os.path.dirname(wf), exist_ok=True)
    with open(wf, "w", encoding="utf-8", newline="\n") as f:
        f.write(body)
    return "CI installed (vendored scanner + .github/workflows/pii-scan.yml)"


def git_has_remote(root):
    r = sh(root, "remote")
    return bool((r.stdout or "").strip())


def install_all(base, scan, max_tier, extra_gate, with_ci=False):
    """Install into every git repo under `base`, resolving visibility per repo."""
    gh = find_gh()
    repos = git_repos(base)
    if not repos:
        # Never let an empty sweep read as success.
        print(f"NOTHING DONE — no git repositories found under {base}")
        return 1
    print(f"PII controls — installing into {len(repos)} repo(s) under {base}")
    print(f"  gh: {gh or 'NOT FOUND — visibility will be assumed public (stricter)'}\n")
    failures = []
    for root in repos:
        vis, how = repo_visibility(root, gh)
        name = os.path.basename(root)
        tier = existing_tier(root) or max_tier
        kept = "kept" if tier != max_tier else "default"
        for _ in install(root, scan.replace("\\", "/"), vis, tier, extra_gate):
            pass
        refreshed = refresh_vendored(root, scan)
        ci = install_ci(root, scan, vis, tier) if with_ci else None
        problems = verify(root, scan)
        status = "ok" if not problems else "FAILED"
        print(f"  {name:<24} {vis:<8} {tier} ({kept:<7}) {status:<7} ({how})")
        if refreshed:
            print(f"      {refreshed}")
        if ci:
            print(f"      {ci}")
        if problems:
            failures.append(f"{name}: {'; '.join(problems)}")
    print()
    if failures:
        print(f"  {len(failures)} repo(s) did not verify:")
        for f in failures:
            print(f"    {f}")
        return 1
    print(f"  all {len(repos)} repo(s) verified: both gates installed and executable")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("repo", nargs="?")
    ap.add_argument("--all", nargs="?", const="", metavar="DIR",
                    help="install into EVERY git repo under DIR "
                         "(default: the directory holding this checkout)")
    ap.add_argument("--visibility", choices=["public", "private"], default="private")
    ap.add_argument("--max-tier", choices=["P0", "P1", "P2", "P3"], default="P1")
    ap.add_argument("--scanner", default=None, help="path to pii_scan.py (default: alongside this)")
    ap.add_argument("--extra-gate", action="append", default=None,
                    help="repo-relative script to run as an extra commit gate "
                         "(repeatable; auto-detects known house gates if omitted)")
    ap.add_argument("--with-ci", action="store_true", dest="with_ci",
                    help="also vendor the scanner and install a CI workflow "
                         "(the hooks are --no-verify-bypassable; CI is the real gate)")
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args()

    scan_default = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pii_scan.py")

    if a.all is not None:
        base = os.path.abspath(a.all) if a.all else \
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        return install_all(base, os.path.abspath(a.scanner or scan_default),
                           a.max_tier, a.extra_gate, with_ci=a.with_ci)

    if not a.repo:
        ap.error("give a repo path, or --all to sweep every repo in the workspace")

    root = os.path.abspath(a.repo)
    if not os.path.isdir(os.path.join(root, ".git")):
        print(f"error: not a git repo: {root}", file=sys.stderr)
        return 2
    scan = os.path.abspath(a.scanner or os.path.join(os.path.dirname(os.path.abspath(__file__)), "pii_scan.py"))

    if a.verify:
        problems = verify(root, scan)
        print(f"PII controls — verify {root}")
        for p in problems:
            print(f"  MISSING  {p}")
        if not problems:
            print("  All controls present, installed, and executable.")
        return 1 if problems else 0

    print(f"PII controls — install into {root}  (visibility={a.visibility}, max-tier={a.max_tier})")
    for d in install(root, scan.replace("\\", "/"), a.visibility, a.max_tier, a.extra_gate):
        print(f"  {d}")
    problems = verify(root, scan)
    print("  ---")
    print("  verified: all controls active" if not problems
          else "  VERIFY FAILED: " + "; ".join(problems))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
