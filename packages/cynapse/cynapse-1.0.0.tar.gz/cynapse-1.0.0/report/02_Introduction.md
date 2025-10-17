# Introduction

## Background and problem statement
Python’s dynamic nature enables monkey-patching and runtime modifications. Attackers can exploit this to modify function bytecode, replace functions, inject modules, or tamper with import hooks at runtime. Traditional build-time integrity checks don’t address runtime changes.

## Motivation for developing the software
- Provide a runtime guardrail that continuously verifies code integrity.
- Detect and respond to tampering promptly to reduce dwell time and impact.
- Be easy to adopt in existing codebases with minimal changes (decorators/context manager).

## Goals and objectives
- Detect runtime integrity violations reliably with low overhead.
- Offer configurable responses (alert, auto-restore, terminate, snapshot).
- Provide API ergonomics that fit Python idioms and popular frameworks.
- Maintain cross-platform compatibility.

## Scope of the project
- Runtime integrity monitoring for Python functions, modules, and import hooks.
- Developer APIs for selectively protecting code paths.
- Framework integrations (Flask, Django, FastAPI) and async support.

## Limitations and assumptions
- Baseline integrity must be trusted ("baseline poisoning").
- TOCTOU remains a consideration between check cycles.
- Not a replacement for code signing, sandboxing, or broader app hardening.
- Some platform memory features may require privileges (see `cynapse/platform/`).
- Forensics/attestation are stubs or limited; future-ready toggles exist but not fully implemented in all paths.

References: `README.md` (Security Considerations), `cynapse/models.py`, `cynapse/monitor.py`.
