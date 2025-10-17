# Maintenance and Updates

## Versioning policy
- Semantic-style versioning; current `__version__ = "1.0.0"` (`cynapse/__init__.py`).
- Track changes in `CHANGELOG.md`.

## Bug fixing process
- Reproduce with examples/tests; add a failing test first; patch with minimal changes; update docs and changelog.

## Feature enhancement workflow
- Discuss in Issues/Discussions; design in `docs/design.md` as needed; PR with tests and examples.

## Future roadmap (high-level)
- Hardening for forensics snapshot pipeline.
- Expand detectors (deserialization, anomaly patterns) and platform primitives.
- Remote attestation integration path based on existing toggles.

References: `CHANGELOG.md`, `docs/HANDOFF.md`.
