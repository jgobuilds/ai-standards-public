#!/usr/bin/env python3
"""Protocol + quality smoke test for a stdio MCP server.

Written after hand-rolling an MCP server and testing it by pasting JSON-RPC
frames into a shell. That "worked" right up until it did not, and nothing was
committed that would catch a regression. This is the missing gate.

It checks two different things, and the distinction matters:

  PROTOCOL  — does it speak MCP at all? A server that fails here is broken.
  QUALITY   — does its tool surface follow the conventions that make a tool
              usable by a model? Failing here is a warning, not a break.

    python scripts/mcp_smoke.py -- node ./ask-human-mcp.js
    python scripts/mcp_smoke.py --strict -- python -m my_server

STDIN STAYS OPEN until the checks finish. A real MCP client holds the pipe; a
test that closes it early kills in-flight calls and looks like a server bug —
which cost a real debugging cycle.
"""
from __future__ import annotations
import argparse, json, subprocess, sys, threading, time

PROTOCOL_VERSION = "2024-11-05"


class Server:
    """A stdio MCP server under test, with the pipe deliberately held open."""

    def __init__(self, argv, timeout):
        self.timeout = timeout
        self.proc = subprocess.Popen(
            argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True, encoding="utf-8",
            errors="replace", bufsize=1)
        self._lines, self._lock = [], threading.Lock()
        threading.Thread(target=self._pump, daemon=True).start()

    def _pump(self):
        for line in self.proc.stdout:
            with self._lock:
                self._lines.append(line.strip())

    def send(self, obj):
        self.proc.stdin.write(json.dumps(obj) + "\n")
        self.proc.stdin.flush()

    def await_id(self, want_id):
        """Wait for the response with this id. Returns None on timeout."""
        end = time.time() + self.timeout
        while time.time() < end:
            with self._lock:
                for raw in list(self._lines):
                    try:
                        msg = json.loads(raw)
                    except ValueError:
                        continue
                    if msg.get("id") == want_id:
                        self._lines.remove(raw)
                        return msg
            time.sleep(0.05)
        return None

    def close(self):
        try:
            self.proc.stdin.close()
        except OSError:
            pass
        try:
            self.proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.proc.kill()

    def stderr_tail(self, n=400):
        try:
            self.proc.stderr.close()
        except OSError:
            pass
        return ""


class Report:
    def __init__(self):
        self.fails, self.warns, self.passes = [], [], 0

    def ok(self, label):
        self.passes += 1
        print(f"  PASS  {label}")

    def fail(self, label, detail=""):
        self.fails.append(label)
        print(f"  FAIL  {label}" + (f" — {detail}" if detail else ""))

    def warn(self, label, detail=""):
        self.warns.append(label)
        print(f"  WARN  {label}" + (f" — {detail}" if detail else ""))


def check_protocol(s, r):
    s.send({"jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {"protocolVersion": PROTOCOL_VERSION,
                       "capabilities": {}, "clientInfo": {"name": "mcp_smoke", "version": "1"}}})
    init = s.await_id(1)
    if not init:
        r.fail("responds to initialize", "no reply before timeout")
        return None
    res = init.get("result") or {}
    r.ok("responds to initialize")
    if res.get("protocolVersion"):
        r.ok(f"declares protocolVersion ({res['protocolVersion']})")
    else:
        r.fail("declares protocolVersion")
    if isinstance(res.get("capabilities"), dict) and "tools" in res["capabilities"]:
        r.ok("declares tools capability")
    else:
        r.fail("declares tools capability", "a tool server that does not advertise tools")
    if (res.get("serverInfo") or {}).get("name"):
        r.ok("declares serverInfo.name")
    else:
        r.warn("declares serverInfo.name")

    # A notification carries no id and MUST NOT be answered.
    s.send({"jsonrpc": "2.0", "method": "notifications/initialized"})

    s.send({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
    listed = s.await_id(2)
    if not listed:
        r.fail("responds to tools/list", "no reply — often a crash on the notification")
        return None
    tools = (listed.get("result") or {}).get("tools")
    if not isinstance(tools, list) or not tools:
        r.fail("tools/list returns a non-empty list")
        return None
    r.ok(f"tools/list returns {len(tools)} tool(s)")

    s.send({"jsonrpc": "2.0", "id": 3, "method": "no/such/method"})
    unknown = s.await_id(3)
    if unknown and "error" in unknown:
        r.ok("rejects an unknown method with an error")
    elif unknown:
        r.warn("rejects an unknown method with an error", "replied with a result")
    else:
        r.fail("survives an unknown method", "no reply — the server may have died")
    return tools


def check_quality(tools, r):
    for t in tools:
        name = t.get("name") or "<unnamed>"
        desc = (t.get("description") or "").strip()
        schema = t.get("inputSchema") or {}

        if desc:
            r.ok(f"[{name}] has a description")
        else:
            r.fail(f"[{name}] has a description", "a model picks tools by description alone")

        # The single highest-value convention: say when NOT to use it. Without a
        # negative boundary a model reaches for the tool constantly.
        if any(k in desc.lower() for k in ("do not", "don't", "never", "only use", "not for")):
            r.ok(f"[{name}] states when NOT to use it")
        else:
            r.warn(f"[{name}] states when NOT to use it",
                   "no negative boundary — expect over-use")

        if len(desc) < 60:
            r.warn(f"[{name}] description is substantive", f"{len(desc)} chars")

        if schema.get("type") == "object" and isinstance(schema.get("properties"), dict):
            r.ok(f"[{name}] inputSchema is an object with properties")
        else:
            r.fail(f"[{name}] inputSchema is an object with properties")

        props = schema.get("properties") or {}
        undescribed = [k for k, v in props.items() if not (v or {}).get("description")]
        if props and not undescribed:
            r.ok(f"[{name}] every parameter is described")
        elif undescribed:
            r.warn(f"[{name}] every parameter is described", f"missing: {', '.join(undescribed)}")

        if props and not schema.get("required"):
            r.warn(f"[{name}] declares required parameters",
                   "nothing required — the model may call it with nothing")


def check_robustness(s, tools, r):
    """A tool error must not kill the server: the agent should lose the ANSWER,
    never the session."""
    name = tools[0].get("name")
    s.send({"jsonrpc": "2.0", "id": 10, "method": "tools/call",
            "params": {"name": name, "arguments": {}}})
    got = s.await_id(10)
    if not got:
        r.fail(f"[{name}] survives a call with no arguments",
               "no reply — the server likely crashed")
        return
    r.ok(f"[{name}] survives a call with no arguments")
    result = got.get("result") or {}
    if "error" in got or result.get("isError") is True:
        r.ok(f"[{name}] reports bad input as an error rather than pretending")
    else:
        r.warn(f"[{name}] reports bad input as an error rather than pretending",
               "returned a normal result for empty arguments")

    s.send({"jsonrpc": "2.0", "id": 11, "method": "tools/call",
            "params": {"name": "definitely_not_a_tool", "arguments": {}}})
    got = s.await_id(11)
    if got:
        r.ok("rejects an unknown tool name")
    else:
        r.fail("rejects an unknown tool name", "no reply — the server may have died")


def main():
    ap = argparse.ArgumentParser(description="Smoke-test a stdio MCP server.")
    ap.add_argument("--timeout", type=float, default=20.0)
    ap.add_argument("--strict", action="store_true",
                    help="treat quality warnings as failures")
    ap.add_argument("cmd", nargs=argparse.REMAINDER,
                    help="-- <command to launch the server>")
    a = ap.parse_args()
    argv = [c for c in a.cmd if c != "--"]
    if not argv:
        ap.error("give the server command after --, e.g. -- node ./server.js")

    print(f"MCP smoke test — {' '.join(argv)}\n")
    r = Report()
    s = Server(argv, a.timeout)
    try:
        tools = check_protocol(s, r)
        if tools:
            check_quality(tools, r)
            check_robustness(s, tools, r)
    finally:
        s.close()

    print(f"\n  {r.passes} passed, {len(r.warns)} warning(s), {len(r.fails)} failure(s)")
    if r.fails:
        print("\nFAILED — the server does not speak MCP correctly.")
        return 1
    if r.warns and a.strict:
        print("\nFAILED (--strict) — protocol is fine; the tool surface needs work.")
        return 1
    if r.warns:
        print("\nProtocol OK. Warnings are tool-surface quality, not breakage.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
