# CI failure notifications — setup manifest

Autonomous changes mean nobody is watching the Actions tab. Every repo's CI has a
`notify` job that fires **only on failure** and pushes a message to a channel.
This is the one-time config to turn it on.

> This is the **interrupt** tier — "a human must act now." The complementary
> **digest** tier ("stay aware", a scheduled anomaly-forward heartbeat) and the
> **on-demand** tier (the ledger) are described in
> `notification-taxonomy.md`. One selector-variable note carried there: CI uses
> `NOTIFY_KIND`; the n8n lanes use `NOTIFY_CHANNEL` — same values, same secrets.

## How it works

The `notify` job reads:

| Config | Kind | Where | Default |
|---|---|---|---|
| `NOTIFY_KIND` | **variable** (not secret) | repo | `slack` |
| `NOTIFY_SLACK_MENTION` | **variable** (not secret) | repo | — (no mention) |
| `SLACK_WEBHOOK_URL` | secret | repo | — |
| `TEAMS_WEBHOOK_URL` | secret | repo | — |
| `NOTIFY_WEBHOOK_URL` | secret | repo | — |

It selects the URL matching `NOTIFY_KIND`, formats the payload for that channel
(Slack `{text}`, Teams MessageCard, generic `{text}`), and POSTs. **If the
matching URL secret is unset it no-ops silently** — so the job is safe to merge
before any config exists, and a repo with no webhook simply relies on GitHub's
own red-build + email.

> **On a USER account, org-level secrets do not exist**, so each secret is set
> **per repo** — which is what the loops below do. On an Organization, a single
> `gh secret set <NAME> --org <name> --visibility all` replaces every loop here.
> Check which you have before copying the commands.

## Slack (the default) — one-time setup

1. **Create an incoming webhook** in your Slack workspace:
   - <https://api.slack.com/apps> → *Create New App* → *From scratch*
   - *Incoming Webhooks* → toggle **On** → *Add New Webhook to Workspace*
   - Pick the channel (e.g. `#ci-alerts`) → copy the
     `https://hooks.slack.com/services/T…/B…/…` URL.
   - This is a Slack-admin action; the URL is a **secret** (anyone with it can
     post to that channel).

2. **Set it on each repo.** Fill in your own owner and repo list — this file is
   a shared source and names nobody's fleet.

   ```bash
   URL='https://hooks.slack.com/services/XXX/YYY/ZZZ'   # your webhook
   OWNER=your-org
   for repo in repo-a repo-b repo-c; do
     gh secret set SLACK_WEBHOOK_URL --repo "$OWNER/$repo" --body "$URL"
   done
   ```

   `NOTIFY_KIND` defaults to `slack`, so **nothing else is needed** for Slack.

   **Don't hand-edit the webhook per repo.** GitHub secrets are write-only, so
   any non-CI consumer (a container, a daemon) needs its own copy — typically in
   a `.env`. Two copies are unavoidable; drift is the risk. Use the one-input
   fan-out so entering or rotating it is a single command:

   ```bash
   export SYNC_NOTIFY_OWNER=your-org SYNC_NOTIFY_REPOS=repo-a,repo-b,repo-c
   python scripts/sync_notify_webhook.py --env-file ../someproject/.env
   # rotate everywhere (updates the .env too):
   python scripts/sync_notify_webhook.py --value "https://hooks.slack.com/services/..." \n       --env-file ../someproject/.env
   ```

   It never prints the secret (fingerprint only), and it REFUSES to run with an
   empty fleet rather than reporting "synced to 0 repos" and exiting 0. As shared
   secrets multiply, move to a real secrets manager and record the decision in an
   ADR.

3a. **(Optional) Make it an explicit alert, not just a post.** By default the
   message posts quietly. To have a failure actively *notify* the channel, set
   the `NOTIFY_SLACK_MENTION` variable — the mention is prepended to both the
   header and the notification text, which is what makes Slack ping:

   ```bash
   for repo in repo-a repo-b repo-c; do
     gh variable set NOTIFY_SLACK_MENTION --repo "$OWNER/$repo" --body channel
   done
   ```

   Accepted values: `channel` (→ `<!channel>`, everyone in the channel) ·
   `here` (→ `<!here>`, only active members) · a raw `<@U012ABC>` (one user) ·
   a raw `<!subteam^S012ABC>` (a user group). Unset = no mention (today's
   behaviour). **Slack-only** — the token is ignored for Teams and generic
   webhooks, which don't understand Slack mention syntax.

   ⚠️ `channel` pings *every* member on *every* red build. For a busy shared
   channel prefer `here`, a dedicated `#ci-alerts` channel, or a user-group
   mention so only the on-call owners are alerted.

3. **Test it** — push a trivially-failing commit to a branch, or re-run a failed
   job. The first real failure is the only true test (see caveat below).

## Switching a repo to Teams

```bash
gh variable set NOTIFY_KIND --repo $OWNER/<repo> --body teams
gh secret   set TEAMS_WEBHOOK_URL --repo $OWNER/<repo> --body 'https://…'
```

⚠️ **Teams' webhook story is in flux.** The classic Office 365 *Incoming Webhook*
connector (which accepts the MessageCard payload this job sends) is being retired
in favour of **Workflows** (Power Automate), whose HTTP trigger expects a
different schema (often an Adaptive Card). If your Teams URL is a Workflows
trigger, the MessageCard body may need adjusting — verify against your specific
webhook before relying on it. Slack has no such ambiguity, which is why it is the
default.

## Generic webhook (anything else)

```bash
gh variable set NOTIFY_KIND --repo $OWNER/<repo> --body webhook
gh secret   set NOTIFY_WEBHOOK_URL --repo $OWNER/<repo> --body 'https://…'
```

Sends `{"text": "..."}` — works for most webhook receivers, or point it at the
n8n Notify sub-workflow's inbound webhook to route through the existing
channel-abstraction there.

## What the message contains

**Slack** gets a Block Kit message: a header (`:x: *CI failed* — repo`), a fields
row (branch + short commit), and a red **View run** button linking to the failed
run. A plain-text `text` fallback is included for notifications/accessibility.
**Teams** (MessageCard) and **generic webhook** get plain text — same info, no
Block Kit (that format is Slack-specific).

Either way: repo, short SHA, branch, run link. **No log content, no secrets, no
PII** — just enough to click through. The Actions run itself holds the detail
(and is access-controlled to repo collaborators).

## Rotating or removing

```bash
gh secret set SLACK_WEBHOOK_URL --repo $OWNER/<repo> --body '<new-url>'  # rotate
gh secret delete SLACK_WEBHOOK_URL --repo $OWNER/<repo>                  # disable (job no-ops)
```

## Design notes

- **The block is duplicated across the fleet on purpose.** A shared reusable
  workflow would couple every repo — including the public one — to a private repo
  being present, breaking "a repo stands alone". This file is the single source
  of truth for the block; if it changes, update each workflow.
- **`NOTIFY_KIND` is a variable, not a secret** — it isn't sensitive, and
  variables are visible in logs, which is fine for a channel selector.
- **Failure of the notification is non-fatal.** A dead webhook must not turn a
  *green* build red — the POST failure is caught and logged, and CI status
  already reflects the real result.

## Caveat — untested against a live channel

The job is verified for valid YAML, valid JSON payloads (Slack + Teams), and the
no-op-when-unset path. The **actual POST is not exercised until a webhook is
configured and a build fails.** The first real red build is the end-to-end test.
