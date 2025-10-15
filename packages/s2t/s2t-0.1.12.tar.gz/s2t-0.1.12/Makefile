SHELL := /bin/bash
# Ensure project venv binaries are preferred
PATH := .venv/bin:$(PATH)
# Prefer the project venv if present
PYTHON := $(shell if [ -x .venv/bin/python ]; then echo .venv/bin/python; else command -v python; fi)
PIP := $(PYTHON) -m pip
.PHONY: help setup dev install ensure-dev lint format test check build publish publish-test record list-models clean version precommit-install guard-venv tag

help:
	@echo "Common targets:"
	@echo "  setup          Create/refresh .venv and install dev extras"
	@echo "  dev            Install dev extras into current env"
	@echo "  install        Install package (editable)"
	@echo "  lint           Run ruff (auto-fix) and mypy"
	@echo "  format         Run ruff check --fix and ruff format"
	@echo "  test           Run pytest"
	@echo "  check          Lint + tests (pre-publish gate)"
	@echo "  build          Build sdist/wheel (installs 'build' if missing)"
	@echo "  publish        Upload to PyPI via twine (username=__token__, requires TWINE_PASSWORD)"
	@echo "  publish-test   Upload to TestPyPI via twine (username=__token__, requires TWINE_PASSWORD)"
	@echo "  tag            Create/push git tag (VERSION=x.y.z or auto-bump patch)"
	@echo "  record         Run s2t (passes ARGS='...' to forward options)"
	@echo "  profile        Run s2t with --profile (use ARGS to pass flags)"
	@echo "  list-models    Print whisper.available_models()"
	@echo "  version        Print package version"
	@echo "  precommit-install  Install pre-commit git hooks"

setup: guard-venv
	@if [ ! -x .venv/bin/python ]; then $(PYTHON) -m venv .venv; fi; \
	.venv/bin/python -m pip install -U pip setuptools wheel; \
	.venv/bin/python -m pip install -e '.[dev]'

dev: guard-venv
	$(PIP) install -e '.[dev]'

install: guard-venv
	$(PIP) install -e .

lint: guard-venv ensure-dev
	# Auto-fix what Ruff can, then format, then type-check
	$(PYTHON) -m ruff check . --fix --unsafe-fixes
	$(PYTHON) -m ruff format .
	$(PYTHON) -m mypy src

format: guard-venv ensure-dev
	$(PYTHON) -m ruff check . --fix --unsafe-fixes
	$(PYTHON) -m ruff format .

test: guard-venv ensure-dev
	@$(PYTHON) -m pytest -q || { code=$$?; if [ $$code -eq 5 ]; then echo "No tests collected; treating as success."; exit 0; else exit $$code; fi; }

check: guard-venv ensure-dev lint test

build: guard-venv
	$(MAKE) format
	$(MAKE) lint
	$(PYTHON) -m mypy src
	# Build artifacts (clean dist to avoid duplicate files)
	rm -rf dist
	$(PYTHON) -c 'import importlib.util,sys; sys.exit(0) if importlib.util.find_spec("build") else sys.exit(1)' || $(PIP) install build ; \
	$(PYTHON) -m build $(if $(NO_ISOLATION),--no-isolation,)

publish: guard-venv build
	# Ensure twine is available
	$(PYTHON) -c 'import importlib.util,sys; sys.exit(0) if importlib.util.find_spec("twine") else sys.exit(1)' || $(PIP) install twine ; \
	if [ -z "$$TWINE_PASSWORD" ]; then echo "Error: TWINE_PASSWORD is not set in the environment." >&2; exit 2; fi; \
	env TWINE_USERNAME="__token__" TWINE_PASSWORD="$$TWINE_PASSWORD" twine upload --non-interactive $$TWINE_EXTRA_FLAGS dist/*

publish-test: guard-venv build
	# Ensure twine is available
	$(PYTHON) -c 'import importlib.util,sys; sys.exit(0) if importlib.util.find_spec("twine") else sys.exit(1)' || $(PIP) install twine ; \
	if [ -z "$$TWINE_PASSWORD" ]; then echo "Error: TWINE_PASSWORD is not set in the environment." >&2; exit 2; fi; \
	env TWINE_USERNAME="__token__" TWINE_PASSWORD="$$TWINE_PASSWORD" twine upload --non-interactive --repository testpypi $$TWINE_EXTRA_FLAGS dist/*

record: guard-venv
	@if [ -x .venv/bin/s2t ]; then .venv/bin/s2t $(ARGS); else s2t $(ARGS); fi

profile: guard-venv
	@if [ -x .venv/bin/s2t ]; then .venv/bin/s2t --profile $(ARGS); else s2t --profile $(ARGS); fi

list-models: guard-venv
	$(PYTHON) -c "import whisper; print('\n'.join(sorted(whisper.available_models())))"

clean:
	rm -rf build dist .pytest_cache .mypy_cache .ruff_cache *.egg-info

version: guard-venv
	$(PYTHON) -c "import s2t; print(s2t.__version__)"


ensure-dev:
	@which ruff >/dev/null 2>&1 || $(PIP) install -e '.[dev]'
	@which mypy >/dev/null 2>&1 || true
	@which pytest >/dev/null 2>&1 || true
	# Do not auto-install pre-commit during lint/format/test to avoid network
	@which pre-commit >/dev/null 2>&1 || true

precommit-install: guard-venv ensure-dev
	# Install pre-commit only when explicitly requested
	@which pre-commit >/dev/null 2>&1 || $(PIP) install pre-commit
	pre-commit install --install-hooks

guard-venv:
	@if [ -n "$$VIRTUAL_ENV" ] && [ "$$VIRTUAL_ENV" != "$$PWD/.venv" ]; then \
		echo "Error: active venv ($$VIRTUAL_ENV) differs from project .venv ($$PWD/.venv)."; \
		echo "Please 'deactivate' or use the project venv (.venv)."; \
		exit 1; \
		fi

# Create and push a git tag
# Usage:
#   make tag VERSION=1.2.3            # use provided version
#   make tag TAG_PREFIX=v              # default prefix 'v'
#   make tag REMOTE=origin             # default remote 'origin'
#   make tag                           # auto-bump patch from latest tag
# Create and push a git tag only after checks pass
tag: check
	@VERSION="$(VERSION)" scripts/tag.sh
