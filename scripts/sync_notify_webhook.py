#!/usr/bin/env python3
r"""Sync one notification webhook to the fleet's GitHub secrets (and optionally .env).

WHY THIS EXISTS. GitHub Actions secrets are **write-only** — nothing can read a
secret's value back (GitHub only decrypts it into the ephemeral runner at workflow
time). So the same webhook must ALSO live wherever a non-CI consumer reads it
(typically a `.env`). Two copies are unavoidable; the risk is they drift. This
tool makes ONE place authoritative and fans the value out, so entering or
rotating the webhook is a single command, not N hand-edits across repos.

WHICH REPOS. There is no built-in fleet list — this file is a shared SOURCE and
must not name anyone's repositories. Pass `--repos`, or set SYNC_NOTIFY_REPOS
(comma-separated) and SYNC_NOTIFY_OWNER once in your shell profile.

    # Propagate the value already in a .env to every repo's GitHub secret:
    python scripts/sync_notify_webhook.py --owner ACME --repos api,web,infra \
        --env-file ../someproject/.env

    # Rotate: set a NEW value everywhere (updates the .env too) in one shot:
    python scripts/sync_notify_webhook.py --owner ACME --repos api,web \
        --value "https://hooks.slack.com/services/..." --env-file ../someproject/.env

It never prints the secret — only a short fingerprint (sha256 prefix + length), so
you can confirm the SAME value landed everywhere without exposing it. Requires the
gh CLI, authenticated.

SCALE NOTE. This is deliberate house glue for ONE shared secret. As the number of
shared secrets grows, replace it with a real secrets manager that BOTH CI and n8n
read at runtime (e.g. GCP Secret Manager, which fits the control plane's GCP orbit) —
that removes the duplication entirely instead of syncing it. Worth an ADR in the
consuming repo; revisit past ~3 shared secrets or the first cross-machine deploy.

Pure stdlib. Windows-friendly.
"""
import sys, os, re, argparse, hashlib, subprocess, shutil

# No fleet is hardcoded. This repo is a shared source; a list of someone's
# repositories baked into it is both wrong for every other user and a leak of
# private repo names if this ever ships publicly. Supply them per invocation, or
# once via the environment.
DEFAULT_OWNER = os.environ.get("SYNC_NOTIFY_OWNER", "")
DEFAULT_REPOS = [r for r in os.environ.get("SYNC_NOTIFY_REPOS", "").split(",") if r.strip()]
DEFAULT_SECRET = "SLACK_WEBHOOK_URL"


def find_gh():
    """gh is often off-PATH on Windows. Prefer PATH, fall back to the known install."""
    p = shutil.which("gh")
    if p:
        return p
    for c in (r"C:\Program Files\GitHub CLI\gh.exe",
              r"C:\Program Files (x86)\GitHub CLI\gh.exe"):
        if os.path.exists(c):
            return c
    return None


def fingerprint(value):
    """A non-reversible tag so you can confirm the same value everywhere without
    ever printing it."""
    return f"sha256:{hashlib.sha256(value.encode()).hexdigest()[:8]} len={len(value)}"


def read_env_value(path, key):
    with open(path, encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if s.startswith("#") or "=" not in s:
                continue
            k, _, v = s.partition("=")
            if k.strip() == key:
                return v.strip()
    return None


def write_env_value(path, key, value):
    """Replace (or append) KEY=value in a .env, preserving everything else. The
    file holds secrets and is gitignored — we edit in place, never echo it."""
    lines = open(path, encoding="utf-8").read().splitlines()
    pat = re.compile(rf"^{re.escape(key)}=")
    out, replaced = [], False
    for line in lines:
        if pat.match(line):
            out.append(f"{key}={value}"); replaced = True
        else:
            out.append(line)
    if not replaced:
        out.append(f"{key}={value}")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(out) + "\n")
    return replaced


def gh_set(gh, owner, repo, name, value):
    # --body would place the secret in argv (visible in the process list); pipe it
    # on stdin instead so it never appears there. gh reads stdin when --body is
    # omitted. (A secrets manager avoids even this — see the SCALE NOTE.)
    r = subprocess.run([gh, "secret", "set", name, "--repo", f"{owner}/{repo}"],
                       input=value, text=True, capture_output=True)
    return r.returncode == 0, (r.stderr.strip() or r.stdout.strip() or "ok")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Fan a notify webhook out to the fleet's GitHub secrets.")
    ap.add_argument("--secret", default=DEFAULT_SECRET, help=f"secret name (default {DEFAULT_SECRET})")
    ap.add_argument("--value", default=None, help="the webhook value; if omitted, read from --env-file")
    ap.add_argument("--env-file", default=None, help="a .env to read the value from and/or write it into")
    ap.add_argument("--owner", default=DEFAULT_OWNER,
                    help="GitHub owner/org (or set SYNC_NOTIFY_OWNER)")
    ap.add_argument("--repos", default=",".join(DEFAULT_REPOS),
                    help="comma-separated repo names (or set SYNC_NOTIFY_REPOS)")
    ap.add_argument("--dry-run", action="store_true", help="show the plan; touch nothing")
    args = ap.parse_args(argv)

    repos = [r.strip() for r in args.repos.split(",") if r.strip()]
    # Refuse rather than default. A silent empty fleet would print "Synced to 0
    # repo(s)" and exit 0 — the operator would believe a secret ROTATION landed
    # when nothing was written anywhere, which is the worst possible outcome for
    # this particular tool.
    if not args.owner or not repos:
        print("error: no fleet to sync to. Pass --owner and --repos, or set "
              "SYNC_NOTIFY_OWNER and SYNC_NOTIFY_REPOS.\n"
              "       This file is a shared source and deliberately hardcodes "
              "nobody's repositories.", file=sys.stderr)
        return 2

    # Resolve the value: explicit --value wins; else read it from the .env.
    value = args.value
    if value is None:
        if not args.env_file or not os.path.exists(args.env_file):
            print("error: no --value and no readable --env-file to read it from", file=sys.stderr)
            return 2
        value = read_env_value(args.env_file, args.secret)
        if not value:
            print(f"error: {args.secret} not set (or empty) in {args.env_file}", file=sys.stderr)
            return 2

    print(f"{args.secret}  {fingerprint(value)}")
    print(f"repos: {', '.join(f'{args.owner}/{r}' for r in repos)}")
    if args.env_file:
        print(f"env-file: {args.env_file}")

    if args.dry_run:
        print("\n[dry-run] would set the GitHub secret on each repo above"
              + (" and write the value into the env-file" if (args.value and args.env_file) else "")
              + "; nothing changed.")
        return 0

    gh = find_gh()
    if not gh:
        print("error: gh CLI not found (PATH or the standard Windows install path)", file=sys.stderr)
        return 3

    # If a NEW value was passed explicitly, keep the .env in step too.
    if args.value and args.env_file and os.path.exists(args.env_file):
        write_env_value(args.env_file, args.secret, value)
        print(f"  wrote {args.secret} into {args.env_file}")

    failures = 0
    for r in repos:
        ok, detail = gh_set(gh, args.owner, r, args.secret, value)
        print(f"  {'ok  ' if ok else 'FAIL'}  {args.owner}/{r}" + ("" if ok else f"  — {detail}"))
        failures += (0 if ok else 1)

    if failures:
        print(f"\n{failures} repo(s) failed — re-run after fixing (gh auth, repo access).", file=sys.stderr)
        return 1
    print(f"\nSynced to {len(repos)} repo(s). Any NON-CI consumer that already "
          f"read the old value — a running container, a daemon — still holds it "
          f"in memory. Restart it, or the rotation is only half done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
