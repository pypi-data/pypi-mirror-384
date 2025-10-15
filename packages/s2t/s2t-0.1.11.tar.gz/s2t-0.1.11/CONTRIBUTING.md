# Contributing

Thanks for contributing! This guide summarizes the setup and common development commands.

## Requirements
- Python 3.11–3.12
- Recommended: project virtualenv via Makefile

## Setup
```
make setup
```

## Common Commands
- Format (auto-fix): `make format` (Ruff fixes + Ruff formatter)
- Lint + type check: `make lint` (Ruff + mypy)
- Tests: `make test`
- Full gate (pre-release): `make check`

## Pre-commit Hooks
Install optional Git hooks locally:
```
make precommit-install
```
Hooks include Ruff (`--fix`), Ruff formatter, mypy, and basic checks.

## Style & Typing
- Formatter: Ruff formatter (Black is not used)
- Linting: Ruff (including import sorting and quality rules)
- Types: mypy; please use type hints consistently

## Project Structure
- App code: `src/s2t/` (CLI, modules, utils)
- Tests: `tests/`
- Scripts: `scripts/`
- Docs: `docs/`
