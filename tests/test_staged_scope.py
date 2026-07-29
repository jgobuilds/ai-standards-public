#!/usr/bin/env python3
"""Corpus for the staged-scope gate.

The two cases that matter are reconstructions of real incidents, not invented
ones — both from 2026-07-26, both caused by a broad `git add`:

  - another writer's in-flight file was staged, capturing HALF their change
    (their new test, not the source function it called) and breaking their build
  - a .pyc that was tracked BEFORE a .gitignore rule existed was staged, so the
    ignore rule looked applied and did nothing

Equally important, and easier to get wrong: the gate must NOT fire on an
ordinary commit, and must NOT block a human at a terminal with no agent ledger.
A gate with false positives gets switched off, and then it protects nothing.
"""
import os, subprocess, sys, tempfile, unittest, importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
SPEC = importlib.util.spec_from_file_location(
    "ssc", os.path.join(HERE, "..", "scripts", "staged_scope_check.py"))
ssc = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ssc)
CHECK = os.path.join(HERE, "..", "scripts", "staged_scope_check.py")


def git(d, *a, **kw):
    return subprocess.run(["git", "-C", d, *a], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", **kw)


def run(d, env=None):
    e = dict(os.environ, **(env or {}))
    return subprocess.run([sys.executable, CHECK, "--root", d], capture_output=True,
                          text=True, encoding="utf-8", errors="replace", env=e, cwd=d)


def write(d, rel, text):
    p = os.path.join(d, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True) if os.path.dirname(rel) else None
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


class _Repo(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        git(self.d, "init", "-q", ".")
        write(self.d, "a.py", "src\n")
        git(self.d, "add", "-A")
        git(self.d, "-c", "commit.gpgsign=false", "commit", "-qm", "init")

    def ledger(self, touched=(), baseline=()):
        write(self.d, ".git/agent-touched", "\n".join(touched) + "\n")
        write(self.d, ".git/agent-baseline", "\n".join(baseline) + "\n")


class ForeignWork(_Repo):
    def test_another_writers_in_flight_file_is_blocked(self):
        # Reconstruction: their edit is already in the tree; the agent edits its
        # own file, then `git add -A` takes both.
        write(self.d, "a.py", "src\ntheir in-flight edit\n")
        write(self.d, "mine.py", "mine\n")
        self.ledger(touched=["mine.py"], baseline=["a.py"])
        git(self.d, "add", "-A")
        r = run(self.d)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("a.py", r.stderr)
        self.assertIn("git restore --staged", r.stderr,
                      "must say how to fix it, not just that it is wrong")

    def test_the_agents_own_edit_to_a_dirty_file_is_fine(self):
        # A file can be dirty at baseline AND legitimately edited by the agent
        # afterwards — continuing someone's work deliberately is not the failure.
        write(self.d, "a.py", "src\nedited by the agent\n")
        self.ledger(touched=["a.py"], baseline=["a.py"])
        git(self.d, "add", "-A")
        self.assertEqual(run(self.d).returncode, 0)


class IgnoredButTracked(_Repo):
    def test_a_tracked_file_matching_gitignore_is_blocked(self):
        # Reconstruction: tracked FIRST, ignore rule added later. .gitignore has
        # no effect on files git already tracks, so the rule looks applied and
        # does nothing — which made a render gate unpassable for seven commits.
        write(self.d, "__pycache__/x.pyc", "bytecode")
        git(self.d, "add", "-A")
        git(self.d, "-c", "commit.gpgsign=false", "commit", "-qm", "tracked first")
        write(self.d, ".gitignore", "__pycache__/\n")
        git(self.d, "add", ".gitignore")
        git(self.d, "-c", "commit.gpgsign=false", "commit", "-qm", "ignore rule")
        write(self.d, "__pycache__/x.pyc", "regenerated")
        self.ledger(touched=["a.py"], baseline=[])
        git(self.d, "add", "-A")
        r = run(self.d)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("git rm --cached", r.stderr)


class NoFalsePositives(_Repo):
    def test_an_ordinary_scoped_commit_passes(self):
        write(self.d, "mine.py", "mine\n")
        self.ledger(touched=["mine.py"], baseline=[])
        git(self.d, "add", "mine.py")
        r = run(self.d)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_a_file_created_this_session_by_a_command_passes(self):
        # Generators and shell heredocs create files the agent never "edited".
        # Flagging those would fire constantly, and a noisy gate gets removed.
        write(self.d, "generated.json", "{}\n")
        self.ledger(touched=["a.py"], baseline=[])
        git(self.d, "add", "-A")
        self.assertEqual(run(self.d).returncode, 0)

    def test_no_ledger_is_advisory_not_blocking(self):
        # A human at a terminal, or a session predating the hook. It must say so
        # rather than pass silently — "checked" and "nothing to check with" are
        # different facts.
        write(self.d, "a.py", "someone else entirely\n")
        git(self.d, "add", "-A")
        r = run(self.d)
        self.assertEqual(r.returncode, 0)
        self.assertIn("no agent ledger", r.stdout)


class Waiver(_Repo):
    def test_the_override_works_and_is_reported(self):
        write(self.d, "a.py", "src\ntheirs\n")
        self.ledger(touched=[], baseline=["a.py"])
        git(self.d, "add", "-A")
        r = run(self.d, env={"SCOPE_CHECK_ALLOW": "a.py"})
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        # A gate that prints "all yours" after being overridden lies in the
        # transcript, and the transcript is what someone reads later.
        self.assertIn("WAIVED", r.stdout)
        self.assertNotIn("all yours", r.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
