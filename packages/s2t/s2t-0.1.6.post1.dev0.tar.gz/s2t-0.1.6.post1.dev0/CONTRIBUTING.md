# Contributing

Danke für deinen Beitrag! Hier findest du die wichtigsten Hinweise für Entwicklung und Checks.

## Voraussetzungen
- Python 3.11+
- Empfohlen: Projekt-venv via Makefile

## Setup
```
make setup
```

## Wichtige Befehle
- Formatieren (auto-fix): `make format`  (Ruff Lint-Fixes + Ruff Formatter)
- Lint + Typprüfung (auto-fix + mypy): `make lint`
- Tests: `make test`
- Kombiniert (Gate vor Build/Release): `make check`

## Pre-commit Hooks
Installiere optionale Git-Hooks lokal:
```
make precommit-install
```
Aktive Hooks: Ruff (`--fix`), Ruff Formatter, mypy und Basis-Hooks.

## Stil & Typen
- Formatter: Ruff Formatter (Black wurde entfernt)
- Linting: Ruff (Importsortierung, Qualitätsregeln)
- Typen: mypy; bitte durchgängig Typannotationen nutzen

## Struktur
- App-Code: `src/transcriber/` (CLI, Module)
- Tests: `tests/`
- Scripts: `scripts/`
- Docs: `docs/`

