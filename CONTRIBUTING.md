# Contributing

Thanks for taking the time. This project keeps a small, predictable shape.

## Setup

```
pip install -r requirements-dev.txt
```

## Before you open a pull request

- Keep public API in `src/tzoffset/__init__.py`; internals live in `_`-prefixed modules.
- Add a test for the behaviour you change, one behaviour per test. What the suite
  touches for real: it reads files (the README, the GUIDE, the recorded vectors, the time
  zone database, and the fetched third-party sources, whose tests skip while those are
  absent); the command line tests of `--zone` without `--at` read the real clock, in
  zones whose offset has not changed in decades; and the wheel test (`TZOFFSET_E2E=1`)
  builds the package, which downloads the build backend, and installs it into a new
  virtual environment. Nothing else uses the network.
- Run `scripts/check.ps1` (format, lint, types, tests) and make sure it passes.
- One logical change per commit, imperative subject line.

Open an issue first if the change is large or shifts the public API.
