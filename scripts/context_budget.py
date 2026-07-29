#!/usr/bin/env python3
r"""Context budget — measure what an agent actually has to hold, and gate it.

WHY THIS EXISTS. workspace_doctor already budgets INDIVIDUAL instruction files
(200 lines for a CLAUDE.md, 500 for a skill). That is necessary and not
sufficient: every file can pass its own budget while the SUM quietly grows past
what an agent can use well. Measured 2026-07-25 across this fleet: 13 review
lenses at ~87,000 chars, added four at a time over a single session, with nothing
watching the total. Per-file budgets cannot see that; only an aggregate can.

TWO BUDGETS, because they are paid at different times:

  ALWAYS-LOADED — the ancestor CLAUDE.md chain, the repo's own CLAUDE.md, and
    anything they @import. Paid on EVERY session, every turn. The expensive one.
  ON-DEMAND — the review lenses named in .engineering-standard/config.yml. Paid
    only when a review runs, but 13 lenses at once is a real load.

Conflating them produces the wrong advice: a large lens set is fine, a large
always-loaded set is not.

MEASURED IN CHARACTERS, not lines. Lines are a poor proxy — 200 lines of terse
bullets and 200 lines of dense prose differ by 3-4x. Characters are deterministic
and need no tokenizer; the token figures shown are a rough chars/4 estimate and
are labelled as such.

    python scripts/context_budget.py <repo>          # human report
    python scripts/context_budget.py <repo> --json    # machine-readable
    python scripts/context_budget.py <repo> --strict  # WARN also fails

Exit 1 on FAIL (over the hard band). Pure stdlib.
"""
from __future__ import annotations
import os, re, sys, json, argparse

# Targets in CHARACTERS. Bands rather than a cliff: a check that flips to FAIL on
# a 2% overshoot gets weakened rather than obeyed.
ALWAYS_TARGET = 12_000       # ~3k tokens of per-session tax
LENS_TARGET   = 90_000       # ~22k tokens if a review loads every lens
WARN_RATIO    = 1.00         # at/over target -> WARN
FAIL_RATIO    = 1.20         # 20% over target -> FAIL

SPLIT_OVER    = 10_000       # a single file this large is a split candidate
MERGE_UNDER   = 500          # a non-trivial file this small rarely earns its slot

IMPORT_RE = re.compile(r"^@(\S+)")


def measure(path):
    try:
        t = open(path, encoding="utf-8", errors="replace").read()
    except OSError:
        return None
    return {"path": path, "chars": len(t),
            "lines": len([l for l in t.splitlines() if l.strip()]), "text": t}


def always_loaded(repo, stop_at=None):
    """Instruction files loaded on EVERY session, walking the ancestor chain.

    An ancestor CLAUDE.md loads into every repo beneath it, which is exactly why
    it is easy to forget: the cost is paid by projects that never mention it.
    """
    files, seen = [], set()
    stop_at = os.path.abspath(stop_at) if stop_at else os.path.abspath(os.path.join(repo, ".."))
    d = os.path.abspath(repo)
    chain = []
    while True:
        chain.append(d)
        if os.path.abspath(d) == stop_at or os.path.dirname(d) == d:
            break
        d = os.path.dirname(d)
    for d in reversed(chain):                      # outermost first: it loads first
        for name in ("CLAUDE.md", "AGENTS.md"):
            p = os.path.join(d, name)
            if os.path.isfile(p) and p not in seen:
                m = measure(p)
                if not m:
                    continue
                seen.add(p)
                files.append(m)
                # follow @imports — they are part of the always-loaded cost
                for line in m["text"].splitlines():
                    im = IMPORT_RE.match(line.strip())
                    if im:
                        ip = os.path.normpath(os.path.join(d, im.group(1)))
                        if os.path.isfile(ip) and ip not in seen:
                            m2 = measure(ip)
                            if m2:
                                seen.add(ip)
                                m2["via"] = f"@import from {name}"
                                files.append(m2)
    return files


def lens_files(repo):
    """The review lenses this repo actually enables — not every file on disk."""
    cfg = os.path.join(repo, ".engineering-standard", "config.yml")
    if not os.path.isfile(cfg):
        return [], None
    text = open(cfg, encoding="utf-8").read()
    overlay = None
    mo = re.search(r"^overlay:\s*(\S+)", text, re.M)
    if mo:
        overlay = os.path.normpath(os.path.join(repo, mo.group(1)))
    ml = re.search(r"lenses:\s*\[(.*?)\]", text, re.S)
    names = [n.strip() for n in ml.group(1).replace("\n", " ").split(",")] if ml else []
    out, external = [], []
    for n in [n for n in names if n]:
        p = os.path.join(overlay, "references", f"{n}.md") if overlay else None
        if p and os.path.isfile(p):
            m = measure(p)
            if m:
                m["lens"] = n
                out.append(m)
        else:
            # Base-skill lenses ship with the review skill, not this overlay. They
            # still cost context; we just cannot measure them from here, and
            # silently dropping them would understate the real total.
            external.append(n)
    return out, overlay, external


def band(total, target):
    if total >= target * FAIL_RATIO:
        return "FAIL"
    if total >= target * WARN_RATIO:
        return "WARN"
    return "ok"


def report(repo, strict=False, as_json=False):
    always = always_loaded(repo)
    lenses, overlay, external = lens_files(repo)
    a_tot = sum(f["chars"] for f in always)
    l_tot = sum(f["chars"] for f in lenses)
    a_band, l_band = band(a_tot, ALWAYS_TARGET), band(l_tot, LENS_TARGET)

    splits = [f for f in always + lenses if f["chars"] > SPLIT_OVER]
    merges = [f for f in lenses if f["chars"] < MERGE_UNDER]

    if as_json:
        print(json.dumps({
            "repo": os.path.abspath(repo),
            "always_loaded": {"chars": a_tot, "target": ALWAYS_TARGET, "band": a_band,
                              "files": [{"path": f["path"], "chars": f["chars"]} for f in always]},
            "lenses": {"chars": l_tot, "target": LENS_TARGET, "band": l_band, "count": len(lenses),
                       "unmeasured_base_skill_lenses": external,
                       "files": [{"lens": f.get("lens"), "chars": f["chars"]} for f in lenses]},
            "split_candidates": [f["path"] for f in splits],
            "merge_candidates": [f["path"] for f in merges],
        }, indent=2))
    else:
        rel = lambda p: os.path.relpath(p, os.path.dirname(os.path.abspath(repo)))
        print(f"Context budget — {os.path.abspath(repo)}\n")
        print(f"ALWAYS-LOADED (every session)   {a_tot:>7,} / {ALWAYS_TARGET:,} chars  "
              f"(~{a_tot//4:,} tok)  [{a_band}]")
        for f in always:
            via = f"  ({f['via']})" if f.get("via") else ""
            print(f"    {f['chars']:>7,}  {rel(f['path'])}{via}")
        named = len(lenses) + len(external)
        print(f"\nON-DEMAND lenses ({len(lenses)} of {named})      {l_tot:>7,} / {LENS_TARGET:,} chars  "
              f"(~{l_tot//4:,} tok)  [{l_band}]")
        for f in sorted(lenses, key=lambda x: -x["chars"])[:5]:
            print(f"    {f['chars']:>7,}  {f['lens']}")
        if len(lenses) > 5:
            print(f"    {'':>7}  … {len(lenses)-5} more")
        if external:
            print(f"    {'':>7}  NOT MEASURED (ship with the base skill, cost is real "
                  f"but not ours to see): {', '.join(external)}")
        if splits:
            print("\n  SPLIT candidates (single file over "
                  f"{SPLIT_OVER:,} chars — push depth into a reference):")
            for f in splits:
                print(f"    {f['chars']:>7,}  {rel(f['path'])}")
        if merges:
            print(f"\n  MERGE candidates (under {MERGE_UNDER:,} chars — rarely earns a slot):")
            for f in merges:
                print(f"    {f['chars']:>7,}  {f.get('lens') or rel(f['path'])}")
        print()
        if a_band == "ok" and l_band == "ok":
            print("Within budget.")
        else:
            print("Over target. The aggregate is the number that matters — every file "
                  "can pass\nits own budget while the sum grows past what an agent uses well.")

    hard = ("FAIL" in (a_band, l_band)) or (strict and "WARN" in (a_band, l_band))
    return 1 if hard else 0


def main():
    ap = argparse.ArgumentParser(description="Measure and gate aggregate agent context.")
    ap.add_argument("repo", nargs="?", default=".")
    ap.add_argument("--json", action="store_true", dest="as_json")
    ap.add_argument("--strict", action="store_true", help="treat WARN as failure")
    a = ap.parse_args()
    return report(a.repo, strict=a.strict, as_json=a.as_json)


if __name__ == "__main__":
    sys.exit(main())
