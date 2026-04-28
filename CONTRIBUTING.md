# Contributing to Mapilio Kit

Thanks for your interest in improving Mapilio Kit! This document explains how
to set up your environment, how the project is organised, and what we expect
from contributions.

## Getting Started

1. **Fork & clone**
   ```bash
   git clone https://github.com/<your-user>/mapilio-kit-v2.git
   cd mapilio-kit-v2
   ```

2. **Create a virtual environment** (Python 3.8+ supported, 3.10+ recommended):
   ```bash
   python -m venv .venv
   source .venv/bin/activate          # Windows: .venv\Scripts\activate
   python -m pip install --upgrade pip
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install pytest pytest-cov ruff black pre-commit
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env       # edit if you need Sentry / telemetry
   ```

5. **Install pre-commit hooks** (optional but recommended):
   ```bash
   pre-commit install
   ```

## Branching & commits

- Open feature branches from `main`:
  ```bash
  git checkout -b feature/<short-description>
  git checkout -b fix/<short-description>
  ```
- Use clear, imperative commit messages: `"Fix GPX parser for sub-second timestamps"`.
- Squash trivial fixups before opening the PR.

## Running the test suite

```bash
pytest                       # unit tests only (fast, no external tools)
pytest --run-integration     # includes tests that need ffmpeg / exiftool
pytest --cov=mapilio_kit     # with coverage report
```

Heavy optional dependencies (`calculation`, GoPro binaries) are stubbed in
`tests/conftest.py` so the unit tests run on a clean machine. If you add a
test that needs a real binary, mark it with
`@pytest.mark.integration` so it's skipped by default.

## Linting & formatting

We use `ruff` for linting/imports and `black` for formatting:

```bash
ruff check mapilio_kit tests
ruff check --fix mapilio_kit tests
black mapilio_kit tests
```

Both tools are configured in `pyproject.toml` and run automatically via
`pre-commit`.

## Pull requests

Before opening a PR, make sure:

- [ ] Tests pass locally (`pytest`).
- [ ] Lint is clean (`ruff check`).
- [ ] You've added/updated tests for any behaviour change.
- [ ] User-visible changes are noted in the PR description.
- [ ] No secrets, tokens, or credentials are committed (the `.gitignore`
      excludes `.env`; double-check with `git status`).

Once green, open a PR against `main` and request review. CI runs the test
suite on Python 3.9 / 3.10 / 3.11 / 3.12 — please keep all of those green.

## Where to make changes

A short tour of the codebase lives in
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md). The CLI commands and their
arguments are documented in [`docs/CLI.md`](docs/CLI.md).

## License

This project is licensed under the MIT License — see [`LICENSE`](LICENSE).
