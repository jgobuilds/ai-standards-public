---
description: Conformance-test a stdio MCP server — protocol correctness and tool-surface quality.
argument-hint: "-- <command to launch the server>   e.g. -- node ./server.js"
---

Smoke-test the MCP server launched by `$ARGUMENTS`.

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/mcp_smoke.py" $ARGUMENTS
```

Read the result in two halves, because they mean different things:

- **FAIL = protocol breakage.** The server does not speak MCP. Nothing else
  matters until this is green.
- **WARN = tool-surface quality.** The server works but a model will misuse it.
  The most common and most costly warning is *"states when NOT to use it"* — a
  tool with no negative boundary in its description gets reached for constantly.

If the user is building the server, load the `build-mcp-server` skill: the
checklist there covers the decisions this test cannot see — whether the server
should have been written at all, what egress it needs, and the rule that a tool
must not be registered in `.mcp.json` until its whole round trip is proven.
