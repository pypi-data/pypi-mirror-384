# Project Management

## Team structure and roles
- Maintainers and contributors (see `CONTRIBUTING.md`). Roles typically include maintainer, developer, reviewer, release manager.

## Timeline / Gantt chart
- Not tracked in-repo. Recommend milestones aligned to feature clusters (core engine, integrations, platform expansions, forensics/attestation).

## Budget and resource allocation
- Open-source; resource planning depends on adoption and contributor bandwidth.

## Risk management and mitigation
- Technical: baseline poisoning, TOCTOU → mitigate with trusted baselines, higher intervals, defense-in-depth.
- Operational: false positives → use whitelists and staged rollouts (alert-only before restore).
- Platform variance: abstract via `platform/` and document privilege needs.

References: `SECURITY.md`, `CONTRIBUTING.md`.
