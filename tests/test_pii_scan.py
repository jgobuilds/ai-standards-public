#!/usr/bin/env python3
"""Labeled corpus for pii_scan.py — every false positive it ever produced is a
permanent regression test here.

pii-scan: ignore-file  (this file is 100% synthetic fixtures by design; the
marker exempts it from the PII gate it exists to test — visible and reviewable).

The scanner shipped with five false-positive classes that were only found by
running it against production repos. That is exactly backwards: a detector
without a labeled corpus is unshipped. Each row below is a case the scanner got
wrong once; the test fails if it regresses.

Fixtures are written to temp dirs at runtime, never committed — a file of
real-shaped SSNs and cards in the repo would (correctly) be blocked by our own
PII gate. stdlib unittest, no pytest, matching the fleet convention.

    python -m unittest tests.test_pii_scan
"""
import os, sys, json, tempfile, subprocess, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCANNER = os.path.join(HERE, "..", "scripts", "pii_scan.py")


def scan(content, *, visibility="public", max_tier="P0", filename="x.py", extra=None):
    """Write content to a temp file, scan it, return (findings, raw_stdout)."""
    with tempfile.TemporaryDirectory() as d:
        with open(os.path.join(d, filename), "w", encoding="utf-8") as f:
            f.write(content)
        for name, body in (extra or {}).items():
            with open(os.path.join(d, name), "w", encoding="utf-8") as f:
                f.write(body)
        cmd = [sys.executable, SCANNER, d, "--tree", "--no-gitleaks",
               "--visibility", visibility, "--max-tier", max_tier, "--json"]
        r = subprocess.run(cmd, capture_output=True, text=True)
        return json.loads(r.stdout)["findings"], r.stdout


def types(findings):
    return {f["type"] for f in findings}


# (label, content, expected-detector). Must be caught.
MUST_CATCH = [
    ("plain ssn",         'ssn = "451-22-8837"',                  "ssn"),
    ("plain card",        'c = "4532015112830366"',               "credit_card"),
    ("hyphenated card",   'c = "4532-0151-1283-0366"',            "credit_card"),
    ("rsa private key",   'k = "-----BEGIN RSA PRIVATE KEY-----"', "private_key"),
    ("aws access key",    'k = "AKIAQZ7X9W3V5N2R8KP4"',           "aws_key"),
    ("real-shaped phone", 'p = "617-482-9930"',                   "phone_us"),
    ("street address",    's = "88 Maple Street"',                "street_address"),
    ("real email",        'e = "j.smith@acme.co"',                "email"),
    ("date of birth",     'dob: 1984-03-02',                      "date_of_birth"),
]

# Must stay silent — placeholders, plus the five FP classes found in production.
MUST_STAY_SILENT = [
    ("555 phone",         'p = "555-123-4567"'),
    ("(555) phone",       'p = "(555) 867-5309"'),
    ("123 phone",         'p = "123-456-7890"'),
    ("example.com email", 'e = "user@example.com"'),
    ("placeholder ssn",   's = "123-45-6789"'),
    ("test card",         'c = "4111 1111 1111 1111"'),
    ("Jane Doe",          'name = "Jane Doe"'),
    ("PII token",         'x = "«PERSON_003»"'),
    ("angle placeholder", 'e = "<your_email>"'),
    ("your-email form",   'contact = "your-email@..."'),
    ("webhookId 16-digit", '"webhookId": "4532015112830366"'),
    ("UUID numeric tail", '"id": "abababab-1111-2222-3333-444444444444"'),
    ("standard UUID",     'u = "550e8400-e29b-41d4-a716-446655440000"'),
    # Luhn-valid fraction, so this actually exercises the coordinate guard.
    ("lat/long coordinate", 'poly = [-72.4532015112830366, 41.9]'),
    ("sha-keyed digits",  '"sha": "4532015112830366"'),
]


class PositiveDetection(unittest.TestCase):
    def test_catches_real_pii(self):
        for label, content, expected in MUST_CATCH:
            with self.subTest(label):
                found = types(scan(content)[0])
                self.assertIn(expected, found,
                              f"{label!r}: expected {expected}, got {found or 'nothing'}")


class NoFalsePositives(unittest.TestCase):
    def test_placeholders_and_fp_classes_stay_silent(self):
        for label, content in MUST_STAY_SILENT:
            with self.subTest(label):
                found = types(scan(content)[0])
                self.assertEqual(found, set(),
                                 f"{label!r} produced a false positive: {found}")


class StructuralGuarantees(unittest.TestCase):
    def test_never_prints_a_matched_value(self):
        # The single most important property: a finding carries no value field,
        # and the raw output never contains the matched secret.
        secret = "451-22-8837"
        findings, raw = scan(f'ssn = "{secret}"')
        self.assertTrue(findings, "should have caught the SSN")
        self.assertNotIn(secret, raw, "MATCHED VALUE LEAKED INTO OUTPUT")
        for f in findings:
            self.assertNotIn("value", f, "finding must carry no value field")

    def test_hyphenated_card_is_not_a_uuid(self):
        # The regression that nearly slipped: the UUID suppression must not eat a
        # real hyphen-grouped card (a card has no hex letters).
        findings, _ = scan('real = "4532-0151-1283-0366"\n'
                           'fake = "abababab-1111-2222-3333-444444444444"')
        self.assertEqual(sum(1 for f in findings if f["type"] == "credit_card"), 1,
                         "exactly the real card should be caught, not the UUID")

    def test_public_is_stricter_than_private(self):
        addr = 'home = "88 Maple Street, Anytown"'
        pub = types(scan(addr, visibility="public")[0])
        priv = types(scan(addr, visibility="private")[0])
        self.assertIn("street_address", pub, "public must catch low-confidence PII")
        self.assertNotIn("street_address", priv,
                         "private runs high-confidence only, so address is skipped")

    def test_tree_scan_respects_gitignore(self):
        # The externalize control PUTS real data in gitignored paths on purpose.
        # A tree scan that flags them fights its own model.
        with tempfile.TemporaryDirectory() as d:
            subprocess.run(["git", "-C", d, "init", "-q"], check=True)
            os.makedirs(os.path.join(d, "personal"))
            with open(os.path.join(d, ".gitignore"), "w") as f:
                f.write("/personal/\n")
            with open(os.path.join(d, "personal", "real.py"), "w") as f:
                f.write('ssn = "451-22-8837"\n')
            r = subprocess.run(
                [sys.executable, SCANNER, d, "--tree", "--no-gitleaks",
                 "--max-tier", "P0", "--json"], capture_output=True, text=True)
            findings = json.loads(r.stdout)["findings"]
            self.assertEqual(findings, [],
                             "gitignored real data must not be scanned in tree mode")

    def test_staged_scan_decodes_utf8_not_the_locale_codepage(self):
        # Regression: git() used text=True with no encoding=, so a staged blob
        # was decoded with the LOCALE default — cp1252 on stock Windows. Every
        # non-ASCII byte came back as mojibake, which meant a .pii-allow regex
        # containing a non-ASCII character silently stopped matching and the
        # scan reported CLEAN because it never saw the text it was looking for.
        # A security gate that fails open on a codepage is worse than none.
        #
        # Asserted through the real staged path (git add + --staged), because
        # that is the layer that broke; a unit test on the helper would have
        # passed on Linux and told us nothing.
        with tempfile.TemporaryDirectory() as d:
            subprocess.run(["git", "-C", d, "init", "-q"], check=True)
            with open(os.path.join(d, ".pii-allow"), "w", encoding="utf-8") as f:
                f.write("« reviewed fixture »\n")
            with open(os.path.join(d, "f.py"), "w", encoding="utf-8") as f:
                f.write('ssn = "451-22-8837"  # « reviewed fixture »\n')
            subprocess.run(["git", "-C", d, "add", "-A"], check=True,
                           capture_output=True)
            r = subprocess.run(
                [sys.executable, SCANNER, d, "--staged", "--no-gitleaks",
                 "--max-tier", "P0", "--json"], capture_output=True, text=True)
            self.assertEqual(json.loads(r.stdout)["findings"], [],
                             "a non-ASCII .pii-allow entry must match staged content")

            # And the allowlist must still be an allowlist: the same SSN on a
            # line WITHOUT the marker has to block. Otherwise this test would
            # pass just as well against a scanner that found nothing at all.
            with open(os.path.join(d, "g.py"), "w", encoding="utf-8") as f:
                f.write('ssn = "451-22-8837"\n')
            subprocess.run(["git", "-C", d, "add", "-A"], check=True,
                           capture_output=True)
            r2 = subprocess.run(
                [sys.executable, SCANNER, d, "--staged", "--no-gitleaks",
                 "--max-tier", "P0", "--json"], capture_output=True, text=True)
            paths = [f["file"] for f in json.loads(r2.stdout)["findings"]]
            self.assertIn("g.py", paths, "an unmarked value must still be caught")
            self.assertNotIn("f.py", paths)

    def test_max_tier_gates_blocking(self):
        # A P1 email should be a finding but NOT blocking under max-tier P1.
        d = scan('e = "j@acme.co"', max_tier="P1", visibility="private")
        raw = json.loads(d[1])
        self.assertEqual(raw["blocking"], 0, "P1 email must not block a P1 repo")
        d3 = scan('ssn = "451-22-8837"', max_tier="P1", visibility="private")
        self.assertGreater(json.loads(d3[1])["blocking"], 0,
                           "P3 SSN must block a P1 repo")


if __name__ == "__main__":
    unittest.main(verbosity=2)


# --------------------------------------------------------------- commit messages
def scan_message(message, *, terms=None, ignored=None, visibility="public", max_tier="P1"):
    """Scan a commit message inside a throwaway git repo.

    A real repo is required, not a bare directory: the quoted-run layer asks git
    which files are ignored, so a fake tree would silently exercise nothing.
    """
    with tempfile.TemporaryDirectory() as d:
        subprocess.run(["git", "init", "-q", d], capture_output=True)
        if ignored:
            with open(os.path.join(d, ".gitignore"), "w", encoding="utf-8") as f:
                f.write("notes/\n.pii-terms\n")
            os.makedirs(os.path.join(d, "notes"), exist_ok=True)
            for name, body in ignored.items():
                with open(os.path.join(d, "notes", name), "w", encoding="utf-8") as f:
                    f.write(body)
        if terms:
            with open(os.path.join(d, ".pii-terms"), "w", encoding="utf-8") as f:
                f.write("\n".join(terms))
        msg = os.path.join(d, "MSG")
        with open(msg, "w", encoding="utf-8") as f:
            f.write(message)
        cmd = [sys.executable, SCANNER, d, "--message", msg, "--no-gitleaks",
               "--visibility", visibility, "--max-tier", max_tier, "--json"]
        r = subprocess.run(cmd, capture_output=True, text=True)
        return json.loads(r.stdout)["findings"]


class CommitMessageScanning(unittest.TestCase):
    """The message is prose ABOUT the protected files, and is otherwise unscanned."""

    def test_private_term_is_caught(self):
        f = scan_message("feat: onboard Northgate Logistics", terms=["Northgate Logistics"])
        self.assertIn("private_term", types(f))

    def test_quoted_run_from_an_ignored_file_is_caught_without_configuration(self):
        f = scan_message(
            'fix: timeline\n\nThe note said "we need the migration done by Q3".',
            ignored={"n.md": 'The client said "we need the migration done by Q3" firmly.'},
        )
        self.assertIn("quoted_from_ignored_file", types(f))

    def test_a_quote_not_present_in_any_ignored_file_is_left_alone(self):
        f = scan_message(
            'fix: docs\n\nThe README says "run the installer before the tests".',
            ignored={"n.md": "unrelated private content"},
        )
        self.assertNotIn("quoted_from_ignored_file", types(f))

    def test_ordinary_engineering_message_is_clean(self):
        f = scan_message("sweep: throttle per domain\n\nHold the lock across the sleep.")
        self.assertEqual(f, [])

    def test_a_possessive_is_not_treated_as_a_quote(self):
        """Treating ' as a delimiter makes an ordinary possessive close a quote
        opened earlier in the sentence. A gate with false positives gets disabled."""
        f = scan_message(
            "fix: parser\n\nThe filter matched any \"word:\" prefix, which is this repo's own.",
            ignored={"n.md": "prefix, which is this repo"},
        )
        self.assertNotIn("quoted_from_ignored_file", types(f))

    def test_comment_lines_are_not_scanned(self):
        """git strips them, and --verbose injects the whole diff as comments."""
        f = scan_message("feat: ok\n# Northgate Logistics appears only here\n",
                         terms=["Northgate Logistics"])
        self.assertEqual(f, [])


# --- shared vocabulary -------------------------------------------------------
# A term listed only in the repo where it was noticed protects that repo alone,
# so the same employer or client name stays exposed in every sibling. Measured
# before this change: NO repo had a .pii-terms, so the feature protected nothing
# anywhere. These tests pin the merge that makes one global list cover all of it.
import importlib.util

_SPEC = importlib.util.spec_from_file_location("pii_scan", SCANNER)
_ps = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_ps)


class SharedVocabulary(unittest.TestCase):
    def setUp(self):
        self._d = tempfile.TemporaryDirectory()
        self.home = os.path.join(self._d.name, "home")
        self.ws = os.path.join(self._d.name, "workspace")
        self.repo = os.path.join(self.ws, "repo")
        for p in (self.home, self.ws, self.repo):
            os.makedirs(p, exist_ok=True)
        self._prev = os.environ.get("PII_TERMS_HOME")
        os.environ["PII_TERMS_HOME"] = self.home

    def tearDown(self):
        if self._prev is None:
            os.environ.pop("PII_TERMS_HOME", None)
        else:
            os.environ["PII_TERMS_HOME"] = self._prev
        self._d.cleanup()

    def write(self, base, *terms):
        with open(os.path.join(base, ".pii-terms"), "w", encoding="utf-8") as f:
            f.write("\n".join(terms) + "\n")

    def test_global_terms_reach_a_repo_with_no_local_file(self):
        """The whole point: name the employer once, protected everywhere."""
        self.write(self.home, "Northgate Logistics")
        self.assertIn("northgate logistics", _ps.load_terms(self.repo))

    def test_repo_local_still_works(self):
        self.write(self.repo, "Blueharbor Trust")
        self.assertIn("blueharbor trust", _ps.load_terms(self.repo))

    def test_all_three_sources_are_unioned(self):
        self.write(self.home, "Northgate Logistics")
        self.write(self.ws, "Fenwick Partners")
        self.write(self.repo, "Blueharbor Trust")
        got = _ps.load_terms(self.repo)
        for t in ("northgate logistics", "fenwick partners", "blueharbor trust"):
            self.assertIn(t, got)

    def test_a_term_in_two_files_appears_once(self):
        self.write(self.home, "Northgate Logistics")
        self.write(self.repo, "northgate logistics")
        self.assertEqual(_ps.load_terms(self.repo).count("northgate logistics"), 1)

    def test_comments_and_short_tokens_are_still_ignored(self):
        self.write(self.home, "# a comment", "abc", "Northgate Logistics")
        got = _ps.load_terms(self.repo)
        self.assertNotIn("# a comment", got)
        self.assertNotIn("abc", got)          # <=3 chars: too noisy to match on

    def test_a_missing_file_is_not_an_error(self):
        self.assertEqual(_ps.load_terms(self.repo), [])

    def test_the_same_file_is_not_read_twice(self):
        """root's parent can BE the home dir; double-reading would be harmless
        but signals the dedupe is gone, which matters once counts are reported."""
        os.environ["PII_TERMS_HOME"] = self.ws
        self.write(self.ws, "Fenwick Partners")
        self.assertEqual(_ps.load_terms(self.repo).count("fenwick partners"), 1)
