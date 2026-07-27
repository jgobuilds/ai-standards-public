# Dependency security (house lens)

A lens for **choosing and holding third-party dependencies** — the ones you don't
write, can't fix, and can only upgrade.

Written after verifying the 2026 CVE record of five candidate dependencies during
a real adoption decision. The findings reset how we evaluate: every orchestration
platform surveyed had **critical unauthenticated RCEs**, and two components had
CVEs **exploited in the wild within 36 hours of disclosure**. This is the normal
condition of the ecosystem, not an unlucky quarter.

## The privileged-path principle

**The security bar scales with a dependency's position, not its popularity.**

Ask: *when* this is compromised — not if — what does the attacker get? A
dependency that sits in the path of every request and holds every credential is a
different risk class from one that formats a document, even at identical CVSS.

| Position | Bar |
|---|---|
| **Privileged path** — sees every request, holds keys/secrets, writes the audit record | Highest. Prefer *fewer, smaller, boring*. A feature you don't need is attack surface you own. |
| **Adjacent** — processes data but holds no credential | Standard: pin, scan, contain. |
| **Leaf** — build tooling, doc generation, dev-only | Lowest. Keep it out of the runtime image entirely. |

The corollary is uncomfortable and worth stating: **a popular, feature-rich
dependency can be the wrong choice for the privileged path** precisely because
popularity makes it a target and features make it large. "Everyone uses it" is a
statement about blast radius, not about safety.

## Category risk is structural, not incidental

Some categories are dangerous *by construction*, and no vendor choice escapes it.
Workflow/orchestration platforms **execute user-supplied code as their core
feature** — expressions, script nodes, query modes. Arbitrary code execution *is
the product*. So a swap within the category is lateral, not an improvement.

Before adopting, ask **what this software is designed to do that an attacker
would also want** — and if the answer is "run arbitrary code," treat every
instance in the category as high-risk and contain it accordingly.

## Pin to a digest — and gate the pin on a date

Two failure modes that pull in opposite directions, so you need both halves:

- **Floating tags** (`:latest`) — a restart silently changes what runs; you cannot
  state your own version without looking; a downgrade hides as easily as an upgrade.
- **Stale pins** — pinning *without* an update process is **worse** than floating,
  because you deliberately freeze on a known-vulnerable version and nothing tells you.

So: **pin every third-party image and base image to a digest**, record the pins
with their risk notes in a policy file, and put a **`reviewBy` date on the policy
that FAILS a check when it passes**. Same forcing-function shape as a dated model
policy — a gate that fails, not a dashboard nobody opens.

Worked example: a repo-level `image-policy.json` +
`scripts/image_policy_check.py` (static — no daemon, so it runs in CI), enforced
as a CI step.

## Scan on a schedule, not only on push

A push-triggered pipeline can never catch the most common way you become
vulnerable: **a pinned dependency ages into a CVE without a single line of your
code changing.** Only a clock catches that.

- **On push:** the static checks — everything pinned, pins reviewed, no IaC
  misconfiguration. Fast, no image pull.
- **On a schedule:** the vulnerability scan against the pinned artifacts, routed
  to a channel on failure (see `notification-taxonomy.md` — this is the
  *interrupt* tier).
- **Fail on fixable CRITICALs.** A critical with no available patch is a risk to
  *record and contain*, not a build to block on forever.

## Trusted sources: a gate on the way in, checked daily thereafter

Two separate obligations, and most teams do only the first:

- **On the way in** — nothing enters the stack without being scanned and recorded.
- **Every day after** — because what you approved yesterday is not what it is today.

### The entry gate (works with no registry infrastructure)

You do not need an artifact registry to have an approval process. The minimum
viable version is a **register of approved artifacts, enforced in CI**:

1. **Scan before adopting.** Run the vulnerability scanner against the exact
   artifact — not the project's reputation — at CRITICAL.
2. **Record the decision**: the resolved digest, where it is used, a **risk note**
   saying what an attacker gets if it falls, and a review date.
3. **Enforce it.** A CI check fails on any artifact that is not pinned, or whose
   pin is absent from the register, or whose review date has passed.
4. **Exceptions get a reason and a revisit trigger** (see below) or they are holes.

Worked example: a repo-level `image-policy.json` +
`scripts/image_policy_check.py`. The register *is* the allowlist; the CI gate is
what makes it a control rather than a document.

### When a real registry earns its place

A pull-through cache or a full registry (Harbor — CNCF, Apache-2.0, scan-on-push,
"prevent vulnerable images from running", Cosign content trust) adds things the
register cannot:

| Rung | Adds | Costs |
|---|---|---|
| Register + CI gate | Approval, reproducibility, tamper-resistance | ~0 |
| **Pull-through cache** | **Insulation from upstream deletion** — the one real gap digest pinning leaves | ~1 container |
| **Full registry** | Enforcement *at pull time*, signing/provenance, promotion workflow, air-gap | 6–9 containers, TLS, backups, and its own patching |

**Climb a rung when a trigger fires, not on principle.** A registry you maintain
for its own sake is an unpatched attack surface wearing a security label. Name the
trigger in an ADR: a deleted upstream image, a second publisher, an auditor asking
for provenance, or an air-gapped deployment.

### Daily, not weekly

Set the cadence against the threat: the 2026 pattern is **CVEs exploited within
36 hours of disclosure**, so a weekly loop can leave a known-exploited flaw live
for six days. **Check daily**, on two tracks that answer different questions:

- **"Is something I depend on now vulnerable?"** → dependency alerts (Dependabot
  is free, covers private repos, and needs no infrastructure). Turn it on for
  *every* repo — verify it is actually enabled rather than assuming; it is off by
  default on many, and free alerting you never switched on protects nothing.
- **"Is a *pinned* artifact now vulnerable?"** → a scheduled scan, because a pin
  ages into a CVE with no commit to trigger a pipeline.

Pair them with an **update** mechanism, not just an alert one — a scanner tells
you something is broken, Dependabot/Renovate opens the PR that fixes it. Alerting
without a fix path just accumulates known debt.

## Supply chain: assume the registry is hostile

[454,600 new malicious packages in 2025; 1.23M cumulative.](https://shattered.io/npm-supply-chain-attacks-2026/)
The controls that actually worked in 2026:

- **Disable lifecycle install scripts** (`npm ci --ignore-scripts`) — the single
  highest-value control; most package malware executes at install time.
- **Committed lockfiles, exact versions**, installed with the ci/frozen resolver.
- **A quarantine window** on fresh releases — do not auto-adopt a version
  published hours ago. Most malicious releases are caught within days.
- **Provenance is necessary but NOT sufficient.** In the 2026 axios compromise the
  backdoored package carried *valid* Sigstore/SLSA provenance, because the
  attacker compromised the CI identity and the build system signed the malware
  honestly. Signed does not mean trustworthy; it means attributable.

## Containment beats patch cadence

You will run a vulnerable dependency at some point — between disclosure and your
upgrade, at minimum. So design for **what an exploit reaches**, and treat that as
the primary control:

- No host port unless something outside genuinely needs it; bind to loopback.
- Least-privilege mounts (**read-only** by default), non-root users.
- Default-deny egress, so a compromised component cannot phone home.
- Secrets scoped per hop, never one credential that opens everything.
- Keep the crown jewels (key vault, audit ledger) reachable from exactly one
  service, and never writable by the others.

**State the blast radius honestly.** "Contained" is not "harmless" — write down
what an attacker *would* get, so the risk is a known quantity rather than a
comforting adjective.

## Exceptions are written down or they are holes

An accepted finding needs, in the file: what it is, **why** it is accepted (not
merely inconvenient), the compensating control, and **what would make us
revisit**. A silently-suppressed finding is indistinguishable from one nobody
noticed. Prefer upgrading over adding a suppression.

## Enforcement

- `image_policy_check.py` — everything pinned, pins reviewed by a date. CI, every push.
- A scheduled vulnerability scan with a documented ignore-file (`.trivyignore`).
- The **build-vs-adopt** survey gains a security column: CVE history and the
  vendor's security *process* (a CNA, a published advisory feed, and fast fix
  releases are maturity signals worth more than a low CVE count, which often
  just means nobody is looking).
