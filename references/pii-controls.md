# PII controls (house lens)

A lens for keeping personal data out of repositories — and for the fact that
once it is in git history, it is effectively permanent.

Each item: the risk, what to check, the fix.

## The two facts everything follows from

**1. History is forever.** Rewriting a pushed repo is disruptive; once it is
public, cloned, or forked, you cannot guarantee removal. The only cheap moment
is *before the commit exists*. Every control here is therefore preventive.

**2. Detection is a net, not a wall.** Structured PII — SSN, cards, email,
phone — is caught reliably. **Names and street addresses are not.** A real
incident in this workspace was an address in a docstring, which every structured
detector misses. So PII must be absent *by construction*; scanning is the
backstop, never the strategy.

Any design that leads with scanning is one clever formatting away from failure.

## Classify the data, then the repo

| Class | What | Examples |
|---|---|---|
| **P0** | synthetic or none | generated fixtures, `«PERSON_003»` tokens |
| **P1** | low | internal names, org email addresses |
| **P2** | personal | real names, addresses, personal contact details |
| **P3** | sensitive | financial, health, government ID, credentials |

Repos are already classified **Tier I** (internal) or **Tier P** (portable —
public, or outside contributors) by `agent-context-architecture`. The required
mechanism is the intersection:

| | Tier I (private) | Tier P (public / external) |
|---|---|---|
| **P0** | — | — |
| **P1** | gitignore | externalize |
| **P2** | externalize | tokenize, or exclude entirely |
| **P3** | tokenize + vault | **never** — does not belong in the repo |

**Public repos are always one step stricter.** The rule derives from two facts
you already know about a repo, so it scales without per-repo judgement.

## The four mechanisms

- **Gitignore** — whole files of real data live at ignored paths (`.local/`,
  `data/private/`, `*.private.*`). Cheap. Useless against PII embedded *inside*
  source, and `git add -f` defeats it.
- **Externalize** — code references a key; the value lives in env or an
  untracked config. This is the fix for the docstring-address case.
- **Tokenize + vault** — stable tokens in the repo, real values outside it,
  rehydrated after processing. Strongest; needs vault discipline.
- **Synthetic fixtures** — test data is generated, never real. Narrow, but test
  fixtures are a common leak vector.

## Enforce at commit time, gate in CI

- **Risk:** a control that is configured but not installed runs zero times. Two
  repos in this workspace carried a `.pre-commit-config.yaml` with **no hook
  installed** — `pre-commit install` had never been run, so the gate had never
  once fired. Both had `detect-private-key`, which finds SSH keys and no PII at all.
- **Check:** does `.git/hooks/pre-commit` exist, is it executable, and is it the
  PII gate? Does CI run the scan? `install_controls.py --verify` answers all three.
- **Fix:** `scripts/install_controls.py <repo>` installs a **native** hook (no
  framework dependency), preserves and chains any existing hook, and adds a
  `local` entry to `.pre-commit-config.yaml` when one exists — because
  `pre-commit install` overwrites `.git/hooks/pre-commit` and would otherwise
  silently remove the gate.

**CI is the real gate.** Hooks are local, bypassable with `--no-verify`, and — as
observed — frequently uninstalled. The hook is fast feedback; CI is enforcement.

```bash
python scripts/pii_scan.py . --tree --visibility public --max-tier P1   # CI
```

## The commit message is unscanned surface

- **Risk:** gitignore, externalization, tokenization, and synthetic fixtures all
  protect **files**. A commit message is prose written *about* those files — it is
  permanent, public, replicated to every clone and fork, and until now no control
  in this lens looked at it. The observed leak was **narrative**: a private
  document quoted verbatim to explain a fix, plus proper nouns naming who it
  belonged to. Structured detectors miss both by design (fact 2 above), and the
  file-level gate never sees the message at all.
- **Why it recurs:** defects are usually found by running *real* data through the
  system, so the natural way to explain a fix is to describe the real thing that
  broke. The pull toward specificity is strongest exactly where the data is most
  sensitive.
- **Check:** `python scripts/pii_scan.py . --message <file>` — installed as a
  `commit-msg` hook by `install_controls.py`, and covered by `--verify`.
- **Fix:** describe the **defect class and the fix**, never the specifics.
  *"Developer caught an incorrect entry; additional checks added"* carries
  everything a reader of the history needs. Reproduction detail belongs in a test,
  where it is synthetic, or in ignored notes.

Three layers, cheapest first:

| Layer | Catches | Configuration |
|---|---|---|
| the normal detectors | an address, phone, or key pasted into a message | none |
| `.pii-terms` | proper nouns — employer, client, patient, codename | one term per line, **gitignored** |
| quoted-run matching | a phrase quoted verbatim from a gitignored file | none |

The third needs no setup and generalizes: **if you quoted something that lives in
a file you deliberately kept out of the repo, you just put it in the repo.** It
costs nothing on the common path, because a message with no quoted run never
opens a file.

`.pii-terms` must be gitignored, and `install_controls.py` adds it to the block
automatically — a *tracked* list of the words you are hiding is itself the
disclosure.

### Write the vocabulary once, not once per repo

`load_terms()` reads the **union** of three files, most global first:

| File | Scope |
|---|---|
| `$PII_TERMS_HOME/.pii-terms`, else `~/.pii-terms` | the machine — employer, client, codenames |
| `<parent of repo>/.pii-terms` | the workspace holding sibling repos |
| `<repo>/.pii-terms` | that repo only (the original behaviour) |

**Put the standing vocabulary in the global file.** A term listed only in the
repo where it was first noticed protects that repo and leaves every sibling
exposed — and this failed silently in the worst way: audited across a real
fleet, *no* repo had a `.pii-terms` at all, so the feature was protecting
nothing anywhere while appearing to be configured.

The global file also lives **outside every repo**, so it cannot be committed to
a public one. That is what makes it safe to write down real client names.

⚠️ **The code change is not the whole job.** An empty `~/.pii-terms` catches
nothing. Someone has to decide what belongs in it, and until that happens this
layer is inert.

### A gate that cannot run must not stay quiet

Both hooks bake in an absolute path to the scanner. If it stops resolving —
`ai-standards` moved, renamed, cloned to another machine — the hooks **fail
closed**: they block the commit and name the path they looked for.

They did not always. The original shape was `if [ -f "$SCAN" ]; then … fi;
exit 0`, which passed the commit **silently** whenever the scanner was absent.
A backstop that disappears without saying so is worse than no backstop, because
the team believes it is covered. `tests/test_hook_behaviour.py` runs the
generated hook through a real shell and pins this.

`PII_GATE=off git commit …` is the deliberate escape hatch for a genuinely
toolless environment. It announces itself on stderr — a silent bypass would be
indistinguishable from the bug it replaced.

**Both hooks are verified separately.** `pre-commit install` overwrites
`.git/hooks/pre-commit` and leaves `commit-msg` untouched, so a repo can end up
with one gate live and the other silently gone.

## Never print what you found

- **Risk:** a scanner that echoes matched values into a CI log has published
  them somewhere more widely readable than the repo — build logs are often
  world-readable and retained long after the finding is fixed.
- **Check:** does any tooling, log line, or bug report quote the matched text?
- **Fix:** report **type, file, line** only. `pii_scan.py` findings carry no
  value field at all, so it cannot regress into leaking one.

## The scanner respects .gitignore — that is the point

- **Risk:** the externalize control deliberately puts real data in gitignored
  paths (`personal/`, `data/private/`). A scanner that walks the whole
  filesystem flags exactly the data the control just protected, and fights its
  own model.
- **Check:** does the tree scan skip gitignored files? `pii_scan.py --tree` lists
  `git ls-files --cached --others --exclude-standard`, so gitignored real data is
  not scanned; only what would actually enter the repo is.
- **Fix:** keep real data in gitignored paths and it is correct by construction.
  History mode still scans everything ever committed, because the ignore rule may
  post-date the leak.

## Security-tool test fixtures are a known false-positive class

- **Risk:** a guardrail's own tests contain the patterns it detects
  (`outputScan("AKIA…")`). A secret/PII scanner flags them, every time.
- **Check:** are the findings in `tests/` asserting *detection*?
- **Fix:** a reviewed `.pii-allow` entry, or delegate secrets to gitleaks, whose
  baseline workflow is built for exactly this. Do not special-case it in regex —
  that path has no end (see the decision record for how far it goes).

## Tune placeholders or the gate gets switched off

- **Risk:** template and fixture files are full of `555-123-4567` and
  `user@example.com`. A scanner that flags them produces noise on every commit,
  and a noisy gate gets bypassed — permanently, and for real findings too.
- **Check:** run the scan across the whole repo. Is every finding real?
- **Fix:** `.pii-allow` holds reviewed-safe regexes, one per line. Widen the
  built-in placeholder list rather than allowlisting case by case: the NANP 555
  range, `000`/`123`/`999` prefixes, `example.com`, `<placeholder>` forms.

## History findings cannot be fixed by editing the file

- **Risk:** removing a value in a new commit leaves the old blob reachable
  forever. The fix feels done and isn't.
- **Check:** `pii_scan.py <repo> --history`. Scan every repo once; re-scan
  periodically, since detection improves over time.
- **Fix, in order of preference:**
  1. **If the repo is private and unshared** — rewrite history
     (`git filter-repo`), force-push, and confirm no forks exist.
  2. **If it is public or forked** — assume the data is disclosed. Rotate
     anything rotatable (credentials, tokens), and handle the rest as a
     disclosure, not a code fix. Deleting the repo does not retract forks,
     caches, or archives.
  3. **Either way** — install the commit-time gate first, so remediation isn't
     immediately re-broken.

**Do not force-push a shared repo to fix this without telling collaborators.**
Rewriting shared history breaks every clone, and the rushed re-clone that
follows is its own incident.

## What this lens does not do

It does not make you compliant with anything. GDPR, CCPA, HIPAA and their
relatives impose obligations — lawful basis, retention, deletion rights, breach
notification — that no scanner addresses. This keeps personal data out of source
control. That is one control, not a programme.
