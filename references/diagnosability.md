# Diagnosability (house lens)

A lens for building systems an agent can **self-diagnose and resolve** — not the
change process (that is `change-safety.md`), but the property that makes a
failure *legible* to whoever debugs it next, which is increasingly an agent
running unattended.

The governing fact: **an agent can only fix what it can see.** Every item below
was written after a real session where the agent was blind and therefore
*guessed*. Most come from one site-planning tool that pulled coordinates,
parcel geometry and sun data from several external sources: diagnosis there kept
waiting on a human to send a screenshot, because the system recorded nothing an
agent could read. The examples below are from that codebase; the failures are
not specific to it.

Each item: the risk, what to check, the fix.

## Log the inputs that decided the outcome, not just the outcome

- **Risk:** "it failed" is not diagnosable. A real instance: a lookup pipeline
  logged success/failure but not *which source* broke or *why*, so the agent
  admitted "I have been guessing at which source fails because I could not see
  your lookups." Every debugging step needed a human screenshot.
- **Check:** when this fails, does the record contain the facts that *determined*
  the result — the branch conditions, the booleans, each dependency's status —
  or only the verdict? Could an agent reconstruct *why* from the log alone,
  without asking a human?
- **Fix:** log the deciding inputs. That tool's fix records, per attempt,
  the three booleans that decide the outcome (`got_coordinate`, `got_parcel`,
  `got_sun`) plus every source's status, timing, and error — one structured
  line (`lookups.jsonl`) per attempt. Now "which source failed for THIS input"
  is answerable from the file.

## Make the record machine-parseable, one line per attempt

- **Risk:** prose logs buried in a stream can be read by a human scrolling, but
  not diffed, counted, or parsed by an agent. And a single summarized line hides
  whether a failure is chronic or a one-off.
- **Check:** is the diagnostic record structured (JSONL / key-value) and keyed so
  an agent can `grep`/parse it? Is there **one record per attempt**, so "fails
  every time" is distinguishable from "blipped once"?
- **Fix:** structured, append-only, one line per attempt, with a correlation key
  (which input, which attempt, which source). Retry-distinguishable by
  construction. This is the machine-readable substrate the self-diagnosis loop
  below runs on.

## A silent empty or degraded result is a lie

- **Risk:** returning empty/null/degraded that *looks like* a normal result. A
  real instance: a dropped geocoder connection produced "No plan could be
  produced" — an empty result that carried no reason and no hint it was
  transient. The user hit a wall the agent could not explain.
- **Check:** can this function return empty, partial, or degraded output? If so,
  does that output carry *why* — and does a degraded result *announce* itself
  rather than pass as full quality?
- **Fix:** every empty/degraded result carries its cause. Degradation is loud:
  the fallback that assumes a default lot when the parcel is
  missing says so, with a louder caveat — it never silently pretends to be a
  real measurement.

## Distinguish transient from permanent — retry the blip, surface the wall

- **Risk:** treating a one-off network blip and a real outage identically. A
  real instance: a single transient connection reset at the pipeline's entry
  point killed the whole run; the same input worked on the next request.
- **Check:** does a failure path tell a transient fault (reset, refused,
  timeout) apart from a permanent one (4xx, malformed, absent)? Does it retry the
  former and surface the latter, rather than failing hard on both or retrying
  forever on neither?
- **Fix:** bounded retry with backoff for transient classes only; permanent
  failures fail fast *with the reason*. Record both the retries and the final
  outcome, so "recovered after 2 retries" and "dead" are different log stories.

## Reported state must match real state (honest progress)

- **Risk:** a UI or progress signal that shows something other than what is
  happening. A real instance: a progress panel iterated results in *submission*
  order, so one slow source froze the display of others that had already
  finished, and a failed source spun forever instead of turning red. "Stuck-
  looking" was indistinguishable from "hung" — an observability bug even though
  the process was fine.
- **Check:** does each unit of work report its own status promptly and
  independently? Can a slow or failed unit mask the true state of the others?
- **Fix:** surface per-unit status as it resolves (the fix switched to
  `as_completed`): each row updates the instant *its* work returns, a failure
  turns red immediately. A stuck-looking system erodes trust and hides real
  hangs — treat "looks stuck" as a bug, not a cosmetic.

## Instrumentation must never break what it observes

- **Risk:** the logger crashes the task it was added to help. A telemetry call
  that can throw turns a diagnostic aid into a new failure mode — and the worst
  time to discover it is mid-incident.
- **Check:** can the logging / metrics / run-record path raise? Is there a test
  that proves it stays silent on bad input rather than propagating?
- **Fix:** instrumentation degrades to silent, never fatal. Its run-log
  corpus asserts exactly this — "logging never raises" — alongside
  "the record captures the deciding facts." That two-part contract (never
  crash, always capture) is the reusable test for any run-log.

## A fallback must not depend on the thing that failed

- **Risk:** a degradation path wired through the same dependency whose failure
  triggered it — so it can never actually save the case it exists for. A real
  instance: the full-sun fallback required the parcel, but the parcel fetch was
  the thing that had failed, so degradation was dead code exactly when needed.
- **Check:** for each fallback, does it rely on any input that the primary
  failure could have taken out? Trace the fallback's dependencies against the
  failure it handles.
- **Fix:** a fallback must stand on inputs that survive the failure it covers.
  The fix degrades from only a geocoded point (assuming a default lot), so a
  missing parcel no longer blocks the recovery.

## Diagnostic depth may need real inputs — keep those local

- **Risk:** the log that is actually useful contains PII (you cannot diagnose
  "which source failed for THIS address" without the address), but PII in git
  history or CI output cannot be taken back.
- **Check:** does the diagnostic record hold personal or sensitive data? If so,
  is it written somewhere gitignored and kept off CI — not the repo, not a
  shared channel?
- **Fix:** diagnostic logs with real inputs live in a gitignored local path
  (`personal/logs/…`), deliberately holding the real value *on the machine* and
  never leaving it. This is the diagnosability side of `pii-controls.md`: depth
  locally, never in anything that syncs.

---

## The resolve half — the self-diagnosis loop

The items above make a system *legible*; this is how an agent should *use* that
legibility to fix a problem without guessing:

1. **Reproduce minimally.** Get the smallest input that fails before changing
   anything. A fix for a failure you cannot reproduce is a guess.
2. **Read the structured record first.** The deciding inputs and per-attempt
   lines answer "what actually happened" before you form a theory. If the log
   *cannot* answer it, the first fix is to add the missing signal.
3. **Classify transient vs permanent.** One-off blip or a real wall? The retry
   story in the log tells you; do not "fix" a transient by rewriting logic.
4. **Suspect the harness before the code.** A 400 from mangled shell quoting is
   not a router bug. Confirm the input arrived intact and the tooling is sound
   before debugging the target (see `change-safety.md` — "a harness error is not
   a code error until proven").
5. **Fix the root cause *and* add the signal that was missing.** Every
   diagnosis that required a human screenshot or a guess is a gap in the record.
   Close it: the failure that was hard to see once must be one log line away the
   next time. That is how the system gets *more* diagnosable with each incident,
   not less.

## Enforcement

- The run-log contract is testable: **never raises** + **captures the deciding
  facts** (`test_runlog.py` is the worked example). Any run-record should ship
  that two-part test.
- This lens pairs with `change-safety.md` (how to *act* on a diagnosis safely),
  `pii-controls.md` (where diagnostic depth is allowed to live), and the
  human-awareness tiers in the observability plan (this lens is machine-level
  self-diagnosis; those are the human-level interrupt/digest/on-demand tiers).
