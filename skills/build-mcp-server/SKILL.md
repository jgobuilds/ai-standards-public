---
name: build-mcp-server
description: >-
  Build, review, or fix an MCP (Model Context Protocol) server so an agent can
  call a new capability. Use whenever the user wants to "give the agent a tool",
  "wire up an MCP", "connect <service> to Claude", "make an MCP server", asks why
  an agent is not calling a tool, or is about to hand-write JSON-RPC. Covers the
  adopt-vs-generate-vs-write decision, the tool-surface conventions that decide
  whether a model actually uses the tool correctly, the failure-reporting rules,
  the egress declaration, and the conformance gate (scripts/mcp_smoke.py). Run it
  BEFORE writing a server, not after.
---

# Building an MCP server

Written after hand-rolling one, skipping every step below, and shipping a tool
whose answer path did not work. The order here is the point.

## 1. Do not write one yet

Three ways to get an MCP server, cheapest first:

| Route | When it wins |
|---|---|
| **Adopt an existing server** | The service is popular. Check the vendor's own, then the MCP registry/community list. A maintained server beats yours the day the API changes. |
| **Generate one** | The capability is "wrap this API". Generators (e.g. `cli-printing-press`, already wired into this workspace's capability factory) produce a CLI + MCP pair and bake in token-efficiency conventions. |
| **Write one** | Genuinely bespoke — it talks to *your* control plane, enforces *your* policy, or has no API behind it at all. |

State which you chose and why, per `build-vs-adopt.md`. "I wrote it because I did
not look" is the failure this section exists to prevent, and it is the one that
actually happened.

If you do write one, **use the official MCP SDK** unless you can name the reason
not to. Hand-rolled JSON-RPC means you own protocol compliance — version
negotiation, notifications, error codes — forever. A dependency-free server is
only worth it where a dependency is genuinely unwelcome (a hardened image, a
supply-chain-sensitive path); say so in the file header if you take that route.

## 2. Design the tool surface for a reader who cannot ask questions

A model picks tools from the description alone. Everything here is cheap to get
right up front and expensive to retrofit once agents depend on it.

- **Say when NOT to use it.** The single highest-value line. Without a negative
  boundary the model reaches for the tool constantly. "Do not use this for things
  you can determine yourself."
- **One tool, one job.** A `do_everything(action, payload)` tool pushes the
  dispatch decision into the model, where it is invisible and untestable.
- **Describe every parameter**, and mark the genuinely required ones `required`.
  A schema with nothing required invites a call with nothing in it.
- **Prefer compound operations over chatty ones.** One call that answers the real
  question beats ten round trips the model has to orchestrate — the local-first,
  compound-command principle behind agent-native CLIs. Every round trip is
  context the model spends and can get wrong.
- **Return prose the model can act on**, not raw JSON dumps, and cap what you
  return. Tool output is context.

## 3. Report failure honestly — this is where tools do real damage

- **`isError: true` for faults**, so the model can tell "the tool broke" from
  "the answer is no".
- **Never assert a cause you cannot know.** A fallback string like "the form came
  back empty" printed on *any* missing field turns a transport failure into a
  false statement about what a human did. State what you observed, not what you
  infer.
- **Distinguish "no answer" from "empty answer".** They are different facts and a
  caller that cannot tell them apart will treat silence as data.
- **A tool error must never kill the server.** The agent should lose the answer,
  never the session.
- **Fail closed on auth**, and never log a credential value.

## 4. Prove the RESULT PATH before you build on it

A tool is a round trip. The call is the easy half; getting the result back is
where the host's limits bite, and they bite late.

**Spend the first hour proving the answer can travel**, with a hardcoded value
and no product logic. Four transports were built for one tool before one worked,
and each failure was a property of the host, discoverable on day one:

- it would not await a suspended child (measured: returned in 0.4s)
- it could not write files — at any path, at any permission
- it would not register a second endpoint

**Then use the direction that already works.** Every hop in the design that
finally shipped was a path already in use: the one open egress port, the call the
orchestrator already makes, and loopback. The tempting fix each time was to open
a firewall rule; not one was needed. When a transport needs a new hole, that is
evidence you are pushing against the grain of the system, not that the hole is
missing.

## 5. Declare what it touches

- **Egress**: name the host and port it needs. If the runner is firewalled, check
  whether the hole already exists before asking for a new one — widening a
  containment boundary is a security decision, not a config tweak.
- **Secrets**: read from the environment, fail closed when absent, and say which
  variable is missing rather than failing silently.

## 6. Gate it

```bash
python scripts/mcp_smoke.py -- <command to launch the server>
python scripts/mcp_smoke.py --strict -- <command>     # warnings become failures
```

It separates **protocol** failures (broken) from **tool-surface** warnings
(usable but will be misused), and it is itself verified against a deliberately
bad server so it cannot pass everything. Wire it into CI for any server you own.

## 7. Do not register it until the WHOLE round trip is proven

The last step, and the one that matters most. A tool that is registered but whose
result path is broken is **worse than no tool**: the agent calls it, the side
effect happens — a human is paged, a record is written — and the answer is
discarded. Prove the full loop end to end, then add it to `.mcp.json`.

If the loop cannot be closed yet, ship the server **unregistered**, with a
comment saying why. Half a tool, clearly labelled, is honest. Half a tool, wired
in, is a trap.

## Checklist

- [ ] Adopt / generate / write — decided and stated
- [ ] SDK used, or a reason given for hand-rolling
- [ ] Description says when NOT to use it
- [ ] Every parameter described; required marked
- [ ] Errors use `isError`; no inferred causes in failure text
- [ ] "No answer" ≠ "empty answer"
- [ ] Result path proven with a hardcoded value BEFORE any product logic
- [ ] Every hop uses a path that already worked — no new firewall rule
- [ ] Egress named; existing holes reused, not widened
- [ ] `mcp_smoke.py` green, committed as a gate
- [ ] Full round trip proven **before** registration
