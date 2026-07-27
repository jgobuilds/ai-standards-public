# Notification taxonomy (house lens)

A lens for **keeping humans aware of autonomous work** — agent actions and CI —
without the two failure modes that kill every observability system:

- **Alert fatigue** — so many notifications that the one that mattered is missed.
- **Silent drift** — problems that never throw an error, so nothing ever pages.

You avoid both by routing every event to a tier by **what the human must do about
it**, not by how interesting it is. Three tiers, and the rule for each.

## The three tiers

| Tier | The human must… | Delivery | Example events |
|---|---|---|---|
| **Interrupt** | act **now** | push + @mention | CI failure on `main`, policy-gate block, breaker / kill-switch trip, PII / secret detection, budget-breaker trip |
| **Digest** | stay **aware** | scheduled post | throughput, notional cost + coverage, drift flags, block reasons, handoff-chain depth |
| **On-demand** | **investigate** | query / dashboard | the audit ledger, the Actions tab, `eval_metrics.py` |

The discipline, straight from SRE practice: **page only on symptoms that require
action; everything else is a report or a dashboard.** An interrupt with no named
owner and no action is noise — which is why the CI alert links to the run and
@mentions a channel (`ci-notifications.md`).

Map an event by asking *"what does a human do when they see this?"* — if the
answer is "nothing right now," it is not an interrupt, no matter how it feels.

## Digest design rules

A digest is where "stay aware" lives — but a feed of green checkmarks becomes
wallpaper, and then the red one is ignored too. So:

- **Anomaly-forward.** Lead with what's wrong (drift, blocks, failures); counts
  follow. "Nothing needs you today" is a *valid* digest — earned by surfacing
  anomalies when they exist, not by omitting them.
- **Heartbeat / dead-man's-switch.** Post at least on a fixed cadence even when
  quiet, so the channel's *silence* is unambiguous and a *missing* heartbeat
  signals the digest lane itself is down. Density-adaptive is the shape: daily
  when active, one heartbeat when quiet.
- **Coverage before any total.** A number computed from 3% of records is a lie of
  omission — state the denominator first (see AIOPS.md's `usage_coverage_pct`).
- **Metadata only, PII-scrubbed.** A digest aggregates across many tasks — higher
  leak risk than a single alert. Links and counts, never task content. Same
  discipline as the interrupt tier (`pii-controls.md`).
- **Never go dark.** If the digest generator fails, it must surface *its own*
  failure as an error post — a missing digest must never read as a quiet day
  (`diagnosability.md` — instrumentation must not hide its own breakage).

## The message contract — BLUF, then evidence

Tiering decides *whether* to post. This decides *what a post says*. The reader is
scanning a channel on a phone, deciding in about two seconds whether this needs
them. Write for that reader.

**Bottom line up front, supporting detail last.** In order:

1. **Title states the outcome, not the event.** "n8n is 2 minor versions behind"
   — not "Research watch ran". A title that only names the job forces the reader
   into the body to learn whether anything happened.
2. **The action line, and it is one of exactly three:** `no action` ·
   `act by <date>` · `act now`. Not "may want to consider". If you cannot say
   which, the alert is not ready to send.
3. **The one number that matters**, with its denominator (`2 of 20 releases`).
4. **Supporting detail** — the few facts that justify the action line.
5. **Provenance last, small:** source lane, cost, a link to the full run.

**Six lines is the cap.** Past that it is a report, and reports are linked, not
pasted. The channel is an index, not an archive.

**Severity is defined, not felt.** Same words everywhere, or the colours stop
meaning anything:

| | Meaning | Reader's obligation |
|---|---|---|
| `error` | Something is broken. | Act now. |
| `warn` | Degraded, or a decision is due. | Decide this week. |
| `info` | Coverage / heartbeat. | Safe to skim. |

A partial result is **`warn`, never `info`** — "4 of 6 sources checked" that
renders as routine is how a blind spot passes for a clean bill of health.

**Detail lives behind a link, and the link is not the message.** Deep-link the
run (n8n execution, CI job) rather than pasting node output. But assume the link
will not be opened: many detail surfaces are localhost-bound and unreachable from
the phone the alert was read on. **The message must carry the decision; the link
only carries the evidence.** If a reader cannot act without clicking, rewrite it.

**Name the lane.** Every alert says which lane produced it, so a wrong or noisy
alert can be traced to a workflow and fixed rather than muted.

## One channel selector, one set of secrets

Both the CI lane and the n8n lane route to Slack / Teams / generic-webhook, and
they share the **same secret names** — but, as of this writing, **two different
selector-variable names**. Document both so the drift stops here:

| Lane | Channel selector | URL secrets |
|---|---|---|
| GitHub Actions (CI notify) | **`NOTIFY_KIND`** (repo variable) | `SLACK_WEBHOOK_URL` / `TEAMS_WEBHOOK_URL` / `NOTIFY_WEBHOOK_URL` |
| n8n (digest, eval-drift, Notify sub-workflow) | **`NOTIFY_CHANNEL`** (`$env`) | same three |

Same three values (`slack` / `teams` / `webhook`), same secrets, two names.
**Converge new work on `NOTIFY_CHANNEL`** for the n8n side; leave the CI
`NOTIFY_KIND` as-is (renaming a live variable across the fleet buys nothing).
Whichever tier posts, the payload shape into the Notify sub-workflow is the same
four fields: `{ severity, title, message, source }`.

## Where each tier lives today

- **Interrupt** → `ci-notifications.md` (CI failure alerts, `NOTIFY_SLACK_MENTION`
  for the loud `<!channel>` ping), plus the router's breakers and Global Error
  Handler.
- **Digest** → the daily digest lane (a daily-digest lane +
  `n8n-workflows/daily-digest.workflow.json`) and the weekly eval-drift lane;
  metrics discipline in `AIOPS.md`.
- **On-demand** → the hash-chained audit ledger, `eval_metrics.py`, the Actions
  tab.

## Enforcement

- The digest's own run-log contract is testable (**never raises** + **captures the
  deciding facts**) — its regression corpus is the worked
  example, applying `diagnosability.md` to the instrumentation itself.
- This lens is the human-awareness umbrella; `diagnosability.md` is its
  machine-level counterpart (how an *agent* self-diagnoses). Interrupt delivery is
  specified in `ci-notifications.md`; digest metrics in `AIOPS.md`.
