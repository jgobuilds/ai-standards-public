# Ticketing — durable state an agent can write and a human can browse

The third tier of `notification-taxonomy`. That lens covers **interrupt**
(an alert) and **on-demand** (a report you go and read). Neither answers *"what
is currently open, and who is on it?"* — which is the question that actually
scales when several agents are working.

## Adopt, don't build — and that includes the wiki

Two decisions, both in the direction of less software.

**Use the tracker you already have.** For a team already on GitHub, that is
**GitHub Issues**: the agents already have `gh` authenticated, commits and CI
comments already reference issues natively, and it costs no new service, no new
auth, and no new thing to keep running. Linear and Jira are better products for
a large team with process to enforce; neither is worth adding for a fleet whose
agents already hold a GitHub token.

**Do not add a wiki.** A wiki that consumes your Markdown is a *second copy* of
knowledge that already lives in git — the drift failure `generated-artifacts.md`
exists to prevent. If browsing is the problem, generate a navigational map from
the source (`knowledge-for-agents.md`), and let the tracker hold *state* rather
than *content*. Content in git, state in the tracker, alerts in chat: three
tiers, no overlap.

## The seam, and why there is one at all

`scripts/ticket.py` is four verbs — `open`, `note`, `close`, `list` — over a
backend chosen by `TICKET_BACKEND`.

The abstraction is deliberately thin, and it is not there to wrap a tracker's
feature set. It is there because **"which tracker" is exactly the decision that
becomes irreversible by accident**: inline `gh issue create` into every lane,
hook and workflow, and switching later means editing all of them. Four verbs
behind one seam keeps that one decision cheap to revisit.

| Backend | For |
|---|---|
| `github` | the default — GitHub Issues via `gh` |
| `file` | newline-delimited JSON on disk: offline, tests, air-gapped |
| `none` | explicitly off — and it says so on every call |

Adding one (Linear, Jira, a webhook) means writing four methods and registering
the class. It does not mean touching a single caller.

The `file` backend is not a toy. **A seam with one implementation is an
assumption, not a seam** — it is what proves the abstraction holds, and it is
what runs when the tracker is unreachable.

## Idempotency is the entire point

Every ticket carries `<!-- ticket-key: KEY -->` in its body, and `open` with an
existing key **edits in place**. Without that:

- an agent re-runs → a second ticket
- a nightly lane fires → thirty tickets a month
- a flaky job fails five times → five tickets

and a tracker full of duplicates gets ignored, in exactly the way a noisy alert
channel does. Pick keys that name the *condition*, not the occurrence:
`ci/<workflow>/unrecognised-failure`, not `ci/run-30219038087`.

Re-filing a **closed** ticket reopens it rather than starting a new one. Someone
closed it for a reason, and that reason is in the thread.

## Two failure modes it is built against

**Silent downgrade.** If the chosen backend is unavailable, `ticket.py` refuses
— it does not quietly fall back to another. A fallback means an agent reports
"filed" while the ticket landed somewhere nobody reads.

**Silent off.** The `none` backend prints to stderr on every call. Turning
ticketing off is a legitimate choice; doing it invisibly, so every agent believes
it filed something, is not.

## What to file, and what not to

File when there is **state that outlives the run**: an unrecognised CI failure,
a flaky test, a decision waiting on a human, a promoted-but-unfixed cause.

Do not file for anything the alert already resolves. A known CI failure with a
confirmed fix does not need a ticket — it needs the fix. A ticket per red build
is the duplicate problem wearing a different hat.
