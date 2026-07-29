#!/usr/bin/env python3
r"""platform_cmd.py — render a shell command for Windows or POSIX, and wrap
Linux-only commands (Docker, containers, WSL) so they run from a Windows shell.

WHY. This fleet runs on Windows/PowerShell, but its Docker engine lives inside
WSL. Host commands run natively; anything touching Docker/Linux has to go through
`wsl -e bash -lc '…'`. Doing that wrap by hand is error-prone — PowerShell expands
`$` and mangles `"` inside double quotes — so this centralizes the one correct
form and keeps run-hints in scripts/docs consistent.

Two command KINDS:
  - "host"  — runs natively on the host shell (PowerShell on Windows, sh on POSIX).
  - "linux" — must run in a Linux/WSL context (Docker, bash); on Windows it is
              wrapped in `wsl -e bash -lc '…'`, on POSIX it runs unchanged.

    from platform_cmd import render, wsl_wrap, wsl_argv, render_options
    render("docker compose up -d n8n", kind="linux")   # wsl-wrapped on Windows
    wsl_argv("docker compose up -d n8n")               # argv list, quote-safe, to EXECUTE
    render_options("python foo.py", kind="host")       # {'Windows (PowerShell)':…, 'Linux / macOS':…}

CLI (handy when writing docs):
    python platform_cmd.py --linux "cd /app && docker compose up -d n8n"
    python platform_cmd.py --host  "python scripts\foo.py --flag" --both

The wrap uses a SINGLE-quoted PowerShell string on purpose: single quotes stop
PowerShell expanding `$vars` and choking on embedded `"`, both common in shell
commands. The only thing to escape is a literal `'` (doubled, per PowerShell).
Targets PowerShell (this fleet's shell), not cmd.exe. Host path separators are
NOT translated — a "host" command is shown as written. Pure stdlib.
"""
import os, sys, argparse

IS_WINDOWS = os.name == "nt"


def _ps_single_quote(s):
    """Escape for a PowerShell single-quoted literal: ' -> ''."""
    return s.replace("'", "''")


def wsl_wrap(linux_cmd):
    r"""Wrap a Linux shell command to run from Windows PowerShell via WSL.

        wsl_wrap("cd /app && docker compose up -d n8n")
        -> wsl -e bash -lc 'cd /app && docker compose up -d n8n'

    Single-quoted so `$VAR` and `"…"` inside the command survive to bash intact.
    """
    return f"wsl -e bash -lc '{_ps_single_quote(linux_cmd)}'"


def wsl_argv(linux_cmd):
    """The same wrap as an argv list for subprocess — NO quoting layer, so it is
    safe for ANY command (embedded quotes, `$`, …). Prefer this to EXECUTE from
    Python; use wsl_wrap only to DISPLAY a copy-pasteable line."""
    return ["wsl", "-e", "bash", "-lc", linux_cmd]


def render(cmd, *, kind="host", windows=None):
    """Render `cmd` for the target platform.

    kind="host"  -> unchanged (already native to the target shell).
    kind="linux" -> wrapped for WSL when targeting Windows; unchanged on POSIX.
    windows: force the target (True/False); default = detect the current OS.
    """
    win = IS_WINDOWS if windows is None else windows
    if kind == "host":
        return cmd
    if kind == "linux":
        return wsl_wrap(cmd) if win else cmd
    raise ValueError(f"kind must be 'host' or 'linux', got {kind!r}")


def render_options(cmd, *, kind="host"):
    """Both platform renderings, labeled — for showing a command two ways in docs."""
    return {
        "Windows (PowerShell)": render(cmd, kind=kind, windows=True),
        "Linux / macOS": render(cmd, kind=kind, windows=False),
    }


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Render a command for Windows/POSIX; wrap Linux commands to run on Windows.")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--host", metavar="CMD", help="a host command (runs natively)")
    g.add_argument("--linux", metavar="CMD", help="a Linux/Docker command (wrapped for Windows)")
    ap.add_argument("--both", action="store_true", help="print both platform forms, labeled")
    args = ap.parse_args(argv)

    cmd = args.host if args.host is not None else args.linux
    kind = "host" if args.host is not None else "linux"
    if args.both:
        for label, form in render_options(cmd, kind=kind).items():
            print(f"# {label}\n{form}")
    else:
        print(render(cmd, kind=kind))
    return 0


if __name__ == "__main__":
    sys.exit(main())
