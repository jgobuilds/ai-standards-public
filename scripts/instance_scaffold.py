#!/usr/bin/env python3
"""Scaffold an organization's instance overlay, and refuse to call it done early.

Companion to the `instance-onboarding` skill. Writes the skeleton the interview
fills in, and `--check` fails while any `<!-- UNANSWERED -->` marker remains.

WHY THE MARKER IS THE POINT. A half-filled overlay is worse than an empty one: an
empty one is obviously not ready, and a half-filled one reads as configured. The
agent then builds against three answered sections and silently invents the rest —
which is exactly the "generic defaults are not neutral" failure the skill exists
to prevent. So the marker is machine-checkable, and the check is the gate.

    python scripts/instance_scaffold.py ../acme-instance
    python scripts/instance_scaffold.py ../acme-instance --check
    python scripts/instance_scaffold.py ../acme-instance --check --json

Never overwrites an answered file. Re-running is safe and is how you add a
section that did not exist when the overlay was first created.

Pure stdlib.
"""
from __future__ import annotations
import argparse, json, os, sys

MARK = "<!-- UNANSWERED -->"
# The header deliberately does NOT contain the marker it describes. The first
# version did, and every file then reported a phantom unanswered field on the
# header line — a checker that counts its own instructions is one whose count
# nobody trusts.
HDR = ("<!-- Instance overlay. Filled by the `instance-onboarding` skill.\n"
       "     Every field below is marked until answered; instance_scaffold.py\n"
       "     --check fails while any remain. Do not delete a mark you have not\n"
       "     answered — a half-filled overlay that reads as complete is worse\n"
       "     than an empty one. Date every answer and cite its source. -->\n\n")


def _s(title, *fields):
    """A section: a heading, then one marked line per field."""
    out = [f"## {title}", ""]
    for f in fields:
        out.append(f"- **{f}:** {MARK}")
    out.append("")
    return "\n".join(out)


FILES = {
"context/purpose.md": (
    "# Purpose\n\n" + HDR +
    "Why this organization exists and how it knows it is winning. Filled FIRST:\n"
    "it decides what is worth automating, and a fleet built without it runs\n"
    "beautifully while moving nothing anyone measures.\n\n"
    + _s("Goals (next 6–12 months, three at most)",
         "Goal 1 — what changes if it succeeds, what happens if it does not",
         "Goal 2", "Goal 3")
    + _s("Who we interact with",
         "Customers / users — who they are, what they buy, what they complain about",
         "Prospects — how they find us, what they evaluate on",
         "Partners / suppliers — what depends on them, what SLAs bind",
         "Regulators / auditors — what must be provable, to whom",
         "Internal consumers — which teams depend on our output",
         "Investors / board — what they are told, how often")
    + _s("How success is measured",
         "Outcome metrics — the numbers the business runs on, current values, where they live",
         "Driver metrics — what a team can move that feeds an outcome",
         "Health metrics — must not degrade while the others move",
         "Which of these could an agent plausibly move, and how would attribution be established")
    + _s("Explicitly out of scope",
         "What must stay human, and why (this is where the approval gates come from)")
),
"context/tech-stack.md": (
    "# Tech stack\n\n" + HDR +
    "Not a résumé of technologies — what an agent must not get wrong.\n\n"
    + _s("Repos and runtimes",
         "Repos, and what each is for",
         "Languages + versions, per repo",
         "Package manager and lockfile")
    + _s("How work is verified",
         "Test command", "Lint command", "Type check",
         "What gates a merge", "How CI is triggered")
    + _s("State and boundaries",
         "Datastores in use", "Datastores explicitly NOT allowed",
         "Deploy path, and who may trigger it",
         "Egress / firewall boundaries",
         "Vendored files that must stay byte-identical")
    + _s("Tacit knowledge (the highest-yield answers)",
         "What breaks most often, and the usual cause — seeds the known-cause table",
         "What a competent new engineer would get wrong in week one")
),
"context/org-design.md": (
    "# Org design\n\n" + HDR +
    "For routing, escalating and stopping — not for an org chart's sake.\n\n"
    + _s("Ownership", "Teams, and the SYSTEMS each owns (not titles)")
    + _s("Authority",
         "Irreversible acts, and who authorizes each (becomes the approval gate config)",
         "Spend limits, and who approves above them")
    + _s("Reaching a human",
         "Escalation path when an agent is stuck", "Expected response time",
         "Working hours and timezones")
    + _s("Timing", "Change windows", "Freezes, and how an agent learns of one")
    + _s("Memory", "Where decisions are recorded")
),
"context/proposed-fleet.md": (
    "# Proposed fleet\n\n" + HDR +
    "Derived from purpose.md, tech-stack.md and org-design.md — not from a\n"
    "catalogue of what agents can do. A proposal that does not trace to a goal\n"
    "and a metric is a demo.\n\n"
    "Selection rule: **value × verifiability**, and verifiability is the harder\n"
    "constraint. An agent whose output cannot be checked cannot be trusted to run\n"
    "unattended however valuable it would be — build the check first.\n\n"
    + _s("Candidate work (agent-shaped: repetitive, text/code-mediated, verifiable)",
         "Candidate 1 — goal it serves, metric it moves, how it would be verified",
         "Candidate 2", "Candidate 3",
         "Rejected candidates, and why (irreversible + undetectable failure, or unverifiable)")
    + _s("Agent 1 — the FIRST one to build",
         "Persona ({Name} the {Role})", "Goal it serves", "Metric it moves",
         "Verification — the check that says the output is CORRECT",
         "Autonomy rung (start at advisory)",
         "Gates it must stop at",
         "Failure mode, and who notices")
    + _s("Capabilities it needs",
         "Tools / integrations required",
         "For each: adopt, generate, or write? (build-vs-adopt order)",
         "Egress domains this adds, named deliberately",
         "Any capability that would send data to a third party (check against data-handling)")
    + _s("Knowledge resources it needs",
         "Domain vocabulary — what our words mean",
         "Known-cause table seed (from tech-stack)",
         "Worked examples of GOOD output",
         "Decision record location", "Who to ask, for what")
    + _s("Sequence",
         "What agent 1 will prove, and by when",
         "Agent 2 if agent 1 SUCCEEDS", "Agent 2 if agent 1 FAILS")
),
"context/data-handling.md": (
    "# Data handling\n\n" + HDR +
    "The one section that is not optional. Personal data in git history cannot\n"
    "be taken back, and a commit message is history too.\n\n"
    + _s("Classification", "Data classes present (P0–P3)",
         "Which repos may hold which class")
    + _s("Visibility", "Public repos", "Private repos",
         "Repos that must NEVER be published, and why")
    + _s("Protection", "Fields to tokenize", "Where the vault lives")
    + _s("Third parties", "Approved processors",
         "Is ANY external processor acceptable? (decides whether a hosted tracker can be used)")
    + _s("Retention", "What is deleted, when, and by what")
),
"lenses/README.md": (
    "# House lenses\n\n" + HDR +
    "The shared lenses in `ai-standards/references/` are the floor. Org-specific\n"
    "rules live here so they survive an engine upgrade.\n\n"
    "One file per lens, in the house shape — **risk → check → fix** — with a real\n"
    "failure named. A rule with no failure behind it gets argued with.\n\n"
    + _s("Inventory",
         "Lenses added here (list, with binding vs advisory marked)",
         "The review comment we make over and over (this is the next lens)")
),
}


def scaffold(root):
    made, kept = [], []
    for rel, body in FILES.items():
        p = os.path.join(root, *rel.split("/"))
        if os.path.exists(p):
            kept.append(rel)
            continue
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(body)
        made.append(rel)
    return made, kept


def unanswered(root):
    """{file: [line numbers]} for every remaining marker."""
    out = {}
    for rel in FILES:
        p = os.path.join(root, *rel.split("/"))
        if not os.path.exists(p):
            out[rel] = ["MISSING"]
            continue
        with open(p, encoding="utf-8", errors="replace") as fh:
            hits = [i for i, l in enumerate(fh, 1) if MARK in l]
        if hits:
            out[rel] = hits
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="Scaffold and check an instance overlay.")
    ap.add_argument("root", help="path to <org>-instance")
    ap.add_argument("--check", action="store_true", help="fail while anything is unanswered")
    ap.add_argument("--json", action="store_true", dest="as_json")
    a = ap.parse_args(argv)
    root = os.path.abspath(os.path.expanduser(a.root))

    if a.check:
        gaps = unanswered(root)
        total = sum(len(v) for v in gaps.values())
        if a.as_json:
            print(json.dumps({"root": root, "unanswered": gaps, "total": total}, indent=2))
        elif gaps:
            print(f"INSTANCE OVERLAY INCOMPLETE — {total} unanswered field(s):",
                  file=sys.stderr)
            for rel, lines in sorted(gaps.items()):
                where = "file missing" if lines == ["MISSING"] else \
                        f"lines {', '.join(str(l) for l in lines[:12])}" + \
                        (" …" if len(lines) > 12 else "")
                print(f"  {rel:34s} {where}", file=sys.stderr)
            print("\n  Run the `instance-onboarding` skill. Do not delete a marker\n"
                  "  you have not answered — an overlay that reads as complete and\n"
                  "  is not is the failure this check exists to prevent.",
                  file=sys.stderr)
        else:
            print("Instance overlay complete — every field answered. ✓")
        return 1 if gaps else 0

    if not os.path.isdir(root):
        os.makedirs(root, exist_ok=True)
    made, kept = scaffold(root)
    for rel in made:
        print(f"  created  {rel}")
    for rel in kept:
        print(f"  kept     {rel}  (already exists — never overwritten)")
    gaps = unanswered(root)
    print(f"\n{sum(len(v) for v in gaps.values())} field(s) to answer. "
          f"Run the `instance-onboarding` skill, then:\n"
          f"  python scripts/instance_scaffold.py {a.root} --check")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
