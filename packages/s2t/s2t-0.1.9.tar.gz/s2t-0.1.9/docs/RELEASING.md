# Releasing

Versioning and releases are powered by `setuptools-scm` (PEP 621 dynamic version):

- Versions are derived from Git tags (e.g., `v0.1.0`).
- During development (without a tag) a fallback version is used; with a tag the package gets the exact version.

## Steps
1. Create and push a tag, for example:
   - `git tag v0.1.1`
   - `git push --tags`
2. Publish to TestPyPI or PyPI:
   - `make publish-test` or `make publish`
   - These targets build artifacts first (`make build`) and run checks (`make check`).

## Build Details
- `make check` runs formatting/linting/type checking and tests.
- `make build` creates the sdist and wheel.
