#!/usr/bin/env python3
"""Corpus for the aggregate context-budget check.

The behaviours worth pinning are the ones that make it honest rather than
decorative: bands (so a marginal overshoot warns instead of failing), the
ancestor-chain walk (the cost a repo pays for a parent CLAUDE.md it never
mentions), @import following, and never silently dropping a lens it cannot
measure — that last one is how an aggregate check understates the real total.

    python -m unittest tests.test_context_budget
"""
import os, sys, json, tempfile, importlib.util, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SPEC = importlib.util.spec_from_file_location(
    "context_budget", os.path.join(HERE, "..", "scripts", "context_budget.py"))
cb = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(cb)


class Bands(unittest.TestCase):
    def test_under_target_is_ok(self):
        self.assertEqual(cb.band(100, 1000), "ok")

    def test_at_target_warns_rather_than_fails(self):
        # A 1% overshoot must not turn the build red, or the budget gets raised
        # to silence it rather than respected.
        self.assertEqual(cb.band(1010, 1000), "WARN")

    def test_well_over_target_fails(self):
        self.assertEqual(cb.band(1250, 1000), "FAIL")

    def test_fail_boundary_is_the_documented_ratio(self):
        self.assertEqual(cb.band(int(1000 * cb.FAIL_RATIO), 1000), "FAIL")
        self.assertEqual(cb.band(int(1000 * cb.FAIL_RATIO) - 1, 1000), "WARN")


class AlwaysLoadedChain(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.parent = self.tmp.name
        self.repo = os.path.join(self.parent, "repo")
        os.makedirs(self.repo)

    def tearDown(self):
        self.tmp.cleanup()

    def test_counts_the_ancestor_file_the_repo_never_mentions(self):
        # The parent CLAUDE.md loads into every repo beneath it. A repo that
        # carries no instruction file of its own still pays for it.
        open(os.path.join(self.parent, "CLAUDE.md"), "w").write("x" * 500)
        files = cb.always_loaded(self.repo, stop_at=self.parent)
        self.assertEqual(sum(f["chars"] for f in files), 500)

    def test_follows_at_imports(self):
        open(os.path.join(self.repo, "CLAUDE.md"), "w").write("@AGENTS.md\n")
        open(os.path.join(self.repo, "AGENTS.md"), "w").write("y" * 300)
        files = cb.always_loaded(self.repo, stop_at=self.parent)
        imported = [f for f in files if f.get("via")]
        self.assertTrue(imported, "the @import target was not counted")
        self.assertEqual(imported[0]["chars"], 300)

    def test_a_file_is_counted_once(self):
        open(os.path.join(self.repo, "CLAUDE.md"), "w").write("@AGENTS.md\n@AGENTS.md\n")
        open(os.path.join(self.repo, "AGENTS.md"), "w").write("z" * 100)
        files = cb.always_loaded(self.repo, stop_at=self.parent)
        self.assertEqual(len([f for f in files if f["path"].endswith("AGENTS.md")]), 1)


class LensAccounting(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        self.repo = os.path.join(self.root, "repo")
        os.makedirs(os.path.join(self.repo, ".engineering-standard"))
        os.makedirs(os.path.join(self.root, "overlay", "references"))

    def tearDown(self):
        self.tmp.cleanup()

    def _cfg(self, body):
        open(os.path.join(self.repo, ".engineering-standard", "config.yml"),
             "w", encoding="utf-8").write(body)

    def test_unmeasurable_lenses_are_reported_not_dropped(self):
        # A lens with no file in our overlay still costs context. Dropping it
        # silently would understate the total — the exact failure this check
        # exists to prevent.
        open(os.path.join(self.root, "overlay", "references", "mine.md"),
             "w").write("m" * 400)
        self._cfg("overlay: ../overlay\nlenses: [mine, base-only-lens]\n")
        measured, overlay, external = cb.lens_files(self.repo)
        self.assertEqual([m["lens"] for m in measured], ["mine"])
        self.assertEqual(external, ["base-only-lens"])

    def test_no_overlay_means_every_lens_is_external(self):
        self._cfg("lenses: [pragmatic-principles, code-smells]\n")
        measured, overlay, external = cb.lens_files(self.repo)
        self.assertEqual(measured, [])
        self.assertEqual(len(external), 2)


class RealRepo(unittest.TestCase):
    def test_json_shape_is_stable(self):
        import io, contextlib
        buf = io.StringIO()
        repo = os.path.join(HERE, "..")
        with contextlib.redirect_stdout(buf):
            cb.report(repo, as_json=True)
        d = json.loads(buf.getvalue())
        for key in ("repo", "always_loaded", "lenses", "split_candidates", "merge_candidates"):
            self.assertIn(key, d)
        self.assertIn("unmeasured_base_skill_lenses", d["lenses"])


if __name__ == "__main__":
    unittest.main()
