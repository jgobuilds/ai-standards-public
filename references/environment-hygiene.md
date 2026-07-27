# Environment & dependency hygiene (house lens)

A lens for how software gets **installed and run**, not how it's written. Most
review lenses look inside the repo; this one looks at the blast radius *outside*
it. Each item: the risk, what to check, the fix.

Applies to every repo. Weight it higher for projects with heavy native
dependencies (GDAL, PDAL, rasterio, torch, opencv), which are the ones most
likely to drag a shared environment somewhere it can't come back from.

## Never install into a shared interpreter

- **The global/system Python is production for some other project.** On this
  machine it is the runtime for real projects — anything without its own venv.
  A "quick" install there is a change to a live system.
- **`pip install X` is never just X.** It resolves a dependency tree and will
  silently upgrade transitive packages another project pins. Installing `pvlib`
  on 2026-07-21 upgraded numpy 1.26.3 → 2.5.1 and pandas → 3.0.2, breaking
  `python-jobspy`'s pins, and additionally pulled in scipy and h5py unasked.
- **Check:** does any install command in scripts, docs, CI, or a README run
  without an activated venv or container? Does onboarding say `pip install -r
  requirements.txt` with no venv step immediately before it?
- **Fix:** venv first, always — including for a one-line experiment.

```bash
python -m venv .venv && .venv/Scripts/python.exe -m pip install -r requirements.txt
```

Throwaway work (spikes, benchmarks, one-offs) gets its venv in a **scratch
directory, not the repo**, so it leaves no trace and nobody commits it.

## Reverting is not the same as restoring

- **Risk:** a partial rollback leaves a *worse* state than the original break.
  Reverting numpy to 1.26.3 left behind a scipy built against numpy ≥ 2.0 —
  installed, imported, and broken, warning on every import.
- **Check:** after any environment repair, enumerate what was newly introduced
  (not just what was changed) and remove it too.
- **Fix:** capture `pip freeze` *before* touching a shared environment. Restore
  by diffing against it, not from memory.

## Verify with tests, not imports

- **Risk:** "the package imports, so it's fine" is the single most common false
  all-clear. Import success proves almost nothing about version compatibility.
- **Check:** was the affected project's test suite actually run after the repair?
- **Fix:** run it. `python -m unittest discover -s tests` / `pytest` / `npm test`.
  A green suite is evidence; a successful import is a guess.

## Pin what you depend on, and know what pins you

- **Risk:** a project with unpinned transitive deps breaks from unrelated
  activity elsewhere on the machine.
- **Check:** is there a lockfile (`requirements.txt` with pins, `uv.lock`,
  `poetry.lock`, `package-lock.json`)? Do direct dependencies pin their own
  critical transitives?
- **Fix:** commit a lockfile. Before upgrading anything shared, check what
  depends on it — `pip index versions`, `pipdeptree`, `npm ls <pkg>`.

## Make the environment reproducible, not documented

- **Risk:** setup instructions in prose drift from reality and only fail for new
  people, who assume it's their fault.
- **Check:** can a clean machine reach a working state in one command?
- **Fix:** a `Makefile`/`justfile` target or `docker compose up` that creates the
  venv, installs pinned deps, and runs the tests. Prefer automating the standard
  over documenting it.

## Native dependencies deserve a container

- **Risk:** GDAL, PDAL, and friends often can't be installed by pip alone on
  Windows and need conda or system libraries. Attempting it anyway produces
  half-installed states that are hard to unwind.
- **Check:** does the project need native geospatial/ML libraries? Is there a
  container or conda environment definition, or just a hopeful `requirements.txt`?
- **Fix:** define the environment in a container image or conda env file and make
  it the supported path. Record which dependencies cannot come from pip, so the
  next person doesn't rediscover it by breaking something.
