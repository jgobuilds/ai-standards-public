#!/usr/bin/env python3
"""The hooks' SHELL behaviour — the layer nothing tested, which is why it broke.

`tests/test_pii_scan.py` covers the scanner's internals thoroughly. Nothing
covered the generated `.git/hooks/*` shell, so this survived unnoticed:

    if [ -f "$SCAN" ]; then ... fi
    exit 0                       # <- reached silently when $SCAN is absent

`$SCAN` is baked in at install time as an ABSOLUTE path. Move, rename or clone
ai-standards elsewhere and the gate stops running — commits pass unscanned, with
no warning and a zero exit. The lens's own doctrine is "absent by construction;
scanning is the backstop", and a backstop that disappears without saying so is
worse than none, because the team believes it is covered.

These tests run the real generated hook through a real `sh`.

    python -m unittest tests.test_hook_behaviour
"""
import os, re, shutil, stat, subprocess, tempfile, unittest, importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
SPEC = importlib.util.spec_from_file_location(
    "install_controls", os.path.join(HERE, "..", "scripts", "install_controls.py"))
ic = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ic)

SH = shutil.which("sh") or shutil.which("bash")


def render(template, scan, scope=""):
    """Render a hook exactly as install_controls does, minus the chained tail.

    `scope` points at staged_scope_check.py in a real install; empty here, which
    the hook treats as absent and skips — these cases are about the PII gate.
    """
    body = template.format(scan=scan, vis="private", tier="P1", chain="",
                           scope=scope)
    # The templates carry a {chain} placeholder for a pre-existing hook; empty
    # here so we exercise the gate itself rather than someone else's script.
    return body


def run_hook(text, args=(), env=None):
    d = tempfile.mkdtemp()
    try:
        p = os.path.join(d, "hook")
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        os.chmod(p, os.stat(p).st_mode | stat.S_IEXEC)
        e = dict(os.environ)
        e.pop("PII_GATE", None)
        if env:
            e.update(env)
        r = subprocess.run([SH, p, *args], capture_output=True, text=True,
                           cwd=d, env=e, encoding="utf-8", errors="replace")
        return r
    finally:
        shutil.rmtree(d, ignore_errors=True)


@unittest.skipIf(not SH, "no POSIX shell available")
class MissingScannerFailsClosed(unittest.TestCase):
    """The regression that motivated this file."""

    def test_pre_commit_blocks_when_scanner_is_absent(self):
        r = run_hook(render(ic.HOOK, "/nonexistent/pii_scan.py"))
        self.assertNotEqual(r.returncode, 0,
                            "an unresolvable scanner must BLOCK, not pass silently")

    def test_commit_msg_blocks_when_scanner_is_absent(self):
        r = run_hook(render(ic.MSG_HOOK, "/nonexistent/pii_scan.py"), args=("msg.txt",))
        self.assertNotEqual(r.returncode, 0)

    def test_it_says_why_rather_than_failing_mutely(self):
        """A gate that blocks without explaining gets deleted by whoever it blocks."""
        r = run_hook(render(ic.HOOK, "/nonexistent/pii_scan.py"))
        out = r.stdout + r.stderr
        self.assertIn("not found", out.lower())
        self.assertIn("/nonexistent/pii_scan.py", out,
                      "must name the path it looked for, so it can be fixed")


@unittest.skipIf(not SH, "no POSIX shell available")
class EscapeHatch(unittest.TestCase):
    """A toolless environment needs a way through — but a DELIBERATE one."""

    def test_pii_gate_off_allows_the_commit(self):
        r = run_hook(render(ic.HOOK, "/nonexistent/pii_scan.py"), env={"PII_GATE": "off"})
        self.assertEqual(r.returncode, 0)

    def test_the_hatch_announces_itself(self):
        r = run_hook(render(ic.HOOK, "/nonexistent/pii_scan.py"), env={"PII_GATE": "off"})
        self.assertIn("PII_GATE=off", r.stdout + r.stderr,
                      "a silent bypass is indistinguishable from the bug being fixed")

    def test_only_the_exact_value_opens_the_hatch(self):
        # "0", "false", "no" and a stray truthy string must NOT disable the gate.
        for v in ("0", "false", "no", "OFF", "1", "yes"):
            with self.subTest(value=v):
                r = run_hook(render(ic.HOOK, "/nonexistent/pii_scan.py"),
                             env={"PII_GATE": v})
                self.assertNotEqual(r.returncode, 0,
                                    f"PII_GATE={v!r} must not disable the gate")


class TemplatesStayFailClosed(unittest.TestCase):
    """A static guard, so a future edit cannot quietly restore the old shape."""

    def test_no_bare_existence_test_around_the_scan(self):
        for name, tpl in (("HOOK", ic.HOOK), ("MSG_HOOK", ic.MSG_HOOK)):
            with self.subTest(template=name):
                self.assertNotIn('if [ -f "$SCAN" ]; then', tpl,
                                 "this is the fail-open shape; use `elif [ ! -f ... ]`")
                self.assertIn('[ ! -f "$SCAN" ]', tpl)

    def test_templates_still_avoid_set_e(self):
        """Deliberate: under `set -e` a false test in a chain aborts the hook and
        blocks a clean commit, and a gate with false positives gets disabled.

        Checks EXECUTABLE lines only — both templates carry a comment explaining
        the choice ("Deliberately NOT `set -e`"), and a naive substring match
        fires on the explanation rather than on the thing it warns about.
        """
        for name, tpl in (("HOOK", ic.HOOK), ("MSG_HOOK", ic.MSG_HOOK)):
            with self.subTest(template=name):
                code = [l for l in tpl.splitlines() if not l.strip().startswith("#")]
                offenders = [l for l in code if re.match(r"\s*set\s+-\w*e", l)]
                self.assertEqual(offenders, [], f"{name} enables set -e")


class PortabilityCheckPrecision(unittest.TestCase):
    """The `.pre-commit-config.yaml` absolute-path check, and what it must NOT flag.

    Found in the wild: the drive-letter pattern matched the "s:/" inside
    "https://", so two repos with perfectly portable configs were reported as
    carrying machine-specific paths. Every false positive is a permanent case
    here — a check that fires on the common path gets ignored, and then the real
    absolute path it exists to catch slips through.
    """

    PATTERN = r"(?<![A-Za-z0-9])[A-Za-z]:[\\/]|/(?:home|Users)/[A-Za-z0-9._-]+/"

    def flags(self, body):
        return bool(re.search(self.PATTERN, body))

    def test_https_repo_urls_are_not_absolute_paths(self):
        for url in ("  - repo: https://github.com/pre-commit/pre-commit-hooks",
                    "  - repo: http://example.com/x",
                    "  entry: python -m ruff --config https://x/y"):
            with self.subTest(line=url):
                self.assertFalse(self.flags(url), f"false positive on {url!r}")

    def test_real_windows_paths_are_still_caught(self):
        for line in (r"        entry: python D:\work\standards\scripts\pii_scan.py",
                     "        entry: python D:/work/standards/scripts/pii_scan.py",
                     '        entry: "C:/tools/scan.py"'):
            with self.subTest(line=line):
                self.assertTrue(self.flags(line), f"missed a real path: {line!r}")

    def test_real_posix_home_paths_are_still_caught(self):
        for line in ("        entry: python /home/dev/standards/scripts/pii_scan.py",
                     "        entry: python /Users/dev/standards/scripts/pii_scan.py"):
            with self.subTest(line=line):
                self.assertTrue(self.flags(line))

    def test_the_shipped_regex_matches_this_corpus(self):
        """Guard against the check and its test drifting apart."""
        src = open(os.path.join(HERE, "..", "scripts", "install_controls.py"),
                   encoding="utf-8").read()
        self.assertIn("(?<![A-Za-z0-9])[A-Za-z]:", src,
                      "install_controls no longer uses the guarded pattern")


if __name__ == "__main__":
    unittest.main()
