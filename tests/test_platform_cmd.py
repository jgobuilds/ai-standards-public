#!/usr/bin/env python3
r"""Corpus for platform_cmd — the Windows/Linux command renderer.

The whole point is correct wrapping of Linux commands for PowerShell, so the
cases pin the escaping that makes single-quote wrapping the right choice: `$` and
`"` must pass through UNexpanded, and a literal `'` must be doubled.

    python -m unittest tests.test_platform_cmd
"""
import os, importlib.util, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location(
    "platform_cmd", os.path.join(HERE, "..", "scripts", "platform_cmd.py"))
pc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pc)


class WslWrap(unittest.TestCase):
    def test_simple_command_is_single_quoted(self):
        self.assertEqual(
            pc.wsl_wrap("cd /app && docker compose up -d n8n"),
            "wsl -e bash -lc 'cd /app && docker compose up -d n8n'")

    def test_dollar_and_double_quotes_survive_unexpanded(self):
        # Single-quote wrapping is chosen precisely so PowerShell does NOT eat
        # `$VAR` or choke on `"…"` — they must appear verbatim inside the wrap.
        wrapped = pc.wsl_wrap('echo "$HOME is $USER"')
        self.assertEqual(wrapped, "wsl -e bash -lc 'echo \"$HOME is $USER\"'")
        self.assertIn("$HOME", wrapped)
        self.assertIn('"', wrapped)

    def test_embedded_single_quote_is_doubled(self):
        # A literal ' in the command must be escaped as '' for PowerShell.
        self.assertEqual(
            pc.wsl_wrap("echo 'hi'"),
            "wsl -e bash -lc 'echo ''hi'''")


class Render(unittest.TestCase):
    def test_host_is_passthrough_both_platforms(self):
        c = "python scripts\\foo.py --flag"
        self.assertEqual(pc.render(c, kind="host", windows=True), c)
        self.assertEqual(pc.render(c, kind="host", windows=False), c)

    def test_linux_wrapped_only_on_windows(self):
        c = "docker compose up -d n8n"
        self.assertEqual(pc.render(c, kind="linux", windows=True), pc.wsl_wrap(c))
        self.assertEqual(pc.render(c, kind="linux", windows=False), c)  # native on POSIX

    def test_bad_kind_raises(self):
        with self.assertRaises(ValueError):
            pc.render("x", kind="container")

    def test_render_options_labels_both(self):
        opts = pc.render_options("docker ps", kind="linux")
        self.assertEqual(set(opts), {"Windows (PowerShell)", "Linux / macOS"})
        self.assertTrue(opts["Windows (PowerShell)"].startswith("wsl -e bash -lc "))
        self.assertEqual(opts["Linux / macOS"], "docker ps")


class WslArgv(unittest.TestCase):
    def test_argv_is_quote_safe_list(self):
        # No quoting layer at all — safe for execution regardless of contents.
        self.assertEqual(
            pc.wsl_argv("echo '$weird\" chars"),
            ["wsl", "-e", "bash", "-lc", "echo '$weird\" chars"])


if __name__ == "__main__":
    unittest.main()
