#!/usr/bin/env python3
"""Corpus for the ticket layer.

Only two properties really matter, and neither is about any one tracker:

  - **A re-run must not duplicate.** An agent re-runs, a nightly lane fires, a
    flaky job fails five times. Without stable-key idempotency the tracker fills
    with duplicates and gets ignored, exactly as a noisy alert channel does.
  - **Swapping must be real.** A seam with one implementation is an assumption,
    not a seam. The file backend is exercised here for that reason, not as a toy.
"""
import importlib.util, os, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SPEC = importlib.util.spec_from_file_location(
    "ticket", os.path.join(HERE, "..", "scripts", "ticket.py"))
t = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(t)


class Idempotency(unittest.TestCase):
    def setUp(self):
        self.f = os.path.join(tempfile.mkdtemp(), "t.jsonl")
        self.b = t.FileBackend(self.f)

    def test_the_same_key_updates_instead_of_duplicating(self):
        self.b.open("k", "title", "first")
        self.b.open("k", "title", "second")
        self.assertEqual(len(self.b._all()), 1, "a re-run must not create a second ticket")
        self.assertEqual(self.b._all()[0]["body"], "second")

    def test_a_different_key_is_a_different_ticket(self):
        self.b.open("a", "t", "x")
        self.b.open("b", "t", "x")
        self.assertEqual(len(self.b._all()), 2)

    def test_note_and_close_address_by_key_not_by_number(self):
        self.b.open("k", "t", "x")
        self.assertTrue(self.b.note("k", "hello")[0])
        self.assertTrue(self.b.close("k", "done")[0])
        self.assertEqual(self.b.list(), [])

    def test_acting_on_a_missing_key_fails_rather_than_inventing_one(self):
        ok, why = self.b.note("nope", "x")
        self.assertFalse(ok)
        self.assertIn("nope", why)


class Swappable(unittest.TestCase):
    def test_every_backend_implements_the_whole_verb_set(self):
        # The contract IS the four verbs. A backend missing one fails at the
        # call site, in production, on the verb nobody exercised.
        for name, cls in t.BACKENDS.items():
            for verb in ("open", "note", "close", "assign", "list", "available"):
                self.assertTrue(callable(getattr(cls, verb, None)),
                                f"{name} backend is missing {verb}()")

    def test_an_unknown_backend_is_refused_not_defaulted(self):
        with self.assertRaises(SystemExit):
            t.get_backend("linear-someday")

    def test_the_none_backend_says_it_discarded(self):
        ok, why = t.NoneBackend().open("k", "t", "b")
        self.assertTrue(ok)
        self.assertIn("discarded", why)

    def test_github_without_a_repo_is_unavailable_rather_than_silently_wrong(self):
        b = t.GitHubBackend(repo="")
        b.repo = ""
        ok, why = b.available()
        self.assertFalse(ok)
        self.assertIn("repo", why)


class ListContract(unittest.TestCase):
    """The fields and ORDER a caller may rely on.

    The first consumer assumed both and got them wrong in opposite directions —
    body was absent everywhere, and ordering was newest-first on GitHub and
    oldest-first on file. A seam exists to stop exactly that, so the contract is
    asserted rather than described.
    """

    def test_list_returns_the_documented_fields(self):
        b = t.FileBackend(os.path.join(tempfile.mkdtemp(), "t.jsonl"))
        b.open("k", "title", "the body", ["l"])
        row = b.list()[0]
        for f in ("number", "title", "body", "labels", "assignees"):
            self.assertIn(f, row, f"list() must return {f}")
        self.assertEqual(row["body"], "the body",
                         "a caller cannot read a handoff without the body")

    def test_list_is_oldest_first(self):
        b = t.FileBackend(os.path.join(tempfile.mkdtemp(), "t.jsonl"))
        b.open("first", "first", "x")
        b.open("second", "second", "x")
        self.assertEqual([r["title"] for r in b.list()], ["first", "second"],
                         "a queue that serves the newest item starves the oldest")

    def test_the_claim_is_an_agent_label_not_the_github_assignee(self):
        # Found by testing GitHub rather than assuming: assignees must be real
        # accounts, and `gh` EXITS 0 when it rejects one — so a returncode check
        # reports success while claiming nobody. Under ADR 0012 the claim IS the
        # mutual exclusion, so that silently re-serves the ticket forever.
        b = t.FileBackend(os.path.join(tempfile.mkdtemp(), "t.jsonl"))
        b.open("k", "t", "x")
        b.assign("k", "dex-the-dispatcher")
        row = b.list()[0]
        self.assertIn("agent:dex-the-dispatcher", row["labels"])
        self.assertEqual(row["assignees"], ["dex-the-dispatcher"],
                         "assignees is DERIVED from the agent: label, so the "
                         "contract reads identically across backends")

    def test_reassignment_replaces_rather_than_accumulates(self):
        # Two agent: labels on one ticket is two claims, which is the failure.
        b = t.FileBackend(os.path.join(tempfile.mkdtemp(), "t.jsonl"))
        b.open("k", "t", "x")
        b.assign("k", "a1")
        b.assign("k", "a2")
        self.assertEqual(b.list()[0]["assignees"], ["a2"])

    def test_assign_marks_the_ticket_claimed(self):
        b = t.FileBackend(os.path.join(tempfile.mkdtemp(), "t.jsonl"))
        b.open("k", "t", "x")
        self.assertEqual(b.list()[0]["assignees"], [])
        b.assign("k", "agent-1")
        self.assertEqual(b.list()[0]["assignees"], ["agent-1"],
                         "assignment IS the claim (ADR 0012)")

    def test_github_assign_verifies_the_label_landed(self):
        # The structural guarantee: assign() must READ BACK, not trust an exit
        # code, because gh returns 0 on a rejected edit.
        import ast, inspect
        src = inspect.getsource(t.GitHubBackend.assign)
        tree = ast.parse(src.lstrip())
        calls = [ast.unparse(n) for n in ast.walk(tree) if isinstance(n, ast.Call)]
        self.assertTrue(any("issue" in c and "view" in c for c in calls),
                        "assign() must re-read the ticket to confirm the claim")
        self.assertFalse(any("returncode" in c for c in calls),
                         "a returncode check is exactly what fails here")


class KeyMarker(unittest.TestCase):
    def test_the_key_is_carried_in_the_body_as_an_html_comment(self):
        # That is what makes the GitHub backend able to find its own ticket
        # again without a side database — and a reader never sees it.
        m = t.KEY_MARK.format("some/key")
        self.assertTrue(m.startswith("<!--") and m.endswith("-->"))
        self.assertIn("some/key", m)


if __name__ == "__main__":
    unittest.main(verbosity=2)
