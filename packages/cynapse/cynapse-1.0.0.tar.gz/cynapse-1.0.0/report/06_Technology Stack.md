# Technology Stack

## Programming languages
- Python 3.8–3.13 (pure stdlib core)

## Frameworks and libraries
- Optional: `blake3` (faster hashing), `psutil` (status metrics)
- Integrations: Flask, Django, FastAPI

## Databases
- None. Baseline held in-memory; can be saved/exported to disk via `Baseline.save()`/`export_json()`.

## APIs and integrations
- Python import system (`sys.meta_path`) monitoring.
- OS memory mapping abstractions: `cynapse/platform/` for Linux/Windows/macOS.

## DevOps tools, CI/CD, version control
- Packaging: `pyproject.toml`, `setup.py`.
- Testing: `pytest`, `pytest-asyncio`, `pytest-cov` (optional dev extras).
- Lint/format/type: `ruff`, `black`, `isort`, `mypy` (optional dev extras).
- Version control: Git. Project metadata: `CHANGELOG.md`, `LICENSE`, `CONTRIBUTING.md`, `SECURITY.md`.

References: `pyproject.toml`, `docs/INSTALLATION.md`.
