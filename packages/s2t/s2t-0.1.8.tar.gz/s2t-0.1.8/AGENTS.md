# Repository Guidelines

## Project Structure & Module Organization
- `src/transcriber/` — application code (CLI, core modules, utils).
- `tests/` — pytest test suite; fixtures under `tests/fixtures/`.
- `scripts/` — maintenance/dev scripts (one task per file).
- `assets/` — sample media and static assets used in docs/tests.
- `docs/` — user and developer docs.
- `data/` — local runtime artifacts (ignored via `.gitignore`).

## Build, Test, and Development Commands
Prefer Make targets when available:
- `make setup` — create venv and install app + dev deps.
- `make run ARGS=\"...\"` — run the CLI locally with arguments.
- `make test` — run tests; show failures concisely.
- `make lint` — static checks (ruff/flake8, mypy) and style checks.
- `make format` — auto-format code (black) in-place.
If no Makefile: `python -m venv .venv && source .venv/bin/activate && pip install -e .[dev]`, then `pytest -q`, `ruff check .`, `black --check .`.

## Coding Style & Naming Conventions
- Python 3.11+, 4-space indentation, type hints required.
- Naming: `snake_case` for modules/functions/vars, `PascalCase` for classes.
- Docstrings: concise, Google-style; include argument/return types when helpful.
- Tools: `black` (format), `ruff` (lint), `mypy` (types). Keep imports sorted.

## Testing Guidelines
- Framework: `pytest` with `pytest-cov`.
- Place tests mirroring package paths; name files `test_*.py`.
- Aim for ≥90% coverage on core modules; run `pytest --cov=src/transcriber`.
- Include edge cases (empty/long inputs, I/O errors). Use fixtures for media samples.

## Commit & Pull Request Guidelines
- Use Conventional Commits: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`.
- Keep commits focused; include rationale in body when non-trivial.
- PRs: clear description, linked issues, screenshots or sample CLI output when applicable, and updated tests/docs.

## Security & Configuration Tips
- Never commit API keys or raw user data. Use `.env` and provide `.env.example`.
- Sanitize example assets; large files belong outside the repo or via Git LFS.

## Agent-Specific Instructions
- Scope: applies to the entire repository.
- Keep patches minimal and targeted; update tests/docs alongside code.
- Follow the structure and commands above; avoid introducing new tools without discussion.
