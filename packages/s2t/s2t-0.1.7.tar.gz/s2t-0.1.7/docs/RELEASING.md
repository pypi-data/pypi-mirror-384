# Releasing

Versionierung und Releases basieren auf `setuptools-scm` (PEP 621, dynamische Version):

- Versionen werden über Git-Tags abgeleitet (z. B. `v0.1.0`).
- Während der Entwicklung (ohne Tag) wird eine Fallback-Version genutzt; mit Tag erhält das Paket die exakte Version.

## Schritte
1. Tag erstellen und pushen, z. B.:
   - `git tag v0.1.1`
   - `git push --tags`
2. Optional TestPyPI, sonst direkt PyPI:
   - `make publish-test` oder `make publish`
   - Diese Targets bauen zuvor (`make build`) und führen Checks aus (`make check`).

## Build-Details
- `make check` führt Format/Lint/Typprüfung und Tests aus.
- `make build` erzeugt sdist und Wheel.

