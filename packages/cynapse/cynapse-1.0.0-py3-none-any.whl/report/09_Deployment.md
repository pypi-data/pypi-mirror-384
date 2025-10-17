# Deployment

## Deployment environment
- Distributed as a Python library (package metadata in `pyproject.toml`).
- Works on Linux, Windows, macOS; Python 3.8+.

## Steps and tools used
- Install from source (dev): `pip install -e .`
- Optional extras: `cynapse[blake3]`, `cynapse[flask]`, `cynapse[django]`, `cynapse[fastapi]`, `cynapse[all]`.

## Configuration management
- Use `MonitorConfig` or `Monitor.builder()` to set interval, protection level, toggles, whitelists, response, and callbacks.
- Framework configs (e.g., Django `CYNAPSE_CONFIG` in `settings.py`).

## Continuous integration and delivery setup
- Not included in repo; recommended: lint, type-check, unit + integration tests, example runs, packaging checks.

## Rollback and recovery strategies
- Disable auto-healing if instability observed; revert package version.
- Use `TamperResponse.ALERT` first, then enable `RESTORE` as confidence increases.

References: `README.md`, `docs/INSTALLATION.md`, `cynapse/utils/config.py`.
