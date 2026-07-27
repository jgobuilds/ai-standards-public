---
name: instance-onboarding
description: >-
  Interview an organization and stand up its private instance overlay for the AI
  Control Plane — goals and how success is measured, who it serves, tech stack,
  org design, house lenses, data posture, brand — then propose the starting
  fleet: which agents to build first, what capabilities they need, and what
  knowledge resources to create. Use when setting up a NEW instance ("onboard
  us", "set up a new instance", "configure the control plane for my company",
  "what agents should we build first"), when an existing overlay is incomplete
  or stale, or when someone wants to feed existing documentation (an engineering
  handbook, an architecture doc, a style guide, an org chart) into the standards
  so agents actually follow it. Owns `<org>-instance/context/`. Run it before
  the first real agent task, and re-run the affected section whenever the goals,
  the stack, or the org change.
---

# Onboard an organization

The engine ships brand-neutral and assumption-free. Everything specific to *this*
organization lives in a private overlay at `../<org>-instance`. This skill fills
that overlay by interview, then uses it to propose a starting fleet.

**The failure this prevents:** an agent that builds competently for a company
that isn't yours. It picks Postgres because Postgres is common, writes a React
component into a Vue codebase, opens a PR against a branch nobody uses — none of
it wrong in general, all of it wrong here. Generic defaults are not neutral.

**And the bigger one:** a fleet of agents that runs beautifully and moves nothing
the business measures. Sections 2 and 8 exist for that, and they are why the
interview starts with purpose rather than with the stack.

## Before you start

```bash
python scripts/instance_scaffold.py ../<org>-instance
```

Writes the skeleton with every unanswered field marked `<!-- UNANSWERED -->`;
`--check` fails while any remain. **Do not delete a marker you have not
answered** — a half-filled overlay that reads as complete is worse than an empty
one, because nobody returns to it.

## The rule for every answer

**Record what is true, not what would be nice.** If there are three deploy paths
and one is documented, write three. If a rule is aspirational, mark it
`aspiration` — an agent that treats a wish as a constraint will block on it.

**Cite where each answer came from** — a repo, a doc, a person, a date. Six
months on, the only question that matters about a stale answer is *how would we
know?*, and a source answers it.

## 1. Feed in what already exists — before asking anything

Most organizations have written much of this down. Questions you can answer from
a document are questions you should not ask.

Ask for, and read: engineering handbook, main README, ADRs/RFCs, architecture
docs, runbooks, on-call docs, coding standards, linter configs, security and
data-handling policy, processor list, org chart, team charters, strategy deck,
OKRs, the board or investor update, the pricing page.

Extract into the overlay and **link back to the source** rather than copying
wholesale. A copy drifts; a pointer plus a summary does not.

> If a document contradicts the interview, surface the conflict rather than
> picking. *"The handbook says trunk-based; you said release branches — which is
> true today?"* A contradiction is usually a stale doc, and finding it is worth
> more than either answer.

## 2. Purpose — `context/purpose.md`

This comes first because it decides what is worth automating. Skip it and you
get a technically excellent fleet pointed at the wrong work.

**Goals.** What is the organization trying to achieve in the next 6–12 months?
Three at most; if everything is a goal, nothing is. For each: what changes if it
succeeds, and what happens if it does not.

**Who it interacts with.** Not just customers — every party whose expectations
constrain the work:

| Party | What an agent needs to know |
|---|---|
| Customers / users | who they are, what they buy, what they complain about |
| Prospects | how they find you and what they evaluate on |
| Partners / suppliers | what depends on them, what SLAs bind |
| Regulators / auditors | what must be provable, and to whom |
| Internal consumers | which teams depend on this team's output |
| Investors / board | what they are told, how often |

**How success is measured.** The actual numbers, with their current values and
where they live. Distinguish:

- **outcome metrics** — revenue, retention, margin. What the business runs on.
- **driver metrics** — the things a team can move that feed an outcome.
- **health metrics** — must not degrade while you move the others.

Then the question that makes this operational: **which of these could an agent
plausibly move, and how would you know it did?** A metric nobody can attribute is
a metric no agent should be pointed at — you will not be able to tell success
from coincidence.

**What is explicitly out of scope.** The things that must stay human, and why.
This is as load-bearing as the goals; it is where the approval gates come from.

## 3. Tech stack — `context/tech-stack.md`

Not a résumé of technologies. **What an agent must not get wrong.**

| Ask | Because an agent will otherwise |
|---|---|
| Languages + versions, per repo | write 3.12 syntax into a 3.9 runtime |
| Package manager and lockfile | add a dep the other tool cannot see |
| Test, lint, and type-check commands | "run the tests" and run nothing |
| How CI triggers, and what gates merge | open a PR that cannot pass |
| Datastores — and which are **not** allowed | reach for Redis in a stack with no cache tier |
| Deploy path, and who may trigger it | assume a merge ships |
| Egress and firewall boundaries | design something that cannot make its calls |
| What is **vendored** and must stay byte-identical | let a formatter rewrite it, forever |

Two questions that repay themselves:

- **"What breaks most often, and what is the usual cause?"** Seeds the
  known-cause table; the second occurrence is then free.
- **"What would a competent new engineer get wrong in week one?"** The highest-
  yield question in the interview. It surfaces the tacit rules nobody wrote down,
  which are exactly the ones an agent breaks.

## 4. Org design — `context/org-design.md`

For routing, escalating and stopping — not for an org chart's sake.

- **Teams, and what each owns.** Ownership by *system*, not by title.
- **Who approves what.** Name the irreversible acts — deploys, schema changes,
  spend, anything customer-visible — and who authorizes each. This becomes the
  approval gate's config, so vagueness here becomes a gate that blocks everything
  or nothing.
- **Escalation path when an agent is stuck**, and expected response time.
  Without it, `ask_human` has nowhere to go.
- **Working hours and timezones.** A blocking question at 02:00 local has stalled
  until morning; a digest is the right tier instead.
- **Change windows and freezes.** A freeze an agent does not know about is a
  freeze it violates.
- **Where decisions are recorded**, so an agent can find the *why* before
  proposing to undo it.

## 5. House lenses — `lenses/`

The shared lenses in `ai-standards/references/` are the floor. An org adds its
own, and they live in the overlay so they survive an engine upgrade.

Ask: **what review comment do you make over and over?** That is a lens. Write it
in the house shape — *risk → check → fix* — with a real failure named, because a
rule with no failure behind it gets argued with.

State plainly which lenses are **binding** and which are advisory. An agent
cannot tell from tone.

## 6. Data handling — the one section that is not optional

- Data classes present (P0–P3), and which repos may hold which
- Which repos are public, private, or **must never be published**, and why
- Fields to tokenize, and where the vault lives
- Approved third-party processors — and whether *any* external processor is
  acceptable, which decides whether a hosted tracker can be used at all
- Retention: what is deleted, when, by what

**Get this before the first agent runs.** Personal data in git history cannot be
taken back, and a commit message is history too.

## 7. Brand — `brand/`

Only if the org produces human-facing output. Tokens, not hex values, so a
rebrand is one file. Neutral fallbacks ship with the engine, so this is the one
section safe to defer.

## 8. Propose the starting fleet — `context/proposed-fleet.md`

Now use sections 2–6 rather than a catalogue of what agents can do. **A proposal
that does not trace to a goal and a metric is a demo.**

### Choose candidates by value × verifiability

For each goal, list the work that moves it, then keep only the work that is
**agent-shaped**:

- **repetitive** — it happens often enough that a fixed cost pays back
- **text- or code-mediated** — the whole job lives in artifacts a model can read
  and write
- **verifiable** — there is a check that says *done correctly*, not just *done*

Score each candidate on **value** (from §2's metrics) and **verifiability**, and
start where both are high. This ordering is not a preference:

> **An agent whose output cannot be checked cannot be trusted to run unattended,
> however valuable it would be.** High value with no verification is the *last*
> thing to automate, not the first — it is the one that fails silently and
> expensively. Build the check first, then the agent.

Two more filters, both learned the hard way:

- **Reject work whose failure is irreversible and undetectable.** Sending, paying,
  publishing, deleting. These get gates, not autonomy.
- **Prefer narrow and complete over broad and partial.** One agent that fully owns
  a small loop beats five that each do part of a big one, because partial
  ownership is where handoffs and ambiguity live.

### For each proposed agent, write

| Field | Why |
|---|---|
| **Persona** | `{Name} the {Role}` per `naming-standard.md` — a stable identity across notifications, tickets and the ledger |
| **Goal it serves** | traced to §2, by name |
| **Metric it moves** | and how attribution will be established |
| **Verification** | the check that says the output is correct. If you cannot name one, the agent is not ready |
| **Autonomy rung** | advisory → gated → autonomous. Start at advisory; autonomy is earned by a verification record, not granted at design time |
| **Gates** | which irreversible acts it must stop at, from §4 |
| **Failure mode** | what it does wrong when it goes wrong, and who notices |

### Capabilities — what it needs to reach

For each agent, the tools and integrations it needs, and for each: **does it
already exist?** Adopt, then generate, then write — in that order
(`build-vs-adopt.md`, `build-mcp-server`). Every new capability is an explicit
egress decision: name the domain it must reach and add it deliberately, because
a capability is also a blast radius.

Flag any capability that would send data to a third party against §6. That is
the check that stops a convenient tool from quietly becoming an unapproved
processor.

### Knowledge resources — what it needs to know

Most first-agent failures are missing knowledge, not missing capability. For each
agent, list what it must know that is not in the code, and where that will live —
per `knowledge-for-agents.md`: Markdown as source of truth, stable IDs, a
generated index and catalog, `last_verified` on every atom.

Common gaps, in rough order of how often they bite:

1. **Domain vocabulary** — what the org's words mean, which are never what a
   general model assumes
2. **The known-cause table** — seeded from §3's "what breaks most often"
3. **Worked examples of good output** — one real example teaches more than a page
   of description
4. **The decision record** — so an agent finds the *why* before proposing to
   undo it
5. **Who to ask, for what** — from §4

### Sequence it

Recommend **one** first agent, not a fleet. Say what it will prove, how long
until that is known, and what the second one becomes if the first succeeds — and
if it fails. A roadmap that only branches on success is a plan for a world that
does not exist.

## Finish

```bash
python scripts/instance_scaffold.py ../<org>-instance --check
```

Green means every marker is answered. Then:

1. Commit the overlay to a **private** repo. It holds org detail the engine
   deliberately does not.
2. Build the first proposed agent and run one real task end to end. **The
   interview is a hypothesis; the first task is the test.** Fix the overlay, not
   the agent.
3. Re-run the affected section when goals, stack, org or rules change. Date every
   answer so staleness is visible rather than assumed.

## What good looks like

An agent picks up a ticket and, without being told: uses the right test command,
respects the freeze, routes the approval to the right person, renders in the
house palette, stops at the boundary the security policy draws — and the work it
did shows up in a number someone already cared about. None of that is
intelligence. All of it is this overlay.
